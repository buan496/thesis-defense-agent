import json
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


CommandRunner = Callable[[list[str], int, str | None], "CommandProbe"]
HttpChecker = Callable[[str, int, str | None], "HttpProbe"]
SleepFunction = Callable[[float], None]


@dataclass(frozen=True)
class CommandProbe:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float

    @property
    def passed(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True)
class HttpProbe:
    name: str
    url: str
    status_code: int | None
    body_preview: str
    error: str | None
    duration_ms: float

    @property
    def passed(self) -> bool:
        return self.status_code is not None and 200 <= self.status_code < 300

    def to_dict(self) -> dict:
        data = asdict(self)
        data["passed"] = self.passed
        return data


@dataclass(frozen=True)
class LocalLongRunSmokeCycle:
    index: int
    started_at: str
    command_probes: list[CommandProbe]
    http_probes: list[HttpProbe]

    @property
    def passed(self) -> bool:
        compose_output_is_healthy = all(
            _compose_probe_has_healthy_output(probe)
            for probe in self.command_probes
            if probe.name == "docker_compose_ps"
        )
        return (
            all(probe.passed for probe in self.command_probes)
            and compose_output_is_healthy
            and all(probe.passed for probe in self.http_probes)
        )

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "started_at": self.started_at,
            "passed": self.passed,
            "command_probes": [
                probe.to_dict()
                for probe in self.command_probes
            ],
            "http_probes": [
                probe.to_dict()
                for probe in self.http_probes
            ],
        }


@dataclass(frozen=True)
class LocalLongRunSmokeReport:
    environment: str
    generated_at: str
    duration_seconds: int
    interval_seconds: int
    passed: bool
    cycles: list[LocalLongRunSmokeCycle]

    def to_dict(self) -> dict:
        return {
            "environment": self.environment,
            "generated_at": self.generated_at,
            "duration_seconds": self.duration_seconds,
            "interval_seconds": self.interval_seconds,
            "passed": self.passed,
            "cycle_count": len(self.cycles),
            "cycles": [
                cycle.to_dict()
                for cycle in self.cycles
            ],
        }


def run_local_long_run_smoke(
    environment: str = "local-docker-compose",
    duration_seconds: int = 0,
    interval_seconds: int = 30,
    api_url: str = "http://127.0.0.1:8000",
    prometheus_url: str = "http://127.0.0.1:9090",
    alertmanager_url: str = "http://127.0.0.1:9093",
    qdrant_url: str = "http://127.0.0.1:6333",
    include_compose_ps: bool = True,
    command_timeout_seconds: int = 30,
    http_timeout_seconds: int = 5,
    command_runner: CommandRunner | None = None,
    http_checker: HttpChecker | None = None,
    sleep_fn: SleepFunction = time.sleep,
) -> LocalLongRunSmokeReport:
    normalized_environment = _normalize_required_text(
        environment,
        "environment",
    )
    _validate_non_negative_int(duration_seconds, "duration_seconds")
    _validate_positive_int(interval_seconds, "interval_seconds")
    _validate_positive_int(command_timeout_seconds, "command_timeout_seconds")
    _validate_positive_int(http_timeout_seconds, "http_timeout_seconds")

    runner = command_runner or run_command_probe
    checker = http_checker or run_http_probe
    cycle_count = _calculate_cycle_count(duration_seconds, interval_seconds)
    cycles = []

    for index in range(1, cycle_count + 1):
        cycles.append(
            _run_smoke_cycle(
                index=index,
                api_url=api_url,
                prometheus_url=prometheus_url,
                alertmanager_url=alertmanager_url,
                qdrant_url=qdrant_url,
                include_compose_ps=include_compose_ps,
                command_timeout_seconds=command_timeout_seconds,
                http_timeout_seconds=http_timeout_seconds,
                command_runner=runner,
                http_checker=checker,
            )
        )

        if index < cycle_count:
            sleep_fn(interval_seconds)

    return LocalLongRunSmokeReport(
        environment=normalized_environment,
        generated_at=_now_iso(),
        duration_seconds=duration_seconds,
        interval_seconds=interval_seconds,
        passed=all(cycle.passed for cycle in cycles),
        cycles=cycles,
    )


def run_command_probe(
    command: list[str],
    timeout_seconds: int,
    name: str | None = None,
) -> CommandProbe:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as error:
        returncode = 124
        stdout = error.stdout or ""
        stderr = f"Command timed out after {timeout_seconds}s"

    duration_ms = round((time.perf_counter() - started) * 1000, 2)

    return CommandProbe(
        name=name or _command_name(command),
        command=command,
        returncode=returncode,
        stdout=_truncate_text(stdout),
        stderr=_truncate_text(stderr),
        duration_ms=duration_ms,
    )


def run_http_probe(
    url: str,
    timeout_seconds: int,
    name: str | None = None,
) -> HttpProbe:
    started = time.perf_counter()
    status_code = None
    body_preview = ""
    error_message = None

    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
            status_code = response.status
            body_preview = response.read(2048).decode(
                "utf-8",
                errors="replace",
            )
    except urllib.error.HTTPError as error:
        status_code = error.code
        error_message = str(error)
        body_preview = error.read(2048).decode("utf-8", errors="replace")
    except Exception as error:  # pragma: no cover - exercised by integration runs
        error_message = f"{type(error).__name__}: {error}"

    duration_ms = round((time.perf_counter() - started) * 1000, 2)

    return HttpProbe(
        name=name or _url_name(url),
        url=url,
        status_code=status_code,
        body_preview=_truncate_text(body_preview),
        error=error_message,
        duration_ms=duration_ms,
    )


def render_local_long_run_smoke_markdown(
    report: LocalLongRunSmokeReport,
) -> str:
    status = "PASS" if report.passed else "FAIL"
    lines = [
        "# Local Long-Run Smoke Report",
        "",
        f"- Environment: `{report.environment}`",
        f"- Generated at: `{report.generated_at}`",
        f"- Duration seconds: `{report.duration_seconds}`",
        f"- Interval seconds: `{report.interval_seconds}`",
        f"- Cycle count: `{len(report.cycles)}`",
        f"- Status: **{status}**",
        "",
        "## Cycle Summary",
        "",
        "| Cycle | Started At | Passed | Command Checks | HTTP Checks |",
        "| --- | --- | --- | --- | --- |",
    ]

    for cycle in report.cycles:
        lines.append(
            "| "
            f"{cycle.index} | `{cycle.started_at}` | `{cycle.passed}` | "
            f"`{len(cycle.command_probes)}` | `{len(cycle.http_probes)}` |"
        )

    for cycle in report.cycles:
        lines.extend(_render_cycle_details(cycle))

    return "\n".join(lines).strip() + "\n"


def save_local_long_run_smoke_report(
    report: LocalLongRunSmokeReport,
    file_path: str,
) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def save_local_long_run_smoke_markdown(
    report: LocalLongRunSmokeReport,
    file_path: str,
) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_local_long_run_smoke_markdown(report),
        encoding="utf-8",
    )
    return path


def _run_smoke_cycle(
    index: int,
    api_url: str,
    prometheus_url: str,
    alertmanager_url: str,
    qdrant_url: str,
    include_compose_ps: bool,
    command_timeout_seconds: int,
    http_timeout_seconds: int,
    command_runner: CommandRunner,
    http_checker: HttpChecker,
) -> LocalLongRunSmokeCycle:
    command_probes = []

    if include_compose_ps:
        command_probes.append(
            _run_named_command_probe(
                command_runner=command_runner,
                name="docker_compose_ps",
                command=["docker", "compose", "ps"],
                timeout_seconds=command_timeout_seconds,
            )
        )

    http_targets = [
        ("api_health", _join_url(api_url, "/health")),
        ("api_version", _join_url(api_url, "/version")),
        ("api_prometheus_metrics", _join_url(api_url, "/metrics/prometheus")),
        ("prometheus_ready", _join_url(prometheus_url, "/-/ready")),
        ("alertmanager_ready", _join_url(alertmanager_url, "/-/ready")),
        ("qdrant_ready", _join_url(qdrant_url, "/readyz")),
    ]

    http_probes = [
        _run_named_http_probe(
            http_checker=http_checker,
            name=name,
            url=url,
            timeout_seconds=http_timeout_seconds,
        )
        for name, url in http_targets
    ]

    return LocalLongRunSmokeCycle(
        index=index,
        started_at=_now_iso(),
        command_probes=command_probes,
        http_probes=http_probes,
    )


def _run_named_command_probe(
    command_runner: CommandRunner,
    name: str,
    command: list[str],
    timeout_seconds: int,
) -> CommandProbe:
    return command_runner(command, timeout_seconds, name)


def _run_named_http_probe(
    http_checker: HttpChecker,
    name: str,
    url: str,
    timeout_seconds: int,
) -> HttpProbe:
    return http_checker(url, timeout_seconds, name)


def _render_cycle_details(cycle: LocalLongRunSmokeCycle) -> list[str]:
    lines = [
        "",
        f"## Cycle {cycle.index}",
        "",
        f"- Started at: `{cycle.started_at}`",
        f"- Passed: `{cycle.passed}`",
        "",
        "### Command Probes",
        "",
        "| Name | Passed | Return Code | Duration ms |",
        "| --- | --- | --- | --- |",
    ]

    for probe in cycle.command_probes:
        lines.append(
            f"| `{probe.name}` | `{probe.passed}` | "
            f"`{probe.returncode}` | `{probe.duration_ms}` |"
        )

    lines.extend(
        [
            "",
            "### HTTP Probes",
            "",
            "| Name | Passed | Status | Duration ms | URL |",
            "| --- | --- | --- | --- | --- |",
        ]
    )

    for probe in cycle.http_probes:
        status = "N/A" if probe.status_code is None else str(probe.status_code)
        lines.append(
            f"| `{probe.name}` | `{probe.passed}` | `{status}` | "
            f"`{probe.duration_ms}` | `{probe.url}` |"
        )

    return lines


def _compose_probe_has_healthy_output(probe: CommandProbe) -> bool:
    if not probe.passed:
        return False

    lowered = f"{probe.stdout}\n{probe.stderr}".lower()
    unhealthy_markers = [
        "exited",
        "dead",
        "unhealthy",
        "restarting",
    ]
    return not any(marker in lowered for marker in unhealthy_markers)


def _calculate_cycle_count(
    duration_seconds: int,
    interval_seconds: int,
) -> int:
    if duration_seconds <= 0:
        return 1

    return max(1, (duration_seconds // interval_seconds) + 1)


def _join_url(
    base_url: str,
    path: str,
) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _normalize_required_text(
    value: str,
    field_name: str,
) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _validate_positive_int(
    value: int,
    field_name: str,
) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0")


def _validate_non_negative_int(
    value: int,
    field_name: str,
) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")


def _truncate_text(
    text: str,
    max_length: int = 2000,
) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n...[truncated]"


def _command_name(command: list[str]) -> str:
    return "_".join(command[:3]).replace(" ", "_")


def _url_name(url: str) -> str:
    return url.replace("https://", "").replace("http://", "").replace("/", "_")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()
