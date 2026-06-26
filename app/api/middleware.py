import json
import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.api.metrics import record_api_request


logger = logging.getLogger("app.api.request")


async def log_request_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
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
                },
                ensure_ascii=False,
            )
        )
