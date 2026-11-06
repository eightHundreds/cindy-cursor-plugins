# Origin API Guides · Cursor Skills

Unofficial Cindy adaptation of [origin-apps](https://github.com/cursor/plugins/tree/main/origin-apps).

Both skills and their references are included unchanged. They need access to live Cursor Origin documentation. This package does not create an account, grant API access, migrate a repository or install an MCP server.

Only the skills listed in ghost.json are included. Cursor rules, hooks, agents and MCP configuration are not loaded.

These skills run through the main Agent with the user's permissions and are globally available while the plugin is enabled. Dependencies mentioned by a skill must be obtained separately. No extra credentials are bundled.

Use the slash commands named in ghost.json; a plugin-level $command is not provided by this skills-only package.
