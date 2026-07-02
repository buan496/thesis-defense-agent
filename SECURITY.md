# Security Policy

## 支持范围

当前仓库是个人学习型项目，不承诺生产级安全响应 SLA。安全规则主要覆盖：

- API Key 和 `.env` 管理
- 论文文档、训练记录、trace、向量库等本地数据
- Docker / Kubernetes / observability 配置
- GitHub Actions 和 CI 日志中的敏感信息泄露风险

## 敏感信息规则

不要提交以下内容：

- `.env`
- API Key、Token、SSH 私钥、服务器密码
- 真实用户数据或未脱敏论文
- `data/vector_store.json`
- `data/traces/`
- `data/reports/`
- `data/task_reports/`
- 数据库 dump、Qdrant / Milvus 备份文件

如果误提交敏感信息：

1. 立即撤销或轮换对应密钥。
2. 从最新提交中移除文件。
3. 如已推送到远程，按 GitHub secret exposure 处理流程清理历史。
4. 不要在 Issue、PR 或 CI 日志中再次粘贴密钥原文。

## 漏洞报告

如果发现安全问题：

- 不要在公开 Issue 中粘贴密钥、服务器地址、完整日志或真实数据。
- 优先通过 GitHub 的私密安全报告能力联系维护者。
- 如果只能通过公开 Issue 描述问题，请只提交最小复现和脱敏信息。

## 部署边界

本仓库包含 Docker、Prometheus、PostgreSQL、Qdrant、Milvus 和 Kubernetes 的学习型配置。默认配置不等同于生产安全配置。用于公网或长期服务前，至少需要单独补齐：

- 认证与授权
- TLS
- 网络隔离
- 密钥管理
- 数据备份与恢复演练
- 审计日志与告警策略

