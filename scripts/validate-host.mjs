// Validate against the exact official Cindy release, not a parallel schema.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';

const sourceRoot = process.argv[2];
if (!sourceRoot) throw new Error('Usage: npm run validate:host -- /path/to/cindy-v0.1.126');
const { validateGhostManifest } = await import(pathToFileURL(path.resolve(sourceRoot, 'packages/plugin-protocol/src/manifest.ts')));
const root = path.resolve(import.meta.dirname, '..');
const marketplace = JSON.parse(fs.readFileSync(path.join(root, '.agents/plugins/marketplace.json')));
assert.equal(marketplace.name, 'cindy-cursor-plugins');
assert.deepEqual(marketplace, JSON.parse(fs.readFileSync(path.join(root, '.cursor-plugin/marketplace.json'))));
const state = JSON.parse(fs.readFileSync(path.join(root, 'sync-state.json')));
const ids = new Set();
for (const plugin of marketplace.plugins) {
  const dir = path.resolve(root, plugin.source);
  assert.ok(dir.startsWith(root + path.sep));
  assert.equal(fs.realpathSync(dir), dir);
  const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'ghost.json')));
  const validation = validateGhostManifest(manifest);
  assert.ok(validation.ok, `${plugin.name}: ${validation.reason}`);
  assert.equal(manifest.id, plugin.name);
  assert.ok(!ids.has(manifest.id));
  ids.add(manifest.id);
  assert.equal(manifest.minCindyVersion, '0.1.126');
  assert.equal(manifest.version, state.packages[manifest.id].version);
  assert.ok(fs.existsSync(path.join(dir, manifest.entry)));
  assert.ok(fs.existsSync(path.join(dir, 'LICENSE')));
  assert.ok(manifest.skill.items.length >= 1 && manifest.skill.items.length <= 4);
  // Only skills are contributed: no pretend MCP tools, native runtime permissions or command.
  assert.deepEqual(Object.keys(manifest).sort(), ['schemaVersion', 'id', 'name', 'description', 'whenToUse', 'version', 'minCindyVersion', 'entry', 'skill', 'releaseNotes'].sort());
  for (const skill of manifest.skill.items) {
    const file = path.join(dir, skill.dir, 'SKILL.md');
    assert.ok(fs.statSync(file).size <= 65536);
  }
  console.log(`${manifest.id}@${manifest.version}: official manifest validator OK (${manifest.skill.items.length} skills)`);
}
assert.ok(ids.size > 0);
