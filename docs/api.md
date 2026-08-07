# API 文档

服务启动：

```powershell
cd agent-platform
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

## GET /health

请求：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

响应：

```json
{"status": "ok"}
```

## POST /api/v1/agent/runs

普通问答：

```json
{
  "query": "报销超过 5000 元需要谁审批？",
  "session_id": "demo-session",
  "trace_id": "demo-trace",
  "thread_id": "demo-thread",
  "require_sql_approval": false
}
```

SQL 审批：

```json
{
  "query": "销售额最高的商品是什么？",
  "session_id": "sql-session",
  "trace_id": "sql-trace",
  "thread_id": "sql-thread",
  "require_sql_approval": true
}
```

可能响应：

```json
{
  "status": "interrupted",
  "thread_id": "sql-thread",
  "interrupt": [
    {
      "id": "...",
      "value": {
        "type": "approval_required"
      }
    }
  ]
}
```

## POST /api/v1/agent/resume

批准：

```json
{
  "thread_id": "sql-thread",
  "decision": "approve",
  "reason": "approved by demo user"
}
```

拒绝：

```json
{
  "thread_id": "sql-thread",
  "decision": "reject",
  "reason": "not allowed"
}
```

注意：`resume` 必须使用和 `runs` 相同的 `thread_id`。

## GET /api/v1/agent/runs/{thread_id}

查询 checkpoint state。

## GET /api/v1/traces/{trace_id}

查询 Observer trace。