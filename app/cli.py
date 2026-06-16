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
from app.retrieval_evaluator import evaluate_retrieval
from app.vector_store_builder import build_pdf_vector_store
from app.config import (
    AGENT_ROUTING_BENCHMARK_PATH,
    AGENT_TRACE_PATH,
    DEEPSEEK_MODEL,
    FAITHFULNESS_BENCHMARK_PATH,
    RAG_BENCHMARK_PATH,
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RAG_MIN_CHUNK_SIZE,
    RAG_TOP_K,
    RAG_VECTOR_STORE_PATH,
)
from app.agent_routing_evaluator import evaluate_agent_routing
from app.agent_trace_analyzer import analyze_agent_traces
from app.session_service import run_agent_session
from app.budget_guard import BudgetExceededError

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
    
    mock_parser = subparsers.add_parser("mock-defense")
    mock_parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Training topic for this mock defense round",
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
        )

        for item in report["results"]:
            print(
                f"QUERY: {item['query']}\n"
                f"HIT: {item['hit_count']} / {item['total']}\n"
                f"MISSING: {item['missing']}\n"
                f"SCORE: {item['score']}\n"
                f"{'-' * 40}"
            )

        print("TOP_K:", report["top_k"])
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
        
        try:
            result, session, session_path = run_agent_session(
                user_message=user_message,
                session_id=args.session_id,
                max_history_turns=args.max_history_turns,
                max_history_characters=args.max_history_characters,
                max_run_cost=args.max_run_cost,
            )
        except FileNotFoundError as error:
            print(f"SESSION ERROR: {error}")
            raise SystemExit(1) from error
        
        except BudgetExceededError as error:
            print(f"BUDGET ERROR: {error}")
            raise SystemExit(1) from error

        print("\nASSISTANT:")
        print(result.final_output)

        print("\nSESSION ID:")
        print(session.session_id)

        print("\nSESSION SAVED:")
        print(session_path)

    elif args.command == "mock-defense":
        run_mock_defense(training_query=args.topic)
    else:
        parser.print_help()


if __name__ == "__main__":
    
    main()
