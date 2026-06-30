from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
K8S_BASE = ROOT / "k8s" / "base"


EXPECTED_MANIFESTS = [
    "kustomization.yaml",
    "namespace.yaml",
    "api-configmap.yaml",
    "api-secret.example.yaml",
    "api-deployment.yaml",
    "api-service.yaml",
    "prometheus-configmap.yaml",
    "prometheus-deployment.yaml",
    "prometheus-service.yaml",
    "alertmanager-configmap.yaml",
    "alertmanager-deployment.yaml",
    "alertmanager-service.yaml",
]


def read_manifest(name: str) -> str:
    return (K8S_BASE / name).read_text(encoding="utf-8")


def test_k8s_base_manifest_files_exist():
    for manifest_name in EXPECTED_MANIFESTS:
        assert (K8S_BASE / manifest_name).exists()


def test_k8s_kustomization_lists_base_resources():
    text = read_manifest("kustomization.yaml")

    assert "kind: Kustomization" in text
    for manifest_name in EXPECTED_MANIFESTS:
        if manifest_name == "kustomization.yaml":
            continue

        assert f"- {manifest_name}" in text


def test_k8s_namespace_is_scoped_to_project():
    text = read_manifest("namespace.yaml")

    assert "kind: Namespace" in text
    assert "name: thesis-defense-agent" in text


def test_k8s_api_deployment_maps_compose_api_service():
    text = read_manifest("api-deployment.yaml")

    assert "kind: Deployment" in text
    assert "name: thesis-defense-agent-api" in text
    assert "namespace: thesis-defense-agent" in text
    assert "image: ghcr.io/buan496/thesis-defense-agent:latest" in text
    assert "containerPort: 8000" in text
    assert "configMapRef:" in text
    assert "name: thesis-defense-agent-api-config" in text
    assert "secretRef:" in text
    assert "name: thesis-defense-agent-api-secret" in text
    assert "optional: true" in text
    assert "readinessProbe:" in text
    assert "livenessProbe:" in text
    assert "path: /health" in text
    assert "emptyDir: {}" in text


def test_k8s_api_service_uses_compose_dns_name():
    text = read_manifest("api-service.yaml")

    assert "kind: Service" in text
    assert "name: api" in text
    assert "port: 8000" in text
    assert "targetPort: http" in text


def test_k8s_api_configmap_keeps_non_secret_runtime_config():
    text = read_manifest("api-configmap.yaml")

    assert "kind: ConfigMap" in text
    assert "STORAGE_BACKEND: \"json\"" in text
    assert "VECTOR_STORE_BACKEND: \"json\"" in text
    assert "RAG_VECTOR_STORE_PATH: \"data/vector_store.json\"" in text
    assert "DEEPSEEK_API_KEY" not in text
    assert "EMBEDDING_API_KEY" not in text


def test_k8s_api_secret_example_contains_only_placeholders():
    text = read_manifest("api-secret.example.yaml")

    assert "kind: Secret" in text
    assert "stringData:" in text
    assert "replace-with-real-deepseek-api-key" in text
    assert "replace-with-real-embedding-api-key" in text
    assert "your_deepseek_api_key_here" not in text
    assert "your_embedding_api_key_here" not in text


def test_k8s_prometheus_config_keeps_api_and_alertmanager_dns_names():
    text = read_manifest("prometheus-configmap.yaml")

    assert "kind: ConfigMap" in text
    assert "prometheus.yml: |" in text
    assert "- \"api:8000\"" in text
    assert "- \"alertmanager:9093\"" in text
    assert "alert_rules.yml: |" in text
    assert "ThesisDefenseAgentApiDown" in text
    assert "ThesisDefenseAgentHigh5xxRate" in text
    assert "ThesisDefenseAgentHighAverageLatency" in text


def test_k8s_prometheus_deployment_and_service_are_cluster_internal():
    deployment_text = read_manifest("prometheus-deployment.yaml")
    service_text = read_manifest("prometheus-service.yaml")

    assert "image: prom/prometheus:v3.8.0" in deployment_text
    assert "--config.file=/etc/prometheus/prometheus.yml" in deployment_text
    assert "subPath: prometheus.yml" in deployment_text
    assert "subPath: alert_rules.yml" in deployment_text
    assert "readinessProbe:" in deployment_text
    assert "livenessProbe:" in deployment_text
    assert "name: prometheus" in service_text
    assert "type: ClusterIP" in service_text
    assert "port: 9090" in service_text


def test_k8s_alertmanager_config_routes_to_api_webhook():
    text = read_manifest("alertmanager-configmap.yaml")

    assert "kind: ConfigMap" in text
    assert "alertmanager.yml: |" in text
    assert "receiver: local-webhook" in text
    assert "group_wait: 10s" in text
    assert "repeat_interval: 30m" in text
    assert "url: http://api:8000/alerts/alertmanager" in text
    assert "send_resolved: true" in text


def test_k8s_alertmanager_deployment_and_service_are_cluster_internal():
    deployment_text = read_manifest("alertmanager-deployment.yaml")
    service_text = read_manifest("alertmanager-service.yaml")

    assert "image: prom/alertmanager:v0.28.1" in deployment_text
    assert "--config.file=/etc/alertmanager/alertmanager.yml" in deployment_text
    assert "subPath: alertmanager.yml" in deployment_text
    assert "readinessProbe:" in deployment_text
    assert "livenessProbe:" in deployment_text
    assert "name: alertmanager" in service_text
    assert "type: ClusterIP" in service_text
    assert "port: 9093" in service_text
