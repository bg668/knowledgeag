# CHANGE_LOG.md

### 2026-04-28 - REQ-KM-001 Source 幂等导入与版本管理验收

#### 修改目标

检查 `docs/REQUIREMENTS.md` 中 `REQ-KM-001` 是否已完成，并在合格后记录验收结果。

#### 修改文件

- `CHANGE_LOG.md`：记录 `REQ-KM-001` 验收结果、验证方式和剩余风险。

#### 未修改范围

未修改入口文件、主流程、领域模型、配置装配、存储/导入/检索代码和测试代码。

#### 验证方式

- `uv run pytest -q tests\test_source_versioning.py`：3 passed。
- `uv run pytest -q`：9 passed。

#### 剩余风险

本次仅基于现有测试和代码核对确认需求完成；未额外验证历史生产数据库迁移后的真实数据兼容性。

### 2026-04-28 - REQ-KM-002 支持 SourceSummary

#### 修改目标

为每个有效输入文档导入后生成稳定、非空的文档级 `source_summary`，覆盖主题、核心观点、适用场景和主要结构，并避免重复导入覆盖已有摘要。

#### 修改文件

- `src/knowledgeag_card/ingestion/source_summarizer.py`：集中生成、归一化和兜底 SourceSummary。
- `src/knowledgeag_card/ingestion/ingest_service.py`：在导入主流程中显式加入 SourceSummary 步骤。
- `src/knowledgeag_card/adapters/llm/base.py`、`mock_llm.py`、`paimonsdk_adapter.py`：新增 SourceSummary LLM 接口和 mock/paimon 实现。
- `src/knowledgeag_card/app/config.py`、`config.json.example`、`src/knowledgeag_card/app/container.py`：增加可选 prompt 配置并装配 SourceSummarizer。
- `tests/test_source_summary.py`：验证结构化摘要、复用已有摘要和空结果兜底。

#### 未修改范围

未修改入口文件、领域模型字段、SQLite schema、检索问答流程、Claim/Evidence/Card schema。

#### 验证方式

- `uv run pytest -q tests\test_source_summary.py`：3 passed。
- `uv run pytest -q tests\test_end_to_end.py`：1 passed。
- `uv run pytest -q`：12 passed。

#### 剩余风险

paimon 后端的摘要质量依赖实际模型输出；当前通过 JSON 解析和确定性兜底保证非空与结构稳定，但未做人工语义质量评估。
