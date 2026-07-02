# Contributing

本仓库是个人学习型 AI Agent 工程化项目，仍按工程化流程维护。所有代码、文档和配置改动都应可追踪、可测试、可回滚。

## 分支流程

不要直接在 `main` 上开发。常用分支命名：

- `feat/<topic>`：新增功能
- `fix/<topic>`：修复问题
- `docs/<topic>`：文档更新
- `chore/<topic>`：工程配置、仓库治理、依赖维护
- `ci/<topic>`：CI/CD 相关改动

推荐流程：

```powershell
git switch main
git pull --ff-only
git switch -c feat/example
uv run pytest -q
git status --short
git add <files>
git commit -m "Add example feature"
git push -u origin feat/example
gh pr create --base main --head feat/example --title "Add example feature" --body "..."
```

PR 合并后：

```powershell
git switch main
git pull --ff-only
git branch -d feat/example
git remote prune origin
```

## 提交前检查

至少运行：

```powershell
uv run pytest -q
```

涉及容器、部署或 CI 时，按改动范围补充：

```powershell
docker compose config
docker build -t thesis-defense-agent:local .
```

涉及 RAG、Agent、评估或 Task State 时，优先补充或更新对应 benchmark / evaluator 测试。

## 代码规则

- 保持小步提交，不把多个无关主题混在一个 PR。
- 不提交 `.env`、API Key、真实论文 PDF、向量库缓存、trace、运行报告。
- 不绕过已有测试门禁。
- 不用 LangGraph 覆盖现有手写 `app/task_*` 和 `app/agent.py`，LangGraph 只做旁路对照学习。
- 部署相关内容应进入 `docs/deployment/`、`k8s/`、`observability/` 或对应配置目录，不堆进 README。

## PR 要求

PR 描述应包含：

- 改动目的
- 主要变更
- 验证命令和结果
- 是否涉及密钥、数据文件、部署配置
- 后续未完成事项

仓库默认使用 squash merge，合并后删除远程功能分支。

