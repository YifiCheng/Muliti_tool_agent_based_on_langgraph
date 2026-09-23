# Business Multi-Tool Agent Based on LangGraph

面向企业业务问答场景的多工具 Agent 项目。项目使用 LangGraph 编排 Planner、Tool、Reflection、Approval、Answer 节点，集成 RAG 文档检索、只读 SQL 查询、审批断点、Trace 可观测、FastAPI 服务层和浏览器演示页面。

## 项目环境和程序启动

### 1. 基础环境

本地开发环境建议：

```text
Windows 10/11
Python 3.11+ 或 3.13
Node.js LTS
PowerShell
```

检查：

```powershell
python --version
node -v
npm -v
```

如果没有 Node.js：

```powershell
winget install OpenJS.NodeJS.LTS
```

### 2. Python 虚拟环境

在项目根目录创建并激活虚拟环境：

```powershell
cd D:\Code\develop\Business_Multi_Tool_Agent_Based_on_LangGraph
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

安装后端依赖：

```powershell
cd agent-platform
python -m pip install -r requirements.txt
```

检查：

```powershell
python -c "import pydantic, yaml, dotenv, pytest, httpx; print('deps ok')"
```

### 3. 后端环境变量

后端配置文件：

```text
agent-platform/config/config.yaml
agent-platform/config/config.test.yaml
```

本地私密环境变量写在：

```text
agent-platform/.env
```

首次配置可以先从示例文件复制：

```powershell
cd D:\Code\develop\Business_Multi_Tool_Agent_Based_on_LangGraph\agent-platform
Copy-Item .env.example .env
```

然后按需补充真实配置。示例：

```text
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
QWEN_API_KEY=你的 Qwen API Key

REMOTE_QWEN_BASE_URL=http://127.0.0.1:18080/v1
REMOTE_QWEN_MODEL=Qwen/Qwen2.5-3B-Instruct
REMOTE_QWEN_API_KEY=local-no-auth

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=你的 MySQL 只读账号
MYSQL_PASSWORD=你的 MySQL 密码
MYSQL_DATABASE=business_db

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

API_HOST=127.0.0.1
API_PORT=8000
```

不要提交真实 `.env`、API Key、数据库密码或远程服务器密码。

### 4. 初始化本地数据

进入后端目录：

```powershell
cd D:\Code\develop\Business_Multi_Tool_Agent_Based_on_LangGraph\agent-platform
```

初始化 SQLite demo 数据：

```powershell
python scripts\init_sqlite.py
```

准备公开企业文档 RAG 语料：

```powershell
python scripts\fetch_public_docs.py
python scripts\prepare_public_docs.py
```

如果使用 MySQL demo 库，先确认 `.env` 中 MySQL 账号具备建表权限，再执行：

```powershell
python scripts\init_mysql_demo.py
python scripts\smoke_mysql.py --show-schema
```

如果使用 Redis，先启动 Redis 服务，再验证：

```powershell
python scripts\smoke_redis.py
python scripts\benchmark_redis_cache.py --repeat 5 --simulate-delay-ms 100
```

### 5. Qwen API

当前主配置默认使用 Qwen 官方 API：

```text
config/config.yaml -> llm.provider=qwen_api
config/config.test.yaml -> llm.provider=mock
```

验证：

```powershell
python scripts\smoke_qwen_api.py
```

### 6. 远端 Qwen

远端 Qwen 是可选模型后端，使用 OpenAI-compatible vLLM 服务。需要对比本地远端模型和 Qwen API 时，再通过 SSH tunnel 映射到本机：

```powershell
ssh -p 32500 -L 18080:127.0.0.1:8000 apulis-dev@10.8.19.3
```

如果远端服务无鉴权，本机验证：

```powershell
Invoke-RestMethod http://127.0.0.1:18080/v1/models
```

如果远端服务启用了 Bearer Token：

```powershell
Invoke-RestMethod http://127.0.0.1:18080/v1/models -Headers @{Authorization="Bearer <token>"}
```

项目侧验证：

```powershell
python scripts\smoke_remote_qwen.py
```

对比 Qwen API 与远端 Qwen：

```powershell
python scripts\compare_qwen_providers.py --cases direct handbook sql
```

报告输出：

```text
agent-platform/eval/reports/qwen_provider_comparison.json
agent-platform/eval/reports/qwen_provider_comparison.md
```

### 7. 启动后端

推荐启动方式：

```powershell
cd D:\Code\develop\Business_Multi_Tool_Agent_Based_on_LangGraph\agent-platform
python scripts\start_api.py
```

排查 FastAPI 时可直接运行：

```powershell
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/status
```

### 8. 启动 React 前端

前端目录：

```text
frontend/
```

安装依赖：

```powershell
cd D:\Code\develop\Business_Multi_Tool_Agent_Based_on_LangGraph\frontend
npm install
```

开发启动：

```powershell
npm run dev
```

访问：

```text
http://127.0.0.1:5173
```

构建检查：

```powershell
npm run build
```

### 9. 测试和 smoke

后端测试：

```powershell
cd D:\Code\develop\Business_Multi_Tool_Agent_Based_on_LangGraph\agent-platform
New-Item -ItemType Directory -Force .tmp | Out-Null
New-Item -ItemType Directory -Force .pytest-cache | Out-Null
$env:TEMP=(Resolve-Path .tmp)
$env:TMP=(Resolve-Path .tmp)
python -m pytest tests -o cache_dir=.pytest-cache
```

常用 smoke：

```powershell
python scripts\smoke_qwen_api.py
python scripts\smoke_remote_qwen.py
python scripts\smoke_mysql.py --show-schema
python scripts\smoke_redis.py
python scripts\smoke_frontend_react.py
```

### 10. Docker

项目保留 Docker 配置：

```powershell
docker compose build
docker compose up
```

当前主要开发路径是本地虚拟环境 + FastAPI + Vite React。


## 项目定位

本项目用于展示 Agent/AI 应用开发能力，重点覆盖：

- LangGraph 状态机编排；
- 多工具选择与执行；
- RAG 混合检索；
- SQLite 只读结构化查询；
- Reflection 证据充分性判断；
- SQL 查询前人工审批 interrupt；
- checkpoint 会话恢复；
- Observer trace 可观测；
- FastAPI 服务化；
- 静态 Web 演示页面；
- pytest 自动化测试。

## 已实现能力

```text
用户问题
  -> Plan Node
  -> Approval Node
  -> Tool Node
  -> Reflection Node
  -> Answer Node
```

已实现工具：

- `document_search`：基于本地文档的 RAG 检索；
- `sql_query`：SQLite 只读 SQL 查询；

已实现工程能力：

- Qwen API / 远端 Qwen / Mock LLM 配置切换；
- LangGraph checkpoint；
- SQL 审批暂停与恢复；
- SQLite trace 记录；
- FastAPI HTTP 接口；
- Web UI 演示；
- 端到端 smoke 脚本；
- 自动化测试。

## 快速开始

```powershell
.\.venv\Scripts\Activate.ps1
cd agent-platform
python -m pip install -r requirements.txt
python scripts\init_sqlite.py
python -m pytest tests -o cache_dir=.pytest-cache
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

浏览器打开：

```text
http://127.0.0.1:8000/
```

## 常用 Smoke

```powershell
python scripts\smoke_graph.py --query "报销超过 5000 元需要谁审批？"
python scripts\smoke_sql.py --query "销售额最高的商品是什么？"
python scripts\smoke_approval.py --decision approve
python scripts\smoke_api.py
python scripts\smoke_frontend.py
```

## API

```text
GET  /health
POST /api/v1/agent/runs
POST /api/v1/agent/resume
GET  /api/v1/agent/runs/{thread_id}
GET  /api/v1/traces/{trace_id}
```

详细说明见：

```text
docs/api.md
```

## 架构文档

```text
docs/architecture.md
docs/demo_script.md
docs/interview_notes.md
```

## 测试

```powershell
cd agent-platform
New-Item -ItemType Directory -Force .tmp | Out-Null
New-Item -ItemType Directory -Force .pytest-cache | Out-Null
$env:TEMP=(Resolve-Path .tmp)
$env:TMP=(Resolve-Path .tmp)
python -m pytest tests -o cache_dir=.pytest-cache
```

## 不提交的运行产物

```text
.env
.tmp/
.pytest-cache/
__pycache__/
data/checkpoints/*.sqlite
data/sql/business.db
data/traces/*.db
```

## 自动化评测

项目内置 MVP 评测集：

```powershell
cd agent-platform
python scripts\smoke_eval.py
```

评测覆盖：

- RAG 工具选择；
- SQL 工具选择；
- Calculator 工具选择；
- 关键词命中；
- evidence 返回；
- SQL approval approve 流程。

报告输出：

```text
eval/reports/mvp_report.json
eval/reports/mvp_report.md
```

注意：评测指标来自 mock 模式和本地模拟数据，不代表生产效果。

## 公开文档 RAG 评测

项目支持基于公开企业 handbook 的 RAG 评测。

```powershell
cd agent-platform
python scripts\fetch_public_docs.py
python scripts\prepare_public_docs.py
python scripts\smoke_public_eval.py
```

报告输出：

```text
agent-platform/eval/reports/public_docs_rag_report.json
agent-platform/eval/reports/public_docs_rag_report.md
```

说明：

- 英文 query 用作公开文档 RAG 基线；
- 中文 query 用作跨语言检索 baseline；
- 当前失败样本用于指导后续 embedding / rerank 优化，不直接删除。

## 中文 Query Translation

公开 handbook 语料主要是英文。项目增加了 query translation 层，把部分中文业务问题转换为英文检索 query，并在 evidence metadata 中记录转换信息。

```powershell
cd agent-platform
python scripts\smoke_query_translation.py
python scripts\compare_public_rag_translation.py --query "GitLab handbook 中如何描述沟通方式？"
```

说明：

- 当前是规则版 translator，用于建立可控 baseline；
- 不是通用机器翻译；
- 后续可替换为 Qwen 翻译、Qwen embedding 或 rerank。

## 真实公开文档语料

RAG 默认语料可以切换到公开企业 handbook 文档。

来源清单：

```text
agent-platform/data/source_manifest.yaml
docs/public_docs_sources.md
```

生成公开文档语料：

```powershell
cd agent-platform
python scripts\fetch_public_docs.py
python scripts\prepare_public_docs.py
python scripts\smoke_public_rag.py --query "What does the handbook say about communication?"
```

说明：

- 这些文档来自公开 Web 来源；
- 项目保留 source URL、license URL 和 NOTICE；
- 不包含企业内部私有数据；
- 当前主要是英文文档，中文跨语言检索会在后续 embedding / rerank 步骤增强。

## 部署运行

本项目支持本地虚拟环境运行和 Docker Compose 运行。

本地运行：

```powershell
cd agent-platform
python scripts\init_sqlite.py
uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Docker 运行：

```powershell
docker compose build
docker compose up
```

启动后访问：

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/health
```

更详细说明见：

```text
docs/deployment.md
```

## 远端服务器部署

远端实例不支持 Docker 时，可以使用 venv + uvicorn 部署 FastAPI，并通过 SSH tunnel 从本地访问。

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\pack_remote.ps1
scp -P 30205 .\business-multi-tool-agent-remote.tar.gz apulis-dev@10.8.19.3:~/
ssh -p 30205 -L 18000:127.0.0.1:8000 apulis-dev@10.8.19.3
```

当前远端部署默认仍使用：

```text
provider=mock
```

详细说明见：

```text
docs/remote_deployment.md
```

## MySQL 模块

项目的 SQL 工具支持 SQLite 和 MySQL 两个后端：

```text
sqlite -> 本地开发 / 测试
mysql  -> 真实业务数据库
```

MySQL 需要通过环境变量配置：

```text
MYSQL_HOST
MYSQL_PORT
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
```

验证命令：

```powershell
cd agent-platform
python scripts\smoke_mysql.py --query "销售额最高的商品是什么？"
python scripts\smoke_mysql.py --show-schema
```

详细说明见：

```text
docs/mysql_tool.md
```

## Redis 模块

项目支持 Redis 作为业务缓存和临时状态工具。

环境变量：

```text
REDIS_HOST
REDIS_PORT
REDIS_DB
REDIS_PASSWORD
```

验证：

```powershell
cd agent-platform
python scripts\smoke_redis.py
python scripts\benchmark_redis_cache.py --repeat 5 --simulate-delay-ms 100
python -m pytest tests\test_redis_tool.py -o cache_dir=.pytest-cache
```

详细说明见：

```text
docs/redis_tool.md
```

## React Agent Console

前端位于：

```text
frontend/
```

技术栈：

```text
Vite + React + TypeScript
```

启动后端：

```powershell
cd agent-platform
python scripts\start_api.py
```

启动前端：

```powershell
cd frontend
npm run dev
```

访问：

```text
http://127.0.0.1:5173
```

前端支持 Agent 问答、工具选择、RAG evidence、trace、运行状态和实验报告展示。

详细说明见：

```text
docs/frontend_console.md
```
