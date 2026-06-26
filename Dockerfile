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

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
