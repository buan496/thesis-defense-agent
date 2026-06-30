from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docker_compose_defines_alertmanager_service():
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "  alertmanager:" in compose_text
    assert "image: prom/alertmanager:v0.28.1" in compose_text
    assert "container_name: thesis-defense-agent-alertmanager" in compose_text
    assert '"${ALERTMANAGER_PORT:-9093}:9093"' in compose_text
    assert (
        "./observability/alertmanager/alertmanager.yml:"
        "/etc/alertmanager/alertmanager.yml:ro"
    ) in compose_text
    assert "--config.file=/etc/alertmanager/alertmanager.yml" in compose_text


def test_prometheus_config_routes_alerts_to_alertmanager():
    prometheus_text = (
        ROOT / "observability" / "prometheus" / "prometheus.yml"
    ).read_text(encoding="utf-8")

    assert "alerting:" in prometheus_text
    assert "alertmanagers:" in prometheus_text
    assert '"alertmanager:9093"' in prometheus_text


def test_alertmanager_config_defines_local_webhook_receiver():
    alertmanager_text = (
        ROOT / "observability" / "alertmanager" / "alertmanager.yml"
    ).read_text(encoding="utf-8")

    assert "route:" in alertmanager_text
    assert "receiver: local-webhook" in alertmanager_text
    assert "group_by:" in alertmanager_text
    assert "group_wait: 10s" in alertmanager_text
    assert "group_interval: 1m" in alertmanager_text
    assert "repeat_interval: 30m" in alertmanager_text
    assert 'severity="critical"' in alertmanager_text
    assert "webhook_configs:" in alertmanager_text
    assert "url: http://api:8000/alerts/alertmanager" in alertmanager_text
    assert "send_resolved: true" in alertmanager_text


def test_env_example_documents_alertmanager_port():
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "ALERTMANAGER_PORT=9093" in env_text
