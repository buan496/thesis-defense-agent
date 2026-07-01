from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
K8S_BASE = ROOT / "k8s" / "base"


EXPECTED_MANIFESTS = [
    "kustomization.yaml",
    "namespace.yaml",
    "api-configmap.yaml",
    "api-secret.example.yaml",
    "api-deployment.yaml",
    "api-pod-disruption-budget.yaml",
    "api-service.yaml",
    "qdrant-statefulset.yaml",
    "qdrant-pod-disruption-budget.yaml",
    "qdrant-service.yaml",
    "prometheus-configmap.yaml",
    "prometheus-deployment.yaml",
    "prometheus-pod-disruption-budget.yaml",
    "prometheus-service.yaml",
    "alertmanager-configmap.yaml",
    "alertmanager-deployment.yaml",
    "alertmanager-pod-disruption-budget.yaml",
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
    assert "revisionHistoryLimit: 3" in text
    assert "progressDeadlineSeconds: 180" in text
    assert "type: RollingUpdate" in text
    assert "maxUnavailable: 0" in text
    assert "maxSurge: 1" in text
    assert "terminationGracePeriodSeconds: 30" in text
    assert "runAsNonRoot: true" in text
    assert "runAsUser: 10001" in text
    assert "seccompProfile:" in text
    assert "type: RuntimeDefault" in text
    assert "allowPrivilegeEscalation: false" in text
    assert "drop:" in text
    assert "- ALL" in text
    assert "requests:" in text
    assert "limits:" in text
    assert "emptyDir: {}" in text


def test_k8s_api_pod_disruption_budget_targets_api_pods():
    text = read_manifest("api-pod-disruption-budget.yaml")

    assert "kind: PodDisruptionBudget" in text
    assert "name: thesis-defense-agent-api-pdb" in text
    assert "namespace: thesis-defense-agent" in text
    assert "minAvailable: 1" in text
    assert "app.kubernetes.io/name: thesis-defense-agent-api" in text


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
    assert "QDRANT_URL: \"http://qdrant:6333\"" in text
    assert "QDRANT_COLLECTION: \"thesis_chunks\"" in text
    assert "QDRANT_VECTOR_SIZE: \"1024\"" in text
    assert "QDRANT_DISTANCE: \"Cosine\"" in text
    assert "QDRANT_BACKUP_DIR: \"data/qdrant_backups\"" in text
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


def test_k8s_qdrant_statefulset_uses_persistent_storage_and_probes():
    text = read_manifest("qdrant-statefulset.yaml")

    assert "kind: StatefulSet" in text
    assert "name: qdrant" in text
    assert "namespace: thesis-defense-agent" in text
    assert "serviceName: qdrant" in text
    assert "replicas: 1" in text
    assert "image: qdrant/qdrant:v1.18.2" in text
    assert "containerPort: 6333" in text
    assert "containerPort: 6334" in text
    assert "QDRANT__SERVICE__HTTP_PORT" in text
    assert "QDRANT__SERVICE__GRPC_PORT" in text
    assert "readinessProbe:" in text
    assert "path: /readyz" in text
    assert "livenessProbe:" in text
    assert "path: /livez" in text
    assert "volumeClaimTemplates:" in text
    assert "mountPath: /qdrant/storage" in text
    assert "storage: 1Gi" in text
    assert "seccompProfile:" in text
    assert "allowPrivilegeEscalation: false" in text
    assert "drop:" in text
    assert "- ALL" in text
    assert "requests:" in text
    assert "limits:" in text


def test_k8s_qdrant_service_is_cluster_internal():
    text = read_manifest("qdrant-service.yaml")

    assert "kind: Service" in text
    assert "name: qdrant" in text
    assert "type: ClusterIP" in text
    assert "port: 6333" in text
    assert "targetPort: http" in text
    assert "port: 6334" in text
    assert "targetPort: grpc" in text


def test_k8s_qdrant_pod_disruption_budget_targets_qdrant_pods():
    text = read_manifest("qdrant-pod-disruption-budget.yaml")

    assert "kind: PodDisruptionBudget" in text
    assert "name: qdrant-pdb" in text
    assert "namespace: thesis-defense-agent" in text
    assert "minAvailable: 1" in text
    assert "app.kubernetes.io/name: qdrant" in text


def test_k8s_prometheus_deployment_and_service_are_cluster_internal():
    deployment_text = read_manifest("prometheus-deployment.yaml")
    service_text = read_manifest("prometheus-service.yaml")

    assert "image: prom/prometheus:v3.8.0" in deployment_text
    assert "--config.file=/etc/prometheus/prometheus.yml" in deployment_text
    assert "subPath: prometheus.yml" in deployment_text
    assert "subPath: alert_rules.yml" in deployment_text
    assert "readinessProbe:" in deployment_text
    assert "livenessProbe:" in deployment_text
    assert "revisionHistoryLimit: 3" in deployment_text
    assert "progressDeadlineSeconds: 180" in deployment_text
    assert "type: RollingUpdate" in deployment_text
    assert "maxUnavailable: 0" in deployment_text
    assert "maxSurge: 1" in deployment_text
    assert "terminationGracePeriodSeconds: 30" in deployment_text
    assert "runAsNonRoot: true" in deployment_text
    assert "runAsUser: 65534" in deployment_text
    assert "seccompProfile:" in deployment_text
    assert "allowPrivilegeEscalation: false" in deployment_text
    assert "drop:" in deployment_text
    assert "- ALL" in deployment_text
    assert "requests:" in deployment_text
    assert "limits:" in deployment_text
    assert "name: prometheus" in service_text
    assert "type: ClusterIP" in service_text
    assert "port: 9090" in service_text


def test_k8s_prometheus_pod_disruption_budget_targets_prometheus_pods():
    text = read_manifest("prometheus-pod-disruption-budget.yaml")

    assert "kind: PodDisruptionBudget" in text
    assert "name: thesis-defense-agent-prometheus-pdb" in text
    assert "namespace: thesis-defense-agent" in text
    assert "minAvailable: 1" in text
    assert "app.kubernetes.io/name: thesis-defense-agent-prometheus" in text


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
    assert "revisionHistoryLimit: 3" in deployment_text
    assert "progressDeadlineSeconds: 180" in deployment_text
    assert "type: RollingUpdate" in deployment_text
    assert "maxUnavailable: 0" in deployment_text
    assert "maxSurge: 1" in deployment_text
    assert "terminationGracePeriodSeconds: 30" in deployment_text
    assert "runAsNonRoot: true" in deployment_text
    assert "runAsUser: 65534" in deployment_text
    assert "seccompProfile:" in deployment_text
    assert "allowPrivilegeEscalation: false" in deployment_text
    assert "drop:" in deployment_text
    assert "- ALL" in deployment_text
    assert "requests:" in deployment_text
    assert "limits:" in deployment_text
    assert "name: alertmanager" in service_text
    assert "type: ClusterIP" in service_text
    assert "port: 9093" in service_text


def test_k8s_alertmanager_pod_disruption_budget_targets_alertmanager_pods():
    text = read_manifest("alertmanager-pod-disruption-budget.yaml")

    assert "kind: PodDisruptionBudget" in text
    assert "name: thesis-defense-agent-alertmanager-pdb" in text
    assert "namespace: thesis-defense-agent" in text
    assert "minAvailable: 1" in text
    assert "app.kubernetes.io/name: thesis-defense-agent-alertmanager" in text
