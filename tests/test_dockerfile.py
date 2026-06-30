from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_runs_api_as_non_root_user():
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "groupadd --gid 10001 app" in text
    assert "useradd --uid 10001" in text
    assert "mkdir -p /app/data /app/.cache/uv" in text
    assert "chown -R 10001:10001 /app" in text
    assert "ENV HOME=/app" in text
    assert "ENV UV_CACHE_DIR=/app/.cache/uv" in text
    assert "USER 10001:10001" in text


def test_dockerfile_still_starts_fastapi_with_uvicorn():
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert 'EXPOSE 8000' in text
    assert '"uvicorn", "app.api.main:app"' in text
    assert '"--host", "0.0.0.0"' in text
    assert '"--port", "8000"' in text
