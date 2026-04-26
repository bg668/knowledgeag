# knowledgeag-card

KnowledgeCard 主检索，Claim 内部支撑，Evidence / Source 回源。

## 安装

```bash
pip install -e .
# 或安装 paimon 运行时
pip install -e .[paimon]
```

## 配置

1. 复制 `config.json.example` 为 `config.json`
2. 复制 `.env.example` 为 `.env`
3. 按 `config.json` 中选中 provider 的 `apiKeyEnv` 填写 API Key，例如 `QWEN_API_KEY`

## 运行

```bash
knowledgeag-card
```

## 命令

- `/ingest <path>` 导入文件或目录
- `/ask <question>` 提问
- `/stats` 查看统计
- `/quit` 退出

## 主链路

### 接入

`Source -> ReadPlan -> ClaimDraft -> Evidence -> Claim -> KnowledgeCard`

### 使用

`KnowledgeCard -> Claim -> Evidence -> Source`
