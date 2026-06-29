from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docker_compose_defines_postgres_service():
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "  postgres:" in compose_text
    assert "image: postgres:17-alpine" in compose_text
    assert "container_name: thesis-defense-agent-postgres" in compose_text
    assert '"${POSTGRES_PORT:-5432}:5432"' in compose_text
    assert 'POSTGRES_DB: "${POSTGRES_DB:-thesis_defense_agent}"' in compose_text
    assert 'POSTGRES_USER: "${POSTGRES_USER:-thesis_agent}"' in compose_text
    assert (
        'POSTGRES_PASSWORD: "${POSTGRES_PASSWORD:-thesis_agent_dev_password}"'
        in compose_text
    )


def test_docker_compose_postgres_has_healthcheck_and_volume():
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "pg_isready" in compose_text
    assert "postgres_data:/var/lib/postgresql/data" in compose_text
    assert "\nvolumes:\n  postgres_data:" in compose_text


def test_env_example_documents_postgres_defaults():
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "STORAGE_BACKEND=json" in env_text
    assert (
        "DATABASE_URL=postgresql://thesis_agent:"
        "thesis_agent_dev_password@localhost:5432/thesis_defense_agent"
        in env_text
    )
    assert "POSTGRES_DB=thesis_defense_agent" in env_text
    assert "POSTGRES_USER=thesis_agent" in env_text
    assert "POSTGRES_PASSWORD=thesis_agent_dev_password" in env_text
    assert "POSTGRES_PORT=5432" in env_text


def test_app_config_uses_empty_database_url_default():
    config_text = (ROOT / "app" / "config.py").read_text(encoding="utf-8")

    assert 'STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "json")' in config_text
    assert 'DATABASE_URL = os.getenv("DATABASE_URL", "")' in config_text
    assert "thesis_agent_dev_password" not in config_text
