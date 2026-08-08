# Public RAG Evaluation

本项目基于公开企业 handbook 构建 RAG 评测集。

## 数据集

```text
agent-platform/eval/cases/public_docs_rag_cases.yaml
```

## 语料目录

```text
agent-platform/data/public_docs/clean
```

该目录由以下脚本生成：

```powershell
cd agent-platform
python scripts\fetch_public_docs.py
python scripts\prepare_public_docs.py
```

## 评测指标

当前评测检查：

- 工具选择是否包含 `document_search`；
- 最终回答是否包含关键字；
- evidence 是否存在；
- evidence 数量是否达到最低要求；
- evidence source 是否命中预期公开文档。

## 运行方式

```powershell
cd agent-platform
python scripts\smoke_public_eval.py
```

输出：

```text
eval/reports/public_docs_rag_report.json
eval/reports/public_docs_rag_report.md
```

## 当前限制

公开来源主要是英文。中文 query 属于跨语言检索 baseline，当前 BM25 + hash embedding 可能无法稳定命中正确来源。

后续优化方向：

- Qwen embedding；
- query translation；
- rerank；
- 中文摘要 metadata；
- 按来源和标题加权。

## Query Translation Baseline

Step 19 增加了 query translation 层，用于改善中文 query 检索英文公开 handbook 的效果。

相关文件：

```text
agent-platform/rag/query_translation.py
agent-platform/scripts/compare_public_rag_translation.py
docs/query_translation.md
```

验证：

```powershell
cd agent-platform
python scripts\compare_public_rag_translation.py --query "GitLab handbook 中如何描述沟通方式？"
python scripts\smoke_public_eval.py
```