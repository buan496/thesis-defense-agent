from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docker_compose_defines_milvus_service():
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "  milvus:" in compose_text
    assert "image: milvusdb/milvus:v2.5.17" in compose_text
    assert "container_name: thesis-defense-agent-milvus" in compose_text
    assert 'command: ["milvus", "run", "standalone"]' in compose_text
    assert '"${MILVUS_PORT:-19530}:19530"' in compose_text
    assert '"${MILVUS_METRICS_PORT:-9091}:9091"' in compose_text
    assert 'ETCD_USE_EMBED: "true"' in compose_text
    assert 'COMMON_STORAGETYPE: "local"' in compose_text


def test_docker_compose_milvus_uses_named_volume():
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "milvus_data:/var/lib/milvus" in compose_text
    assert "  milvus_data:" in compose_text


def test_env_example_documents_milvus_defaults():
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "MILVUS_URI=http://127.0.0.1:19530" in env_text
    assert "MILVUS_TOKEN=" in env_text
    assert "MILVUS_COLLECTION=thesis_chunks" in env_text
    assert "MILVUS_VECTOR_SIZE=1024" in env_text
    assert "MILVUS_METRIC_TYPE=COSINE" in env_text
    assert "MILVUS_PORT=19530" in env_text
    assert "MILVUS_METRICS_PORT=9091" in env_text


def test_app_config_documents_milvus_defaults_without_secret():
    config_text = (ROOT / "app" / "config.py").read_text(encoding="utf-8")

    assert 'MILVUS_URI = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")' in config_text
    assert 'MILVUS_TOKEN = os.getenv("MILVUS_TOKEN", "")' in config_text
    assert 'MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "thesis_chunks")' in config_text
    assert 'MILVUS_VECTOR_SIZE = int(os.getenv("MILVUS_VECTOR_SIZE", "1024"))' in config_text
    assert 'MILVUS_METRIC_TYPE = os.getenv("MILVUS_METRIC_TYPE", "COSINE")' in config_text
    assert "milvus_token_here" not in config_text


def test_milvus_docs_include_runtime_smoke_commands():
    docs_text = (
        ROOT / "docs" / "deployment" / "milvus.md"
    ).read_text(encoding="utf-8")

    assert "docker compose up -d milvus" in docs_text
    assert "import-vector-store-to-milvus" in docs_text
    assert "compare-vector-store-backends" in docs_text
    assert "--include-milvus" in docs_text
    assert "JSON / Qdrant / Milvus benchmark result report" in docs_text

