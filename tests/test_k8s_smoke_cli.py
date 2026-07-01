from app import cli
from app.k8s_smoke_runner import K8sSmokeRunReport, K8sSmokeStepResult


def fake_run_report(overall_status: str = "passed") -> K8sSmokeRunReport:
    return K8sSmokeRunReport(
        namespace="test-ns",
        kustomize_dir="k8s/base",
        api_local_port=19000,
        apply_cluster=True,
        include_port_forward=False,
        include_rollback=False,
        started_at="2026-07-01T00:00:00",
        finished_at="2026-07-01T00:00:01",
        overall_status=overall_status,
        results=[
            K8sSmokeStepResult(
                name="render_manifests",
                command="kubectl kustomize k8s/base",
                status=overall_status,
                returncode=0 if overall_status == "passed" else 1,
                stdout="ok",
                stderr="" if overall_status == "passed" else "boom",
                notes="",
            )
        ],
    )


def test_k8s_smoke_plan_command_prints_plan(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "k8s-smoke-plan",
            "--namespace",
            "test-ns",
            "--kustomize-dir",
            "k8s/base",
            "--api-local-port",
            "19000",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# K8s Smoke Test Plan" in output
    assert "Namespace: `test-ns`" in output
    assert "kubectl kustomize k8s/base" in output
    assert "kubectl rollout status deployment/thesis-defense-agent-api -n test-ns" in output
    assert "curl.exe -f http://127.0.0.1:19000/health" in output


def test_k8s_smoke_plan_command_writes_markdown(monkeypatch, capsys, tmp_path):
    output_path = tmp_path / "k8s-smoke-plan.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "k8s-smoke-plan",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert str(output_path) in output
    assert "# K8s Smoke Test Plan" in saved
    assert "kubectl apply -k k8s/base" in saved


def test_k8s_smoke_plan_command_rejects_invalid_port(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "k8s-smoke-plan",
            "--api-local-port",
            "0",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("Expected k8s-smoke-plan to fail")

    output = capsys.readouterr().out

    assert "K8S SMOKE PLAN ERROR:" in output
    assert "api_local_port" in output


def test_k8s_smoke_report_template_command_prints_template(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "k8s-smoke-report-template",
            "--namespace",
            "test-ns",
            "--environment",
            "kind-local",
            "--operator",
            "tester",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# K8s Smoke Test Execution Report" in output
    assert "- Environment: `kind-local`" in output
    assert "- Operator: `tester`" in output
    assert "kubectl apply -k k8s/base" in output
    assert "kubectl rollout status deployment/thesis-defense-agent-api -n test-ns" in output
    assert "- Result: `[ ] PASS  [ ] FAIL  [ ] SKIPPED`" in output


def test_k8s_smoke_report_template_command_writes_markdown(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "k8s-smoke-report.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "k8s-smoke-report-template",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert str(output_path) in output
    assert "# K8s Smoke Test Execution Report" in saved
    assert "Evidence:" in saved


def test_k8s_smoke_report_template_command_rejects_invalid_environment(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "k8s-smoke-report-template",
            "--environment",
            " ",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("Expected k8s-smoke-report-template to fail")

    output = capsys.readouterr().out

    assert "K8S SMOKE REPORT TEMPLATE ERROR:" in output
    assert "environment" in output


def test_k8s_smoke_run_command_prints_report(monkeypatch, capsys):
    calls = []

    def fake_execute(plan, **kwargs):
        calls.append((plan, kwargs))
        return fake_run_report()

    monkeypatch.setattr(
        cli,
        "execute_k8s_smoke_plan",
        fake_execute,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "k8s-smoke-run",
            "--namespace",
            "test-ns",
            "--api-local-port",
            "19000",
            "--apply-cluster",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# K8s Smoke Test Run Report" in output
    assert "Overall status: `passed`" in output
    assert calls[0][0].namespace == "test-ns"
    assert calls[0][1]["apply_cluster"] is True
    assert calls[0][1]["include_port_forward"] is False


def test_k8s_smoke_run_command_writes_report(monkeypatch, capsys, tmp_path):
    output_path = tmp_path / "k8s-smoke-run.md"

    monkeypatch.setattr(
        cli,
        "execute_k8s_smoke_plan",
        lambda plan, **kwargs: fake_run_report(),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "k8s-smoke-run",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert "# K8s Smoke Test Run Report" in saved


def test_k8s_smoke_run_command_exits_on_failure(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "execute_k8s_smoke_plan",
        lambda plan, **kwargs: fake_run_report("failed"),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "k8s-smoke-run",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("Expected k8s-smoke-run to fail")

    output = capsys.readouterr().out

    assert "Overall status: `failed`" in output


def test_k8s_smoke_run_command_allows_failure(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "execute_k8s_smoke_plan",
        lambda plan, **kwargs: fake_run_report("failed"),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "k8s-smoke-run",
            "--allow-fail",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "Overall status: `failed`" in output
