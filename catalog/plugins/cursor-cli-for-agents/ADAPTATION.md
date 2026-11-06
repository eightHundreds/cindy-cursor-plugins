# CLI for Agents · Cursor Skills

Unofficial Cindy adaptation of [cli-for-agent](https://github.com/cursor/plugins/tree/main/cli-for-agent).

The complete CLI design skill is included unchanged. No tools, rules or background processes are installed.

Only the skills listed in ghost.json are included. Cursor rules, hooks, agents and MCP configuration are not loaded.

These skills run through the main Agent with the user's permissions and are globally available while the plugin is enabled. Dependencies mentioned by a skill must be obtained separately. No extra credentials are bundled.

Use the slash commands named in ghost.json; a plugin-level $command is not provided by this skills-only package.
