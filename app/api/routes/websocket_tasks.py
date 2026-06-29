from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.routes.tasks import (
    analyze_task_service,
    execute_task_step_service,
    get_task_directory,
    start_task_step_service,
    submit_follow_up_answer_service,
    submit_task_answer_service,
)


router = APIRouter(tags=["websocket"])


def websocket_success(
    event_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": event_type,
        **payload,
    }


def websocket_error(message: str) -> dict[str, Any]:
    return {
        "type": "error",
        "message": message,
    }


def serialize_task_step_response(
    event_type: str,
    task,
    step,
    path,
) -> dict[str, Any]:
    return websocket_success(
        event_type,
        {
            "task": asdict(task),
            "step": asdict(step) if step is not None else None,
            "path": str(path) if path is not None else None,
        },
    )


def handle_task_websocket_message(
    task_id: str,
    message: dict[str, Any],
    directory: Path,
) -> dict[str, Any]:
    message_type = message.get("type")

    if message_type == "ping":
        return websocket_success(
            "pong",
            {
                "task_id": task_id,
            },
        )

    if message_type == "start_next_step":
        task, step, path = start_task_step_service(
            task_id=task_id,
            directory=directory,
            input=message.get("input") or {},
        )
        return serialize_task_step_response(
            "step_started",
            task,
            step,
            path,
        )

    if message_type == "execute_current_step":
        task, step, path = execute_task_step_service(
            task_id=task_id,
            directory=directory,
        )
        return serialize_task_step_response(
            "step_completed",
            task,
            step,
            path,
        )

    if message_type == "submit_answer":
        answer = str(message.get("answer") or "").strip()

        if not answer:
            raise ValueError("answer must not be empty")

        task, step, path = submit_task_answer_service(
            task_id=task_id,
            answer=answer,
            directory=directory,
        )
        return serialize_task_step_response(
            "answer_submitted",
            task,
            step,
            path,
        )

    if message_type == "submit_follow_up_answer":
        answer = str(message.get("answer") or "").strip()

        if not answer:
            raise ValueError("answer must not be empty")

        task, step, path = submit_follow_up_answer_service(
            task_id=task_id,
            answer=answer,
            directory=directory,
        )
        return serialize_task_step_response(
            "follow_up_answer_submitted",
            task,
            step,
            path,
        )

    if message_type == "analyze_task":
        analysis = analyze_task_service(
            task_id=task_id,
            directory=directory,
        )
        return websocket_success(
            "task_analysis",
            {
                "analysis": analysis,
            },
        )

    raise ValueError(f"unsupported websocket message type: {message_type}")


@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(
    websocket: WebSocket,
    task_id: str,
) -> None:
    await websocket.accept()
    directory = get_task_directory()

    await websocket.send_json(
        websocket_success(
            "connected",
            {
                "task_id": task_id,
            },
        )
    )

    try:
        while True:
            message = await websocket.receive_json()

            try:
                response = handle_task_websocket_message(
                    task_id=task_id,
                    message=message,
                    directory=directory,
                )
            except Exception as error:
                response = websocket_error(str(error))

            await websocket.send_json(response)
    except WebSocketDisconnect:
        return
