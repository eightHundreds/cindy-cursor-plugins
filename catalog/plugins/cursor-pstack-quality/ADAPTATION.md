# pstack Quality · Cursor Skills

Unofficial Cindy adaptation of [pstack](https://github.com/cursor/plugins/tree/main/pstack).

Only these four skills are included unchanged. No always-on pstack mode, hooks, team chat, shipping, auto-approval or automation workflow is imported. Original frontmatter is preserved; invocation-field behavior can differ by Cindy agent engine.

Only the skills listed in ghost.json are included. Cursor rules, hooks, agents and MCP configuration are not loaded.

These skills run through the main Agent with the user's permissions and are globally available while the plugin is enabled. Dependencies mentioned by a skill must be obtained separately. No extra credentials are bundled.

Use the slash commands named in ghost.json; a plugin-level $command is not provided by this skills-only package.
