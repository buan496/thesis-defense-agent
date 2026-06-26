# Docker 镜像构建说明

## 定位

当前 Dockerfile 和 docker-compose.yml 用于本地验证 FastAPI 服务容器化启动。

本阶段只构建单容器 API 服务，不包含 PostgreSQL、Qdrant、Prometheus 或 K8s。

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
http://127.0.0.1:8000/metrics
http://127.0.0.1:8000/metrics/prometheus
http://127.0.0.1:8000/docs
```

## 使用 Docker Compose

推荐本地验证使用 docker compose：

```powershell
docker compose up --build
```

后台启动：

```powershell
docker compose up -d --build
```

如果本机 `8000` 端口已被占用，可以临时改用其他宿主机端口：

```powershell
$env:API_PORT = "8001"
docker compose up -d --build
```

访问地址也对应改为：

```text
http://127.0.0.1:8001/health
```

查看状态：

```powershell
docker compose ps
```

查看日志：

```powershell
docker compose logs -f api
```

停止服务：

```powershell
docker compose down
```

compose 当前提供：

```text
FastAPI API 服务
8000:8000 端口映射
.env 环境变量注入
./data:/app/data 数据目录挂载
/health 健康检查
/metrics JSON 指标
/metrics/prometheus Prometheus 文本指标
```

注意：

```text
不要把 docker compose config 的完整输出贴到公开位置。
如果 .env 中有真实密钥，该命令会把环境变量展开显示。
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

- 暂未拆分数据库、向量库和 API 服务。
- 暂未提供生产级密钥管理。
- 暂未接入独立 Prometheus 服务。
- 暂未提供 K8s manifests。

下一阶段再补：

```text
日志与 metrics
-> 服务器长期运行说明
-> PostgreSQL / Qdrant 服务拆分
-> K8s manifests
```
