from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ServerLongRunPreflightCheck:
    name: str
    category: str
    status: str
    purpose: str
    commands: list[str]
    acceptance_criteria: list[str]
    evidence: list[str]
    notes: str = ""


@dataclass(frozen=True)
class ServerLongRunPreflightReport:
    environment: str
    runtime: str
    operator: str
    generated_at: str
    checks: list[ServerLongRunPreflightCheck]


def build_server_long_run_preflight(
    environment: str = "server",
    runtime: str = "docker_compose",
    operator: str = "operator",
) -> ServerLongRunPreflightReport:
    normalized_environment = _normalize_required_text(
        environment,
        "environment",
    )
    normalized_runtime = _normalize_required_text(runtime, "runtime")
    normalized_operator = _normalize_required_text(operator, "operator")

    if normalized_runtime not in {"docker_compose", "kubernetes"}:
        raise ValueError("runtime must be docker_compose or kubernetes")

    checks = _build_common_checks()

    if normalized_runtime == "docker_compose":
        checks.extend(_build_docker_compose_checks())
    else:
        checks.extend(_build_kubernetes_checks())

    checks.extend(_build_long_run_checks())

    return ServerLongRunPreflightReport(
        environment=normalized_environment,
        runtime=normalized_runtime,
        operator=normalized_operator,
        generated_at=_now_iso(),
        checks=checks,
    )


def render_server_long_run_preflight_report(
    report: ServerLongRunPreflightReport,
) -> str:
    lines = [
        "# Server Long-Run Preflight Report",
        "",
        f"- Environment: `{report.environment}`",
        f"- Runtime: `{report.runtime}`",
        f"- Operator: `{report.operator}`",
        f"- Generated at: `{report.generated_at}`",
        f"- Check count: `{len(report.checks)}`",
        "",
        "Do not paste real API keys, passwords, kubeconfig content, private endpoints, or tokens into this report.",
        "",
        "## Summary",
        "",
        "| # | Category | Check | Status |",
        "|---|---|---|---|",
    ]

    for index, check in enumerate(report.checks, start=1):
        lines.append(
            f"| {index} | `{check.category}` | `{check.name}` | `{check.status}` |"
        )

    lines.append("")

    for index, check in enumerate(report.checks, start=1):
        lines.extend(
            [
                f"## {index}. {check.name}",
                "",
                f"- Category: `{check.category}`",
                f"- Status: `{check.status}`",
                f"- Purpose: {check.purpose}",
                "",
                "Commands:",
                "",
                "```powershell",
                "\n".join(check.commands) if check.commands else "N/A",
                "```",
                "",
                "Acceptance criteria:",
                "",
            ]
        )

        lines.extend(f"- {item}" for item in check.acceptance_criteria)
        lines.extend(["", "Evidence to save:", ""])
        lines.extend(f"- {item}" for item in check.evidence)

        if check.notes:
            lines.extend(["", f"Notes: {check.notes}"])

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _build_common_checks() -> list[ServerLongRunPreflightCheck]:
    return [
        ServerLongRunPreflightCheck(
            name="source_control_baseline",
            category="release",
            status="manual_required",
            purpose="Ensure the server only runs code merged into main.",
            commands=[
                "git checkout main",
                "git pull --ff-only",
                "git status --short --branch",
                "git log --oneline -5",
            ],
            acceptance_criteria=[
                "Working tree is clean.",
                "Local main points to origin/main.",
                "Latest commit is the intended release commit.",
            ],
            evidence=[
                "Sanitized git status output.",
                "Latest commit hash and PR number.",
            ],
        ),
        ServerLongRunPreflightCheck(
            name="secret_boundary",
            category="security",
            status="manual_required",
            purpose="Verify secrets are local runtime configuration and never committed.",
            commands=[
                "Test-Path .env",
                "git status --short --ignored=no",
                "git check-ignore .env",
            ],
            acceptance_criteria=[
                ".env exists on the server.",
                ".env is ignored by Git.",
                "No real secrets appear in git status, logs, reports, or screenshots.",
            ],
            evidence=[
                "Boolean result that .env exists.",
                "git check-ignore output for .env.",
            ],
            notes="Do not paste .env contents into reports.",
        ),
        ServerLongRunPreflightCheck(
            name="quality_gate_baseline",
            category="quality",
            status="manual_required",
            purpose="Confirm the code passed local and GitHub quality gates before long-run.",
            commands=[
                "uv run pytest -q",
                "gh pr status",
                "gh run list --branch main --limit 5",
            ],
            acceptance_criteria=[
                "Offline tests pass.",
                "No open release-blocking PR remains.",
                "Recent main CI runs are successful.",
            ],
            evidence=[
                "pytest summary.",
                "GitHub Actions run summary.",
            ],
        ),
        ServerLongRunPreflightCheck(
            name="runtime_data_boundary",
            category="data",
            status="manual_required",
            purpose="Make persistent runtime data explicit before starting long-run.",
            commands=[
                "Get-ChildItem data -Force",
                "git status --short --ignored=no",
            ],
            acceptance_criteria=[
                "Required data artifacts are present or intentionally rebuilt.",
                "Runtime artifacts under data/ are not accidentally staged.",
                "Sensitive PDFs, traces, task records, and backup files are not committed.",
            ],
            evidence=[
                "Sanitized data directory inventory.",
                "Confirmation that runtime artifacts remain outside Git.",
            ],
        ),
    ]


def _build_docker_compose_checks() -> list[ServerLongRunPreflightCheck]:
    return [
        ServerLongRunPreflightCheck(
            name="docker_compose_runtime",
            category="runtime",
            status="manual_required",
            purpose="Verify Docker and Compose are available before starting services.",
            commands=[
                "docker version",
                "docker compose version",
                "docker compose config",
            ],
            acceptance_criteria=[
                "Docker daemon is reachable.",
                "Compose file renders successfully.",
                "No required environment variable is missing from rendered config.",
            ],
            evidence=[
                "Docker version summary.",
                "Compose config success result.",
            ],
        ),
        ServerLongRunPreflightCheck(
            name="compose_service_health",
            category="runtime",
            status="manual_required",
            purpose="Start the stack and verify API, Prometheus, Alertmanager, and vector DB health.",
            commands=[
                "docker compose up -d --build",
                "docker compose ps",
                "curl.exe -f http://127.0.0.1:8000/health",
                "curl.exe -f http://127.0.0.1:8000/version",
                "curl.exe -f http://127.0.0.1:9090/-/ready",
                "curl.exe -f http://127.0.0.1:9093/-/ready",
                "curl.exe -f http://127.0.0.1:6333/readyz",
            ],
            acceptance_criteria=[
                "All required containers are running or healthy.",
                "API health endpoint returns ok.",
                "Prometheus and Alertmanager are ready.",
                "Qdrant readiness endpoint is reachable if Qdrant is enabled.",
            ],
            evidence=[
                "docker compose ps output.",
                "Sanitized health-check responses.",
            ],
        ),
        ServerLongRunPreflightCheck(
            name="compose_logs_and_rollback",
            category="operations",
            status="manual_required",
            purpose="Confirm logs and rollback commands are known before leaving services running.",
            commands=[
                "docker compose logs --tail 100 api",
                "docker compose logs --tail 100 prometheus",
                "docker compose logs --tail 100 alertmanager",
                "docker compose down",
                "git pull --ff-only",
                "docker compose up -d --build",
            ],
            acceptance_criteria=[
                "Recent logs contain no repeating startup failures.",
                "Rollback and restart commands are documented.",
                "Operator knows how to stop services without deleting data.",
            ],
            evidence=[
                "Sanitized tail logs.",
                "Rollback command record.",
            ],
        ),
    ]


def _build_kubernetes_checks() -> list[ServerLongRunPreflightCheck]:
    return [
        ServerLongRunPreflightCheck(
            name="kubernetes_context",
            category="runtime",
            status="manual_required",
            purpose="Verify kubectl is pointed at the intended cluster.",
            commands=[
                "kubectl config current-context",
                "kubectl get namespace thesis-defense-agent",
                "kubectl apply --dry-run=client --validate=false -k k8s/base",
            ],
            acceptance_criteria=[
                "Current context is the intended server or local cluster.",
                "Namespace exists or can be created from manifests.",
                "Client-side manifest dry-run passes.",
            ],
            evidence=[
                "Current context name with private details removed.",
                "Dry-run success output.",
            ],
            notes="Do not commit kubeconfig or cluster credentials.",
        ),
        ServerLongRunPreflightCheck(
            name="kubernetes_rollout_health",
            category="runtime",
            status="manual_required",
            purpose="Verify Kubernetes workloads roll out and expose expected services.",
            commands=[
                "kubectl apply -k k8s/base",
                "kubectl rollout status deployment/thesis-defense-agent-api -n thesis-defense-agent",
                "kubectl rollout status statefulset/qdrant -n thesis-defense-agent",
                "kubectl rollout status deployment/thesis-defense-agent-prometheus -n thesis-defense-agent",
                "kubectl rollout status deployment/thesis-defense-agent-alertmanager -n thesis-defense-agent",
                "kubectl get pod,svc,statefulset,pvc,pdb -n thesis-defense-agent",
            ],
            acceptance_criteria=[
                "API, Prometheus, Alertmanager, and Qdrant rollouts complete.",
                "Qdrant PVC is Bound.",
                "Services expose expected cluster ports.",
            ],
            evidence=[
                "Sanitized rollout status.",
                "Workload inventory output.",
            ],
        ),
        ServerLongRunPreflightCheck(
            name="kubernetes_cronjob_scheduler",
            category="operations",
            status="manual_required",
            purpose="Verify Qdrant snapshot drill can be scheduled repeatedly in Kubernetes.",
            commands=[
                "uv run python -m app.cli qdrant-k8s-cronjob-multi-cycle-observe --namespace thesis-defense-agent --cron-schedule \"* * * * *\" --expected-cycles 2 --cleanup-jobs --cleanup-cronjob --output data/reports/qdrant_k8s_cronjob_multi_cycle_observe.md",
                "kubectl get cronjob,job -n thesis-defense-agent",
            ],
            acceptance_criteria=[
                "At least two naturally scheduled CronJob Jobs complete.",
                "Job logs show snapshot create and download completed.",
                "No CronJob or Job remains after cleanup.",
            ],
            evidence=[
                "Sanitized multi-cycle observe report.",
                "Post-cleanup kubectl get cronjob,job output.",
            ],
        ),
    ]


def _build_long_run_checks() -> list[ServerLongRunPreflightCheck]:
    return [
        ServerLongRunPreflightCheck(
            name="observability_baseline",
            category="observability",
            status="manual_required",
            purpose="Confirm metrics, alerts, and logs are visible before long-run.",
            commands=[
                "curl.exe -f http://127.0.0.1:8000/metrics/prometheus",
                "curl.exe -f http://127.0.0.1:9090/api/v1/targets",
                "curl.exe -f http://127.0.0.1:9093/api/v2/status",
            ],
            acceptance_criteria=[
                "API metrics endpoint is reachable.",
                "Prometheus target for API is up.",
                "Alertmanager status endpoint is reachable.",
            ],
            evidence=[
                "Sanitized metrics endpoint status.",
                "Prometheus target up summary.",
                "Alertmanager ready summary.",
            ],
        ),
        ServerLongRunPreflightCheck(
            name="long_run_observation_window",
            category="operations",
            status="manual_required",
            purpose="Define the observation window and evidence collection cadence.",
            commands=[
                "docker compose ps",
                "docker compose logs --tail 100 api",
                "curl.exe -f http://127.0.0.1:8000/health",
                "curl.exe -f http://127.0.0.1:9090/-/ready",
            ],
            acceptance_criteria=[
                "Observation window is defined before start, for example 6h or 24h.",
                "Health, logs, and scheduler status are sampled on a fixed cadence.",
                "Failures are recorded with timestamp, command, sanitized output, and recovery action.",
            ],
            evidence=[
                "Start timestamp.",
                "Periodic health samples.",
                "Final summary with pass/fail decision.",
            ],
        ),
        ServerLongRunPreflightCheck(
            name="rollback_and_data_recovery",
            category="recovery",
            status="manual_required",
            purpose="Confirm the operator can roll back code and recover vector data.",
            commands=[
                "git log --oneline -5",
                "docker compose down",
                "uv run python -m app.cli qdrant-snapshot-drill-run --collection thesis_chunks --restore-collection thesis_chunks_restore --confirm-restore-collection thesis_chunks_restore --skip-compare",
            ],
            acceptance_criteria=[
                "Previous release commit is known.",
                "Stop/restart path is documented.",
                "Qdrant snapshot drill can restore into a disposable collection when enabled.",
            ],
            evidence=[
                "Release and rollback commit hashes.",
                "Sanitized snapshot drill report.",
            ],
            notes="Restore must target a disposable collection unless a production cutover plan exists.",
        ),
    ]


def _normalize_required_text(value: str, field_name: str) -> str:
    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    return normalized


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()
