from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docker_compose_defines_qdrant_service():
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "  qdrant:" in compose_text
    assert "image: qdrant/qdrant:v1.18.2" in compose_text
    assert "container_name: thesis-defense-agent-qdrant" in compose_text
    assert '"${QDRANT_HTTP_PORT:-6333}:6333"' in compose_text
    assert '"${QDRANT_GRPC_PORT:-6334}:6334"' in compose_text
    assert 'QDRANT__SERVICE__HTTP_PORT: "6333"' in compose_text
    assert 'QDRANT__SERVICE__GRPC_PORT: "6334"' in compose_text


def test_docker_compose_qdrant_uses_named_volume():
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "qdrant_data:/qdrant/storage" in compose_text
    assert "\nvolumes:\n  postgres_data:\n  qdrant_data:" in compose_text


def test_env_example_documents_qdrant_defaults():
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "VECTOR_STORE_BACKEND=json" in env_text
    assert "QDRANT_URL=http://127.0.0.1:6333" in env_text
    assert "QDRANT_COLLECTION=thesis_chunks" in env_text
    assert "QDRANT_VECTOR_SIZE=1024" in env_text
    assert "QDRANT_DISTANCE=Cosine" in env_text
    assert "QDRANT_HTTP_PORT=6333" in env_text
    assert "QDRANT_GRPC_PORT=6334" in env_text
    assert "QDRANT_API_KEY=" in env_text
    assert "QDRANT_BACKUP_DIR=data/qdrant_backups" in env_text


def test_app_config_documents_qdrant_defaults_without_secret():
    config_text = (ROOT / "app" / "config.py").read_text(encoding="utf-8")

    assert 'QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")' in config_text
    assert 'QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "thesis_chunks")' in config_text
    assert 'QDRANT_VECTOR_SIZE = int(os.getenv("QDRANT_VECTOR_SIZE", "1024"))' in config_text
    assert 'QDRANT_DISTANCE = os.getenv("QDRANT_DISTANCE", "Cosine")' in config_text
    assert 'QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")' in config_text
    assert 'QDRANT_BACKUP_DIR = os.getenv("QDRANT_BACKUP_DIR", "data/qdrant_backups")' in config_text
    assert "qdrant_api_key_here" not in config_text


def test_qdrant_docs_include_snapshot_backup_restore_sop():
    docs_text = (
        ROOT / "docs" / "deployment" / "qdrant.md"
    ).read_text(encoding="utf-8")

    assert "## Backup and Restore SOP" in docs_text
    assert "https://qdrant.tech/documentation/snapshots/" in docs_text
    assert "/collections/thesis_chunks/snapshots" in docs_text
    assert "data/qdrant_backups" in docs_text
    assert "snapshots/upload?priority=snapshot" in docs_text
    assert "compare-vector-store-backends" in docs_text
    assert "Rebuild from JSON Baseline" in docs_text
    assert "qdrant-backup-retention" in docs_text


def test_gitignore_excludes_qdrant_backup_artifacts():
    gitignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "data/qdrant_backups/" in gitignore_text
