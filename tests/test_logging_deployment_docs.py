from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docker_compose_configures_log_rotation_for_runtime_services():
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert compose_text.count("driver: json-file") == 4
    assert compose_text.count('max-size: "${DOCKER_LOG_MAX_SIZE:-10m}"') == 4
    assert compose_text.count('max-file: "${DOCKER_LOG_MAX_FILE:-5}"') == 4


def test_env_example_documents_docker_log_retention_defaults():
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "DOCKER_LOG_MAX_SIZE=10m" in env_text
    assert "DOCKER_LOG_MAX_FILE=5" in env_text


def test_logging_deployment_documentation_covers_queries_and_boundaries():
    docs_text = (
        ROOT / "docs" / "deployment" / "logging.md"
    ).read_text(encoding="utf-8")

    assert "# Logging and Retention" in docs_text
    assert "app/api/middleware.py" in docs_text
    assert "logger name: app.api.request" in docs_text
    assert "X-Correlation-ID" in docs_text
    assert '"correlation_id":' in docs_text
    assert "docker compose logs -f api" in docs_text
    assert "docker compose logs --tail 100 api" in docs_text
    assert "docker compose logs --since 30m api" in docs_text
    assert "uv run python -m app.cli analyze-traces" in docs_text
    assert "uv run python -m app.cli replay-agent-trace" in docs_text
    assert "centralized log storage" in docs_text
    assert "correlation IDs" in docs_text
