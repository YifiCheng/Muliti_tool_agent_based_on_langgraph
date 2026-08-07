# 面试讲解材料

## 30 秒介绍

这是一个面向企业业务问答的 LangGraph 多工具 Agent。它可以根据用户问题自动选择 RAG、SQL 或计算工具，并通过 Reflection 判断证据是否充分。系统支持 SQL 查询前人工审批、checkpoint 恢复、Trace 可观测、FastAPI 服务化和 Web 演示页面。

## 技术亮点

1. LangGraph 状态机编排；
2. 多工具注册和选择；
3. RAG 混合检索；
4. SQLite 只读 SQL 工具和安全校验；
5. Reflection 证据充分性判断；
6. Human-in-the-loop interrupt；
7. SQLite checkpoint；
8. Observer trace；
9. FastAPI 服务层；
10. Web 演示层；
11. pytest 自动化测试。

## 可以重点讲的实现细节

### 为什么用 LangGraph

因为本项目不是单轮 prompt，而是有计划、工具、反思、审批、恢复等明确状态流转。LangGraph 更适合表达可控流程。

### 为什么 SQL 要审批

即使当前 SQL 是只读，也用审批机制展示高风险工具调用前的人类确认能力。后续如果扩展写操作或敏感数据查询，可以复用同一机制。

### 为什么要 Reflection

工具返回不等于可以回答。Reflection 用于判断证据是否足够，必要时触发二次检索。

### 为什么要 Trace

Agent 失败时需要知道是规划错、工具错、检索错、反思错还是回答错。Trace 能支撑调试和演示。

## 面试可能被问

### Q：这个项目和普通 RAG 有什么区别？

A：普通 RAG 只做文档检索。本项目有工具规划、SQL 查询、反思判断、人工审批、checkpoint 和 trace，是一个 Agent 工程闭环。

### Q：如何避免 SQL 风险？

A：当前阶段只允许 SELECT，禁止危险关键字、多语句，并限制最大返回行数。SQL 工具执行前还可以开启人工审批。

### Q：Qwen API 和远端 Qwen 怎么切换？

A：通过 `config/config.yaml` 的 `llm.provider` 切换。`mock` 用于测试，`qwen_api` 用官方 API，`remote_qwen` 用 OpenAI-compatible 远端服务。

### Q：项目还有哪些不足？

A：还没有生产级鉴权、限流、分布式 checkpoint、评测数据集和 Docker 部署。这些是后续增强方向。

## 简历描述

可写：

```text
基于 LangGraph 开发企业业务多工具 Agent，集成 RAG 文档检索、SQLite 只读 SQL 查询、Reflection 证据校验、Human-in-the-loop 审批、checkpoint 会话恢复、Trace 可观测与 FastAPI/Web 演示层；编写 pytest 测试覆盖核心节点、工具、审批恢复和 API 接口。
```