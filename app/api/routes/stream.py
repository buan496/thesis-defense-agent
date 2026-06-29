import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse


router = APIRouter(prefix="/stream", tags=["stream"])


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
