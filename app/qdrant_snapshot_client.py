from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import requests


@dataclass(frozen=True)
class QdrantSnapshotInfo:
    name: str
    creation_time: str | None = None
    size: int | None = None


class QdrantSnapshotHttpClient(Protocol):
    def post(self, url: str, **kwargs):
        ...

    def get(self, url: str, **kwargs):
        ...


class RequestsQdrantSnapshotHttpClient:
    def post(self, url: str, **kwargs):
        return requests.post(url, **kwargs)

    def get(self, url: str, **kwargs):
        return requests.get(url, **kwargs)


class QdrantSnapshotClient:
    def __init__(
        self,
        url: str,
        api_key: str = "",
        http_client: QdrantSnapshotHttpClient | None = None,
        timeout_seconds: float = 30,
    ):
        normalized_url = url.strip().rstrip("/")

        if not normalized_url:
            raise ValueError("url must not be empty")

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0")

        self.url = normalized_url
        self.api_key = api_key
        self.http_client = http_client or RequestsQdrantSnapshotHttpClient()
        self.timeout_seconds = timeout_seconds

    def create_snapshot(self, collection: str) -> QdrantSnapshotInfo:
        normalized_collection = _normalize_collection(collection)
        response = self.http_client.post(
            self._collection_snapshots_url(normalized_collection),
            headers=self._headers(),
            timeout=self.timeout_seconds,
        )
        _raise_for_status(response)
        return _parse_snapshot_response(response.json())

    def list_snapshots(self, collection: str) -> list[QdrantSnapshotInfo]:
        normalized_collection = _normalize_collection(collection)
        response = self.http_client.get(
            self._collection_snapshots_url(normalized_collection),
            headers=self._headers(),
            timeout=self.timeout_seconds,
        )
        _raise_for_status(response)
        data = response.json()
        snapshots = data.get("result", [])

        if not isinstance(snapshots, list):
            raise ValueError("Qdrant list snapshots response result must be a list")

        return [_parse_snapshot_item(item) for item in snapshots]

    def download_snapshot(
        self,
        collection: str,
        snapshot_name: str,
        output_path: str | Path,
    ) -> str:
        normalized_collection = _normalize_collection(collection)
        normalized_snapshot_name = _normalize_snapshot_name(snapshot_name)
        target_path = Path(output_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        response = self.http_client.get(
            (
                f"{self._collection_snapshots_url(normalized_collection)}"
                f"/{normalized_snapshot_name}"
            ),
            headers=self._headers(),
            timeout=self.timeout_seconds,
        )
        _raise_for_status(response)
        target_path.write_bytes(response.content)
        return str(target_path)

    def restore_snapshot(
        self,
        restore_collection: str,
        snapshot_path: str | Path,
    ) -> dict:
        normalized_collection = _normalize_collection(restore_collection)
        path = Path(snapshot_path)

        if not path.exists():
            raise FileNotFoundError(f"snapshot file does not exist: {snapshot_path}")

        with path.open("rb") as file:
            response = self.http_client.post(
                (
                    f"{self._collection_snapshots_url(normalized_collection)}"
                    "/upload?priority=snapshot"
                ),
                headers=self._headers(),
                files={"snapshot": file},
                timeout=self.timeout_seconds,
            )

        _raise_for_status(response)
        return response.json()

    def _collection_snapshots_url(self, collection: str) -> str:
        return f"{self.url}/collections/{collection}/snapshots"

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}

        return {"api-key": self.api_key}


def _normalize_collection(collection: str) -> str:
    normalized = collection.strip()

    if not normalized:
        raise ValueError("collection must not be empty")

    return normalized


def _normalize_snapshot_name(snapshot_name: str) -> str:
    normalized = snapshot_name.strip()

    if not normalized:
        raise ValueError("snapshot_name must not be empty")

    return normalized


def _raise_for_status(response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        raise RuntimeError(f"Qdrant snapshot request failed: {error}") from error


def _parse_snapshot_response(data: dict) -> QdrantSnapshotInfo:
    result = data.get("result")

    if isinstance(result, dict):
        return _parse_snapshot_item(result)

    raise ValueError("Qdrant snapshot response result must be an object")


def _parse_snapshot_item(item: dict) -> QdrantSnapshotInfo:
    name = item.get("name")

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Qdrant snapshot item is missing name")

    return QdrantSnapshotInfo(
        name=name,
        creation_time=item.get("creation_time"),
        size=item.get("size"),
    )
