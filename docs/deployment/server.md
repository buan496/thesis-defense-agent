# 服务器长期运行说明

## 定位

服务器不作为开发环境使用。

本项目推荐流程：

```text
本机开发 / 测试 / Docker 验证
-> GitHub PR / CI / main 分支
-> 服务器拉取 main
-> docker compose 长期运行
```

服务器只负责运行已经合并到 `main` 的稳定版本。

## 服务器前提

服务器需要准备：

```text
Git
Docker
Docker Compose
可访问 GitHub
可访问模型 API / Embedding API
```

不要求服务器安装 Python 开发环境。

## 首次部署

克隆仓库：

```powershell
git clone https://github.com/buan496/thesis-defense-agent.git
cd thesis-defense-agent
```

确认分支：

```powershell
git checkout main
git pull --ff-only
```

创建 `.env`：

```powershell
Copy-Item .env.example .env
```

然后在服务器本机编辑 `.env`，写入真实密钥和运行参数。

不要提交 `.env`。

## 数据目录

当前 compose 会挂载：

```text
./data:/app/data
```

因此服务器上的 `data/` 会保存：

```text
向量库
任务记录
训练报告
trace
长期记忆
```

如果服务器上需要使用已有论文向量库，可以把本机生成的非敏感数据按需复制到服务器 `data/`。

注意：真实论文 PDF、向量库、trace 和任务记录通常不建议直接提交 Git。

## 启动服务

默认端口：

```text
API: 8000
Prometheus: 9090
Alertmanager: 9093
```

启动：

```powershell
docker compose up -d --build
```

如果端口冲突：

```powershell
$env:API_PORT = "8001"
$env:PROMETHEUS_PORT = "9091"
$env:ALERTMANAGER_PORT = "9094"
docker compose up -d --build
```

## 验证服务

检查容器：

```powershell
docker compose ps
```

验证 API：

```powershell
curl.exe -sS http://127.0.0.1:8000/health
curl.exe -sS http://127.0.0.1:8000/version
curl.exe -sS http://127.0.0.1:8000/metrics/prometheus
```

验证 Prometheus：

```powershell
curl.exe -sS http://127.0.0.1:9090/-/ready
```

验证 Alertmanager：

```powershell
curl.exe -sS http://127.0.0.1:9093/-/ready
```

浏览器访问：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:9090/targets
http://127.0.0.1:9093
```

## 更新版本

本机完成开发并合并 PR 后，服务器执行：

```powershell
git checkout main
git pull --ff-only
docker compose up -d --build
```

如果只想重启：

```powershell
docker compose restart
```

## 查看日志

API 日志：

```powershell
docker compose logs -f api
```

Prometheus 日志：

```powershell
docker compose logs -f prometheus
```

Alertmanager 日志：

```powershell
docker compose logs -f alertmanager
```

最近日志：

```powershell
docker compose logs --tail 100 api
```

## 停止服务

停止并移除容器和网络：

```powershell
docker compose down
```

不删除 `data/`。

## 当前边界

当前服务器运行方案仍是学习版：

```text
PostgreSQL 本机 Compose 和 runtime smoke 已完成
Qdrant 本机最小后端已完成
未做用户鉴权
未做 HTTPS / 反向代理
Prometheus 告警规则和 Alertmanager 本机路由已完成
未接外部通知渠道 / on-call routing
未做日志集中采集
未做 K8s
```

后续服务器阶段按顺序推进：

```text
服务器长期运行验证
-> 反向代理 / HTTPS
-> 外部通知渠道
-> Qdrant 生产化治理 / Milvus
-> K8s manifests
```
