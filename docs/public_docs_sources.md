# Public Document Sources

本项目的真实 RAG 语料来自公开企业或组织 handbook。所有来源记录在：

```text
agent-platform/data/source_manifest.yaml
```

## 使用原则

- 只使用公开可访问文档；
- 不抓取需要登录的内容；
- 不使用内部企业资料；
- 保留 source URL；
- 保留 license URL；
- 保留 `data/public_docs/NOTICE.md`；
- 简历和 README 中不声称这些是内部私有数据。

## 当前来源

- GitLab Handbook
- Mattermost Handbook
- Clef Handbook

## 生成方式

```powershell
cd agent-platform
python scripts\fetch_public_docs.py
python scripts\prepare_public_docs.py
```

生成目录：

```text
agent-platform/data/public_docs/raw/
agent-platform/data/public_docs/clean/
```

## 检索验证

```powershell
cd agent-platform
python scripts\smoke_public_rag.py --query "What does the handbook say about communication?"
```

## 多语言限制

当前公开来源主要是英文。如果用中文问题直接检索，BM25 效果可能不稳定。后续可以通过 Qwen embedding、query translation、rerank 或中文摘要 metadata 改善跨语言检索。


## 评测

公开文档 RAG 评测说明见：

```text
docs/public_rag_eval.md
```

运行：

```powershell
cd agent-platform
python scripts\smoke_public_eval.py
```