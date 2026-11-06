# Grok Voice Guides · Cursor Skills

Unofficial Cindy adaptation of [grok-voice](https://github.com/cursor/plugins/tree/main/grok-voice).

All four upstream coding guides are included unchanged. They modify an application the user asks to develop; they do not add voice controls to Cindy. API access, xAI billing and application dependencies are separate.

Only the skills listed in ghost.json are included. Cursor rules, hooks, agents and MCP configuration are not loaded.

These skills run through the main Agent with the user's permissions and are globally available while the plugin is enabled. Dependencies mentioned by a skill must be obtained separately. No extra credentials are bundled.

Use the slash commands named in ghost.json; a plugin-level $command is not provided by this skills-only package.
