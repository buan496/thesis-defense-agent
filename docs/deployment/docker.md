# Docker 镜像构建说明

## 定位

当前 Dockerfile 用于本地验证 FastAPI 服务容器化启动。

本阶段只构建单容器 API 镜像，不包含 PostgreSQL、Qdrant、Prometheus 或 K8s。

## 构建镜像

```powershell
docker build -t thesis-defense-agent:local .
```

## 启动容器

```powershell
docker run --rm `
  -p 8000:8000 `
  --name thesis-defense-agent-api `
  thesis-defense-agent:local
```

访问：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/version
http://127.0.0.1:8000/docs
```

## 传入环境变量

如果需要调用真实 LLM / Embedding API，可以通过 `--env-file` 传入：

```powershell
docker run --rm `
  -p 8000:8000 `
  --env-file .env `
  --name thesis-defense-agent-api `
  thesis-defense-agent:local
```

## 挂载数据目录

如果需要使用本地向量库或任务数据，可以挂载 `data/`：

```powershell
docker run --rm `
  -p 8000:8000 `
  --env-file .env `
  -v "${PWD}\data:/app/data" `
  --name thesis-defense-agent-api `
  thesis-defense-agent:local
```

## 当前边界

- 暂未提供 docker-compose。
- 暂未拆分数据库、向量库和 API 服务。
- 暂未提供生产级密钥管理。
- 暂未提供健康检查脚本和 metrics。
- 暂未提供 K8s manifests。

下一阶段再补：

```text
docker-compose.yml
-> 数据目录挂载
-> 健康检查
-> 日志与 metrics
-> 服务器长期运行说明
```
