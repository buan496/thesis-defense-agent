from dataclasses import dataclass
from datetime import datetime
import subprocess
from typing import Callable

from app.k8s_smoke_plan import K8sSmokePlan, K8sSmokeStep


CommandRunner = Callable[[str, int], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class K8sSmokeStepResult:
    name: str
    command: str
    status: str
    returncode: int | None
    stdout: str
    stderr: str
    notes: str


@dataclass(frozen=True)
class K8sSmokeRunReport:
    namespace: str
    kustomize_dir: str
    api_local_port: int
    apply_cluster: bool
    include_port_forward: bool
    include_rollback: bool
    started_at: str
    finished_at: str
    overall_status: str
    results: list[K8sSmokeStepResult]


def run_command(
    command: str,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )


def execute_k8s_smoke_plan(
    plan: K8sSmokePlan,
    apply_cluster: bool = False,
    include_port_forward: bool = False,
    include_rollback: bool = False,
    timeout_seconds: int = 120,
    command_runner: CommandRunner = run_command,
) -> K8sSmokeRunReport:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than 0")

    started_at = _now_iso()
    results = []

    for step in plan.steps:
        if _should_skip_step(
            step,
            apply_cluster=apply_cluster,
            include_port_forward=include_port_forward,
            include_rollback=include_rollback,
        ):
            results.append(
                K8sSmokeStepResult(
                    name=step.name,
                    command=step.command,
                    status="skipped",
                    returncode=None,
                    stdout="",
                    stderr="",
                    notes=_skip_reason(
                        step,
                        apply_cluster=apply_cluster,
                        include_port_forward=include_port_forward,
                        include_rollback=include_rollback,
                    ),
                )
            )
            continue

        try:
            completed = command_runner(
                step.command,
                timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            results.append(
                K8sSmokeStepResult(
                    name=step.name,
                    command=step.command,
                    status="failed",
                    returncode=None,
                    stdout=error.stdout or "",
                    stderr=error.stderr or "",
                    notes=(
                        "command timed out after "
                        f"{timeout_seconds} seconds"
                    ),
                )
            )
            continue

        status = "passed" if completed.returncode == 0 else "failed"
        results.append(
            K8sSmokeStepResult(
                name=step.name,
                command=step.command,
                status=status,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                notes="",
            )
        )

    finished_at = _now_iso()
    overall_status = _calculate_overall_status(results)

    return K8sSmokeRunReport(
        namespace=plan.namespace,
        kustomize_dir=plan.kustomize_dir,
        api_local_port=plan.api_local_port,
        apply_cluster=apply_cluster,
        include_port_forward=include_port_forward,
        include_rollback=include_rollback,
        started_at=started_at,
        finished_at=finished_at,
        overall_status=overall_status,
        results=results,
    )


def render_k8s_smoke_run_report(
    report: K8sSmokeRunReport,
) -> str:
    lines = [
        "# K8s Smoke Test Run Report",
        "",
        f"- Namespace: `{report.namespace}`",
        f"- Kustomize directory: `{report.kustomize_dir}`",
        f"- API local port: `{report.api_local_port}`",
        f"- Apply cluster steps: `{report.apply_cluster}`",
        f"- Include port-forward steps: `{report.include_port_forward}`",
        f"- Include rollback step: `{report.include_rollback}`",
        f"- Started at: `{report.started_at}`",
        f"- Finished at: `{report.finished_at}`",
        f"- Overall status: `{report.overall_status}`",
        "",
        "Do not paste real API keys, tokens, kubeconfig content, or other secrets into this report.",
        "",
    ]

    for index, result in enumerate(report.results, start=1):
        lines.extend(
            [
                f"## {index}. {result.name}",
                "",
                f"- Status: `{result.status}`",
                f"- Return code: `{result.returncode}`",
                f"- Notes: {result.notes or 'N/A'}",
                "",
                "Command:",
                "",
                "```powershell",
                result.command,
                "```",
                "",
                "Stdout:",
                "",
                "```text",
                _sanitize_output(result.stdout),
                "```",
                "",
                "Stderr:",
                "",
                "```text",
                _sanitize_output(result.stderr),
                "```",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _should_skip_step(
    step: K8sSmokeStep,
    apply_cluster: bool,
    include_port_forward: bool,
    include_rollback: bool,
) -> bool:
    if step.requires_cluster and not apply_cluster:
        return True

    if step.name in {"port_forward_api", "health_check_api"}:
        return not include_port_forward

    if step.name == "rollback_api":
        return not include_rollback

    return False


def _skip_reason(
    step: K8sSmokeStep,
    apply_cluster: bool,
    include_port_forward: bool,
    include_rollback: bool,
) -> str:
    if step.requires_cluster and not apply_cluster:
        return "cluster step skipped because apply_cluster is false"

    if (
        step.name in {"port_forward_api", "health_check_api"}
        and not include_port_forward
    ):
        return "port-forward dependent step skipped"

    if step.name == "rollback_api" and not include_rollback:
        return "rollback step skipped by default"

    return "skipped"


def _calculate_overall_status(
    results: list[K8sSmokeStepResult],
) -> str:
    if any(result.status == "failed" for result in results):
        return "failed"

    if all(result.status == "skipped" for result in results):
        return "skipped"

    return "passed"


def _sanitize_output(text: str) -> str:
    if not text:
        return ""

    sanitized_lines = []

    for line in text.splitlines():
        if any(
            marker in line.lower()
            for marker in ["token", "api_key", "apikey", "password", "secret"]
        ):
            sanitized_lines.append("[REDACTED]")
        else:
            sanitized_lines.append(line)

    return "\n".join(sanitized_lines)


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()
