import subprocess

import pytest

from app import cli
from app.qdrant_k8s_cronjob_smoke import (
    QdrantK8sCronJobMultiCycleObserveReport,
    QdrantK8sCronJobScheduleObserveReport,
    QdrantK8sCronJobSmokeReport,
    QdrantK8sCronJobSmokeStepResult,
    execute_qdrant_k8s_cronjob_multi_cycle_observe,
    execute_qdrant_k8s_cronjob_schedule_observe,
    execute_qdrant_k8s_cronjob_smoke,
    render_qdrant_k8s_cronjob_multi_cycle_observe_report,
    render_qdrant_k8s_cronjob_schedule_observe_report,
    render_qdrant_k8s_cronjob_smoke_report,
)


def completed(command: str, returncode: int = 0):
    return subprocess.CompletedProcess(
        args=command,
        returncode=returncode,
        stdout=f"ok: {command}",
        stderr="" if returncode == 0 else "boom",
    )


def fake_smoke_report(overall_status: str = "passed"):
    return QdrantK8sCronJobSmokeReport(
        namespace="agent",
        task_name="qdrant-drill",
        job_name="qdrant-drill-manual",
        cleanup_job=True,
        cleanup_cronjob=True,
        started_at="2026-07-01T00:00:00",
        finished_at="2026-07-01T00:00:01",
        overall_status=overall_status,
        results=[
            QdrantK8sCronJobSmokeStepResult(
                name="apply_cronjob",
                command="kubectl apply -f manifest.yaml",
                status=overall_status,
                returncode=0 if overall_status == "passed" else 1,
                stdout="applied",
                stderr="" if overall_status == "passed" else "failed",
                notes="",
            )
        ],
    )


def fake_observe_report(overall_status: str = "passed"):
    return QdrantK8sCronJobScheduleObserveReport(
        namespace="agent",
        task_name="qdrant-drill",
        scheduled_job_name="qdrant-drill-123",
        cleanup_job=True,
        cleanup_cronjob=True,
        started_at="2026-07-01T00:00:00",
        finished_at="2026-07-01T00:00:01",
        overall_status=overall_status,
        results=[
            QdrantK8sCronJobSmokeStepResult(
                name="wait_scheduled_job_created",
                command="kubectl get jobs -n agent -o json",
                status=overall_status,
                returncode=0 if overall_status == "passed" else 1,
                stdout='{"items":[]}',
                stderr="" if overall_status == "passed" else "failed",
                notes="",
            )
        ],
    )


def fake_multi_cycle_observe_report(overall_status: str = "passed"):
    return QdrantK8sCronJobMultiCycleObserveReport(
        namespace="agent",
        task_name="qdrant-drill",
        scheduled_job_names=["qdrant-drill-123", "qdrant-drill-124"],
        expected_cycles=2,
        cleanup_jobs=True,
        cleanup_cronjob=True,
        started_at="2026-07-01T00:00:00",
        finished_at="2026-07-01T00:00:01",
        overall_status=overall_status,
        results=[
            QdrantK8sCronJobSmokeStepResult(
                name="wait_scheduled_job_count",
                command="kubectl get jobs -n agent -o json",
                status=overall_status,
                returncode=0 if overall_status == "passed" else 1,
                stdout='{"items":[]}',
                stderr="" if overall_status == "passed" else "failed",
                notes="",
            )
        ],
    )


def jobs_json(*names: str, owner: str = "qdrant-drill") -> str:
    return (
        '{"items":['
        + ",".join(
            (
                '{"metadata":{'
                f'"name":"{name}",'
                f'"ownerReferences":[{{"kind":"CronJob","name":"{owner}"}}],'
                f'"labels":{{"batch.kubernetes.io/cronjob-name":"{owner}"}}'
                "}}"
            )
            for name in names
        )
        + "]}"
    )


def test_execute_qdrant_k8s_cronjob_smoke_runs_expected_commands():
    commands = []

    def fake_runner(command: str, timeout_seconds: int):
        commands.append((command, timeout_seconds))
        return completed(command)

    report = execute_qdrant_k8s_cronjob_smoke(
        manifest_yaml="kind: CronJob",
        task_name="qdrant-drill",
        namespace="agent",
        job_name="qdrant-drill-manual",
        timeout_seconds=30,
        cleanup_job=True,
        cleanup_cronjob=True,
        command_runner=fake_runner,
    )

    command_texts = [command for command, _ in commands]

    assert report.overall_status == "passed"
    assert report.job_name == "qdrant-drill-manual"
    assert command_texts[0].startswith('kubectl apply -f "')
    assert "kubectl get cronjob qdrant-drill -n agent -o wide" in command_texts
    assert (
        "kubectl create job qdrant-drill-manual "
        "--from=cronjob/qdrant-drill -n agent"
    ) in command_texts
    assert (
        "kubectl wait --for=condition=complete "
        "job/qdrant-drill-manual -n agent --timeout=30s"
    ) in command_texts
    assert "kubectl logs job/qdrant-drill-manual -n agent --tail=200" in command_texts
    assert (
        "kubectl delete job qdrant-drill-manual "
        "-n agent --ignore-not-found=true"
    ) in command_texts
    assert (
        "kubectl delete cronjob qdrant-drill "
        "-n agent --ignore-not-found=true"
    ) in command_texts


def test_execute_qdrant_k8s_cronjob_smoke_records_failed_command_and_continues():
    def fake_runner(command: str, timeout_seconds: int):
        if "kubectl wait" in command:
            return completed(command, returncode=1)

        return completed(command)

    report = execute_qdrant_k8s_cronjob_smoke(
        manifest_yaml="kind: CronJob",
        task_name="qdrant-drill",
        namespace="agent",
        job_name="qdrant-drill-manual",
        command_runner=fake_runner,
    )

    assert report.overall_status == "failed"
    assert any(
        result.name == "wait_manual_job" and result.status == "failed"
        for result in report.results
    )
    assert report.results[-1].name == "collect_manual_job_logs"


def test_execute_qdrant_k8s_cronjob_smoke_validates_inputs():
    with pytest.raises(ValueError, match="manifest_yaml"):
        execute_qdrant_k8s_cronjob_smoke(
            manifest_yaml=" ",
            task_name="qdrant-drill",
            namespace="agent",
        )

    with pytest.raises(ValueError, match="task_name"):
        execute_qdrant_k8s_cronjob_smoke(
            manifest_yaml="kind: CronJob",
            task_name="Bad_Name",
            namespace="agent",
        )

    with pytest.raises(ValueError, match="timeout_seconds"):
        execute_qdrant_k8s_cronjob_smoke(
            manifest_yaml="kind: CronJob",
            task_name="qdrant-drill",
            namespace="agent",
            timeout_seconds=0,
        )


def test_render_qdrant_k8s_cronjob_smoke_report_sanitizes_sensitive_output():
    report = QdrantK8sCronJobSmokeReport(
        namespace="agent",
        task_name="qdrant-drill",
        job_name="qdrant-drill-manual",
        cleanup_job=False,
        cleanup_cronjob=False,
        started_at="2026-07-01T00:00:00",
        finished_at="2026-07-01T00:00:01",
        overall_status="passed",
        results=[
            QdrantK8sCronJobSmokeStepResult(
                name="collect_manual_job_logs",
                command="kubectl logs job/qdrant-drill-manual",
                status="passed",
                returncode=0,
                stdout="api_key=secret\nsnapshot ok",
                stderr="",
                notes="",
            )
        ],
    )

    rendered = render_qdrant_k8s_cronjob_smoke_report(report)

    assert "# Qdrant Kubernetes CronJob Smoke Run Report" in rendered
    assert "[REDACTED]" in rendered
    assert "snapshot ok" in rendered
    assert "api_key=secret" not in rendered


def test_execute_qdrant_k8s_cronjob_schedule_observe_waits_for_natural_job():
    commands = []
    job_list_calls = 0
    sleeps = []

    def fake_runner(command: str, timeout_seconds: int):
        nonlocal job_list_calls
        commands.append(command)

        if command == "kubectl get jobs -n agent -o json":
            job_list_calls += 1

            if job_list_calls < 3:
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout=jobs_json(),
                    stderr="",
                )

            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=jobs_json("qdrant-drill-123"),
                stderr="",
            )

        return completed(command)

    report = execute_qdrant_k8s_cronjob_schedule_observe(
        manifest_yaml="kind: CronJob",
        task_name="qdrant-drill",
        namespace="agent",
        timeout_seconds=30,
        poll_interval_seconds=0.1,
        cleanup_job=True,
        cleanup_cronjob=True,
        command_runner=fake_runner,
        sleeper=lambda seconds: sleeps.append(seconds),
    )

    assert report.overall_status == "passed"
    assert report.scheduled_job_name == "qdrant-drill-123"
    assert "kubectl create job" not in "\n".join(commands)
    assert (
        "kubectl wait --for=condition=complete "
        "job/qdrant-drill-123 -n agent --timeout=30s"
    ) in commands
    assert "kubectl logs job/qdrant-drill-123 -n agent --tail=200" in commands
    assert "kubectl delete job qdrant-drill-123 -n agent --ignore-not-found=true" in commands
    assert "kubectl delete cronjob qdrant-drill -n agent --ignore-not-found=true" in commands
    assert sleeps == [0.1]
    assert any(
        result.name == "wait_scheduled_job_created"
        and "found scheduled job qdrant-drill-123" in result.notes
        for result in report.results
    )


def test_execute_qdrant_k8s_cronjob_schedule_observe_ignores_existing_jobs():
    calls = 0

    def fake_runner(command: str, timeout_seconds: int):
        nonlocal calls

        if command == "kubectl get jobs -n agent -o json":
            calls += 1

            if calls == 1:
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout=jobs_json("qdrant-drill-old"),
                    stderr="",
                )

            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=jobs_json("qdrant-drill-old", "qdrant-drill-new"),
                stderr="",
            )

        return completed(command)

    report = execute_qdrant_k8s_cronjob_schedule_observe(
        manifest_yaml="kind: CronJob",
        task_name="qdrant-drill",
        namespace="agent",
        timeout_seconds=30,
        poll_interval_seconds=0.1,
        command_runner=fake_runner,
        sleeper=lambda seconds: None,
    )

    assert report.overall_status == "passed"
    assert report.scheduled_job_name == "qdrant-drill-new"


def test_execute_qdrant_k8s_cronjob_schedule_observe_reports_missing_job():
    def fake_runner(command: str, timeout_seconds: int):
        if command == "kubectl get jobs -n agent -o json":
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=jobs_json(),
                stderr="",
            )

        return completed(command)

    report = execute_qdrant_k8s_cronjob_schedule_observe(
        manifest_yaml="kind: CronJob",
        task_name="qdrant-drill",
        namespace="agent",
        timeout_seconds=1,
        poll_interval_seconds=0.1,
        cleanup_cronjob=True,
        command_runner=fake_runner,
        sleeper=lambda seconds: None,
    )

    assert report.overall_status == "failed"
    assert report.scheduled_job_name is None
    assert any(
        result.name == "wait_scheduled_job_created"
        and "no new scheduled job" in result.notes
        for result in report.results
    )
    assert report.results[-1].name == "cleanup_cronjob"


def test_execute_qdrant_k8s_cronjob_schedule_observe_validates_inputs():
    with pytest.raises(ValueError, match="manifest_yaml"):
        execute_qdrant_k8s_cronjob_schedule_observe(
            manifest_yaml=" ",
            task_name="qdrant-drill",
            namespace="agent",
        )

    with pytest.raises(ValueError, match="poll_interval_seconds"):
        execute_qdrant_k8s_cronjob_schedule_observe(
            manifest_yaml="kind: CronJob",
            task_name="qdrant-drill",
            namespace="agent",
            poll_interval_seconds=0,
        )


def test_render_qdrant_k8s_cronjob_schedule_observe_report_sanitizes_output():
    report = QdrantK8sCronJobScheduleObserveReport(
        namespace="agent",
        task_name="qdrant-drill",
        scheduled_job_name="qdrant-drill-123",
        cleanup_job=False,
        cleanup_cronjob=False,
        started_at="2026-07-01T00:00:00",
        finished_at="2026-07-01T00:00:01",
        overall_status="passed",
        results=[
            QdrantK8sCronJobSmokeStepResult(
                name="collect_scheduled_job_logs",
                command="kubectl logs job/qdrant-drill-123",
                status="passed",
                returncode=0,
                stdout="authorization: secret\nsnapshot ok",
                stderr="",
                notes="",
            )
        ],
    )

    rendered = render_qdrant_k8s_cronjob_schedule_observe_report(report)

    assert "# Qdrant Kubernetes CronJob Schedule Observe Report" in rendered
    assert "Scheduled Job: `qdrant-drill-123`" in rendered
    assert "[REDACTED]" in rendered
    assert "snapshot ok" in rendered
    assert "authorization: secret" not in rendered


def test_execute_qdrant_k8s_cronjob_multi_cycle_observe_waits_for_two_jobs():
    commands = []
    job_list_calls = 0
    sleeps = []

    def fake_runner(command: str, timeout_seconds: int):
        nonlocal job_list_calls
        commands.append(command)

        if command == "kubectl get jobs -n agent -o json":
            job_list_calls += 1

            if job_list_calls < 3:
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout=jobs_json(),
                    stderr="",
                )

            if job_list_calls == 3:
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout=jobs_json("qdrant-drill-123"),
                    stderr="",
                )

            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=jobs_json("qdrant-drill-123", "qdrant-drill-124"),
                stderr="",
            )

        return completed(command)

    report = execute_qdrant_k8s_cronjob_multi_cycle_observe(
        manifest_yaml="kind: CronJob",
        task_name="qdrant-drill",
        namespace="agent",
        expected_cycles=2,
        timeout_seconds=30,
        poll_interval_seconds=0.1,
        cleanup_jobs=True,
        cleanup_cronjob=True,
        command_runner=fake_runner,
        sleeper=lambda seconds: sleeps.append(seconds),
    )

    command_text = "\n".join(commands)

    assert report.overall_status == "passed"
    assert report.scheduled_job_names == ["qdrant-drill-123", "qdrant-drill-124"]
    assert "kubectl create job" not in command_text
    assert (
        "kubectl wait --for=condition=complete "
        "job/qdrant-drill-123 -n agent --timeout=30s"
    ) in commands
    assert (
        "kubectl wait --for=condition=complete "
        "job/qdrant-drill-124 -n agent --timeout=30s"
    ) in commands
    assert "kubectl logs job/qdrant-drill-123 -n agent --tail=200" in commands
    assert "kubectl logs job/qdrant-drill-124 -n agent --tail=200" in commands
    assert "kubectl delete job qdrant-drill-123 -n agent --ignore-not-found=true" in commands
    assert "kubectl delete job qdrant-drill-124 -n agent --ignore-not-found=true" in commands
    assert "kubectl delete cronjob qdrant-drill -n agent --ignore-not-found=true" in commands
    assert sleeps == [0.1, 0.1]
    assert any(
        result.name == "wait_scheduled_job_count"
        and "found 2 scheduled job(s)" in result.notes
        for result in report.results
    )


def test_execute_qdrant_k8s_cronjob_multi_cycle_observe_keeps_partial_evidence():
    commands = []
    job_list_calls = 0

    def fake_runner(command: str, timeout_seconds: int):
        nonlocal job_list_calls
        commands.append(command)

        if command == "kubectl get jobs -n agent -o json":
            job_list_calls += 1
            if job_list_calls == 1:
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout=jobs_json(),
                    stderr="",
                )

            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=jobs_json("qdrant-drill-123"),
                stderr="",
            )

        return completed(command)

    report = execute_qdrant_k8s_cronjob_multi_cycle_observe(
        manifest_yaml="kind: CronJob",
        task_name="qdrant-drill",
        namespace="agent",
        expected_cycles=2,
        timeout_seconds=0.01,
        poll_interval_seconds=0.01,
        cleanup_jobs=True,
        cleanup_cronjob=True,
        command_runner=fake_runner,
        sleeper=lambda seconds: None,
    )

    assert report.overall_status == "failed"
    assert report.scheduled_job_names == ["qdrant-drill-123"]
    assert any(
        result.name == "wait_scheduled_job_count"
        and "found 1 / 2 scheduled job(s)" in result.notes
        for result in report.results
    )
    assert "kubectl logs job/qdrant-drill-123 -n agent --tail=200" in commands
    assert "kubectl delete job qdrant-drill-123 -n agent --ignore-not-found=true" in commands
    assert "kubectl delete cronjob qdrant-drill -n agent --ignore-not-found=true" in commands


def test_execute_qdrant_k8s_cronjob_multi_cycle_observe_validates_inputs():
    with pytest.raises(ValueError, match="manifest_yaml"):
        execute_qdrant_k8s_cronjob_multi_cycle_observe(
            manifest_yaml=" ",
            task_name="qdrant-drill",
            namespace="agent",
        )

    with pytest.raises(ValueError, match="expected_cycles"):
        execute_qdrant_k8s_cronjob_multi_cycle_observe(
            manifest_yaml="kind: CronJob",
            task_name="qdrant-drill",
            namespace="agent",
            expected_cycles=0,
        )

    with pytest.raises(ValueError, match="poll_interval_seconds"):
        execute_qdrant_k8s_cronjob_multi_cycle_observe(
            manifest_yaml="kind: CronJob",
            task_name="qdrant-drill",
            namespace="agent",
            poll_interval_seconds=0,
        )


def test_render_qdrant_k8s_cronjob_multi_cycle_observe_report_sanitizes_output():
    report = QdrantK8sCronJobMultiCycleObserveReport(
        namespace="agent",
        task_name="qdrant-drill",
        scheduled_job_names=["qdrant-drill-123", "qdrant-drill-124"],
        expected_cycles=2,
        cleanup_jobs=False,
        cleanup_cronjob=False,
        started_at="2026-07-01T00:00:00",
        finished_at="2026-07-01T00:00:01",
        overall_status="passed",
        results=[
            QdrantK8sCronJobSmokeStepResult(
                name="collect_scheduled_job_logs",
                command="kubectl logs job/qdrant-drill-123",
                status="passed",
                returncode=0,
                stdout="password: secret\nsnapshot ok",
                stderr="",
                notes="",
            )
        ],
    )

    rendered = render_qdrant_k8s_cronjob_multi_cycle_observe_report(report)

    assert "# Qdrant Kubernetes CronJob Multi-Cycle Observe Report" in rendered
    assert "Expected cycles: `2`" in rendered
    assert "Observed scheduled Jobs: `2`" in rendered
    assert "qdrant-drill-123, qdrant-drill-124" in rendered
    assert "[REDACTED]" in rendered
    assert "snapshot ok" in rendered
    assert "password: secret" not in rendered


def test_qdrant_k8s_cronjob_smoke_cli_prints_report(monkeypatch, capsys):
    seen = {}

    def fake_execute(**kwargs):
        seen.update(kwargs)
        return fake_smoke_report()

    monkeypatch.setattr(
        cli,
        "execute_qdrant_k8s_cronjob_smoke",
        fake_execute,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-k8s-cronjob-smoke-run",
            "--task-name",
            "qdrant-drill",
            "--job-name",
            "qdrant-drill-manual",
            "--namespace",
            "agent",
            "--cleanup-job",
            "--cleanup-cronjob",
            "--timeout-seconds",
            "45",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Kubernetes CronJob Smoke Run Report" in output
    assert seen["task_name"] == "qdrant-drill"
    assert seen["namespace"] == "agent"
    assert seen["job_name"] == "qdrant-drill-manual"
    assert seen["timeout_seconds"] == 45
    assert seen["cleanup_job"] is True
    assert seen["cleanup_cronjob"] is True
    assert "--skip-restore-drill" in seen["manifest_yaml"]
    assert "--skip-compare" in seen["manifest_yaml"]


def test_qdrant_k8s_cronjob_smoke_cli_writes_outputs(
    monkeypatch,
    capsys,
    tmp_path,
):
    manifest_path = tmp_path / "cronjob.yaml"
    report_path = tmp_path / "report.md"

    monkeypatch.setattr(
        cli,
        "execute_qdrant_k8s_cronjob_smoke",
        lambda **kwargs: fake_smoke_report(),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-k8s-cronjob-smoke-run",
            "--manifest-output",
            str(manifest_path),
            "--output",
            str(report_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "MANIFEST OUTPUT:" in output
    assert "OUTPUT:" in output
    assert "kind: CronJob" in manifest_path.read_text(encoding="utf-8")
    assert "# Qdrant Kubernetes CronJob Smoke Run Report" in report_path.read_text(
        encoding="utf-8"
    )


def test_qdrant_k8s_cronjob_smoke_cli_exits_on_failed_report(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        cli,
        "execute_qdrant_k8s_cronjob_smoke",
        lambda **kwargs: fake_smoke_report("failed"),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-k8s-cronjob-smoke-run",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "Overall status: `failed`" in output


def test_qdrant_k8s_cronjob_schedule_observe_cli_prints_report(
    monkeypatch,
    capsys,
):
    seen = {}

    def fake_execute(**kwargs):
        seen.update(kwargs)
        return fake_observe_report()

    monkeypatch.setattr(
        cli,
        "execute_qdrant_k8s_cronjob_schedule_observe",
        fake_execute,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-k8s-cronjob-schedule-observe",
            "--task-name",
            "qdrant-drill",
            "--namespace",
            "agent",
            "--cleanup-job",
            "--cleanup-cronjob",
            "--timeout-seconds",
            "45",
            "--poll-interval-seconds",
            "0.5",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Kubernetes CronJob Schedule Observe Report" in output
    assert seen["task_name"] == "qdrant-drill"
    assert seen["namespace"] == "agent"
    assert seen["timeout_seconds"] == 45
    assert seen["poll_interval_seconds"] == 0.5
    assert seen["cleanup_job"] is True
    assert seen["cleanup_cronjob"] is True
    assert "--skip-restore-drill" in seen["manifest_yaml"]
    assert "--skip-compare" in seen["manifest_yaml"]


def test_qdrant_k8s_cronjob_schedule_observe_cli_writes_outputs(
    monkeypatch,
    capsys,
    tmp_path,
):
    manifest_path = tmp_path / "cronjob.yaml"
    report_path = tmp_path / "report.md"

    monkeypatch.setattr(
        cli,
        "execute_qdrant_k8s_cronjob_schedule_observe",
        lambda **kwargs: fake_observe_report(),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-k8s-cronjob-schedule-observe",
            "--manifest-output",
            str(manifest_path),
            "--output",
            str(report_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "MANIFEST OUTPUT:" in output
    assert "OUTPUT:" in output
    assert "kind: CronJob" in manifest_path.read_text(encoding="utf-8")
    assert "# Qdrant Kubernetes CronJob Schedule Observe Report" in report_path.read_text(
        encoding="utf-8"
    )


def test_qdrant_k8s_cronjob_schedule_observe_cli_exits_on_failed_report(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        cli,
        "execute_qdrant_k8s_cronjob_schedule_observe",
        lambda **kwargs: fake_observe_report("failed"),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-k8s-cronjob-schedule-observe",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "Overall status: `failed`" in output


def test_qdrant_k8s_cronjob_multi_cycle_observe_cli_prints_report(
    monkeypatch,
    capsys,
):
    seen = {}

    def fake_execute(**kwargs):
        seen.update(kwargs)
        return fake_multi_cycle_observe_report()

    monkeypatch.setattr(
        cli,
        "execute_qdrant_k8s_cronjob_multi_cycle_observe",
        fake_execute,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-k8s-cronjob-multi-cycle-observe",
            "--task-name",
            "qdrant-drill",
            "--namespace",
            "agent",
            "--expected-cycles",
            "3",
            "--cleanup-jobs",
            "--cleanup-cronjob",
            "--timeout-seconds",
            "45",
            "--poll-interval-seconds",
            "0.5",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Kubernetes CronJob Multi-Cycle Observe Report" in output
    assert seen["task_name"] == "qdrant-drill"
    assert seen["namespace"] == "agent"
    assert seen["expected_cycles"] == 3
    assert seen["timeout_seconds"] == 45
    assert seen["poll_interval_seconds"] == 0.5
    assert seen["cleanup_jobs"] is True
    assert seen["cleanup_cronjob"] is True
    assert "--skip-restore-drill" in seen["manifest_yaml"]
    assert "--skip-compare" in seen["manifest_yaml"]


def test_qdrant_k8s_cronjob_multi_cycle_observe_cli_writes_outputs(
    monkeypatch,
    capsys,
    tmp_path,
):
    manifest_path = tmp_path / "cronjob.yaml"
    report_path = tmp_path / "report.md"

    monkeypatch.setattr(
        cli,
        "execute_qdrant_k8s_cronjob_multi_cycle_observe",
        lambda **kwargs: fake_multi_cycle_observe_report(),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-k8s-cronjob-multi-cycle-observe",
            "--manifest-output",
            str(manifest_path),
            "--output",
            str(report_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "MANIFEST OUTPUT:" in output
    assert "OUTPUT:" in output
    assert "kind: CronJob" in manifest_path.read_text(encoding="utf-8")
    assert "# Qdrant Kubernetes CronJob Multi-Cycle Observe Report" in report_path.read_text(
        encoding="utf-8"
    )


def test_qdrant_k8s_cronjob_multi_cycle_observe_cli_exits_on_failed_report(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        cli,
        "execute_qdrant_k8s_cronjob_multi_cycle_observe",
        lambda **kwargs: fake_multi_cycle_observe_report("failed"),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-k8s-cronjob-multi-cycle-observe",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "Overall status: `failed`" in output


def test_qdrant_k8s_cronjob_smoke_cli_allows_failed_report(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        cli,
        "execute_qdrant_k8s_cronjob_smoke",
        lambda **kwargs: fake_smoke_report("failed"),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-k8s-cronjob-smoke-run",
            "--allow-fail",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "Overall status: `failed`" in output
