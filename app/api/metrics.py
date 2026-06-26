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


def reset_api_metrics() -> None:
    global _request_count
    global _total_duration_ms

    with _lock:
        _request_count = 0
        _total_duration_ms = 0.0
        _status_counts.clear()
