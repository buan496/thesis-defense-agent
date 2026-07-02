from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
from typing import Callable


CommandRunner = Callable[[str, int], subprocess.CompletedProcess[str]]
Sleeper = Callable[[float], None]


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


@dataclass(frozen=True)
class QdrantK8sCronJobScheduleObserveReport:
    namespace: str
    task_name: str
    scheduled_job_name: str | None
    cleanup_job: bool
    cleanup_cronjob: bool
    started_at: str
    finished_at: str
    overall_status: str
    results: list[QdrantK8sCronJobSmokeStepResult]


@dataclass(frozen=True)
class QdrantK8sCronJobMultiCycleObserveReport:
    namespace: str
    task_name: str
    scheduled_job_names: list[str]
    expected_cycles: int
    cleanup_jobs: bool
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


def execute_qdrant_k8s_cronjob_schedule_observe(
    manifest_yaml: str,
    task_name: str,
    namespace: str,
    timeout_seconds: int = 240,
    poll_interval_seconds: float = 5,
    cleanup_job: bool = False,
    cleanup_cronjob: bool = False,
    command_runner: CommandRunner = run_command,
    sleeper: Sleeper = time.sleep,
) -> QdrantK8sCronJobScheduleObserveReport:
    normalized_manifest = manifest_yaml.strip()
    normalized_task_name = _normalize_k8s_name(task_name, "task_name")
    normalized_namespace = _normalize_k8s_name(namespace, "namespace")

    if not normalized_manifest:
        raise ValueError("manifest_yaml must not be empty")

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than 0")

    if poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be greater than 0")

    started_at = _now_iso()
    results: list[QdrantK8sCronJobSmokeStepResult] = []
    scheduled_job_name = None

    with tempfile.TemporaryDirectory() as temp_dir:
        manifest_path = Path(temp_dir) / "qdrant-cronjob.yaml"
        manifest_path.write_text(
            normalized_manifest + "\n",
            encoding="utf-8",
        )

        initial_job_names, capture_result = _capture_cronjob_job_names(
            task_name=normalized_task_name,
            namespace=normalized_namespace,
            timeout_seconds=timeout_seconds,
            command_runner=command_runner,
            step_name="capture_existing_jobs",
        )
        results.append(capture_result)

        results.append(
            _run_smoke_step(
                name="apply_cronjob",
                command=f'kubectl apply -f "{manifest_path}"',
                timeout_seconds=timeout_seconds,
                command_runner=command_runner,
            )
        )

        results.append(
            _run_smoke_step(
                name="inspect_cronjob",
                command=(
                    f"kubectl get cronjob {normalized_task_name} "
                    f"-n {normalized_namespace} -o wide"
                ),
                timeout_seconds=timeout_seconds,
                command_runner=command_runner,
            )
        )

        scheduled_job_name, wait_created_result = _wait_for_new_scheduled_job(
            task_name=normalized_task_name,
            namespace=normalized_namespace,
            ignored_job_names=initial_job_names,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            command_runner=command_runner,
            sleeper=sleeper,
        )
        results.append(wait_created_result)

        if scheduled_job_name is not None:
            results.extend(
                _build_scheduled_job_evidence_results(
                    task_name=normalized_task_name,
                    namespace=normalized_namespace,
                    scheduled_job_name=scheduled_job_name,
                    timeout_seconds=timeout_seconds,
                    cleanup_job=cleanup_job,
                    cleanup_cronjob=cleanup_cronjob,
                    command_runner=command_runner,
                )
            )
        else:
            if cleanup_cronjob:
                results.append(
                    _run_smoke_step(
                        name="cleanup_cronjob",
                        command=(
                            f"kubectl delete cronjob {normalized_task_name} "
                            f"-n {normalized_namespace} --ignore-not-found=true"
                        ),
                        timeout_seconds=timeout_seconds,
                        command_runner=command_runner,
                    )
                )

    finished_at = _now_iso()
    overall_status = _calculate_overall_status(results)

    return QdrantK8sCronJobScheduleObserveReport(
        namespace=normalized_namespace,
        task_name=normalized_task_name,
        scheduled_job_name=scheduled_job_name,
        cleanup_job=cleanup_job,
        cleanup_cronjob=cleanup_cronjob,
        started_at=started_at,
        finished_at=finished_at,
        overall_status=overall_status,
        results=results,
    )


def render_qdrant_k8s_cronjob_schedule_observe_report(
    report: QdrantK8sCronJobScheduleObserveReport,
) -> str:
    lines = [
        "# Qdrant Kubernetes CronJob Schedule Observe Report",
        "",
        f"- Namespace: `{report.namespace}`",
        f"- CronJob: `{report.task_name}`",
        f"- Scheduled Job: `{report.scheduled_job_name or 'None'}`",
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


def execute_qdrant_k8s_cronjob_multi_cycle_observe(
    manifest_yaml: str,
    task_name: str,
    namespace: str,
    expected_cycles: int = 2,
    timeout_seconds: int = 420,
    poll_interval_seconds: float = 5,
    cleanup_jobs: bool = False,
    cleanup_cronjob: bool = False,
    command_runner: CommandRunner = run_command,
    sleeper: Sleeper = time.sleep,
) -> QdrantK8sCronJobMultiCycleObserveReport:
    normalized_manifest = manifest_yaml.strip()
    normalized_task_name = _normalize_k8s_name(task_name, "task_name")
    normalized_namespace = _normalize_k8s_name(namespace, "namespace")

    if not normalized_manifest:
        raise ValueError("manifest_yaml must not be empty")

    if expected_cycles <= 0:
        raise ValueError("expected_cycles must be greater than 0")

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than 0")

    if poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be greater than 0")

    started_at = _now_iso()
    results: list[QdrantK8sCronJobSmokeStepResult] = []
    scheduled_job_names: list[str] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        manifest_path = Path(temp_dir) / "qdrant-cronjob.yaml"
        manifest_path.write_text(
            normalized_manifest + "\n",
            encoding="utf-8",
        )

        initial_job_names, capture_result = _capture_cronjob_job_names(
            task_name=normalized_task_name,
            namespace=normalized_namespace,
            timeout_seconds=timeout_seconds,
            command_runner=command_runner,
            step_name="capture_existing_jobs",
        )
        results.append(capture_result)

        results.append(
            _run_smoke_step(
                name="apply_cronjob",
                command=f'kubectl apply -f "{manifest_path}"',
                timeout_seconds=timeout_seconds,
                command_runner=command_runner,
            )
        )

        results.append(
            _run_smoke_step(
                name="inspect_cronjob",
                command=(
                    f"kubectl get cronjob {normalized_task_name} "
                    f"-n {normalized_namespace} -o wide"
                ),
                timeout_seconds=timeout_seconds,
                command_runner=command_runner,
            )
        )

        scheduled_job_names, wait_created_result = _wait_for_scheduled_job_count(
            task_name=normalized_task_name,
            namespace=normalized_namespace,
            ignored_job_names=initial_job_names,
            expected_count=expected_cycles,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            command_runner=command_runner,
            sleeper=sleeper,
        )
        results.append(wait_created_result)

        for scheduled_job_name in scheduled_job_names:
            results.extend(
                _build_scheduled_job_evidence_results(
                    task_name=normalized_task_name,
                    namespace=normalized_namespace,
                    scheduled_job_name=scheduled_job_name,
                    timeout_seconds=timeout_seconds,
                    cleanup_job=cleanup_jobs,
                    cleanup_cronjob=False,
                    command_runner=command_runner,
                )
            )

        if cleanup_cronjob:
            results.append(
                _run_smoke_step(
                    name="cleanup_cronjob",
                    command=(
                        f"kubectl delete cronjob {normalized_task_name} "
                        f"-n {normalized_namespace} --ignore-not-found=true"
                    ),
                    timeout_seconds=timeout_seconds,
                    command_runner=command_runner,
                )
            )

    finished_at = _now_iso()
    overall_status = _calculate_overall_status(results)

    return QdrantK8sCronJobMultiCycleObserveReport(
        namespace=normalized_namespace,
        task_name=normalized_task_name,
        scheduled_job_names=scheduled_job_names,
        expected_cycles=expected_cycles,
        cleanup_jobs=cleanup_jobs,
        cleanup_cronjob=cleanup_cronjob,
        started_at=started_at,
        finished_at=finished_at,
        overall_status=overall_status,
        results=results,
    )


def render_qdrant_k8s_cronjob_multi_cycle_observe_report(
    report: QdrantK8sCronJobMultiCycleObserveReport,
) -> str:
    lines = [
        "# Qdrant Kubernetes CronJob Multi-Cycle Observe Report",
        "",
        f"- Namespace: `{report.namespace}`",
        f"- CronJob: `{report.task_name}`",
        f"- Expected cycles: `{report.expected_cycles}`",
        f"- Observed scheduled Jobs: `{len(report.scheduled_job_names)}`",
        f"- Scheduled Job names: `{', '.join(report.scheduled_job_names) or 'None'}`",
        f"- Cleanup Jobs: `{report.cleanup_jobs}`",
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


def _build_scheduled_job_evidence_results(
    task_name: str,
    namespace: str,
    scheduled_job_name: str,
    timeout_seconds: int,
    cleanup_job: bool,
    cleanup_cronjob: bool,
    command_runner: CommandRunner,
) -> list[QdrantK8sCronJobSmokeStepResult]:
    commands = [
        (
            "wait_scheduled_job",
            (
                "kubectl wait "
                f"--for=condition=complete job/{scheduled_job_name} "
                f"-n {namespace} "
                f"--timeout={timeout_seconds}s"
            ),
            timeout_seconds + 10,
        ),
        (
            "inspect_scheduled_job",
            f"kubectl get job {scheduled_job_name} -n {namespace} -o wide",
            timeout_seconds,
        ),
        (
            "inspect_scheduled_job_pods",
            (
                f"kubectl get pods -n {namespace} "
                f"-l job-name={scheduled_job_name} -o wide"
            ),
            timeout_seconds,
        ),
        (
            "collect_scheduled_job_logs",
            (
                f"kubectl logs job/{scheduled_job_name} "
                f"-n {namespace} --tail=200"
            ),
            timeout_seconds,
        ),
    ]

    if cleanup_job:
        commands.append(
            (
                "cleanup_scheduled_job",
                (
                    f"kubectl delete job {scheduled_job_name} "
                    f"-n {namespace} --ignore-not-found=true"
                ),
                timeout_seconds,
            )
        )

    if cleanup_cronjob:
        commands.append(
            (
                "cleanup_cronjob",
                (
                    f"kubectl delete cronjob {task_name} "
                    f"-n {namespace} --ignore-not-found=true"
                ),
                timeout_seconds,
            )
        )

    return [
        _run_smoke_step(
            name=name,
            command=command,
            timeout_seconds=command_timeout,
            command_runner=command_runner,
        )
        for name, command, command_timeout in commands
    ]


def _capture_cronjob_job_names(
    task_name: str,
    namespace: str,
    timeout_seconds: int,
    command_runner: CommandRunner,
    step_name: str,
) -> tuple[set[str], QdrantK8sCronJobSmokeStepResult]:
    command = f"kubectl get jobs -n {namespace} -o json"

    result = _run_smoke_step(
        name=step_name,
        command=command,
        timeout_seconds=timeout_seconds,
        command_runner=command_runner,
    )

    if result.status != "passed":
        return set(), result

    try:
        job_names = _extract_cronjob_job_names(result.stdout, task_name)
    except ValueError as error:
        return (
            set(),
            QdrantK8sCronJobSmokeStepResult(
                name=step_name,
                command=command,
                status="failed",
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                notes=str(error),
            ),
        )

    return job_names, result


def _wait_for_new_scheduled_job(
    task_name: str,
    namespace: str,
    ignored_job_names: set[str],
    timeout_seconds: int,
    poll_interval_seconds: float,
    command_runner: CommandRunner,
    sleeper: Sleeper,
) -> tuple[str | None, QdrantK8sCronJobSmokeStepResult]:
    command = f"kubectl get jobs -n {namespace} -o json"
    deadline = time.monotonic() + timeout_seconds
    attempts = 0
    last_stdout = ""
    last_stderr = ""
    last_returncode = None

    while True:
        attempts += 1
        result = _run_smoke_step(
            name="wait_scheduled_job_created",
            command=command,
            timeout_seconds=timeout_seconds,
            command_runner=command_runner,
        )
        last_stdout = result.stdout
        last_stderr = result.stderr
        last_returncode = result.returncode

        if result.status == "passed":
            try:
                job_names = _extract_cronjob_job_names(result.stdout, task_name)
            except ValueError as error:
                return (
                    None,
                    QdrantK8sCronJobSmokeStepResult(
                        name="wait_scheduled_job_created",
                        command=command,
                        status="failed",
                        returncode=result.returncode,
                        stdout=result.stdout,
                        stderr=result.stderr,
                        notes=str(error),
                    ),
                )

            new_job_names = sorted(job_names - ignored_job_names)

            if new_job_names:
                job_name = new_job_names[-1]
                return (
                    job_name,
                    QdrantK8sCronJobSmokeStepResult(
                        name="wait_scheduled_job_created",
                        command=command,
                        status="passed",
                        returncode=result.returncode,
                        stdout=result.stdout,
                        stderr=result.stderr,
                        notes=(
                            f"found scheduled job {job_name} "
                            f"after {attempts} attempt(s)"
                        ),
                    ),
                )

        if time.monotonic() >= deadline:
            return (
                None,
                QdrantK8sCronJobSmokeStepResult(
                    name="wait_scheduled_job_created",
                    command=command,
                    status="failed",
                    returncode=last_returncode,
                    stdout=last_stdout,
                    stderr=last_stderr,
                    notes=(
                        "no new scheduled job created within "
                        f"{timeout_seconds} seconds after {attempts} attempt(s)"
                    ),
                ),
            )

        sleeper(poll_interval_seconds)


def _wait_for_scheduled_job_count(
    task_name: str,
    namespace: str,
    ignored_job_names: set[str],
    expected_count: int,
    timeout_seconds: int,
    poll_interval_seconds: float,
    command_runner: CommandRunner,
    sleeper: Sleeper,
) -> tuple[list[str], QdrantK8sCronJobSmokeStepResult]:
    command = f"kubectl get jobs -n {namespace} -o json"
    deadline = time.monotonic() + timeout_seconds
    attempts = 0
    observed_job_names: list[str] = []
    observed_job_name_set: set[str] = set()
    last_stdout = ""
    last_stderr = ""
    last_returncode = None

    while True:
        attempts += 1
        result = _run_smoke_step(
            name="wait_scheduled_job_count",
            command=command,
            timeout_seconds=timeout_seconds,
            command_runner=command_runner,
        )
        last_stdout = result.stdout
        last_stderr = result.stderr
        last_returncode = result.returncode

        if result.status == "passed":
            try:
                job_names = _extract_cronjob_job_names(result.stdout, task_name)
            except ValueError as error:
                return (
                    observed_job_names,
                    QdrantK8sCronJobSmokeStepResult(
                        name="wait_scheduled_job_count",
                        command=command,
                        status="failed",
                        returncode=result.returncode,
                        stdout=result.stdout,
                        stderr=result.stderr,
                        notes=str(error),
                    ),
                )

            new_job_names = sorted(
                job_names - ignored_job_names - observed_job_name_set
            )

            for job_name in new_job_names:
                observed_job_names.append(job_name)
                observed_job_name_set.add(job_name)

            if len(observed_job_names) >= expected_count:
                return (
                    observed_job_names,
                    QdrantK8sCronJobSmokeStepResult(
                        name="wait_scheduled_job_count",
                        command=command,
                        status="passed",
                        returncode=result.returncode,
                        stdout=result.stdout,
                        stderr=result.stderr,
                        notes=(
                            f"found {len(observed_job_names)} scheduled job(s) "
                            f"after {attempts} attempt(s)"
                        ),
                    ),
                )

        if time.monotonic() >= deadline:
            return (
                observed_job_names,
                QdrantK8sCronJobSmokeStepResult(
                    name="wait_scheduled_job_count",
                    command=command,
                    status="failed",
                    returncode=last_returncode,
                    stdout=last_stdout,
                    stderr=last_stderr,
                    notes=(
                        f"found {len(observed_job_names)} / {expected_count} "
                        "scheduled job(s) within "
                        f"{timeout_seconds} seconds after {attempts} attempt(s)"
                    ),
                ),
            )

        sleeper(poll_interval_seconds)


def _extract_cronjob_job_names(jobs_json: str, task_name: str) -> set[str]:
    try:
        data = json.loads(jobs_json)
    except json.JSONDecodeError as error:
        raise ValueError("kubectl jobs output must be valid JSON") from error

    items = data.get("items")

    if not isinstance(items, list):
        raise ValueError("kubectl jobs JSON must contain an items list")

    job_names = set()

    for item in items:
        if not isinstance(item, dict):
            continue

        metadata = item.get("metadata") or {}

        if not isinstance(metadata, dict):
            continue

        name = metadata.get("name")

        if not isinstance(name, str):
            continue

        if _is_owned_by_cronjob(metadata, task_name):
            job_names.add(name)

    return job_names


def _is_owned_by_cronjob(metadata: dict, task_name: str) -> bool:
    owner_references = metadata.get("ownerReferences") or []

    if isinstance(owner_references, list):
        for owner in owner_references:
            if not isinstance(owner, dict):
                continue

            if owner.get("kind") == "CronJob" and owner.get("name") == task_name:
                return True

    labels = metadata.get("labels") or {}

    if isinstance(labels, dict):
        return labels.get("batch.kubernetes.io/cronjob-name") == task_name

    return False


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
