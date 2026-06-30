from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_prometheus_config_loads_alert_rules():
    prometheus_text = (
        ROOT / "observability" / "prometheus" / "prometheus.yml"
    ).read_text(encoding="utf-8")

    assert "alerting:" in prometheus_text
    assert '"alertmanager:9093"' in prometheus_text
    assert "rule_files:" in prometheus_text
    assert "- /etc/prometheus/alert_rules.yml" in prometheus_text
    assert 'job_name: "thesis-defense-agent-api"' in prometheus_text
    assert 'metrics_path: "/metrics/prometheus"' in prometheus_text


def test_docker_compose_mounts_prometheus_alert_rules():
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert (
        "./observability/prometheus/prometheus.yml:"
        "/etc/prometheus/prometheus.yml:ro"
    ) in compose_text
    assert (
        "./observability/prometheus/alert_rules.yml:"
        "/etc/prometheus/alert_rules.yml:ro"
    ) in compose_text


def test_prometheus_alert_rules_define_api_operational_alerts():
    alert_text = (
        ROOT / "observability" / "prometheus" / "alert_rules.yml"
    ).read_text(encoding="utf-8")

    assert "groups:" in alert_text
    assert "name: thesis-defense-agent-api" in alert_text
    assert "alert: ThesisDefenseAgentApiDown" in alert_text
    assert 'up{job="thesis-defense-agent-api"} == 0' in alert_text
    assert "alert: ThesisDefenseAgentHigh5xxRate" in alert_text
    assert (
        'thesis_defense_api_request_status_total{status_code=~"5.."}'
        in alert_text
    )
    assert "clamp_min(sum(rate(thesis_defense_api_requests_total[5m])), 1)" in alert_text
    assert "alert: ThesisDefenseAgentHighAverageLatency" in alert_text
    assert "thesis_defense_api_request_duration_ms_average > 2000" in alert_text
    assert "severity: critical" in alert_text
    assert "severity: warning" in alert_text


def test_prometheus_alerts_documentation_exists():
    docs_text = (
        ROOT / "docs" / "deployment" / "prometheus.md"
    ).read_text(encoding="utf-8")

    assert "# Prometheus Alerts" in docs_text
    assert "ThesisDefenseAgentApiDown" in docs_text
    assert "ThesisDefenseAgentHigh5xxRate" in docs_text
    assert "ThesisDefenseAgentHighAverageLatency" in docs_text
    assert "docker compose up -d api alertmanager prometheus" in docs_text
    assert "Alertmanager" in docs_text
