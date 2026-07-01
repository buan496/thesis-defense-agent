# Kubernetes Manifests

## Purpose

This directory contains learning-version Kubernetes manifests for the
stateless runtime path:

```text
FastAPI API
Prometheus
Alertmanager
Qdrant
```

The goal is to translate the existing Docker Compose mental model into
Kubernetes resource objects:

```text
docker-compose service
-> Deployment
-> Service
-> ConfigMap
-> Secret example
```

This is not a production K8s release yet.

## Files

```text
k8s/base/namespace.yaml
k8s/base/kustomization.yaml
k8s/base/api-configmap.yaml
k8s/base/api-secret.example.yaml
k8s/base/api-deployment.yaml
k8s/base/api-pod-disruption-budget.yaml
k8s/base/api-service.yaml
k8s/base/qdrant-statefulset.yaml
k8s/base/qdrant-pod-disruption-budget.yaml
k8s/base/qdrant-service.yaml
k8s/base/prometheus-configmap.yaml
k8s/base/prometheus-deployment.yaml
k8s/base/prometheus-pod-disruption-budget.yaml
k8s/base/prometheus-service.yaml
k8s/base/alertmanager-configmap.yaml
k8s/base/alertmanager-deployment.yaml
k8s/base/alertmanager-pod-disruption-budget.yaml
k8s/base/alertmanager-service.yaml
```

## Resource Mapping

### API

```text
Docker Compose api
-> thesis-defense-agent-api Deployment
-> api Service
-> thesis-defense-agent-api-config ConfigMap
-> thesis-defense-agent-api-secret Secret example
```

The API image defaults to:

```text
ghcr.io/buan496/thesis-defense-agent:latest
```

The deployment exposes:

```text
containerPort: 8000
readinessProbe: /health
livenessProbe: /health
resources requests / limits
rollingUpdate maxUnavailable=0 maxSurge=1
PodDisruptionBudget minAvailable=1
restricted container securityContext
```

Runtime data currently uses:

```text
emptyDir: {}
```

This is intentional for the first learning version. Persistent task, trace, and
vector-store data should be moved to PVC or an external storage backend in a
later phase.

### Prometheus

```text
Docker Compose prometheus
-> thesis-defense-agent-prometheus Deployment
-> prometheus Service
-> thesis-defense-agent-prometheus-config ConfigMap
```

Prometheus scrapes the API service through the Kubernetes DNS name:

```text
api:8000
```

Prometheus sends alerts to:

```text
alertmanager:9093
```

### Alertmanager

```text
Docker Compose alertmanager
-> thesis-defense-agent-alertmanager Deployment
-> alertmanager Service
-> thesis-defense-agent-alertmanager-config ConfigMap
```

Alertmanager sends local webhook notifications to:

```text
http://api:8000/alerts/alertmanager
```

### Qdrant

```text
Docker Compose qdrant
-> qdrant StatefulSet
-> qdrant Service
-> qdrant-pdb PodDisruptionBudget
-> storage-qdrant-0 PersistentVolumeClaim
```

The in-cluster API configuration points to:

```text
QDRANT_URL=http://qdrant:6333
```

The service is `ClusterIP` only. It exposes:

```text
http: 6333
grpc: 6334
```

The StatefulSet keeps one replica in this learning version and mounts:

```text
/qdrant/storage
```

through a `ReadWriteOnce` PVC. This is enough for local kind validation and
future Qdrant CronJob smoke tests, but it is not yet a production HA Qdrant
topology.

## Production-Basics Hardening

This repository still keeps the manifests as a learning-version base, but the
base now includes the minimum fields that should be present before discussing
real cluster deployment:

```text
revisionHistoryLimit: keep recent ReplicaSets for rollback
progressDeadlineSeconds: fail stuck rollouts instead of waiting forever
RollingUpdate: create a new pod before removing the old pod
readinessProbe: remove unhealthy pods from Service endpoints
livenessProbe: restart stuck pods
resources.requests: make scheduling requirements explicit
resources.limits: cap runaway CPU / memory usage
securityContext: run without privilege escalation and drop Linux capabilities
PodDisruptionBudget: reduce voluntary-disruption downtime
```

The API keeps `replicas: 1` in this learning version. The default runtime
backend is still JSON / `emptyDir`, so increasing API replicas would create
inconsistent local task/session files across pods. Use PostgreSQL and external
vector storage before scaling API replicas.

The Docker image is also prepared for the Kubernetes security context:

```text
USER 10001:10001
HOME=/app
UV_CACHE_DIR=/app/.cache/uv
/app/data owned by uid 10001
```

This keeps the container compatible with `runAsNonRoot: true`.

## Secret Boundary

Do not commit real secrets.

The file below is only a template:

```text
k8s/base/api-secret.example.yaml
```

Before applying manifests to a real cluster, create a real Secret using your
local values:

```powershell
kubectl create secret generic thesis-defense-agent-api-secret `
  --namespace thesis-defense-agent `
  --from-literal=DEEPSEEK_API_KEY="<real-key>" `
  --from-literal=DEEPSEEK_BASE_URL="https://api.deepseek.com" `
  --from-literal=DEEPSEEK_MODEL="deepseek-v4-flash" `
  --from-literal=EMBEDDING_API_KEY="<real-key>" `
  --from-literal=EMBEDDING_BASE_URL="https://api.siliconflow.cn/v1" `
  --from-literal=EMBEDDING_MODEL="BAAI/bge-m3"
```

## Optional Local Validation

If `kubectl` is installed but no cluster is running, render manifests offline:

```powershell
kubectl kustomize k8s/base
```

If a cluster context is configured, run client-side dry-run without server schema validation:

```powershell
kubectl apply --dry-run=client --validate=false -k k8s/base
```

If a cluster is configured, run client-side validation with server schema discovery:

```powershell
kubectl apply --dry-run=client -k k8s/base
```

Apply to a local cluster:

```powershell
kubectl apply -k k8s/base
```

Check pods and services:

```powershell
kubectl get pods -n thesis-defense-agent
kubectl get services -n thesis-defense-agent
```

Port-forward API:

```powershell
kubectl port-forward service/api 8000:8000 -n thesis-defense-agent
```

Port-forward Prometheus:

```powershell
kubectl port-forward service/prometheus 9090:9090 -n thesis-defense-agent
```

Port-forward Alertmanager:

```powershell
kubectl port-forward service/alertmanager 9093:9093 -n thesis-defense-agent
```

## Rollout / Rollback SOP

Generate the smoke-test plan from code:

```powershell
uv run python -m app.cli k8s-smoke-plan
```

Save the plan as Markdown:

```powershell
uv run python -m app.cli k8s-smoke-plan `
  --output data/reports/k8s_smoke_plan.md
```

Generate an execution report template before running against a real cluster:

```powershell
uv run python -m app.cli k8s-smoke-report-template `
  --environment kind-local `
  --operator "<your-name>" `
  --output data/reports/k8s_smoke_report.md
```

The report template is intentionally separate from the plan. The plan describes
what to run; the report records sanitized evidence, PASS / FAIL status, skipped
steps, and notes after running the commands.

Run the smoke-test runner in offline mode:

```powershell
uv run python -m app.cli k8s-smoke-run
```

Offline mode runs only:

```text
kubectl kustomize k8s/base
```

Run cluster steps against the current `kubectl` context:

```powershell
uv run python -m app.cli k8s-smoke-run `
  --apply-cluster `
  --output data/reports/k8s_smoke_run.md
```

The cluster run applies manifests, waits for rollouts, and inspects workloads.
It skips `port-forward`, API health check through localhost, and rollback unless
explicitly requested:

```powershell
uv run python -m app.cli k8s-smoke-run `
  --apply-cluster `
  --include-port-forward `
  --include-rollback `
  --output data/reports/k8s_smoke_run_full.md
```

Use `--allow-fail` when collecting evidence from a partially available cluster
without failing the command:

```powershell
uv run python -m app.cli k8s-smoke-run --apply-cluster --allow-fail
```

Render manifests before applying:

```powershell
kubectl kustomize k8s/base
```

Apply the base:

```powershell
kubectl apply -k k8s/base
```

Watch rollout status:

```powershell
kubectl rollout status deployment/thesis-defense-agent-api -n thesis-defense-agent
kubectl rollout status statefulset/qdrant -n thesis-defense-agent
kubectl rollout status deployment/thesis-defense-agent-prometheus -n thesis-defense-agent
kubectl rollout status deployment/thesis-defense-agent-alertmanager -n thesis-defense-agent
```

Inspect rollout history:

```powershell
kubectl rollout history deployment/thesis-defense-agent-api -n thesis-defense-agent
```

Rollback the API deployment to the previous ReplicaSet:

```powershell
kubectl rollout undo deployment/thesis-defense-agent-api -n thesis-defense-agent
```

Check events when rollout is stuck:

```powershell
kubectl describe deployment/thesis-defense-agent-api -n thesis-defense-agent
kubectl get events -n thesis-defense-agent --sort-by=.lastTimestamp
```

Check effective pod resources and probes:

```powershell
kubectl describe pod -l app.kubernetes.io/name=thesis-defense-agent-api -n thesis-defense-agent
```

Check Qdrant runtime state:

```powershell
kubectl get pod,svc,statefulset,pvc,pdb -n thesis-defense-agent -l app.kubernetes.io/name=qdrant
kubectl get endpoints qdrant -n thesis-defense-agent
kubectl describe statefulset qdrant -n thesis-defense-agent
```

Port-forward Qdrant readiness:

```powershell
kubectl port-forward service/qdrant 16333:6333 -n thesis-defense-agent
Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:16333/readyz
```


## Local Kind Smoke Evidence

Verified on 2026-07-01 with local `kind-thesis-defense-agent` context.
The raw smoke report is stored under `data/reports/` and is intentionally not committed.

Validation summary:

```text
uv run python -m app.cli k8s-smoke-run --apply-cluster --output data/reports/k8s_smoke_run.md

Overall status: passed
thesis-defense-agent-api: successfully rolled out
thesis-defense-agent-prometheus: successfully rolled out
thesis-defense-agent-alertmanager: successfully rolled out
api pod: 1/1 Running, restarts 0
prometheus pod: 1/1 Running, restarts 0
alertmanager pod: 1/1 Running, restarts 0
```

Service checks:

```text
GET /health -> {"status":"ok","service":"thesis-defense-agent"}
Prometheus /-/ready -> ready
Prometheus target http://api:8000/metrics/prometheus -> up
Alertmanager /-/ready -> OK
Alertmanager status -> ready
```

## Local Kind Qdrant Runtime Evidence

Verified on 2026-07-01 with local `kind-thesis-defense-agent` context.
The raw Qdrant smoke report is stored under `data/reports/` and is intentionally not committed.

Validation summary:

```text
kubectl apply -k k8s/base
kubectl rollout status statefulset/qdrant -n thesis-defense-agent
uv run python -m app.cli k8s-smoke-run --apply-cluster --output data/reports/k8s_smoke_run_qdrant.md

Overall status: passed
qdrant-0: 1/1 Running
qdrant StatefulSet: 1/1 ready
storage-qdrant-0 PVC: Bound
qdrant Service: ClusterIP
qdrant endpoints: 6333 and 6334 populated
GET /readyz through port-forward: 200
```

Local kind proxy note:

```text
The local Docker Desktop / kind node initially failed to pull qdrant/qdrant:v1.18.2
because the node inherited HTTP_PROXY=http://127.0.0.1:10808. Inside the kind node,
127.0.0.1 points to the node container, not the Windows host proxy.

For this local validation only, the kind node proxy was changed to:
HTTP_PROXY=http://host.docker.internal:10808

This is local environment evidence, not a repository configuration requirement.
```

## Local Container Smoke Test

Validate that the Docker image starts as the non-root app user:

```powershell
docker build -t thesis-defense-agent:k8s-production-basics .

docker run -d --name thesis-agent-k8s-test `
  -p 18000:8000 `
  -e DEEPSEEK_API_KEY=dummy `
  -e EMBEDDING_API_KEY=dummy `
  thesis-defense-agent:k8s-production-basics

docker exec thesis-agent-k8s-test id
curl.exe -f http://127.0.0.1:18000/health
docker rm -f thesis-agent-k8s-test
```

## Current Boundary

Completed:

```text
Namespace
API Deployment / Service
API ConfigMap
API Secret example
Prometheus Deployment / Service / ConfigMap
Alertmanager Deployment / Service / ConfigMap
readiness and liveness probes
resource requests and limits
rolling update strategy
revision history and progress deadline
restricted container securityContext
PodDisruptionBudget resources
k8s-smoke-plan CLI
k8s-smoke-report-template CLI
k8s-smoke-run CLI
automated offline / optional cluster smoke runner
offline manifest tests
local kind real-cluster smoke execution evidence
Qdrant StatefulSet / Service / PVC / PDB runtime validation
Qdrant Kubernetes CronJob manual Job smoke evidence
```

Not completed:

```text
Ingress
TLS
HorizontalPodAutoscaler
NetworkPolicy
PersistentVolumeClaim for /app/data
PostgreSQL StatefulSet
production Secret management
Helm chart / Kustomize overlays
Qdrant Kubernetes CronJob long-running schedule evidence
```

## Qdrant Kubernetes CronJob Smoke

Before running the CronJob smoke, seed the in-cluster Qdrant collection through
a temporary port-forward:

```powershell
$process = Start-Process -FilePath kubectl `
  -ArgumentList @("port-forward","service/qdrant","16333:6333","-n","thesis-defense-agent") `
  -PassThru `
  -WindowStyle Hidden

try {
  Start-Sleep -Seconds 5
  uv run python -m app.cli import-vector-store-to-qdrant `
    --source data/vector_store.json `
    --url http://127.0.0.1:16333 `
    --collection thesis_chunks `
    --vector-size 1024 `
    --distance Cosine
}
finally {
  if ($process -and -not $process.HasExited) {
    Stop-Process -Id $process.Id -Force
  }
}
```

Run one CronJob smoke cycle by manually triggering a Job:

```powershell
uv run python -m app.cli qdrant-k8s-cronjob-smoke-run `
  --namespace thesis-defense-agent `
  --cron-schedule "*/10 * * * *" `
  --cleanup-job `
  --cleanup-cronjob `
  --manifest-output data/reports/qdrant_k8s_cronjob_smoke.yaml `
  --output data/reports/qdrant_k8s_cronjob_smoke.md
```

The smoke runner executes:

```text
kubectl apply -f <generated-cronjob-yaml>
kubectl get cronjob ...
kubectl create job ... --from=cronjob/...
kubectl wait --for=condition=complete job/...
kubectl get job ...
kubectl get pods -l job-name=...
kubectl logs job/...
optional cleanup job
optional cleanup cronjob
```

Verified local kind result:

```text
Overall status: passed
Manual Job status: Complete
Job Pod status: Completed
Job logs include Qdrant Snapshot Drill Report
Snapshot create: completed
Snapshot download: completed
Retention: dry_run=True
```

Current boundary:

```text
This validates that the CronJob template can run a manually triggered Job.
It does not prove natural schedule execution over time.
Default smoke mode skips restore and JSON baseline compare.
Use --run-restore-drill and --run-compare only after confirming the image has the required data and dependencies.
```
