import json
import shlex

from app.qdrant_snapshot_scheduler import QdrantSnapshotScheduleConfig


def render_qdrant_snapshot_cronjob_manifest(
    config: QdrantSnapshotScheduleConfig,
    config_map_name: str = "thesis-defense-agent-api-config",
    secret_name: str = "thesis-defense-agent-api-secret",
) -> str:
    if config.platform != "kubernetes_cronjob":
        raise ValueError("platform must be kubernetes_cronjob")

    normalized_config_map_name = config_map_name.strip()
    normalized_secret_name = secret_name.strip()

    if not normalized_config_map_name:
        raise ValueError("config_map_name must not be empty")

    if not normalized_secret_name:
        raise ValueError("secret_name must not be empty")

    args = shlex.split(config.runner_command)
    lines = [
        "apiVersion: batch/v1",
        "kind: CronJob",
        "metadata:",
        f"  name: {config.task_name}",
        f"  namespace: {config.namespace}",
        "  labels:",
        "    app.kubernetes.io/name: qdrant-snapshot-drill",
        "    app.kubernetes.io/part-of: thesis-defense-agent",
        "  annotations:",
        "    thesis-defense-agent/safety: restore-to-disposable-collection",
        "spec:",
        f"  schedule: {_quote_yaml(config.cron_schedule)}",
        "  suspend: false",
        "  concurrencyPolicy: Forbid",
        "  startingDeadlineSeconds: 600",
        "  successfulJobsHistoryLimit: 3",
        "  failedJobsHistoryLimit: 3",
        "  jobTemplate:",
        "    spec:",
        "      backoffLimit: 0",
        "      ttlSecondsAfterFinished: 86400",
        "      template:",
        "        metadata:",
        "          labels:",
        "            app.kubernetes.io/name: qdrant-snapshot-drill",
        "            app.kubernetes.io/part-of: thesis-defense-agent",
        "        spec:",
        "          restartPolicy: Never",
        "          securityContext:",
        "            runAsNonRoot: true",
        "            runAsUser: 10001",
        "            runAsGroup: 10001",
        "            fsGroup: 10001",
        "            seccompProfile:",
        "              type: RuntimeDefault",
        "          containers:",
        "            - name: qdrant-snapshot-drill",
        f"              image: {config.image}",
        "              imagePullPolicy: IfNotPresent",
        "              envFrom:",
        "                - configMapRef:",
        f"                    name: {normalized_config_map_name}",
        "                - secretRef:",
        f"                    name: {normalized_secret_name}",
        "                    optional: true",
        "              args:",
    ]

    for arg in args:
        lines.append(f"                - {_quote_yaml(arg)}")

    lines.extend(
        [
            "              volumeMounts:",
            "                - name: data",
            "                  mountPath: /app/data",
            "              resources:",
            "                requests:",
            "                  cpu: 100m",
            "                  memory: 256Mi",
            "                limits:",
            "                  cpu: 1000m",
            "                  memory: 1Gi",
            "              securityContext:",
            "                allowPrivilegeEscalation: false",
            "                capabilities:",
            "                  drop:",
            "                    - ALL",
            "          volumes:",
            "            - name: data",
            "              emptyDir: {}",
            "",
        ]
    )

    return "\n".join(lines)


def _quote_yaml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)
