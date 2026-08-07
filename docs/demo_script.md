# 演示脚本

## 演示前准备

```powershell
.\.venv\Scripts\Activate.ps1
cd agent-platform
python scripts\init_sqlite.py
python -m pytest tests -o cache_dir=.pytest-cache
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

浏览器打开：

```text
http://127.0.0.1:8000/
```

## 演示 1：RAG 文档问答

问题：

```text
报销超过 5000 元需要谁审批？
```

预期讲解：

- Planner 选择 `document_search`；
- RAG 返回制度文档证据；
- Reflection 判断证据充分；
- Answer 基于证据回答；
- Trace 展示完整链路。

## 演示 2：SQL 结构化查询

问题：

```text
销售额最高的商品是什么？
```

勾选：

```text
SQL 查询需要人工审批
```

点击运行后，先展示审批卡片。

批准后讲解：

- SQL 查询前被 interrupt；
- 人工批准后通过 `Command(resume=...)` 恢复；
- SQL 只读执行；
- Trace 中出现 `sql_query`。

## 演示 3：拒绝 SQL

同样问题，审批时点击拒绝。

预期：

- 不执行 `sql_query`；
- Answer 说明无法获得授权数据；
- State 中 errors 包含 approval；
- Trace 不出现 SQL 工具事件。

## 演示 4：Trace

展示 trace 时间线：

```text
plan
approval
tool
reflect
answer
```

讲解每个节点的职责和 metadata。