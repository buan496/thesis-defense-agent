from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter(tags=["frontend"])
STATIC_DIRECTORY = Path(__file__).resolve().parents[1] / "static"
INDEX_HTML = STATIC_DIRECTORY / "index.html"


@router.get("/", include_in_schema=False)
def web_frontend() -> FileResponse:
    return FileResponse(INDEX_HTML)
