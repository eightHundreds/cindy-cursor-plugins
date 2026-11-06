# Cursor Skills for Cindy

从 [cursor/plugins](https://github.com/cursor/plugins) 适配的 **Cindy 自定义插件市场**。这是独立的社区适配项目，与 Cursor、Cindy 官方无隶属关系。

首批提供 **7 个插件、18 个 Skill**，来源于上游 130 个插件中的 6 个。完整范围、未适配条目及原因见 [兼容性报告](catalog/REPORT.md)。这里提供可移植的工作流和开发指南；MCP、Cursor hooks、rules、内置 Canvas 与云 Agent 功能均需原生适配，未作为可用功能发布。

## 在 Cindy 中使用

已验证 Cindy **0.1.126** 的官方清单校验器及 Forge 打包。`minCindyVersion` 保守声明为这一已验证版本，不代表 Skills 最早于该版本引入。

1. 打开 Cindy 的「插件」页，选择「添加插件市场」。
2. 选择 Git 来源，填入仓库地址：

   ```text
   https://github.com/eightHundreds/cindy-cursor-plugins
   ```

3. Git 引用填 `main`，稀疏路径留空，添加后选择所需插件安装。
4. 阅读 Cindy 的安装权限说明。安装并启用后，在任务中使用对应的 `/Skill名称`。

仓库同时提供 `.agents/plugins/marketplace.json` 与 `.cursor-plugin/marketplace.json`，均指向仓库内带有效 `ghost.json` 的普通目录，无 submodule 依赖。请添加**仓库 URL**，而非 JSON 文件的网页 URL。

| 插件 | Skills | 用途 |
| --- | --- | --- |
| CLI for Agents | `/cli-for-agents` | 设计可供 Agent 可靠调用的 CLI |
| Teaching | `/create-learning-path`、`/run-learning-retrospective` | 学习路线与学习复盘 |
| Cursor SDK Guide | `/cursor-sdk` | 为外部 `@cursor/sdk` 编写集成代码 |
| Origin API Guides | `/origin-api`、`/port-github-app-to-origin` | 查阅 Origin API、规划 GitHub App 移植 |
| Grok Voice Guides | `/add-voice`、`/add-dictation`、`/add-read-aloud`、`/debug-voice` | 为用户自己的应用编写语音功能 |
| pstack Types | `/typescript-best-practices` 及 3 个类型和边界原则 Skill | 类型设计与边界校验 |
| pstack Quality | 4 个领域建模、行为测试、根因与幂等原则 Skill | 代码质量实践 |

完整 Skill 名称见各目录的 `ghost.json`。每个插件最多 4 个 Skill；通过 Skill 斜杠命令使用，因此没有额外的插件级 `$command`。

SDK、Origin、Grok Voice 是**开发指南**，运行外部服务需要另行获取账号、API 凭证与应用依赖。它们不会将 Cindy 任务转交给 Cursor，也不会给 Cindy 界面添加语音控件。保留的上游 API 示例可能随服务变化，使用时须核对最新官方文档。不同 Agent 引擎对上游附加 frontmatter 的处理可能不同。

## 自动跟随上游

[GitHub Actions](https://github.com/eightHundreds/cindy-cursor-plugins/actions/workflows/catalog.yml) 每 6 小时检查 `cursor/plugins` 的 `main`（UTC `00:17 / 06:17 / 12:17 / 18:17`）；也可以在该工作流页面点击 **Run workflow** 手动同步。

- 自动更新 `policy.json` 中已纳入的 Skills、同目录参考文件、许可与来源记录，同时刷新全部上游条目的兼容性报告。
- 插件内容、来源证据、适配规则或可执行位变化时自动增加补丁版本；上游无关文件变化时保持插件版本。没有变化就不提交。
- 上游删除插件或选定 Skill 后，从可安装目录撤下对应包，保留版本记录以避免未来恢复时倒退。已安装副本不会被远程卸载。
- 新插件、新 Skill、MCP 或新增原生能力不会自动纳入安装范围；先审查再修改 `policy.json`。对于这些新增条目，仓库会持续记录其存在和未适配状态。
- 转换、测试或官方清单校验失败时，工作流失败，不推送生成结果；远端保留上次成功的市场。精确文本适配不再匹配时也停止同步。许可证按已审查全文的 SHA-256 固定，任何变动都需人工复核后更新允许列表。

这是 **GitHub 定时检查**，并非即时 webhook；运行时间与成功率取决于 GitHub Actions。GitHub 可能在公开仓库长期无活动后暂停计划任务，维护者可在 Actions 页面重新启用。工作流通过仓库自带的 `GITHUB_TOKEN` 提交，不需要用户配置 PAT；仓库或组织策略若禁止 Actions 写入，需在 GitHub 设置中允许该工作流的 `contents: write` 权限。

通过 Cindy 自定义市场安装的插件会绑定该市场来源；Cindy 的后续更新遵循宿主的市场刷新与权限确认规则。手工导入本地 `.cindy` 不会自动绑定这个仓库。

## 来源、修改与信任范围

每个插件都保留上游 MIT `LICENSE`，并附带：

- `UPSTREAM.json`：仓库、内容来源 commit、路径，以及原始/分发版 `SKILL.md` 的 SHA-256。
- `ADAPTATION.md`：移植范围、修改说明和依赖限制。
- `ghost.json`：Cindy schema v3 清单，准确列出所含 Skills。

当前正文修改仅为 Teaching 的通用提问工具名称适配；Cursor SDK 的过长 frontmatter description 缩短到 Cindy 的限制内。其余入选 Skills 保留原文。未复制上游市场的官方身份声明、未导入 MCP 登录配置、未执行上游 hooks 或安装脚本。

**Skills 由主 Agent 使用用户权限执行，随插件全局启用，在所有项目可见，不受插件 JS 沙箱限制。** 自动同步也会更新这些指令。请按这个信任范围选择安装；仅在某个工作目录停用插件不会隐藏其 Skills，需全局停用或卸载。首次安装及新增权限由 Cindy 按宿主规则征求确认。

## 本地维护与验证

需要 Python 3.12+、Node.js 22+ 和 Git。转换器只从上游 Git 的提交对象读取文件，不读取未提交工作区内容、不运行上游代码，并拒绝越界路径、符号链接、submodule 与超限文件。

```bash
git clone https://github.com/eightHundreds/cindy-cursor-plugins.git
cd cindy-cursor-plugins
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm ci --ignore-scripts
git clone https://github.com/cursor/plugins.git .cache/upstream
.venv/bin/python scripts/sync.py --upstream .cache/upstream
.venv/bin/python scripts/sync.py --upstream .cache/upstream --check
.venv/bin/python -m unittest discover -s tests -v

git clone --branch v0.1.126 --depth 1 https://github.com/makecindy/cindy.git .cache/cindy
git -C .cache/cindy rev-parse HEAD
# 必须对应 5ab30ec856e57e2ae8944657e9e2d69264c672f5
npm run validate:host -- .cache/cindy
```

只提交成功验证后的 `catalog/`、两个市场清单和 `sync-state.json`。`.cindy` 是本机验证产物，不提交；Cindy 从自定义市场的插件源码目录打包安装。新增包须维护唯一且不超过 32 字符的 id，提供明确的移植说明并遵守每插件 4 个 Skill 的限制。

协议依据：[Cindy v0.1.126 清单校验器](https://github.com/makecindy/cindy/blob/5ab30ec856e57e2ae8944657e9e2d69264c672f5/packages/plugin-protocol/src/manifest.ts)、[自定义市场发现](https://github.com/makecindy/cindy/blob/5ab30ec856e57e2ae8944657e9e2d69264c672f5/apps/desktop/src/main/plugin-market/sources/discover.ts)、[市场安装打包](https://github.com/makecindy/cindy/blob/5ab30ec856e57e2ae8944657e9e2d69264c672f5/apps/desktop/src/main/plugin-market/install.ts)。

本仓库没有向 Cindy 官方公共市场提审；使用入口是上面的 Git 自定义市场。首批全部插件已使用 Cindy Forge 实际打包校验，未安装到作者账号；外部 API 功能未进行账号集成测试。
