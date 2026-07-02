import json
import argparse
from pathlib import Path
from datetime import datetime

from app.logger import setup_logger
from app.mock_defense import run_mock_defense
from app.faithfulness_benchmark_evaluator import (
    evaluate_faithfulness_benchmark,
)
from app.faithfulness_stability_evaluator import (
    evaluate_faithfulness_stability,
)
from app.evaluation_report import (
    build_timestamped_report_path,
    create_evaluation_report,
    save_evaluation_report,
)
from app.evaluation_report_comparator import (
    compare_evaluation_report_files,
    save_evaluation_comparison_markdown,
)
from app.retrieval_evaluator import (
    compare_retrieval_strategies,
    compare_retrievers,
    compare_vector_store_repositories,
    evaluate_retrieval,
    scan_hybrid_weights,
)
from app.vector_store_builder import build_pdf_vector_store
from app.config import (
    AGENT_ROUTING_BENCHMARK_PATH,
    AGENT_TRACE_PATH,
    DATABASE_URL,
    DEEPSEEK_MODEL,
    FAITHFULNESS_BENCHMARK_PATH,
    FEEDBACK_STORE_PATH,
    BENCHMARK_CANDIDATE_DIRECTORY,
    LONG_TERM_MEMORY_PATH,
    MILVUS_COLLECTION,
    MILVUS_BACKUP_DIR,
    MILVUS_METRIC_TYPE,
    MILVUS_TOKEN,
    MILVUS_URI,
    MILVUS_VECTOR_SIZE,
    QDRANT_API_KEY,
    QDRANT_BACKUP_DIR,
    QDRANT_COLLECTION,
    QDRANT_DISTANCE,
    QDRANT_URL,
    QDRANT_VECTOR_SIZE,
    RAG_BENCHMARK_PATH,
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RAG_MIN_CHUNK_SIZE,
    RAG_TOP_K,
    RAG_VECTOR_STORE_PATH,
    STORAGE_BACKEND,
    SUB_AGENT_EXECUTION_TRACE_PATH,
    SUB_AGENT_PLAN_TRACE_PATH,
    VECTOR_STORE_BACKEND,
)
from app.agent_routing_evaluator import evaluate_agent_routing
from app.agent_trace_analyzer import analyze_agent_traces
from app.agent_trace_replayer import (
    compare_agent_trace_records,
    replay_agent_trace,
)
from app.trace_feedback import build_trace_feedback_record
from app.trace_replay import replay_trace_file
from app.session_service import run_agent_session
from app.budget_guard import (
    BudgetExceededError ,
    PreflightBudgetExceededError,
)
from app.long_term_memory import (
    add_training_summary,
    add_weakness,
    build_long_term_memory_context,
    load_long_term_memory,
    prune_long_term_memory,
    save_long_term_memory,
    update_memory_profile,
)
from app.memory_auditor import (
    audit_long_term_memory,
    audit_memory_hits,
    build_memory_context_report,
)
from app.task_service import (
    complete_task_step,
    create_defense_task,
    execute_current_task_step,
    get_defense_task,
    start_next_task_step,
    submit_follow_up_answer,
    submit_task_answer,
)
from app.task_resume import get_resumable_task_status
from app.task_trace_analyzer import analyze_task_trace
from app.task_markdown_exporter import export_task_markdown_report
from app.task_memory_exporter import export_task_to_long_term_memory
from app.task_store import DEFAULT_TASK_DIRECTORY
from app.langgraph_workflow.demo_task import run_demo_task
from app.langgraph_workflow.interrupt_demo import (
    build_interrupt_demo_graph,
    get_interrupt_payload,
    resume_interrupt_demo,
    start_interrupt_demo,
)
from app.langgraph_workflow.checkpointer_demo import run_checkpointer_demo
from app.langgraph_workflow.conditional_demo import run_conditional_demo
from app.langgraph_workflow.persistent_checkpoint_demo import (
    run_persistent_checkpoint_demo,
)
from app.langgraph_workflow.evaluate_rewrite_demo import (
    run_evaluate_rewrite_demo,
)
from app.langgraph_workflow.follow_up_demo import run_follow_up_demo
from app.langgraph_workflow.summary_demo import run_summary_demo
from app.langgraph_workflow.parity_report import (
    build_langgraph_task_parity_report,
)
from app.tool_registry import list_registered_tools
from app.sub_agent_specs import list_sub_agent_specs
from app.sub_agent_permissions import check_sub_agent_tool_permission
from app.sub_agent_plan import create_sub_agent_execution_plan
from app.sub_agent_plan_trace import (
    load_sub_agent_plan_traces,
    save_sub_agent_plan_trace,
    summarize_sub_agent_plan_traces,
)
from app.sub_agent_dry_run import dry_run_sub_agent_tool_call
from app.sub_agent_plan_comparator import compare_sub_agent_plan_records
from app.sub_agent_executor import execute_sub_agent_tool_call
from app.sub_agent_execution_comparator import (
    compare_sub_agent_execution_records,
)
from app.sub_agent_execution_trace import (
    load_sub_agent_execution_traces,
    summarize_sub_agent_execution_traces,
)
from app.local_quality_gate import (
    run_local_quality_gate,
    save_local_quality_gate_markdown,
    save_local_quality_gate_report,
)
from app.server_long_run_preflight import (
    build_server_long_run_preflight,
    render_server_long_run_preflight_report,
)
from app.postgres_migrations import build_postgres_migration_plan
from app.postgres_migration_runner import run_postgres_migrations
from app.postgres_json_importer import import_json_storage_to_repositories
from app.repository_factory import create_repositories
from app.k8s_smoke_plan import (
    build_k8s_smoke_plan,
    render_k8s_smoke_plan,
    render_k8s_smoke_report_template,
)
from app.k8s_smoke_runner import (
    execute_k8s_smoke_plan,
    render_k8s_smoke_run_report,
)
from app.vector_store_io import load_vector_store
from app.vector_store_repository import (
    MilvusVectorStoreRepository,
    QdrantVectorStoreRepository,
)
from app.vector_db_governance import (
    build_vector_db_governance_report,
    render_vector_db_governance_report,
)
from app.qdrant_backup_retention import (
    DEFAULT_QDRANT_BACKUP_PATTERNS,
    build_qdrant_backup_retention_plan,
    execute_qdrant_backup_retention,
    render_qdrant_backup_retention_report,
)
from app.qdrant_snapshot_smoke_plan import (
    build_qdrant_snapshot_smoke_plan,
    render_qdrant_snapshot_smoke_plan,
    render_qdrant_snapshot_smoke_report_template,
)
from app.milvus_backup_restore_plan import (
    build_milvus_backup_restore_plan,
    render_milvus_backup_restore_plan,
    render_milvus_restore_report_template,
)
from app.qdrant_snapshot_client import QdrantSnapshotClient
from app.qdrant_snapshot_cronjob_manifest import (
    render_qdrant_snapshot_cronjob_manifest,
)
from app.qdrant_k8s_cronjob_smoke import (
    execute_qdrant_k8s_cronjob_multi_cycle_observe,
    execute_qdrant_k8s_cronjob_smoke,
    execute_qdrant_k8s_cronjob_schedule_observe,
    render_qdrant_k8s_cronjob_multi_cycle_observe_report,
    render_qdrant_k8s_cronjob_schedule_observe_report,
    render_qdrant_k8s_cronjob_smoke_report,
)
from app.qdrant_snapshot_scheduler import (
    build_qdrant_snapshot_drill_plan,
    build_qdrant_snapshot_schedule_config,
    build_qdrant_snapshot_schedule_install_plan,
    build_qdrant_snapshot_schedule_verification_plan,
    execute_qdrant_snapshot_drill,
    execute_qdrant_snapshot_schedule_install_plan,
    render_qdrant_snapshot_drill_plan,
    render_qdrant_snapshot_drill_report,
    render_qdrant_snapshot_schedule_config,
    render_qdrant_snapshot_schedule_evidence_template,
    render_qdrant_snapshot_schedule_install_execution_report,
    render_qdrant_snapshot_schedule_install_plan,
    render_qdrant_snapshot_schedule_verification_plan,
)
from app.session_store import DEFAULT_SESSION_DIRECTORY
from app.feedback_store import (
    create_feedback_record,
    load_feedback_records,
    save_feedback_record,
    summarize_feedback_records,
)
from app.benchmark_candidate_exporter import (
    build_default_candidate_output_path,
    export_feedback_benchmark_candidates,
)
from app.benchmark_candidate_reviewer import (
    load_candidate_report,
    review_benchmark_candidate,
    save_candidate_report,
    summarize_candidate_review_status,
)
from app.benchmark_draft_exporter import (
    build_default_benchmark_draft_output_path,
    export_accepted_candidates_to_benchmark_draft,
)
from app.benchmark_draft_validator import (
    load_benchmark_draft,
    validate_benchmark_draft,
)
from app.benchmark_draft_converter import (
    export_validated_benchmark_draft,
)
from app.benchmark_draft_converter import (
    export_validated_benchmark_draft,
)


def parse_json_argument(
    value: str,
    argument_name: str,
) -> dict:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{argument_name} 必须是合法 JSON"
        ) from error

    if not isinstance(data, dict):
        raise ValueError(
            f"{argument_name} 必须是 JSON 对象"
        )

    return data


def parse_weight_pairs(value: str) -> list[tuple[float, float]]:
    pairs = []

    for raw_pair in value.split(","):
        raw_pair = raw_pair.strip()

        if not raw_pair:
            continue

        parts = raw_pair.split(":")

        if len(parts) != 2:
            raise ValueError(
                "--weights must use VECTOR:BM25 pairs separated by commas"
            )

        vector_weight = float(parts[0])
        bm25_weight = float(parts[1])
        pairs.append((vector_weight, bm25_weight))

    if not pairs:
        raise ValueError("--weights must contain at least one pair")

    return pairs


def parse_key_value_arguments(
    values: list[str],
) -> dict:
    arguments = {}

    for value in values:
        if "=" not in value:
            raise ValueError(
                "--argument must use KEY=VALUE format"
            )

        key, raw_value = value.split("=", 1)
        key = key.strip()

        if not key:
            raise ValueError("--argument key cannot be empty")

        arguments[key] = raw_value

    return arguments


def create_task_repository_for_cli(directory: str):
    repositories = create_repositories(
        storage_backend=STORAGE_BACKEND,
        database_url=DATABASE_URL,
        task_directory=directory,
    )

    return repositories.task_repository


def create_session_repository_for_cli(directory: str):
    repositories = create_repositories(
        storage_backend=STORAGE_BACKEND,
        database_url=DATABASE_URL,
        session_directory=directory,
    )

    return repositories.session_repository


def create_trace_repository_for_cli(file_path: str):
    repositories = create_repositories(
        storage_backend=STORAGE_BACKEND,
        database_url=DATABASE_URL,
        trace_file_path=file_path,
    )

    return repositories.trace_repository


def save_text_output(path: str, content: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(
        description="Thesis Defense Agent CLI"
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level",
    )

    subparsers = parser.add_subparsers(dest="command")
    
    build_parser = subparsers.add_parser("build-store")
    build_parser.add_argument(
        "--file",
        type=str,
        default="data/thesis.pdf",
        help="PDF file path used to build vector store",
    )
    build_parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        help="Chunk size for text splitting",
        )
    build_parser.add_argument(
        "--overlap",
        type=int,
        default=None,
        help="Chunk overlap for text splitting",
    )
    build_parser.add_argument(
        "--min-chunk-size",
        type=int,
        default=None,
        help="Minimum chunk size to keep",
    )
    build_parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild vector store even if metadata does not match",
    )
    
    evaluate_parser = subparsers.add_parser("evaluate-rag")
    evaluate_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )
    evaluate_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save retrieval evaluation report as JSON",
    )
    evaluate_parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save retrieval evaluation report to data/reports with timestamp",
    )
    evaluate_parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Minimum average score required to pass evaluation",
    )
    evaluate_parser.add_argument(
        "--retriever",
        type=str,
        default="vector",
        choices=["vector", "bm25", "hybrid"],
        help="Retriever used for RAG evaluation",
    )
    evaluate_parser.add_argument(
        "--vector-weight",
        type=float,
        default=0.7,
        help="Vector score weight for hybrid retrieval",
    )
    evaluate_parser.add_argument(
        "--bm25-weight",
        type=float,
        default=0.3,
        help="BM25 score weight for hybrid retrieval",
    )
    evaluate_parser.add_argument(
        "--rerank",
        action="store_true",
        help="Rerank retrieved candidates before scoring",
    )
    evaluate_parser.add_argument(
        "--rerank-candidate-multiplier",
        type=int,
        default=3,
        help="Retrieve top_k times this multiplier before reranking",
    )
    evaluate_parser.add_argument(
        "--model-rerank",
        action="store_true",
        help="Use LLM-based reranker on retrieved candidates",
    )
    evaluate_parser.add_argument(
        "--model-rerank-candidate-multiplier",
        type=int,
        default=3,
        help="Retrieve top_k times this multiplier before model reranking",
    )
    evaluate_parser.add_argument(
        "--rewrite-query",
        action="store_true",
        help="Rewrite benchmark queries before retrieval",
    )
    evaluate_parser.add_argument(
        "--llm-rewrite-query",
        action="store_true",
        help="Use LLM to rewrite benchmark queries before retrieval",
    )
    evaluate_parser.add_argument(
        "--multi-query",
        action="store_true",
        help="Generate multiple search queries before retrieval",
    )

    compare_retrievers_parser = subparsers.add_parser(
        "compare-retrievers",
        help="Compare vector, BM25, and hybrid retrieval on the RAG benchmark",
    )
    compare_retrievers_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )
    compare_retrievers_parser.add_argument(
        "--vector-weight",
        type=float,
        default=0.7,
        help="Vector score weight for hybrid retrieval",
    )
    compare_retrievers_parser.add_argument(
        "--bm25-weight",
        type=float,
        default=0.3,
        help="BM25 score weight for hybrid retrieval",
    )
    compare_retrievers_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save retriever comparison report as JSON",
    )
    compare_retrievers_parser.add_argument(
        "--rerank",
        action="store_true",
        help="Rerank retrieved candidates before scoring",
    )
    compare_retrievers_parser.add_argument(
        "--rerank-candidate-multiplier",
        type=int,
        default=3,
        help="Retrieve top_k times this multiplier before reranking",
    )
    compare_retrievers_parser.add_argument(
        "--model-rerank",
        action="store_true",
        help="Use LLM-based reranker on retrieved candidates",
    )
    compare_retrievers_parser.add_argument(
        "--model-rerank-candidate-multiplier",
        type=int,
        default=3,
        help="Retrieve top_k times this multiplier before model reranking",
    )
    compare_retrievers_parser.add_argument(
        "--rewrite-query",
        action="store_true",
        help="Rewrite benchmark queries before retrieval",
    )
    compare_retrievers_parser.add_argument(
        "--llm-rewrite-query",
        action="store_true",
        help="Use LLM to rewrite benchmark queries before retrieval",
    )
    compare_retrievers_parser.add_argument(
        "--multi-query",
        action="store_true",
        help="Generate multiple search queries before retrieval",
    )

    scan_hybrid_parser = subparsers.add_parser(
        "scan-hybrid-weights",
        help="Scan multiple hybrid retrieval weight pairs",
    )
    scan_hybrid_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )
    scan_hybrid_parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help="Weight pairs like 1:0,0.7:0.3,0.5:0.5",
    )
    scan_hybrid_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save hybrid weight scan report as JSON",
    )
    scan_hybrid_parser.add_argument(
        "--rerank",
        action="store_true",
        help="Rerank retrieved candidates before scoring",
    )
    scan_hybrid_parser.add_argument(
        "--rerank-candidate-multiplier",
        type=int,
        default=3,
        help="Retrieve top_k times this multiplier before reranking",
    )
    scan_hybrid_parser.add_argument(
        "--model-rerank",
        action="store_true",
        help="Use LLM-based reranker on retrieved candidates",
    )
    scan_hybrid_parser.add_argument(
        "--model-rerank-candidate-multiplier",
        type=int,
        default=3,
        help="Retrieve top_k times this multiplier before model reranking",
    )
    scan_hybrid_parser.add_argument(
        "--rewrite-query",
        action="store_true",
        help="Rewrite benchmark queries before retrieval",
    )
    scan_hybrid_parser.add_argument(
        "--llm-rewrite-query",
        action="store_true",
        help="Use LLM to rewrite benchmark queries before retrieval",
    )
    scan_hybrid_parser.add_argument(
        "--multi-query",
        action="store_true",
        help="Generate multiple search queries before retrieval",
    )

    strategy_parser = subparsers.add_parser(
        "compare-retrieval-strategies",
        help="Compare retrieval strategy combinations on the RAG benchmark",
    )
    strategy_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )
    strategy_parser.add_argument(
        "--vector-weight",
        type=float,
        default=0.7,
        help="Vector score weight for hybrid retrieval",
    )
    strategy_parser.add_argument(
        "--bm25-weight",
        type=float,
        default=0.3,
        help="BM25 score weight for hybrid retrieval",
    )
    strategy_parser.add_argument(
        "--rerank-candidate-multiplier",
        type=int,
        default=3,
        help="Retrieve top_k times this multiplier before reranking",
    )
    strategy_parser.add_argument(
        "--model-rerank-candidate-multiplier",
        type=int,
        default=3,
        help="Retrieve top_k times this multiplier before model reranking",
    )
    strategy_parser.add_argument(
        "--include-expensive",
        action="store_true",
        help="Include LLM rewrite and model reranker strategy combinations",
    )
    strategy_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save retrieval strategy comparison report as JSON",
    )
    trace_parser = subparsers.add_parser(
        "analyze-traces",
        help="Analyze Agent JSONL traces",
    )

    trace_parser.add_argument(
        "--file",
        type=str,
        default=AGENT_TRACE_PATH,
        help="Agent trace JSONL file path",
    )
    
    replay_trace_parser = subparsers.add_parser(
        "replay-agent-trace",
        help="Replay one Agent JSONL trace record",
    )
    replay_trace_parser.add_argument(
        "--file",
        type=str,
        default=AGENT_TRACE_PATH,
        help="Agent trace JSONL file path",
    )
    replay_trace_parser.add_argument(
        "--line-number",
        type=int,
        default=None,
        help="Trace line number to replay. Defaults to the latest record.",
    )

    generic_replay_trace_parser = subparsers.add_parser(
        "replay-trace",
        help="Replay and summarize a generic JSONL trace file",
    )
    generic_replay_trace_parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Trace JSONL file path",
    )
    generic_replay_trace_parser.add_argument(
        "--source-type",
        type=str,
        required=True,
        choices=["agent", "sub_agent_plan", "sub_agent_execution"],
        help="Trace source type",
    )

    trace_feedback_parser = subparsers.add_parser(
        "trace-feedback",
        help="Convert trace replay issues into a feedback record",
    )
    trace_feedback_parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Trace JSONL file path",
    )
    trace_feedback_parser.add_argument(
        "--source-type",
        type=str,
        required=True,
        choices=["agent", "sub_agent_plan", "sub_agent_execution"],
        help="Trace source type",
    )
    trace_feedback_parser.add_argument(
        "--source-id",
        type=str,
        default=None,
        help="Feedback source identifier. Defaults to source_type:file.",
    )
    trace_feedback_parser.add_argument(
        "--feedback-file",
        type=str,
        default=FEEDBACK_STORE_PATH,
        help="Feedback JSONL file path",
    )
    
    compare_trace_parser = subparsers.add_parser(
        "compare-agent-traces",
        help="Compare two Agent trace replay records",
    )
    compare_trace_parser.add_argument(
        "--baseline-file",
        type=str,
        required=True,
        help="Baseline Agent trace JSONL file path",
    )
    compare_trace_parser.add_argument(
        "--current-file",
        type=str,
        required=True,
        help="Current Agent trace JSONL file path",
    )
    compare_trace_parser.add_argument(
        "--baseline-line-number",
        type=int,
        default=None,
        help="Baseline trace line number. Defaults to latest record.",
    )
    compare_trace_parser.add_argument(
        "--current-line-number",
        type=int,
        default=None,
        help="Current trace line number. Defaults to latest record.",
    )

    feedback_parser = subparsers.add_parser(
        "record-feedback",
        help="Record user feedback for an Agent output, task, or trace",
    )
    feedback_parser.add_argument(
        "--source-type",
        type=str,
        required=True,
        help="Feedback source type, such as agent_trace or defense_task",
    )
    feedback_parser.add_argument(
        "--source-id",
        type=str,
        required=True,
        help="Source identifier, such as task ID or trace line number",
    )
    feedback_parser.add_argument(
        "--rating",
        type=int,
        required=True,
        help="Feedback rating from 1 to 5",
    )
    feedback_parser.add_argument(
        "--comment",
        type=str,
        required=True,
        help="Human feedback comment",
    )
    feedback_parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Feedback tag. Can be passed multiple times.",
    )
    feedback_parser.add_argument(
        "--metadata",
        type=str,
        default=None,
        help="Optional metadata JSON object",
    )
    feedback_parser.add_argument(
        "--file",
        type=str,
        default=FEEDBACK_STORE_PATH,
        help="Feedback JSONL file path",
    )

    feedback_summary_parser = subparsers.add_parser(
        "summarize-feedback",
        help="Summarize recorded user feedback",
    )
    feedback_summary_parser.add_argument(
        "--file",
        type=str,
        default=FEEDBACK_STORE_PATH,
        help="Feedback JSONL file path",
    )

    feedback_candidate_parser = subparsers.add_parser(
        "export-feedback-candidates",
        help="Export feedback records as benchmark candidate JSON",
    )
    feedback_candidate_parser.add_argument(
        "--feedback-file",
        type=str,
        default=FEEDBACK_STORE_PATH,
        help="Feedback JSONL file path",
    )
    feedback_candidate_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output benchmark candidate JSON path",
    )
    feedback_candidate_parser.add_argument(
        "--max-rating",
        type=int,
        default=2,
        help="Export feedback with rating less than or equal to this value",
    )
    feedback_candidate_parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Export feedback with this tag. Can be passed multiple times.",
    )

    review_candidate_parser = subparsers.add_parser(
        "review-benchmark-candidate",
        help="Mark a benchmark candidate as accepted or rejected",
    )
    review_candidate_parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Benchmark candidate JSON file path",
    )
    review_candidate_parser.add_argument(
        "--candidate-id",
        type=str,
        required=True,
        help="Candidate ID to review",
    )
    review_candidate_parser.add_argument(
        "--status",
        type=str,
        required=True,
        choices=["accepted", "rejected"],
        help="Review status",
    )
    review_candidate_parser.add_argument(
        "--reviewer",
        type=str,
        required=True,
        help="Reviewer name",
    )
    review_candidate_parser.add_argument(
        "--reason",
        type=str,
        required=True,
        help="Review reason",
    )

    summarize_candidate_parser = subparsers.add_parser(
        "summarize-benchmark-candidates",
        help="Summarize benchmark candidate review status",
    )
    summarize_candidate_parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Benchmark candidate JSON file path",
    )

    benchmark_draft_parser = subparsers.add_parser(
        "export-benchmark-draft",
        help="Export accepted benchmark candidates as a benchmark draft JSON",
    )
    benchmark_draft_parser.add_argument(
        "--candidate-file",
        type=str,
        required=True,
        help="Benchmark candidate JSON file path",
    )
    benchmark_draft_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output benchmark draft JSON path",
    )

    validate_draft_parser = subparsers.add_parser(
        "validate-benchmark-draft",
        help="Validate whether benchmark draft fields are complete",
    )
    validate_draft_parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Benchmark draft JSON file path",
    )
    validate_draft_parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with code 1 when draft validation fails",
    )

    export_validated_draft_parser = subparsers.add_parser(
        "export-validated-benchmark-draft",
        help="Convert a validated benchmark draft into benchmark JSON drafts",
    )
    export_validated_draft_parser.add_argument(
        "--draft-file",
        type=str,
        required=True,
        help="Validated benchmark draft JSON file path",
    )
    export_validated_draft_parser.add_argument(
        "--output-directory",
        type=str,
        default=BENCHMARK_CANDIDATE_DIRECTORY,
        help="Directory for generated benchmark draft files",
    )

    routing_parser = subparsers.add_parser(
        "evaluate-agent-routing",
        help="Evaluate Agent tool routing accuracy",
    )
    routing_parser.add_argument(
        "--benchmark",
        type=str,
        default=AGENT_ROUTING_BENCHMARK_PATH,
        help="Agent routing benchmark JSON file path",
    )
    routing_parser.add_argument(
        "--min-accuracy",
        type=float,
        default=None,
        help="Minimum task accuracy required to pass evaluation",
    )
    routing_parser.add_argument(
        "--min-argument-accuracy",
        type=float,
        default=None,
        help="Minimum tool argument accuracy required to pass evaluation",
    )
    routing_parser.add_argument(
        "--min-completion-rate",
        type=float,
        default=None,
        help="Minimum task completion rate required to pass evaluation",
    )
    routing_parser.add_argument(
        "--min-groundedness-score",
        type=float,
        default=None,
        help="Minimum supported claim ratio required to pass evaluation",
    )
    routing_parser.add_argument(
        "--min-grounded-task-rate",
        type=float,
        default=None,
        help="Minimum grounded task rate required to pass evaluation",
    )
    routing_parser.add_argument(
        "--min-faithfulness-score",
        type=float,
        default=None,
        help="Minimum average Faithfulness score",
    )
    routing_parser.add_argument(
        "--min-faithfulness-pass-rate",
        type=float,
        default=None,
        help="Minimum Faithfulness pass rate",
    )

    faithfulness_parser = subparsers.add_parser(
        "evaluate-faithfulness",
        help="Evaluate the Faithfulness Judge",
    )
    faithfulness_parser.add_argument(
        "--benchmark",
        type=str,
        default=FAITHFULNESS_BENCHMARK_PATH,
        help="Faithfulness benchmark JSON file path",
    )
    faithfulness_parser.add_argument(
        "--min-accuracy",
        type=float,
        default=None,
        help="Minimum Judge accuracy required to pass",
    )
    faithfulness_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save the Faithfulness report as JSON",
    )
    faithfulness_parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save a timestamped Faithfulness report",
    )

    stability_parser = subparsers.add_parser(
        "evaluate-faithfulness-stability",
        help="Evaluate Faithfulness Judge stability",
    )
    stability_parser.add_argument(
        "--benchmark",
        type=str,
        default=FAITHFULNESS_BENCHMARK_PATH,
        help="Faithfulness benchmark JSON file path",
    )
    stability_parser.add_argument(
        "--repeat-count",
        type=int,
        default=3,
        help="Number of repeated Judge evaluations",
    )
    stability_parser.add_argument(
        "--min-average-agreement",
        type=float,
        default=None,
        help="Minimum average prediction agreement",
    )
    stability_parser.add_argument(
        "--min-unanimous-rate",
        type=float,
        default=None,
        help="Minimum unanimous prediction rate",
    )
    stability_parser.add_argument(
        "--min-majority-accuracy",
        type=float,
        default=None,
        help="Minimum majority-vote accuracy",
    )
    stability_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save the stability report as JSON",
    )
    stability_parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save a timestamped stability report",
    )

    comparison_parser = subparsers.add_parser(
        "compare-evaluation-reports",
        help="Compare baseline and current evaluation reports",
    )
    comparison_parser.add_argument(
        "--baseline",
        type=str,
        required=True,
        help="Baseline evaluation report path",
    )
    comparison_parser.add_argument(
        "--current",
        type=str,
        required=True,
        help="Current evaluation report path",
    )
    comparison_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save the comparison report as JSON",
    )
    comparison_parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save a timestamped comparison report",
    )
    comparison_parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with code 1 when a regression is detected",
    )
    comparison_parser.add_argument(
        "--metric-tolerance",
        type=float,
        default=0.0,
        help="Allowed drop for aggregate metrics",
    )
    comparison_parser.add_argument(
        "--stability-tolerance",
        type=float,
        default=0.0,
        help="Allowed agreement drop for each stability case",
    )
    comparison_parser.add_argument(
        "--markdown-output",
        type=str,
        default=None,
        help="Path to save a Markdown comparison summary",
    )
    
    chat_parser = subparsers.add_parser(
        "chat",
        help="Run one persistent Agent conversation turn",
    )

    chat_parser.add_argument(
        "--message",
        type=str,
        default=None,
        help="User message sent to the Agent",
    )

    chat_parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="Existing session ID used to resume a conversation",
    )
    
    chat_parser.add_argument(
        "--max-history-turns",
        type=int,
        default=6,
        help="Maximum number of recent conversation turns sent to the LLM",
    )
    
    chat_parser.add_argument(
        "--max-history-characters",
        type=int,
        default=12000,
        help="Maximum number of recent message characters sent to the LLM",
    )
    
    chat_parser.add_argument(
        "--max-run-cost",
        type=float,
        default=None,
        help="Maximum allowed cost for this Agent run",
    )
    
    chat_parser.add_argument(
        "--preflight-max-run-cost",
        type=float,
        default=None,
        help="Maximum estimated cost allowed before calling the LLM",
    )
    chat_parser.add_argument(
        "--disable-memory",
        action="store_true",
        help="Disable long-term memory injection for this chat turn",
    )
    chat_parser.add_argument(
        "--max-memory-weaknesses",
        type=int,
        default=5,
        help="Maximum relevant weaknesses injected into the chat context",
    )
    chat_parser.add_argument(
        "--max-memory-summaries",
        type=int,
        default=3,
        help="Maximum relevant training summaries injected into the chat context",
    )
    chat_parser.add_argument(
        "--disable-session-compaction",
        action="store_true",
        help="Disable session history summary compaction for this chat turn",
    )
    chat_parser.add_argument(
        "--compact-summary-max-characters",
        type=int,
        default=4000,
        help="Maximum characters kept in the session summary",
    )
    
    memory_show_parser = subparsers.add_parser(
        "memory-show",
        help="Show local long-term memory",
    )
    memory_show_parser.add_argument(
        "--path",
        type=str,
        default=LONG_TERM_MEMORY_PATH,
        help="Long-term memory JSON path",
    )
    
    memory_set_profile_parser = subparsers.add_parser(
        "memory-set-profile",
        help="Set one profile field in local long-term memory",
    )
    memory_set_profile_parser.add_argument(
        "--key",
        required=True,
        help="Profile field name",
    )
    memory_set_profile_parser.add_argument(
        "--value",
        required=True,
        help="Profile field value",
    )
    memory_set_profile_parser.add_argument(
        "--path",
        type=str,
        default=LONG_TERM_MEMORY_PATH,
        help="Long-term memory JSON path",
    )
    
    memory_add_weakness_parser = subparsers.add_parser(
        "memory-add-weakness",
        help="Add one weakness to local long-term memory",
    )
    memory_add_weakness_parser.add_argument(
        "--text",
        required=True,
        help="Weakness text",
    )
    memory_add_weakness_parser.add_argument(
        "--task-id",
        type=str,
        default=None,
        help="Optional source task ID",
    )
    memory_add_weakness_parser.add_argument(
        "--path",
        type=str,
        default=LONG_TERM_MEMORY_PATH,
        help="Long-term memory JSON path",
    )
    
    memory_add_summary_parser = subparsers.add_parser(
        "memory-add-summary",
        help="Add one training summary to local long-term memory",
    )
    memory_add_summary_parser.add_argument(
        "--summary",
        required=True,
        help="Training summary text",
    )
    memory_add_summary_parser.add_argument(
        "--task-id",
        type=str,
        default=None,
        help="Optional source task ID",
    )
    memory_add_summary_parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Optional training topic",
    )
    memory_add_summary_parser.add_argument(
        "--path",
        type=str,
        default=LONG_TERM_MEMORY_PATH,
        help="Long-term memory JSON path",
    )
    
    memory_prune_parser = subparsers.add_parser(
        "memory-prune",
        help="Prune local long-term memory by retention limits",
    )
    memory_prune_parser.add_argument(
        "--max-weaknesses",
        type=int,
        default=20,
        help="Maximum weaknesses to keep",
    )
    memory_prune_parser.add_argument(
        "--max-summaries",
        type=int,
        default=10,
        help="Maximum training summaries to keep",
    )
    memory_prune_parser.add_argument(
        "--path",
        type=str,
        default=LONG_TERM_MEMORY_PATH,
        help="Long-term memory JSON path",
    )
    memory_prune_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview prune result without writing memory file",
    )

    memory_audit_parser = subparsers.add_parser(
        "memory-audit",
        help="Audit local long-term memory quality without modifying it",
    )
    memory_audit_parser.add_argument(
        "--path",
        type=str,
        default=LONG_TERM_MEMORY_PATH,
        help="Long-term memory JSON path",
    )

    memory_hit_audit_parser = subparsers.add_parser(
        "memory-hit-audit",
        help="Show which long-term memory items match a query",
    )
    memory_hit_audit_parser.add_argument(
        "--query",
        required=True,
        help="Query used to select memory items",
    )
    memory_hit_audit_parser.add_argument(
        "--max-weaknesses",
        type=int,
        default=5,
        help="Maximum weakness hits to show",
    )
    memory_hit_audit_parser.add_argument(
        "--max-summaries",
        type=int,
        default=3,
        help="Maximum summary hits to show",
    )
    memory_hit_audit_parser.add_argument(
        "--path",
        type=str,
        default=LONG_TERM_MEMORY_PATH,
        help="Long-term memory JSON path",
    )

    memory_context_report_parser = subparsers.add_parser(
        "memory-context-report",
        help="Show final long-term memory context injected into Agent prompts",
    )
    memory_context_report_parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Optional query used to select relevant memory items",
    )
    memory_context_report_parser.add_argument(
        "--max-weaknesses",
        type=int,
        default=5,
        help="Maximum weaknesses included in context",
    )
    memory_context_report_parser.add_argument(
        "--max-summaries",
        type=int,
        default=3,
        help="Maximum summaries included in context",
    )
    memory_context_report_parser.add_argument(
        "--path",
        type=str,
        default=LONG_TERM_MEMORY_PATH,
        help="Long-term memory JSON path",
    )
      
    mock_parser = subparsers.add_parser("mock-defense")
    mock_parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Training topic for this mock defense round",
    )

    create_task_parser = subparsers.add_parser(
        "create-task",
        help="Create a defense workflow task",
    )
    create_task_parser.add_argument(
        "--topic",
        required=True,
        help="Defense task topic",
    )
    create_task_parser.add_argument(
        "--directory",
        type=str,
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Directory used to store defense task JSON files",
    )

    start_task_step_parser = subparsers.add_parser(
        "start-task-step",
        help="Start the next defense task step",
    )
    start_task_step_parser.add_argument(
        "--task-id",
        required=True,
        help="Defense task ID",
    )
    start_task_step_parser.add_argument(
        "--input",
        default="{}",
        help="JSON object used as the next step input",
    )
    start_task_step_parser.add_argument(
        "--directory",
        type=str,
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Directory used to store defense task JSON files",
    )

    complete_task_step_parser = subparsers.add_parser(
        "complete-task-step",
        help="Complete the current defense task step",
    )
    complete_task_step_parser.add_argument(
        "--task-id",
        required=True,
        help="Defense task ID",
    )
    complete_task_step_parser.add_argument(
        "--output",
        default="{}",
        help="JSON object used as the current step output",
    )
    complete_task_step_parser.add_argument(
        "--directory",
        type=str,
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Directory used to store defense task JSON files",
    )

    execute_task_step_parser = subparsers.add_parser(
        "execute-task-step",
        help="Execute the current defense task step",
    )
    execute_task_step_parser.add_argument(
        "--task-id",
        required=True,
        help="Defense task ID",
    )
    execute_task_step_parser.add_argument(
        "--directory",
        type=str,
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Directory used to store defense task JSON files",
    )

    resume_task_parser = subparsers.add_parser(
        "resume-task",
        help="Show how to resume a defense task",
    )
    resume_task_parser.add_argument(
        "--task-id",
        required=True,
        help="Defense task ID",
    )
    resume_task_parser.add_argument(
        "--directory",
        type=str,
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Directory used to store defense task JSON files",
    )

    analyze_task_parser = subparsers.add_parser(
        "analyze-task",
        help="Analyze a defense task trace summary",
    )
    analyze_task_parser.add_argument(
        "--task-id",
        required=True,
        help="Defense task ID",
    )
    analyze_task_parser.add_argument(
        "--directory",
        type=str,
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Directory used to store defense task JSON files",
    )

    submit_task_answer_parser = subparsers.add_parser(
        "submit-task-answer",
        help="Submit a student answer for the current task",
    )
    submit_task_answer_parser.add_argument(
        "--task-id",
        required=True,
        help="Defense task ID",
    )
    submit_task_answer_parser.add_argument(
        "--answer",
        required=True,
        help="Student answer text",
    )
    submit_task_answer_parser.add_argument(
        "--directory",
        type=str,
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Directory used to store defense task JSON files",
    )

    submit_follow_up_answer_parser = subparsers.add_parser(
        "submit-follow-up-answer",
        help="Submit a student follow-up answer for the current task",
    )
    submit_follow_up_answer_parser.add_argument(
        "--task-id",
        required=True,
        help="Defense task ID",
    )
    submit_follow_up_answer_parser.add_argument(
        "--answer",
        required=True,
        help="Student follow-up answer text",
    )
    submit_follow_up_answer_parser.add_argument(
        "--directory",
        type=str,
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Directory used to store defense task JSON files",
    )

    export_task_markdown_parser = subparsers.add_parser(
        "export-task-markdown",
        help="Export a defense task as a Markdown report",
    )
    export_task_markdown_parser.add_argument(
        "--task-id",
        required=True,
        help="Defense task ID",
    )
    export_task_markdown_parser.add_argument(
        "--directory",
        type=str,
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Directory used to store defense task JSON files",
    )
    export_task_markdown_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Markdown output path",
    )

    export_task_memory_parser = subparsers.add_parser(
        "export-task-memory",
        help="Export a completed task summary into long-term memory",
    )
    export_task_memory_parser.add_argument(
        "--task-id",
        required=True,
        help="Defense task ID",
    )
    export_task_memory_parser.add_argument(
        "--directory",
        type=str,
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Directory used to store defense task JSON files",
    )
    export_task_memory_parser.add_argument(
        "--memory-path",
        type=str,
        default=LONG_TERM_MEMORY_PATH,
        help="Long-term memory JSON path",
    )

    show_task_parser = subparsers.add_parser(
        "show-task",
        help="Show defense task status and steps",
    )
    show_task_parser.add_argument(
        "--task-id",
        required=True,
        help="Defense task ID",
    )
    show_task_parser.add_argument(
        "--directory",
        type=str,
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Directory used to store defense task JSON files",
    )

    graph_demo_task_parser = subparsers.add_parser(
        "graph-demo-task",
        help="Run a side-by-side LangGraph demo task",
    )
    graph_demo_task_parser.add_argument(
        "--topic",
        required=True,
        help="Defense topic for the LangGraph demo task",
    )
    graph_demo_task_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )

    graph_interrupt_parser = subparsers.add_parser(
        "graph-interrupt-demo",
        help="Run a LangGraph interrupt/resume demo task",
    )
    graph_interrupt_parser.add_argument(
        "--topic",
        required=True,
        help="Defense topic for the LangGraph interrupt demo",
    )
    graph_interrupt_parser.add_argument(
        "--thread-id",
        default="demo-thread",
        help="LangGraph thread ID used by the checkpointer",
    )
    graph_interrupt_parser.add_argument(
        "--answer",
        default=None,
        help="Optional student answer used to immediately resume the graph",
    )
    graph_interrupt_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )

    graph_checkpointer_parser = subparsers.add_parser(
        "graph-checkpointer-demo",
        help="Inspect LangGraph checkpointer state before and after resume",
    )
    graph_checkpointer_parser.add_argument(
        "--topic",
        required=True,
        help="Defense topic for the LangGraph checkpointer demo",
    )
    graph_checkpointer_parser.add_argument(
        "--thread-id",
        default="checkpoint-demo-thread",
        help="LangGraph thread ID used by the checkpointer",
    )
    graph_checkpointer_parser.add_argument(
        "--answer",
        default=None,
        help="Optional student answer used to resume the graph",
    )
    graph_checkpointer_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )

    graph_persistent_checkpoint_parser = subparsers.add_parser(
        "graph-persistent-checkpoint-demo",
        help="Persist a LangGraph checkpoint snapshot as JSON",
    )
    graph_persistent_checkpoint_parser.add_argument(
        "--topic",
        required=True,
        help="Defense topic for the persistent checkpoint demo",
    )
    graph_persistent_checkpoint_parser.add_argument(
        "--thread-id",
        default="persistent-checkpoint-demo-thread",
        help="LangGraph thread ID used by the checkpointer",
    )
    graph_persistent_checkpoint_parser.add_argument(
        "--answer",
        default=None,
        help="Optional student answer used to resume before saving snapshot",
    )
    graph_persistent_checkpoint_parser.add_argument(
        "--output",
        default="data/langgraph_checkpoints/persistent_checkpoint_demo.json",
        help="JSON file path used to save the checkpoint snapshot",
    )
    graph_persistent_checkpoint_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )

    graph_conditional_parser = subparsers.add_parser(
        "graph-conditional-demo",
        help="Run a LangGraph conditional edge routing demo",
    )
    graph_conditional_parser.add_argument(
        "--topic",
        required=True,
        help="Defense topic for the LangGraph conditional demo",
    )
    graph_conditional_parser.add_argument(
        "--thread-id",
        default="conditional-demo-thread",
        help="LangGraph thread ID used by the checkpointer",
    )
    graph_conditional_parser.add_argument(
        "--answer",
        default=None,
        help="Optional existing answer; skips the interrupt route",
    )
    graph_conditional_parser.add_argument(
        "--resume-answer",
        default=None,
        help="Optional answer used to resume when the graph interrupts",
    )
    graph_conditional_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )

    graph_evaluate_rewrite_parser = subparsers.add_parser(
        "graph-evaluate-rewrite-demo",
        help="Run a LangGraph demo through evaluate and rewrite nodes",
    )
    graph_evaluate_rewrite_parser.add_argument(
        "--topic",
        required=True,
        help="Defense topic for the LangGraph evaluate/rewrite demo",
    )
    graph_evaluate_rewrite_parser.add_argument(
        "--thread-id",
        default="evaluate-rewrite-demo-thread",
        help="LangGraph thread ID used by the checkpointer",
    )
    graph_evaluate_rewrite_parser.add_argument(
        "--answer",
        default=None,
        help="Optional student answer used to resume and finish the graph",
    )
    graph_evaluate_rewrite_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )

    graph_follow_up_parser = subparsers.add_parser(
        "graph-follow-up-demo",
        help="Run a LangGraph demo through follow-up evaluation",
    )
    graph_follow_up_parser.add_argument(
        "--topic",
        required=True,
        help="Defense topic for the LangGraph follow-up demo",
    )
    graph_follow_up_parser.add_argument(
        "--thread-id",
        default="follow-up-demo-thread",
        help="LangGraph thread ID used by the checkpointer",
    )
    graph_follow_up_parser.add_argument(
        "--answer",
        default=None,
        help="Optional student answer used to reach follow-up interrupt",
    )
    graph_follow_up_parser.add_argument(
        "--follow-up-answer",
        default=None,
        help="Optional student answer to the generated follow-up question",
    )
    graph_follow_up_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )

    graph_summary_parser = subparsers.add_parser(
        "graph-summary-demo",
        help="Run a LangGraph demo through full training summary",
    )
    graph_summary_parser.add_argument(
        "--topic",
        required=True,
        help="Defense topic for the LangGraph summary demo",
    )
    graph_summary_parser.add_argument(
        "--thread-id",
        default="summary-demo-thread",
        help="LangGraph thread ID used by the checkpointer",
    )
    graph_summary_parser.add_argument(
        "--answer",
        default=None,
        help="Optional student answer used to reach follow-up interrupt",
    )
    graph_summary_parser.add_argument(
        "--follow-up-answer",
        default=None,
        help="Optional student answer to the generated follow-up question",
    )
    graph_summary_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )

    subparsers.add_parser(
        "graph-task-parity",
        help="Compare LangGraph sidecar steps with the Task workflow contract",
    )

    list_tools_parser = subparsers.add_parser(
        "list-tools",
        help="List registered Agent tools and governance metadata",
    )
    list_tools_parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Also show disabled tools",
    )

    subparsers.add_parser(
        "list-sub-agents",
        help="List local Sub-Agent specs without running them",
    )

    check_sub_agent_tool_parser = subparsers.add_parser(
        "check-sub-agent-tool",
        help="Check whether a Sub-Agent is allowed to use a tool",
    )
    check_sub_agent_tool_parser.add_argument(
        "--sub-agent",
        required=True,
        help="Sub-Agent name",
    )
    check_sub_agent_tool_parser.add_argument(
        "--tool",
        required=True,
        help="Tool name",
    )

    plan_sub_agent_call_parser = subparsers.add_parser(
        "plan-sub-agent-call",
        help="Create a local Sub-Agent tool-call plan without executing it",
    )
    plan_sub_agent_call_parser.add_argument(
        "--sub-agent",
        required=True,
        help="Sub-Agent name",
    )
    plan_sub_agent_call_parser.add_argument(
        "--tool",
        required=True,
        help="Tool name",
    )
    plan_sub_agent_call_parser.add_argument(
        "--arguments",
        default=None,
        help="Tool arguments as a JSON object",
    )
    plan_sub_agent_call_parser.add_argument(
        "--argument",
        action="append",
        default=[],
        help=(
            "Tool argument in KEY=VALUE format. "
            "Can be passed multiple times."
        ),
    )
    plan_sub_agent_call_parser.add_argument(
        "--save-trace",
        action="store_true",
        help="Save the generated plan to a JSONL audit trace",
    )
    plan_sub_agent_call_parser.add_argument(
        "--trace-file",
        default=SUB_AGENT_PLAN_TRACE_PATH,
        help="Sub-Agent plan trace JSONL file path",
    )

    analyze_sub_agent_plans_parser = subparsers.add_parser(
        "analyze-sub-agent-plans",
        help="Analyze saved Sub-Agent plan trace records",
    )
    analyze_sub_agent_plans_parser.add_argument(
        "--file",
        default=SUB_AGENT_PLAN_TRACE_PATH,
        help="Sub-Agent plan trace JSONL file path",
    )

    compare_sub_agent_plans_parser = subparsers.add_parser(
        "compare-sub-agent-plans",
        help="Compare two Sub-Agent plan trace JSONL files",
    )
    compare_sub_agent_plans_parser.add_argument(
        "--baseline",
        required=True,
        help="Baseline Sub-Agent plan trace JSONL file",
    )
    compare_sub_agent_plans_parser.add_argument(
        "--candidate",
        required=True,
        help="Candidate Sub-Agent plan trace JSONL file",
    )

    dry_run_sub_agent_call_parser = subparsers.add_parser(
        "dry-run-sub-agent-call",
        help="Create and audit a Sub-Agent plan without executing the tool",
    )
    dry_run_sub_agent_call_parser.add_argument(
        "--sub-agent",
        required=True,
        help="Sub-Agent name",
    )
    dry_run_sub_agent_call_parser.add_argument(
        "--tool",
        required=True,
        help="Tool name",
    )
    dry_run_sub_agent_call_parser.add_argument(
        "--arguments",
        default=None,
        help="Tool arguments as a JSON object",
    )
    dry_run_sub_agent_call_parser.add_argument(
        "--argument",
        action="append",
        default=[],
        help=(
            "Tool argument in KEY=VALUE format. "
            "Can be passed multiple times."
        ),
    )
    dry_run_sub_agent_call_parser.add_argument(
        "--save-trace",
        action="store_true",
        help="Save the generated dry-run plan to a JSONL audit trace",
    )
    dry_run_sub_agent_call_parser.add_argument(
        "--trace-file",
        default=SUB_AGENT_PLAN_TRACE_PATH,
        help="Sub-Agent plan trace JSONL file path",
    )

    execute_sub_agent_call_parser = subparsers.add_parser(
        "execute-sub-agent-call",
        help="Execute one allowed Sub-Agent tool call",
    )
    execute_sub_agent_call_parser.add_argument(
        "--sub-agent",
        required=True,
        help="Sub-Agent name",
    )
    execute_sub_agent_call_parser.add_argument(
        "--tool",
        required=True,
        help="Tool name",
    )
    execute_sub_agent_call_parser.add_argument(
        "--arguments",
        default=None,
        help="Tool arguments as a JSON object",
    )
    execute_sub_agent_call_parser.add_argument(
        "--argument",
        action="append",
        default=[],
        help=(
            "Tool argument in KEY=VALUE format. "
            "Can be passed multiple times."
        ),
    )
    execute_sub_agent_call_parser.add_argument(
        "--save-trace",
        action="store_true",
        help="Save the execution result to a JSONL audit trace",
    )
    execute_sub_agent_call_parser.add_argument(
        "--trace-file",
        default=SUB_AGENT_EXECUTION_TRACE_PATH,
        help="Sub-Agent execution trace JSONL file path",
    )

    analyze_sub_agent_executions_parser = subparsers.add_parser(
        "analyze-sub-agent-executions",
        help="Analyze saved Sub-Agent execution trace records",
    )
    analyze_sub_agent_executions_parser.add_argument(
        "--file",
        default=SUB_AGENT_EXECUTION_TRACE_PATH,
        help="Sub-Agent execution trace JSONL file path",
    )

    compare_sub_agent_executions_parser = subparsers.add_parser(
        "compare-sub-agent-executions",
        help="Compare two Sub-Agent execution trace JSONL files",
    )
    compare_sub_agent_executions_parser.add_argument(
        "--baseline",
        required=True,
        help="Baseline Sub-Agent execution trace JSONL file",
    )
    compare_sub_agent_executions_parser.add_argument(
        "--candidate",
        required=True,
        help="Candidate Sub-Agent execution trace JSONL file",
    )
    compare_sub_agent_executions_parser.add_argument(
        "--max-duration-ratio",
        type=float,
        default=2.0,
        help="Maximum allowed candidate/baseline duration ratio",
    )
    compare_sub_agent_executions_parser.add_argument(
        "--allow-fail",
        action="store_true",
        help=(
            "Print the comparison report without failing the command "
            "when regressions are detected"
        ),
    )

    local_quality_gate_parser = subparsers.add_parser(
        "local-quality-gate",
        help="Run local offline quality gate checks",
    )
    local_quality_gate_parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Skip the pytest check",
    )
    local_quality_gate_parser.add_argument(
        "--sub-agent-execution-baseline",
        default=None,
        help="Baseline Sub-Agent execution trace JSONL file",
    )
    local_quality_gate_parser.add_argument(
        "--sub-agent-execution-candidate",
        default=None,
        help="Candidate Sub-Agent execution trace JSONL file",
    )
    local_quality_gate_parser.add_argument(
        "--max-duration-ratio",
        type=float,
        default=2.0,
        help="Maximum allowed candidate/baseline duration ratio",
    )
    local_quality_gate_parser.add_argument(
        "--allow-fail",
        action="store_true",
        help="Print the gate report without failing the command",
    )
    local_quality_gate_parser.add_argument(
        "--output",
        default=None,
        help="Optional JSON output path for the quality gate report",
    )
    local_quality_gate_parser.add_argument(
        "--markdown-output",
        default=None,
        help="Optional Markdown output path for the quality gate report",
    )

    server_long_run_preflight_parser = subparsers.add_parser(
        "server-long-run-preflight",
        help="Generate a server long-run preflight checklist and evidence index",
    )
    server_long_run_preflight_parser.add_argument(
        "--environment",
        default="server",
        help="Target environment label used in the report",
    )
    server_long_run_preflight_parser.add_argument(
        "--runtime",
        default="docker_compose",
        choices=["docker_compose", "kubernetes"],
        help="Target runtime checklist to render",
    )
    server_long_run_preflight_parser.add_argument(
        "--operator",
        default="operator",
        help="Operator name or role recorded in the report",
    )
    server_long_run_preflight_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the preflight report",
    )

    k8s_smoke_plan_parser = subparsers.add_parser(
        "k8s-smoke-plan",
        help="Print a Kubernetes smoke-test plan without applying manifests",
    )
    k8s_smoke_plan_parser.add_argument(
        "--namespace",
        default="thesis-defense-agent",
        help="Kubernetes namespace used by the manifests",
    )
    k8s_smoke_plan_parser.add_argument(
        "--kustomize-dir",
        default="k8s/base",
        help="Kustomize directory to render and apply",
    )
    k8s_smoke_plan_parser.add_argument(
        "--api-local-port",
        type=int,
        default=18000,
        help="Local port used in the API port-forward smoke test",
    )
    k8s_smoke_plan_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the smoke-test plan",
    )

    k8s_smoke_report_template_parser = subparsers.add_parser(
        "k8s-smoke-report-template",
        help="Print a Kubernetes smoke-test execution report template",
    )
    k8s_smoke_report_template_parser.add_argument(
        "--namespace",
        default="thesis-defense-agent",
        help="Kubernetes namespace used by the manifests",
    )
    k8s_smoke_report_template_parser.add_argument(
        "--kustomize-dir",
        default="k8s/base",
        help="Kustomize directory to render and apply",
    )
    k8s_smoke_report_template_parser.add_argument(
        "--api-local-port",
        type=int,
        default=18000,
        help="Local port used in the API port-forward smoke test",
    )
    k8s_smoke_report_template_parser.add_argument(
        "--environment",
        default="local-cluster",
        help="Environment label written into the smoke-test report",
    )
    k8s_smoke_report_template_parser.add_argument(
        "--operator",
        default="",
        help="Operator name written into the smoke-test report",
    )
    k8s_smoke_report_template_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the smoke-test report template",
    )

    k8s_smoke_run_parser = subparsers.add_parser(
        "k8s-smoke-run",
        help="Run Kubernetes smoke-test steps and print an execution report",
    )
    k8s_smoke_run_parser.add_argument(
        "--namespace",
        default="thesis-defense-agent",
        help="Kubernetes namespace used by the manifests",
    )
    k8s_smoke_run_parser.add_argument(
        "--kustomize-dir",
        default="k8s/base",
        help="Kustomize directory to render and apply",
    )
    k8s_smoke_run_parser.add_argument(
        "--api-local-port",
        type=int,
        default=18000,
        help="Local port used in the API port-forward smoke test",
    )
    k8s_smoke_run_parser.add_argument(
        "--apply-cluster",
        action="store_true",
        help="Run cluster-mutating steps such as kubectl apply",
    )
    k8s_smoke_run_parser.add_argument(
        "--include-port-forward",
        action="store_true",
        help="Run port-forward and local health-check steps",
    )
    k8s_smoke_run_parser.add_argument(
        "--include-rollback",
        action="store_true",
        help="Run the rollback step; skipped by default",
    )
    k8s_smoke_run_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="Maximum seconds allowed for each command",
    )
    k8s_smoke_run_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the smoke-test run report",
    )
    k8s_smoke_run_parser.add_argument(
        "--allow-fail",
        action="store_true",
        help="Do not exit non-zero when one or more smoke steps fail",
    )

    postgres_migrations_parser = subparsers.add_parser(
        "postgres-migrations",
        help="Show PostgreSQL migration files without executing them",
    )
    postgres_migrations_parser.add_argument(
        "--directory",
        default=None,
        help="Optional PostgreSQL migration directory",
    )

    run_postgres_migrations_parser = subparsers.add_parser(
        "run-postgres-migrations",
        help="Apply pending PostgreSQL migrations",
    )
    run_postgres_migrations_parser.add_argument(
        "--database-url",
        default=None,
        help=(
            "PostgreSQL connection URL. Defaults to DATABASE_URL from the "
            "environment."
        ),
    )
    run_postgres_migrations_parser.add_argument(
        "--directory",
        default=None,
        help="Optional PostgreSQL migration directory",
    )

    show_repositories_parser = subparsers.add_parser(
        "show-repositories",
        help="Show selected repository implementations without connecting",
    )
    show_repositories_parser.add_argument(
        "--storage-backend",
        default=STORAGE_BACKEND,
        help="Storage backend to inspect: json or postgres",
    )
    show_repositories_parser.add_argument(
        "--database-url",
        default=None,
        help=(
            "PostgreSQL connection URL. Defaults to DATABASE_URL from the "
            "environment. The value is not printed."
        ),
    )

    import_vector_store_to_qdrant_parser = subparsers.add_parser(
        "import-vector-store-to-qdrant",
        help="Import local JSON vector store items into Qdrant",
    )
    import_vector_store_to_qdrant_parser.add_argument(
        "--source",
        default=RAG_VECTOR_STORE_PATH,
        help="Local JSON vector store path",
    )
    import_vector_store_to_qdrant_parser.add_argument(
        "--url",
        default=QDRANT_URL,
        help="Qdrant URL",
    )
    import_vector_store_to_qdrant_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Qdrant collection name",
    )
    import_vector_store_to_qdrant_parser.add_argument(
        "--vector-size",
        type=int,
        default=QDRANT_VECTOR_SIZE,
        help="Qdrant vector size",
    )
    import_vector_store_to_qdrant_parser.add_argument(
        "--distance",
        default=QDRANT_DISTANCE,
        help="Qdrant distance metric",
    )
    import_vector_store_to_qdrant_parser.add_argument(
        "--api-key",
        default=None,
        help="Optional Qdrant API key. Defaults to QDRANT_API_KEY.",
    )

    import_vector_store_to_milvus_parser = subparsers.add_parser(
        "import-vector-store-to-milvus",
        help="Import local JSON vector store items into Milvus",
    )
    import_vector_store_to_milvus_parser.add_argument(
        "--source",
        default=RAG_VECTOR_STORE_PATH,
        help="Local JSON vector store path",
    )
    import_vector_store_to_milvus_parser.add_argument(
        "--uri",
        default=MILVUS_URI,
        help="Milvus URI",
    )
    import_vector_store_to_milvus_parser.add_argument(
        "--collection",
        default=MILVUS_COLLECTION,
        help="Milvus collection name",
    )
    import_vector_store_to_milvus_parser.add_argument(
        "--vector-size",
        type=int,
        default=MILVUS_VECTOR_SIZE,
        help="Milvus vector size",
    )
    import_vector_store_to_milvus_parser.add_argument(
        "--metric-type",
        default=MILVUS_METRIC_TYPE,
        help="Milvus metric type",
    )
    import_vector_store_to_milvus_parser.add_argument(
        "--token",
        default=None,
        help="Optional Milvus token. Defaults to MILVUS_TOKEN.",
    )

    milvus_backup_restore_plan_parser = subparsers.add_parser(
        "milvus-backup-restore-plan",
        help="Generate a Milvus backup and restore smoke-test plan",
    )
    milvus_backup_restore_plan_parser.add_argument(
        "--uri",
        default=MILVUS_URI,
        help="Milvus URI",
    )
    milvus_backup_restore_plan_parser.add_argument(
        "--collection",
        default=MILVUS_COLLECTION,
        help="Source Milvus collection name",
    )
    milvus_backup_restore_plan_parser.add_argument(
        "--restore-collection",
        default=f"{MILVUS_COLLECTION}_restore",
        help="Disposable Milvus collection name used for restore smoke tests",
    )
    milvus_backup_restore_plan_parser.add_argument(
        "--source",
        default=RAG_VECTOR_STORE_PATH,
        help="Local JSON vector store baseline path",
    )
    milvus_backup_restore_plan_parser.add_argument(
        "--backup-dir",
        default=MILVUS_BACKUP_DIR,
        help="Local backup directory for Milvus backup artifacts",
    )
    milvus_backup_restore_plan_parser.add_argument(
        "--vector-size",
        type=int,
        default=MILVUS_VECTOR_SIZE,
        help="Milvus vector size",
    )
    milvus_backup_restore_plan_parser.add_argument(
        "--metric-type",
        default=MILVUS_METRIC_TYPE,
        help="Milvus metric type",
    )
    milvus_backup_restore_plan_parser.add_argument(
        "--volume-name",
        default="thesis-defense-agent_milvus_data",
        help="Docker volume name used by the local Milvus standalone service",
    )
    milvus_backup_restore_plan_parser.add_argument(
        "--backup-file-name",
        default="milvus_data_backup.tar.gz",
        help="File name used in the optional local volume backup command",
    )
    milvus_backup_restore_plan_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the Milvus backup/restore plan",
    )

    milvus_restore_report_parser = subparsers.add_parser(
        "milvus-restore-report-template",
        help="Generate a Milvus backup and restore execution report template",
    )
    milvus_restore_report_parser.add_argument(
        "--uri",
        default=MILVUS_URI,
        help="Milvus URI",
    )
    milvus_restore_report_parser.add_argument(
        "--collection",
        default=MILVUS_COLLECTION,
        help="Source Milvus collection name",
    )
    milvus_restore_report_parser.add_argument(
        "--restore-collection",
        default=f"{MILVUS_COLLECTION}_restore",
        help="Disposable Milvus collection name used for restore smoke tests",
    )
    milvus_restore_report_parser.add_argument(
        "--source",
        default=RAG_VECTOR_STORE_PATH,
        help="Local JSON vector store baseline path",
    )
    milvus_restore_report_parser.add_argument(
        "--backup-dir",
        default=MILVUS_BACKUP_DIR,
        help="Local backup directory for Milvus backup artifacts",
    )
    milvus_restore_report_parser.add_argument(
        "--vector-size",
        type=int,
        default=MILVUS_VECTOR_SIZE,
        help="Milvus vector size",
    )
    milvus_restore_report_parser.add_argument(
        "--metric-type",
        default=MILVUS_METRIC_TYPE,
        help="Milvus metric type",
    )
    milvus_restore_report_parser.add_argument(
        "--volume-name",
        default="thesis-defense-agent_milvus_data",
        help="Docker volume name used by the local Milvus standalone service",
    )
    milvus_restore_report_parser.add_argument(
        "--backup-file-name",
        default="milvus_data_backup.tar.gz",
        help="File name used in the optional local volume backup command",
    )
    milvus_restore_report_parser.add_argument(
        "--environment",
        default="local-milvus",
        help="Environment label written into the restore report",
    )
    milvus_restore_report_parser.add_argument(
        "--operator",
        default="",
        help="Operator name written into the restore report",
    )
    milvus_restore_report_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the Milvus restore report template",
    )

    compare_vector_store_backends_parser = subparsers.add_parser(
        "compare-vector-store-backends",
        help="Compare local JSON vector store search with Qdrant search",
    )
    compare_vector_store_backends_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve",
    )
    compare_vector_store_backends_parser.add_argument(
        "--source",
        default=RAG_VECTOR_STORE_PATH,
        help="Local JSON vector store path",
    )
    compare_vector_store_backends_parser.add_argument(
        "--url",
        default=QDRANT_URL,
        help="Qdrant URL",
    )
    compare_vector_store_backends_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Qdrant collection name",
    )
    compare_vector_store_backends_parser.add_argument(
        "--vector-size",
        type=int,
        default=QDRANT_VECTOR_SIZE,
        help="Qdrant vector size",
    )
    compare_vector_store_backends_parser.add_argument(
        "--distance",
        default=QDRANT_DISTANCE,
        help="Qdrant distance metric",
    )
    compare_vector_store_backends_parser.add_argument(
        "--api-key",
        default=None,
        help="Optional Qdrant API key. Defaults to QDRANT_API_KEY.",
    )
    compare_vector_store_backends_parser.add_argument(
        "--include-milvus",
        action="store_true",
        help="Also include Milvus in the backend comparison",
    )
    compare_vector_store_backends_parser.add_argument(
        "--milvus-uri",
        default=MILVUS_URI,
        help="Milvus URI",
    )
    compare_vector_store_backends_parser.add_argument(
        "--milvus-collection",
        default=MILVUS_COLLECTION,
        help="Milvus collection name",
    )
    compare_vector_store_backends_parser.add_argument(
        "--milvus-vector-size",
        type=int,
        default=MILVUS_VECTOR_SIZE,
        help="Milvus vector size",
    )
    compare_vector_store_backends_parser.add_argument(
        "--milvus-metric-type",
        default=MILVUS_METRIC_TYPE,
        help="Milvus metric type",
    )
    compare_vector_store_backends_parser.add_argument(
        "--milvus-token",
        default=None,
        help="Optional Milvus token. Defaults to MILVUS_TOKEN.",
    )
    compare_vector_store_backends_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save backend comparison report as JSON",
    )

    delete_qdrant_collection_parser = subparsers.add_parser(
        "delete-qdrant-collection",
        help="Delete a Qdrant collection with explicit confirmation",
    )
    delete_qdrant_collection_parser.add_argument(
        "--url",
        default=QDRANT_URL,
        help="Qdrant URL",
    )
    delete_qdrant_collection_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Qdrant collection name",
    )
    delete_qdrant_collection_parser.add_argument(
        "--vector-size",
        type=int,
        default=QDRANT_VECTOR_SIZE,
        help="Qdrant vector size",
    )
    delete_qdrant_collection_parser.add_argument(
        "--distance",
        default=QDRANT_DISTANCE,
        help="Qdrant distance metric",
    )
    delete_qdrant_collection_parser.add_argument(
        "--api-key",
        default=None,
        help="Optional Qdrant API key. Defaults to QDRANT_API_KEY.",
    )
    delete_qdrant_collection_parser.add_argument(
        "--confirm-collection",
        required=True,
        help=(
            "Required destructive confirmation. Must exactly match "
            "--collection."
        ),
    )

    delete_milvus_collection_parser = subparsers.add_parser(
        "delete-milvus-collection",
        help="Delete a Milvus collection with explicit confirmation",
    )
    delete_milvus_collection_parser.add_argument(
        "--uri",
        default=MILVUS_URI,
        help="Milvus URI",
    )
    delete_milvus_collection_parser.add_argument(
        "--collection",
        default=MILVUS_COLLECTION,
        help="Milvus collection name",
    )
    delete_milvus_collection_parser.add_argument(
        "--vector-size",
        type=int,
        default=MILVUS_VECTOR_SIZE,
        help="Milvus vector size",
    )
    delete_milvus_collection_parser.add_argument(
        "--metric-type",
        default=MILVUS_METRIC_TYPE,
        help="Milvus metric type",
    )
    delete_milvus_collection_parser.add_argument(
        "--token",
        default=None,
        help="Optional Milvus token. Defaults to MILVUS_TOKEN.",
    )
    delete_milvus_collection_parser.add_argument(
        "--confirm-collection",
        required=True,
        help=(
            "Required destructive confirmation. Must exactly match "
            "--collection."
        ),
    )

    vector_db_governance_parser = subparsers.add_parser(
        "vector-db-governance-report",
        help="Generate an offline vector database governance and comparison report",
    )
    vector_db_governance_parser.add_argument(
        "--current-backend",
        default=VECTOR_STORE_BACKEND,
        help="Current vector store backend, usually json or qdrant",
    )
    vector_db_governance_parser.add_argument(
        "--target-backend",
        default="qdrant",
        choices=["qdrant", "milvus"],
        help="Target backend to evaluate for promotion",
    )
    vector_db_governance_parser.add_argument(
        "--exclude-milvus",
        action="store_true",
        help="Exclude Milvus from the comparison section",
    )
    vector_db_governance_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the governance report",
    )

    qdrant_backup_retention_parser = subparsers.add_parser(
        "qdrant-backup-retention",
        help="Apply or preview local Qdrant backup retention policy",
    )
    qdrant_backup_retention_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Directory containing downloaded Qdrant snapshot files",
    )
    qdrant_backup_retention_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_backup_retention_parser.add_argument(
        "--pattern",
        action="append",
        default=None,
        help=(
            "Backup filename glob pattern. Can be repeated. "
            f"Default: {', '.join(DEFAULT_QDRANT_BACKUP_PATTERNS)}"
        ),
    )
    qdrant_backup_retention_parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete old backups. Without this flag the command is dry-run.",
    )
    qdrant_backup_retention_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the retention report",
    )

    qdrant_snapshot_smoke_plan_parser = subparsers.add_parser(
        "qdrant-snapshot-smoke-plan",
        help="Generate a Qdrant snapshot create/restore smoke-test plan",
    )
    qdrant_snapshot_smoke_plan_parser.add_argument(
        "--url",
        default=QDRANT_URL,
        help="Qdrant URL",
    )
    qdrant_snapshot_smoke_plan_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_snapshot_smoke_plan_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore smoke tests",
    )
    qdrant_snapshot_smoke_plan_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Local backup directory for downloaded snapshots",
    )
    qdrant_snapshot_smoke_plan_parser.add_argument(
        "--snapshot-name",
        default="<snapshot_name>",
        help="Snapshot name placeholder used in generated commands",
    )
    qdrant_snapshot_smoke_plan_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the snapshot smoke plan",
    )

    qdrant_snapshot_smoke_report_parser = subparsers.add_parser(
        "qdrant-snapshot-smoke-report-template",
        help="Generate a Qdrant snapshot smoke-test execution report template",
    )
    qdrant_snapshot_smoke_report_parser.add_argument(
        "--url",
        default=QDRANT_URL,
        help="Qdrant URL",
    )
    qdrant_snapshot_smoke_report_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_snapshot_smoke_report_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore smoke tests",
    )
    qdrant_snapshot_smoke_report_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Local backup directory for downloaded snapshots",
    )
    qdrant_snapshot_smoke_report_parser.add_argument(
        "--snapshot-name",
        default="<snapshot_name>",
        help="Snapshot name placeholder used in generated commands",
    )
    qdrant_snapshot_smoke_report_parser.add_argument(
        "--environment",
        default="local-qdrant",
        help="Environment label written into the smoke report",
    )
    qdrant_snapshot_smoke_report_parser.add_argument(
        "--operator",
        default="",
        help="Operator name written into the smoke report",
    )
    qdrant_snapshot_smoke_report_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the snapshot smoke report template",
    )

    qdrant_snapshot_drill_plan_parser = subparsers.add_parser(
        "qdrant-snapshot-drill-plan",
        help="Generate a scheduled Qdrant snapshot drill plan",
    )
    qdrant_snapshot_drill_plan_parser.add_argument(
        "--url",
        default=QDRANT_URL,
        help="Qdrant URL",
    )
    qdrant_snapshot_drill_plan_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_snapshot_drill_plan_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore drills",
    )
    qdrant_snapshot_drill_plan_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Local backup directory for downloaded snapshots",
    )
    qdrant_snapshot_drill_plan_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_snapshot_drill_plan_parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Plan retention as an apply step instead of dry-run preview",
    )
    qdrant_snapshot_drill_plan_parser.add_argument(
        "--skip-restore-drill",
        action="store_true",
        help="Do not include restore and restored-collection comparison steps",
    )
    qdrant_snapshot_drill_plan_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the snapshot drill plan",
    )

    qdrant_snapshot_drill_run_parser = subparsers.add_parser(
        "qdrant-snapshot-drill-run",
        help="Run a one-time Qdrant snapshot drill",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--url",
        default=QDRANT_URL,
        help="Qdrant URL",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore drills",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--confirm-restore-collection",
        default=None,
        help=(
            "Required when restore drill is enabled. "
            "Must exactly match --restore-collection."
        ),
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Local backup directory for downloaded snapshots",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Actually delete old local backup files during retention",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--skip-restore-drill",
        action="store_true",
        help="Do not restore into the disposable collection",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--skip-compare",
        action="store_true",
        help="Do not compare the restored collection against the JSON baseline",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--source",
        default=RAG_VECTOR_STORE_PATH,
        help="Local JSON vector store path used for comparison",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve during comparison",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--vector-size",
        type=int,
        default=QDRANT_VECTOR_SIZE,
        help="Qdrant vector size used during comparison",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--distance",
        default=QDRANT_DISTANCE,
        help="Qdrant distance metric used during comparison",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--api-key",
        default=None,
        help="Optional Qdrant API key. Defaults to QDRANT_API_KEY.",
    )
    qdrant_snapshot_drill_run_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the snapshot drill report",
    )

    qdrant_snapshot_schedule_config_parser = subparsers.add_parser(
        "qdrant-snapshot-schedule-config",
        help="Generate schedule config previews for the Qdrant snapshot drill runner",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--platform",
        default="all",
        help="Schedule platform config to render",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--task-name",
        default="thesis-defense-qdrant-snapshot-drill",
        help="Schedule task name",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--cron-schedule",
        default="0 3 * * *",
        help="Five-field cron schedule",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--windows-start-time",
        default="03:00",
        help="Windows Task Scheduler start time in HH:MM format",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--working-directory",
        default=".",
        help="Project working directory used by local schedulers",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--log-path",
        default="data/reports/qdrant_snapshot_drill_scheduled.log",
        help="Local log path used by generated scheduler snippets",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace used by generated CronJob preview",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--image",
        default="ghcr.io/buan496/thesis-defense-agent:latest",
        help="Container image used by generated Kubernetes CronJob preview",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore drills",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Local backup directory for downloaded snapshots",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Configure retention as an apply step instead of dry-run preview",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--skip-restore-drill",
        action="store_true",
        help="Do not include restore in the scheduled runner command",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--skip-compare",
        action="store_true",
        help="Do not include restored-collection comparison in the runner command",
    )
    qdrant_snapshot_schedule_config_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the schedule config preview",
    )

    qdrant_snapshot_cronjob_manifest_parser = subparsers.add_parser(
        "qdrant-snapshot-cronjob-manifest",
        help="Render a Kubernetes CronJob manifest for the Qdrant snapshot drill runner",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--task-name",
        default="thesis-defense-qdrant-snapshot-drill",
        help="CronJob name",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--cron-schedule",
        default="0 3 * * *",
        help="Five-field cron schedule",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace used by the generated CronJob",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--image",
        default="ghcr.io/buan496/thesis-defense-agent:latest",
        help="Container image used by the generated CronJob",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--config-map-name",
        default="thesis-defense-agent-api-config",
        help="ConfigMap used as envFrom source",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--secret-name",
        default="thesis-defense-agent-api-secret",
        help="Secret used as optional envFrom source",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore drills",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Container backup directory for downloaded snapshots",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Configure retention as an apply step instead of dry-run preview",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--skip-restore-drill",
        action="store_true",
        help="Do not include restore in the scheduled runner command",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--skip-compare",
        action="store_true",
        help="Do not include restored-collection comparison in the runner command",
    )
    qdrant_snapshot_cronjob_manifest_parser.add_argument(
        "--output",
        default=None,
        help="Optional YAML output path for the CronJob manifest",
    )

    qdrant_k8s_cronjob_smoke_parser = subparsers.add_parser(
        "qdrant-k8s-cronjob-smoke-run",
        help="Apply a Qdrant CronJob manifest, trigger one Job, and collect Kubernetes evidence",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--task-name",
        default="thesis-defense-qdrant-snapshot-drill",
        help="CronJob name",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--job-name",
        default=None,
        help="Optional manual Job name. Defaults to a timestamped name.",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--cron-schedule",
        default="0 3 * * *",
        help="Five-field cron schedule",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--namespace",
        default="thesis-defense-agent",
        help="Kubernetes namespace used by the generated CronJob",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--image",
        default="ghcr.io/buan496/thesis-defense-agent:latest",
        help="Container image used by the generated CronJob",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--config-map-name",
        default="thesis-defense-agent-api-config",
        help="ConfigMap used as envFrom source",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--secret-name",
        default="thesis-defense-agent-api-secret",
        help="Secret used as optional envFrom source",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore drills",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Container backup directory for downloaded snapshots",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Configure retention as an apply step instead of dry-run preview",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--run-restore-drill",
        action="store_true",
        help="Run restore into the disposable collection during the Job.",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--run-compare",
        action="store_true",
        help="Run restored-collection benchmark comparison during the Job.",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--cleanup-job",
        action="store_true",
        help="Delete the manual Job after evidence collection.",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--cleanup-cronjob",
        action="store_true",
        help="Delete the CronJob after evidence collection.",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="Timeout for kubectl commands.",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--manifest-output",
        default=None,
        help="Optional YAML output path for the generated CronJob manifest.",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the smoke report.",
    )
    qdrant_k8s_cronjob_smoke_parser.add_argument(
        "--allow-fail",
        action="store_true",
        help="Print failed report without exiting with status 1.",
    )

    qdrant_k8s_cronjob_observe_parser = subparsers.add_parser(
        "qdrant-k8s-cronjob-schedule-observe",
        help="Apply a Qdrant CronJob and observe one naturally scheduled Job",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--task-name",
        default="thesis-defense-qdrant-snapshot-drill",
        help="CronJob name",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--cron-schedule",
        default="* * * * *",
        help="Five-field cron schedule. Defaults to every minute for smoke observation.",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--namespace",
        default="thesis-defense-agent",
        help="Kubernetes namespace used by the generated CronJob",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--image",
        default="ghcr.io/buan496/thesis-defense-agent:latest",
        help="Container image used by the generated CronJob",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--config-map-name",
        default="thesis-defense-agent-api-config",
        help="ConfigMap used as envFrom source",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--secret-name",
        default="thesis-defense-agent-api-secret",
        help="Secret used as optional envFrom source",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore drills",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Container backup directory for downloaded snapshots",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Configure retention as an apply step instead of dry-run preview",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--run-restore-drill",
        action="store_true",
        help="Run restore into the disposable collection during the scheduled Job.",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--run-compare",
        action="store_true",
        help="Run restored-collection benchmark comparison during the scheduled Job.",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--cleanup-job",
        action="store_true",
        help="Delete the observed scheduled Job after evidence collection.",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--cleanup-cronjob",
        action="store_true",
        help="Delete the CronJob after evidence collection.",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=240,
        help="Timeout for waiting on scheduled Job creation and completion.",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=5,
        help="Polling interval while waiting for Kubernetes to create a scheduled Job.",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--manifest-output",
        default=None,
        help="Optional YAML output path for the generated CronJob manifest.",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the observe report.",
    )
    qdrant_k8s_cronjob_observe_parser.add_argument(
        "--allow-fail",
        action="store_true",
        help="Print failed report without exiting with status 1.",
    )

    qdrant_k8s_cronjob_multi_cycle_observe_parser = subparsers.add_parser(
        "qdrant-k8s-cronjob-multi-cycle-observe",
        help="Apply a Qdrant CronJob and observe multiple naturally scheduled Jobs",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--task-name",
        default="thesis-defense-qdrant-snapshot-drill",
        help="CronJob name",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--cron-schedule",
        default="* * * * *",
        help="Five-field cron schedule. Defaults to every minute for multi-cycle observation.",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--namespace",
        default="thesis-defense-agent",
        help="Kubernetes namespace used by the generated CronJob",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--image",
        default="ghcr.io/buan496/thesis-defense-agent:latest",
        help="Container image used by the generated CronJob",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--config-map-name",
        default="thesis-defense-agent-api-config",
        help="ConfigMap used as envFrom source",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--secret-name",
        default="thesis-defense-agent-api-secret",
        help="Secret used as optional envFrom source",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore drills",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Container backup directory for downloaded snapshots",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Configure retention as an apply step instead of dry-run preview",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--run-restore-drill",
        action="store_true",
        help="Run restore into the disposable collection during scheduled Jobs.",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--run-compare",
        action="store_true",
        help="Run restored-collection benchmark comparison during scheduled Jobs.",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--expected-cycles",
        type=int,
        default=2,
        help="Number of naturally scheduled Jobs to observe.",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--cleanup-jobs",
        action="store_true",
        help="Delete observed scheduled Jobs after evidence collection.",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--cleanup-cronjob",
        action="store_true",
        help="Delete the CronJob after evidence collection.",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=420,
        help="Timeout for waiting on scheduled Job creation and completion.",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=5,
        help="Polling interval while waiting for Kubernetes to create scheduled Jobs.",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--manifest-output",
        default=None,
        help="Optional YAML output path for the generated CronJob manifest.",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the observe report.",
    )
    qdrant_k8s_cronjob_multi_cycle_observe_parser.add_argument(
        "--allow-fail",
        action="store_true",
        help="Print failed report without exiting with status 1.",
    )

    qdrant_snapshot_schedule_install_plan_parser = subparsers.add_parser(
        "qdrant-snapshot-schedule-install-plan",
        help="Generate scheduler install commands for the Qdrant snapshot drill runner",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--platform",
        default="all",
        help="Schedule platform install plan to render",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--task-name",
        default="thesis-defense-qdrant-snapshot-drill",
        help="Schedule task name",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--cron-schedule",
        default="0 3 * * *",
        help="Five-field cron schedule",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--windows-start-time",
        default="03:00",
        help="Windows Task Scheduler start time in HH:MM format",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--working-directory",
        default=".",
        help="Project working directory used by local schedulers",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--log-path",
        default="data/reports/qdrant_snapshot_drill_scheduled.log",
        help="Local log path used by generated scheduler snippets",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace used by generated CronJob preview",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--image",
        default="ghcr.io/buan496/thesis-defense-agent:latest",
        help="Container image used by generated Kubernetes CronJob preview",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore drills",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Local backup directory for downloaded snapshots",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Configure retention as an apply step instead of dry-run preview",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--skip-restore-drill",
        action="store_true",
        help="Do not include restore in the scheduled runner command",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--skip-compare",
        action="store_true",
        help="Do not include restored-collection comparison in the runner command",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--apply",
        action="store_true",
        help="Render commands as real installation commands",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--confirm-task-name",
        default=None,
        help="Must match --task-name when --apply is used",
    )
    qdrant_snapshot_schedule_install_plan_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the install plan",
    )

    qdrant_snapshot_schedule_verify_plan_parser = subparsers.add_parser(
        "qdrant-snapshot-schedule-verify-plan",
        help="Generate status, log, and rollback commands for an installed Qdrant snapshot drill schedule",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--platform",
        required=True,
        help="Installed scheduler platform to verify",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--task-name",
        default="thesis-defense-qdrant-snapshot-drill",
        help="Schedule task name",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--cron-schedule",
        default="0 3 * * *",
        help="Five-field cron schedule",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--windows-start-time",
        default="03:00",
        help="Windows Task Scheduler start time in HH:MM format",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--working-directory",
        default=".",
        help="Project working directory used by local schedulers",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--log-path",
        default="data/reports/qdrant_snapshot_drill_scheduled.log",
        help="Local log path used by generated scheduler snippets",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace used by generated CronJob preview",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--image",
        default="ghcr.io/buan496/thesis-defense-agent:latest",
        help="Container image used by generated Kubernetes CronJob preview",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore drills",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Local backup directory for downloaded snapshots",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Configure retention as an apply step instead of dry-run preview",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--skip-restore-drill",
        action="store_true",
        help="Do not include restore in the scheduled runner command",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--skip-compare",
        action="store_true",
        help="Do not include restored-collection comparison in the runner command",
    )
    qdrant_snapshot_schedule_verify_plan_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the verification plan",
    )

    qdrant_snapshot_schedule_evidence_template_parser = subparsers.add_parser(
        "qdrant-snapshot-schedule-evidence-template",
        help="Generate an evidence report template for a scheduled Qdrant snapshot drill",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--platform",
        required=True,
        help="Installed scheduler platform to document",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--task-name",
        default="thesis-defense-qdrant-snapshot-drill",
        help="Schedule task name",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--cron-schedule",
        default="0 3 * * *",
        help="Five-field cron schedule",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--windows-start-time",
        default="03:00",
        help="Windows Task Scheduler start time in HH:MM format",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--working-directory",
        default=".",
        help="Project working directory used by local schedulers",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--log-path",
        default="data/reports/qdrant_snapshot_drill_scheduled.log",
        help="Local log path used by generated scheduler snippets",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace used by generated CronJob preview",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--image",
        default="ghcr.io/buan496/thesis-defense-agent:latest",
        help="Container image used by generated Kubernetes CronJob preview",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore drills",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Local backup directory for downloaded snapshots",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Configure retention as an apply step instead of dry-run preview",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--skip-restore-drill",
        action="store_true",
        help="Do not include restore in the scheduled runner command",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--skip-compare",
        action="store_true",
        help="Do not include restored-collection comparison in the runner command",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--environment",
        default="local-scheduler",
        help="Environment label written into the evidence report",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--operator",
        default="",
        help="Operator name written into the evidence report",
    )
    qdrant_snapshot_schedule_evidence_template_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the evidence report template",
    )

    qdrant_snapshot_schedule_install_execute_parser = subparsers.add_parser(
        "qdrant-snapshot-schedule-install-execute",
        help="Execute one confirmed Qdrant snapshot drill scheduler install command",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--platform",
        required=True,
        help="Scheduler platform to install",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--task-name",
        default="thesis-defense-qdrant-snapshot-drill",
        help="Schedule task name",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--confirm-task-name",
        required=True,
        help="Must exactly match --task-name",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--cron-schedule",
        default="0 3 * * *",
        help="Five-field cron schedule",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--windows-start-time",
        default="03:00",
        help="Windows Task Scheduler start time in HH:MM format",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--working-directory",
        default=".",
        help="Project working directory used by local schedulers",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--log-path",
        default="data/reports/qdrant_snapshot_drill_scheduled.log",
        help="Local log path used by generated scheduler snippets",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace used by generated CronJob preview",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--image",
        default="ghcr.io/buan496/thesis-defense-agent:latest",
        help="Container image used by generated Kubernetes CronJob preview",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Source Qdrant collection name",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--restore-collection",
        default=f"{QDRANT_COLLECTION}_restore",
        help="Disposable Qdrant collection name used for restore drills",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Local backup directory for downloaded snapshots",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--keep-last",
        type=int,
        default=5,
        help="Number of newest backup files to retain",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Configure retention as an apply step instead of dry-run preview",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--skip-restore-drill",
        action="store_true",
        help="Do not include restore in the scheduled runner command",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--skip-compare",
        action="store_true",
        help="Do not include restored-collection comparison in the runner command",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="Maximum seconds allowed for the install command",
    )
    qdrant_snapshot_schedule_install_execute_parser.add_argument(
        "--output",
        default=None,
        help="Optional Markdown output path for the execution report",
    )

    qdrant_snapshot_create_parser = subparsers.add_parser(
        "qdrant-snapshot-create",
        help="Create a Qdrant collection snapshot through the Qdrant HTTP API",
    )
    qdrant_snapshot_create_parser.add_argument(
        "--url",
        default=QDRANT_URL,
        help="Qdrant URL",
    )
    qdrant_snapshot_create_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Qdrant collection name",
    )
    qdrant_snapshot_create_parser.add_argument(
        "--api-key",
        default=None,
        help="Optional Qdrant API key. Defaults to QDRANT_API_KEY.",
    )

    qdrant_snapshot_list_parser = subparsers.add_parser(
        "qdrant-snapshot-list",
        help="List Qdrant collection snapshots through the Qdrant HTTP API",
    )
    qdrant_snapshot_list_parser.add_argument(
        "--url",
        default=QDRANT_URL,
        help="Qdrant URL",
    )
    qdrant_snapshot_list_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Qdrant collection name",
    )
    qdrant_snapshot_list_parser.add_argument(
        "--api-key",
        default=None,
        help="Optional Qdrant API key. Defaults to QDRANT_API_KEY.",
    )

    qdrant_snapshot_download_parser = subparsers.add_parser(
        "qdrant-snapshot-download",
        help="Download a Qdrant collection snapshot through the Qdrant HTTP API",
    )
    qdrant_snapshot_download_parser.add_argument(
        "--url",
        default=QDRANT_URL,
        help="Qdrant URL",
    )
    qdrant_snapshot_download_parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help="Qdrant collection name",
    )
    qdrant_snapshot_download_parser.add_argument(
        "--snapshot-name",
        required=True,
        help="Qdrant snapshot file name to download",
    )
    qdrant_snapshot_download_parser.add_argument(
        "--backup-dir",
        default=QDRANT_BACKUP_DIR,
        help="Local backup directory for downloaded snapshots",
    )
    qdrant_snapshot_download_parser.add_argument(
        "--api-key",
        default=None,
        help="Optional Qdrant API key. Defaults to QDRANT_API_KEY.",
    )

    qdrant_snapshot_restore_parser = subparsers.add_parser(
        "qdrant-snapshot-restore",
        help="Restore a Qdrant snapshot into a confirmed target collection",
    )
    qdrant_snapshot_restore_parser.add_argument(
        "--url",
        default=QDRANT_URL,
        help="Qdrant URL",
    )
    qdrant_snapshot_restore_parser.add_argument(
        "--restore-collection",
        required=True,
        help="Target collection to restore the snapshot into",
    )
    qdrant_snapshot_restore_parser.add_argument(
        "--snapshot-path",
        required=True,
        help="Local snapshot file path to upload",
    )
    qdrant_snapshot_restore_parser.add_argument(
        "--confirm-restore-collection",
        required=True,
        help=(
            "Required restore confirmation. Must exactly match "
            "--restore-collection."
        ),
    )
    qdrant_snapshot_restore_parser.add_argument(
        "--api-key",
        default=None,
        help="Optional Qdrant API key. Defaults to QDRANT_API_KEY.",
    )

    import_json_to_postgres_parser = subparsers.add_parser(
        "import-json-to-postgres",
        help="Import local JSON / JSONL storage into PostgreSQL repositories",
    )
    import_json_to_postgres_parser.add_argument(
        "--database-url",
        default=None,
        help=(
            "PostgreSQL connection URL. Defaults to DATABASE_URL from the "
            "environment. The value is not printed."
        ),
    )
    import_json_to_postgres_parser.add_argument(
        "--task-directory",
        default=str(DEFAULT_TASK_DIRECTORY),
        help="Local JSON task directory",
    )
    import_json_to_postgres_parser.add_argument(
        "--session-directory",
        default=str(DEFAULT_SESSION_DIRECTORY),
        help="Local JSON session directory",
    )
    import_json_to_postgres_parser.add_argument(
        "--trace-file",
        default=AGENT_TRACE_PATH,
        help="Local JSONL trace file",
    )
    import_json_to_postgres_parser.add_argument(
        "--skip-tasks",
        action="store_true",
        help="Skip task import",
    )
    import_json_to_postgres_parser.add_argument(
        "--skip-sessions",
        action="store_true",
        help="Skip session import",
    )
    import_json_to_postgres_parser.add_argument(
        "--skip-traces",
        action="store_true",
        help="Skip trace import",
    )
    import_json_to_postgres_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count source records without writing to PostgreSQL",
    )
    
    args = parser.parse_args()
    setup_logger(args.log_level)
    
    if args.command == "build-store":
        build_pdf_vector_store(
        file_path=args.file,
        chunk_size=args.chunk_size if args.chunk_size is not None else RAG_CHUNK_SIZE,
        overlap=args.overlap if args.overlap is not None else RAG_CHUNK_OVERLAP,
        min_chunk_size=args.min_chunk_size if args.min_chunk_size is not None else RAG_MIN_CHUNK_SIZE,
        force=args.force,
    )
    elif args.command == "evaluate-rag":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K

        report = evaluate_retrieval(
            benchmark_path=RAG_BENCHMARK_PATH,
            vector_store_path=RAG_VECTOR_STORE_PATH,
            top_k=top_k,
            retriever=args.retriever,
            vector_weight=args.vector_weight,
            bm25_weight=args.bm25_weight,
            use_reranker=args.rerank,
            rerank_candidate_multiplier=args.rerank_candidate_multiplier,
            use_model_reranker=args.model_rerank,
            model_rerank_candidate_multiplier=(
                args.model_rerank_candidate_multiplier
            ),
            use_query_rewrite=args.rewrite_query,
            use_llm_query_rewrite=args.llm_rewrite_query,
            use_multi_query=args.multi_query,
        )

        for item in report["results"]:
            print(
                f"QUERY: {item['query']}\n"
                f"REWRITTEN QUERY: {item['rewritten_query']}\n"
                f"SEARCH QUERIES: {item['search_queries']}\n"
                f"HIT: {item['hit_count']} / {item['total']}\n"
                f"MISSING: {item['missing']}\n"
                f"SCORE: {item['score']}\n"
                f"{'-' * 40}"
            )

        print("TOP_K:", report["top_k"])
        print("RETRIEVER:", report["retriever"])
        print("VECTOR WEIGHT:", report["vector_weight"])
        print("BM25 WEIGHT:", report["bm25_weight"])
        print("USE RERANKER:", report["use_reranker"])
        print(
            "RERANK CANDIDATE MULTIPLIER:",
            report["rerank_candidate_multiplier"],
        )
        print("USE MODEL RERANKER:", report["use_model_reranker"])
        print(
            "MODEL RERANK CANDIDATE MULTIPLIER:",
            report["model_rerank_candidate_multiplier"],
        )
        print("USE QUERY REWRITE:", report["use_query_rewrite"])
        print("USE LLM QUERY REWRITE:", report["use_llm_query_rewrite"])
        print("USE MULTI QUERY:", report["use_multi_query"])
        print("AVERAGE SCORE:", report["average_score"])
        print("CACHE HITS:", report["embedding_cache"]["hits"])
        print("CACHE MISSES:", report["embedding_cache"]["misses"])
        if args.min_score is not None:
            if report["average_score"] >= args.min_score:
                print("EVALUATION STATUS: PASS")
            else:
                print("EVALUATION STATUS: FAIL")
                raise SystemExit(1)
            

        output_path = None

        if args.output is not None:
            output_path = Path(args.output)

        if args.save_report:
            timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
            output_path = Path(f"data/reports/retrieval_eval_{timestamp}.json")

        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            output_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print("REPORT SAVED:", output_path)
    elif args.command == "compare-retrievers":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K
        report = compare_retrievers(
            benchmark_path=RAG_BENCHMARK_PATH,
            vector_store_path=RAG_VECTOR_STORE_PATH,
            top_k=top_k,
            vector_weight=args.vector_weight,
            bm25_weight=args.bm25_weight,
            use_reranker=args.rerank,
            rerank_candidate_multiplier=args.rerank_candidate_multiplier,
            use_model_reranker=args.model_rerank,
            model_rerank_candidate_multiplier=(
                args.model_rerank_candidate_multiplier
            ),
            use_query_rewrite=args.rewrite_query,
            use_llm_query_rewrite=args.llm_rewrite_query,
            use_multi_query=args.multi_query,
        )

        print("RETRIEVER COMPARISON")
        print("TOP_K:", report["top_k"])
        print("VECTOR WEIGHT:", report["vector_weight"])
        print("BM25 WEIGHT:", report["bm25_weight"])
        print("USE RERANKER:", report["use_reranker"])
        print(
            "RERANK CANDIDATE MULTIPLIER:",
            report["rerank_candidate_multiplier"],
        )
        print("USE MODEL RERANKER:", report["use_model_reranker"])
        print(
            "MODEL RERANK CANDIDATE MULTIPLIER:",
            report["model_rerank_candidate_multiplier"],
        )
        print("USE QUERY REWRITE:", report["use_query_rewrite"])
        print("USE LLM QUERY REWRITE:", report["use_llm_query_rewrite"])
        print("USE MULTI QUERY:", report["use_multi_query"])
        print("BEST RETRIEVER:", report["best_retriever"])

        for retriever_report in report["reports"]:
            print("-" * 40)
            print("RETRIEVER:", retriever_report["retriever"])
            print("AVERAGE SCORE:", retriever_report["average_score"])
            print(
                "CACHE HITS:",
                retriever_report["embedding_cache"]["hits"],
            )
            print(
                "CACHE MISSES:",
                retriever_report["embedding_cache"]["misses"],
            )

            for item in retriever_report["results"]:
                print(
                    f"QUERY: {item['query']} | "
                    f"REWRITTEN QUERY: {item['rewritten_query']} | "
                    f"SEARCH QUERIES: {item['search_queries']} | "
                    f"SCORE: {item['score']} | "
                    f"MISSING: {item['missing']}"
                )

        if args.output is not None:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print("REPORT SAVED:", output_path)
    elif args.command == "scan-hybrid-weights":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K

        try:
            weight_pairs = (
                parse_weight_pairs(args.weights)
                if args.weights is not None
                else None
            )
        except ValueError as error:
            print(f"HYBRID WEIGHT SCAN ERROR: {error}")
            raise SystemExit(1) from error

        report = scan_hybrid_weights(
            benchmark_path=RAG_BENCHMARK_PATH,
            vector_store_path=RAG_VECTOR_STORE_PATH,
            top_k=top_k,
            weight_pairs=weight_pairs,
            use_reranker=args.rerank,
            rerank_candidate_multiplier=args.rerank_candidate_multiplier,
            use_model_reranker=args.model_rerank,
            model_rerank_candidate_multiplier=(
                args.model_rerank_candidate_multiplier
            ),
            use_query_rewrite=args.rewrite_query,
            use_llm_query_rewrite=args.llm_rewrite_query,
            use_multi_query=args.multi_query,
        )

        print("HYBRID WEIGHT SCAN")
        print("TOP_K:", report["top_k"])
        print("USE RERANKER:", report["use_reranker"])
        print(
            "RERANK CANDIDATE MULTIPLIER:",
            report["rerank_candidate_multiplier"],
        )
        print("USE MODEL RERANKER:", report["use_model_reranker"])
        print(
            "MODEL RERANK CANDIDATE MULTIPLIER:",
            report["model_rerank_candidate_multiplier"],
        )
        print("USE QUERY REWRITE:", report["use_query_rewrite"])
        print("USE LLM QUERY REWRITE:", report["use_llm_query_rewrite"])
        print("USE MULTI QUERY:", report["use_multi_query"])
        print("BEST VECTOR WEIGHT:", report["best_vector_weight"])
        print("BEST BM25 WEIGHT:", report["best_bm25_weight"])
        print("BEST AVERAGE SCORE:", report["best_average_score"])

        for item in report["reports"]:
            print("-" * 40)
            print("VECTOR WEIGHT:", item["vector_weight"])
            print("BM25 WEIGHT:", item["bm25_weight"])
            print("AVERAGE SCORE:", item["average_score"])
            print("CACHE HITS:", item["embedding_cache"]["hits"])
            print("CACHE MISSES:", item["embedding_cache"]["misses"])

        if args.output is not None:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print("REPORT SAVED:", output_path)
    elif args.command == "compare-retrieval-strategies":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K
        report = compare_retrieval_strategies(
            benchmark_path=RAG_BENCHMARK_PATH,
            vector_store_path=RAG_VECTOR_STORE_PATH,
            top_k=top_k,
            vector_weight=args.vector_weight,
            bm25_weight=args.bm25_weight,
            rerank_candidate_multiplier=args.rerank_candidate_multiplier,
            model_rerank_candidate_multiplier=(
                args.model_rerank_candidate_multiplier
            ),
            include_expensive=args.include_expensive,
        )

        print("RETRIEVAL STRATEGY COMPARISON")
        print("TOP_K:", report["top_k"])
        print("RETRIEVER:", report["retriever"])
        print("VECTOR WEIGHT:", report["vector_weight"])
        print("BM25 WEIGHT:", report["bm25_weight"])
        print("INCLUDE EXPENSIVE:", report["include_expensive"])
        print("BEST STRATEGY:", report["best_strategy"])
        print("BEST AVERAGE SCORE:", report["best_average_score"])

        for strategy_report in report["reports"]:
            print("-" * 40)
            print("STRATEGY:", strategy_report["strategy_name"])
            print("AVERAGE SCORE:", strategy_report["average_score"])
            print(
                "CACHE HITS:",
                strategy_report["embedding_cache"]["hits"],
            )
            print(
                "CACHE MISSES:",
                strategy_report["embedding_cache"]["misses"],
            )

            missing_summary = [
                {
                    "query": item["query"],
                    "missing": item["missing"],
                }
                for item in strategy_report["results"]
                if item["missing"]
            ]
            print("MISSING SUMMARY:", missing_summary)

        if args.output is not None:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print("REPORT SAVED:", output_path)
    elif args.command == "analyze-traces":
        trace_repository = create_trace_repository_for_cli(args.file)
        report = analyze_agent_traces(
            args.file,
            trace_repository=trace_repository,
        )

        print("AGENT RUNS:", report["run_count"])
        print("TOOL CALLS:", report["tool_call_count"])
        print("SUCCESS COUNT:", report["success_count"])
        print("FAILURE COUNT:", report["failure_count"])
        print("SUCCESS RATE:", report["success_rate"])
        print(
            "AVERAGE DURATION MS:",
            round(report["average_duration_ms"], 2),
        )
        print("TOTAL PROMPT TOKENS:", report["total_prompt_tokens"])
        print(
            "TOTAL COMPLETION TOKENS:",
            report["total_completion_tokens"],
        )
        print("TOTAL TOKENS:", report["total_tokens"])
        print(
            "AVERAGE TOKENS PER RUN:",
            round(report["average_total_tokens_per_run"], 2),
        )
        print("TOTAL COST:", round(report["total_cost"], 6))
        print(
            "AVERAGE COST PER RUN:",
            round(report["average_cost_per_run"], 6),
        )
        print("CURRENCY:", report["currency"])

        if report["most_expensive_run"] is not None:
            print("MOST EXPENSIVE RUN:")
            print(
                "  LINE:",
                report["most_expensive_run"]["line_number"],
            )
            print(
                "  COST:",
                round(report["most_expensive_run"]["total_cost"], 6),
            )
            print(
                "  TOKENS:",
                report["most_expensive_run"]["total_tokens"],
            )
            print(
                "  MESSAGE:",
                report["most_expensive_run"]["user_message"],
            )
        print("TOOL COUNTS:")

        for tool_name, count in report["tool_counts"].items():
            print(f"  {tool_name}: {count}")

    elif args.command == "replay-agent-trace":
        try:
            trace_repository = create_trace_repository_for_cli(args.file)
            replay = replay_agent_trace(
                file_path=args.file,
                line_number=args.line_number,
                trace_repository=trace_repository,
            )
        except (FileNotFoundError, ValueError) as error:
            print(f"TRACE REPLAY ERROR: {error}")
            raise SystemExit(1) from error

        print("AGENT TRACE REPLAY")
        print("LINE NUMBER:", replay["line_number"])
        print("CREATED AT:", replay["created_at"])
        print("USER MESSAGE:")
        print(replay["user_message"])
        print("FINAL OUTPUT:")
        print(replay["final_output"])
        print("STEPS:", replay["steps"])
        print("TOOL CALLS:", replay["tool_call_count"])
        print("SUCCESSFUL TOOL CALLS:", replay["successful_tool_calls"])
        print("FAILED TOOL CALLS:", replay["failed_tool_calls"])
        print("TOTAL TOOL DURATION MS:", replay["total_duration_ms"])
        print("TOKEN USAGE:")
        print("  PROMPT TOKENS:", replay["token_usage"]["prompt_tokens"])
        print(
            "  COMPLETION TOKENS:",
            replay["token_usage"]["completion_tokens"],
        )
        print("  TOTAL TOKENS:", replay["token_usage"]["total_tokens"])
        print("COST ESTIMATE:")
        print("  INPUT COST:", replay["cost_estimate"]["input_cost"])
        print("  OUTPUT COST:", replay["cost_estimate"]["output_cost"])
        print("  TOTAL COST:", replay["cost_estimate"]["total_cost"])
        print("  CURRENCY:", replay["cost_estimate"]["currency"])
        print("TOOL TRACE:")

        for index, tool_trace in enumerate(
            replay["tool_traces"],
            start=1,
        ):
            print(f"  #{index}")
            print("    STEP:", tool_trace.get("step"))
            print("    TOOL:", tool_trace.get("tool_name"))
            print("    SUCCESS:", tool_trace.get("success"))
            print("    DURATION_MS:", tool_trace.get("duration_ms"))
            print("    ARGUMENTS:", tool_trace.get("arguments"))

    elif args.command == "replay-trace":
        try:
            trace_repository = create_trace_repository_for_cli(args.file)
            summary = replay_trace_file(
                file_path=args.file,
                source_type=args.source_type,
                trace_repository=trace_repository,
            )
        except (FileNotFoundError, ValueError) as error:
            print(f"TRACE REPLAY ERROR: {error}")
            raise SystemExit(1) from error

        print("TRACE REPLAY SUMMARY")
        print("FILE:", args.file)
        print("SOURCE TYPE:", args.source_type)
        print("RECORD COUNT:", summary["record_count"])
        print("FAILED RECORD COUNT:", summary["failed_record_count"])
        print("TOOL CALL COUNT:", summary["total_tool_call_count"])
        print(
            "FAILED TOOL CALL COUNT:",
            summary["total_failed_tool_call_count"],
        )
        print("TOTAL DURATION MS:", summary["total_duration_ms"])
        print("BY SOURCE TYPE:", summary["by_source_type"])
        print("BY TOOL:", summary["by_tool"])

    elif args.command == "trace-feedback":
        try:
            trace_repository = create_trace_repository_for_cli(args.file)
            summary = replay_trace_file(
                file_path=args.file,
                source_type=args.source_type,
                trace_repository=trace_repository,
            )
            source_id = args.source_id

            if source_id is None:
                source_id = f"{args.source_type}:{args.file}"

            feedback_record = build_trace_feedback_record(
                replay_summary=summary,
                source_id=source_id,
            )

            if feedback_record is not None:
                saved_path = save_feedback_record(
                    file_path=args.feedback_file,
                    feedback_record=feedback_record,
                )
            else:
                saved_path = None
        except (FileNotFoundError, ValueError) as error:
            print(f"TRACE FEEDBACK ERROR: {error}")
            raise SystemExit(1) from error

        if feedback_record is None:
            print("TRACE FEEDBACK NOT CREATED")
            print("REASON: no trace replay issues detected")
            print("FILE:", args.file)
            print("SOURCE TYPE:", args.source_type)
        else:
            print("TRACE FEEDBACK RECORDED")
            print("FEEDBACK ID:", feedback_record["id"])
            print("SOURCE TYPE:", feedback_record["source_type"])
            print("SOURCE ID:", feedback_record["source_id"])
            print("RATING:", feedback_record["rating"])
            print("TAGS:", feedback_record["tags"])
            print("SAVED:", saved_path)

    elif args.command == "compare-agent-traces":
        try:
            comparison = compare_agent_trace_records(
                baseline_file_path=args.baseline_file,
                current_file_path=args.current_file,
                baseline_line_number=args.baseline_line_number,
                current_line_number=args.current_line_number,
            )
        except (FileNotFoundError, ValueError) as error:
            print(f"TRACE COMPARISON ERROR: {error}")
            raise SystemExit(1) from error

        print("AGENT TRACE COMPARISON")
        print("BASELINE LINE:", comparison["baseline_line_number"])
        print("CURRENT LINE:", comparison["current_line_number"])
        print("SAME USER MESSAGE:", comparison["same_user_message"])
        print("SAME FINAL OUTPUT:", comparison["same_final_output"])
        print("SAME TOOL SEQUENCE:", comparison["same_tool_sequence"])
        print(
            "BASELINE TOOLS:",
            comparison["baseline_tool_sequence"],
        )
        print("CURRENT TOOLS:", comparison["current_tool_sequence"])
        print(
            "SAME TOOL SUCCESS SEQUENCE:",
            comparison["same_tool_success_sequence"],
        )
        print(
            "TOOL CALL COUNT DELTA:",
            comparison["tool_call_count_delta"],
        )
        print(
            "FAILED TOOL CALL DELTA:",
            comparison["failed_tool_call_delta"],
        )
        print("TOTAL TOKENS DELTA:", comparison["total_tokens_delta"])
        print("TOTAL COST DELTA:", comparison["total_cost_delta"])
        print("DURATION MS DELTA:", comparison["duration_ms_delta"])
        print("REGRESSIONS:", comparison["regressions"])

    elif args.command == "record-feedback":
        try:
            metadata = {}

            if args.metadata is not None:
                metadata = parse_json_argument(
                    args.metadata,
                    "--metadata",
                )

            feedback_record = create_feedback_record(
                source_type=args.source_type,
                source_id=args.source_id,
                rating=args.rating,
                comment=args.comment,
                tags=args.tag,
                metadata=metadata,
            )

            saved_path = save_feedback_record(
                file_path=args.file,
                feedback_record=feedback_record,
            )
        except ValueError as error:
            print(f"FEEDBACK ERROR: {error}")
            raise SystemExit(1) from error

        print("FEEDBACK RECORDED")
        print("FEEDBACK ID:", feedback_record["id"])
        print("SOURCE TYPE:", feedback_record["source_type"])
        print("SOURCE ID:", feedback_record["source_id"])
        print("RATING:", feedback_record["rating"])
        print("TAGS:", feedback_record["tags"])
        print("SAVED:", saved_path)

    elif args.command == "summarize-feedback":
        try:
            feedback_records = load_feedback_records(args.file)
        except ValueError as error:
            print(f"FEEDBACK SUMMARY ERROR: {error}")
            raise SystemExit(1) from error

        summary = summarize_feedback_records(feedback_records)

        print("FEEDBACK SUMMARY")
        print("FILE:", args.file)
        print("COUNT:", summary["count"])
        print("AVERAGE RATING:", summary["average_rating"])
        print("SOURCE TYPE COUNTS:", summary["source_type_counts"])
        print("TAG COUNTS:", summary["tag_counts"])

    elif args.command == "export-feedback-candidates":
        try:
            feedback_records = load_feedback_records(args.feedback_file)
        except ValueError as error:
            print(f"FEEDBACK CANDIDATE ERROR: {error}")
            raise SystemExit(1) from error

        output_path = args.output

        if output_path is None:
            output_path = build_default_candidate_output_path(
                BENCHMARK_CANDIDATE_DIRECTORY
            )

        candidate_tags = args.tag or None

        report = export_feedback_benchmark_candidates(
            feedback_records=feedback_records,
            output_file_path=output_path,
            max_rating=args.max_rating,
            candidate_tags=candidate_tags,
        )

        print("FEEDBACK CANDIDATES EXPORTED")
        print("SOURCE FEEDBACK FILE:", args.feedback_file)
        print("OUTPUT:", output_path)
        print("MAX RATING:", report["max_rating"])
        print("CANDIDATE TAGS:", report["candidate_tags"])
        print("CANDIDATE COUNT:", report["count"])

    elif args.command == "review-benchmark-candidate":
        try:
            candidate_report = load_candidate_report(args.file)
            candidate = review_benchmark_candidate(
                candidate_report=candidate_report,
                candidate_id=args.candidate_id,
                status=args.status,
                reviewer=args.reviewer,
                reason=args.reason,
            )
            saved_path = save_candidate_report(
                args.file,
                candidate_report,
            )
        except (FileNotFoundError, ValueError) as error:
            print(f"BENCHMARK CANDIDATE REVIEW ERROR: {error}")
            raise SystemExit(1) from error

        print("BENCHMARK CANDIDATE REVIEWED")
        print("FILE:", saved_path)
        print("CANDIDATE ID:", candidate["candidate_id"])
        print("STATUS:", candidate["status"])
        print("REVIEWER:", candidate["review"]["reviewer"])
        print("REASON:", candidate["review"]["reason"])

    elif args.command == "summarize-benchmark-candidates":
        try:
            candidate_report = load_candidate_report(args.file)
        except FileNotFoundError as error:
            print(f"BENCHMARK CANDIDATE SUMMARY ERROR: {error}")
            raise SystemExit(1) from error

        summary = summarize_candidate_review_status(candidate_report)

        print("BENCHMARK CANDIDATE SUMMARY")
        print("FILE:", args.file)
        print("COUNT:", summary["count"])
        print("STATUS COUNTS:", summary["status_counts"])

    elif args.command == "export-benchmark-draft":
        try:
            candidate_report = load_candidate_report(args.candidate_file)
        except FileNotFoundError as error:
            print(f"BENCHMARK DRAFT ERROR: {error}")
            raise SystemExit(1) from error

        output_path = args.output

        if output_path is None:
            output_path = build_default_benchmark_draft_output_path(
                BENCHMARK_CANDIDATE_DIRECTORY
            )

        draft = export_accepted_candidates_to_benchmark_draft(
            candidate_report=candidate_report,
            output_file_path=output_path,
        )

        print("BENCHMARK DRAFT EXPORTED")
        print("CANDIDATE FILE:", args.candidate_file)
        print("OUTPUT:", output_path)
        print("DRAFT COUNT:", draft["count"])

    elif args.command == "validate-benchmark-draft":
        try:
            draft = load_benchmark_draft(args.file)
        except FileNotFoundError as error:
            print(f"BENCHMARK DRAFT VALIDATION ERROR: {error}")
            raise SystemExit(1) from error

        report = validate_benchmark_draft(draft)

        print("BENCHMARK DRAFT VALIDATION")
        print("FILE:", args.file)
        print("PASSED:", report["passed"])
        print("ITEM COUNT:", report["item_count"])
        print("VALID COUNT:", report["valid_count"])
        print("INVALID COUNT:", report["invalid_count"])

        for item in report["items"]:
            print("DRAFT ID:", item["draft_id"])
            print("BENCHMARK TYPE:", item["benchmark_type"])
            print("ITEM PASSED:", item["passed"])
            print("ERRORS:", item["errors"])
            print("-" * 40)

        if args.fail_on_error and not report["passed"]:
            raise SystemExit(1)

    elif args.command == "export-validated-benchmark-draft":
        try:
            draft = load_benchmark_draft(args.draft_file)
            report = export_validated_benchmark_draft(
                draft=draft,
                output_directory=args.output_directory,
            )
        except (FileNotFoundError, ValueError) as error:
            print(f"VALIDATED BENCHMARK EXPORT ERROR: {error}")
            raise SystemExit(1) from error

        print("VALIDATED BENCHMARK DRAFT EXPORTED")
        print("DRAFT FILE:", args.draft_file)
        print("OUTPUT DIRECTORY:", report["output_directory"])
        print("COUNTS:", report["counts"])
        print("FILES:", report["files"])

    elif args.command == "evaluate-agent-routing":
        report = evaluate_agent_routing(
            benchmark_path=args.benchmark,
        )

        for item in report["results"]:
            print("USER MESSAGE:", item["user_message"])
            print("EXPECTED TOOLS:", item["expected_tools"])
            print("ACTUAL TOOLS:", item["actual_tools"])
            print("ROUTING PASSED:", item["routing_passed"])
            print("ARGUMENTS PASSED:", item["arguments_passed"])
            print("COMPLETION PASSED:", item["completion_passed"])
            print("GROUNDING PASSED:", item["grounding_passed"])
            print(
                "COMPLETION ERRORS:",
                item["completion_check"]["errors"],
            )
            print(
                "QUESTION COUNT:",
                item["completion_check"]["question_count"],
            )
            print(
                "GROUNDEDNESS SCORE:",
                item["grounding_check"]["score"],
            )
            print(
                "GROUNDING ERRORS:",
                item["grounding_check"]["errors"],
            )
            print(
                "FAITHFULNESS EVALUATED:",
                item["faithfulness_check"]["evaluated"],
            )
            print(
                "FAITHFULNESS SCORE:",
                item["faithfulness_check"]["score"],
            )
            print(
                "FAITHFULNESS PASSED:",
                item["faithfulness_passed"],
            )
            print(
                "FAITHFULNESS REASON:",
                item["faithfulness_check"]["reason"],
            )
            print(
                "UNSUPPORTED CLAIMS:",
                item["faithfulness_check"]["unsupported_claims"],
            )
            print(
                "CONTRADICTIONS:",
                item["faithfulness_check"]["contradictions"],
            )

            for claim in item["grounding_check"]["claims"]:
                print("GROUNDING CLAIM:", claim["claim"])
                print(
                    "CLAIM IN ANSWER:",
                    claim["claim_in_answer"],
                )
                print(
                    "EVIDENCE FOUND:",
                    claim["evidence_found"],
                )
                print("SUPPORTED:", claim["supported"])

            for check in item["argument_checks"]:
                print("ARGUMENT TOOL:", check["tool_name"])
                print("ARGUMENTS:", check["arguments"])
                print("ARGUMENT PASSED:", check["passed"])

                if check["errors"]:
                    print("ARGUMENT ERRORS:", check["errors"])

            print("PASSED:", item["passed"])

            if item["error"] is not None:
                print("ERROR:", item["error"])

            print("-" * 40)

        print("TOTAL:", report["total"])
        print("PASSED:", report["passed"])
        print("FAILED:", report["failed"])
        print("TOOL ROUTING ACCURACY:", report["routing_accuracy"])
        print("TOOL ARGUMENT ACCURACY:", report["argument_accuracy"])
        print("TASK COMPLETION RATE:", report["completion_rate"])
        print(
            "END-TO-END SUCCESS RATE:",
            report["end_to_end_success_rate"],
        )
        print("GROUNDEDNESS SCORE:", report["groundedness_score"])
        print(
            "GROUNDED TASK RATE:",
            report["grounded_task_rate"],
        )
        print(
            "END-TO-END GROUNDED SUCCESS RATE:",
            report["end_to_end_grounded_success_rate"],
        )
        print("FAITHFULNESS CASES:", report["faithfulness_cases"])
        print("FAITHFULNESS SCORE:", report["faithfulness_score"])
        print(
            "FAITHFULNESS PASS RATE:",
            report["faithfulness_pass_rate"],
        )
        print(
            "END-TO-END FAITHFUL SUCCESS RATE:",
            report["end_to_end_faithful_success_rate"],
        )

        if args.min_accuracy is not None:
            if report["accuracy"] >= args.min_accuracy:
                print("EVALUATION STATUS: PASS")
            else:
                print("EVALUATION STATUS: FAIL")
                raise SystemExit(1)

        if args.min_argument_accuracy is not None:
            if (
                report["argument_accuracy"]
                >= args.min_argument_accuracy
            ):
                print("ARGUMENT EVALUATION STATUS: PASS")
            else:
                print("ARGUMENT EVALUATION STATUS: FAIL")
                raise SystemExit(1)

        if args.min_completion_rate is not None:
            if (
                report["completion_rate"]
                >= args.min_completion_rate
            ):
                print("COMPLETION EVALUATION STATUS: PASS")
            else:
                print("COMPLETION EVALUATION STATUS: FAIL")
                raise SystemExit(1)

        if args.min_groundedness_score is not None:
            if (
                report["groundedness_score"]
                >= args.min_groundedness_score
            ):
                print("GROUNDEDNESS EVALUATION STATUS: PASS")
            else:
                print("GROUNDEDNESS EVALUATION STATUS: FAIL")
                raise SystemExit(1)

        if args.min_grounded_task_rate is not None:
            if (
                report["grounded_task_rate"]
                >= args.min_grounded_task_rate
            ):
                print("GROUNDED TASK EVALUATION STATUS: PASS")
            else:
                print("GROUNDED TASK EVALUATION STATUS: FAIL")
                raise SystemExit(1)

        if args.min_faithfulness_score is not None:
            if (
                report["faithfulness_score"]
                >= args.min_faithfulness_score
            ):
                print("FAITHFULNESS SCORE STATUS: PASS")
            else:
                print("FAITHFULNESS SCORE STATUS: FAIL")
                raise SystemExit(1)

        if args.min_faithfulness_pass_rate is not None:
            if (
                report["faithfulness_pass_rate"]
                >= args.min_faithfulness_pass_rate
            ):
                print("FAITHFULNESS PASS RATE STATUS: PASS")
            else:
                print("FAITHFULNESS PASS RATE STATUS: FAIL")
                raise SystemExit(1)

    elif args.command == "evaluate-faithfulness":
        evaluation_result = evaluate_faithfulness_benchmark(
            benchmark_path=args.benchmark,
        )
        report = create_evaluation_report(
            evaluation_type="faithfulness",
            model=DEEPSEEK_MODEL,
            config={
                "benchmark_path": args.benchmark,
            },
            result=evaluation_result,
        )

        for item in report["results"]:
            print("NAME:", item["name"])
            print("EXPECTED:", item["expected_passed"])
            print("ACTUAL:", item["actual_passed"])
            print("CORRECT:", item["prediction_correct"])
            print("SCORE:", item["score"])
            print("REASON:", item["reason"])
            print(
                "UNSUPPORTED CLAIMS:",
                item["unsupported_claims"],
            )
            print(
                "CONTRADICTIONS:",
                item["contradictions"],
            )
            print("-" * 40)

        print("TOTAL:", report["total"])
        print("PASSED:", report["passed"])
        print("FAILED:", report["failed"])
        print("JUDGE ACCURACY:", report["accuracy"])

        output_path = None

        if args.output is not None:
            output_path = Path(args.output)
        elif args.save_report:
            output_path = build_timestamped_report_path(
                prefix="faithfulness_eval",
            )

        if output_path is not None:
            saved_path = save_evaluation_report(
                report=report,
                output_path=output_path,
            )
            print("REPORT SAVED:", saved_path)

        if args.min_accuracy is not None:
            if report["accuracy"] >= args.min_accuracy:
                print("JUDGE EVALUATION STATUS: PASS")
            else:
                print("JUDGE EVALUATION STATUS: FAIL")
                raise SystemExit(1)

    elif args.command == "evaluate-faithfulness-stability":
        evaluation_result = evaluate_faithfulness_stability(
            benchmark_path=args.benchmark,
            repeat_count=args.repeat_count,
        )
        report = create_evaluation_report(
            evaluation_type="faithfulness_stability",
            model=DEEPSEEK_MODEL,
            config={
                "benchmark_path": args.benchmark,
                "repeat_count": args.repeat_count,
            },
            result=evaluation_result,
        )

        for item in report["results"]:
            print("NAME:", item["name"])
            print("EXPECTED:", item["expected_passed"])
            print("PREDICTIONS:", item["predictions"])
            print(
                "MAJORITY PREDICTION:",
                item["majority_prediction"],
            )
            print(
                "AGREEMENT SCORE:",
                item["agreement_score"],
            )
            print("UNANIMOUS:", item["unanimous"])
            print(
                "MAJORITY CORRECT:",
                item["majority_correct"],
            )
            print("-" * 40)

        print("REPEAT COUNT:", report["repeat_count"])
        print("TOTAL:", report["total"])
        print(
            "AVERAGE AGREEMENT:",
            report["average_agreement"],
        )
        print("UNANIMOUS RATE:", report["unanimous_rate"])
        print(
            "MAJORITY ACCURACY:",
            report["majority_accuracy"],
        )

        output_path = None

        if args.output is not None:
            output_path = Path(args.output)
        elif args.save_report:
            output_path = build_timestamped_report_path(
                prefix="faithfulness_stability",
            )

        if output_path is not None:
            saved_path = save_evaluation_report(
                report=report,
                output_path=output_path,
            )
            print("REPORT SAVED:", saved_path)

        if args.min_average_agreement is not None:
            if (
                report["average_agreement"]
                >= args.min_average_agreement
            ):
                print("AVERAGE AGREEMENT STATUS: PASS")
            else:
                print("AVERAGE AGREEMENT STATUS: FAIL")
                raise SystemExit(1)

        if args.min_unanimous_rate is not None:
            if (
                report["unanimous_rate"]
                >= args.min_unanimous_rate
            ):
                print("UNANIMOUS RATE STATUS: PASS")
            else:
                print("UNANIMOUS RATE STATUS: FAIL")
                raise SystemExit(1)

        if args.min_majority_accuracy is not None:
            if (
                report["majority_accuracy"]
                >= args.min_majority_accuracy
            ):
                print("MAJORITY ACCURACY STATUS: PASS")
            else:
                print("MAJORITY ACCURACY STATUS: FAIL")
                raise SystemExit(1)

    elif args.command == "compare-evaluation-reports":
        comparison_result = compare_evaluation_report_files(
            baseline_path=args.baseline,
            current_path=args.current,
            metric_tolerance=args.metric_tolerance,
            stability_tolerance=args.stability_tolerance,
        )
        report = create_evaluation_report(
            evaluation_type="evaluation_regression",
            model="deterministic-comparator",
            config={
                "baseline_path": args.baseline,
                "current_path": args.current,
                "metric_tolerance": args.metric_tolerance,
                "stability_tolerance": args.stability_tolerance,
            },
            result=comparison_result,
        )

        print("EVALUATION TYPE:", report["evaluation_type"])

        for item in report["metric_changes"]:
            print(
                f"METRIC: {item['name']}\n"
                f"BASELINE: {item['baseline']}\n"
                f"CURRENT: {item['current']}\n"
                f"DELTA: {item['delta']}\n"
                f"REGRESSED: {item['regressed']}\n"
                f"{'-' * 40}"
            )

        print("PREDICTION FLIPS:")
        for item in report["prediction_flips"]:
            print(
                f"  {item['name']}: "
                f"{item['baseline_prediction']} -> "
                f"{item['current_prediction']} "
                f"(regression={item['regression']})"
            )

        print("STABILITY REGRESSIONS:")
        for item in report["stability_regressions"]:
            print(
                f"  {item['name']} / {item['metric']}: "
                f"{item['baseline']} -> {item['current']}"
            )

        print("ADDED CASES:", report["added_cases"])
        print("REMOVED CASES:", report["removed_cases"])
        print("METADATA CHANGES:", report["metadata_changes"])
        print("REGRESSION COUNT:", report["regression_count"])
        print("HAS REGRESSION:", report["has_regression"])

        output_path = None

        if args.output is not None:
            output_path = Path(args.output)
        elif args.save_report:
            output_path = build_timestamped_report_path(
                prefix="evaluation_regression",
            )

        if output_path is not None:
            saved_path = save_evaluation_report(
                report=report,
                output_path=output_path,
            )
            print("REPORT SAVED:", saved_path)

        if args.markdown_output is not None:
            markdown_path = save_evaluation_comparison_markdown(
                report=report,
                output_path=args.markdown_output,
            )
            print("MARKDOWN REPORT SAVED:", markdown_path)

        if args.fail_on_regression:
            if report["has_regression"]:
                print("REGRESSION STATUS: FAIL")
                raise SystemExit(1)

            print("REGRESSION STATUS: PASS")

    elif args.command == "chat":
        user_message = args.message

        if user_message is None:
            user_message = input("USER: ")

        if not user_message.strip():
            raise ValueError("用户消息不能为空")
        
        if args.max_history_turns <= 0:
            print("ARGUMENT ERROR: --max-history-turns 必须大于 0")
            raise SystemExit(2)
        
        if args.max_history_characters <= 0:
            print("ARGUMENT ERROR: --max-history-characters 必须大于 0")
            raise SystemExit(2)
        
        if args.max_run_cost is not None and args.max_run_cost < 0:
            print("ARGUMENT ERROR: --max-run-cost 不能小于 0")
            raise SystemExit(2)
        
        if (
            args.preflight_max_run_cost is not None
            and args.preflight_max_run_cost < 0
        ):
            print("ARGUMENT ERROR: --preflight-max-run-cost 不能小于 0")
            raise SystemExit(2)
        
        if args.max_memory_weaknesses < 0:
            print("ARGUMENT ERROR: --max-memory-weaknesses 不能小于 0")
            raise SystemExit(2)
        
        if args.max_memory_summaries < 0:
            print("ARGUMENT ERROR: --max-memory-summaries 不能小于 0")
            raise SystemExit(2)
        
        if args.compact_summary_max_characters <= 0:
            print(
                "ARGUMENT ERROR: "
                "--compact-summary-max-characters must be greater than 0"
            )
            raise SystemExit(2)
        
        try:
            session_repository = create_session_repository_for_cli(
                str(DEFAULT_SESSION_DIRECTORY),
            )
            result, session, session_path = run_agent_session(
                user_message=user_message,
                session_id=args.session_id,
                max_history_turns=args.max_history_turns,
                max_history_characters=args.max_history_characters,
                max_run_cost=args.max_run_cost,
                preflight_max_run_cost=args.preflight_max_run_cost,
                use_long_term_memory=not args.disable_memory,
                max_memory_weaknesses=args.max_memory_weaknesses,
                max_memory_summaries=args.max_memory_summaries,
                compact_session=not args.disable_session_compaction,
                compact_summary_max_characters=(
                    args.compact_summary_max_characters
                ),
                session_repository=session_repository,
            )
        except FileNotFoundError as error:
            print(f"SESSION ERROR: {error}")
            raise SystemExit(1) from error
        
        except BudgetExceededError as error:
            print(f"BUDGET ERROR: {error}")
            raise SystemExit(1) from error

        except PreflightBudgetExceededError as error:
            print(f"PREFLIGHT BUDGET ERROR: {error}")
            raise SystemExit(1) from error
        
        print("\nASSISTANT:")
        print(result.final_output)

        print("\nTOKEN USAGE:")
        print("PROMPT TOKENS:", result.token_usage.prompt_tokens)
        print(
            "COMPLETION TOKENS:",
            result.token_usage.completion_tokens,
        )
        print("TOTAL TOKENS:", result.token_usage.total_tokens)

        print("\nCOST ESTIMATE:")
        print("INPUT COST:", round(result.cost_estimate.input_cost, 6))
        print("OUTPUT COST:", round(result.cost_estimate.output_cost, 6))
        print("TOTAL COST:", round(result.cost_estimate.total_cost, 6))
        print("CURRENCY:", result.cost_estimate.currency)

        print("\nSESSION ID:")
        print(session.session_id)

        print("\nSESSION SAVED:")
        print(session_path)

    elif args.command == "memory-show":
        memory = load_long_term_memory(args.path)
        context = build_long_term_memory_context(memory)

        print("MEMORY PATH:", args.path)
        print("MEMORY JSON:")
        print(json.dumps(memory, ensure_ascii=False, indent=2))
        print("MEMORY CONTEXT:")
        print(context or "<empty>")

    elif args.command == "memory-set-profile":
        if not args.key.strip():
            print("ARGUMENT ERROR: --key cannot be empty")
            raise SystemExit(2)
        
        if not args.value.strip():
            print("ARGUMENT ERROR: --value cannot be empty")
            raise SystemExit(2)
        
        memory = load_long_term_memory(args.path)
        memory = update_memory_profile(
            memory,
            **{args.key.strip(): args.value.strip()},
        )
        memory_path = save_long_term_memory(memory, args.path)

        print("MEMORY PROFILE UPDATED")
        print("PATH:", memory_path)
        print("KEY:", args.key.strip())
        print("VALUE:", args.value.strip())

    elif args.command == "memory-add-weakness":
        try:
            memory = load_long_term_memory(args.path)
            memory = add_weakness(
                memory,
                weakness=args.text,
                source_task_id=args.task_id,
            )
            memory_path = save_long_term_memory(memory, args.path)
        except ValueError as error:
            print(f"MEMORY ERROR: {error}")
            raise SystemExit(1) from error

        print("MEMORY WEAKNESS ADDED")
        print("PATH:", memory_path)
        print("WEAKNESS:", args.text.strip())

    elif args.command == "memory-add-summary":
        try:
            memory = load_long_term_memory(args.path)
            memory = add_training_summary(
                memory,
                summary=args.summary,
                task_id=args.task_id,
                topic=args.topic,
            )
            memory_path = save_long_term_memory(memory, args.path)
        except ValueError as error:
            print(f"MEMORY ERROR: {error}")
            raise SystemExit(1) from error

        print("MEMORY SUMMARY ADDED")
        print("PATH:", memory_path)
        print("SUMMARY:", args.summary.strip())

    elif args.command == "memory-prune":
        if args.max_weaknesses < 0:
            print("ARGUMENT ERROR: --max-weaknesses cannot be negative")
            raise SystemExit(2)
        
        if args.max_summaries < 0:
            print("ARGUMENT ERROR: --max-summaries cannot be negative")
            raise SystemExit(2)
        
        try:
            memory = load_long_term_memory(args.path)
            before_weaknesses = len(memory["weaknesses"])
            before_summaries = len(memory["training_summaries"])
            memory = prune_long_term_memory(
                memory,
                max_weaknesses=args.max_weaknesses,
                max_summaries=args.max_summaries,
            )
            if args.dry_run:
                memory_path = args.path
            else:
                memory_path = save_long_term_memory(memory, args.path)
        except ValueError as error:
            print(f"MEMORY ERROR: {error}")
            raise SystemExit(1) from error

        if args.dry_run:
            print("MEMORY PRUNE DRY RUN")
        else:
            print("MEMORY PRUNED")
        print("PATH:", memory_path)
        print("WEAKNESSES:", before_weaknesses, "->", len(memory["weaknesses"]))
        print(
            "SUMMARIES:",
            before_summaries,
            "->",
            len(memory["training_summaries"]),
        )

    elif args.command == "memory-audit":
        try:
            memory = load_long_term_memory(args.path)
            report = audit_long_term_memory(memory)
        except ValueError as error:
            print(f"MEMORY AUDIT ERROR: {error}")
            raise SystemExit(1) from error

        print("MEMORY AUDIT")
        print("PATH:", args.path)
        print("PASSED:", report["passed"])
        print("PROFILE COUNT:", report["profile_count"])
        print("WEAKNESS COUNT:", report["weakness_count"])
        print("SUMMARY COUNT:", report["summary_count"])
        print(
            "DUPLICATE WEAKNESS COUNT:",
            report["duplicate_weakness_count"],
        )
        print(
            "DUPLICATE SUMMARY COUNT:",
            report["duplicate_summary_count"],
        )
        print(
            "EMPTY PROFILE FIELD COUNT:",
            report["empty_profile_field_count"],
        )
        print("EMPTY WEAKNESS COUNT:", report["empty_weakness_count"])
        print("EMPTY SUMMARY COUNT:", report["empty_summary_count"])
        print("ISSUE COUNT:", report["issue_count"])
        print("RECOMMENDATIONS:", report["recommendations"])

    elif args.command == "memory-hit-audit":
        try:
            memory = load_long_term_memory(args.path)
            report = audit_memory_hits(
                memory,
                query=args.query,
                max_weaknesses=args.max_weaknesses,
                max_summaries=args.max_summaries,
            )
        except ValueError as error:
            print(f"MEMORY HIT AUDIT ERROR: {error}")
            raise SystemExit(1) from error

        print("MEMORY HIT AUDIT")
        print("PATH:", args.path)
        print("QUERY:", report["query"])
        print("WEAKNESS HIT COUNT:", report["weakness_hit_count"])
        print("SUMMARY HIT COUNT:", report["summary_hit_count"])
        print("WEAKNESS HITS:")

        for hit in report["weakness_hits"]:
            print(
                f"  INDEX: {hit['index']} "
                f"SCORE: {hit['score']} "
                f"TEXT: {hit['text']}"
            )

        print("SUMMARY HITS:")

        for hit in report["summary_hits"]:
            print(
                f"  INDEX: {hit['index']} "
                f"SCORE: {hit['score']} "
                f"TEXT: {hit['text']}"
            )

    elif args.command == "memory-context-report":
        try:
            memory = load_long_term_memory(args.path)
            report = build_memory_context_report(
                memory,
                query=args.query,
                max_weaknesses=args.max_weaknesses,
                max_summaries=args.max_summaries,
            )
        except ValueError as error:
            print(f"MEMORY CONTEXT REPORT ERROR: {error}")
            raise SystemExit(1) from error

        print("MEMORY CONTEXT REPORT")
        print("PATH:", args.path)
        print("QUERY:", report["query"])
        print("MAX WEAKNESSES:", report["max_weaknesses"])
        print("MAX SUMMARIES:", report["max_summaries"])
        print("IS EMPTY:", report["is_empty"])
        print("CHARACTERS:", report["context_character_count"])
        print("LINES:", report["line_count"])
        print("CONTEXT:")
        print(report["context"] or "<empty>")

    elif args.command == "mock-defense":
        run_mock_defense(training_query=args.topic)
    elif args.command == "create-task":
        task_repository = create_task_repository_for_cli(args.directory)
        task, task_path = create_defense_task(
            topic=args.topic,
            directory=args.directory,
            task_repository=task_repository,
        )

        print("TASK CREATED")
        print(f"TASK ID: {task.task_id}")
        print(f"TOPIC: {task.topic}")
        print(f"STATUS: {task.status}")
        print(f"SAVED: {task_path}")

    elif args.command == "start-task-step":
        try:
            step_input = parse_json_argument(
                args.input,
                "--input",
            )
        except ValueError as error:
            print(f"ARGUMENT ERROR: {error}")
            raise SystemExit(2) from error

        task_repository = create_task_repository_for_cli(args.directory)
        task, step, task_path = start_next_task_step(
            task_id=args.task_id,
            directory=args.directory,
            input=step_input,
            task_repository=task_repository,
        )

        print("TASK UPDATED")
        print(f"TASK ID: {task.task_id}")
        print(f"STATUS: {task.status}")

        if step is None:
            print("STEP: None")
            print("REASON: 当前步骤尚未完成，不能开始下一步")
        else:
            print(f"STEP ID: {step.step_id}")
            print(f"STEP TYPE: {step.step_type}")
            print(f"STEP STATUS: {step.status}")

        print(f"SAVED: {task_path}")

    elif args.command == "complete-task-step":
        try:
            step_output = parse_json_argument(
                args.output,
                "--output",
            )
        except ValueError as error:
            print(f"ARGUMENT ERROR: {error}")
            raise SystemExit(2) from error

        try:
            task_repository = create_task_repository_for_cli(args.directory)
            task, step, task_path = complete_task_step(
                task_id=args.task_id,
                directory=args.directory,
                output=step_output,
                task_repository=task_repository,
            )
        except ValueError as error:
            print(f"TASK ERROR: {error}")
            raise SystemExit(1) from error

        print("TASK STEP COMPLETED")
        print(f"TASK ID: {task.task_id}")
        print(f"STATUS: {task.status}")
        print(f"STEP ID: {step.step_id}")
        print(f"STEP TYPE: {step.step_type}")
        print(f"STEP STATUS: {step.status}")
        print(f"SAVED: {task_path}")

    elif args.command == "execute-task-step":
        try:
            task_repository = create_task_repository_for_cli(args.directory)
            task, step, task_path = execute_current_task_step(
                task_id=args.task_id,
                directory=args.directory,
                long_term_memory_path=LONG_TERM_MEMORY_PATH,
                task_repository=task_repository,
            )
        except ValueError as error:
            print(f"TASK ERROR: {error}")
            raise SystemExit(1) from error

        print("TASK STEP EXECUTED")
        print(f"TASK ID: {task.task_id}")
        print(f"STATUS: {task.status}")
        print(f"STEP ID: {step.step_id}")
        print(f"STEP TYPE: {step.step_type}")
        print(f"STEP STATUS: {step.status}")

        if "query" in step.output:
            print(f"QUERY: {step.output['query']}")

        if "sources" in step.output:
            print(f"SOURCE COUNT: {len(step.output['sources'])}")

        print(f"SAVED: {task_path}")

    elif args.command == "resume-task":
        task_repository = create_task_repository_for_cli(args.directory)
        task = get_defense_task(
            task_id=args.task_id,
            directory=args.directory,
            task_repository=task_repository,
        )
        status = get_resumable_task_status(task)

        print("TASK RESUME STATUS")
        print(f"TASK ID: {task.task_id}")
        print(f"TASK STATUS: {status.task_status}")
        print(f"ACTION: {status.action}")
        print(f"CURRENT STEP ID: {status.current_step_id}")
        print(f"CURRENT STEP TYPE: {status.current_step_type}")
        print(f"CURRENT STEP STATUS: {status.current_step_status}")
        print(f"NEXT STEP TYPE: {status.next_step_type}")
        print(
            "CAN EXECUTE CURRENT STEP:",
            status.can_execute_current_step,
        )
        print("NEEDS HUMAN INPUT:", status.needs_human_input)
        print(f"MESSAGE: {status.message}")

    elif args.command == "analyze-task":
        task_repository = create_task_repository_for_cli(args.directory)
        task = get_defense_task(
            task_id=args.task_id,
            directory=args.directory,
            task_repository=task_repository,
        )
        report = analyze_task_trace(task)

        print("TASK TRACE SUMMARY")
        print(f"TASK ID: {report['task_id']}")
        print(f"TOPIC: {report['topic']}")
        print(f"STATUS: {report['status']}")
        print(f"CURRENT STEP ID: {report['current_step_id']}")
        print(f"CURRENT STEP TYPE: {report['current_step_type']}")
        print(f"CURRENT STEP STATUS: {report['current_step_status']}")
        print(f"STEP COUNT: {report['step_count']}")
        print(f"COMPLETED STEPS: {report['completed_step_count']}")
        print(f"FAILED STEPS: {report['failed_step_count']}")
        print(f"PENDING STEPS: {report['pending_step_count']}")
        print(f"RUNNING STEPS: {report['running_step_count']}")
        print(f"TOOL CALLS: {report['tool_call_count']}")
        print(
            "SUCCESSFUL TOOL CALLS:",
            report["successful_tool_call_count"],
        )
        print("FAILED TOOL CALLS:", report["failed_tool_call_count"])
        print(
            "TOTAL DURATION MS:",
            round(report["total_duration_ms"], 2),
        )
        print("TOTAL PROMPT TOKENS:", report["total_prompt_tokens"])
        print(
            "TOTAL COMPLETION TOKENS:",
            report["total_completion_tokens"],
        )
        print("TOTAL TOKENS:", report["total_tokens"])
        print("TOTAL COST:", round(report["total_cost"], 6))
        print("CURRENCY:", report["currency"])
        print("EVIDENCE COUNT:", report["evidence_count"])

    elif args.command == "submit-task-answer":
        try:
            task_repository = create_task_repository_for_cli(args.directory)
            task, step, task_path = submit_task_answer(
                task_id=args.task_id,
                answer=args.answer,
                directory=args.directory,
                task_repository=task_repository,
            )
        except ValueError as error:
            print(f"TASK ERROR: {error}")
            raise SystemExit(1) from error

        print("TASK ANSWER SUBMITTED")
        print(f"TASK ID: {task.task_id}")
        print(f"STATUS: {task.status}")
        print(f"STEP ID: {step.step_id}")
        print(f"STEP TYPE: {step.step_type}")
        print(f"STEP STATUS: {step.status}")
        print(f"ANSWER: {step.output['answer']}")
        print(f"SAVED: {task_path}")

    elif args.command == "submit-follow-up-answer":
        try:
            task_repository = create_task_repository_for_cli(args.directory)
            task, step, task_path = submit_follow_up_answer(
                task_id=args.task_id,
                answer=args.answer,
                directory=args.directory,
                task_repository=task_repository,
            )
        except ValueError as error:
            print(f"TASK ERROR: {error}")
            raise SystemExit(1) from error

        print("TASK FOLLOW-UP ANSWER SUBMITTED")
        print(f"TASK ID: {task.task_id}")
        print(f"STATUS: {task.status}")
        print(f"STEP ID: {step.step_id}")
        print(f"STEP TYPE: {step.step_type}")
        print(f"STEP STATUS: {step.status}")
        print(f"FOLLOW-UP ANSWER: {step.output['follow_up_answer']}")
        print(f"SAVED: {task_path}")

    elif args.command == "export-task-markdown":
        task_repository = create_task_repository_for_cli(args.directory)
        task = get_defense_task(
            task_id=args.task_id,
            directory=args.directory,
            task_repository=task_repository,
        )

        report_path = export_task_markdown_report(
            task,
            output_path=args.output,
        )

        print("TASK MARKDOWN EXPORTED")
        print(f"TASK ID: {task.task_id}")
        print(f"STATUS: {task.status}")
        print(f"REPORT: {report_path}")

    elif args.command == "export-task-memory":
        try:
            task_repository = create_task_repository_for_cli(args.directory)
            task = get_defense_task(
                task_id=args.task_id,
                directory=args.directory,
                task_repository=task_repository,
            )
            report = export_task_to_long_term_memory(
                task=task,
                memory_path=args.memory_path,
            )
        except (FileNotFoundError, ValueError) as error:
            print(f"TASK MEMORY EXPORT ERROR: {error}")
            raise SystemExit(1) from error

        print("TASK MEMORY EXPORTED")
        print(f"TASK ID: {report['task_id']}")
        print(f"TOPIC: {report['topic']}")
        print(f"MEMORY PATH: {report['memory_path']}")
        print(f"SUMMARY EXPORTED: {report['summary_exported']}")
        print(f"WEAKNESS COUNT: {report['weakness_count']}")

        for weakness in report["weaknesses"]:
            print(f"WEAKNESS: {weakness}")

    elif args.command == "graph-demo-task":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K

        try:
            result = run_demo_task(
                topic=args.topic,
                top_k=top_k,
            )
        except ValueError as error:
            print(f"LANGGRAPH DEMO ERROR: {error}")
            raise SystemExit(1) from error

        print("LANGGRAPH DEMO TASK")
        print("TOPIC:", result.get("topic"))
        print("STATUS:", result.get("status"))
        print("CURRENT NODE:", result.get("current_node"))
        print("NEEDS HUMAN INPUT:", result.get("needs_human_input"))
        print("QUERY:", result.get("query"))
        print("SOURCE COUNT:", len(result.get("sources", [])))
        print("QUESTION:", result.get("question"))

    elif args.command == "graph-interrupt-demo":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K

        try:
            graph = build_interrupt_demo_graph(top_k=top_k)
            interrupted_result = start_interrupt_demo(
                graph=graph,
                topic=args.topic,
                thread_id=args.thread_id,
            )
            interrupt_payload = get_interrupt_payload(interrupted_result)
        except ValueError as error:
            print(f"LANGGRAPH INTERRUPT ERROR: {error}")
            raise SystemExit(1) from error

        print("LANGGRAPH INTERRUPT DEMO")
        print("THREAD ID:", args.thread_id)
        print("TOPIC:", interrupted_result.get("topic"))
        print("INTERRUPTED:", interrupt_payload is not None)

        if interrupt_payload is not None:
            print("INTERRUPT TYPE:", interrupt_payload.get("type"))
            print("QUESTION:", interrupt_payload.get("question"))
            print("MESSAGE:", interrupt_payload.get("message"))

        if args.answer is not None:
            try:
                resumed_result = resume_interrupt_demo(
                    graph=graph,
                    thread_id=args.thread_id,
                    answer=args.answer,
                )
            except ValueError as error:
                print(f"LANGGRAPH INTERRUPT ERROR: {error}")
                raise SystemExit(1) from error

            print("RESUMED:", True)
            print("STATUS:", resumed_result.get("status"))
            print("CURRENT NODE:", resumed_result.get("current_node"))
            print("ANSWER:", resumed_result.get("answer"))
        else:
            print("RESUMED:", False)
            print(
                "NOTE:",
                "This demo uses an in-memory checkpointer; pass --answer "
                "in the same command to demonstrate resume.",
            )

    elif args.command == "graph-checkpointer-demo":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K

        try:
            report = run_checkpointer_demo(
                topic=args.topic,
                thread_id=args.thread_id,
                answer=args.answer,
                top_k=top_k,
            )
        except ValueError as error:
            print(f"LANGGRAPH CHECKPOINTER ERROR: {error}")
            raise SystemExit(1) from error

        interrupted_checkpoint = report["interrupted_checkpoint"]
        resumed_checkpoint = report["resumed_checkpoint"]

        print("LANGGRAPH CHECKPOINTER DEMO")
        print("THREAD ID:", report["thread_id"])
        print("CHECKPOINTER TYPE:", report["checkpointer_type"])
        print(
            "INTERRUPT TYPE:",
            (report["interrupt_payload"] or {}).get("type"),
        )
        print(
            "QUESTION:",
            (report["interrupt_payload"] or {}).get("question"),
        )
        print("INTERRUPTED CHECKPOINT ID:", interrupted_checkpoint["checkpoint_id"])
        print("INTERRUPTED NEXT:", interrupted_checkpoint["next"])
        print(
            "INTERRUPTED HAS PENDING INTERRUPT:",
            interrupted_checkpoint["has_pending_interrupt"],
        )
        print(
            "INTERRUPTED VALUE KEYS:",
            sorted(interrupted_checkpoint["values"].keys()),
        )

        if resumed_checkpoint is None:
            print("RESUMED:", False)
            print(
                "NOTE:",
                "Pass --answer to resume and inspect the next checkpoint.",
            )
        else:
            print("RESUMED:", True)
            print("RESUMED CHECKPOINT ID:", resumed_checkpoint["checkpoint_id"])
            print("RESUMED NEXT:", resumed_checkpoint["next"])
            print(
                "RESUMED HAS PENDING INTERRUPT:",
                resumed_checkpoint["has_pending_interrupt"],
            )
            print("ANSWER:", report["resumed_result"].get("answer"))
            print(
                "RESUMED VALUE KEYS:",
                sorted(resumed_checkpoint["values"].keys()),
            )

    elif args.command == "graph-persistent-checkpoint-demo":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K

        try:
            result = run_persistent_checkpoint_demo(
                topic=args.topic,
                thread_id=args.thread_id,
                output_path=args.output,
                answer=args.answer,
                top_k=top_k,
            )
        except ValueError as error:
            print(f"LANGGRAPH PERSISTENT CHECKPOINT ERROR: {error}")
            raise SystemExit(1) from error

        summary = result["summary"]

        print("LANGGRAPH PERSISTENT CHECKPOINT DEMO")
        print("THREAD ID:", summary["thread_id"])
        print("CHECKPOINTER TYPE:", summary["checkpointer_type"])
        print("SNAPSHOT PATH:", result["snapshot_path"])
        print("INTERRUPTED NEXT:", summary["interrupted_next"])
        print(
            "INTERRUPTED HAS PENDING INTERRUPT:",
            summary["interrupted_has_pending_interrupt"],
        )
        print(
            "INTERRUPTED VALUE KEYS:",
            summary["interrupted_value_keys"],
        )
        print("HAS RESUMED:", summary["has_resumed"])

        if summary["has_resumed"]:
            print("RESUMED NEXT:", summary["resumed_next"])
            print(
                "RESUMED HAS PENDING INTERRUPT:",
                summary["resumed_has_pending_interrupt"],
            )
            print("RESUMED VALUE KEYS:", summary["resumed_value_keys"])

    elif args.command == "graph-conditional-demo":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K

        try:
            report = run_conditional_demo(
                topic=args.topic,
                thread_id=args.thread_id,
                answer=args.answer,
                resume_answer=args.resume_answer,
                top_k=top_k,
            )
        except ValueError as error:
            print(f"LANGGRAPH CONDITIONAL ERROR: {error}")
            raise SystemExit(1) from error

        first_result = report["first_result"]
        interrupt_payload = report["interrupt_payload"]
        resumed_result = report["resumed_result"]

        print("LANGGRAPH CONDITIONAL DEMO")
        print("THREAD ID:", report["thread_id"])
        print("ROUTE:", report["route"])
        print("FIRST STATUS:", first_result.get("status"))
        print("FIRST CURRENT NODE:", first_result.get("current_node"))
        print("QUESTION:", first_result.get("question"))
        print("INTERRUPTED:", interrupt_payload is not None)

        if interrupt_payload is not None:
            print("INTERRUPT TYPE:", interrupt_payload.get("type"))
            print("INTERRUPT QUESTION:", interrupt_payload.get("question"))

        if resumed_result is None:
            print("RESUMED:", False)
        else:
            print("RESUMED:", True)
            print("RESUMED STATUS:", resumed_result.get("status"))
            print("RESUMED CURRENT NODE:", resumed_result.get("current_node"))
            print("ANSWER:", resumed_result.get("answer"))

    elif args.command == "graph-evaluate-rewrite-demo":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K

        try:
            report = run_evaluate_rewrite_demo(
                topic=args.topic,
                thread_id=args.thread_id,
                answer=args.answer,
                top_k=top_k,
            )
        except ValueError as error:
            print(f"LANGGRAPH EVALUATE REWRITE ERROR: {error}")
            raise SystemExit(1) from error

        interrupted_result = report["interrupted_result"]
        interrupt_payload = report["interrupt_payload"]
        resumed_result = report["resumed_result"]

        print("LANGGRAPH EVALUATE REWRITE DEMO")
        print("THREAD ID:", report["thread_id"])
        print("QUESTION:", interrupted_result.get("question"))
        print("INTERRUPTED:", interrupt_payload is not None)

        if interrupt_payload is not None:
            print("INTERRUPT TYPE:", interrupt_payload.get("type"))
            print("INTERRUPT QUESTION:", interrupt_payload.get("question"))

        if resumed_result is None:
            print("RESUMED:", False)
        else:
            print("RESUMED:", True)
            print("STATUS:", resumed_result.get("status"))
            print("CURRENT NODE:", resumed_result.get("current_node"))
            print("ANSWER:", resumed_result.get("answer"))
            print("EVALUATION:", resumed_result.get("evaluation"))
            print("REWRITTEN ANSWER:", resumed_result.get("rewritten_answer"))

    elif args.command == "graph-follow-up-demo":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K

        try:
            report = run_follow_up_demo(
                topic=args.topic,
                thread_id=args.thread_id,
                answer=args.answer,
                follow_up_answer=args.follow_up_answer,
                top_k=top_k,
            )
        except ValueError as error:
            print(f"LANGGRAPH FOLLOW UP ERROR: {error}")
            raise SystemExit(1) from error

        answer_interrupt = report["answer_interrupt_payload"]
        answer_result = report["answer_result"]
        follow_up_interrupt = report["follow_up_interrupt_payload"]
        final_result = report["final_result"]

        print("LANGGRAPH FOLLOW UP DEMO")
        print("THREAD ID:", report["thread_id"])
        print("ANSWER INTERRUPTED:", answer_interrupt is not None)

        if answer_interrupt is not None:
            print("ANSWER INTERRUPT TYPE:", answer_interrupt.get("type"))
            print("QUESTION:", answer_interrupt.get("question"))

        if answer_result is None:
            print("ANSWER RESUMED:", False)
        else:
            print("ANSWER RESUMED:", True)
            print("ANSWER:", answer_result.get("answer"))
            print("EVALUATION:", answer_result.get("evaluation"))
            print("REWRITTEN ANSWER:", answer_result.get("rewritten_answer"))
            print(
                "FOLLOW UP QUESTION:",
                answer_result.get("follow_up_question"),
            )

        print("FOLLOW UP INTERRUPTED:", follow_up_interrupt is not None)

        if follow_up_interrupt is not None:
            print(
                "FOLLOW UP INTERRUPT TYPE:",
                follow_up_interrupt.get("type"),
            )
            print(
                "FOLLOW UP INTERRUPT QUESTION:",
                follow_up_interrupt.get("question"),
            )

        if final_result is None:
            print("FOLLOW UP RESUMED:", False)
        else:
            print("FOLLOW UP RESUMED:", True)
            print("STATUS:", final_result.get("status"))
            print("CURRENT NODE:", final_result.get("current_node"))
            print("FOLLOW UP ANSWER:", final_result.get("follow_up_answer"))
            print(
                "FOLLOW UP EVALUATION:",
                final_result.get("follow_up_evaluation"),
            )

    elif args.command == "graph-summary-demo":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K

        try:
            report = run_summary_demo(
                topic=args.topic,
                thread_id=args.thread_id,
                answer=args.answer,
                follow_up_answer=args.follow_up_answer,
                top_k=top_k,
            )
        except ValueError as error:
            print(f"LANGGRAPH SUMMARY ERROR: {error}")
            raise SystemExit(1) from error

        answer_interrupt = report["answer_interrupt_payload"]
        answer_result = report["answer_result"]
        follow_up_interrupt = report["follow_up_interrupt_payload"]
        final_result = report["final_result"]

        print("LANGGRAPH SUMMARY DEMO")
        print("THREAD ID:", report["thread_id"])
        print("ANSWER INTERRUPTED:", answer_interrupt is not None)

        if answer_interrupt is not None:
            print("ANSWER INTERRUPT TYPE:", answer_interrupt.get("type"))
            print("QUESTION:", answer_interrupt.get("question"))

        if answer_result is None:
            print("ANSWER RESUMED:", False)
        else:
            print("ANSWER RESUMED:", True)
            print("ANSWER:", answer_result.get("answer"))
            print("EVALUATION:", answer_result.get("evaluation"))
            print("REWRITTEN ANSWER:", answer_result.get("rewritten_answer"))
            print(
                "FOLLOW UP QUESTION:",
                answer_result.get("follow_up_question"),
            )

        print("FOLLOW UP INTERRUPTED:", follow_up_interrupt is not None)

        if follow_up_interrupt is not None:
            print(
                "FOLLOW UP INTERRUPT TYPE:",
                follow_up_interrupt.get("type"),
            )
            print(
                "FOLLOW UP INTERRUPT QUESTION:",
                follow_up_interrupt.get("question"),
            )

        if final_result is None:
            print("SUMMARY COMPLETED:", False)
        else:
            print("SUMMARY COMPLETED:", True)
            print("STATUS:", final_result.get("status"))
            print("CURRENT NODE:", final_result.get("current_node"))
            print("FOLLOW UP ANSWER:", final_result.get("follow_up_answer"))
            print(
                "FOLLOW UP EVALUATION:",
                final_result.get("follow_up_evaluation"),
            )
            print("SUMMARY:", final_result.get("summary"))

    elif args.command == "graph-task-parity":
        report = build_langgraph_task_parity_report()

        print("LANGGRAPH TASK PARITY")
        print("PASSED:", report["passed"])
        print("ORDER MATCHES:", report["order_matches"])
        print("TASK CONTRACT STEPS:", report["task_contract_steps"])
        print("LANGGRAPH STEPS:", report["langgraph_steps"])
        print("MAPPED LANGGRAPH STEPS:", report["mapped_langgraph_steps"])
        print("MISSING STEPS:", report["missing_steps"])
        print("EXTRA STEPS:", report["extra_steps"])

    elif args.command == "list-tools":
        tools = list_registered_tools(
            include_disabled=args.include_disabled,
        )

        print("REGISTERED TOOLS")
        print("COUNT:", len(tools))

        for tool in tools:
            print("-" * 40)
            print("NAME:", tool.name)
            print("PERMISSION:", tool.permission)
            print("OWNER:", tool.owner)
            print("ENABLED:", tool.enabled)
            print("TIMEOUT_SECONDS:", tool.timeout_seconds)
            print("RETRY_COUNT:", tool.retry_count)
            print("RESULT_MAX_CHARACTERS:", tool.result_max_characters)
            print("DESCRIPTION:", tool.description)

    elif args.command == "list-sub-agents":
        specs = list_sub_agent_specs()

        print("SUB-AGENT SPECS")
        print("COUNT:", len(specs))

        for spec in specs:
            print("-" * 40)
            print("NAME:", spec.name)
            print("ROLE:", spec.role)
            print("MAX_STEPS:", spec.max_steps)
            print("ALLOWED_TOOLS:", spec.allowed_tools)
            print("INPUT_FIELDS:", spec.input_fields)
            print("OUTPUT_FIELDS:", spec.output_fields)
            print("DESCRIPTION:", spec.description)

    elif args.command == "check-sub-agent-tool":
        try:
            result = check_sub_agent_tool_permission(
                sub_agent_name=args.sub_agent,
                tool_name=args.tool,
            )
        except ValueError as error:
            print(f"SUB-AGENT TOOL CHECK ERROR: {error}")
            raise SystemExit(1) from error

        print("SUB-AGENT TOOL CHECK")
        print("SUB_AGENT:", result.sub_agent_name)
        print("TOOL:", result.tool_name)
        print("ALLOWED:", result.allowed)
        print("REASON:", result.reason)
        print("ALLOWED_TOOLS:", result.allowed_tools)

    elif args.command == "plan-sub-agent-call":
        try:
            if args.arguments is not None:
                tool_arguments = parse_json_argument(
                    args.arguments,
                    "--arguments",
                )
            else:
                tool_arguments = parse_key_value_arguments(
                    args.argument,
                )

            if not tool_arguments:
                raise ValueError(
                    "必须提供 --arguments JSON 或至少一个 --argument KEY=VALUE"
                )

            plan = create_sub_agent_execution_plan(
                sub_agent_name=args.sub_agent,
                tool_name=args.tool,
                tool_arguments=tool_arguments,
            )
        except ValueError as error:
            print(f"SUB-AGENT PLAN ERROR: {error}")
            raise SystemExit(1) from error

        print("SUB-AGENT EXECUTION PLAN")
        print("PLAN ID:", plan.plan_id)
        print("SUB_AGENT:", plan.sub_agent_name)
        print("ROLE:", plan.role)
        print("TOOL:", plan.tool_name)
        print("TOOL_ARGUMENTS:", json.dumps(
            plan.tool_arguments,
            ensure_ascii=False,
        ))
        print("EXPECTED_OUTPUT_FIELDS:", plan.expected_output_fields)
        print("MAX_STEPS:", plan.max_steps)
        print("STATUS:", plan.status)

        if args.save_trace:
            trace_repository = create_trace_repository_for_cli(
                args.trace_file,
            )
            trace_path = save_sub_agent_plan_trace(
                plan,
                file_path=args.trace_file,
                trace_repository=trace_repository,
            )
            print("TRACE SAVED:", trace_path)

    elif args.command == "analyze-sub-agent-plans":
        trace_repository = create_trace_repository_for_cli(args.file)
        records = load_sub_agent_plan_traces(
            args.file,
            trace_repository=trace_repository,
        )
        summary = summarize_sub_agent_plan_traces(records)

        print("SUB-AGENT PLAN TRACE SUMMARY")
        print("FILE:", args.file)
        print("TOTAL:", summary["total"])
        print("BY_SUB_AGENT:", summary["by_sub_agent"])
        print("BY_TOOL:", summary["by_tool"])

    elif args.command == "compare-sub-agent-plans":
        baseline_records = load_sub_agent_plan_traces(args.baseline)
        candidate_records = load_sub_agent_plan_traces(args.candidate)
        report = compare_sub_agent_plan_records(
            baseline_records=baseline_records,
            candidate_records=candidate_records,
        )

        print("SUB-AGENT PLAN COMPARISON")
        print("BASELINE:", args.baseline)
        print("CANDIDATE:", args.candidate)
        print("BASELINE COUNT:", report["baseline_count"])
        print("CANDIDATE COUNT:", report["candidate_count"])
        print("ADDED:", report["added_count"])
        print("REMOVED:", report["removed_count"])
        print("CHANGED:", report["changed_count"])
        print("STABLE:", report["stable_count"])
        print("PASSED:", report["passed"])

        if report["added"]:
            print("ADDED ITEMS:", json.dumps(
                report["added"],
                ensure_ascii=False,
            ))

        if report["removed"]:
            print("REMOVED ITEMS:", json.dumps(
                report["removed"],
                ensure_ascii=False,
            ))

        if report["changed"]:
            print("CHANGED ITEMS:", json.dumps(
                report["changed"],
                ensure_ascii=False,
            ))

    elif args.command == "dry-run-sub-agent-call":
        try:
            if args.arguments is not None:
                tool_arguments = parse_json_argument(
                    args.arguments,
                    "--arguments",
                )
            else:
                tool_arguments = parse_key_value_arguments(
                    args.argument,
                )

            if not tool_arguments:
                raise ValueError(
                    "must provide --arguments JSON or at least one "
                    "--argument KEY=VALUE"
                )

            report = dry_run_sub_agent_tool_call(
                sub_agent_name=args.sub_agent,
                tool_name=args.tool,
                tool_arguments=tool_arguments,
                save_trace=args.save_trace,
                trace_file=args.trace_file,
                trace_repository=(
                    create_trace_repository_for_cli(args.trace_file)
                    if args.save_trace
                    else None
                ),
            )
        except ValueError as error:
            print(f"SUB-AGENT DRY-RUN ERROR: {error}")
            raise SystemExit(1) from error

        print("SUB-AGENT DRY-RUN")
        print("SUB_AGENT:", report.sub_agent_name)
        print("TOOL:", report.tool_name)
        print("ALLOWED:", report.allowed)
        print("WILL_EXECUTE:", report.will_execute)
        print("PLAN_ID:", report.plan.plan_id)
        print("TOOL_ARGUMENTS:", json.dumps(
            report.plan.tool_arguments,
            ensure_ascii=False,
        ))
        print(
            "EXPECTED_OUTPUT_FIELDS:",
            report.plan.expected_output_fields,
        )
        print("MAX_STEPS:", report.plan.max_steps)
        print("TRACE_SAVED:", report.trace_saved)

        if report.trace_path is not None:
            print("TRACE PATH:", report.trace_path)

        print("REASON:", report.reason)

    elif args.command == "execute-sub-agent-call":
        try:
            if args.arguments is not None:
                tool_arguments = parse_json_argument(
                    args.arguments,
                    "--arguments",
                )
            else:
                tool_arguments = parse_key_value_arguments(
                    args.argument,
                )

            if not tool_arguments:
                raise ValueError(
                    "must provide --arguments JSON or at least one "
                    "--argument KEY=VALUE"
                )

            result = execute_sub_agent_tool_call(
                sub_agent_name=args.sub_agent,
                tool_name=args.tool,
                tool_arguments=tool_arguments,
                save_trace=args.save_trace,
                trace_file=args.trace_file,
                trace_repository=(
                    create_trace_repository_for_cli(args.trace_file)
                    if args.save_trace
                    else None
                ),
            )
        except ValueError as error:
            print(f"SUB-AGENT EXECUTION ERROR: {error}")
            raise SystemExit(1) from error

        print("SUB-AGENT EXECUTION")
        print("SUB_AGENT:", result.sub_agent_name)
        print("TOOL:", result.tool_name)
        print("SUCCESS:", result.success)
        print("PLAN_ID:", result.plan.plan_id)
        print("TOOL_ARGUMENTS:", json.dumps(
            result.plan.tool_arguments,
            ensure_ascii=False,
        ))
        print("DURATION_MS:", result.duration_ms)
        print("TRACE_SAVED:", result.trace_saved)

        if result.trace_path is not None:
            print("TRACE PATH:", result.trace_path)

        print("RESULT:", result.result_text)

    elif args.command == "analyze-sub-agent-executions":
        trace_repository = create_trace_repository_for_cli(args.file)
        records = load_sub_agent_execution_traces(
            args.file,
            trace_repository=trace_repository,
        )
        summary = summarize_sub_agent_execution_traces(records)

        print("SUB-AGENT EXECUTION TRACE SUMMARY")
        print("FILE:", args.file)
        print("TOTAL:", summary["total"])
        print("SUCCESSFUL:", summary["successful"])
        print("FAILED:", summary["failed"])
        print("BY_SUB_AGENT:", summary["by_sub_agent"])
        print("BY_TOOL:", summary["by_tool"])

    elif args.command == "compare-sub-agent-executions":
        try:
            baseline_records = load_sub_agent_execution_traces(
                args.baseline
            )
            candidate_records = load_sub_agent_execution_traces(
                args.candidate
            )
            report = compare_sub_agent_execution_records(
                baseline_records=baseline_records,
                candidate_records=candidate_records,
                max_duration_ratio=args.max_duration_ratio,
            )
        except ValueError as error:
            print(f"SUB-AGENT EXECUTION COMPARISON ERROR: {error}")
            raise SystemExit(1) from error

        print("SUB-AGENT EXECUTION COMPARISON")
        print("BASELINE:", args.baseline)
        print("CANDIDATE:", args.candidate)
        print("BASELINE COUNT:", report["baseline_count"])
        print("CANDIDATE COUNT:", report["candidate_count"])
        print("ADDED:", report["added_count"])
        print("REMOVED:", report["removed_count"])
        print("CHANGED:", report["changed_count"])
        print(
            "DURATION REGRESSIONS:",
            report["duration_regression_count"],
        )
        print("STABLE:", report["stable_count"])
        print("PASSED:", report["passed"])

        if report["added"]:
            print("ADDED ITEMS:", json.dumps(
                report["added"],
                ensure_ascii=False,
            ))

        if report["removed"]:
            print("REMOVED ITEMS:", json.dumps(
                report["removed"],
                ensure_ascii=False,
            ))

        if report["changed"]:
            print("CHANGED ITEMS:", json.dumps(
                report["changed"],
                ensure_ascii=False,
            ))

        if report["duration_regressions"]:
            print("DURATION REGRESSION ITEMS:", json.dumps(
                report["duration_regressions"],
                ensure_ascii=False,
            ))

        if not report["passed"] and not args.allow_fail:
            raise SystemExit(1)

    elif args.command == "local-quality-gate":
        try:
            report = run_local_quality_gate(
                run_pytest=not args.skip_pytest,
                sub_agent_execution_baseline=(
                    args.sub_agent_execution_baseline
                ),
                sub_agent_execution_candidate=(
                    args.sub_agent_execution_candidate
                ),
                max_duration_ratio=args.max_duration_ratio,
            )
        except ValueError as error:
            print(f"LOCAL QUALITY GATE ERROR: {error}")
            raise SystemExit(1) from error

        print("LOCAL QUALITY GATE")
        print("PASSED:", report.passed)

        for check in report.checks:
            print("-" * 40)
            print("CHECK:", check.name)
            print("PASSED:", check.passed)
            print("SUMMARY:", check.summary)

        if args.output is not None:
            output_path = save_local_quality_gate_report(
                report,
                args.output,
            )
            print("OUTPUT:", output_path)

        if args.markdown_output is not None:
            markdown_path = save_local_quality_gate_markdown(
                report,
                args.markdown_output,
            )
            print("MARKDOWN OUTPUT:", markdown_path)

        if not report.passed and not args.allow_fail:
            raise SystemExit(1)

    elif args.command == "server-long-run-preflight":
        try:
            report = build_server_long_run_preflight(
                environment=args.environment,
                runtime=args.runtime,
                operator=args.operator,
            )
            markdown = render_server_long_run_preflight_report(report)
        except ValueError as error:
            print(f"SERVER LONG RUN PREFLIGHT ERROR: {error}")
            raise SystemExit(2) from error

        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "k8s-smoke-plan":
        try:
            plan = build_k8s_smoke_plan(
                namespace=args.namespace,
                kustomize_dir=args.kustomize_dir,
                api_local_port=args.api_local_port,
            )
        except ValueError as error:
            print(f"K8S SMOKE PLAN ERROR: {error}")
            raise SystemExit(2) from error

        markdown = render_k8s_smoke_plan(plan)
        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "k8s-smoke-report-template":
        try:
            plan = build_k8s_smoke_plan(
                namespace=args.namespace,
                kustomize_dir=args.kustomize_dir,
                api_local_port=args.api_local_port,
            )
            markdown = render_k8s_smoke_report_template(
                plan,
                environment=args.environment,
                operator=args.operator,
            )
        except ValueError as error:
            print(f"K8S SMOKE REPORT TEMPLATE ERROR: {error}")
            raise SystemExit(2) from error

        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "k8s-smoke-run":
        try:
            plan = build_k8s_smoke_plan(
                namespace=args.namespace,
                kustomize_dir=args.kustomize_dir,
                api_local_port=args.api_local_port,
            )
            report = execute_k8s_smoke_plan(
                plan,
                apply_cluster=args.apply_cluster,
                include_port_forward=args.include_port_forward,
                include_rollback=args.include_rollback,
                timeout_seconds=args.timeout_seconds,
            )
        except (OSError, TimeoutError, ValueError) as error:
            print(f"K8S SMOKE RUN ERROR: {error}")
            raise SystemExit(2) from error

        markdown = render_k8s_smoke_run_report(report)
        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

        if report.overall_status == "failed" and not args.allow_fail:
            raise SystemExit(1)

    elif args.command == "postgres-migrations":
        try:
            if args.directory is None:
                plan = build_postgres_migration_plan()
            else:
                plan = build_postgres_migration_plan(args.directory)
        except (FileNotFoundError, ValueError) as error:
            print(f"POSTGRES MIGRATION ERROR: {error}")
            raise SystemExit(1) from error

        print("POSTGRES MIGRATION PLAN")
        print("COUNT:", len(plan))

        for migration in plan:
            print("-" * 40)
            print("VERSION:", migration["version"])
            print("NAME:", migration["name"])
            print("PATH:", migration["path"])
            print("CHECKSUM:", migration["checksum"])

    elif args.command == "run-postgres-migrations":
        database_url = args.database_url or DATABASE_URL

        if not database_url:
            print(
                "POSTGRES MIGRATION ERROR: DATABASE_URL is required. "
                "Set DATABASE_URL or pass --database-url."
            )
            raise SystemExit(1)

        try:
            if args.directory is None:
                report = run_postgres_migrations(database_url)
            else:
                report = run_postgres_migrations(
                    database_url,
                    migrations_directory=args.directory,
                )
        except (FileNotFoundError, ValueError, RuntimeError) as error:
            print(f"POSTGRES MIGRATION ERROR: {error}")
            raise SystemExit(1) from error

        print("POSTGRES MIGRATION RUN")
        print("DATABASE URL: configured")
        print("TOTAL:", report.total_count)
        print("APPLIED:", report.applied_count)
        print("SKIPPED:", report.skipped_count)

        if report.applied:
            print("APPLIED MIGRATIONS:", json.dumps(
                report.applied,
                ensure_ascii=False,
            ))

        if report.skipped:
            print("SKIPPED MIGRATIONS:", json.dumps(
                report.skipped,
                ensure_ascii=False,
            ))

    elif args.command == "show-repositories":
        database_url = (
            args.database_url
            if args.database_url is not None
            else DATABASE_URL
        )

        try:
            repositories = create_repositories(
                storage_backend=args.storage_backend,
                database_url=database_url,
            )
        except ValueError as error:
            print(f"REPOSITORY CONFIG ERROR: {error}")
            raise SystemExit(1) from error

        print("REPOSITORY CONFIG")
        print("STORAGE BACKEND:", repositories.storage_backend)
        print(
            "TASK REPOSITORY:",
            type(repositories.task_repository).__name__,
        )
        print(
            "SESSION REPOSITORY:",
            type(repositories.session_repository).__name__,
        )
        print(
            "TRACE REPOSITORY:",
            type(repositories.trace_repository).__name__,
        )

    elif args.command == "import-vector-store-to-qdrant":
        try:
            store = load_vector_store(args.source)
            repository = QdrantVectorStoreRepository(
                url=args.url,
                collection_name=args.collection,
                vector_size=args.vector_size,
                distance=args.distance,
                api_key=(
                    args.api_key
                    if args.api_key is not None
                    else QDRANT_API_KEY
                ),
            )
            saved_identifier = repository.save(store)
        except (FileNotFoundError, ValueError, RuntimeError) as error:
            print(f"QDRANT IMPORT ERROR: {error}")
            raise SystemExit(1) from error

        print("QDRANT VECTOR STORE IMPORT")
        print("SOURCE:", args.source)
        print("QDRANT URL:", args.url)
        print("COLLECTION:", saved_identifier)
        print("VECTOR SIZE:", args.vector_size)
        print("DISTANCE:", args.distance)
        print("IMPORTED COUNT:", len(store))

    elif args.command == "import-vector-store-to-milvus":
        try:
            store = load_vector_store(args.source)
            repository = MilvusVectorStoreRepository(
                uri=args.uri,
                collection_name=args.collection,
                vector_size=args.vector_size,
                metric_type=args.metric_type,
                token=(
                    args.token
                    if args.token is not None
                    else MILVUS_TOKEN
                ),
            )
            saved_identifier = repository.save(store)
        except (FileNotFoundError, ValueError, RuntimeError) as error:
            print(f"MILVUS IMPORT ERROR: {error}")
            raise SystemExit(1) from error

        print("MILVUS VECTOR STORE IMPORT")
        print("SOURCE:", args.source)
        print("MILVUS URI:", args.uri)
        print("COLLECTION:", saved_identifier)
        print("VECTOR SIZE:", args.vector_size)
        print("METRIC TYPE:", args.metric_type)
        print("IMPORTED COUNT:", len(store))

    elif args.command == "milvus-backup-restore-plan":
        try:
            plan = build_milvus_backup_restore_plan(
                uri=args.uri,
                collection=args.collection,
                restore_collection=args.restore_collection,
                source=args.source,
                backup_dir=args.backup_dir,
                vector_size=args.vector_size,
                metric_type=args.metric_type,
                volume_name=args.volume_name,
                backup_file_name=args.backup_file_name,
            )
        except ValueError as error:
            print(f"MILVUS BACKUP RESTORE PLAN ERROR: {error}")
            raise SystemExit(2) from error

        markdown = render_milvus_backup_restore_plan(plan)
        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "milvus-restore-report-template":
        try:
            plan = build_milvus_backup_restore_plan(
                uri=args.uri,
                collection=args.collection,
                restore_collection=args.restore_collection,
                source=args.source,
                backup_dir=args.backup_dir,
                vector_size=args.vector_size,
                metric_type=args.metric_type,
                volume_name=args.volume_name,
                backup_file_name=args.backup_file_name,
            )
            markdown = render_milvus_restore_report_template(
                plan,
                environment=args.environment,
                operator=args.operator,
            )
        except ValueError as error:
            print(f"MILVUS RESTORE REPORT ERROR: {error}")
            raise SystemExit(2) from error

        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "compare-vector-store-backends":
        top_k = args.top_k if args.top_k is not None else RAG_TOP_K

        try:
            report = compare_vector_store_repositories(
                benchmark_path=RAG_BENCHMARK_PATH,
                vector_store_path=args.source,
                top_k=top_k,
                qdrant_url=args.url,
                qdrant_collection=args.collection,
                qdrant_vector_size=args.vector_size,
                qdrant_distance=args.distance,
                qdrant_api_key=(
                    args.api_key
                    if args.api_key is not None
                    else QDRANT_API_KEY
                ),
                include_milvus=args.include_milvus,
                milvus_uri=args.milvus_uri,
                milvus_collection=args.milvus_collection,
                milvus_vector_size=args.milvus_vector_size,
                milvus_metric_type=args.milvus_metric_type,
                milvus_token=(
                    args.milvus_token
                    if args.milvus_token is not None
                    else MILVUS_TOKEN
                ),
            )
        except (FileNotFoundError, ValueError, RuntimeError) as error:
            print(f"VECTOR STORE BACKEND COMPARISON ERROR: {error}")
            raise SystemExit(1) from error

        print("VECTOR STORE BACKEND COMPARISON")
        print("TOP_K:", report["top_k"])
        print("BEST REPOSITORY:", report["best_repository"])
        print(
            "SCORE DELTA QDRANT-JSON:",
            report["score_delta_qdrant_minus_json"],
        )
        print(
            "DURATION DELTA MS QDRANT-JSON:",
            report["duration_delta_ms_qdrant_minus_json"],
        )

        for repository_report in report["reports"]:
            print("-" * 40)
            print("REPOSITORY:", repository_report["repository"])
            print("AVERAGE SCORE:", repository_report["average_score"])
            print(
                "AVERAGE DURATION MS:",
                repository_report["average_duration_ms"],
            )
            print(
                "CACHE HITS:",
                repository_report["embedding_cache"]["hits"],
            )
            print(
                "CACHE MISSES:",
                repository_report["embedding_cache"]["misses"],
            )

            for item in repository_report["results"]:
                print(
                    f"QUERY: {item['query']} | "
                    f"SCORE: {item['score']} | "
                    f"DURATION_MS: {item['duration_ms']} | "
                    f"MISSING: {item['missing']}"
                )

        if args.output is not None:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(
                    report,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            print("REPORT SAVED:", output_path)

    elif args.command == "delete-qdrant-collection":
        if args.confirm_collection != args.collection:
            print(
                "QDRANT DELETE ERROR: --confirm-collection must exactly "
                "match --collection"
            )
            raise SystemExit(1)

        try:
            repository = QdrantVectorStoreRepository(
                url=args.url,
                collection_name=args.collection,
                vector_size=args.vector_size,
                distance=args.distance,
                api_key=(
                    args.api_key
                    if args.api_key is not None
                    else QDRANT_API_KEY
                ),
            )
            deleted = repository.delete_collection()
        except (ValueError, RuntimeError) as error:
            print(f"QDRANT DELETE ERROR: {error}")
            raise SystemExit(1) from error

        print("QDRANT COLLECTION DELETE")
        print("QDRANT URL:", args.url)
        print("COLLECTION:", args.collection)
        print("DELETED:", deleted)

    elif args.command == "delete-milvus-collection":
        if args.confirm_collection != args.collection:
            print(
                "MILVUS DELETE ERROR: --confirm-collection must exactly "
                "match --collection"
            )
            raise SystemExit(1)

        try:
            repository = MilvusVectorStoreRepository(
                uri=args.uri,
                collection_name=args.collection,
                vector_size=args.vector_size,
                metric_type=args.metric_type,
                token=(
                    args.token
                    if args.token is not None
                    else MILVUS_TOKEN
                ),
            )
            deleted = repository.delete_collection()
        except (ValueError, RuntimeError) as error:
            print(f"MILVUS DELETE ERROR: {error}")
            raise SystemExit(1) from error

        print("MILVUS COLLECTION DELETE")
        print("MILVUS URI:", args.uri)
        print("COLLECTION:", args.collection)
        print("DELETED:", deleted)

    elif args.command == "vector-db-governance-report":
        try:
            report = build_vector_db_governance_report(
                current_backend=args.current_backend,
                target_backend=args.target_backend,
                include_milvus=not args.exclude_milvus,
            )
        except ValueError as error:
            print(f"VECTOR DB GOVERNANCE ERROR: {error}")
            raise SystemExit(2) from error

        markdown = render_vector_db_governance_report(report)
        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-backup-retention":
        try:
            plan = build_qdrant_backup_retention_plan(
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                patterns=args.pattern,
            )
            result = execute_qdrant_backup_retention(
                plan,
                dry_run=not args.apply,
            )
        except (FileNotFoundError, NotADirectoryError, ValueError) as error:
            print(f"QDRANT BACKUP RETENTION ERROR: {error}")
            raise SystemExit(2) from error

        markdown = render_qdrant_backup_retention_report(result)
        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-snapshot-smoke-plan":
        try:
            plan = build_qdrant_snapshot_smoke_plan(
                url=args.url,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                snapshot_name_placeholder=args.snapshot_name,
            )
        except ValueError as error:
            print(f"QDRANT SNAPSHOT SMOKE PLAN ERROR: {error}")
            raise SystemExit(2) from error

        markdown = render_qdrant_snapshot_smoke_plan(plan)
        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-snapshot-smoke-report-template":
        try:
            plan = build_qdrant_snapshot_smoke_plan(
                url=args.url,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                snapshot_name_placeholder=args.snapshot_name,
            )
            markdown = render_qdrant_snapshot_smoke_report_template(
                plan,
                environment=args.environment,
                operator=args.operator,
            )
        except ValueError as error:
            print(f"QDRANT SNAPSHOT SMOKE REPORT ERROR: {error}")
            raise SystemExit(2) from error

        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-snapshot-drill-plan":
        try:
            plan = build_qdrant_snapshot_drill_plan(
                url=args.url,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                apply_retention=args.apply_retention,
                run_restore_drill=not args.skip_restore_drill,
            )
        except ValueError as error:
            print(f"QDRANT SNAPSHOT DRILL PLAN ERROR: {error}")
            raise SystemExit(2) from error

        markdown = render_qdrant_snapshot_drill_plan(plan)
        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-snapshot-schedule-config":
        try:
            config = build_qdrant_snapshot_schedule_config(
                platform=args.platform,
                task_name=args.task_name,
                cron_schedule=args.cron_schedule,
                windows_start_time=args.windows_start_time,
                working_directory=args.working_directory,
                log_path=args.log_path,
                namespace=args.namespace,
                image=args.image,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                apply_retention=args.apply_retention,
                run_restore_drill=not args.skip_restore_drill,
                run_compare=not args.skip_compare,
            )
        except ValueError as error:
            print(f"QDRANT SNAPSHOT SCHEDULE CONFIG ERROR: {error}")
            raise SystemExit(2) from error

        markdown = render_qdrant_snapshot_schedule_config(config)
        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-snapshot-cronjob-manifest":
        try:
            config = build_qdrant_snapshot_schedule_config(
                platform="kubernetes_cronjob",
                task_name=args.task_name,
                cron_schedule=args.cron_schedule,
                namespace=args.namespace,
                image=args.image,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                apply_retention=args.apply_retention,
                run_restore_drill=not args.skip_restore_drill,
                run_compare=not args.skip_compare,
            )
            yaml = render_qdrant_snapshot_cronjob_manifest(
                config,
                config_map_name=args.config_map_name,
                secret_name=args.secret_name,
            )
        except ValueError as error:
            print(f"QDRANT SNAPSHOT CRONJOB MANIFEST ERROR: {error}")
            raise SystemExit(2) from error

        print(yaml, end="")

        if args.output is not None:
            save_text_output(args.output, yaml)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-k8s-cronjob-smoke-run":
        try:
            config = build_qdrant_snapshot_schedule_config(
                platform="kubernetes_cronjob",
                task_name=args.task_name,
                cron_schedule=args.cron_schedule,
                namespace=args.namespace,
                image=args.image,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                apply_retention=args.apply_retention,
                run_restore_drill=args.run_restore_drill,
                run_compare=args.run_compare,
            )
            yaml = render_qdrant_snapshot_cronjob_manifest(
                config,
                config_map_name=args.config_map_name,
                secret_name=args.secret_name,
            )
            report = execute_qdrant_k8s_cronjob_smoke(
                manifest_yaml=yaml,
                task_name=args.task_name,
                namespace=args.namespace,
                job_name=args.job_name,
                timeout_seconds=args.timeout_seconds,
                cleanup_job=args.cleanup_job,
                cleanup_cronjob=args.cleanup_cronjob,
            )
            markdown = render_qdrant_k8s_cronjob_smoke_report(report)
        except ValueError as error:
            print(f"QDRANT K8S CRONJOB SMOKE ERROR: {error}")
            raise SystemExit(2) from error

        print(markdown, end="")

        if args.manifest_output is not None:
            save_text_output(args.manifest_output, yaml)
            print("MANIFEST OUTPUT:", args.manifest_output)

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

        if report.overall_status != "passed" and not args.allow_fail:
            raise SystemExit(1)

    elif args.command == "qdrant-k8s-cronjob-schedule-observe":
        try:
            config = build_qdrant_snapshot_schedule_config(
                platform="kubernetes_cronjob",
                task_name=args.task_name,
                cron_schedule=args.cron_schedule,
                namespace=args.namespace,
                image=args.image,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                apply_retention=args.apply_retention,
                run_restore_drill=args.run_restore_drill,
                run_compare=args.run_compare,
            )
            yaml = render_qdrant_snapshot_cronjob_manifest(
                config,
                config_map_name=args.config_map_name,
                secret_name=args.secret_name,
            )
            report = execute_qdrant_k8s_cronjob_schedule_observe(
                manifest_yaml=yaml,
                task_name=args.task_name,
                namespace=args.namespace,
                timeout_seconds=args.timeout_seconds,
                poll_interval_seconds=args.poll_interval_seconds,
                cleanup_job=args.cleanup_job,
                cleanup_cronjob=args.cleanup_cronjob,
            )
            markdown = render_qdrant_k8s_cronjob_schedule_observe_report(report)
        except ValueError as error:
            print(f"QDRANT K8S CRONJOB SCHEDULE OBSERVE ERROR: {error}")
            raise SystemExit(2) from error

        print(markdown, end="")

        if args.manifest_output is not None:
            save_text_output(args.manifest_output, yaml)
            print("MANIFEST OUTPUT:", args.manifest_output)

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

        if report.overall_status != "passed" and not args.allow_fail:
            raise SystemExit(1)

    elif args.command == "qdrant-k8s-cronjob-multi-cycle-observe":
        try:
            config = build_qdrant_snapshot_schedule_config(
                platform="kubernetes_cronjob",
                task_name=args.task_name,
                cron_schedule=args.cron_schedule,
                namespace=args.namespace,
                image=args.image,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                apply_retention=args.apply_retention,
                run_restore_drill=args.run_restore_drill,
                run_compare=args.run_compare,
            )
            yaml = render_qdrant_snapshot_cronjob_manifest(
                config,
                config_map_name=args.config_map_name,
                secret_name=args.secret_name,
            )
            report = execute_qdrant_k8s_cronjob_multi_cycle_observe(
                manifest_yaml=yaml,
                task_name=args.task_name,
                namespace=args.namespace,
                expected_cycles=args.expected_cycles,
                timeout_seconds=args.timeout_seconds,
                poll_interval_seconds=args.poll_interval_seconds,
                cleanup_jobs=args.cleanup_jobs,
                cleanup_cronjob=args.cleanup_cronjob,
            )
            markdown = render_qdrant_k8s_cronjob_multi_cycle_observe_report(report)
        except ValueError as error:
            print(f"QDRANT K8S CRONJOB MULTI-CYCLE OBSERVE ERROR: {error}")
            raise SystemExit(2) from error

        print(markdown, end="")

        if args.manifest_output is not None:
            save_text_output(args.manifest_output, yaml)
            print("MANIFEST OUTPUT:", args.manifest_output)

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

        if report.overall_status != "passed" and not args.allow_fail:
            raise SystemExit(1)

    elif args.command == "qdrant-snapshot-schedule-install-plan":
        try:
            config = build_qdrant_snapshot_schedule_config(
                platform=args.platform,
                task_name=args.task_name,
                cron_schedule=args.cron_schedule,
                windows_start_time=args.windows_start_time,
                working_directory=args.working_directory,
                log_path=args.log_path,
                namespace=args.namespace,
                image=args.image,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                apply_retention=args.apply_retention,
                run_restore_drill=not args.skip_restore_drill,
                run_compare=not args.skip_compare,
            )
            plan = build_qdrant_snapshot_schedule_install_plan(
                config=config,
                apply=args.apply,
                confirm_task_name=args.confirm_task_name,
            )
        except ValueError as error:
            print(f"QDRANT SNAPSHOT SCHEDULE INSTALL PLAN ERROR: {error}")
            raise SystemExit(2) from error

        markdown = render_qdrant_snapshot_schedule_install_plan(plan)
        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-snapshot-schedule-verify-plan":
        try:
            config = build_qdrant_snapshot_schedule_config(
                platform=args.platform,
                task_name=args.task_name,
                cron_schedule=args.cron_schedule,
                windows_start_time=args.windows_start_time,
                working_directory=args.working_directory,
                log_path=args.log_path,
                namespace=args.namespace,
                image=args.image,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                apply_retention=args.apply_retention,
                run_restore_drill=not args.skip_restore_drill,
                run_compare=not args.skip_compare,
            )
            plan = build_qdrant_snapshot_schedule_verification_plan(config)
        except ValueError as error:
            print(f"QDRANT SNAPSHOT SCHEDULE VERIFY PLAN ERROR: {error}")
            raise SystemExit(2) from error

        markdown = render_qdrant_snapshot_schedule_verification_plan(plan)
        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-snapshot-schedule-evidence-template":
        try:
            config = build_qdrant_snapshot_schedule_config(
                platform=args.platform,
                task_name=args.task_name,
                cron_schedule=args.cron_schedule,
                windows_start_time=args.windows_start_time,
                working_directory=args.working_directory,
                log_path=args.log_path,
                namespace=args.namespace,
                image=args.image,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                apply_retention=args.apply_retention,
                run_restore_drill=not args.skip_restore_drill,
                run_compare=not args.skip_compare,
            )
            markdown = render_qdrant_snapshot_schedule_evidence_template(
                config,
                environment=args.environment,
                operator=args.operator,
            )
        except ValueError as error:
            print(f"QDRANT SNAPSHOT SCHEDULE EVIDENCE TEMPLATE ERROR: {error}")
            raise SystemExit(2) from error

        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-snapshot-schedule-install-execute":
        try:
            config = build_qdrant_snapshot_schedule_config(
                platform=args.platform,
                task_name=args.task_name,
                cron_schedule=args.cron_schedule,
                windows_start_time=args.windows_start_time,
                working_directory=args.working_directory,
                log_path=args.log_path,
                namespace=args.namespace,
                image=args.image,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                apply_retention=args.apply_retention,
                run_restore_drill=not args.skip_restore_drill,
                run_compare=not args.skip_compare,
            )
            install_plan = build_qdrant_snapshot_schedule_install_plan(
                config=config,
                apply=True,
                confirm_task_name=args.confirm_task_name,
            )
            report = execute_qdrant_snapshot_schedule_install_plan(
                install_plan,
                timeout_seconds=args.timeout_seconds,
            )
            markdown = render_qdrant_snapshot_schedule_install_execution_report(
                report
            )
        except (OSError, TimeoutError, ValueError) as error:
            print(f"QDRANT SNAPSHOT SCHEDULE INSTALL EXECUTE ERROR: {error}")
            raise SystemExit(2) from error

        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-snapshot-drill-run":
        if (
            not args.skip_restore_drill
            and args.confirm_restore_collection != args.restore_collection
        ):
            print(
                "QDRANT SNAPSHOT DRILL RUN ERROR: "
                "--confirm-restore-collection must exactly match "
                "--restore-collection when restore drill is enabled"
            )
            raise SystemExit(2)

        try:
            plan = build_qdrant_snapshot_drill_plan(
                url=args.url,
                collection=args.collection,
                restore_collection=args.restore_collection,
                backup_dir=args.backup_dir,
                keep_last=args.keep_last,
                apply_retention=args.apply_retention,
                run_restore_drill=not args.skip_restore_drill,
            )
            client = QdrantSnapshotClient(
                url=args.url,
                api_key=(
                    args.api_key
                    if args.api_key is not None
                    else QDRANT_API_KEY
                ),
            )
            top_k = args.top_k if args.top_k is not None else RAG_TOP_K

            def compare_restored_collection(collection: str) -> dict:
                return compare_vector_store_repositories(
                    benchmark_path=RAG_BENCHMARK_PATH,
                    vector_store_path=args.source,
                    top_k=top_k,
                    qdrant_url=args.url,
                    qdrant_collection=collection,
                    qdrant_vector_size=args.vector_size,
                    qdrant_distance=args.distance,
                    qdrant_api_key=(
                        args.api_key
                        if args.api_key is not None
                        else QDRANT_API_KEY
                    ),
                )

            report = execute_qdrant_snapshot_drill(
                plan=plan,
                snapshot_client=client,
                compare_restored_collection=(
                    None
                    if args.skip_compare
                    else compare_restored_collection
                ),
            )
        except (
            FileNotFoundError,
            NotADirectoryError,
            OSError,
            RuntimeError,
            ValueError,
        ) as error:
            print(f"QDRANT SNAPSHOT DRILL RUN ERROR: {error}")
            raise SystemExit(1) from error

        markdown = render_qdrant_snapshot_drill_report(report)
        print(markdown, end="")

        if args.output is not None:
            save_text_output(args.output, markdown)
            print("OUTPUT:", args.output)

    elif args.command == "qdrant-snapshot-create":
        try:
            client = QdrantSnapshotClient(
                url=args.url,
                api_key=(
                    args.api_key
                    if args.api_key is not None
                    else QDRANT_API_KEY
                ),
            )
            snapshot = client.create_snapshot(args.collection)
        except (ValueError, RuntimeError) as error:
            print(f"QDRANT SNAPSHOT CREATE ERROR: {error}")
            raise SystemExit(1) from error

        print("QDRANT SNAPSHOT CREATE")
        print("QDRANT URL:", args.url)
        print("COLLECTION:", args.collection)
        print("SNAPSHOT NAME:", snapshot.name)
        print("CREATION TIME:", snapshot.creation_time)
        print("SIZE:", snapshot.size)

    elif args.command == "qdrant-snapshot-list":
        try:
            client = QdrantSnapshotClient(
                url=args.url,
                api_key=(
                    args.api_key
                    if args.api_key is not None
                    else QDRANT_API_KEY
                ),
            )
            snapshots = client.list_snapshots(args.collection)
        except (ValueError, RuntimeError) as error:
            print(f"QDRANT SNAPSHOT LIST ERROR: {error}")
            raise SystemExit(1) from error

        print("QDRANT SNAPSHOT LIST")
        print("QDRANT URL:", args.url)
        print("COLLECTION:", args.collection)
        print("COUNT:", len(snapshots))

        for snapshot in snapshots:
            print("-" * 40)
            print("SNAPSHOT NAME:", snapshot.name)
            print("CREATION TIME:", snapshot.creation_time)
            print("SIZE:", snapshot.size)

    elif args.command == "qdrant-snapshot-download":
        try:
            target_path = Path(args.backup_dir) / args.snapshot_name
            client = QdrantSnapshotClient(
                url=args.url,
                api_key=(
                    args.api_key
                    if args.api_key is not None
                    else QDRANT_API_KEY
                ),
            )
            saved_path = client.download_snapshot(
                collection=args.collection,
                snapshot_name=args.snapshot_name,
                output_path=target_path,
            )
        except (ValueError, RuntimeError, OSError) as error:
            print(f"QDRANT SNAPSHOT DOWNLOAD ERROR: {error}")
            raise SystemExit(1) from error

        print("QDRANT SNAPSHOT DOWNLOAD")
        print("QDRANT URL:", args.url)
        print("COLLECTION:", args.collection)
        print("SNAPSHOT NAME:", args.snapshot_name)
        print("SAVED PATH:", saved_path)

    elif args.command == "qdrant-snapshot-restore":
        if args.confirm_restore_collection != args.restore_collection:
            print(
                "QDRANT SNAPSHOT RESTORE ERROR: "
                "--confirm-restore-collection must exactly match "
                "--restore-collection"
            )
            raise SystemExit(1)

        try:
            client = QdrantSnapshotClient(
                url=args.url,
                api_key=(
                    args.api_key
                    if args.api_key is not None
                    else QDRANT_API_KEY
                ),
            )
            result = client.restore_snapshot(
                restore_collection=args.restore_collection,
                snapshot_path=args.snapshot_path,
            )
        except (FileNotFoundError, ValueError, RuntimeError, OSError) as error:
            print(f"QDRANT SNAPSHOT RESTORE ERROR: {error}")
            raise SystemExit(1) from error

        print("QDRANT SNAPSHOT RESTORE")
        print("QDRANT URL:", args.url)
        print("RESTORE COLLECTION:", args.restore_collection)
        print("SNAPSHOT PATH:", args.snapshot_path)
        print("RESULT:", result)

    elif args.command == "import-json-to-postgres":
        database_url = (
            args.database_url
            if args.database_url is not None
            else DATABASE_URL
        )

        if not database_url:
            print(
                "POSTGRES IMPORT ERROR: DATABASE_URL is required. "
                "Set DATABASE_URL or pass --database-url."
            )
            raise SystemExit(1)

        try:
            repositories = create_repositories(
                storage_backend="postgres",
                database_url=database_url,
            )
            report = import_json_storage_to_repositories(
                repositories=repositories,
                task_directory=args.task_directory,
                session_directory=args.session_directory,
                trace_file_path=args.trace_file,
                include_tasks=not args.skip_tasks,
                include_sessions=not args.skip_sessions,
                include_traces=not args.skip_traces,
                dry_run=args.dry_run,
            )
        except (FileNotFoundError, ValueError, RuntimeError) as error:
            print(f"POSTGRES IMPORT ERROR: {error}")
            raise SystemExit(1) from error

        print("POSTGRES JSON IMPORT")
        print("DATABASE URL: configured")
        print("DRY RUN:", report.dry_run)
        print("TASK SOURCE COUNT:", report.tasks.source_count)
        print("TASK IMPORTED COUNT:", report.tasks.imported_count)
        print("SESSION SOURCE COUNT:", report.sessions.source_count)
        print("SESSION IMPORTED COUNT:", report.sessions.imported_count)
        print("TRACE SOURCE COUNT:", report.traces.source_count)
        print("TRACE IMPORTED COUNT:", report.traces.imported_count)
        print("TOTAL SOURCE COUNT:", report.total_source_count)
        print("TOTAL IMPORTED COUNT:", report.total_imported_count)

    elif args.command == "show-task":
        task_repository = create_task_repository_for_cli(args.directory)
        task = get_defense_task(
            task_id=args.task_id,
            directory=args.directory,
            task_repository=task_repository,
        )

        print("TASK")
        print(f"TASK ID: {task.task_id}")
        print(f"TOPIC: {task.topic}")
        print(f"STATUS: {task.status}")
        print(f"CURRENT STEP ID: {task.current_step_id}")
        print(f"STEP COUNT: {len(task.steps)}")

        for index, step in enumerate(task.steps, start=1):
            print("-" * 40)
            print(f"STEP {index}")
            print(f"STEP ID: {step.step_id}")
            print(f"STEP TYPE: {step.step_type}")
            print(f"STEP STATUS: {step.status}")
    else:
        parser.print_help()


if __name__ == "__main__":
    
    main()
