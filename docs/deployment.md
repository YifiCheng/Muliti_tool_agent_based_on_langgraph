# Deployment Guide

本项目支持两种本地运行方式：虚拟环境直接运行，以及 Docker Compose 运行。

## 1. 本地虚拟环境运行

进入项目根目录：

```powershell
cd D:\Code\develop\Business_Multi_Tool_Agent_Based_on_LangGraph
.\.venv\Scripts\Activate.ps1
cd agent-platform
```

初始化 SQLite：

```powershell
python scripts\init_sqlite.py
```

启动 API：

```powershell
uvicorn api.app:app --host 127.0.0.1 --port 8000
```

访问：

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/health
```

## 2. Docker Compose 运行

回到项目根目录：

```powershell
cd D:\Code\develop\Business_Multi_Tool_Agent_Based_on_LangGraph
```

构建镜像：

```powershell
docker compose build
```

启动服务：

```powershell
docker compose up
```

访问：

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/health
```

停止服务：

```powershell
docker compose down
```

## 3. 数据目录

Compose 会挂载：

```text
./agent-platform/data:/app/data
```

因此以下运行时数据会保留在本机：

```text
agent-platform/data/sql/business.db
agent-platform/data/traces/agent_traces.db
agent-platform/data/checkpoints/agent_checkpoints.sqlite
agent-platform/data/index/
```

## 4. LLM 配置

默认配置仍然使用 `mock`：

```yaml
llm:
  provider: mock
```

如果要切换到 Qwen 官方 API，需要修改：

```yaml
llm:
  provider: qwen_api
```

并在 `.env` 或系统环境变量中配置：

```text
QWEN_API_KEY=你的 DashScope API Key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

如果后续切换到远端实例上的 Qwen 模型，则改为：

```yaml
llm:
  provider: remote_qwen
```

并配置：

```text
REMOTE_QWEN_BASE_URL=
REMOTE_QWEN_API_KEY=
REMOTE_QWEN_MODEL=
```

## 5. 验证命令

本地测试：

```powershell
cd agent-platform
python -m pytest tests -o cache_dir=.pytest-cache
python scripts\smoke_release.py
```

Docker 可选测试：

```powershell
docker compose build
docker compose up
```

然后打开：

```text
http://127.0.0.1:8000/health
```