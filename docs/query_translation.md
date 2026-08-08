# Query Translation

本项目的公开企业 handbook 语料主要是英文。中文问题直接检索英文文档时，BM25 和 hash embedding 很难稳定命中正确来源。

因此项目增加了 query translation 层：

```text
中文 query -> 英文 search_query -> RAG 检索 -> evidence metadata 记录转换信息
```

## 当前实现

当前版本使用规则版 translator：

```text
agent-platform/rag/query_translation.py
```

它只覆盖公开 handbook 演示中的常见词，例如：

- 沟通 -> communication
- 价值观 -> values
- 工程 -> engineering
- 产品管理 -> product management
- 员工手册 -> employee handbook

## 验证命令

```powershell
cd agent-platform
python scripts\smoke_query_translation.py
python scripts\compare_public_rag_translation.py --query "GitLab handbook 中如何描述沟通方式？"
python scripts\smoke_public_eval.py
```

## 当前边界

规则版 translator 不是通用翻译器。它适合做可控 baseline，但不能覆盖复杂业务中文表达。

后续增强方向：

- Qwen API 翻译 query；
- Qwen embedding 跨语言向量检索；
- rerank；
- 为公开文档生成中文标题和摘要 metadata。