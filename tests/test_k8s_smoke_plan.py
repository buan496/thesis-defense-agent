import pytest

from app.k8s_smoke_plan import (
    build_k8s_smoke_plan,
    render_k8s_smoke_plan,
    render_k8s_smoke_report_template,
)


def test_build_k8s_smoke_plan_contains_offline_and_cluster_steps():
    plan = build_k8s_smoke_plan()

    assert plan.namespace == "thesis-defense-agent"
    assert plan.kustomize_dir == "k8s/base"
    assert plan.api_local_port == 18000

    step_names = [step.name for step in plan.steps]

    assert step_names == [
        "render_manifests",
        "client_dry_run",
        "apply_manifests",
        "rollout_api",
        "rollout_prometheus",
        "rollout_alertmanager",
        "inspect_workloads",
        "port_forward_api",
        "health_check_api",
        "rollback_api",
    ]

    assert plan.steps[0].requires_cluster is False
    assert plan.steps[1].requires_cluster is True
    assert all(step.requires_cluster for step in plan.steps[1:])
    assert "kubectl kustomize k8s/base" in plan.steps[0].command
    assert (
        "kubectl apply --dry-run=client --validate=false -k k8s/base"
        in plan.steps[1].command
    )
    assert (
        "kubectl rollout status deployment/thesis-defense-agent-api "
        "-n thesis-defense-agent"
    ) in plan.steps[3].command
    assert "curl.exe -f http://127.0.0.1:18000/health" in plan.steps[8].command


def test_build_k8s_smoke_plan_accepts_custom_values():
    plan = build_k8s_smoke_plan(
        namespace="custom-namespace",
        kustomize_dir="deploy/k8s",
        api_local_port=19000,
    )

    rendered = render_k8s_smoke_plan(plan)

    assert "Namespace: `custom-namespace`" in rendered
    assert "Kustomize directory: `deploy/k8s`" in rendered
    assert "API local port: `19000`" in rendered
    assert "kubectl apply -k deploy/k8s" in rendered
    assert "curl.exe -f http://127.0.0.1:19000/health" in rendered


def test_build_k8s_smoke_plan_rejects_invalid_values():
    with pytest.raises(ValueError, match="namespace"):
        build_k8s_smoke_plan(namespace=" ")

    with pytest.raises(ValueError, match="kustomize_dir"):
        build_k8s_smoke_plan(kustomize_dir="")

    with pytest.raises(ValueError, match="api_local_port"):
        build_k8s_smoke_plan(api_local_port=0)


def test_render_k8s_smoke_plan_marks_cluster_required_steps():
    plan = build_k8s_smoke_plan()
    rendered = render_k8s_smoke_plan(plan)

    assert "# K8s Smoke Test Plan" in rendered
    assert "## 1. render_manifests" in rendered
    assert "- Scope: `offline`" in rendered
    assert "## 3. apply_manifests" in rendered
    assert "- Scope: `requires cluster`" in rendered
    assert "rollback_api" in rendered


def test_render_k8s_smoke_report_template_contains_evidence_fields():
    plan = build_k8s_smoke_plan(
        namespace="test-ns",
        api_local_port=19000,
    )

    rendered = render_k8s_smoke_report_template(
        plan,
        environment="kind-local",
        operator="tester",
    )

    assert "# K8s Smoke Test Execution Report" in rendered
    assert "- Environment: `kind-local`" in rendered
    assert "- Operator: `tester`" in rendered
    assert "- Result: `[ ] PASS  [ ] FAIL  [ ] SKIPPED`" in rendered
    assert "Evidence:" in rendered
    assert "Paste sanitized command output here." in rendered
    assert "kubectl rollout status deployment/thesis-defense-agent-api -n test-ns" in rendered
    assert "curl.exe -f http://127.0.0.1:19000/health" in rendered


def test_render_k8s_smoke_report_template_rejects_empty_environment():
    plan = build_k8s_smoke_plan()

    with pytest.raises(ValueError, match="environment"):
        render_k8s_smoke_report_template(plan, environment=" ")
