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
    evaluate_retrieval,
    scan_hybrid_weights,
)
from app.vector_store_builder import build_pdf_vector_store
from app.config import (
    AGENT_ROUTING_BENCHMARK_PATH,
    AGENT_TRACE_PATH,
    DEEPSEEK_MODEL,
    FAITHFULNESS_BENCHMARK_PATH,
    FEEDBACK_STORE_PATH,
    BENCHMARK_CANDIDATE_DIRECTORY,
    LONG_TERM_MEMORY_PATH,
    RAG_BENCHMARK_PATH,
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RAG_MIN_CHUNK_SIZE,
    RAG_TOP_K,
    RAG_VECTOR_STORE_PATH,
    SUB_AGENT_EXECUTION_TRACE_PATH,
    SUB_AGENT_PLAN_TRACE_PATH,
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
        report = analyze_agent_traces(args.file)

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
            replay = replay_agent_trace(
                file_path=args.file,
                line_number=args.line_number,
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
            summary = replay_trace_file(
                file_path=args.file,
                source_type=args.source_type,
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
            summary = replay_trace_file(
                file_path=args.file,
                source_type=args.source_type,
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
        task, task_path = create_defense_task(
            topic=args.topic,
            directory=args.directory,
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

        task, step, task_path = start_next_task_step(
            task_id=args.task_id,
            directory=args.directory,
            input=step_input,
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
            task, step, task_path = complete_task_step(
                task_id=args.task_id,
                directory=args.directory,
                output=step_output,
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
            task, step, task_path = execute_current_task_step(
                task_id=args.task_id,
                directory=args.directory,
                long_term_memory_path=LONG_TERM_MEMORY_PATH,
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
        task = get_defense_task(
            task_id=args.task_id,
            directory=args.directory,
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
        task = get_defense_task(
            task_id=args.task_id,
            directory=args.directory,
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
            task, step, task_path = submit_task_answer(
                task_id=args.task_id,
                answer=args.answer,
                directory=args.directory,
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
            task, step, task_path = submit_follow_up_answer(
                task_id=args.task_id,
                answer=args.answer,
                directory=args.directory,
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
        task = get_defense_task(
            task_id=args.task_id,
            directory=args.directory,
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
            task = get_defense_task(
                task_id=args.task_id,
                directory=args.directory,
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
            trace_path = save_sub_agent_plan_trace(
                plan,
                file_path=args.trace_file,
            )
            print("TRACE SAVED:", trace_path)

    elif args.command == "analyze-sub-agent-plans":
        records = load_sub_agent_plan_traces(args.file)
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
        records = load_sub_agent_execution_traces(args.file)
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

    elif args.command == "show-task":
        task = get_defense_task(
            task_id=args.task_id,
            directory=args.directory,
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
