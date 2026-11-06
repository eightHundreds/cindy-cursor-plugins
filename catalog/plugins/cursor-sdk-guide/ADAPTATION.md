# Cursor SDK Guide · Cursor Skills

Unofficial Cindy adaptation of [cursor-sdk](https://github.com/cursor/plugins/tree/main/cursor-sdk).

The SDK guide body and its references are included unchanged. Its frontmatter description is shortened to fit Cindy's 1024-character limit. It helps write external integration code; it does not make Cursor the execution engine for Cindy. Using the external SDK requires a separate Cursor account, credentials and dependencies.

Only the skills listed in ghost.json are included. Cursor rules, hooks, agents and MCP configuration are not loaded.

These skills run through the main Agent with the user's permissions and are globally available while the plugin is enabled. Dependencies mentioned by a skill must be obtained separately. No extra credentials are bundled.

Use the slash commands named in ghost.json; a plugin-level $command is not provided by this skills-only package.
