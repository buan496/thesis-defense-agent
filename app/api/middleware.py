import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.api.metrics import record_api_request


logger = logging.getLogger("app.api.request")
CORRELATION_ID_HEADER = "X-Correlation-ID"


def get_or_create_correlation_id(request: Request) -> str:
    incoming_correlation_id = request.headers.get(CORRELATION_ID_HEADER)

    if incoming_correlation_id and incoming_correlation_id.strip():
        return incoming_correlation_id.strip()

    return str(uuid.uuid4())


async def log_request_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    start_time = time.perf_counter()
    status_code = 500
    correlation_id = get_or_create_correlation_id(request)
    request.state.correlation_id = correlation_id

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
    finally:
        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )
        record_api_request(
            status_code=status_code,
            duration_ms=duration_ms,
        )
        logger.info(
            json.dumps(
                {
                    "event": "api_request",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "correlation_id": correlation_id,
                },
                ensure_ascii=False,
            )
        )
