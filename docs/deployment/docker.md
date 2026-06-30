# Docker 镜像构建说明

## 定位

当前 Dockerfile 和 docker-compose.yml 用于本地验证 FastAPI 服务容器化启动。

本阶段包含单容器 API 镜像，以及本机 Docker Compose 中的 Prometheus、Alertmanager、PostgreSQL 和 Qdrant 服务。K8s manifests 仍在后续阶段。

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

Prometheus 默认暴露在 `9090`：

```text
http://127.0.0.1:9090
```

如果本机 `9090` 端口已被占用：

```powershell
$env:PROMETHEUS_PORT = "9091"
docker compose up -d --build
```

Prometheus targets 页面：

```text
http://127.0.0.1:9091/targets
```

Alertmanager 默认暴露在 `9093`：

```text
http://127.0.0.1:9093
```

如果本机 `9093` 端口已被占用：

```powershell
$env:ALERTMANAGER_PORT = "9094"
docker compose up -d --build
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
Prometheus 服务
9090:9090 端口映射
Prometheus 抓取 api:8000/metrics/prometheus
Alertmanager 服务
9093:9093 端口映射
Prometheus 将告警发送到 alertmanager:9093
Alertmanager 将 webhook 发送到 api:8000/alerts/alertmanager
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

- 本机 Compose 已拆分 API、Prometheus、Alertmanager、PostgreSQL 和 Qdrant 服务。
- 暂未提供生产级密钥管理。
- Prometheus 当前用于本地学习版指标抓取和告警规则；Alertmanager 当前用于本机 webhook 路由，不包含外部通知渠道。
- 暂未提供 K8s manifests。

下一阶段再补：

```text
K8s manifests
-> 外部通知渠道
-> PostgreSQL / Qdrant 生产化治理
-> K8s manifests
```

服务器长期运行步骤见：

```text
docs/deployment/server.md
```
