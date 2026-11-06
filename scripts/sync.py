#!/usr/bin/env python3
"""Convert reviewed Cursor skills to Cindy packages; never execute upstream code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile

import yaml

UPSTREAM = "https://github.com/cursor/plugins"
MIN_CINDY = "0.1.126"  # conservative, verified release; not a claim about first introduction
MANAGED = ("catalog", ".agents/plugins/marketplace.json", ".cursor-plugin/marketplace.json", "sync-state.json", "README.md")
MAX_FILE = 2 * 1024 * 1024
MAX_PACKAGE = 8 * 1024 * 1024
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def safe_path(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"Unsafe path: {value!r}")
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in ("", ".", "..") for x in value.split("/")):
        raise ValueError(f"Unsafe path: {value!r}")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("Control character in path")
    if any(x.startswith(".") for x in p.parts):
        raise ValueError(f"Hidden paths are not distributable: {value!r}")
    return value


class GitSource:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.commit = self.git("rev-parse", "HEAD").decode().strip()
        if not re.fullmatch(r"[0-9a-f]{40}", self.commit):
            raise ValueError("Expected a full upstream commit")
        self.tree = {}
        for record in self.git("ls-tree", "-r", "-z", "HEAD").split(b"\0"):
            if record:
                meta, path = record.split(b"\t", 1)
                mode, kind, oid = meta.decode().split()
                self.tree[path.decode("utf-8")] = (mode, kind, oid)

    def git(self, *args):
        return subprocess.check_output(["git", "--no-optional-locks", "-c", "core.hooksPath=/dev/null", "-C", str(self.root), *args])

    def read(self, path):
        mode, kind, oid = self.tree[path]
        if mode not in ("100644", "100755") or kind != "blob":
            raise ValueError(f"Refusing symlink/submodule/non-file: {path}")
        size = int(self.git("cat-file", "-s", oid))
        if size > MAX_FILE:
            raise ValueError(f"File exceeds size limit: {path}")
        return self.git("cat-file", "blob", oid)

    def files_under(self, prefix):
        return sorted(p for p in self.tree if p.startswith(prefix + "/"))


def frontmatter(content):
    if len(content) > 65536:
        raise ValueError("SKILL.md exceeds Cindy's 64 KiB limit")
    text = content.decode("utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
    if not match:
        raise ValueError("SKILL.md requires YAML frontmatter")
    meta = yaml.safe_load(match.group(1))
    if not isinstance(meta, dict):
        raise ValueError("Invalid skill frontmatter")
    name, description = meta.get("name"), meta.get("description")
    if not isinstance(name, str) or not NAME.fullmatch(name) or len(name) > 64:
        raise ValueError("Invalid skill name")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        raise ValueError(f"Invalid skill description for {name!r}: expected 1–1024 characters, got {len(description) if isinstance(description, str) else type(description).__name__}")
    return name, description


def fingerprint(files):
    h = hashlib.sha256()
    for name, data in sorted(files.items()):
        h.update(name.encode() + b"\0" + len(data).to_bytes(8, "big") + data)
    return h.hexdigest()


def bump(version):
    major, minor, patch = map(int, version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def copy_generated(root, destination):
    for rel in MANAGED:
        source = root / rel
        if source.exists():
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copyfile(source, target)


def bundle_pstack(source, plugin_path, package, previous_skills=()):
    prefix = f"{plugin_path}/skills/"
    entry = package["skills"][0]
    skill_names = sorted({p[len(prefix):].split("/", 1)[0] for p in source.files_under(prefix[:-1])
                          if p.endswith("/SKILL.md") and p[len(prefix):].count("/") == 1})
    if entry not in skill_names:
        raise ValueError("Missing pstack entry skill")
    for name in skill_names:
        if not NAME.fullmatch(name) or len(name) > 64:
            raise ValueError(f"Unsafe skill name: {name!r}")
    base = f"skills/{entry}"
    files, modes, evidence, descriptions = {}, {}, [], {}
    replacements = package.get("bundleReplacements", [])
    hits = [0] * len(replacements)
    deleted_skills = set(previous_skills) - set(skill_names)
    def adapt(text, path):
        for deleted in deleted_skills:
            if re.search(r'(?<![a-zA-Z0-9_./:-])/' + re.escape(deleted) + r'(?![a-zA-Z0-9_/-])', text):
                raise ValueError(f'Missing referenced skill: {deleted} in {path}')
        for i, replacement in enumerate(replacements):
            if replacement.get('path') in ('*', path):
                before, after = replacement['before'], replacement['after']
                if not isinstance(before, str) or not before:
                    raise ValueError('Empty adaptation replacement')
                hits[i] += text.count(before)
                text = text.replace(before, after)
        return text
    for skill in skill_names:
        skill_prefix = f"{prefix}{skill}"
        for source_file in source.files_under(skill_prefix):
            relative = safe_path(source_file[len(skill_prefix) + 1:])
            if skill == "statechart" and relative.startswith("scripts/test/"):
                continue
            if relative.lower().endswith('.cindy'):
                raise ValueError("Nested plugin package is not allowed")
            dest_dir = base if skill == entry else f"{base}/bundled/{skill}"
            output_relative = "SKILL.txt" if skill != entry and relative == "SKILL.md" else relative
            dest = safe_path(f"{dest_dir}/{output_relative}")
            data = source.read(source_file)
            if relative == "SKILL.md":
                match = re.match(rb"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", data, re.S)
                if not match:
                    raise ValueError(f"Missing frontmatter: {source_file}")
                meta = yaml.safe_load(match.group(1))
                if not isinstance(meta, dict) or meta.get('name') != skill or not isinstance(meta.get('description'), str) or not meta['description'].strip():
                    raise ValueError(f"Invalid bundled skill metadata: {source_file}")
                descriptions[skill] = ' '.join(meta['description'].split())
            if source_file.endswith('.md'):
                text = adapt(data.decode('utf-8'), source_file[len(plugin_path) + 1:])
                # Rebase relative sibling links from the upstream skills tree to the
                # entry's self-contained reference tree, including nested references.
                def rebase(match):
                    original = match.group(0)
                    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source_file), original))
                    if not resolved.startswith(prefix):
                        return original
                    parts = resolved[len(prefix):].split('/')
                    if parts[0] not in skill_names:
                        if len(parts) > 1 and parts[-1] == 'SKILL.md':
                            raise ValueError(f"Missing referenced skill: {resolved}")
                        return original
                    target_skill = parts.pop(0)
                    if parts and parts[-1] == 'SKILL.md' and target_skill != entry:
                        parts[-1] = 'SKILL.txt'
                    target = base if target_skill == entry else f"{base}/bundled/{target_skill}"
                    if parts:
                        target += '/' + '/'.join(parts)
                    return posixpath.relpath(target, posixpath.dirname(dest))
                if skill != entry:
                    text = re.sub(r'(?<![./])\.\./SKILL\.md', '../SKILL.txt', text)
                text = re.sub(r'(?:\.\./)+[a-z0-9][a-z0-9-]*(?:/[a-zA-Z0-9_.-]+)*', rebase, text)
                def rebase_upstream_skill(match):
                    name = match.group(1)
                    if name not in skill_names:
                        raise ValueError(f'Missing referenced skill: {name}')
                    target = f'{base}/SKILL.md' if name == entry else f'{base}/bundled/{name}/SKILL.txt'
                    return posixpath.relpath(target, posixpath.dirname(dest))
                text = re.sub(r'pstack/skills/([a-z0-9-]+)/SKILL\.md', rebase_upstream_skill, text)
                text = text.replace('../../docs/', f'{UPSTREAM}/blob/@PSTACK_CONTENT_COMMIT@/{plugin_path}/docs/')
                text = text.replace('../../README.md', f'{UPSTREAM}/blob/@PSTACK_CONTENT_COMMIT@/{plugin_path}/README.md')
                for subskill in skill_names:
                    if subskill != entry:
                        text = re.sub(r'(?<![a-zA-Z0-9_./:-])/' + re.escape(subskill) + r'(?![a-zA-Z0-9_/-])', subskill + ' (bundled reference; see entry index)', text)
                data = text.encode()
                if relative == 'SKILL.md':
                    adapted_match = re.match(rb'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)', data, re.S)
                    adapted_meta = yaml.safe_load(adapted_match.group(1))
                    descriptions[skill] = ' '.join(adapted_meta['description'].split())
            if dest in files:
                raise ValueError(f"Duplicate bundled path: {dest}")
            files[dest] = data
            modes[dest] = source.tree[source_file][0]
            if relative == 'SKILL.md':
                evidence.append({'path': dest, 'upstreamSha256': hashlib.sha256(source.read(source_file)).hexdigest(), 'distributedSha256': hashlib.sha256(data).hexdigest()})
    for agent in ('poteto-agent.md', 'comment-sicko.md'):
        upstream_file = f"{plugin_path}/agents/{agent}"
        dest = f"{base}/agents/{agent}"
        files[dest] = adapt(source.read(upstream_file).decode('utf-8'), f"agents/{agent}").encode()
        modes[dest] = source.tree[upstream_file][0]
    for replacement, count in zip(replacements, hits):
        path = replacement.get('path', '')
        segments = path.split('/')
        deleted_skill = len(segments) >= 3 and segments[0] == 'skills' and segments[1] not in skill_names
        if deleted_skill:
            continue
        expected = replacement.get('count', 1)
        if count != expected:
            raise ValueError(f"Adaptation no longer matches upstream: {path}: expected {expected}, got {count}: {replacement['before']!r}")
    index = '\n'.join(f"- [{skill}](bundled/{skill}/SKILL.txt): {descriptions[skill]}" for skill in skill_names if skill != entry)
    entry_file = f"{base}/SKILL.md"
    files[entry_file] += ("\n\n## Bundled skill reference index\n\n" + index + "\n").encode()
    for record in evidence:
        if record['path'] == entry_file:
            record['distributedSha256'] = hashlib.sha256(files[entry_file]).hexdigest()
    name, description = frontmatter(files[entry_file])
    return files, modes, [{'dir': base, 'name': name, 'description': description}], evidence, skill_names, descriptions


def build(upstream, root, destination):
    source = GitSource(upstream)
    policy = json.loads((root / "policy.json").read_text())
    old = json.loads((root / "sync-state.json").read_text()) if (root / "sync-state.json").exists() else {"packages": {}}
    marketplace = json.loads(source.read(".cursor-plugin/marketplace.json"))
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 512:
        raise ValueError("Unexpected upstream marketplace shape")
    upstream_entries = {}
    for entry in entries:
        name, path = entry["name"], entry["source"]
        safe_path(path)
        if name in upstream_entries:
            raise ValueError(f"Duplicate upstream plugin: {name}")
        upstream_entries[name] = entry
    state = {"schemaVersion": 1, "upstream": UPSTREAM, "commit": source.commit, "packages": dict(old["packages"])}
    for record in state["packages"].values():
        record["active"] = False
    plugins, included, seen = [], {}, set()
    bundle_inventory, bundle_playbooks, bundle_descriptions = [], [], {}
    bundle_plugin_id, bundle_entry = None, None
    bundle_only = len(policy['packages']) == 1 and policy['packages'][0].get('bundleAllSkills')
    for package in policy["packages"]:
        plugin_id = package["id"]
        if not NAME.fullmatch(plugin_id) or len(plugin_id) > 32 or plugin_id in seen:
            raise ValueError(f"Invalid/duplicate Cindy id: {plugin_id}")
        seen.add(plugin_id)
        if not 1 <= len(package["skills"]) <= 4:
            raise ValueError("Cindy supports 1–4 skills per plugin")
        upstream_name = package["upstream"]
        entry = upstream_entries.get(upstream_name)
        if entry is None:
            continue  # removed upstream: no stale marketplace entry; retain version tombstone
        plugin_path = entry["source"]
        requested = [safe_path(s) for s in package["skills"]]
        # Deletion withdraws the package until its policy is updated.
        if any(f"{plugin_path}/skills/{s}/SKILL.md" not in source.tree for s in requested):
            continue
        license_path = f"{plugin_path}/LICENSE"
        license_data = source.read(license_path)
        license_digest = hashlib.sha256(license_data).hexdigest()
        if license_digest not in policy["approvedLicenseSha256"]:
            raise ValueError(f"License needs review: {license_path} ({license_digest})")
        files = {"LICENSE": license_data, "main.js": b"// Skills-only plugin; no autonomous runtime or tools.\n"}
        modes = {}
        items, skill_changes = [], []
        bundle_names = []
        if package.get("bundleAllSkills"):
            if len(requested) != 1:
                raise ValueError("A bundled package requires exactly one entry")
            previous_skills = set()
            previous_evidence = root / 'catalog/plugins' / plugin_id / 'UPSTREAM.json'
            if previous_evidence.exists():
                previous_data = json.loads(previous_evidence.read_text())
                for record in previous_data['skills']:
                    match = re.fullmatch(r'skills/[^/]+/bundled/([a-z0-9-]+)/SKILL\.txt', record['path'])
                    if match:
                        previous_skills.add(match.group(1))
            bundle_files, modes, items, skill_changes, bundle_names, bundle_descriptions = bundle_pstack(source, plugin_path, package, previous_skills)
            bundle_inventory = bundle_names
            bundle_plugin_id, bundle_entry = plugin_id, requested[0]
            playbook_prefix = f"skills/{requested[0]}/playbooks/"
            bundle_playbooks = sorted(p[len(playbook_prefix):] for p in bundle_files if p.startswith(playbook_prefix) and '/' not in p[len(playbook_prefix):] and p.endswith('.md'))
            files.update(bundle_files)
        for skill in ([] if package.get("bundleAllSkills") else requested):
            skill_prefix = f"{plugin_path}/skills/{skill}"
            for file in source.files_under(skill_prefix):
                rel = safe_path(file[len(plugin_path) + 1:])
                if rel.endswith(".cindy"):
                    raise ValueError("Nested plugin package is not allowed")
                files[rel] = source.read(file)
                modes[rel] = source.tree[file][0]
            skill_file = f"skills/{skill}/SKILL.md"
            content = files[skill_file]
            for replacement in package.get("replacements", {}).get(skill, []):
                before, after = replacement["before"], replacement["after"]
                if content.count(before.encode()) != 1:
                    raise ValueError(f"Adaptation no longer matches upstream: {skill}")
                content = content.replace(before.encode(), after.encode())
            override = package.get("descriptionOverrides", {}).get(skill)
            if override is not None:
                match = re.match(rb"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", content, re.S)
                if not match:
                    raise ValueError(f"Missing frontmatter for {skill}")
                meta = yaml.safe_load(match.group(1).decode())
                meta["description"] = override
                content = b"---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).encode() + b"---\n" + content[match.end():]
            files[skill_file] = content
            name, description = frontmatter(content)
            if any(i["name"] == name for i in items):
                raise ValueError("Duplicate skill in package")
            items.append({"dir": f"skills/{skill}", "name": name, "description": description})
            skill_changes.append({"path": skill_file, "upstreamSha256": hashlib.sha256(source.read(f"{skill_prefix}/SKILL.md")).hexdigest(), "distributedSha256": hashlib.sha256(content).hexdigest()})
        if len(files) + 3 > 256:
            raise ValueError("Package exceeds Cindy's 256 file limit")
        if sum(map(len, files.values())) > MAX_PACKAGE:
            raise ValueError("Package exceeds size budget")
        description = package["description"]
        manifest = {"schemaVersion": 3, "id": plugin_id, "name": package["name"], "description": description, "whenToUse": package["whenToUse"], "version": "1.0.0", "minCindyVersion": MIN_CINDY, "entry": "main.js", "skill": {"items": items}}
        files["ghost.json"] = json_bytes(manifest)
        files["ADAPTATION.md"] = (f"# {package['name']}\n\nUnofficial Cindy adaptation of [{upstream_name}]({UPSTREAM}/tree/main/{plugin_path}).\n\n{package['notes']}\n\nOnly the skills listed in ghost.json are registered. Cursor rules, hooks, agents and MCP configuration are not loaded.\n\nThese skills run through the main Agent with the user's permissions and are globally available while the plugin is enabled. Dependencies mentioned by a skill must be obtained separately. No extra credentials are bundled.\n\nUse the slash commands named in ghost.json; a plugin-level $command is not provided by this skills-only package.\n" + ("\nBundled skill references: " + ", ".join(bundle_names) + ".\n" if bundle_names else "")).encode()
        if bundle_playbooks:
            files['ADAPTATION.md'] += ('\nBundled playbooks:\n\n' + ''.join(f'- [{name}](skills/{requested[0]}/playbooks/{name})\n' for name in bundle_playbooks)).encode()
        # Executable-bit changes affect package behavior and must bump the version too.
        mode_record = {"@executableModes": json_bytes(modes)}
        # A rewritten upstream description can change provenance even when the
        # distributed body is identical. Hash its source evidence as well.
        digest = fingerprint({**files, **mode_record, "@sourceEvidence": json_bytes(skill_changes)})
        previous = old["packages"].get(plugin_id)
        unchanged = previous and previous["fingerprint"] == digest
        version = previous["version"] if unchanged else (bump(previous["version"]) if previous else "1.0.0")
        content_commit = previous["contentCommit"] if unchanged else source.commit
        if package.get('bundleAllSkills'):
            token = f'{UPSTREAM}/blob/@PSTACK_CONTENT_COMMIT@/'.encode()
            replacement = f'{UPSTREAM}/blob/{content_commit}/'.encode()
            for path in files:
                if path.endswith(('.md', '.txt')):
                    files[path] = files[path].replace(token, replacement)
            for record in skill_changes:
                record['distributedSha256'] = hashlib.sha256(files[record['path']]).hexdigest()
        manifest["version"] = version
        manifest["releaseNotes"] = f"Adapt {upstream_name} skills from cursor/plugins at {content_commit[:12]}. See ADAPTATION.md and UPSTREAM.json for scope and changes."
        files["ghost.json"] = json_bytes(manifest)
        files["UPSTREAM.json"] = json_bytes({"repository": UPSTREAM, "commit": content_commit, "path": plugin_path, "license": "MIT", "skills": skill_changes, "notes": package["notes"]})
        folded_paths = {}
        for path in files:
            parts = path.split('/')
            for n in range(1, len(parts) + 1):
                prefix = '/'.join(parts[:n])
                folded = prefix.casefold()
                if folded in folded_paths and folded_paths[folded] != prefix:
                    raise ValueError('Case-insensitive package path collision')
                folded_paths[folded] = prefix
        if len(files) > 256 or sum(map(len, files.values())) > MAX_PACKAGE:
            raise ValueError('Package exceeds file count or size budget')
        package_dir = destination / "catalog/plugins" / plugin_id
        for rel, data in files.items():
            target = package_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            # Preserve executability for scripts; never execute them during conversion.
            if modes.get(rel) == "100755":
                target.chmod(0o755)
        state["packages"][plugin_id] = {"version": version, "fingerprint": digest, "contentCommit": content_commit, "active": True, "outputFingerprint": fingerprint({**files, **mode_record})}
        if bundle_only:
            state['commit'] = content_commit
        plugins.append({"name": plugin_id, "source": f"./catalog/plugins/{plugin_id}"})
        included.setdefault(upstream_name, []).append(plugin_id)
    if not plugins:
        raise ValueError("Refusing to publish an empty marketplace")
    market = {"name": "cindy-cursor-plugins", "interface": {"displayName": "pstack for Cindy (Unofficial)"}, "plugins": plugins}
    for rel in (".agents/plugins/marketplace.json", ".cursor-plugin/marketplace.json"):
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(json_bytes(market))
    report_entries = {name: entry for name, entry in upstream_entries.items() if not bundle_only or name in included}
    report_commit = state['commit']
    report = {"upstream": UPSTREAM, "commit": report_commit, "totalUpstream": len(report_entries), "cindyPackages": len(plugins), "includedSources": len(included), "plugins": []}
    if bundle_inventory:
        report['bundledSkills'] = bundle_inventory
        report['excludedResources'] = ['docs/', 'automations/benny/', 'skills/statechart/scripts/test/']
    for name, entry in report_entries.items():
        skills = [p for p in source.files_under(entry["source"] + "/skills") if p.endswith("/SKILL.md")]
        report["plugins"].append({"name": name, "source": entry["source"], "status": "adapted-skills-only" if name in included else "excluded", "packages": included.get(name, []), "upstreamSkillCount": len(skills), "reason": "Only reviewed skills are included; other components are excluded." if name in included else policy["exclusions"].get(name, "Requires Cindy-native MCP/authentication/tool adaptation; not installed by this market.")})
    (destination / "catalog/report.json").write_bytes(json_bytes(report))
    rows = ["# Compatibility report", "", f"Upstream: [{report_commit}]({UPSTREAM}/commit/{report_commit})", "", f"{len(plugins)} Cindy packages from {len(included)} of {len(report_entries)} tracked upstream plugins. Only reviewed skills are published.", "", "| Upstream plugin | Status | Cindy packages / reason |", "| --- | --- | --- |"]
    for p in report["plugins"]:
        details = ", ".join(p["packages"]) or p["reason"]
        rows.append(f"| [{p['name']}]({UPSTREAM}/tree/{report_commit}/{p['source']}) | {p['status']} | {details} |")
    if bundle_inventory:
        rows += ['', '## Bundled skill inventory', '']
        for name in bundle_inventory:
            path = f'skills/{bundle_entry}/SKILL.md' if name == bundle_entry else f'skills/{bundle_entry}/bundled/{name}/SKILL.txt'
            rows.append(f'- [`{name}`](plugins/{bundle_plugin_id}/{path}): {bundle_descriptions[name]}')
        rows += ['', 'Excluded: upstream `docs/`, `automations/benny/`, and `skills/statechart/scripts/test/` test resources. The MIT license and original copyright notice are included in the package.']
        readme = root / 'README.md'
        if readme.exists():
            text = readme.read_text()
            markers = [f'<!-- pstack-{section}:{side} -->' for section in ('skills', 'playbooks') for side in ('start', 'end')]
            if any(text.count(marker) != 1 for marker in markers) or [text.index(marker) for marker in markers] != sorted(text.index(marker) for marker in markers):
                raise ValueError('Invalid README markers')
            for section, names in [('skills', bundle_inventory), ('playbooks', bundle_playbooks)]:
                start, end = f'<!-- pstack-{section}:start -->', f'<!-- pstack-{section}:end -->'
                if text.count(start) != 1 or text.count(end) != 1 or text.index(start) >= text.index(end):
                    raise ValueError(f'Invalid README markers: {section}')
                left, right = text.index(start) + len(start), text.index(end)
                text = text[:left] + '\n' + '、'.join(f'`{name}`' for name in names) + '。\n' + text[right:]
            (destination / 'README.md').write_text(text)
    if (root / 'README.md').exists() and not (destination / 'README.md').exists():
        shutil.copyfile(root / 'README.md', destination / 'README.md')
    (destination / "catalog/REPORT.md").write_text("\n".join(rows) + "\n")
    (destination / "sync-state.json").write_bytes(json_bytes(state))
    return report


def tree_snapshot(root):
    result = {}
    for rel in MANAGED:
        p = root / rel
        paths = sorted(p.rglob("*")) if p.is_dir() else [p]
        for file in paths:
            if file.is_file() and not file.name.endswith(".cindy"):
                result[file.relative_to(root).as_posix()] = (file.read_bytes(), bool(file.stat().st_mode & 0o111))
    return result


def sync(upstream, root, check=False):
    root = Path(root).resolve()
    for rel in MANAGED:
        p = root / rel
        for parent in [p, *p.parents]:
            if parent == root.parent:
                break
            if parent.is_symlink():
                raise ValueError(f"Managed destination must not be a symlink: {parent}")
    with tempfile.TemporaryDirectory(prefix="cindy-cursor-sync-") as temp:
        staged = Path(temp)
        report = build(upstream, root, staged)
        changed = tree_snapshot(root) != tree_snapshot(staged)
        if check:
            if changed:
                raise ValueError("Generated catalog is stale; run scripts/sync.py")
            return report
        if changed:
            # Build/validate the entire generation before replacing any current output.
            # GitHub only publishes a successful generation as a single Git commit.
            for rel in MANAGED:
                target = root / rel
                if target.is_dir():
                    shutil.rmtree(target)
                elif target.exists():
                    target.unlink()
                target.parent.mkdir(parents=True, exist_ok=True)
                src = staged / rel
                if not src.exists():
                    continue
                if src.is_dir():
                    shutil.copytree(src, target)
                else:
                    shutil.copyfile(src, target)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True, type=Path, help="Local git clone of cursor/plugins; reads committed HEAD only")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = sync(args.upstream, args.root, args.check)
    print(f"{report['cindyPackages']} packages; {report['includedSources']}/{report['totalUpstream']} upstream sources; commit {report['commit']}")


if __name__ == "__main__":
    main()
