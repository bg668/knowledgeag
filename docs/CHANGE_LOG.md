# CHANGE_LOG.md

### 2026-04-29 - 支持主题化 KnowledgeCard

#### 修改目标

完成 REQ-KM-03：让 KnowledgeCard 按主题生成，每张卡保持 3-7 个核心点，长文不再只生成单张摘要式 card。

#### 修改文件

- `src/knowledgeag_card/ingestion/card_organizer.py`：过滤不满足 3-7 个 core_points 的卡，移除无匹配 claim 时固定复用前 3 条 claim 的兜底。
- `src/knowledgeag_card/agents/mock_knowledge_agent.py`：mock 后端按 claim 顺序稳定拆成多张 3-7 点主题卡。
- `src/knowledgeag_card/agents/paimon_knowledge_agent.py`、`config.json.example`：强化 card 组织 prompt，要求长文/多 claim 拆成主题卡。
- `tests/test_card_organizer.py`、`tests/test_end_to_end.py`：验证主题卡过滤、多卡生成和 core_points 数量约束。
- `docs/REQUIREMENTS.md`：将 REQ-KM-03 标记为已完成、待人工核验。

#### 未修改范围

未修改入口文件、导入主流程、领域模型、配置装配、SQLite schema、检索问答流程；未实现 REQ-KM-004 的逐 core_point 证据绑定重构。

#### 验证方式

- `.venv\Scripts\python.exe -m pytest tests\test_card_organizer.py tests\test_end_to_end.py -q`
- `.venv\Scripts\python.exe -m pytest -q`

#### 剩余风险

主题划分第一版由 mock 的稳定分组和 paimon prompt 约束完成，真实模型输出的主题质量仍需人工核验；每个 core_point 精确绑定 claim/evidence 留给 REQ-KM-004。

### 2026-04-29 - 收敛 code-review 技能

#### 修改目标

将外部 `code-review` skill 改为适配 `knowledgeag` 的后置代码审查技能，避免与 `AGENTS.md` 的修改流程、`docs/PROJECT_CONTEXT.md` 的项目地图和模块边界冲突。

#### 修改文件

- `.claude/skills/code-review/SKILL.md`：移除 Hindsight 项目专用规则，改为审查 `AGENTS.md`、`docs/PROJECT_CONTEXT.md`、当前代码、模块边界、回源链路、验证方式和变更记录。
- `docs/CHANGE_LOG.md`：按 `docs/CHANGE_LOG.example.md` 记录本次技能修改。

#### 未修改范围

不修改项目代码、入口文件、主流程、领域模型、配置装配、存储 schema、测试体系和业务逻辑。

#### 验证方式

人工核对技能内容：只做修改后审查，不自动修复；不覆盖 `AGENTS.md` 的修改前确认和修改后汇报；审查项与 `knowledgeag` 的主链路、模块边界、变更记录要求一致。

#### 剩余风险

未在真实仓库执行 `git diff`、`pytest` 或脚本验证；合入项目后需要再用该 skill 对一次实际变更进行审查验证。

### 2026-04-29 - 收口 KnowledgeAgent 边界

#### 修改目标

完成 REQ-KM-015 的边界优先版本：将知识任务调用从底层 LLM Adapter 收口到 `KnowledgeAgent` 接口，并为 paimonsdk 默认实现增加内部工具注册与节点级工具权限配置。

#### 修改文件

- `src/knowledgeag_card/agents/`：新增 `KnowledgeAgent`、`MockKnowledgeAgent`、`PaimonKnowledgeAgent`。
- `src/knowledgeag_card/tools/registry.py`：新增内部 `ToolRegistry`，只解析 knowledgeag 已注册工具。
- `src/knowledgeag_card/app/config.py`、`config.json.example`：新增 `knowledge_agent` 配置。
- `src/knowledgeag_card/app/container.py`、`ingestion/`、`runtime/answer_service.py`：将主流程依赖从 `llm` 切换为 `knowledge_agent`。
- `src/knowledgeag_card/adapters/llm/`：保留旧 import 路径为兼容薄壳。
- `tests/test_app_config.py`、`tests/test_knowledge_agent_boundary.py`：验证配置、工具权限、paimon 初始化失败不静默 fallback。

#### 未修改范围

未修改入口文件、导入/问答主流程顺序、领域模型、存储 schema、检索逻辑和外部 skill 注册能力。

#### 验证方式

- `uv run pytest tests\test_app_config.py tests\test_knowledge_agent_boundary.py -q`
- `uv run pytest -q`

#### 剩余风险

`ToolRegistry` 第一版只提供内部注册与权限边界，尚未实现具体检索/回源工具；`max_steps` 作为 knowledgeag 节点元数据传给 paimonsdk，单轮模式当前通过 `allow_tools=false` 确保不注册工具。
