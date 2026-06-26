from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter

from app.api.metrics import get_api_metrics


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
