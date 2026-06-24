import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.embeddings import create_embedding
from app.defense_questions import generate_questions_from_context_with_audit
from app.langgraph_workflow.checkpointer_demo import run_checkpointer_demo


def build_checkpoint_snapshot(
    report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "created_at": datetime.now().replace(microsecond=0).isoformat(),
        "thread_id": report["thread_id"],
        "checkpointer_type": report["checkpointer_type"],
        "interrupted_checkpoint": report["interrupted_checkpoint"],
        "resumed_checkpoint": report["resumed_checkpoint"],
        "has_resumed": report["resumed_checkpoint"] is not None,
    }


def save_checkpoint_snapshot(
    snapshot: dict[str, Any],
    output_path: str,
) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(path)


def load_checkpoint_snapshot(
    file_path: str,
) -> dict[str, Any]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"checkpoint snapshot 不存在：{file_path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("checkpoint snapshot 必须是 JSON 对象")

    return data


def summarize_checkpoint_snapshot(
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    interrupted_checkpoint = snapshot["interrupted_checkpoint"]
    resumed_checkpoint = snapshot.get("resumed_checkpoint")

    return {
        "thread_id": snapshot["thread_id"],
        "checkpointer_type": snapshot["checkpointer_type"],
        "interrupted_next": interrupted_checkpoint["next"],
        "interrupted_has_pending_interrupt": interrupted_checkpoint[
            "has_pending_interrupt"
        ],
        "interrupted_value_keys": sorted(
            interrupted_checkpoint["values"].keys()
        ),
        "has_resumed": resumed_checkpoint is not None,
        "resumed_next": (
            resumed_checkpoint["next"]
            if resumed_checkpoint is not None
            else None
        ),
        "resumed_has_pending_interrupt": (
            resumed_checkpoint["has_pending_interrupt"]
            if resumed_checkpoint is not None
            else None
        ),
        "resumed_value_keys": (
            sorted(resumed_checkpoint["values"].keys())
            if resumed_checkpoint is not None
            else None
        ),
    }


def run_persistent_checkpoint_demo(
    topic: str,
    thread_id: str,
    output_path: str,
    answer: str | None = None,
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn=create_embedding,
    question_generator=generate_questions_from_context_with_audit,
) -> dict[str, Any]:
    report = run_checkpointer_demo(
        topic=topic,
        thread_id=thread_id,
        answer=answer,
        vector_store_path=vector_store_path,
        top_k=top_k,
        embedding_fn=embedding_fn,
        question_generator=question_generator,
    )
    snapshot = build_checkpoint_snapshot(report)
    saved_path = save_checkpoint_snapshot(snapshot, output_path)
    summary = summarize_checkpoint_snapshot(snapshot)

    return {
        "snapshot_path": saved_path,
        "snapshot": snapshot,
        "summary": summary,
    }
