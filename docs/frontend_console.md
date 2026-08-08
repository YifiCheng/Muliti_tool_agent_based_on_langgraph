# React Agent Console

本项目前端使用 Vite + React + TypeScript。

## 功能

- Agent 业务问答
- selected_tools 展示
- RAG evidence 展示
- trace 事件查看
- runtime status 展示
- Qwen provider 对比报告查看
- Redis benchmark 报告查看

## 开发启动

后端：

```powershell
cd agent-platform
python scripts\start_api.py
```

前端：

```powershell
cd frontend
npm run dev
```

访问：

```text
http://127.0.0.1:5173
```

## 构建

```powershell
cd frontend
npm run build
```

## 边界

当前前端是 Agent Console，不是权限系统、租户系统或生产管理后台。
````

## 19. 子项 17：更新 README

修改文件：

```text
README.md
```

增加：

````markdown
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