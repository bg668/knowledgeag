下面是一篇可以直接拿去生成博客/音频的**逐字稿**。主题聚焦在：**AI Coding 中，模块化设计如何把影响范围收敛到最小，以及哪些设计模式最有用。**

---

# AI Coding 时代，模块化设计为什么比以前更重要？

大家好，今天我们聊一个非常工程化、但又特别适合 AI Coding 的话题：

**模块化设计。**

更具体一点，我们聊的是：

> 当我们用 Codex、Claude Code、Cursor、Kimi Code 这类 AI 编程工具时，为什么模块化设计会变得比以前更关键？哪些设计模式最能帮助我们控制修改范围，避免“改一个点，炸一大片”？

我先给出今天的核心观点：

> **AI Coding 时代，模块化设计的核心价值，不是让代码看起来更高级，而是把变化关进小房间里。**

或者更形象一点：

> **好的模块边界，就像保险丝。一个地方短路，不应该烧掉整栋楼。**

这就是今天的第一句金句：

> **模块化不是为了分文件，而是为了控制爆炸半径。**

---

# 一、AI Coding 中真正昂贵的东西变了

过去我们写代码，最贵的是“人手写代码的时间”。

一个功能，可能需要人慢慢写、慢慢调、慢慢改。

但现在有了 AI Coding，代码生成变快了。
你一句话，它能帮你生成一个模块。
你再一句话，它能帮你改十个文件。
你再一句话，它甚至能重构一套结构。

听起来很爽，但问题也来了：

**AI 太会改代码了。**

它不怕改多。
它不怕动大。
它不怕重写。
它有时候甚至会因为“热心”，把本来只需要改一行的问题，变成一次全项目重构。

所以 AI Coding 时代，真正昂贵的东西变成了：

* 修改范围是否可控
* 人是否能审查
* AI 是否能理解边界
* 一个模块改动是否会影响其他模块
* 出问题时能不能快速定位
* 新功能能不能局部增加，而不是全局侵入

因此，模块化设计在 AI Coding 中变得特别重要。

因为模块化设计做的事情，本质上是：

> **把系统拆成一个个有边界的小房间，让 AI 每次只进入该进入的房间。**

这就是第二句金句：

> **给 AI 的最好约束，不是长篇原则，而是清晰边界。**

---

# 二、模块化设计的本质：控制变更半径

很多人理解模块化，会以为就是：

“多建几个文件。”
“多拆几个目录。”
“多写几个类。”

但这不是真正的模块化。

真正的模块化不是形式上的拆分，而是：

> **当一个需求变化时，只有应该变化的部分发生变化。**

比如你现在要把模型服务从 OpenAI 换成 Kimi。

好的模块化设计下，你应该只改：

```text
providers/kimi_adapter.py
config.json
```

最多再改一个：

```text
providers/factory.py
```

但如果你发现自己要改：

```text
main.py
tui.py
agent.py
knowledge.py
summary.py
report.py
config.py
```

那就说明模型调用这件事没有被很好地封装。

再比如，你想增加一种新的摘要策略。

好的设计下，你只新增：

```text
summary/strategies/security_news.py
```

主流程不用动。

坏的设计下，你要打开一个巨大的 `process()` 函数，在里面加一堆：

```python
if summary_type == "security_news":
    ...
elif summary_type == "vuln_report":
    ...
elif summary_type == "daily":
    ...
```

这就不是模块化，这是把变化堆进一个垃圾场。

所以，AI Coding 中我们要不断问一个问题：

> **这次变化，会影响多少文件？这些文件是不是本来就应该被影响？**

如果一个变化影响了不该影响的地方，就说明边界有问题。

第三句金句：

> **好的设计，不是没有变化，而是变化有去处。**

---

# 三、AI Coding 中最有用的模块化设计模式

围绕“控制变更半径”这个目标，我认为最有用的设计模式主要有九个：

```text
Facade 外观模式
Adapter 适配器模式
Strategy 策略模式
Command 命令模式
Observer 观察者模式
State 状态模式
Decorator / Proxy 装饰器与代理模式
Composite 组合模式
Factory Method 工厂方法
```

它们每一个都在解决同一个问题：

> **把容易变化的东西隔离起来。**

下面我们一个一个讲。

---

# 四、Facade 外观模式：给复杂系统一个简单门面

第一个模式是 Facade，外观模式。

它是 AI Coding 中非常高频、非常实用的模式。

Facade 的核心思想是：

> **复杂的东西藏在里面，外面只暴露一个简单入口。**

比如我们做 AI 应用，经常会调用 LLM。

底层可能很复杂：

* OpenAI 有一套接口
* Kimi 有一套接口
* Claude 有一套接口
* Ollama 有一套接口
* 有的用 Chat Completions
* 有的用 Responses API
* 有的支持 tools
* 有的不支持
* 有的返回 streaming
* 有的返回完整文本

如果你在业务代码里到处直接调用这些 SDK，就会非常危险。

例如：

```python
# report.py
client.chat.completions.create(...)

# agent.py
openai.responses.create(...)

# summary.py
kimi_client.chat(...)

# tui.py
model_client.stream(...)
```

这时，如果你想换模型，或者换 API 类型，整个项目都会被牵动。

更好的方式是做一个 Facade：

```python
class LLMClient:
    def generate(self, messages, tools=None):
        ...
    
    def stream(self, messages, tools=None):
        ...
```

业务代码只认识：

```python
llm.generate(messages)
```

它不关心底层是什么模型，不关心是 OpenAI 还是 Kimi，也不关心是 Chat API 还是 Responses API。

这样一来，模型变化的影响范围就被收敛到：

```text
providers/
llm_client.py
config.py
```

业务模块不用动。

这就是 Facade 的威力。

它的记忆点是：

> **Facade 是系统的前台。后台再乱，前台要稳。**

或者说：

> **给 AI 一个门口，不要让它翻窗。**

在 AI Coding 中，Facade 特别适合用在这些地方：

```text
LLM 调用
Embedding 调用
向量数据库
Agent Runtime
文件系统
浏览器工具
企业微信推送
TIP 情报接口
第三方平台 SDK
```

只要一个东西满足三个条件，就值得考虑 Facade：

第一，它底层复杂。
第二，它未来可能替换。
第三，它不应该污染业务逻辑。

例如：

```text
KnowledgeStore
LLMClient
RuntimeClient
WeComClient
TipClient
```

这些名字都很适合作为 Facade。

但是注意，Facade 不等于“大一统平台”。

不要一开始就搞一个：

```text
UniversalAIPlatformManager
GlobalServiceFacade
EverythingClient
```

这不是外观模式，这是上帝对象。

好的 Facade 应该小而清楚。

比如：

```text
LLMClient 只负责模型调用
KnowledgeStore 只负责知识存取
ReportExporter 只负责报告导出
```

Facade 的核心不是“包住一切”，而是“给一类复杂能力一个稳定入口”。

这一节的金句是：

> **外观模式的目标，是让复杂系统在外部看起来简单。**

---

# 五、Adapter 适配器模式：把外部差异挡在门外

第二个模式是 Adapter，适配器模式。

Facade 和 Adapter 很像，但它们解决的问题不一样。

Facade 解决的是：

> **复杂系统怎么给外部一个简单入口。**

Adapter 解决的是：

> **不同外部系统怎么变成内部统一协议。**

比如你有多个模型 provider：

```text
OpenAI
Kimi
Claude
Ollama
LocalModel
```

它们的请求格式不同，返回格式也不同。

如果这些差异进入业务代码，业务代码就会变得很脏。

比如：

```python
if provider == "openai":
    content = response.choices[0].message.content
elif provider == "kimi":
    content = response["data"]["message"]
elif provider == "claude":
    content = response.content[0].text
```

这种代码一旦散落各处，后续维护会非常痛苦。

Adapter 的做法是：
定义自己的内部协议。

例如：

```python
class LLMRequest:
    messages: list
    tools: list | None
    temperature: float

class LLMResponse:
    content: str
    tool_calls: list
    raw: dict
```

然后每个 provider 做一个适配器：

```python
class OpenAIAdapter:
    def generate(self, request: LLMRequest) -> LLMResponse:
        ...

class KimiAdapter:
    def generate(self, request: LLMRequest) -> LLMResponse:
        ...

class ClaudeAdapter:
    def generate(self, request: LLMRequest) -> LLMResponse:
        ...
```

业务层只处理：

```text
LLMRequest
LLMResponse
```

它永远不直接接触外部 API 的原始格式。

这对 AI Coding 非常关键。

因为 AI 最容易犯的错误之一，就是把外部服务的细节“顺手”写进业务逻辑里。

Adapter 的价值就是：

> **外部世界再混乱，内部协议要干净。**

这句也可以作为记忆点：

> **Adapter 是海关：外部格式进来，必须先过境检查。**

在你的项目里，Adapter 适合这些场景：

```text
不同 LLM provider
不同 embedding provider
不同向量数据库
不同 RSS 源
不同漏洞情报源
不同报告输出格式
不同 agent runtime
```

例如威胁情报系统中，不同安全厂商的漏洞公告字段肯定不一样。

A 厂商叫：

```text
severity
```

B 厂商叫：

```text
risk_level
```

C 厂商叫：

```text
cvss_score
```

你的内部不应该到处处理这些差异。
应该统一成：

```python
class VulnerabilityInfo:
    cve: str
    title: str
    severity: str
    affected_products: list[str]
    exploit_status: str
    mitigation: str
```

然后用不同 Adapter 把外部数据转成内部模型。

这一节的金句是：

> **Adapter 的作用，是让外部变化止步于边界。**

---

# 六、Strategy 策略模式：把变化点变成可替换零件

第三个模式是 Strategy，策略模式。

这是 AI Coding 中最自然、最常用的模式之一。

它解决的问题是：

> **主流程稳定，但某些步骤经常变化。**

比如你在做知识库或者 LLM-wiki 项目。

主流程可能是：

```text
读取资料
解析文本
切分 chunk
生成摘要
抽取 claim
写入存储
检索回答
```

这里面，哪些东西容易变化？

很明显：

```text
chunk 怎么切
summary 怎么生成
claim 怎么抽取
检索结果怎么排序
prompt 怎么组织
报告怎么生成
```

这些都是变化点。

如果你把这些逻辑全部写进一个大函数里：

```python
def process_source(source):
    # parse
    # chunk
    # summarize
    # extract claims
    # store
    # index
```

一开始很快，后面会很痛苦。

因为每次修改策略，都要动主流程。

Strategy 的做法是：

> **把容易变化的算法、规则、prompt、流程步骤，抽成可替换策略。**

比如 chunk 策略：

```python
class ChunkStrategy:
    def split(self, text: str) -> list[Chunk]:
        ...
```

然后实现：

```python
class FixedSizeChunkStrategy:
    def split(self, text):
        ...

class MarkdownChunkStrategy:
    def split(self, text):
        ...

class CodeAwareChunkStrategy:
    def split(self, text):
        ...
```

主流程只写：

```python
chunks = chunk_strategy.split(text)
```

这时，如果你让 Codex 新增一种切分策略，你可以非常明确地说：

> 新增 `MarkdownChunkStrategy`，实现 `ChunkStrategy` 接口，不要修改主流程。

这就是 AI Coding 中非常好的任务约束。

它把 AI 的修改范围限制在一个小文件里。

Strategy 的记忆点是：

> **Strategy 是插槽：主机不变，插件可换。**

或者：

> **主流程要像轨道，策略要像列车。列车可以换，轨道别乱改。**

适合 Strategy 的场景非常多：

```text
文本切分策略
摘要策略
检索策略
排序策略
prompt 策略
漏洞风险判断策略
情报筛选策略
日报生成策略
报告渲染策略
模型选择策略
```

但是要注意，Strategy 不要过早使用。

如果当前只有一种实现，而且看不到变化压力，就用普通函数。

比如：

```python
def normalize_text(text):
    ...
```

就很好。

不要为了“看起来可扩展”，一上来就写：

```python
class AbstractNormalizeStrategy:
    ...
```

这样反而增加 AI 理解成本。

什么时候用 Strategy？

有一个很简单的判断：

> **当你发现自己想写第三个 if/elif 时，就该考虑 Strategy。**

例如：

```python
if mode == "fixed":
    ...
elif mode == "markdown":
    ...
elif mode == "semantic":
    ...
```

这时 Strategy 就开始有价值了。

这一节的金句是：

> **Strategy 不是为了预测未来，而是为了收纳已经出现的变化。**

---

# 七、Command 命令模式：把动作变成可审计对象

第四个模式是 Command，命令模式。

在普通业务系统里，Command 可能不是最常见的模式。
但在 Agent 和 AI Coding 中，它非常重要。

原因很简单：

> **Agent 最大的问题之一，是它做了什么必须可见、可审计、可回放。**

比如一个威胁情报 Agent 做日报，它可能会执行这些动作：

```text
读取 RSS
筛选资讯
调用模型摘要
生成日报
写入文件
发送企业微信
创建工单
```

如果这些动作都是普通函数直接调用，过程就很容易变黑盒。

比如：

```python
generate_report()
send_wecom()
create_ticket()
```

最后只看到结果，不知道每一步的输入输出是什么。

Command 的做法是把动作结构化。

例如：

```json
{
  "command": "generate_report",
  "input": {
    "date": "2026-04-25",
    "audience": "security_team"
  }
}
```

或者：

```json
{
  "command": "push_wecom_message",
  "input": {
    "target": "emergency_team",
    "content": "重要漏洞预警..."
  }
}
```

这样一来，每个动作都可以：

```text
记录
展示
审核
重试
回放
撤销
权限控制
```

这对 AI Coding 太重要了。

因为 AI 很擅长生成动作，但人需要控制风险。

尤其是高风险动作，比如：

```text
发送邮件
企业微信推送
写入数据库
修改文件
提交代码
创建工单
下发 IOC
```

都应该优先考虑 Command。

Command 的记忆点是：

> **Command 是 Agent 的行车记录仪。**

还有一句更工程化的：

> **能被记录的动作，才是真正可控的动作。**

比如你可以设计：

```python
class Command:
    name: str
    input: dict

class CommandResult:
    status: str
    output: dict
    error: str | None
```

然后所有工具调用都走统一入口：

```python
result = command_runner.run(command)
```

这时你可以很容易做：

```text
命令日志
失败重试
人工确认
权限检查
dry-run 模式
```

例如：

```python
if command.name in HIGH_RISK_COMMANDS:
    require_human_approval(command)
```

这就是模块化设计在 AI Agent 中的实际价值。

不是为了“模式优雅”，而是为了控制风险。

这一节的金句是：

> **Agent 可以自由思考，但不能自由乱动。动作必须命令化。**

---

# 八、Observer 观察者模式：让核心逻辑只发事件，不关心谁在看

第五个模式是 Observer，观察者模式。

它非常适合 CLI、TUI、Agent Runtime、日志系统和 streaming 输出。

很多项目一开始会这么写：

```python
def run_task():
    print("开始任务")
    logger.info("开始任务")
    tui.update_status("开始任务")
    
    result = call_llm()
    
    print("任务完成")
    tui.update_result(result)
```

看起来没问题，但这里有一个严重问题：

**核心逻辑和展示逻辑耦合了。**

也就是说，任务执行模块不仅负责执行任务，还负责：

```text
打印
日志
TUI 刷新
进度显示
错误展示
```

以后你想换 TUI，可能要改 runtime。
你想改日志格式，可能要改业务流程。
你想增加 Web UI，又要把主流程翻出来改。

Observer 的做法是：

> **核心流程只发事件，不关心谁订阅。**

例如：

```text
task_started
llm_call_started
llm_token_received
tool_called
step_completed
task_failed
task_completed
```

Runtime 只负责：

```python
event_bus.emit("task_started", data)
event_bus.emit("tool_called", data)
event_bus.emit("task_completed", data)
```

然后：

```text
TUI 订阅事件，用于刷新界面
Logger 订阅事件，用于写日志
Audit 订阅事件，用于保存审计记录
Metrics 订阅事件，用于统计耗时
```

这样模块边界就清楚了。

Runtime 不知道 TUI 的存在。
TUI 不知道模型怎么调用。
日志系统不影响主流程。

这对 AI Coding 特别有用。

因为你可以让 Codex 单独修改 TUI：

> 只修改 `tui/event_handlers.py`，不要修改 `agent/runtime.py`。

也可以让它单独增加日志：

> 新增一个 `AuditEventSubscriber`，订阅现有事件，不要改主流程。

Observer 的记忆点是：

> **核心逻辑只敲钟，不管谁来听。**

或者：

> **事件是模块之间最轻的胶水。**

Observer 适合这些场景：

```text
Agent 执行过程
TUI 实时刷新
streaming token 输出
任务进度
日志系统
审计系统
指标统计
异步通知
```

但是 Observer 也不能滥用。

如果一个函数内部两三步就结束，不需要搞事件系统。

Observer 适合“一个核心流程，多个旁路系统关注它”的场景。

这一节的金句是：

> **不要让主流程到处喊人干活，让它只发布事实。**

---

# 九、State 状态模式：避免流程被布尔值拖垮

第六个模式是 State，状态模式。

它解决的是流程生命周期问题。

很多系统一开始喜欢用布尔值：

```python
is_checked = True
is_reviewed = False
is_sent = False
is_failed = False
is_retry = True
```

字段多了以后，就会出现各种奇怪组合。

比如：

```text
已发送但未审核？
审核失败但已推送？
重试中但状态是完成？
已发布后还能编辑？
```

这就是状态没有被显式建模造成的。

更好的方式是定义状态机。

比如漏洞公告的流程：

```text
Draft
ReviewPending
Approved
Published
Archived
```

威胁情报日报：

```text
Collected
Filtered
Summarized
Drafted
ReviewPending
Approved
Pushed
```

Agent 执行任务：

```text
Pending
Running
WaitingForTool
Verifying
Completed
Failed
Retrying
```

State 的作用是：

> **明确当前处于哪一步，以及下一步允许去哪。**

例如：

```python
allowed_transitions = {
    "Draft": ["ReviewPending"],
    "ReviewPending": ["Approved", "Draft"],
    "Approved": ["Published"],
    "Published": ["Archived"],
}
```

这样 Codex 在修改流程时，也能看到规则。

你可以要求：

> 不允许从 Draft 直接进入 Published。
> Published 状态不允许修改正文，只能创建新版本。
> Failed 状态可以 Retry，但 Completed 状态不能 Retry。

这比一堆布尔值可靠得多。

State 的记忆点是：

> **状态不是字段，状态是秩序。**

还有一句更适合 AI Coding：

> **状态机是给 AI 的红绿灯。**

没有状态机，AI 可能会写出一条看起来能跑、但业务逻辑错误的路。
有状态机，哪些路能走、哪些路不能走，就很清楚。

State 适合这些地方：

```text
Agent 任务生命周期
报告审核流程
漏洞公告流程
工单流程
知识入库流程
文档发布流程
任务重试流程
```

但同样，不要过度使用。

如果流程只有两个状态：

```text
enabled / disabled
```

用布尔值就够了。

State 适合状态多、转换规则重要、错误转换会带来风险的场景。

这一节的金句是：

> **流程越重要，状态越要显式。**

---

# 十、Decorator 和 Proxy：把横切逻辑放到边界外

第七类模式是 Decorator 和 Proxy。

它们不完全一样，但在 AI Coding 中经常一起出现。

它们解决的问题是：

> **日志、缓存、重试、限流、权限、监控，不应该污染主业务逻辑。**

比如 LLM 调用。

一次模型调用可能需要：

```text
超时控制
失败重试
请求日志
响应日志
token 统计
成本统计
缓存
限流
权限检查
trace id
错误转换
```

如果你把这些都写进主函数，就会很乱。

例如：

```python
def generate_summary(text):
    try:
        logger.info(...)
        if cache.exists(...):
            return cache.get(...)
        response = llm.call(...)
        cache.set(...)
        logger.info(...)
        return response
    except TimeoutError:
        retry(...)
    except Exception as e:
        logger.error(...)
```

这个函数表面叫 `generate_summary`，实际上干了十件事。

更好的方式是：

```python
@retry
@trace
@cache
def call_llm(request):
    ...
```

或者使用 Proxy：

```text
RawLLMClient
CachedLLMProxy
RateLimitedLLMProxy
TracingLLMProxy
```

业务代码仍然调用：

```python
llm.generate(request)
```

但是外层代理负责：

```text
缓存
限流
日志
审计
重试
权限
```

这样主逻辑就干净了。

Decorator / Proxy 的记忆点是：

> **横切逻辑要穿外套，不要长进身体里。**

还有一句：

> **业务逻辑负责做事，代理层负责保护它。**

在 AI Coding 中，这非常重要。

因为 AI 修改业务逻辑时，如果日志、缓存、重试全混在里面，它很可能顺手改坏基础能力。

但如果这些能力在装饰器或代理里，AI 改业务代码时就不容易影响它们。

适合 Decorator / Proxy 的场景：

```text
LLM 调用
HTTP 请求
数据库访问
向量检索
工具调用
文件写入
消息推送
高风险命令执行
```

举个例子。

你可以有：

```python
llm = OpenAIAdapter(config)
llm = CachedLLMProxy(llm)
llm = RateLimitedLLMProxy(llm)
llm = TracingLLMProxy(llm)
```

最终业务层拿到的还是 `llm`，但它已经具备缓存、限流、追踪能力。

这就是非常好的模块化增强。

这一节的金句是：

> **增强能力应该包在外面，而不是塞进里面。**

---

# 十一、Composite 组合模式：处理树状结构，让整体和部分一致

第八个模式是 Composite，组合模式。

它适合处理树状结构。

AI 项目里，树状结构非常多：

```text
文档树
目录树
Markdown 章节
知识节点
任务计划
Agent 子任务
报告结构
代码结构
```

比如一个知识库中的文档：

```text
Source
  Section
    Chunk
      Claim
      Evidence
  Summary
```

再比如一个 Agent 的计划：

```text
Plan
  Step
    SubStep
      ToolCall
```

如果你对每一层都写不同处理逻辑，很快会混乱。

Composite 的做法是：

> **让单个节点和节点集合拥有一致接口。**

比如每个节点都可以：

```python
node.children()
node.validate()
node.render()
node.to_dict()
```

这样你就可以递归处理整棵树。

比如：

```python
def render_node(node):
    output = node.render()
    for child in node.children:
        output += render_node(child)
    return output
```

Composite 的价值在于：

> **让复杂结构可以被统一处理。**

这对 AI Coding 也很友好。

因为你可以让 Codex 增加一种新节点：

```text
EvidenceNode
```

只要它实现同样接口，就能进入现有流程。

Composite 的记忆点是：

> **树再大，也是节点套节点。**

或者：

> **让叶子和树枝说同一种话。**

适合 Composite 的场景：

```text
Markdown AST
报告章节
任务计划树
知识图谱局部结构
文件目录树
多级菜单
Agent 多步计划
```

但要注意，不要过早设计复杂树。

如果你只是处理一段纯文本，就不要搞一套 Node 系统。

Composite 适合结构真的有层级，并且你需要统一遍历、渲染、验证、导出的场景。

这一节的金句是：

> **当结构天然是树，就不要用一堆平铺的 if 去假装它不是。**

---

# 十二、Factory Method 工厂方法：把创建逻辑集中起来

第九个模式是 Factory Method，工厂方法。

它很简单，但非常实用。

它解决的问题是：

> **对象怎么创建，不应该散落在业务代码里。**

比如你根据配置创建模型 provider：

```python
if config.provider == "openai":
    llm = OpenAIAdapter(config)
elif config.provider == "kimi":
    llm = KimiAdapter(config)
elif config.provider == "ollama":
    llm = OllamaAdapter(config)
```

如果这些判断散落在多个文件里，后面新增 provider 会很痛苦。

更好的方式是集中到一个工厂函数：

```python
def create_llm_provider(config):
    if config.provider == "openai":
        return OpenAIAdapter(config)
    if config.provider == "kimi":
        return KimiAdapter(config)
    if config.provider == "ollama":
        return OllamaAdapter(config)
    raise ValueError(f"Unknown provider: {config.provider}")
```

业务代码只写：

```python
llm = create_llm_provider(config)
```

Factory Method 的记忆点是：

> **创建归创建，使用归使用。**

还有一句：

> **工厂不是为了复杂，而是为了不让创建逻辑满地都是。**

它适合：

```text
根据配置创建 LLM provider
根据配置创建 embedding provider
根据类型创建策略
根据命令名创建 handler
根据输出格式创建 renderer
根据存储类型创建 store
```

但是工厂方法也容易被滥用。

不要一开始就搞：

```text
AbstractProviderFactory
RuntimeFactoryManager
UniversalFactoryRegistry
```

在 Python 项目里，很多时候一个普通函数就够了。

判断标准很简单：

> **如果创建逻辑开始重复，或者需要根据配置选择实现，就用工厂。否则直接 new。**

这一节的金句是：

> **简单工厂是收纳盒，复杂工厂可能是迷宫。**

---

# 十三、这些模式如何组合使用？

真实项目里，模式不是孤立使用的。

它们经常组合出现。

比如一个 LLM 模块可以这样设计：

```text
LLMClient           -> Facade
OpenAIAdapter       -> Adapter
KimiAdapter         -> Adapter
create_llm_client   -> Factory Method
CachedLLMProxy      -> Proxy
TracingLLMProxy     -> Proxy
```

一个摘要系统可以这样设计：

```text
SummaryService      -> Facade
SummaryStrategy     -> Strategy
NewsSummaryStrategy -> Strategy
VulnSummaryStrategy -> Strategy
```

一个 Agent Runtime 可以这样设计：

```text
Command             -> Command
CommandRunner       -> Command dispatcher
TaskState           -> State
EventBus            -> Observer
ToolProxy           -> Proxy
```

一个 TUI 系统可以这样设计：

```text
Runtime emits events        -> Observer
TUI subscribes events       -> Observer
Command actions             -> Command
State display               -> State
```

这里有一个非常重要的经验：

> **模式不是一个一个摆上去的，而是围绕变化点自然长出来的。**

你不要问：

“我要不要用设计模式？”

你应该问：

```text
哪里会变化？
哪里不该被影响？
哪里需要统一接口？
哪里需要审计？
哪里需要替换？
哪里需要生命周期？
```

答案出来之后，模式自然就出来了。

这一节的金句是：

> **先找变化点，再选设计模式。不要先选模式，再找地方安放。**

---

# 十四、AI Coding 中的模块化检查表

当你用 Codex Plan mode 设计一个功能时，可以让它按下面的问题思考。

第一，最小闭环是什么？

```text
输入是什么？
处理是什么？
输出是什么？
怎么验证？
```

第二，变化点在哪里？

```text
模型 provider 会变吗？
摘要方式会变吗？
存储会变吗？
输出格式会变吗？
工具调用会变吗？
```

第三，边界在哪里？

```text
外部服务边界
业务逻辑边界
UI 边界
存储边界
Agent Runtime 边界
```

第四，哪个模式最合适？

```text
外部复杂系统：Facade
外部差异接口：Adapter
可替换算法：Strategy
可审计动作：Command
流程生命周期：State
事件通知：Observer
横切增强：Decorator / Proxy
树状结构：Composite
配置创建：Factory Method
```

第五，不做什么？

这是非常关键的一点。

AI Coding 中，“不做什么”比“做什么”还重要。

你要明确告诉 AI：

```text
不重写整个项目
不引入插件系统
不添加复杂继承层级
不新增全局单例
不把 UI 和 runtime 混在一起
不把 provider 细节写进业务逻辑
```

这一节的金句是：

> **计划里没有 Do Not，AI 就容易热心过头。**

---

# 十五、一个完整例子：给威胁情报日报系统做模块化

假设我们要做一个威胁情报日报 Agent。

需求是：

```text
读取安全资讯
筛选重要内容
生成摘要
按照不同受众生成日报
人工审核后推送企业微信
```

如果不做模块化，很容易写成一个大流程：

```python
def run_daily_report():
    rss_items = read_rss()
    filtered = filter_items(rss_items)
    summary = call_llm(filtered)
    report = render_report(summary)
    send_wecom(report)
```

一开始很快，但后面问题会很多。

比如：

* RSS 来源要增加
* 筛选策略要调整
* 摘要 prompt 要换
* 报告格式要变
* 推送渠道要增加
* 审核流程要加入
* 某些推送需要人工确认

这时我们就可以这样拆。

第一，外部资讯源用 Adapter：

```text
RSSAdapter
VendorNewsAdapter
SecurityBlogAdapter
```

统一输出：

```text
NewsItem
```

第二，筛选逻辑用 Strategy：

```text
ImportanceFilterStrategy
AudiencePreferenceStrategy
ZeroDayPriorityStrategy
```

第三，LLM 调用用 Facade + Adapter：

```text
LLMClient
OpenAIAdapter
KimiAdapter
```

第四，日报生成用 Strategy：

```text
LeaderReportStrategy
EmergencyTeamReportStrategy
ResearcherReportStrategy
```

第五，推送动作使用 Command：

```text
GenerateReportCommand
SendWeComCommand
CreateTicketCommand
```

第六，审核流程使用 State：

```text
Draft
ReviewPending
Approved
Pushed
```

第七，执行过程使用 Observer：

```text
on_news_collected
on_summary_generated
on_report_drafted
on_review_required
on_report_pushed
```

第八，企业微信推送用 Proxy：

```text
WeComClient
RateLimitedWeComProxy
AuditWeComProxy
```

这样一个系统的变化就被分区了。

如果要新增资讯源，改 Adapter。
如果要换摘要方式，改 Strategy。
如果要换模型，改 Provider Adapter。
如果要加审核，改 State 和 Command。
如果要改 TUI 显示，改事件订阅者。
如果要加推送审计，改 Proxy。

这就是模块化真正的价值。

> **不是代码拆得多，而是每种变化都有自己的落点。**

---

# 十六、哪些模式要谨慎使用？

讲完有用的，也要讲不建议高频使用的。

第一，Singleton 单例。

它的问题是隐藏依赖。

AI Coding 中，隐藏依赖非常危险。
因为 AI 改代码时，很难判断这个对象从哪里来，什么时候初始化，测试时怎么替换。

例如：

```python
LLMClient.get_instance()
GlobalConfig.get_instance()
StoreManager.get_instance()
```

短期方便，长期痛苦。

更好的方式是显式传入：

```python
app = App(config=config, llm=llm, store=store)
```

金句：

> **单例让调用变简单，也让依赖变隐形。**

第二，Abstract Factory 抽象工厂。

它不是不能用，但一般不要太早用。

如果你真的有“一整套产品族”要切换，比如：

```text
OpenAI LLM + OpenAI Embedding + OpenAI Reranker
Local LLM + Local Embedding + Local Reranker
```

那抽象工厂有价值。

但如果只是创建一个 LLM provider，简单工厂函数就够了。

金句：

> **没有产品族，就别急着建工厂园区。**

第三，Bridge 桥接。

Bridge 适合两个维度独立变化，比如：

```text
报告类型 × 输出格式
```

但它抽象成本高，不适合早期项目。

金句：

> **桥接模式适合真有两岸，不适合在水坑上造大桥。**

第四，Visitor 访问者。

Visitor 适合 AST、编译器、静态分析、复杂文档树。
普通业务里，它会让代码难懂。

金句：

> **Visitor 是重工具，别拿它拧小螺丝。**

第五，Flyweight 享元。

它解决大量小对象内存复用。
但 AI 应用早期瓶颈通常不是内存，而是上下文、模型调用、数据质量和流程正确性。

金句：

> **不要在还没跑通业务时，先优化对象内存。**

---

# 十七、总结：AI Coding 时代的模块化原则

最后我们总结一下。

AI Coding 时代，模块化设计的目标不是“看起来架构漂亮”，而是：

> **让变化只发生在应该发生的地方。**

最有用的设计模式，可以按变化类型记：

```text
外部复杂系统，用 Facade。
外部接口差异，用 Adapter。
可替换算法，用 Strategy。
Agent 动作审计，用 Command。
流程生命周期，用 State。
事件通知解耦，用 Observer。
横切增强能力，用 Decorator / Proxy。
树状结构处理，用 Composite。
配置创建对象，用 Factory Method。
```

再压缩成一句话：

> **Facade 管入口，Adapter 管翻译，Strategy 管变化，Command 管动作，State 管流程，Observer 管通知，Proxy 管保护，Composite 管树，Factory 管创建。**

这是今天最适合作为结尾的金句。

如果你只记住一个原则，那就是：

> **模块化不是把代码切碎，而是把变化关起来。**

如果你只记住一个 AI Coding 的实践建议，那就是：

> **每次让 AI 写代码前，先问它：这次修改应该被限制在哪几个模块里？哪些模块绝对不应该被影响？**

这才是 AI Coding 时代最重要的工程能力。

不是让 AI 写更多代码，而是让 AI 在正确的边界内写代码。

最后用一句话收束：

> **好的模块化，是给人看的地图，也是给 AI 走路的护栏。**
