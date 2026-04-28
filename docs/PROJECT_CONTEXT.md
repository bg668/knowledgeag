# PROJECT_CONTEXT.md

## 用途

本文档是 `knowledgeag` / `knowledgeag-card` 的稳定项目地图，供 AI 修改代码前阅读。
只记录长期稳定信息：项目目标、主流程、模块边界、入口文件、领域对象、技术栈和人工审核重点。
不记录：单次需求方案、临时判断、当前差距、修改影响面、风险点。上述内容必须在每次开发前重新阅读代码后分析。

---

## 项目核心功能

`knowledgeag` / `knowledgeag-card` 是一个以 `KnowledgeCard` 为中心的本地知识接入、检索和问答项目。

核心目标：
把原始资料转成可检索、可验证、可回源的知识卡片库。

核心链路：
Source -> Evidence -> Claim -> KnowledgeCard -> Retrieval -> Validation -> Answer

当前能力：
1. 导入本地文件或目录。
2. 生成 Source / Evidence / Claim / KnowledgeCard。
3. 写入本地 SQLite。
4. 按问题检索 KnowledgeCard。
5. 在需要时回拉 Claim / Evidence / Source。
6. 使用 mock 或 paimonsdk 调用 LLM。
7. 提供 Rich TUI、ingest_demo.py、ask_demo.py 入口。

项目边界：
knowledgeag-card 负责知识接入、组织、存储、检索、回源、问答上下文构造。
paimonsdk 负责模型接入、多轮运行时、流式输出。
当前不做大型检索平台、工具平台或多 Agent 编排平台。

项目价值观：
KnowledgeCard 是主检索对象
Claim 是内部支撑对象
Evidence / Source 用于回源
LLM 负责理解
程序负责定位和验证
默认整体阅读，必要时结构化拆分
---

## 当前主流程

### 主流程概述

项目主流程采用“入口门面 + 容器装配 + 服务编排 + 适配器 + 仓储”的组合方式串联。`AgentApp` 作为 Facade，对 TUI 和脚本隐藏内部复杂度，只暴露 `ingest`、`ask`、`stats`；`AppContainer` 负责依赖装配，相当于轻量 Factory / DI Container，把配置、Repository、Service、LLM Adapter 组装起来；`IngestService`、`ValidationService`、`AgentLoop` 作为流程编排层，只表达主链路，不承载底层实现；`LLMAdapter`、Parser 属于 Adapter，用来隔离 paimonsdk、mock、文本解析等外部差异；各类 Repository 负责持久化边界。整体流程是：入口接收命令，门面转交服务，服务按领域链路推进，外部能力通过 Adapter 调用，领域对象通过 Repository 入库或读取，最后由 PromptBuilder 和 AnswerService 生成回答。

### 资料接入流程

入口：
TUI /ingest <path>
scripts/ingest_demo.py
AgentApp.ingest(path)

主流程：
AgentApp.ingest
-> IngestService.ingest_path
-> SourceLoader.load
-> SourceRepository.save
-> ReadPlanner.plan
-> StructuralSplitter.split
-> ClaimExtractor.extract
-> EvidenceAligner.align
-> ClaimBuilder.build
-> ClaimValidator.validate
-> CardOrganizer.organize
-> CardValidator.validate
-> Evidence / Claim / Card repositories save
-> IngestResult

输入：
本地文件或目录路径

输出：
Source / Evidence / Claim / KnowledgeCard 入库，并返回 IngestResult。

关键原则：
先读 Source，再抽 ClaimDraft，再用 anchor quote 回原文定位 Evidence，最后聚合为 KnowledgeCard。

### 问答流程

入口：
TUI /ask <question>
scripts/ask_demo.py
AgentApp.ask(question)

主流程：
AgentApp.ask
-> AgentLoop.ask
-> ValidationService.validate
-> CardRetriever.retrieve
-> CardRanker.rank
-> TriggerRules.evaluate
-> ClaimRetriever.retrieve_for_cards
-> EvidenceFetcher.fetch
-> AnswerService.answer
-> PromptBuilder.build
-> LLMAdapter.answer
-> ResponseFormatter.format
-> answer text

输入：
用户问题

输出：
基于 KnowledgeCard / Claim / Evidence 构造上下文后生成回答。

回源触发条件：
1. 未检索到卡片，或最高分低于阈值。
2. 问题要求依据、来源、原文、evidence、source。
3. 问题涉及代码、修改、API、配置、约束、implement、refactor、code。

回源链路：
KnowledgeCard.claim_ids -> Claim.evidence_ids -> Evidence -> Source

---

## 主要模块关系

主包：

src/knowledgeag_card/

模块边界：
app/         配置加载、依赖装配、运行时后端选择。
domain/      核心领域对象和枚举，不依赖基础设施。
ingestion/   资料接入流程，负责 Source -> Evidence -> Claim -> Card。
retrieval/   卡片检索、排序、回源触发判断。
validation/  组合检索结果、触发规则、Claim、Evidence、Source。
runtime/     TUI、AgentApp、问答循环、Prompt 构造、输出格式化。
storage/     SQLite schema、连接管理、Repository。
adapters/    LLM 适配和文本解析适配。
scripts/     最小演示入口。

依赖方向：
TUI / scripts
-> runtime.AgentApp
-> app.AppContainer
-> ingestion / validation / runtime services
-> storage repositories / adapters

禁止方向：
1. domain 不依赖 storage / adapters / runtime。
2. app 不写业务规则。
3. runtime 不直接写存储细节。
4. adapters 不反向侵入领域模型设计。

---

## 关键入口文件

### 项目启动

pyproject.toml
src/knowledgeag_card/runtime/tui_app.py
src/knowledgeag_card/runtime/agent_app.py
scripts/ingest_demo.py
scripts/ask_demo.py

### 配置装配

src/knowledgeag_card/app/config.py
src/knowledgeag_card/app/container.py
.env.example
config.json.example

### 资料接入

src/knowledgeag_card/ingestion/ingest_service.py
src/knowledgeag_card/ingestion/source_loader.py
src/knowledgeag_card/ingestion/read_planner.py
src/knowledgeag_card/ingestion/structural_splitter.py
src/knowledgeag_card/ingestion/claim_extractor.py
src/knowledgeag_card/ingestion/evidence_aligner.py
src/knowledgeag_card/ingestion/claim_builder.py
src/knowledgeag_card/ingestion/card_organizer.py

### 检索问答

src/knowledgeag_card/runtime/agent_loop.py
src/knowledgeag_card/validation/validation_service.py
src/knowledgeag_card/retrieval/card_retriever.py
src/knowledgeag_card/storage/vector_index.py
src/knowledgeag_card/retrieval/trigger_rules.py
src/knowledgeag_card/runtime/prompt_builder.py
src/knowledgeag_card/runtime/answer_service.py
src/knowledgeag_card/runtime/response_formatter.py

### LLM 与存储

src/knowledgeag_card/adapters/llm/base.py
src/knowledgeag_card/adapters/llm/mock_llm.py
src/knowledgeag_card/adapters/llm/paimonsdk_adapter.py
src/knowledgeag_card/storage/sqlite_db.py
src/knowledgeag_card/storage/source_repository.py
src/knowledgeag_card/storage/evidence_repository.py
src/knowledgeag_card/storage/claim_repository.py
src/knowledgeag_card/storage/card_repository.py

---

## 核心领域对象

定义位置：

src/knowledgeag_card/domain/models.py
src/knowledgeag_card/domain/enums.py

### Source

原始资料来源。
```text
source_id       src_<uuid>
type            markdown / text / code / unknown
title           当前来自文件名 stem
uri             本地文件绝对路径
version_id      当前内容 sha256
imported_at     导入时间
source_summary  LLM 生成的来源摘要，可为空
```

### Evidence

从 Source 截取的可定位证据窗口。
```text
evidence_id          ev_<uuid>
source_id            所属 Source
source_version       对应 Source.version_id
loc                  section/chars 或 file/lines
content              证据窗口文本
normalized_content   标准化证据文本
```

### Claim

由 Evidence 支撑的可复用判断。

```text
claim_id       clm_<uuid>
text           判断文本
evidence_ids   支撑证据列表
status         supported / conflicted / obsolete
updated_at     更新时间
```

### KnowledgeCard

当前系统主要检索对象。

```text
card_id               card_<uuid>
title                 标题
card_type             principle / method / pattern / sop / analysis / knowledge 等
summary               摘要
applicable_contexts   适用场景
core_points           3-7 个核心点
practice_rules        实践规则
anti_patterns         反模式
claim_ids             支撑 Claim 列表
evidence_ids          支撑 Evidence 列表
tags                  标签
updated_at            更新时间
```

### 过程对象

```text
ReadUnit          模型读取单元。
EvidenceAnchor    LLM 给出的原文锚点。
ClaimDraft        LLM 抽取的 Claim 草稿。
ReadPlan          whole_document 或 structured。
IngestResult      单次接入结果。
RetrievedCard     检索命中的卡片及分数。
ValidationResult  问答前上下文。
StorageStats      数据库统计。
```

### 枚举

```text
SourceType    markdown / text / code / unknown
ClaimStatus   supported / conflicted / obsolete
ReadMode      whole_document / structured
TriggerType   conflict / uncertainty / citation_required / code_task
```

---

## 当前技术栈

Python >= 3.11
setuptools + pyproject.toml
Rich
python-dotenv
OpenAI compatible client
paimonsdk，可选
SQLite
pytest

运行配置：
.env                 存放 API key。
config.json          存放 storage、models、retrieval、ingest、system_prompts。
KNOWLEDGEAG_RUNTIME  paimon | mock

LLM 后端：
mock_llm.py             本地 mock，跑通流程。
paimonsdk_adapter.py    使用 paimonsdk + OpenAI 兼容接口。

模型 API 类型：
chat.completions
responses

当前存储：
data/storage/knowledgeag.sqlite3
sources
evidences
claims
cards

当前检索：
SimpleCardIndex
-> 读取全部 cards
-> 拼接 title / summary / core_points / tags / applicable_contexts
-> 正则分词
-> Counter 统计
-> cosine-like 打分
-> 返回 top_k

当前检索不是向量数据库，也不是 embedding 检索。

当前解析器：
MarkdownParser    按 Markdown 标题拆分。
TextParser        按空行块拆分。
CodeParser        按 Python 风格 def / class 拆分。

---

## 架构原则

1. 主流程必须显式可读。
2. 领域模型必须保持稳定。
3. 外部依赖必须集中装配。
4. 入口文件不写业务逻辑。
5. 调度层只表达流程，不塞实现细节。
6. 回源链路不能被绕开。
7. LLM 输出必须经过解析、对齐、校验后入库。
8. AI 修改必须小步、可审、可验、可回滚。

---

## AI 修改前必须重新分析

每次开发前，AI 不得只依赖本文档，必须重新阅读当前代码并输出：
固定原则：

先有地图，再看现场；先定边界，再动手；先小范围施工，再验收沉淀。