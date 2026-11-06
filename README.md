# pstack for Cindy

这是 [cursor/plugins 的 pstack](https://github.com/cursor/plugins/tree/main/pstack) 面向 Cindy 的非官方适配，自定义市场只提供一个 `pstack` 插件。上游由 Lauren Tan 创作，采用 MIT 许可证；随包保留原许可、作者署名和来源提交。仓库名称保持不变，并不表示与 Cursor 或 Cindy 官方有关联。

## 安装和使用

1. 在 Cindy「插件」页选择「添加插件市场」，使用 Git 地址 `https://github.com/eightHundreds/cindy-cursor-plugins`，引用填 `main`，稀疏路径留空。
2. 阅读插件介绍和权限后安装并启用 `pstack`。
3. 在新任务中输入 `/poteto-mode`，再描述需求，例如「实现一个小功能」或「修复这个错误」。也可以通过自然语言描述需要的工作流，由入口路由到对应参考文件。命令与其他技能同名时，界面可能显示带插件前缀的名称。

只注册一个入口 Skill。其余上游子技能是随包指令资料，没有各自的斜杠命令，也不会按各自描述被单独自动召回；是否选对资料仍取决于当前 Agent 的判断。技能由主 Agent 以用户权限执行，全局启用后对所有项目和会话生效，不受插件 JavaScript 沙箱约束。请在安装和更新前审阅随包内容。

## 收录清单

以下是当前上游版本的完整技能名称；入口为 `poteto-mode`，其余均为参考资料：

<!-- pstack-skills:start -->
`architect`、`arena`、`automate-me`、`benchmark-checklist`、`blast-radius`、`bro`、`correct`、`create-formal-verification-skill`、`create-verification-skill`、`figure-it-out`、`how`、`in-your-own-words`、`interrogate`、`ketchup`、`ketchup-video`、`maintain-formal-verification-skill`、`maintain-verification-skill`、`make-bot-ui`、`no-comments`、`poteto-help`、`poteto-mode`、`principle-attack-the-premise`、`principle-boundary-discipline`、`principle-build-the-lever`、`principle-encode-lessons-in-structure`、`principle-exhaust-the-design-space`、`principle-experience-first`、`principle-explain-the-number`、`principle-fix-root-causes`、`principle-foundational-thinking`、`principle-guard-the-context-window`、`principle-laziness-protocol`、`principle-make-operations-idempotent`、`principle-migrate-callers-then-delete-legacy-apis`、`principle-minimize-reader-load`、`principle-model-the-domain`、`principle-never-block-on-the-human`、`principle-outcome-oriented-execution`、`principle-prove-it-works`、`principle-redesign-from-first-principles`、`principle-separate-before-serializing-shared-state`、`principle-sequence-verifiable-units`、`principle-subtract-before-you-add`、`principle-test-behavior-not-implementation`、`principle-type-system-discipline`、`recall`、`reflect`、`setup-pstack`、`sharpen`、`show-me-your-work`、`statechart`、`swarm`、`tdd`、`teach`、`technical-writing`、`typescript-best-practices`、`unslop`、`why`。
<!-- pstack-skills:end -->

入口附带的流程文档：

<!-- pstack-playbooks:start -->
`authoring-a-skill.md`、`autonomous-run.md`、`autopilot-full.md`、`autopilot-stack.md`、`babysit.md`、`bug-fix.md`、`eval.md`、`feature.md`、`hillclimb.md`、`investigation.md`、`multi-phase-plan.md`、`opening-a-pr.md`、`orchestrate.md`、`pause-safely.md`、`perf-issue.md`、`prototype.md`、`refactoring.md`、`runtime-forensics.md`、`session-pickup.md`、`shipping.md`、`trace-forensics.md`、`visual-parity.md`、`worktree-cleanup.md`。
<!-- pstack-playbooks:end -->

另有入口参考文档 `bugbot-triage.md`，以及子代理提示词 `poteto-agent.md` 和 `comment-sicko.md`。具体路径和适配内容见[适配报告](catalog/REPORT.md)及插件详情。

## 与上游的区别

- 子技能移到入口目录作为参考文件，保留入口路由和逐项用途说明；入口及内部引用按 Cindy 安装路径调整。
- `cursor-team-kit` 的 `deslop` 用 pstack 自带的 `unslop` 和 `no-comments` 代替；Cursor 的终端、浏览器、提问及技能创建依赖对应 Cindy 可用工具和指南。
- 上游代理定义不会由 Cindy 自动加载：需要委派时，将随包代理提示词和通过 `realpath` 获得的入口绝对路径交给通用子代理。后台执行和并行数量取决于当前引擎。
- babysit 与 shipping 的 `gh` 流程保留；Cursor Bugbot 部分仅适用于仓库确实安装了 Cursor Bugbot 的情况。
- 未打包上游的 `automations/benny`、`docs/` 和 `statechart/scripts/test/` 测试资料；因此包内不能运行依赖这些测试资料的上游测试命令。随包文件及适配取舍见[适配报告](catalog/REPORT.md)。

此仓库不提供 Cursor 原生功能，也不能保证每个引擎、外部服务或项目都具备上游流程需要的工具、依赖和权限。GitHub 相关流程需要本机 `gh` 和相应仓库权限。

## 自动同步和维护

[GitHub Actions](https://github.com/eightHundreds/cindy-cursor-plugins/actions/workflows/catalog.yml) 每 6 小时检查上游，也支持手动运行。同步只处理 `cursor/plugins` 的 `pstack/`；上游相关内容没有变化时不提交。上游许可证变化、适配替换未命中、路径不安全、包超限、测试或宿主校验失败时停止发布，保留上一次成功结果。GitHub 可能暂停长期无活动的定时工作流，维护者可在 Actions 页面重新启用。

转换器从上游 Git 提交对象读取内容，不执行上游代码。执行本地维护需要 Python、Node.js、Git 和该仓库已锁定的依赖：

```bash
python -m pip install -r requirements.txt
npm ci --ignore-scripts
python scripts/sync.py --upstream /path/to/cursor-plugins
python scripts/sync.py --upstream /path/to/cursor-plugins --check
python -m unittest discover -s tests -v
npm run validate:host -- /path/to/cindy-v0.1.126
```

转换前请先审阅 `policy.json`。来源与许可记录、完整分发清单及具体限制见 [适配报告](catalog/REPORT.md) 和插件目录。

**旧版用户注意**：旧市场中的七个 Cursor 适配插件会从市场列表消失。已安装的旧副本不会因市场条目移除而自动卸载；其后续更新取决于 Cindy 的来源及更新规则。新 `pstack` 插件需要单独安装。
