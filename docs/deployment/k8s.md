# Kubernetes Manifests

## Purpose

This directory contains learning-version Kubernetes manifests for the
stateless runtime path:

```text
FastAPI API
Prometheus
Alertmanager
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
k8s/base/api-service.yaml
k8s/base/prometheus-configmap.yaml
k8s/base/prometheus-deployment.yaml
k8s/base/prometheus-service.yaml
k8s/base/alertmanager-configmap.yaml
k8s/base/alertmanager-deployment.yaml
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

If a cluster is configured, run client-side validation:

```powershell
kubectl apply --dry-run=client -f k8s/base
```

Apply to a local cluster:

```powershell
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base
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
offline manifest tests
```

Not completed:

```text
Ingress
TLS
HorizontalPodAutoscaler
NetworkPolicy
PersistentVolumeClaim for /app/data
PostgreSQL StatefulSet
Qdrant StatefulSet
production Secret management
Helm chart / Kustomize overlays
real cluster smoke test
```
