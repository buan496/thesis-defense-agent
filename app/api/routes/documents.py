import os
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel


router = APIRouter(prefix="/documents", tags=["documents"])

DEFAULT_UPLOAD_DIRECTORY = Path(
    os.getenv("DOCUMENT_UPLOAD_DIRECTORY", "data/uploads")
)
DEFAULT_MAX_UPLOAD_BYTES = int(
    os.getenv("DOCUMENT_UPLOAD_MAX_BYTES", str(10 * 1024 * 1024))
)
ALLOWED_DOCUMENT_SUFFIXES = {".pdf", ".txt", ".md"}
UPLOAD_CHUNK_BYTES = 1024 * 1024


class DocumentUploadResponse(BaseModel):
    document_id: str
    original_filename: str
    stored_filename: str
    path: str
    content_type: str | None
    suffix: str
    size_bytes: int


def get_upload_directory() -> Path:
    return DEFAULT_UPLOAD_DIRECTORY


def get_max_upload_bytes() -> int:
    return DEFAULT_MAX_UPLOAD_BYTES


def _safe_original_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="filename must not be empty",
        )

    # Handle both POSIX and Windows style paths from client-provided names.
    name = PureWindowsPath(PurePosixPath(filename).name).name.strip()
    name = re.sub(r"\s+", "_", name)
    name = "".join(
        char if char.isalnum() or char in {"-", "_", "."} else "_"
        for char in name
    )
    name = name.strip("._")

    if not name:
        raise HTTPException(
            status_code=400,
            detail="filename must not be empty",
        )

    return name


def _validate_suffix(filename: str) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_DOCUMENT_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_DOCUMENT_SUFFIXES))
        raise HTTPException(
            status_code=415,
            detail=f"unsupported document type: {suffix or '<none>'}; allowed: {allowed}",
        )

    return suffix


async def _save_upload_file(
    upload_file: UploadFile,
    destination: Path,
    max_bytes: int,
) -> int:
    size_bytes = 0

    try:
        with destination.open("wb") as output:
            while True:
                chunk = await upload_file.read(UPLOAD_CHUNK_BYTES)

                if not chunk:
                    break

                size_bytes += len(chunk)

                if size_bytes > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"uploaded file exceeds {max_bytes} bytes",
                    )

                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload_file.close()

    if size_bytes == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="uploaded file must not be empty",
        )

    return size_bytes


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    upload_directory: Path = Depends(get_upload_directory),
    max_upload_bytes: int = Depends(get_max_upload_bytes),
) -> DocumentUploadResponse:
    original_filename = _safe_original_filename(file.filename)
    suffix = _validate_suffix(original_filename)

    document_id = uuid4().hex
    stored_filename = f"{document_id}{suffix}"
    upload_directory.mkdir(parents=True, exist_ok=True)
    destination = upload_directory / stored_filename

    size_bytes = await _save_upload_file(
        upload_file=file,
        destination=destination,
        max_bytes=max_upload_bytes,
    )

    return DocumentUploadResponse(
        document_id=document_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        path=str(destination),
        content_type=file.content_type,
        suffix=suffix,
        size_bytes=size_bytes,
    )
