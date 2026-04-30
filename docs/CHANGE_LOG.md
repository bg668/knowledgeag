# CHANGE_LOG.md

### 2026-04-30 - LLM 可观测与 Run 复盘

#### 修改目标

为 `/ingest`、`/ask` 建立独立观测日志和 `run_id` 主线，让 TUI 展示 provider 显式返回的 thinking/output，并将 `/review` 改为从观测日志按 `run_id` 自动生成复盘卡。

#### 修改文件

- `src/knowledgeag_card/observability/`：新增独立观测 SQLite、轻量 LLMEvent 和运行上下文。
- `src/knowledgeag_card/runtime/agent_app.py`、`src/knowledgeag_card/runtime/tui_app.py`：为 ingest/ask 包裹 run 生命周期，新增 `/runs`，将 `/review` 改为接收 `run_id`。
- `src/knowledgeag_card/agents/`、`src/knowledgeag_card/runtime/answer_service.py`、`src/knowledgeag_card/runtime/agent_loop.py`：记录 LLM 调用并区分 `thinking_delta` 与 `output_delta`。
- `src/knowledgeag_card/ingestion/ingest_service.py`、`src/knowledgeag_card/memory/task_review_service.py`：记录 source artifact、运行指标，并从观测日志生成复盘 Source / Evidence / Claim / KnowledgeCard。
- `src/knowledgeag_card/app/config.py`、`src/knowledgeag_card/app/container.py`、`config.json.example`：新增 `observability.db_path` 并集中装配 recorder。
- `tests/test_observability.py`、`tests/test_task_review.py`、`tests/test_app_config.py`、`tests/test_knowledge_agent_boundary.py`：覆盖观测库、事件流、run 复盘和配置。
- `docs/REQUIREMENTS.md`、`docs/PROJECT_CONTEXT.md`、`docs/CHANGE_LOG.md`：同步需求、项目地图和变更记录。

#### 未修改范围

未修改 KnowledgeCard / Claim / Evidence / Source 领域字段；未把观测日志写入知识库 SQLite；未改变 ingest / ask 主流程顺序；未引入多 Agent 编排；超大原文仍只记录路径、hash、长度和预览。

#### 验证方式

- `.venv\Scripts\python.exe -m pytest tests\test_observability.py tests\test_app_config.py tests\test_knowledge_agent_boundary.py tests\test_task_review.py -q`
- `.venv\Scripts\python.exe -m pytest tests\test_task_review.py tests\test_quality_metrics.py tests\test_end_to_end.py -q`
- `.venv\Scripts\python.exe -m pytest -q`

#### 剩余风险

真实 paimonsdk provider 的 thinking block 类型仍需用实际模型抽样核验；第一版长期保留观测日志，不提供删除或压缩策略；TUI 展示为轻量预览，不做复杂分屏历史浏览。

### 2026-04-30 - 支持任务后复盘沉淀

#### 修改目标

完成 REQ-KM-014 第一版：支持通过任务复盘 JSON 手动触发写入，将原任务、输出、修改文件、成功经验、失败原因、过程记录和验证证据沉淀为可检索的复盘类 KnowledgeCard。

#### 修改文件

- `src/knowledgeag_card/memory/task_review_service.py`：新增任务复盘写入服务，生成 Source / Evidence / Claim / KnowledgeCard 并入库。
- `src/knowledgeag_card/runtime/agent_app.py`、`src/knowledgeag_card/runtime/tui_app.py`：新增 `review_task` 门面和 `/review <json>` 手动触发命令。
- `src/knowledgeag_card/app/container.py`：集中装配 `TaskReviewService`。
- `src/knowledgeag_card/domain/card_types.py`：补充 `review_card`、`sop`、`pattern` 的别名和检索词。
- `tests/test_task_review.py`：验证复盘卡生成、回源关联和后续检索复用。
- `docs/REQUIREMENTS.md`、`docs/CHANGE_LOG.md`：同步需求状态和变更记录。

#### 未修改范围

未修改现有 ingest / ask 主流程，未新增 SQLite 表或字段，未修改 KnowledgeCard / Claim / Evidence 领域字段，未接入自动 Agent 完成钩子，未引入新的外部依赖。

#### 验证方式

- `uv run pytest tests/test_task_review.py -q`
- `uv run pytest tests/test_end_to_end.py tests/test_financial_card_types.py tests/test_trigger_rules.py -q`
- 按 `.agent/skills/code-review/SKILL.md` 对本次 diff 做后置审查。

#### 剩余风险

第一版只支持人工提供 JSON 文件，不自动从 Agent 执行上下文采集复盘内容；复盘卡内容质量依赖输入 JSON 的完整性；检索仍是简单词法索引，召回质量需要结合后续真实任务样例继续校验。

### 2026-04-30 - 支持金融知识卡片类型

#### 修改目标

完成 REQ-KM-013 第一版：复用 `KnowledgeCard` 通用 schema，通过 `card_type` 支持金融知识类卡片，用于区分事实数据、事件脉络、投资逻辑、操作规则和复盘验证。

#### 修改文件

- `src/knowledgeag_card/domain/card_types.py`：新增金融 card_type 常量、别名和检索词。
- `src/knowledgeag_card/agents/paimon_knowledge_agent.py`、`config.json.example`：同步金融卡片类型枚举与组织 prompt。
- `tests/test_financial_card_types.py`、`tests/test_card_organizer.py`：验证金融类型归一化、检索词命中和 CardOrganizer 接收 LLM 明示类型。
- `docs/PROJECT_CONTEXT.md`、`docs/REQUIREMENTS.md`、`docs/CHANGE_LOG.md`：同步项目地图、需求状态和变更记录。

#### 未修改范围

未新增 SQLite 表或字段；未拆分 `KnowledgeCard` 领域模型；未新增 `SourceType.FINANCE`；未修改入口文件、TUI 命令、导入/问答主流程、Repository、container 装配和存储结构；未做金融内容关键词自动推断。

#### 验证方式

- `.venv\Scripts\python.exe -m pytest tests\test_financial_card_types.py tests\test_card_organizer.py -q`
- `.venv\Scripts\python.exe -m pytest -q`
- 按 `.agent/skills/code-review/SKILL.md` 对本次 diff 做后置审查。

#### 剩余风险

真实 LLM 是否正确选择金融卡片类型仍需人工抽样核验；第一版只通过 prompt 和 card_type 归一化约束 FactCard 等类型，不引入复杂语义校验；检索仍是简单词法索引，金融类型别名只提升相关关键词命中能力。

### 2026-04-30 - 支持代码开发知识卡片类型

#### 修改目标

完成 REQ-KM-012 第一版：复用 `KnowledgeCard` 通用 schema，通过 `card_type` 支持代码开发类卡片，用于表达项目地图、模块职责、入口、修改影响面和设计取舍。

#### 修改文件

- `src/knowledgeag_card/domain/card_types.py`：新增代码开发 card_type 常量、别名和归一化逻辑。
- `src/knowledgeag_card/agents/`、`src/knowledgeag_card/ingestion/card_organizer.py`：向卡片组织节点传入 `source_type`，代码 Source 优先生成或归一为代码开发卡片类型。
- `src/knowledgeag_card/storage/vector_index.py`：将 `card_type` 和代码类型别名纳入检索文本。
- `config.json.example`、`tests/test_card_organizer.py`、`tests/test_code_card_types.py`、`tests/test_end_to_end.py`：同步 prompt 与验证用例。
- `docs/PROJECT_CONTEXT.md`、`docs/REQUIREMENTS.md`、`docs/CHANGE_LOG.md`：同步项目地图、需求状态和变更记录。

#### 未修改范围

未新增 SQLite 表或字段；未拆分 `KnowledgeCard` 领域模型；未修改入口文件、TUI 命令、导入/问答主流程顺序、Repository 存取结构、paimonsdk 工具能力和配置装配方式。

#### 验证方式

- `.venv\Scripts\python.exe -m pytest tests\test_card_organizer.py tests\test_code_card_types.py tests\test_end_to_end.py::test_mock_ingest_generates_code_development_card_type_for_code_source -q`
- `.venv\Scripts\python.exe -m pytest tests\test_card_organizer.py tests\test_code_card_types.py tests\test_end_to_end.py tests\test_source_summary.py -q`
- `.venv\Scripts\python.exe -m pytest -q`
- 按 `.agent/skills/code-review/SKILL.md` 对本次 diff 做后置审查。

#### 剩余风险

真实 LLM 对代码卡片类型的选择仍需人工抽样核验；当前检索仍是简单词法索引，代码类型别名只提升“入口/影响面/决策/模块”等关键词命中能力。

### 2026-04-30 - 建立 test_doc.md 期望输出样例

#### 修改目标

完成 REQ-KM-011：为 `tests/test_data/test_doc.md` 建立人工整理的期望输出样例，并让评估脚本可用该样例做结构化差异检查。

#### 修改文件

- `tests/test_data/expected_test_doc.json`：新增 expected source/cards/claims/evidences 与质量阈值。
- `src/knowledgeag_card/validation/quality_metrics.py`：新增结构化 expected 输出构造和子集差异比较。
- `scripts/evaluate_ingest_quality.py`：将导入结果转换为结构化比较视图后执行 expected 对比。
- `tests/test_quality_metrics.py`、`tests/test_evaluate_ingest_quality.py`：验证结构化 expected 比较、失败差异和 test_doc fixture 可用于脚本。
- `docs/REQUIREMENTS.md`、`docs/CHANGE_LOG.md`：同步 REQ-KM-011 状态和变更记录。

#### 未修改范围

未修改入口启动逻辑、导入主流程顺序、领域模型、配置装配、SQLite schema、Repository、KnowledgeAgent / LLM 行为和 Card/Claim/Evidence 生成逻辑。

#### 验证方式

- `.venv\Scripts\python.exe -m pytest tests\test_quality_metrics.py tests\test_evaluate_ingest_quality.py -q`
- `.venv\Scripts\python.exe -m pytest -q`
- `$env:KNOWLEDGEAG_RUNTIME='mock'; .venv\Scripts\python.exe scripts\evaluate_ingest_quality.py tests\test_data\test_doc.md --expected tests\test_data\expected_test_doc.json`
- 按 `.agent/skills/code-review/SKILL.md` 对本次 diff 做后置审查。

#### 剩余风险

期望样例采用稳定文本子集比较，不绑定随机 ID 和时间；真实 LLM 输出若语义正确但措辞不同，仍需要人工核验后调整 expected 样例。

### 2026-04-30 - 完成质量评估指标

#### 修改目标

完成 REQ-KM-010：为一次导入结果生成质量评估指标，并支持命令行 JSON 报告与 expected 阈值/子集对比。

#### 修改文件

- `src/knowledgeag_card/validation/quality_metrics.py`：新增 card/claim/evidence 计数、绑定完整率、覆盖率、重复 source 数和引用精确率计算。
- `scripts/evaluate_ingest_quality.py`：新增导入质量评估命令，支持 `--expected` 对比并用退出码表达结果。
- `tests/test_quality_metrics.py`、`tests/test_evaluate_ingest_quality.py`：验证指标公式、expected 对比、JSON 输出和失败退出码。
- `docs/PROJECT_CONTEXT.md`、`docs/REQUIREMENTS.md`、`docs/CHANGE_LOG.md`：同步项目地图、REQ-KM-010 状态和变更记录。

#### 未修改范围

未修改入口启动逻辑、TUI 主流程、问答流程、SQLite schema、Repository、KnowledgeAgent / LLM 接口、Card/Claim/Evidence 生成逻辑和配置装配。

#### 验证方式

- `.venv\Scripts\python.exe -m pytest tests\test_quality_metrics.py tests\test_evaluate_ingest_quality.py -q`
- `.venv\Scripts\python.exe -m pytest -q`
- `$env:KNOWLEDGEAG_RUNTIME='mock'; .venv\Scripts\python.exe scripts\evaluate_ingest_quality.py tests\test_data\test_doc.md`

#### 剩余风险

引用精确率是基于 quote、loc 和 content 的确定性近似指标，不能替代人工判断 claim 与 evidence 的语义支撑质量；第一版只评估本次导入结果，不扫描历史数据库全量质量。

### 2026-04-30 - 完成 Source 覆盖率检查

#### 修改目标

完成 REQ-KM-009：导入后生成 Source 章节覆盖报告，记录已覆盖章节、未覆盖章节、card/claim 总数和每张 card 的 claim/evidence 数，并支持 JSON 输出。

#### 修改文件

- `src/knowledgeag_card/validation/source_coverage_checker.py`：新增 Source 章节覆盖率检查。
- `src/knowledgeag_card/domain/models.py`：新增 SourceCoverageReport、CardCoverageSummary，并挂到 IngestResult。
- `src/knowledgeag_card/ingestion/ingest_service.py`、`src/knowledgeag_card/app/container.py`：在导入流程 cards 校验后接入 Source 覆盖检查。
- `scripts/ingest_demo.py`、`src/knowledgeag_card/runtime/tui_app.py`：支持 `--json` 输出和 TUI 章节覆盖概览展示。
- `tests/test_source_coverage_checker.py`、`tests/test_ingest_demo.py`、`tests/test_end_to_end.py`：验证覆盖报告、JSON 数据和端到端返回字段。
- `docs/PROJECT_CONTEXT.md`、`docs/REQUIREMENTS.md`、`docs/CHANGE_LOG.md`：同步项目地图、需求状态和变更记录。

#### 未修改范围

未修改 SQLite schema、Repository、KnowledgeAgent / LLM 接口、Evidence 对齐、Card 组织规则、问答流程和检索流程；Source coverage 仅随本次导入结果返回，不持久化历史报告。

#### 验证方式

- `.venv\Scripts\python.exe -m pytest tests\test_source_coverage_checker.py tests\test_ingest_demo.py tests\test_end_to_end.py -q`
- `.venv\Scripts\python.exe -m pytest -q`
- 手动运行 `scripts\ingest_demo.py <path> --json` 核对 JSON 中 `source_coverage.covered_sections`、`source_coverage.uncovered_sections` 和 `source_coverage.cards`。

#### 剩余风险

章节覆盖依赖 ReadUnit 标题、card applicable_contexts 和 evidence loc 中的 section 信息；代码文件或缺少结构信息的文档只能得到较粗的全文覆盖判断。

### 2026-04-30 - 完成 KnowledgeCard 粒度控制

#### 修改目标

完成 REQ-KM-008：过滤结构化长文中过粗的跨章节全文总览卡，并让既有结构补卡逻辑生成围绕单一章节/主题的 KnowledgeCard。

#### 修改文件

- `src/knowledgeag_card/ingestion/card_organizer.py`：过滤绑定 claims 横跨多个 section 的过粗卡，避免单卡退化为全文总览。
- `src/knowledgeag_card/agents/paimon_knowledge_agent.py`、`config.json.example`：收紧 card 组织 prompt，要求不要合并多个 structure 标题下的 claims。
- `tests/test_card_organizer.py`、`tests/test_end_to_end.py`：验证过粗总览卡被过滤、章节主题卡被补足，最终卡不横跨多个章节。
- `docs/REQUIREMENTS.md`、`docs/CHANGE_LOG.md`：同步 REQ-KM-008 状态和变更记录。

#### 未修改范围

未修改入口文件、SQLite schema、Repository、领域模型、配置装配方式、问答/检索流程；未处理 REQ-KM-009/010。

#### 验证方式

- `.venv\Scripts\python.exe -m pytest tests\test_card_organizer.py tests\test_end_to_end.py -q`
- `.venv\Scripts\python.exe -m pytest -q`
- 按 `.agent/skills/code-review/SKILL.md` 对本次 diff 做后置审查。

#### 剩余风险

无结构信息或 evidence loc 缺少 section 的输入仍只能依赖 3-7 个 core_points 与绑定关系过滤；真实 LLM 主题质量仍需人工抽样核验。

### 2026-04-30 - 完成关键主题覆盖校验

#### 修改目标

完成 REQ-KM-007：导入后提取 Source 标题、结构标题、摘要主题和显式关键术语，校验是否被 KnowledgeCard / Claim 覆盖，并输出 missing_topics。

#### 修改文件

- `src/knowledgeag_card/validation/topic_coverage_checker.py`：新增确定性主题提取和覆盖校验。
- `src/knowledgeag_card/domain/models.py`：新增 TopicCoverageReport，并让 IngestResult 暴露 missing_topics。
- `src/knowledgeag_card/ingestion/ingest_service.py`、`src/knowledgeag_card/app/container.py`：在导入流程 cards 校验后接入覆盖校验。
- `src/knowledgeag_card/runtime/tui_app.py`、`scripts/ingest_demo.py`：导入结果展示 missing topics。
- `tests/test_topic_coverage_checker.py`、`tests/test_end_to_end.py`：验证覆盖、缺失、去重和端到端返回字段。
- `docs/PROJECT_CONTEXT.md`、`docs/REQUIREMENTS.md`、`docs/CHANGE_LOG.md`：同步项目地图、需求状态和变更记录。

#### 未修改范围

未修改 SQLite schema、Repository、KnowledgeAgent / paimonsdk 接口、问答流程、检索排序、Evidence 对齐和 Card 组织规则；未实现 REQ-KM-008 粒度控制或 REQ-KM-009 Source 覆盖率报告。

#### 验证方式

- `.venv\Scripts\python.exe -m pytest tests\test_topic_coverage_checker.py -q`
- `.venv\Scripts\python.exe -m pytest tests\test_end_to_end.py -q`
- `.venv\Scripts\python.exe -m pytest -q`
- 按 `.agent/skills/code-review/SKILL.md` 对本次 diff 做后置审查。

#### 剩余风险

中文关键术语提取偏保守；missing_topics 第一版仅随本次导入结果返回和展示，不回写历史数据、不持久化质量报告。

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
