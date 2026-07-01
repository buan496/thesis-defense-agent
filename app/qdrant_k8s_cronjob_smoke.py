from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Callable


CommandRunner = Callable[[str, int], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class QdrantK8sCronJobSmokeStepResult:
    name: str
    command: str
    status: str
    returncode: int | None
    stdout: str
    stderr: str
    notes: str


@dataclass(frozen=True)
class QdrantK8sCronJobSmokeReport:
    namespace: str
    task_name: str
    job_name: str
    cleanup_job: bool
    cleanup_cronjob: bool
    started_at: str
    finished_at: str
    overall_status: str
    results: list[QdrantK8sCronJobSmokeStepResult]


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


def execute_qdrant_k8s_cronjob_smoke(
    manifest_yaml: str,
    task_name: str,
    namespace: str,
    job_name: str | None = None,
    timeout_seconds: int = 180,
    cleanup_job: bool = False,
    cleanup_cronjob: bool = False,
    command_runner: CommandRunner = run_command,
) -> QdrantK8sCronJobSmokeReport:
    normalized_manifest = manifest_yaml.strip()
    normalized_task_name = _normalize_k8s_name(task_name, "task_name")
    normalized_namespace = _normalize_k8s_name(namespace, "namespace")
    normalized_job_name = (
        _normalize_k8s_name(job_name, "job_name")
        if job_name is not None
        else _build_manual_job_name(normalized_task_name)
    )

    if not normalized_manifest:
        raise ValueError("manifest_yaml must not be empty")

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than 0")

    started_at = _now_iso()
    results: list[QdrantK8sCronJobSmokeStepResult] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        manifest_path = Path(temp_dir) / "qdrant-cronjob.yaml"
        manifest_path.write_text(
            normalized_manifest + "\n",
            encoding="utf-8",
        )

        commands = [
            (
                "apply_cronjob",
                f'kubectl apply -f "{manifest_path}"',
                timeout_seconds,
            ),
            (
                "inspect_cronjob",
                (
                    f"kubectl get cronjob {normalized_task_name} "
                    f"-n {normalized_namespace} -o wide"
                ),
                timeout_seconds,
            ),
            (
                "trigger_manual_job",
                (
                    f"kubectl create job {normalized_job_name} "
                    f"--from=cronjob/{normalized_task_name} "
                    f"-n {normalized_namespace}"
                ),
                timeout_seconds,
            ),
            (
                "wait_manual_job",
                (
                    "kubectl wait "
                    f"--for=condition=complete job/{normalized_job_name} "
                    f"-n {normalized_namespace} "
                    f"--timeout={timeout_seconds}s"
                ),
                timeout_seconds + 10,
            ),
            (
                "inspect_manual_job",
                (
                    f"kubectl get job {normalized_job_name} "
                    f"-n {normalized_namespace} -o wide"
                ),
                timeout_seconds,
            ),
            (
                "inspect_manual_job_pods",
                (
                    f"kubectl get pods -n {normalized_namespace} "
                    f"-l job-name={normalized_job_name} -o wide"
                ),
                timeout_seconds,
            ),
            (
                "collect_manual_job_logs",
                (
                    f"kubectl logs job/{normalized_job_name} "
                    f"-n {normalized_namespace} --tail=200"
                ),
                timeout_seconds,
            ),
        ]

        if cleanup_job:
            commands.append(
                (
                    "cleanup_manual_job",
                    (
                        f"kubectl delete job {normalized_job_name} "
                        f"-n {normalized_namespace} --ignore-not-found=true"
                    ),
                    timeout_seconds,
                )
            )

        if cleanup_cronjob:
            commands.append(
                (
                    "cleanup_cronjob",
                    (
                        f"kubectl delete cronjob {normalized_task_name} "
                        f"-n {normalized_namespace} --ignore-not-found=true"
                    ),
                    timeout_seconds,
                )
            )

        for name, command, command_timeout in commands:
            results.append(
                _run_smoke_step(
                    name=name,
                    command=command,
                    timeout_seconds=command_timeout,
                    command_runner=command_runner,
                )
            )

    finished_at = _now_iso()
    overall_status = _calculate_overall_status(results)

    return QdrantK8sCronJobSmokeReport(
        namespace=normalized_namespace,
        task_name=normalized_task_name,
        job_name=normalized_job_name,
        cleanup_job=cleanup_job,
        cleanup_cronjob=cleanup_cronjob,
        started_at=started_at,
        finished_at=finished_at,
        overall_status=overall_status,
        results=results,
    )


def render_qdrant_k8s_cronjob_smoke_report(
    report: QdrantK8sCronJobSmokeReport,
) -> str:
    lines = [
        "# Qdrant Kubernetes CronJob Smoke Run Report",
        "",
        f"- Namespace: `{report.namespace}`",
        f"- CronJob: `{report.task_name}`",
        f"- Manual Job: `{report.job_name}`",
        f"- Cleanup Job: `{report.cleanup_job}`",
        f"- Cleanup CronJob: `{report.cleanup_cronjob}`",
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


def _run_smoke_step(
    name: str,
    command: str,
    timeout_seconds: int,
    command_runner: CommandRunner,
) -> QdrantK8sCronJobSmokeStepResult:
    try:
        completed = command_runner(command, timeout_seconds)
    except subprocess.TimeoutExpired as error:
        return QdrantK8sCronJobSmokeStepResult(
            name=name,
            command=command,
            status="failed",
            returncode=None,
            stdout=error.stdout or "",
            stderr=error.stderr or "",
            notes=f"command timed out after {timeout_seconds} seconds",
        )

    return QdrantK8sCronJobSmokeStepResult(
        name=name,
        command=command,
        status="passed" if completed.returncode == 0 else "failed",
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        notes="",
    )


def _calculate_overall_status(
    results: list[QdrantK8sCronJobSmokeStepResult],
) -> str:
    if any(result.status == "failed" for result in results):
        return "failed"

    return "passed"


def _build_manual_job_name(task_name: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = f"-manual-{timestamp}"
    max_prefix_length = 63 - len(suffix)
    return f"{task_name[:max_prefix_length].rstrip('-')}{suffix}"


def _normalize_k8s_name(value: str | None, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} must not be empty")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    if len(normalized) > 63:
        raise ValueError(f"{field_name} must be at most 63 characters")

    if re.fullmatch(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?", normalized) is None:
        raise ValueError(
            f"{field_name} must be a valid Kubernetes DNS label"
        )

    return normalized


def _sanitize_output(text: str) -> str:
    if not text:
        return ""

    sanitized_lines = []

    for line in text.splitlines():
        if any(
            marker in line.lower()
            for marker in [
                "token",
                "api_key",
                "apikey",
                "password",
                "secret",
                "authorization",
            ]
        ):
            sanitized_lines.append("[REDACTED]")
        else:
            sanitized_lines.append(line)

    return "\n".join(sanitized_lines)


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()
