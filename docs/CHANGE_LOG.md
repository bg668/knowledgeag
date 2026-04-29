# CHANGE_LOG.md

### 2026-04-30 - 完成基于结构的多 KnowledgeCard 组织

#### 修改目标

完成 REQ-KM-006：让结构化 Source 按标题、章节、主题块生成多张主题 KnowledgeCard，避免长文只保留唯一全文卡。

#### 修改文件

- `src/knowledgeag_card/ingestion/structural_splitter.py`：为结构单元补充稳定的 section/index loc_hint。
- `src/knowledgeag_card/ingestion/card_organizer.py`：结合 ReadUnit 与 Evidence section 信息组织主题卡，并为缺失章节补充结构卡。
- `src/knowledgeag_card/ingestion/ingest_service.py`：向 CardOrganizer 传入结构单元和 evidences，不改变接入流程顺序。
- `src/knowledgeag_card/agents/`、`config.json.example`：扩展 organize_cards 输入，强化结构化多卡 prompt 与 mock 行为。
- `tests/test_card_organizer.py`、`tests/test_end_to_end.py`、`tests/test_source_summary.py`：验证结构上下文传递、多章节卡生成和测试替身兼容。
- `docs/PROJECT_CONTEXT.md`、`docs/REQUIREMENTS.md`、`docs/CHANGE_LOG.md`：同步项目地图、需求状态和变更记录。

#### 未修改范围

未修改入口文件、领域模型、SQLite schema、Repository、检索问答流程、配置装配逻辑；未实现 REQ-KM-007/008 的覆盖率检查或粒度控制完整能力。

#### 验证方式

- `uv run pytest tests/test_card_organizer.py tests/test_end_to_end.py -q`
- `uv run pytest -q`
- 按 `.agent/skills/code-review/SKILL.md` 对本次 diff 做后置审查。

#### 剩余风险

真实 LLM 仍可能输出不理想的主题划分；当前实现会基于结构信息补足可验证主题卡，但没有引入覆盖率报告或复杂粒度评估。

### 2026-04-30 - 调整 KnowledgeCard 组织需求

#### 修改目标

将 REQ-KM-006、REQ-KM-007、REQ-KM-008 调整为基于结构的多 KnowledgeCard 组织、关键主题覆盖校验和 KnowledgeCard 粒度控制。

#### 修改文件

- `docs/REQUIREMENTS.md`：替换三项需求的名称、背景、描述、验收标准、优先级、影响对象和备注。
- `docs/CHANGE_LOG.md`：按模板记录本次需求文档调整。

#### 未修改范围

未修改入口文件、主流程、领域模型、配置装配、业务代码、测试代码和其他需求编号。

#### 验证方式

人工核对 `docs/REQUIREMENTS.md` 中 REQ-KM-006 到 REQ-KM-008 的内容与用户描述一致，并检查 Markdown 表格仍保持单行表格格式。

#### 剩余风险

本次只调整需求文档，未实现对应导入、覆盖校验或粒度控制逻辑。

### 2026-04-29 - Evidence 拆分为 Quote + Context

#### 修改目标

完成 REQ-KM-05：将 Evidence 从单一上下文窗口拆为最小原文引用和前后辅助上下文，并让 loc 指向 quote 本身。

#### 修改文件

- `src/knowledgeag_card/domain/models.py`：为 Evidence 增加 `evidence_quote`、`context_before`、`context_after`，保留 `content` 兼容旧调用。
- `src/knowledgeag_card/storage/sqlite_db.py`、`src/knowledgeag_card/storage/evidence_repository.py`：扩展 evidences 表，旧数据迁移时用 `content` 回填 `evidence_quote`。
- `src/knowledgeag_card/ingestion/evidence_aligner.py`、`src/knowledgeag_card/runtime/prompt_builder.py`：生成 quote/context，并在回源 prompt 中优先展示 quote。
- `tests/test_evidence_quote_context.py`、`tests/test_source_versioning.py`、`tests/test_end_to_end.py`：验证文本/代码定位、旧表迁移和端到端 evidence 字段。
- `docs/PROJECT_CONTEXT.md`、`docs/REQUIREMENTS.md`、`docs/CHANGE_LOG.md`：同步项目地图、需求状态和变更记录。

#### 未修改范围

未修改入口文件、导入主流程顺序、问答主流程顺序、配置装配、KnowledgeAgent 接口、Claim/Card 绑定逻辑和检索排序逻辑。

#### 验证方式

- `uv run pytest tests/test_evidence_quote_context.py tests/test_source_versioning.py tests/test_end_to_end.py -q`
- `uv run pytest -q`

#### 剩余风险

旧库中的历史 evidence 只能把旧 `content` 整体回填为 `evidence_quote`，无法自动恢复真实的 quote/context 边界；新导入数据会生成拆分后的字段。

### 2026-04-29 - 修复 Card-Claim-Evidence 绑定关系

#### 修改目标

完成 REQ-KM-04：确保 card 的每个 core_point 逐字绑定唯一 claim，并同序写入 claim_ids；过滤重复 claim 集合和缺少 evidence 的 claim/card。

#### 修改文件

- `src/knowledgeag_card/ingestion/card_organizer.py`：收紧 card 输出过滤，要求所有 core_points 都能唯一匹配非空 evidence 的 claim，并按 core_points 顺序生成 claim_ids。
- `tests/test_card_organizer.py`：验证逐点绑定、同序追溯、重复 claim 集合过滤、空 evidence claim 过滤。
- `tests/test_end_to_end.py`：验证端到端生成的 cards 满足 core_points 与 claim_ids 同序一致，且 claim evidence 非空。
- `docs/REQUIREMENTS.md`：将 REQ-KM-04 标记为已完成、待人工核验。
- `docs/CHANGE_LOG.md`：记录本次修改。

#### 未修改范围

未修改入口文件、导入主流程顺序、领域模型、SQLite schema、配置装配、检索问答流程；未新增 `core_point_claim_ids` 字段。

#### 验证方式

- `uv run pytest tests/test_card_organizer.py tests/test_end_to_end.py -q`
- `uv run pytest -q`

#### 剩余风险

真实 LLM 若输出 paraphrase 的 core_points 会被整卡过滤；这是本次按数据一致性优先做出的约束。

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
