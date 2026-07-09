# Web Search Skill 项目约束

## 范围

- 本仓库只维护一个 Codex skill，根入口固定为 `SKILL.md`。
- skill 名称、安装目录和虚拟环境名称固定使用 `web-search` / `web-search-skill`。
- 不新增旧目录、旧 skill 名称或历史平台路径兼容。
- 不新增顶层搜索选择行为；质量优先多源并行是唯一默认搜索行为。
- `README.md`、`SKILL.md`、脚本帮助、配置模板和安装说明必须保持同一套当前路径。

## 搜索源

- 默认 source 优先级为 `Grok > Exa > Tavily > OpenAlex`。
- 默认尽可能调用所有已配置源；`--source` 只用于显式收窄源集合。
- `scripts/search.py` 直接调用 Exa、Tavily、Grok 兼容源和 OpenAlex；新增凭证模板项时必须同步实现可调用路径。
- 不保留不可用功能或占位行为；没有实现的能力不得写入 README、配置说明或 CLI 帮助。
- Grok 默认模型保持为 `grok-4.5`，默认通过 OpenAI Responses API 兼容格式调用，除非用户明确要求更换。

## 凭证

- 真实 API key 不得写入仓库、README、示例输出或日志。
- 仓库内只能保留 `TODO_...` 或显然不可用的占位凭证。
- 新增凭证字段时，同步更新 `references/search-credentials.example.json`、`references/configuration.md` 和安装后的凭证模板。

## 验证

- 修改 Python 脚本后至少执行语法编译和占位凭证 smoke test。
- 修改文档后必须做残留命名搜索，确认旧路径、旧名称、不可用行为和错误模型默认值没有回流。
