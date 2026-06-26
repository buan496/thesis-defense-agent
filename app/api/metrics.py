from threading import Lock


_lock = Lock()
_request_count = 0
_total_duration_ms = 0.0
_status_counts: dict[str, int] = {}


def record_api_request(
    status_code: int,
    duration_ms: float,
) -> None:
    global _request_count
    global _total_duration_ms

    status_key = str(status_code)

    with _lock:
        _request_count += 1
        _total_duration_ms += duration_ms
        _status_counts[status_key] = _status_counts.get(status_key, 0) + 1


def get_api_metrics() -> dict[str, object]:
    with _lock:
        average_duration_ms = (
            _total_duration_ms / _request_count
            if _request_count
            else 0.0
        )

        return {
            "request_count": _request_count,
            "status_counts": dict(_status_counts),
            "total_duration_ms": round(_total_duration_ms, 2),
            "average_duration_ms": round(average_duration_ms, 2),
        }


def format_prometheus_metrics() -> str:
    metrics = get_api_metrics()
    status_counts = metrics["status_counts"]

    lines = [
        "# HELP thesis_defense_api_requests_total Total API requests.",
        "# TYPE thesis_defense_api_requests_total counter",
        f"thesis_defense_api_requests_total {metrics['request_count']}",
        "# HELP thesis_defense_api_request_status_total API requests by HTTP status code.",
        "# TYPE thesis_defense_api_request_status_total counter",
    ]

    for status_code, count in sorted(status_counts.items()):
        lines.append(
            f'thesis_defense_api_request_status_total{{status_code="{status_code}"}} {count}'
        )

    lines.extend(
        [
            "# HELP thesis_defense_api_request_duration_ms_total Total API request duration in milliseconds.",
            "# TYPE thesis_defense_api_request_duration_ms_total counter",
            f"thesis_defense_api_request_duration_ms_total {metrics['total_duration_ms']}",
            "# HELP thesis_defense_api_request_duration_ms_average Average API request duration in milliseconds.",
            "# TYPE thesis_defense_api_request_duration_ms_average gauge",
            f"thesis_defense_api_request_duration_ms_average {metrics['average_duration_ms']}",
        ]
    )

    return "\n".join(lines) + "\n"


def reset_api_metrics() -> None:
    global _request_count
    global _total_duration_ms

    with _lock:
        _request_count = 0
        _total_duration_ms = 0.0
        _status_counts.clear()
