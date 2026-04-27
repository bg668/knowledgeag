# PROJECT_CONTEXT.md

> 本文档用于给后续 AI 和开发人员提供项目地图。它只记录当前相对稳定的项目上下文：核心功能、主流程、模块关系、入口文件、领域对象、技术栈。具体需求差距、修改影响面、风险点应在每次开发前重新分析。

## 1. 当前项目核心功能

`knowledgeag` / `knowledgeag-card` 是一个以 KnowledgeCard 为中心的本地知识接入、检索和问答项目。

核心目标不是生成传统 Wiki 页面，而是把输入资料转成可回源的知识结构：

```text
Source -> Evidence -> Claim -> KnowledgeCard -> Retrieval -> Validation -> Answer
```

当前能力：

1. 导入本地文件或目录中的资料。
2. 根据文件内容生成 `Source`、`Evidence`、`Claim`、`KnowledgeCard`。
3. 将上述对象写入本地 SQLite 数据库。
4. 基于问题检索相关 KnowledgeCard。
5. 按规则判断是否需要回拉 Claim、Evidence、Source。
6. 使用 mock 或 paimonsdk 作为 LLM 后端生成回答。
7. 提供 Rich TUI 命令行交互，以及 `ask_demo.py`、`ingest_demo.py` 脚本入口。

当前项目本质：

```text
一个最小可运行的“带 evidence 回源能力的知识卡片库”。
```

它的设计边界比较克制：

```text
知识内核负责：导入、抽取、对齐、组织、存储、检索、回源。
paimonsdk 负责：模型接入、多轮运行时、流式输出。
当前没有把检索系统、工具系统、多 Agent 编排揉成一个大平台。
```

## 2. 当前主流程

当前主流程分为两条：资料接入流程和问答流程。

### 2.1 资料接入流程

入口：

```text
TUI /ingest <path>
scripts/ingest_demo.py
AgentApp.ingest(path)
```

主链路：

```text
AgentApp.ingest
  -> AppContainer.ingest_service.ingest_path
    -> SourceLoader.load
    -> SourceRepository.save
    -> ReadPlanner.plan
    -> StructuralSplitter.split        # 仅在 structured 模式触发
    -> ClaimExtractor.extract          # 调用 LLM / mock 生成 ClaimDraft + source summary
    -> SourceRepository.save           # 如有 summary，更新 Source
    -> EvidenceAligner.align           # 用 anchor quote 回原文定位 evidence window
    -> ClaimBuilder.build              # ClaimDraft + evidence_ids -> Claim
    -> ClaimValidator.validate
    -> CardOrganizer.organize          # 调用 LLM / mock 把 Claims 聚合为 KnowledgeCard
    -> CardValidator.validate
    -> EvidenceRepository.save_many
    -> ClaimRepository.save_many
    -> CardRepository.save_many
    -> IngestResult
```

输入：

```text
本地文件或目录路径
```

输出：

```text
Source / Evidence / Claim / KnowledgeCard 入库
IngestResult 返回本次接入结果
```

资料接入的关键原则：

```text
先读 Source，再抽 ClaimDraft，再用 anchor quote 回原文定位 Evidence，最后把 Claims 聚合为 KnowledgeCard。
```

### 2.2 问答流程

入口：

```text
TUI /ask <question>
scripts/ask_demo.py
AgentApp.ask(question)
```

主链路：

```text
AgentApp.ask
  -> AgentLoop.ask
    -> ValidationService.validate
      -> CardRetriever.retrieve        # SimpleCardIndex 搜索 KnowledgeCard
      -> CardRanker.rank
      -> TriggerRules.evaluate         # 判断是否需要 Evidence / Source
      -> ClaimRetriever.retrieve_for_cards      # 仅触发时执行
      -> EvidenceFetcher.fetch                 # 仅触发时执行
      -> ValidationResult
    -> AnswerService.answer
      -> PromptBuilder.build
      -> LLMAdapter.answer             # mock 或 paimonsdk
      -> ResponseFormatter.format
    -> answer text
```

输入：

```text
用户问题
```

输出：

```text
基于 KnowledgeCard / Claim / Evidence 构造 prompt 后生成的回答
```

当前回源触发规则位于 `TriggerRules`，主要条件包括：

```text
1. 未检索到卡片，或最高分低于阈值；
2. 问题包含“依据 / 来源 / 原文 / evidence / source”等词；
3. 问题包含“代码 / 修改 / api / 配置 / 约束 / implement / refactor / code”等词。
```

触发后会回拉：

```text
KnowledgeCard.claim_ids -> Claim.evidence_ids -> Evidence -> Source
```

## 3. 主要模块关系

项目主包：

```text
src/knowledgeag_card/
```

模块关系：

| 模块 | 责任 | 主要输入 | 主要输出 |
|---|---|---|---|
| `app/` | 配置加载、依赖装配、运行时后端选择 | `.env`、`config.json` | `AppConfig`、`AppContainer` |
| `domain/` | 核心领域模型和枚举 | 无外部输入 | Source、Evidence、Claim、KnowledgeCard 等数据结构 |
| `ingestion/` | 资料接入主流程 | 文件路径、文件内容、LLM 输出 | Source、Evidence、Claim、KnowledgeCard |
| `retrieval/` | 知识卡检索、排序、回源触发判断 | 用户问题、数据库中的 Cards | RetrievedCard、TriggerType |
| `validation/` | 将检索结果、触发规则、回源结果组合成问答上下文 | question | ValidationResult |
| `runtime/` | TUI、AgentApp、问答循环、Prompt 构造、输出格式化 | 用户命令、question | ingest 结果、answer text |
| `storage/` | SQLite 表结构与 Repository | 领域对象 | SQLite 持久化数据 |
| `adapters/llm/` | LLM 适配层 | prompt、配置、API key | ClaimDraft、Card JSON、answer text |
| `adapters/parsers/` | Markdown / Text / Code 结构解析 | 原始文本 | ReadUnit sections |
| `scripts/` | 简单命令行示例 | path / question | 控制台输出 |

总体关系：

```text
TUI / scripts
  -> runtime.AgentApp
    -> app.AppContainer
      -> ingestion / retrieval / validation / runtime services
      -> storage repositories
      -> adapters.llm
      -> adapters.parsers
```

模块边界：

```text
app/        只负责配置和装配，不写业务规则。
domain/     只放对象和枚举，不依赖基础设施。
ingestion/  负责 Source -> Evidence -> Claim -> Card。
retrieval/  负责从问题找到 Card，并判断是否需要回源。
validation/ 负责把检索、触发、回源结果合并成 ValidationResult。
runtime/    负责用户交互、问答循环、prompt 和输出。
storage/    负责 SQLite 表和对象持久化。
adapters/   负责外部系统差异，包括 LLM runtime 和文本解析。
```

## 4. 关键入口文件

### 4.1 项目与启动入口

| 文件 | 作用 |
|---|---|
| `pyproject.toml` | 项目元信息、依赖、可执行命令定义。当前命令为 `knowledgeag-card`。 |
| `src/knowledgeag_card/runtime/tui_app.py` | Rich TUI 主入口，处理 `/ingest`、`/ask`、`/stats`、`/help`、`/quit`。 |
| `src/knowledgeag_card/runtime/agent_app.py` | 面向 TUI 和脚本的门面层，暴露 `ingest`、`ask`、`stats`。 |
| `scripts/ingest_demo.py` | 接入资料的最小脚本入口。 |
| `scripts/ask_demo.py` | 提问问答的最小脚本入口。 |

### 4.2 配置与装配入口

| 文件 | 作用 |
|---|---|
| `src/knowledgeag_card/app/config.py` | 加载 `.env`、`config.json` / `config.json.example`，解析模型、存储、接入、检索、prompt 配置。 |
| `src/knowledgeag_card/app/container.py` | 项目依赖装配中心；创建 DB、Repository、Service、LLM Adapter、AgentLoop。 |
| `.env.example` | API key 示例配置。 |
| `config.json.example` | 存储路径、模型 provider、模型模式、检索参数、接入参数、系统提示词配置示例。 |

### 4.3 资料接入入口

| 文件 | 作用 |
|---|---|
| `src/knowledgeag_card/ingestion/ingest_service.py` | 资料接入主编排。 |
| `src/knowledgeag_card/ingestion/source_loader.py` | 读取文件，创建 Source，计算 version_id。 |
| `src/knowledgeag_card/ingestion/read_planner.py` | 决定整篇读取还是结构化拆分。 |
| `src/knowledgeag_card/ingestion/structural_splitter.py` | 根据 SourceType 调用 Markdown / Text / Code parser。 |
| `src/knowledgeag_card/ingestion/claim_extractor.py` | 调用 LLM Adapter 抽取 ClaimDraft。 |
| `src/knowledgeag_card/ingestion/evidence_aligner.py` | 根据 anchor quote 在原文中定位 Evidence。 |
| `src/knowledgeag_card/ingestion/claim_builder.py` | 将 ClaimDraft + evidence_ids 转为 Claim。 |
| `src/knowledgeag_card/ingestion/card_organizer.py` | 调用 LLM Adapter 将 Claims 聚合为 KnowledgeCard。 |

### 4.4 检索与问答入口

| 文件 | 作用 |
|---|---|
| `src/knowledgeag_card/runtime/agent_loop.py` | 问答主循环：先 validation，再 answer。 |
| `src/knowledgeag_card/validation/validation_service.py` | 组织检索、排序、触发规则和回源。 |
| `src/knowledgeag_card/retrieval/card_retriever.py` | 从索引中检索 KnowledgeCard。 |
| `src/knowledgeag_card/storage/vector_index.py` | 当前的简单关键词 / cosine-like 检索实现。 |
| `src/knowledgeag_card/retrieval/trigger_rules.py` | 判断是否需要 Claim / Evidence / Source。 |
| `src/knowledgeag_card/runtime/prompt_builder.py` | 将 Cards / Claims / Evidences 组装为 LLM prompt。 |
| `src/knowledgeag_card/runtime/answer_service.py` | 调用 LLM Adapter 生成回答。 |
| `src/knowledgeag_card/runtime/response_formatter.py` | 在需要回源时追加 Evidence locs。 |

### 4.5 LLM 与存储入口

| 文件 | 作用 |
|---|---|
| `src/knowledgeag_card/adapters/llm/base.py` | LLM Adapter 抽象接口。 |
| `src/knowledgeag_card/adapters/llm/mock_llm.py` | 本地 mock 后端，用于无模型时跑通流程。 |
| `src/knowledgeag_card/adapters/llm/paimonsdk_adapter.py` | paimonsdk 适配层，负责调用模型生成 ClaimDraft、Card JSON 和 Answer。 |
| `src/knowledgeag_card/storage/sqlite_db.py` | SQLite schema 与连接管理。 |
| `src/knowledgeag_card/storage/source_repository.py` | Source 持久化。 |
| `src/knowledgeag_card/storage/evidence_repository.py` | Evidence 持久化。 |
| `src/knowledgeag_card/storage/claim_repository.py` | Claim 持久化。 |
| `src/knowledgeag_card/storage/card_repository.py` | KnowledgeCard 持久化。 |

## 5. 核心领域对象

领域对象定义在：

```text
src/knowledgeag_card/domain/models.py
src/knowledgeag_card/domain/enums.py
```

### 5.1 Source

表示一个原始资料来源。

核心字段：

```text
source_id        Source ID，格式为 src_<uuid>
type             SourceType：markdown / text / code / unknown
title            标题，当前来自文件名 stem
uri              本地文件绝对路径
version_id       当前内容的 sha256
imported_at      导入时间
source_summary   LLM 生成的来源摘要，可为空
```

作用：

```text
Source 是 Evidence 的上游来源，也是后续回源和版本判断的基础。
```

### 5.2 Evidence

表示从 Source 中截取出来、可定位的证据片段。

核心字段：

```text
evidence_id          Evidence ID，格式为 ev_<uuid>
source_id            所属 Source
source_version       对应 Source.version_id
loc                  证据位置，如 section/chars 或 file/lines
content              证据窗口文本
normalized_content   标准化后的证据文本
```

作用：

```text
Evidence 用于支撑 Claim，并在回答涉及依据、来源、代码、配置等问题时回源。
```

### 5.3 Claim

表示从资料中抽取出的可复用判断。

核心字段：

```text
claim_id        Claim ID，格式为 clm_<uuid>
text            判断文本
evidence_ids    支撑该判断的 Evidence ID 列表
status          ClaimStatus：supported / conflicted / obsolete
updated_at      更新时间
```

作用：

```text
Claim 是 Source/Evidence 与 KnowledgeCard 之间的中间知识单元。
```

### 5.4 KnowledgeCard

表示面向使用场景组织后的知识卡片。

核心字段：

```text
card_id                 Card ID，格式为 card_<uuid>
title                   卡片标题
card_type               principle / method / pattern / sop / analysis / knowledge 等
summary                 卡片摘要
applicable_contexts     适用场景
core_points             3-7 个核心点
practice_rules          实践规则
anti_patterns           反模式
claim_ids               支撑卡片的 Claim ID 列表
evidence_ids            支撑卡片的 Evidence ID 列表
tags                    标签
updated_at              更新时间
```

作用：

```text
KnowledgeCard 是当前系统的主要检索对象和问答上下文入口。
```

### 5.5 接入过程临时对象

| 对象 | 作用 |
|---|---|
| `ReadUnit` | 被模型读取的单元。可能是整篇文档，也可能是结构化拆分后的章节 / 代码片段。 |
| `EvidenceAnchor` | LLM 给出的原文锚点，包含 quote、section_title、loc_hint。 |
| `ClaimDraft` | LLM 初步抽取的 claim 草稿，后续需要 evidence 对齐。 |
| `ReadPlan` | 读取计划，决定 `whole_document` 或 `structured`。 |
| `IngestResult` | 单次接入结果，包含 source、evidences、claims、cards。 |

### 5.6 检索与回答过程对象

| 对象 | 作用 |
|---|---|
| `RetrievedCard` | 被检索命中的 KnowledgeCard，包含 score 和 matched_claims。 |
| `ValidationResult` | 问答前的上下文判断结果，包含 Cards、Claims、Evidences、Sources 和是否仅用卡片回答。 |
| `StorageStats` | 当前数据库中 Source / Evidence / Claim / Card 数量。 |

### 5.7 枚举对象

| 枚举 | 当前取值 | 作用 |
|---|---|---|
| `SourceType` | `markdown` / `text` / `code` / `unknown` | 标记来源类型，影响解析和 evidence window。 |
| `ClaimStatus` | `supported` / `conflicted` / `obsolete` | 标记 Claim 状态。当前主要使用 `supported`。 |
| `ReadMode` | `whole_document` / `structured` | 标记读取模式。 |
| `TriggerType` | `conflict` / `uncertainty` / `citation_required` / `code_task` | 标记回源触发原因。 |

## 6. 当前技术栈

### 6.1 语言与包管理

```text
Python >= 3.11
setuptools + pyproject.toml
pip install -e .
```

当前项目包名：

```text
knowledgeag-card
```

当前 Python import 包：

```text
knowledgeag_card
```

当前命令行入口：

```text
knowledgeag-card
```

### 6.2 CLI / TUI

```text
Rich
```

用途：

```text
TUI 面板、Markdown 渲染、Live 流式显示、表格统计、命令行提示。
```

### 6.3 配置管理

```text
python-dotenv
.env
config.json / config.json.example
```

配置职责：

```text
.env                 存放 API key 等环境变量。
config.json          存放 storage、models、retrieval、ingest、system_prompts 等运行配置。
AppConfig.load       负责读取并归一化配置。
```

当前实际运行时后端变量：

```text
KNOWLEDGEAG_RUNTIME=paimon | mock
```

如果没有有效 API key，当前代码会回退到 mock 后端。

### 6.4 LLM / Runtime

当前支持两类 LLM 后端：

```text
mock_llm.py              本地 mock，用于流程验证。
paimonsdk_adapter.py     使用 paimonsdk + OpenAI 兼容客户端。
```

paimonsdk 适配层职责：

```text
1. 通过 AsyncOpenAI 创建 OpenAI 兼容 client。
2. 通过 paimonsdk.Agent / AgentOptions / ModelInfo 创建 agent。
3. 使用 adapter.stream_message 执行模型调用。
4. 支持流式 delta 回调。
5. 解析模型返回的 JSON，生成 ClaimDraft 或 Card 数据。
```

模型 API 配置当前会归一化为：

```text
chat.completions
responses
```

兼容别名包括：

```text
openai-completions -> chat.completions
openai-responses   -> responses
```

### 6.5 存储

```text
SQLite
sqlite3 标准库
```

默认数据库路径：

```text
data/storage/knowledgeag.sqlite3
```

当前表：

```text
sources
evidences
claims
cards
```

数组 / 列表字段当前通过 JSON 字符串存储。

### 6.6 检索

当前不是向量数据库，也不是 embedding 检索。

当前实现：

```text
SimpleCardIndex
  -> 读取所有 cards
  -> 将 title / summary / core_points / tags / applicable_contexts 拼成文档
  -> 正则分词
  -> Counter 统计
  -> cosine-like 分数
  -> 返回 top_k
```

因此当前检索属于：

```text
最小可运行的关键词重叠检索。
```

### 6.7 文件解析

当前解析器：

```text
MarkdownParser    按 Markdown 标题拆分
TextParser        按空行块拆分
CodeParser        按 Python 风格 def / class 拆分
```

注意：

```text
SourceLoader 支持识别多种代码后缀，但 CodeParser 当前主要识别 def / class 形式，更偏 Python 代码结构。
```

### 6.8 当前已显式依赖

来自 `pyproject.toml`：

```text
rich>=13.7.1
python-dotenv>=1.0.1
openai>=1.40.0
typing-extensions>=4.12.2
```

可选依赖：

```text
paimonsdk @ git+https://github.com/bg668/paimon.git@main
```

开发依赖：

```text
pytest>=8.3.2
```

## 后续开发使用建议

后续让 AI 或开发人员改代码前，建议先要求阅读：

```text
docs/PROJECT_CONTEXT.md
```

然后本次任务只重新分析：

```text
1. 当前实现与目标的差距
2. 修改影响面
3. 风险点和不确定点
4. 最小修改方案
5. 验收方式
```

固定原则：

```text
先有地图，再看现场；先定边界，再动手；先小范围施工，再验收沉淀。
```
