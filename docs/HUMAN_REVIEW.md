## 人工优先审核文件

每次 AI 修改后，人工可以优先查看以下文件进行验证

### 第一优先级：项目方向和边界

docs/PROJECT_CONTEXT.md
src/knowledgeag_card/domain/models.py
src/knowledgeag_card/domain/enums.py

审核重点：
1. 是否改变 Source / Evidence / Claim / KnowledgeCard 的含义。
2. 是否破坏 Source -> Evidence -> Claim -> Card -> Retrieval -> Validation -> Answer 链路。
3. 是否把临时需求写进稳定项目地图。


### 第二优先级：主流程和装配

src/knowledgeag_card/app/config.py
src/knowledgeag_card/app/container.py
src/knowledgeag_card/runtime/agent_app.py
src/knowledgeag_card/runtime/agent_loop.py
src/knowledgeag_card/ingestion/ingest_service.py
src/knowledgeag_card/validation/validation_service.py

审核重点：
1. 是否把业务逻辑塞进入口或装配层。
2. 是否新增隐式流程。
3. 是否绕过 validator / repository / adapter 边界。
4. 是否导致 mock 和 paimonsdk 两套后端行为不一致。


### 第三优先级：回源和回答质量

src/knowledgeag_card/ingestion/evidence_aligner.py
src/knowledgeag_card/retrieval/trigger_rules.py
src/knowledgeag_card/runtime/prompt_builder.py
src/knowledgeag_card/runtime/response_formatter.py
src/knowledgeag_card/adapters/llm/base.py
src/knowledgeag_card/adapters/llm/paimonsdk_adapter.py
src/knowledgeag_card/adapters/llm/mock_llm.py

审核重点：
1. 是否削弱 evidence 定位能力。
2. 是否让回答在需要依据时只依赖卡片摘要。
3. 是否把 prompt 规则写死到多个位置。
4. 是否对 LLM JSON 输出缺少解析和失败兜底。

### 第四优先级：存储和检索

src/knowledgeag_card/storage/sqlite_db.py
src/knowledgeag_card/storage/source_repository.py
src/knowledgeag_card/storage/evidence_repository.py
src/knowledgeag_card/storage/claim_repository.py
src/knowledgeag_card/storage/card_repository.py
src/knowledgeag_card/storage/vector_index.py
src/knowledgeag_card/retrieval/card_retriever.py

审核重点：
1. 是否破坏已有表结构或历史数据兼容性。
2. 是否改变 JSON 字段读写格式。
3. 是否让检索结果无法追溯到 Claim / Evidence。
4. 是否误把当前关键词检索描述成向量检索或 embedding 检索。