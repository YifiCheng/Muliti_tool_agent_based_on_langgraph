# 架构说明

## 总体架构

```text
Web UI
  |
FastAPI
  |
AgentService
  |
LangGraph StateGraph
  |
Plan -> Approval -> Tool -> Reflection -> Answer
  |
Tools / RAG / SQL / Observer / Checkpointer
```

## 核心模块

### graph

- `app.py`：构建 LangGraph；
- `nodes.py`：Plan、Approval、Tool、Reflection、Answer 节点；
- `router.py`：条件路由；
- `state.py`：AgentState；
- `checkpointer.py`：MemorySaver 和 SQLite checkpointer；
- `approval.py`：审批协议。

### tools

- `document_search`：文档检索；
- `sql_query`：只读 SQL 查询；
- `mock_calculator`：计算工具；
- `registry_factory.py`：生产工具注册。

### rag

- 文档加载；
- chunk 切分；
- BM25；
- FAISS 向量检索；
- hybrid retriever。

### reflection

- 规则校验；
- LLM JSON reflection；
- fallback。

### observer

- SQLite trace store；
- 节点和工具事件；
- latency、metadata、error。

### api

- FastAPI app；
- 请求响应 schema；
- AgentService；
- run/resume/state/trace 接口。

## 状态流转

```text
START
  -> plan
  -> approval
  -> tool
  -> reflect
  -> answer
  -> END
```

当 Reflection 返回 `retrieve_more` 且未超过最大轮数：

```text
reflect -> plan
```

当 SQL 查询需要审批：

```text
approval -> interrupt -> Command(resume=...) -> approval -> tool
```

当审批拒绝：

```text
approval -> answer
```

## 数据存储

- `data/sql/business.db`：业务 SQLite 数据库；
- `data/traces/agent_traces.db`：Observer trace；
- `data/checkpoints/agent_checkpoints.sqlite`：LangGraph checkpoint；
- `data/index/`：RAG 索引。

这些都是运行产物，不提交 Git。