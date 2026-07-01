from dataclasses import dataclass


@dataclass(frozen=True)
class K8sSmokeStep:
    phase: str
    name: str
    command: str
    requires_cluster: bool
    description: str


@dataclass(frozen=True)
class K8sSmokePlan:
    namespace: str
    kustomize_dir: str
    api_local_port: int
    steps: list[K8sSmokeStep]


def build_k8s_smoke_plan(
    namespace: str = "thesis-defense-agent",
    kustomize_dir: str = "k8s/base",
    api_local_port: int = 18000,
) -> K8sSmokePlan:
    if not namespace.strip():
        raise ValueError("namespace must not be empty")

    if not kustomize_dir.strip():
        raise ValueError("kustomize_dir must not be empty")

    if api_local_port <= 0:
        raise ValueError("api_local_port must be greater than 0")

    steps = [
        K8sSmokeStep(
            phase="offline",
            name="render_manifests",
            command=f"kubectl kustomize {kustomize_dir}",
            requires_cluster=False,
            description="Render Kustomize manifests without contacting a cluster.",
        ),
        K8sSmokeStep(
            phase="cluster",
            name="client_dry_run",
            command=(
                "kubectl apply --dry-run=client "
                f"--validate=false -k {kustomize_dir}"
            ),
            requires_cluster=True,
            description="Run client-side dry-run against the current Kubernetes API discovery context.",
        ),
        K8sSmokeStep(
            phase="cluster",
            name="apply_manifests",
            command=f"kubectl apply -k {kustomize_dir}",
            requires_cluster=True,
            description="Apply namespace, workloads, services, config, secrets template, and PDBs.",
        ),
        K8sSmokeStep(
            phase="cluster",
            name="rollout_api",
            command=(
                "kubectl rollout status "
                f"deployment/thesis-defense-agent-api -n {namespace}"
            ),
            requires_cluster=True,
            description="Verify the API Deployment finishes rollout.",
        ),
        K8sSmokeStep(
            phase="cluster",
            name="rollout_qdrant",
            command=(
                "kubectl rollout status "
                f"statefulset/qdrant -n {namespace}"
            ),
            requires_cluster=True,
            description="Verify the Qdrant StatefulSet finishes rollout.",
        ),
        K8sSmokeStep(
            phase="cluster",
            name="rollout_prometheus",
            command=(
                "kubectl rollout status "
                f"deployment/thesis-defense-agent-prometheus -n {namespace}"
            ),
            requires_cluster=True,
            description="Verify the Prometheus Deployment finishes rollout.",
        ),
        K8sSmokeStep(
            phase="cluster",
            name="rollout_alertmanager",
            command=(
                "kubectl rollout status "
                f"deployment/thesis-defense-agent-alertmanager -n {namespace}"
            ),
            requires_cluster=True,
            description="Verify the Alertmanager Deployment finishes rollout.",
        ),
        K8sSmokeStep(
            phase="cluster",
            name="inspect_workloads",
            command=f"kubectl get pods,svc,statefulset,pvc,pdb -n {namespace}",
            requires_cluster=True,
            description="Inspect pods, services, stateful workloads, persistent claims, and disruption budgets.",
        ),
        K8sSmokeStep(
            phase="cluster",
            name="port_forward_api",
            command=(
                "kubectl port-forward "
                f"service/api {api_local_port}:8000 -n {namespace}"
            ),
            requires_cluster=True,
            description="Expose the API service locally for health checks.",
        ),
        K8sSmokeStep(
            phase="cluster",
            name="health_check_api",
            command=f"curl.exe -f http://127.0.0.1:{api_local_port}/health",
            requires_cluster=True,
            description="Verify the API health endpoint through the Kubernetes Service.",
        ),
        K8sSmokeStep(
            phase="cluster",
            name="rollback_api",
            command=(
                "kubectl rollout undo "
                f"deployment/thesis-defense-agent-api -n {namespace}"
            ),
            requires_cluster=True,
            description="Rollback command kept as SOP; run only after an intentional rollout test.",
        ),
    ]

    return K8sSmokePlan(
        namespace=namespace,
        kustomize_dir=kustomize_dir,
        api_local_port=api_local_port,
        steps=steps,
    )


def render_k8s_smoke_plan(plan: K8sSmokePlan) -> str:
    lines = [
        "# K8s Smoke Test Plan",
        "",
        f"Namespace: `{plan.namespace}`",
        f"Kustomize directory: `{plan.kustomize_dir}`",
        f"API local port: `{plan.api_local_port}`",
        "",
    ]

    for index, step in enumerate(plan.steps, start=1):
        cluster_label = "requires cluster" if step.requires_cluster else "offline"
        lines.extend(
            [
                f"## {index}. {step.name}",
                "",
                f"- Phase: `{step.phase}`",
                f"- Scope: `{cluster_label}`",
                f"- Purpose: {step.description}",
                "",
                "```powershell",
                step.command,
                "```",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def render_k8s_smoke_report_template(
    plan: K8sSmokePlan,
    environment: str = "local-cluster",
    operator: str = "",
) -> str:
    if not environment.strip():
        raise ValueError("environment must not be empty")

    operator_text = operator.strip() or "TBD"

    lines = [
        "# K8s Smoke Test Execution Report",
        "",
        f"- Environment: `{environment}`",
        f"- Namespace: `{plan.namespace}`",
        f"- Kustomize directory: `{plan.kustomize_dir}`",
        f"- API local port: `{plan.api_local_port}`",
        f"- Operator: `{operator_text}`",
        "- Started at: `TBD`",
        "- Finished at: `TBD`",
        "- Overall status: `TBD`",
        "",
        "Do not paste real API keys, tokens, kubeconfig content, or other secrets into this report.",
        "",
    ]

    for index, step in enumerate(plan.steps, start=1):
        cluster_label = "requires cluster" if step.requires_cluster else "offline"
        lines.extend(
            [
                f"## {index}. {step.name}",
                "",
                f"- Phase: `{step.phase}`",
                f"- Scope: `{cluster_label}`",
                f"- Expected result: {step.description}",
                "- Result: `[ ] PASS  [ ] FAIL  [ ] SKIPPED`",
                "- Notes: `TBD`",
                "",
                "Command:",
                "",
                "```powershell",
                step.command,
                "```",
                "",
                "Evidence:",
                "",
                "```text",
                "Paste sanitized command output here.",
                "```",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"
