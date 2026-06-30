import pytest
import requests

from app import cli
from app.qdrant_snapshot_client import QdrantSnapshotClient


class FakeResponse:
    def __init__(
        self,
        json_data=None,
        content: bytes = b"",
        error: Exception | None = None,
    ):
        self._json_data = json_data or {}
        self.content = content
        self.error = error

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.error is not None:
            raise self.error


class FakeHttpClient:
    def __init__(self):
        self.posts = []
        self.gets = []
        self.next_post_response = FakeResponse()
        self.next_get_response = FakeResponse()

    def post(self, url: str, **kwargs):
        self.posts.append({"url": url, "kwargs": kwargs})
        return self.next_post_response

    def get(self, url: str, **kwargs):
        self.gets.append({"url": url, "kwargs": kwargs})
        return self.next_get_response


def test_qdrant_snapshot_client_create_snapshot():
    http_client = FakeHttpClient()
    http_client.next_post_response = FakeResponse(
        {
            "result": {
                "name": "snapshot-1.snapshot",
                "creation_time": "2026-06-30T10:00:00Z",
                "size": 123,
            }
        }
    )
    client = QdrantSnapshotClient(
        url="http://127.0.0.1:6333/",
        api_key="secret",
        http_client=http_client,
    )

    snapshot = client.create_snapshot("thesis_chunks")

    assert snapshot.name == "snapshot-1.snapshot"
    assert snapshot.creation_time == "2026-06-30T10:00:00Z"
    assert snapshot.size == 123
    assert http_client.posts == [
        {
            "url": "http://127.0.0.1:6333/collections/thesis_chunks/snapshots",
            "kwargs": {
                "headers": {"api-key": "secret"},
                "timeout": 30,
            },
        }
    ]


def test_qdrant_snapshot_client_list_snapshots():
    http_client = FakeHttpClient()
    http_client.next_get_response = FakeResponse(
        {
            "result": [
                {
                    "name": "snapshot-1.snapshot",
                    "creation_time": "2026-06-30T10:00:00Z",
                    "size": 123,
                },
                {
                    "name": "snapshot-2.snapshot",
                    "creation_time": "2026-06-30T11:00:00Z",
                    "size": 456,
                },
            ]
        }
    )
    client = QdrantSnapshotClient(
        url="http://127.0.0.1:6333",
        http_client=http_client,
    )

    snapshots = client.list_snapshots("thesis_chunks")

    assert [snapshot.name for snapshot in snapshots] == [
        "snapshot-1.snapshot",
        "snapshot-2.snapshot",
    ]
    assert http_client.gets[0]["url"] == (
        "http://127.0.0.1:6333/collections/thesis_chunks/snapshots"
    )


def test_qdrant_snapshot_client_download_snapshot(tmp_path):
    http_client = FakeHttpClient()
    http_client.next_get_response = FakeResponse(content=b"snapshot-bytes")
    client = QdrantSnapshotClient(
        url="http://127.0.0.1:6333",
        http_client=http_client,
    )
    output_path = tmp_path / "backups" / "snapshot-1.snapshot"

    saved_path = client.download_snapshot(
        collection="thesis_chunks",
        snapshot_name="snapshot-1.snapshot",
        output_path=output_path,
    )

    assert saved_path == str(output_path)
    assert output_path.read_bytes() == b"snapshot-bytes"
    assert http_client.gets[0]["url"] == (
        "http://127.0.0.1:6333/collections/"
        "thesis_chunks/snapshots/snapshot-1.snapshot"
    )


def test_qdrant_snapshot_client_restore_snapshot(tmp_path):
    snapshot_path = tmp_path / "snapshot-1.snapshot"
    snapshot_path.write_bytes(b"snapshot-bytes")
    http_client = FakeHttpClient()
    http_client.next_post_response = FakeResponse({"result": True})
    client = QdrantSnapshotClient(
        url="http://127.0.0.1:6333",
        http_client=http_client,
    )

    result = client.restore_snapshot(
        restore_collection="restore_chunks",
        snapshot_path=snapshot_path,
    )

    assert result == {"result": True}
    assert http_client.posts[0]["url"] == (
        "http://127.0.0.1:6333/collections/"
        "restore_chunks/snapshots/upload?priority=snapshot"
    )
    assert "files" in http_client.posts[0]["kwargs"]


def test_qdrant_snapshot_client_validates_inputs(tmp_path):
    with pytest.raises(ValueError, match="url"):
        QdrantSnapshotClient(url="")

    with pytest.raises(ValueError, match="timeout_seconds"):
        QdrantSnapshotClient(url="http://127.0.0.1:6333", timeout_seconds=0)

    client = QdrantSnapshotClient(
        url="http://127.0.0.1:6333",
        http_client=FakeHttpClient(),
    )

    with pytest.raises(ValueError, match="collection"):
        client.create_snapshot(" ")

    with pytest.raises(ValueError, match="snapshot_name"):
        client.download_snapshot("thesis_chunks", " ", tmp_path / "x.snapshot")

    with pytest.raises(FileNotFoundError, match="snapshot file"):
        client.restore_snapshot("restore_chunks", tmp_path / "missing.snapshot")


def test_qdrant_snapshot_client_wraps_http_errors():
    http_client = FakeHttpClient()
    http_client.next_post_response = FakeResponse(
        error=requests.HTTPError("500 server error")
    )
    client = QdrantSnapshotClient(
        url="http://127.0.0.1:6333",
        http_client=http_client,
    )

    with pytest.raises(RuntimeError, match="Qdrant snapshot request failed"):
        client.create_snapshot("thesis_chunks")


def test_qdrant_snapshot_client_rejects_malformed_responses():
    http_client = FakeHttpClient()
    http_client.next_post_response = FakeResponse({"result": []})
    client = QdrantSnapshotClient(
        url="http://127.0.0.1:6333",
        http_client=http_client,
    )

    with pytest.raises(ValueError, match="result must be an object"):
        client.create_snapshot("thesis_chunks")

    http_client.next_get_response = FakeResponse({"result": {}})

    with pytest.raises(ValueError, match="result must be a list"):
        client.list_snapshots("thesis_chunks")


def test_qdrant_snapshot_create_cli(monkeypatch, capsys):
    created = []

    class FakeSnapshot:
        name = "snapshot-1.snapshot"
        creation_time = "2026-06-30T10:00:00Z"
        size = 123

    class FakeQdrantSnapshotClient:
        def __init__(self, url, api_key):
            created.append({"url": url, "api_key": api_key})

        def create_snapshot(self, collection):
            created[-1]["collection"] = collection
            return FakeSnapshot()

    monkeypatch.setattr(cli, "QdrantSnapshotClient", FakeQdrantSnapshotClient)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-create",
            "--url",
            "http://127.0.0.1:6333",
            "--collection",
            "thesis_chunks",
            "--api-key",
            "secret",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "QDRANT SNAPSHOT CREATE" in output
    assert "SNAPSHOT NAME: snapshot-1.snapshot" in output
    assert created == [
        {
            "url": "http://127.0.0.1:6333",
            "api_key": "secret",
            "collection": "thesis_chunks",
        }
    ]


def test_qdrant_snapshot_list_cli(monkeypatch, capsys):
    class FakeSnapshot:
        def __init__(self, name):
            self.name = name
            self.creation_time = None
            self.size = None

    class FakeQdrantSnapshotClient:
        def __init__(self, url, api_key):
            pass

        def list_snapshots(self, collection):
            return [FakeSnapshot("a.snapshot"), FakeSnapshot("b.snapshot")]

    monkeypatch.setattr(cli, "QdrantSnapshotClient", FakeQdrantSnapshotClient)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-list",
            "--collection",
            "thesis_chunks",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "QDRANT SNAPSHOT LIST" in output
    assert "COUNT: 2" in output
    assert "SNAPSHOT NAME: a.snapshot" in output
    assert "SNAPSHOT NAME: b.snapshot" in output


def test_qdrant_snapshot_download_cli(monkeypatch, capsys, tmp_path):
    captured = []

    class FakeQdrantSnapshotClient:
        def __init__(self, url, api_key):
            captured.append({"url": url, "api_key": api_key})

        def download_snapshot(self, collection, snapshot_name, output_path):
            captured[-1].update(
                {
                    "collection": collection,
                    "snapshot_name": snapshot_name,
                    "output_path": output_path,
                }
            )
            return str(output_path)

    monkeypatch.setattr(cli, "QdrantSnapshotClient", FakeQdrantSnapshotClient)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-download",
            "--collection",
            "thesis_chunks",
            "--snapshot-name",
            "snapshot-1.snapshot",
            "--backup-dir",
            str(tmp_path),
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "QDRANT SNAPSHOT DOWNLOAD" in output
    assert "SAVED PATH:" in output
    assert captured[0]["collection"] == "thesis_chunks"
    assert captured[0]["snapshot_name"] == "snapshot-1.snapshot"


def test_qdrant_snapshot_restore_cli(monkeypatch, capsys, tmp_path):
    snapshot_path = tmp_path / "snapshot-1.snapshot"
    snapshot_path.write_bytes(b"snapshot-bytes")
    captured = []

    class FakeQdrantSnapshotClient:
        def __init__(self, url, api_key):
            captured.append({"url": url, "api_key": api_key})

        def restore_snapshot(self, restore_collection, snapshot_path):
            captured[-1].update(
                {
                    "restore_collection": restore_collection,
                    "snapshot_path": snapshot_path,
                }
            )
            return {"result": True}

    monkeypatch.setattr(cli, "QdrantSnapshotClient", FakeQdrantSnapshotClient)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-restore",
            "--restore-collection",
            "restore_chunks",
            "--confirm-restore-collection",
            "restore_chunks",
            "--snapshot-path",
            str(snapshot_path),
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "QDRANT SNAPSHOT RESTORE" in output
    assert "RESTORE COLLECTION: restore_chunks" in output
    assert "RESULT: {'result': True}" in output
    assert captured[0]["restore_collection"] == "restore_chunks"
    assert captured[0]["snapshot_path"] == str(snapshot_path)


def test_qdrant_snapshot_restore_cli_requires_matching_confirmation(
    monkeypatch,
    capsys,
    tmp_path,
):
    snapshot_path = tmp_path / "snapshot-1.snapshot"
    snapshot_path.write_bytes(b"snapshot-bytes")
    created = []

    class FakeQdrantSnapshotClient:
        def __init__(self, url, api_key):
            created.append({"url": url, "api_key": api_key})

    monkeypatch.setattr(cli, "QdrantSnapshotClient", FakeQdrantSnapshotClient)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-restore",
            "--restore-collection",
            "restore_chunks",
            "--confirm-restore-collection",
            "wrong_chunks",
            "--snapshot-path",
            str(snapshot_path),
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "QDRANT SNAPSHOT RESTORE ERROR" in output
    assert created == []
