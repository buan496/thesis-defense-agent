import pytest

from app import cli
from app.server_long_run_preflight import (
    ServerLongRunPreflightCheck,
    ServerLongRunPreflightReport,
    build_server_long_run_preflight,
    render_server_long_run_preflight_report,
)


def test_build_server_long_run_preflight_for_docker_compose():
    report = build_server_long_run_preflight(
        environment="server-prod",
        runtime="docker_compose",
        operator="ops",
    )

    check_names = [check.name for check in report.checks]

    assert report.environment == "server-prod"
    assert report.runtime == "docker_compose"
    assert report.operator == "ops"
    assert "source_control_baseline" in check_names
    assert "secret_boundary" in check_names
    assert "docker_compose_runtime" in check_names
    assert "compose_service_health" in check_names
    assert "observability_baseline" in check_names
    assert "rollback_and_data_recovery" in check_names
    assert "kubernetes_context" not in check_names


def test_build_server_long_run_preflight_for_kubernetes():
    report = build_server_long_run_preflight(
        environment="kind-local",
        runtime="kubernetes",
        operator="ops",
    )

    check_names = [check.name for check in report.checks]

    assert report.runtime == "kubernetes"
    assert "kubernetes_context" in check_names
    assert "kubernetes_rollout_health" in check_names
    assert "kubernetes_cronjob_scheduler" in check_names
    assert "docker_compose_runtime" not in check_names


def test_build_server_long_run_preflight_validates_inputs():
    with pytest.raises(ValueError, match="environment"):
        build_server_long_run_preflight(environment=" ")

    with pytest.raises(ValueError, match="operator"):
        build_server_long_run_preflight(operator="")

    with pytest.raises(ValueError, match="runtime"):
        build_server_long_run_preflight(runtime="nomad")


def test_render_server_long_run_preflight_report_contains_evidence_index():
    report = ServerLongRunPreflightReport(
        environment="server-prod",
        runtime="docker_compose",
        operator="ops",
        generated_at="2026-07-02T00:00:00",
        checks=[
            ServerLongRunPreflightCheck(
                name="health",
                category="runtime",
                status="manual_required",
                purpose="verify service health",
                commands=["curl.exe -f http://127.0.0.1:8000/health"],
                acceptance_criteria=["health returns ok"],
                evidence=["sanitized health response"],
                notes="do not paste secrets",
            )
        ],
    )

    rendered = render_server_long_run_preflight_report(report)

    assert "# Server Long-Run Preflight Report" in rendered
    assert "- Environment: `server-prod`" in rendered
    assert "| 1 | `runtime` | `health` | `manual_required` |" in rendered
    assert "curl.exe -f http://127.0.0.1:8000/health" in rendered
    assert "- health returns ok" in rendered
    assert "- sanitized health response" in rendered
    assert "Do not paste real API keys" in rendered


def test_server_long_run_preflight_cli_prints_report(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "server-long-run-preflight",
            "--environment",
            "kind-local",
            "--runtime",
            "kubernetes",
            "--operator",
            "tester",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Server Long-Run Preflight Report" in output
    assert "- Environment: `kind-local`" in output
    assert "- Runtime: `kubernetes`" in output
    assert "- Operator: `tester`" in output
    assert "kubernetes_cronjob_scheduler" in output


def test_server_long_run_preflight_cli_writes_output(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "preflight.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "server-long-run-preflight",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    markdown = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert "# Server Long-Run Preflight Report" in markdown
