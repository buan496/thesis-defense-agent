FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY README.md ./README.md

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --home-dir /app --shell /usr/sbin/nologin app \
    && mkdir -p /app/data /app/.cache/uv \
    && chown -R 10001:10001 /app

ENV HOME=/app
ENV UV_CACHE_DIR=/app/.cache/uv

EXPOSE 8000

USER 10001:10001

CMD ["uv", "run", "--no-dev", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
