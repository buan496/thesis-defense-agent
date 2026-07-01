from dataclasses import dataclass


@dataclass(frozen=True)
class VectorDbCandidate:
    name: str
    role: str
    implementation_status: str
    strengths: list[str]
    risks: list[str]
    required_before_promotion: list[str]


@dataclass(frozen=True)
class VectorDbGovernanceReport:
    current_backend: str
    target_backend: str
    candidates: list[VectorDbCandidate]
    promotion_gates: list[str]
    recommended_next_steps: list[str]


SUPPORTED_CURRENT_BACKENDS = {"json", "qdrant"}
SUPPORTED_TARGET_BACKENDS = {"qdrant", "milvus"}


def build_vector_db_governance_report(
    current_backend: str = "json",
    target_backend: str = "qdrant",
    include_milvus: bool = True,
) -> VectorDbGovernanceReport:
    normalized_current = current_backend.strip().lower()
    normalized_target = target_backend.strip().lower()

    if normalized_current not in SUPPORTED_CURRENT_BACKENDS:
        raise ValueError(
            "current_backend must be one of: "
            f"{', '.join(sorted(SUPPORTED_CURRENT_BACKENDS))}"
        )

    if normalized_target not in SUPPORTED_TARGET_BACKENDS:
        raise ValueError(
            "target_backend must be one of: "
            f"{', '.join(sorted(SUPPORTED_TARGET_BACKENDS))}"
        )

    candidates = [
        VectorDbCandidate(
            name="json",
            role="local baseline and fallback artifact",
            implementation_status="implemented",
            strengths=[
                "simple local debugging",
                "deterministic file-based fallback",
                "works without external service",
            ],
            risks=[
                "not suitable for concurrent writes",
                "full-file load limits scale",
                "no native backup, replication, or query observability",
            ],
            required_before_promotion=[
                "do not promote as production vector database",
                "keep only as rebuild fallback and local development baseline",
            ],
        ),
        VectorDbCandidate(
            name="qdrant",
            role="primary production candidate for this project",
            implementation_status="minimal repository implemented",
            strengths=[
                "single-purpose vector database",
                "simple local Compose path",
                "native collection snapshots",
                "current project already has import, delete, and benchmark CLI",
            ],
            risks=[
                "backup retention is not automated",
                "restore verification is manual",
                "runtime promotion still needs operational smoke tests",
            ],
            required_before_promotion=[
                "run JSON vs Qdrant benchmark with no quality regression",
                "complete snapshot create, restore, and compare smoke test",
                "document retention policy and destructive operation guardrails",
                "verify monitoring, logs, and collection metadata before rollout",
            ],
        ),
    ]

    if include_milvus:
        candidates.append(
            VectorDbCandidate(
                name="milvus",
                role="comparison backend candidate for production vector database learning",
                implementation_status="repository skeleton implemented; runtime benchmark pending",
                strengths=[
                    "designed for larger vector workloads",
                    "broader distributed deployment path",
                    "useful comparison point for production vector database learning",
                ],
                risks=[
                    "heavier local and operational footprint",
                    "more moving parts than this project currently needs",
                    "runtime benchmark and backup path are not validated yet",
                ],
                required_before_promotion=[
                    "add Milvus Compose or standalone local environment",
                    "run repository smoke tests against a real Milvus service",
                    "run the same benchmark used by JSON and Qdrant",
                    "compare operational cost before considering migration",
                ],
            )
        )

    promotion_gates = [
        "quality gate: target backend average retrieval score must not regress against JSON",
        "latency gate: target backend average query latency must be recorded and explained",
        "backup gate: snapshot or rebuild path must be documented and smoke-tested",
        "restore gate: restore into disposable collection before switching traffic",
        "safety gate: destructive commands must require explicit confirmation",
        "observability gate: logs, metrics, and comparison reports must be kept",
        "rollback gate: JSON fallback or previous collection must remain available",
    ]

    recommended_next_steps = _build_recommended_next_steps(
        target_backend=normalized_target,
        include_milvus=include_milvus,
    )

    return VectorDbGovernanceReport(
        current_backend=normalized_current,
        target_backend=normalized_target,
        candidates=candidates,
        promotion_gates=promotion_gates,
        recommended_next_steps=recommended_next_steps,
    )


def render_vector_db_governance_report(
    report: VectorDbGovernanceReport,
) -> str:
    lines = [
        "# Vector DB Governance Report",
        "",
        f"- Current backend: `{report.current_backend}`",
        f"- Target backend: `{report.target_backend}`",
        "",
        "## Candidates",
        "",
    ]

    for candidate in report.candidates:
        lines.extend(
            [
                f"### {candidate.name}",
                "",
                f"- Role: {candidate.role}",
                f"- Implementation status: {candidate.implementation_status}",
                "",
                "Strengths:",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in candidate.strengths)
        lines.extend(["", "Risks:", ""])
        lines.extend(f"- {item}" for item in candidate.risks)
        lines.extend(["", "Required before promotion:", ""])
        lines.extend(f"- {item}" for item in candidate.required_before_promotion)
        lines.append("")

    lines.extend(["## Promotion Gates", ""])
    lines.extend(f"- {item}" for item in report.promotion_gates)

    lines.extend(["", "## Recommended Next Steps", ""])
    lines.extend(f"{index}. {item}" for index, item in enumerate(report.recommended_next_steps, start=1))

    return "\n".join(lines).rstrip() + "\n"


def _build_recommended_next_steps(
    target_backend: str,
    include_milvus: bool,
) -> list[str]:
    if target_backend == "qdrant":
        steps = [
            "run compare-vector-store-backends against a local Qdrant service",
            "create a Qdrant snapshot and download it to a gitignored backup directory",
            "restore the snapshot into a disposable collection",
            "run compare-vector-store-backends against the restored collection",
            "document whether Qdrant can replace JSON as the runtime backend",
        ]
    else:
        steps = [
            "add a local Milvus environment without changing the default backend",
            "run MilvusVectorStoreRepository smoke tests against a real Milvus service",
            "import the same JSON vector store into Milvus",
            "run the same benchmark across JSON, Qdrant, and Milvus",
            "compare quality, latency, operational complexity, and rollback path",
        ]

    if include_milvus and target_backend == "qdrant":
        steps.append(
            "keep Milvus as a later comparison path unless Qdrant fails scale or operations requirements"
        )

    return steps
