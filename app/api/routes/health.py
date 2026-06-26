from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter, Response

from app.api.metrics import format_prometheus_metrics, get_api_metrics


router = APIRouter(tags=["health"])


def get_project_version() -> str:
    try:
        return version("thesis-defense-agent")
    except PackageNotFoundError:
        return "0.1.0"


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "thesis-defense-agent",
    }


@router.get("/version")
def version_info() -> dict[str, str]:
    return {
        "service": "thesis-defense-agent",
        "version": get_project_version(),
    }


@router.get("/metrics")
def metrics() -> dict[str, object]:
    return get_api_metrics()


@router.get("/metrics/prometheus")
def prometheus_metrics() -> Response:
    return Response(
        content=format_prometheus_metrics(),
        media_type="text/plain; version=0.0.4",
    )
