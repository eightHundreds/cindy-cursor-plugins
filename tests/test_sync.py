import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "scripts" / "sync.py"
spec = importlib.util.spec_from_file_location("cursor_sync", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.upstream = self.base / "upstream"
        self.root = self.base / "output"
        self.upstream.mkdir()
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.entries = [{"name": name, "source": name} for name in ("alpha", "beta")]
        self.policy = {"packages": [self.package(name) for name in ("alpha", "beta")], "exclusions": {}}
        self.write_market()
        for name in ("alpha", "beta"):
            self.write_upstream(f"{name}/LICENSE", "MIT License\nPermission is hereby granted\n")
            self.write_skill(name)
        self.write_policy()
        self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.upstream), *args], stderr=subprocess.PIPE)

    def write_upstream(self, path, content):
        target = self.upstream / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def write_skill(self, name, text=None):
        self.write_upstream(f"{name}/skills/{name}/SKILL.md", text or f"---\nname: {name}\ndescription: {name} description\n---\n\nInstructions.\n")

    def write_market(self):
        self.write_upstream(".cursor-plugin/marketplace.json", json.dumps({"plugins": self.entries}))

    def write_policy(self):
        (self.root / "policy.json").write_text(json.dumps(self.policy), encoding="utf-8")

    def package(self, name):
        return {"id": name, "upstream": name, "name": name.title(), "description": f"{name} package", "whenToUse": "When needed", "notes": "Reviewed.", "skills": [name]}

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "fixture", "--allow-empty")

    def run_sync(self, check=False):
        return sync.sync(self.upstream, self.root, check=check)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--upstream", str(self.upstream), "--root", str(self.root), *args], capture_output=True, text=True)

    def state(self, name):
        return json.loads((self.root / "sync-state.json").read_text())["packages"][name]

    def manifest(self, name):
        return json.loads((self.root / "catalog" / "plugins" / name / "ghost.json").read_text())

    def assert_failure_preserves_output(self, error):
        before = sync.tree_snapshot(self.root)
        with self.assertRaisesRegex((ValueError, KeyError, sync.yaml.YAMLError), error):
            self.run_sync()
        self.assertEqual(before, sync.tree_snapshot(self.root))

    def test_idempotency_and_check_cli(self):
        self.run_sync()
        before = sync.tree_snapshot(self.root)
        self.run_sync()
        self.assertEqual(before, sync.tree_snapshot(self.root))
        self.assertEqual(self.cli("--check").returncode, 0)
        (self.root / "catalog" / "plugins" / "alpha" / "main.js").write_text("tampered")
        stale = sync.tree_snapshot(self.root)
        result = self.cli("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale", result.stderr)
        self.assertEqual(stale, sync.tree_snapshot(self.root))
        self.run_sync()
        self.assertEqual(before, sync.tree_snapshot(self.root))

    def test_content_change_bumps_only_changed_package(self):
        self.run_sync()
        beta = self.state("beta")
        self.write_skill("alpha", "---\nname: alpha\ndescription: changed\n---\nNew content.\n")
        self.commit()
        self.run_sync()
        self.assertEqual(self.state("alpha")["version"], "1.0.1")
        self.assertEqual(self.manifest("alpha")["version"], "1.0.1")
        self.assertEqual(self.state("beta"), beta)

    def test_executable_bit_change_bumps_only_affected_package(self):
        relative = "alpha/skills/alpha/run.sh"
        content = "#!/bin/sh\necho hello\n"
        self.write_upstream(relative, content)
        script = self.upstream / relative
        script.chmod(0o644)
        self.commit()
        self.run_sync()
        beta = self.state("beta")
        output = self.root / "catalog/plugins/alpha/skills/alpha/run.sh"
        self.assertFalse(output.stat().st_mode & 0o111)
        script.chmod(0o755)
        self.commit()
        self.assertIn(b"100755", self.git("ls-tree", "HEAD", relative))
        self.run_sync()
        self.assertEqual(self.state("alpha")["version"], "1.0.1")
        self.assertEqual(self.manifest("alpha")["version"], "1.0.1")
        self.assertEqual(self.state("beta"), beta)
        self.assertEqual(output.read_text(), content)
        self.assertEqual(output.stat().st_mode & 0o777, 0o755)

    def test_irrelevant_commit_does_not_bump_packages(self):
        self.run_sync()
        alpha, beta = self.state("alpha"), self.state("beta")
        self.write_upstream("unrelated.txt", "new upstream content")
        self.commit()
        self.run_sync()
        self.assertEqual(self.state("alpha"), alpha)
        self.assertEqual(self.state("beta"), beta)
        self.assertEqual(json.loads((self.root / "sync-state.json").read_text())["commit"], self.git("rev-parse", "HEAD").decode().strip())

    def test_removed_package_and_changed_readdition_preserves_version_history(self):
        self.run_sync()
        self.entries = [self.entries[1]]
        self.write_market()
        self.commit()
        self.run_sync()
        self.assertFalse(self.state("alpha")["active"])
        self.assertFalse((self.root / "catalog/plugins/alpha").exists())
        self.entries.insert(0, {"name": "alpha", "source": "alpha"})
        self.write_market()
        self.write_skill("alpha", "---\nname: alpha\ndescription: returned\n---\nUpdated.\n")
        self.commit()
        self.run_sync()
        self.assertTrue(self.state("alpha")["active"])
        self.assertEqual(self.state("alpha")["version"], "1.0.1")
        market = json.loads((self.root / ".cursor-plugin/marketplace.json").read_text())
        self.assertEqual([p["name"] for p in market["plugins"]], ["alpha", "beta"])

    def test_removed_skill_and_unchanged_readdition_keeps_version(self):
        self.run_sync()
        original = (self.upstream / "alpha/skills/alpha/SKILL.md").read_text()
        (self.upstream / "alpha/skills/alpha/SKILL.md").unlink()
        self.commit()
        self.run_sync()
        self.assertFalse(self.state("alpha")["active"])
        self.assertFalse((self.root / "catalog/plugins/alpha").exists())
        self.write_skill("alpha", original)
        self.commit()
        self.run_sync()
        self.assertTrue(self.state("alpha")["active"])
        self.assertEqual(self.state("alpha")["version"], "1.0.0")

    def test_malformed_yaml_does_not_overwrite_output(self):
        self.run_sync()
        self.write_skill("alpha", "---\nname: alpha\ndescription: [unterminated\n---\n")
        self.commit()
        self.assert_failure_preserves_output("(?i)(flow|expected|end)")

    def test_mismatched_replacement_does_not_overwrite_output(self):
        self.run_sync()
        self.policy["packages"][0]["replacements"] = {"alpha": [{"before": "missing text", "after": "replacement"}]}
        self.write_policy()
        self.assert_failure_preserves_output("Adaptation no longer matches")

    def test_traversal_path_rejected_without_overwriting(self):
        self.run_sync()
        self.entries[0]["source"] = "alpha/../beta"
        self.write_market()
        self.commit()
        self.assert_failure_preserves_output("Unsafe path")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_committed_symlink_rejected_without_overwriting(self):
        self.run_sync()
        path = self.upstream / "alpha/skills/alpha/extra"
        path.symlink_to("SKILL.md")
        self.commit()
        self.assertIn(b"120000", self.git("ls-tree", "HEAD", "alpha/skills/alpha/extra"))
        self.assert_failure_preserves_output("Refusing symlink")

    def test_skill_count_maximum(self):
        self.run_sync()
        self.policy["packages"][0]["skills"] = ["one", "two", "three", "four", "five"]
        self.write_policy()
        self.assert_failure_preserves_output("1–4 skills")

    def test_description_override_rewrites_frontmatter_and_preserves_body(self):
        body = "\n# Instructions\n\nKeep this body exactly.\n---\nMore text.\n"
        self.write_skill("alpha", "---\nname: alpha\ndescription: " + "x" * 1025 + "\nmetadata: retained\n---\n" + body)
        self.commit()
        with self.assertRaisesRegex(ValueError, "Invalid skill description"):
            self.run_sync()
        override = "Short description: use when needed."
        self.policy["packages"][0]["descriptionOverrides"] = {"alpha": override}
        self.write_policy()
        self.run_sync()
        content = (self.root / "catalog/plugins/alpha/skills/alpha/SKILL.md").read_text()
        opening, frontmatter, actual_body = content.split("---\n", 2)
        self.assertEqual(opening, "")
        meta = sync.yaml.safe_load(frontmatter)
        self.assertEqual(meta, {"name": "alpha", "description": override, "metadata": "retained"})
        self.assertEqual(self.manifest("alpha")["skill"]["items"][0]["description"], meta["description"])
        self.assertEqual(actual_body, body)

    def test_folded_description_is_exact(self):
        self.write_skill("alpha", "---\nname: alpha\ndescription: >-\n  First line of description\n  continues here.\n\n  Second paragraph.\n---\nBody.\n")
        self.commit()
        self.run_sync()
        item = self.manifest("alpha")["skill"]["items"][0]
        self.assertEqual(item["description"], "First line of description continues here.\nSecond paragraph.")
        self.assertEqual(item["name"], "alpha")


if __name__ == "__main__":
    unittest.main()
