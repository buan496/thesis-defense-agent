from app import cli


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
