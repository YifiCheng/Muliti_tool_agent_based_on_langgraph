# Remote Deployment Without Docker

本项目支持在不使用 Docker 的 Linux 服务器上运行 FastAPI。

当前远端部署目标：

```text
provider=mock
API=FastAPI + Uvicorn
Access=SSH tunnel
```

## 1. 打包

在本地项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\pack_remote.ps1
```

生成：

```text
business-multi-tool-agent-remote.tar.gz
```

## 2. 上传

```powershell
scp -P 30205 .\business-multi-tool-agent-remote.tar.gz apulis-dev@10.8.19.3:~/
```

密码在终端交互式输入，不要写入脚本。

## 3. 远端解压

```bash
ssh -p 30205 apulis-dev@10.8.19.3
mkdir -p ~/apps
tar -xzf ~/business-multi-tool-agent-remote.tar.gz -C ~/apps
cd ~/apps/business-multi-tool-agent/agent-platform
```

## 4. 远端环境

优先使用独立 venv：

```bash
cd ~/apps/business-multi-tool-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r agent-platform/requirements.txt
```

如果服务器没有 `venv`，再考虑使用已有 conda 环境，但不要随意污染模型推理环境。

## 5. 启动 API

```bash
cd ~/apps/business-multi-tool-agent/agent-platform
source ../.venv/bin/activate
python -c "from config.settings import load_settings; print(load_settings().llm.provider)"
python scripts/init_sqlite.py
mkdir -p logs
API_HOST=127.0.0.1 API_PORT=8000 nohup python scripts/start_api.py > logs/api.log 2>&1 &
echo $! > logs/api.pid
```

检查：

```bash
cat logs/api.log
curl http://127.0.0.1:8000/health
```

## 6. 本地 SSH 隧道

在本地新开 PowerShell：

```powershell
ssh -p 30205 -L 18000:127.0.0.1:8000 apulis-dev@10.8.19.3
```

保持这个窗口不要关闭。

然后本地访问：

```text
http://127.0.0.1:18000
http://127.0.0.1:18000/health
```

## 7. 本地 smoke

```powershell
cd agent-platform
python scripts\smoke_remote_api.py --base-url http://127.0.0.1:18000
```

## 8. 停止服务

远端执行：

```bash
cd ~/apps/business-multi-tool-agent/agent-platform
kill $(cat logs/api.pid)
```

如果 pid 文件失效：

```bash
ps aux | grep "scripts/start_api.py"
```

确认进程后再 kill。