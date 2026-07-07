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

## 长期运行前置检查

开始服务器长期运行前，先生成前置检查和证据索引。

Docker Compose runtime：

```powershell
uv run python -m app.cli server-long-run-preflight `
  --environment server-docker `
  --runtime docker_compose `
  --operator "<your-name>" `
  --output data/reports/server_long_run_preflight.md
```

Kubernetes runtime：

```powershell
uv run python -m app.cli server-long-run-preflight `
  --environment server-k8s `
  --runtime kubernetes `
  --operator "<your-name>" `
  --output data/reports/server_long_run_preflight_k8s.md
```

详细说明见：

```text
docs/deployment/server-long-run-preflight.md
```

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

## 已验证状态

2026-07-06 至 2026-07-07 已在服务器 `home-server` 完成 Docker Compose runtime smoke 和 6 小时 long-run smoke。

验证版本：

```text
5cba838 Fix local long-run smoke decoding on Windows (#135)
```

运行服务：

```text
api
postgres
qdrant
milvus
prometheus
alertmanager
```

10 分钟 smoke 采样结果：

```text
采样窗口：2026-07-06T20:14:26+08:00 -> 2026-07-06T20:24:28+08:00
采样间隔：60 秒
采样轮数：11
结果：Compose / API / Version / Prometheus / Alertmanager / Qdrant 全部 PASS
```

服务器报告路径：

```text
/home/server/apps/thesis-defense-agent/data/reports/server_long_run_smoke_10m.md
```

6 小时 long-run smoke 采样结果：

```text
采样窗口：2026-07-06T22:28:14+08:00 -> 2026-07-07T04:28:38+08:00
采样间隔：300 秒
采样轮数：73
失败次数：0
结果：Compose / API / Version / Prometheus / Alertmanager / Qdrant / Milvus / Postgres 全部 PASS
```

服务器报告路径：

```text
/home/server/apps/thesis-defense-agent/data/reports/server_long_run_smoke_6h.md
```

边界说明：

```text
10 分钟 smoke 证明服务能在服务器 Docker Compose runtime 中正常启动并连续通过基础健康检查。
6 小时 long-run smoke 证明服务栈可以跨多个小时保持基础健康检查稳定。
当前还不是 24h 或多天运行验证。
当前尚未覆盖真实告警触发、真实通知通道、故障恢复演练和数据恢复 drill。
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
server-long-run-preflight 前置检查和证据索引已完成
未做用户鉴权
未做 HTTPS / 反向代理
Prometheus 告警规则和 Alertmanager 本机路由已完成
未接外部通知渠道 / on-call routing
未做日志集中采集
K8s 本机 kind 验证已完成，但服务器 K8s 长期运行尚未完成
```

后续服务器阶段按顺序推进：

```text
服务器长期运行验证
-> 反向代理 / HTTPS
-> 外部通知渠道
-> Qdrant 生产化治理 / Milvus
-> K8s manifests
```
