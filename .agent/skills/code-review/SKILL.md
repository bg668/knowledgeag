---
name: code-review
description: Review changed code against AGENTS.md, docs/PROJECT_CONTEXT.md, current code, tests, and change-log requirements. Use after implementation, before final reporting.
user_invocable: true
---

# Code Review

本技能只用于“修改后审查”。

它不替代 `AGENTS.md` 的修改前确认流程，不替代 `docs/PROJECT_CONTEXT.md` 的项目地图，也不自动修复问题。

若本技能与 `AGENTS.md`、`docs/PROJECT_CONTEXT.md` 或当前代码事实冲突，以项目文件和当前代码为准。

## 审查目标

确认本次改动是否满足以下要求：

```text
小范围、可审核、可验证、可回滚。
让变化只发生在应该发生的地方。
```

重点检查：

```text
1. 是否只解决本次需求
2. 是否遵守模块边界
3. 是否破坏主流程可读性
4. 是否绕开回源链路
5. 是否引入无关重构或复杂设计
6. 是否有必要验证
7. 是否按 docs/CHANGE_LOG.example.md 更新 docs/CHANGE_LOG.md
```

## 审查前必须读取

先读取：

```text
AGENTS.md
docs/PROJECT_CONTEXT.md
```

然后核对当前代码和本次 diff。

不要只相信文档；文档是项目地图，当前代码是现场事实。

## 识别本次改动

优先使用：

```bash
git diff --name-only
git diff --cached --name-only
git diff
```

如果本地没有未提交变更，再使用：

```bash
git diff main...HEAD --name-only
git diff main...HEAD
```

如果仓库没有 `main`，根据当前仓库实际默认分支判断。

## 核心审查项

### 1. 需求边界

检查是否存在：

```text
未要求的新功能
顺手重构
顺手改名
顺手改目录
无关格式化
扩大修改范围
用复杂框架解决小问题
```

发现后标为 Must fix。

### 2. 项目主链路

本项目核心链路是：

```text
Source -> Evidence -> Claim -> KnowledgeCard -> Retrieval -> Validation -> Answer
```

检查本次改动是否破坏以下原则：

```text
KnowledgeCard 是主检索对象
Claim 是内部支撑对象
Evidence / Source 用于回源
LLM 负责理解
程序负责定位和验证
LLM 输出必须经过解析、对齐、校验后入库
```

涉及接入流程时，确认没有绕过：

```text
SourceLoader
ReadPlanner
StructuralSplitter
ClaimExtractor
EvidenceAligner
ClaimBuilder
ClaimValidator
CardOrganizer
CardValidator
Repository save
```

涉及问答流程时，确认没有绕过：

```text
ValidationService
CardRetriever
CardRanker
TriggerRules
ClaimRetriever
EvidenceFetcher
AnswerService
PromptBuilder
LLMAdapter
ResponseFormatter
```

### 3. 模块边界

按 `docs/PROJECT_CONTEXT.md` 核对依赖方向。

重点检查：

```text
domain 不依赖 storage / adapters / runtime
app 不写业务规则
runtime 不直接写存储细节
adapters 不反向侵入领域模型设计
storage 不承担业务编排
scripts 只做最小演示入口
```

### 4. LLM / Agent / Adapter 约束

如果本次改动涉及 LLM 或 Agent：

```text
外部模型调用必须通过 adapters 或受控 Agent 接口
配置必须集中由 app/config.py 和 app/container.py 装配
业务模块不得直接读取 API key / base_url / model
paimonsdk 只作为可替换后端，不反向决定领域对象设计
```

如果新增工具调用：

```text
工具清单应由 knowledgeag 控制
工具权限应收敛到本项目内部能力
不得把任意外部工具注册能力扩散到业务层
```

### 5. 类型、数据结构和持久化

检查：

```text
核心领域对象是否仍在 domain/models.py 或明确的领域位置
新增字段是否有稳定含义
Repository 是否只负责读写，不承担业务判断
SQLite schema 改动是否有迁移或兼容说明
Source / Evidence / Claim / KnowledgeCard 的 ID、版本、回源字段是否保持一致
```

不要套用外部项目的硬规则。

本项目不默认要求：

```text
全量 async
所有结构必须 Pydantic
所有函数禁止 tuple 返回
FastAPI / Next.js / Tailwind / shadcn
外部项目专用 MCP 注册检查
```

只有当当前代码已经采用这些规则，或本次需求明确要求时，才按当前代码风格审查。

### 6. 测试和验证

检查是否有与本次改动匹配的验证方式。

优先级：

```text
1. 精准单测
2. 相关 pytest
3. 最小脚本验证
4. 手动流程验证
```

常用命令按项目实际情况选择：

```bash
python -m pytest
python -m pytest tests/<related_test>.py
python scripts/ingest_demo.py
python scripts/ask_demo.py
python -m compileall src scripts
```

不得为了通过验证而修改无关测试体系。

### 7. 变更记录

检查是否按以下模板在 `docs/CHANGE_LOG.md` 追加记录：

```text
修改目标
修改文件
未修改范围
验证方式
剩余风险
```

模板来源：

```text
docs/CHANGE_LOG.example.md
```

如果缺失记录，标为 Must fix。

如果记录过长、泛泛而谈、没有说明未修改范围或剩余风险，标为 Should fix。

## 输出格式

只输出审查结果，不自动修复。

使用以下格式：

```text
## Must fix
- `path:line`：问题。原因。建议改法。

## Should fix
- `path:line`：问题。原因。建议改法。

## Note
- `path:line`：观察项。是否需要处理由用户判断。

## 验证情况
- 已执行：...
- 未执行：...，原因：...

## 结论
通过 / 不通过。
```

如果没有问题，输出：

```text
## Must fix
无。

## Should fix
无。

## Note
无。

## 验证情况
- 已执行：...
- 未执行：...，原因：...

## 结论
通过。
```

## 禁止行为

```text
禁止自动修复审查发现的问题。
禁止替代 AGENTS.md 的修改前确认流程。
禁止输出大段设计解释。
禁止套用外部项目的专用目录、框架、CI、MCP、API 规则。
禁止把建议扩展成本次需求之外的新功能。
禁止因为审查而扩大修改范围。
```
