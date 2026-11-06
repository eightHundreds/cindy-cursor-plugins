# pstack · Cursor Skills

Unofficial Cindy adaptation of [pstack](https://github.com/cursor/plugins/tree/main/pstack).

The poteto-mode entry and all upstream skill references are included. Upstream docs, automations/benny and statechart/scripts/test resources are excluded; links to upstream docs use the immutable source commit. Skills and subprocess capabilities vary by Cindy agent engine. Bugbot requires a repository installation. No Cursor modes, hooks, background processes or plugin tools are installed.

Only the skills listed in ghost.json are registered. Cursor rules, hooks, agents and MCP configuration are not loaded.

These skills run through the main Agent with the user's permissions and are globally available while the plugin is enabled. Dependencies mentioned by a skill must be obtained separately. No extra credentials are bundled.

Use the slash commands named in ghost.json; a plugin-level $command is not provided by this skills-only package.

Bundled skill references: architect, arena, automate-me, benchmark-checklist, blast-radius, bro, correct, create-formal-verification-skill, create-verification-skill, figure-it-out, how, in-your-own-words, interrogate, ketchup, ketchup-video, maintain-formal-verification-skill, maintain-verification-skill, make-bot-ui, no-comments, poteto-help, poteto-mode, principle-attack-the-premise, principle-boundary-discipline, principle-build-the-lever, principle-encode-lessons-in-structure, principle-exhaust-the-design-space, principle-experience-first, principle-explain-the-number, principle-fix-root-causes, principle-foundational-thinking, principle-guard-the-context-window, principle-laziness-protocol, principle-make-operations-idempotent, principle-migrate-callers-then-delete-legacy-apis, principle-minimize-reader-load, principle-model-the-domain, principle-never-block-on-the-human, principle-outcome-oriented-execution, principle-prove-it-works, principle-redesign-from-first-principles, principle-separate-before-serializing-shared-state, principle-sequence-verifiable-units, principle-subtract-before-you-add, principle-test-behavior-not-implementation, principle-type-system-discipline, recall, reflect, setup-pstack, sharpen, show-me-your-work, statechart, swarm, tdd, teach, technical-writing, typescript-best-practices, unslop, why.

Bundled playbooks:

- [authoring-a-skill.md](skills/poteto-mode/playbooks/authoring-a-skill.md)
- [autonomous-run.md](skills/poteto-mode/playbooks/autonomous-run.md)
- [autopilot-full.md](skills/poteto-mode/playbooks/autopilot-full.md)
- [autopilot-stack.md](skills/poteto-mode/playbooks/autopilot-stack.md)
- [babysit.md](skills/poteto-mode/playbooks/babysit.md)
- [bug-fix.md](skills/poteto-mode/playbooks/bug-fix.md)
- [eval.md](skills/poteto-mode/playbooks/eval.md)
- [feature.md](skills/poteto-mode/playbooks/feature.md)
- [hillclimb.md](skills/poteto-mode/playbooks/hillclimb.md)
- [investigation.md](skills/poteto-mode/playbooks/investigation.md)
- [multi-phase-plan.md](skills/poteto-mode/playbooks/multi-phase-plan.md)
- [opening-a-pr.md](skills/poteto-mode/playbooks/opening-a-pr.md)
- [orchestrate.md](skills/poteto-mode/playbooks/orchestrate.md)
- [pause-safely.md](skills/poteto-mode/playbooks/pause-safely.md)
- [perf-issue.md](skills/poteto-mode/playbooks/perf-issue.md)
- [prototype.md](skills/poteto-mode/playbooks/prototype.md)
- [refactoring.md](skills/poteto-mode/playbooks/refactoring.md)
- [runtime-forensics.md](skills/poteto-mode/playbooks/runtime-forensics.md)
- [session-pickup.md](skills/poteto-mode/playbooks/session-pickup.md)
- [shipping.md](skills/poteto-mode/playbooks/shipping.md)
- [trace-forensics.md](skills/poteto-mode/playbooks/trace-forensics.md)
- [visual-parity.md](skills/poteto-mode/playbooks/visual-parity.md)
- [worktree-cleanup.md](skills/poteto-mode/playbooks/worktree-cleanup.md)
