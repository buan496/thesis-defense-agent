# GitHub 仓库规范

本文档记录 `thesis-defense-agent` 的 GitHub 仓库元信息、协作文件和维护约定。README 只保留入口说明，细节放在这里。

## About 区描述

建议仓库 Description：

```text
论文答辩训练 Agent：RAG、Tool Calling、Task State、Memory、Trace、评估闭环、FastAPI/Docker/K8s 学习型 AI Agent 工程化项目。
```

建议 Topics：

```text
ai-agent
rag
tool-calling
llm
fastapi
langgraph
qdrant
milvus
docker
kubernetes
thesis-defense
agent-evaluation
```

## 仓库文件

当前应保留以下仓库规范文件：

- `README.md`：项目定位、当前能力、快速入口、文档索引
- `CONTRIBUTING.md`：分支、提交、测试、PR 规则
- `SECURITY.md`：密钥、数据、部署安全边界
- `.github/PULL_REQUEST_TEMPLATE.md`：PR 描述模板
- `.github/ISSUE_TEMPLATE/bug_report.md`：Bug 模板
- `.github/ISSUE_TEMPLATE/feature_request.md`：Feature 模板
- `.github/ISSUE_TEMPLATE/config.yml`：Issue 模板配置

## 分支策略

默认分支为 `main`。

常规开发流程：

```text
main
-> feature/chore/docs/ci branch
-> PR
-> CI
-> squash merge
-> delete remote branch
-> local main pull --ff-only
```

不建议直接推送到 `main`，除非是明确的紧急修复且没有分支保护限制。

## GitHub 设置建议

建议开启：

- Issues
- Squash merge
- Delete branch on merge
- Secret scanning / push protection（如果仓库权限支持）
- Branch protection：要求 CI 通过后才能合并

建议关闭或谨慎使用：

- Wiki：除非需要单独维护用户文档
- Projects：除非开始做正式排期

## License 状态

当前仓库采用 Apache License 2.0。

需要保留：

- 根目录 `LICENSE`
- README 中的许可证入口
- GitHub About 区的 license 自动识别结果

Apache-2.0 是宽松许可证，允许使用、修改和分发，并包含专利授权条款。对外复用时仍需遵守许可证文本中的保留声明、版权声明和 NOTICE 相关要求。
