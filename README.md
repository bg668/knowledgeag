# knowledge-agent

一个面向 `Source -> Evidence -> Claim -> Retrieval -> Validation -> Answer` 最小闭环的 Python 项目骨架。

这版已经按 `uu-work/main-v2` 当前接口做了适配：
- 知识内核仍保持独立、简单
- `paimonsdk` 只负责模型接入、多轮会话、流式输出
- 不把检索系统和 agent runtime 过早揉成一个大平台

这符合《人月神话》的几个核心取向：
- 先做可运行的最小闭环，再扩展
- 保持概念完整性，边界清楚
- 少接口、少机制、少“为了未来而现在复杂化”

## 当前能力
- 导入 `md / txt / py / js / ts / json / yaml / yml / ini / toml / cfg / conf / java / go / rs / cpp / c / h`
- 生成 Source / Evidence / Claim 并写入 SQLite
- 基于简单关键词重叠做 Claim 检索
- 基于触发规则决定是否回拉 Evidence / Source
- Rich TUI 对话与命令行交互
- 可切换 `mock` / `paimonsdk` 两种回答后端
- `paimonsdk` 路径已适配 `uu-work/main-v2` 的 `chat.completions / responses` 双模式

## 项目结构
```text
knowledge-agent/
├─ .env.example
├─ config.json.example
├─ README.md
├─ docs/
│  └─ architecture.md
├─ scripts/
│  ├─ ask_demo.py
│  └─ ingest_demo.py
├─ src/knowledge_agent/
│  ├─ app/           # 配置、容器、装配
│  ├─ domain/        # 领域模型与枚举
│  ├─ ingestion/     # Source -> Evidence -> Claim
│  ├─ retrieval/     # 检索、触发规则、验证
│  ├─ storage/       # SQLite 与简单索引
│  ├─ runtime/       # AgentLoop、PromptBuilder、Rich TUI
│  └─ adapters/
│     ├─ llm/        # mock / paimonsdk(main-v2)
│     └─ parsers/    # 各类文件解析
└─ tests/
```

## 安装
### 1) 安装本项目
```bash
pip install -e .
```

### 2) 使用 mock 模式
默认就是 `mock`，无需额外安装。

### 3) 使用 paimonsdk 模式
先准备 `uu-work/main-v2`。

你有两种方式：

方式 A：直接安装到当前环境
```bash
pip install -e /path/to/uu-work
```

方式 B：不安装，只在 `.env` 中指定源码路径
```bash
PAIMONSDK_SRC=/path/to/uu-work
```

然后把 `.env.example` 复制为 `.env`，只放密钥：
```bash
APP_LLM_BACKEND=paimonsdk
QWEN_API_KEY=your-qwen-key
MOONSHOT_API_KEY=your-moonshot-key
OPENAI_API_KEY=your-fallback-key
```

再把 `config.json.example` 复制为 `config.json`，填写模型目录与当前模式：
```json
{
  "models": {
    "mode": "qwen3.5-plus",
    "providers": {
      "qwen": {
        "baseUrl": "https://coding.dashscope.aliyuncs.com/v1",
        "api": "openai-completions",
        "apiKeyEnv": "QWEN_API_KEY",
        "models": [
          {
            "id": "qwen3.5-plus",
            "name": "qwen3.5-plus"
          }
        ]
      }
    }
  }
}
```

说明：
- `.env` 负责密钥与运行参数
- `config.json` 负责 `models.mode / providers / baseUrl / model / api / apiKeyEnv`
- 推荐每个 provider 自己通过 `apiKeyEnv` 指定对应的环境变量名
- 当前命中 provider 的 `apiKeyEnv` 会优先取值；若未配置或环境变量为空，再回退到 `OPENAI_API_KEY`
- provider 的 `api` 支持 `openai-completions` / `chat.completions` / `chat`，也支持 `openai-responses` / `responses` / `response`
- provider 未填写 `api` 时，默认走 `chat.completions`

## 启动 TUI
```bash
knowledge-agent
```

## TUI 命令
- `/help` 查看帮助
- `/ingest <path>` 导入单个文件或目录
- `/ask <question>` 提问
- `/stats` 查看数据库统计
- `/quit` 退出

## 示例
```bash
python scripts/ingest_demo.py data/raw
python scripts/ask_demo.py "系统中心是什么？"
```

## 与 uu-work/main-v2 的关系
当前接法刻意保持克制：

1. `knowledge_agent` 自己完成资料导入、切片、Claim 生成、检索、验证
2. `paimonsdk` 只接最终回答阶段
3. 不先做工具编排、不先做多 agent、不先做复杂工作流

这样做的好处是：
- 第一版问题更容易定位
- SDK 升级时，影响面集中在 `adapters/llm/paimonsdk_adapter.py`
- 你之后要换回自己的单 agent loop，也只需要替换这一层

## 当前限制
- 检索现在仍是关键词重叠的最小实现，不是向量检索增强版
- 还没有把检索能力包装成 agent tool

## 下一步建议
最稳妥的开发顺序是：
1. 先用 mock 跑通 ingest / ask / stats
2. 再切到 `paimonsdk`，确认模型接入、base_url、流式输出都正常
3. 然后再决定是否把 retrieval 封装成 tool
4. 最后才考虑经验沉淀、后台聚类、规则合并等增强能力
