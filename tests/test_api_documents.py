from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import documents


client = TestClient(app)


def clear_overrides():
    app.dependency_overrides.clear()


def override_upload_directory(upload_directory: Path):
    app.dependency_overrides[documents.get_upload_directory] = lambda: (
        upload_directory
    )


def test_upload_document_saves_txt_file(tmp_path):
    upload_directory = tmp_path / "uploads"
    override_upload_directory(upload_directory)

    try:
        response = client.post(
            "/documents/upload",
            files={
                "file": (
                    "thesis.txt",
                    b"hello thesis",
                    "text/plain",
                )
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()

    assert body["original_filename"] == "thesis.txt"
    assert body["suffix"] == ".txt"
    assert body["size_bytes"] == len(b"hello thesis")
    assert body["stored_filename"].endswith(".txt")

    stored_path = Path(body["path"])
    assert stored_path.exists()
    assert stored_path.parent == upload_directory
    assert stored_path.read_bytes() == b"hello thesis"


def test_upload_document_sanitizes_client_filename(tmp_path):
    upload_directory = tmp_path / "uploads"
    override_upload_directory(upload_directory)

    try:
        response = client.post(
            "/documents/upload",
            files={
                "file": (
                    "../unsafe thesis.txt",
                    b"content",
                    "text/plain",
                )
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()

    assert body["original_filename"] == "unsafe_thesis.txt"
    assert Path(body["path"]).parent == upload_directory


def test_upload_document_rejects_unsupported_suffix(tmp_path):
    upload_directory = tmp_path / "uploads"
    override_upload_directory(upload_directory)

    try:
        response = client.post(
            "/documents/upload",
            files={
                "file": (
                    "malware.exe",
                    b"content",
                    "application/octet-stream",
                )
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 415
    assert "unsupported document type" in response.json()["detail"]
    assert not upload_directory.exists()


def test_upload_document_rejects_empty_file(tmp_path):
    upload_directory = tmp_path / "uploads"
    override_upload_directory(upload_directory)

    try:
        response = client.post(
            "/documents/upload",
            files={
                "file": (
                    "empty.txt",
                    b"",
                    "text/plain",
                )
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 400
    assert response.json()["detail"] == "uploaded file must not be empty"
    assert list(upload_directory.glob("*")) == []


def test_upload_document_rejects_file_larger_than_limit(tmp_path):
    upload_directory = tmp_path / "uploads"
    override_upload_directory(upload_directory)
    app.dependency_overrides[documents.get_max_upload_bytes] = lambda: 4

    try:
        response = client.post(
            "/documents/upload",
            files={
                "file": (
                    "large.txt",
                    b"too large",
                    "text/plain",
                )
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 413
    assert "exceeds 4 bytes" in response.json()["detail"]
    assert list(upload_directory.glob("*")) == []
