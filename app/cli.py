import json
import argparse
from pathlib import Path
from datetime import datetime

from app.logger import setup_logger
from app.mock_defense import run_mock_defense
from app.retrieval_evaluator import evaluate_retrieval
from app.vector_store_builder import build_pdf_vector_store
from app.config import (
    RAG_BENCHMARK_PATH,
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RAG_MIN_CHUNK_SIZE,
    RAG_TOP_K,
    RAG_VECTOR_STORE_PATH,
    AGENT_TRACE_PATH,
)

from app.agent_trace_analyzer import analyze_agent_traces

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
        print("TOOL COUNTS:")

        for tool_name, count in report["tool_counts"].items():
            print(f"  {tool_name}: {count}")
    
    elif args.command == "mock-defense":
        run_mock_defense(training_query=args.topic)
    else:
        parser.print_help()


if __name__ == "__main__":
    
    main()
