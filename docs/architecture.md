# Architecture

## Core flow
1. SourceLoader 读取原始资料并生成 Source
2. EvidenceExtractor 从 Source 切出可回源 Evidence
3. ClaimGenerator 从 Evidence 生成压缩 Claim
4. Repositories + SQLite 落库
5. ClaimRetriever 检索 Claim
6. TriggerRules 判断是否需要回源
7. ValidationService 拉取 Evidence / Source
8. AgentLoop 组织 prompt 并调用 LLM adapter 输出答案

## Module boundary
- `domain/`：只放核心对象与枚举，不放流程逻辑
- `ingestion/`：只负责资料进入系统
- `retrieval/`：只负责“找什么、拉什么、够不够回答”
- `storage/`：只负责持久化与索引
- `runtime/`：只负责回答编排与交互
- `adapters/llm/`：只负责把回答请求接到具体模型/runtime

## 当前设计取舍
### 为什么没有先把 retrieval 做成 tool
因为第一版目标不是展示“agent 会不会调工具”，而是先验证：
- 资料进入后能否沉淀为 Claim
- 提问时能否稳定回到 Evidence / Source
- 回答时能否受上下文约束

所以当前方案采用：
- 检索与验证：本地确定性流程
- 生成：交给 paimonsdk

这是一个更容易调试、更容易定位问题的切分。

## 已用到的模式
只保留三类：
- Repository：隔离 SQLite 细节
- Strategy：Parser / LLM adapter 可替换
- Orchestrator：IngestService / ValidationService / AgentLoop

## 明确不做的事
- 不预先做多 agent
- 不预先做复杂事件总线
- 不预先抽象过多 provider 层级
- 不把所有对象都设计成基类继承树

## 与 uu-work/main-v2 的接点
当前唯一强耦合点：
- `adapters/llm/paimonsdk_adapter.py`

它负责：
- 自动加载 `PAIMONSDK_SRC` 指向的 `uu-work` 源码
- 初始化 `AsyncOpenAI`
- 初始化 `OpenAIChatCompletionsAdapter`
- 构造 `Agent + AgentOptions + ModelInfo`
- 订阅 `message_update` 事件，把增量文本回传给 Rich TUI

因此 SDK 升级时，优先修改这一个文件即可。
