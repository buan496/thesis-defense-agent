import asyncio
import json
from collections.abc import AsyncIterator, Callable, Iterable

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse


router = APIRouter(prefix="/stream", tags=["stream"])
LlmStreamFunction = Callable[[str], Iterable[str]]


def format_sse_event(
    data: dict[str, object],
    event: str | None = None,
) -> str:
    lines = []

    if event:
        lines.append(f"event: {event}")

    payload = json.dumps(data, ensure_ascii=False)
    lines.append(f"data: {payload}")

    return "\n".join(lines) + "\n\n"


def split_text_chunks(text: str, chunk_size: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    return [
        text[index : index + chunk_size]
        for index in range(0, len(text), chunk_size)
    ]


async def stream_text_chunks(
    text: str,
    chunk_size: int,
) -> AsyncIterator[str]:
    chunks = split_text_chunks(text, chunk_size)

    for index, chunk in enumerate(chunks):
        yield format_sse_event(
            {
                "index": index,
                "text": chunk,
            },
            event="chunk",
        )
        await asyncio.sleep(0)

    yield format_sse_event(
        {
            "chunk_count": len(chunks),
        },
        event="done",
    )


def get_llm_stream_function() -> LlmStreamFunction:
    # Import lazily so lightweight API endpoints do not require LLM/API config.
    from app.llm import stream_chat_with_llm

    return stream_chat_with_llm


async def stream_llm_chat(
    message: str,
    llm_stream_fn: LlmStreamFunction,
) -> AsyncIterator[str]:
    chunk_count = 0

    try:
        for chunk in llm_stream_fn(message):
            yield format_sse_event(
                {
                    "index": chunk_count,
                    "text": chunk,
                },
                event="chunk",
            )
            chunk_count += 1
            await asyncio.sleep(0)
    except Exception as error:
        yield format_sse_event(
            {
                "error_type": type(error).__name__,
                "message": str(error),
            },
            event="error",
        )
        return

    yield format_sse_event(
        {
            "chunk_count": chunk_count,
        },
        event="done",
    )


@router.get("/echo")
async def stream_echo(
    message: str = Query(min_length=1),
    chunk_size: int = Query(default=8, ge=1, le=200),
) -> StreamingResponse:
    message = message.strip()

    if not message:
        raise HTTPException(
            status_code=422,
            detail="message must not be empty",
        )

    return StreamingResponse(
        stream_text_chunks(
            text=message,
            chunk_size=chunk_size,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat")
async def stream_chat(
    message: str = Query(min_length=1),
    llm_stream_fn: LlmStreamFunction = Depends(get_llm_stream_function),
) -> StreamingResponse:
    message = message.strip()

    if not message:
        raise HTTPException(
            status_code=422,
            detail="message must not be empty",
        )

    return StreamingResponse(
        stream_llm_chat(
            message=message,
            llm_stream_fn=llm_stream_fn,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
