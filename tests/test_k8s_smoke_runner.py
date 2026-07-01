import subprocess

import pytest

from app.k8s_smoke_plan import build_k8s_smoke_plan
from app.k8s_smoke_runner import (
    execute_k8s_smoke_plan,
    render_k8s_smoke_run_report,
)


def successful_runner(
    command: str,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=command,
        returncode=0,
        stdout=f"ok: {command}",
        stderr="",
    )


def test_execute_k8s_smoke_plan_runs_only_offline_steps_by_default():
    commands = []

    def runner(
        command: str,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return successful_runner(command, timeout_seconds)

    plan = build_k8s_smoke_plan()
    report = execute_k8s_smoke_plan(
        plan,
        command_runner=runner,
    )

    assert commands == [
        "kubectl kustomize k8s/base",
    ]
    assert report.overall_status == "passed"
    assert report.results[0].status == "passed"
    assert report.results[1].status == "skipped"
    assert "apply_cluster is false" in report.results[1].notes


def test_execute_k8s_smoke_plan_runs_cluster_steps_when_enabled():
    commands = []

    def runner(
        command: str,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return successful_runner(command, timeout_seconds)

    plan = build_k8s_smoke_plan(namespace="test-ns")
    report = execute_k8s_smoke_plan(
        plan,
        apply_cluster=True,
        command_runner=runner,
    )

    assert "kubectl apply -k k8s/base" in commands
    assert (
        "kubectl rollout status deployment/thesis-defense-agent-api "
        "-n test-ns"
    ) in commands
    assert "kubectl rollout status statefulset/qdrant -n test-ns" in commands
    assert "kubectl get pods,svc,statefulset,pvc,pdb -n test-ns" in commands
    assert "kubectl port-forward service/api 18000:8000 -n test-ns" not in commands
    assert "kubectl rollout undo deployment/thesis-defense-agent-api -n test-ns" not in commands
    assert report.overall_status == "passed"


def test_execute_k8s_smoke_plan_can_include_port_forward_and_rollback():
    commands = []

    def runner(
        command: str,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return successful_runner(command, timeout_seconds)

    plan = build_k8s_smoke_plan(namespace="test-ns")
    report = execute_k8s_smoke_plan(
        plan,
        apply_cluster=True,
        include_port_forward=True,
        include_rollback=True,
        command_runner=runner,
    )

    assert "kubectl port-forward service/api 18000:8000 -n test-ns" in commands
    assert "curl.exe -f http://127.0.0.1:18000/health" in commands
    assert "kubectl rollout undo deployment/thesis-defense-agent-api -n test-ns" in commands
    assert all(result.status == "passed" for result in report.results)


def test_execute_k8s_smoke_plan_marks_failed_command():
    def runner(
        command: str,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout="",
            stderr="boom",
        )

    plan = build_k8s_smoke_plan()
    report = execute_k8s_smoke_plan(
        plan,
        command_runner=runner,
    )

    assert report.overall_status == "failed"
    assert report.results[0].status == "failed"
    assert report.results[0].returncode == 1
    assert report.results[0].stderr == "boom"


def test_execute_k8s_smoke_plan_rejects_invalid_timeout():
    plan = build_k8s_smoke_plan()

    with pytest.raises(ValueError, match="timeout_seconds"):
        execute_k8s_smoke_plan(
            plan,
            timeout_seconds=0,
        )


def test_render_k8s_smoke_run_report_sanitizes_secret_like_output():
    def runner(
        command: str,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="token: abc\nnormal line",
            stderr="api_key=secret",
        )

    plan = build_k8s_smoke_plan()
    report = execute_k8s_smoke_plan(
        plan,
        command_runner=runner,
    )
    markdown = render_k8s_smoke_run_report(report)

    assert "# K8s Smoke Test Run Report" in markdown
    assert "[REDACTED]" in markdown
    assert "normal line" in markdown
    assert "api_key=secret" not in markdown
