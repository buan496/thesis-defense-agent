import json
import sys

import pytest

from app import cli
from app.local_long_run_smoke import (
    CommandProbe,
    HttpProbe,
    LocalLongRunSmokeReport,
    render_local_long_run_smoke_markdown,
    run_command_probe,
    run_local_long_run_smoke,
    save_local_long_run_smoke_markdown,
    save_local_long_run_smoke_report,
)


def passing_command_runner(
    command: list[str],
    timeout_seconds: int,
    name: str = "command",
) -> CommandProbe:
    return CommandProbe(
        name=name,
        command=command,
        returncode=0,
        stdout="NAME STATUS\napi running\nqdrant running\n",
        stderr="",
        duration_ms=3.0,
    )


def unhealthy_command_runner(
    command: list[str],
    timeout_seconds: int,
    name: str = "command",
) -> CommandProbe:
    return CommandProbe(
        name=name,
        command=command,
        returncode=0,
        stdout="NAME STATUS\napi unhealthy\n",
        stderr="",
        duration_ms=3.0,
    )


def passing_http_checker(
    url: str,
    timeout_seconds: int,
    name: str = "http",
) -> HttpProbe:
    return HttpProbe(
        name=name,
        url=url,
        status_code=200,
        body_preview="ok",
        error=None,
        duration_ms=2.0,
    )


def failing_http_checker(
    url: str,
    timeout_seconds: int,
    name: str = "http",
) -> HttpProbe:
    return HttpProbe(
        name=name,
        url=url,
        status_code=None,
        body_preview="",
        error="Connection refused",
        duration_ms=2.0,
    )


def test_run_local_long_run_smoke_passes_with_fake_probes():
    report = run_local_long_run_smoke(
        command_runner=passing_command_runner,
        http_checker=passing_http_checker,
    )

    assert report.passed is True
    assert report.environment == "local-docker-compose"
    assert len(report.cycles) == 1
    assert report.cycles[0].passed is True
    assert report.cycles[0].command_probes[0].name == "docker_compose_ps"
    assert len(report.cycles[0].http_probes) == 6


def test_run_local_long_run_smoke_fails_on_unhealthy_compose_output():
    report = run_local_long_run_smoke(
        command_runner=unhealthy_command_runner,
        http_checker=passing_http_checker,
    )

    assert report.passed is False
    assert report.cycles[0].passed is False


def test_run_local_long_run_smoke_fails_on_http_error():
    report = run_local_long_run_smoke(
        command_runner=passing_command_runner,
        http_checker=failing_http_checker,
    )

    assert report.passed is False
    assert report.cycles[0].http_probes[0].error == "Connection refused"


def test_run_local_long_run_smoke_validates_inputs():
    with pytest.raises(ValueError, match="environment"):
        run_local_long_run_smoke(environment=" ")

    with pytest.raises(ValueError, match="duration_seconds"):
        run_local_long_run_smoke(duration_seconds=-1)

    with pytest.raises(ValueError, match="interval_seconds"):
        run_local_long_run_smoke(interval_seconds=0)


def test_run_command_probe_handles_unicode_output():
    probe = run_command_probe(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.stdout.buffer.write('✓ Docker 状态正常'.encode('utf-8'))"
            ),
        ],
        timeout_seconds=10,
        name="unicode_probe",
    )

    assert probe.passed is True
    assert "Docker" in probe.stdout


def test_run_local_long_run_smoke_runs_multiple_cycles_without_real_sleep():
    sleep_calls = []

    report = run_local_long_run_smoke(
        duration_seconds=2,
        interval_seconds=1,
        command_runner=passing_command_runner,
        http_checker=passing_http_checker,
        sleep_fn=lambda seconds: sleep_calls.append(seconds),
    )

    assert report.passed is True
    assert len(report.cycles) == 3
    assert sleep_calls == [1, 1]


def test_render_local_long_run_smoke_markdown():
    report = run_local_long_run_smoke(
        command_runner=passing_command_runner,
        http_checker=passing_http_checker,
    )

    markdown = render_local_long_run_smoke_markdown(report)

    assert "# Local Long-Run Smoke Report" in markdown
    assert "Status: **PASS**" in markdown
    assert "`api_health`" in markdown
    assert "`docker_compose_ps`" in markdown


def test_save_local_long_run_smoke_report(tmp_path):
    report = run_local_long_run_smoke(
        command_runner=passing_command_runner,
        http_checker=passing_http_checker,
    )
    output_path = tmp_path / "reports" / "local_long_run.json"

    saved_path = save_local_long_run_smoke_report(report, str(output_path))
    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert saved_path == output_path
    assert data["passed"] is True
    assert data["cycle_count"] == 1


def test_save_local_long_run_smoke_markdown(tmp_path):
    report = run_local_long_run_smoke(
        command_runner=passing_command_runner,
        http_checker=passing_http_checker,
    )
    output_path = tmp_path / "reports" / "local_long_run.md"

    saved_path = save_local_long_run_smoke_markdown(
        report,
        str(output_path),
    )
    markdown = output_path.read_text(encoding="utf-8")

    assert saved_path == output_path
    assert "# Local Long-Run Smoke Report" in markdown


def test_local_long_run_smoke_cli(monkeypatch, capsys):
    def fake_run_local_long_run_smoke(**kwargs):
        return run_local_long_run_smoke(
            command_runner=passing_command_runner,
            http_checker=passing_http_checker,
        )

    monkeypatch.setattr(
        "app.cli.run_local_long_run_smoke",
        fake_run_local_long_run_smoke,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "local-long-run-smoke",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Local Long-Run Smoke Report" in output
    assert "Status: **PASS**" in output


def test_local_long_run_smoke_cli_writes_outputs(
    monkeypatch,
    capsys,
    tmp_path,
):
    json_path = tmp_path / "local_long_run.json"
    markdown_path = tmp_path / "local_long_run.md"

    def fake_run_local_long_run_smoke(**kwargs):
        return run_local_long_run_smoke(
            command_runner=passing_command_runner,
            http_checker=passing_http_checker,
        )

    monkeypatch.setattr(
        "app.cli.run_local_long_run_smoke",
        fake_run_local_long_run_smoke,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "local-long-run-smoke",
            "--output",
            str(json_path),
            "--markdown-output",
            str(markdown_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "OUTPUT:" in output
    assert "MARKDOWN OUTPUT:" in output
    assert json_path.exists()
    assert markdown_path.exists()


def test_local_long_run_smoke_cli_fails_without_allow_fail(
    monkeypatch,
    capsys,
):
    def fake_run_local_long_run_smoke(**kwargs):
        return run_local_long_run_smoke(
            command_runner=passing_command_runner,
            http_checker=failing_http_checker,
        )

    monkeypatch.setattr(
        "app.cli.run_local_long_run_smoke",
        fake_run_local_long_run_smoke,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "local-long-run-smoke",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "Status: **FAIL**" in output


def test_local_long_run_smoke_cli_allows_failure(
    monkeypatch,
    capsys,
):
    def fake_run_local_long_run_smoke(**kwargs):
        return run_local_long_run_smoke(
            command_runner=passing_command_runner,
            http_checker=failing_http_checker,
        )

    monkeypatch.setattr(
        "app.cli.run_local_long_run_smoke",
        fake_run_local_long_run_smoke,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "local-long-run-smoke",
            "--allow-fail",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "Status: **FAIL**" in output
