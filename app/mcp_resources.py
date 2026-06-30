from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class McpResourceSpec:
    uri: str
    name: str
    description: str
    mime_type: str


RESOURCE_SPECS = {
    "thesis://summary": McpResourceSpec(
        uri="thesis://summary",
        name="Thesis Defense Agent Summary",
        description="High-level project summary for the thesis defense agent.",
        mime_type="text/plain",
    ),
    "thesis://readme": McpResourceSpec(
        uri="thesis://readme",
        name="Project README",
        description="Current README describing project capabilities and usage.",
        mime_type="text/markdown",
    ),
    "thesis://progress": McpResourceSpec(
        uri="thesis://progress",
        name="Project Progress",
        description="Current progress document for the learning roadmap.",
        mime_type="text/markdown",
    ),
}


def list_mcp_resource_schemas() -> list[dict[str, Any]]:
    return [
        {
            "uri": resource.uri,
            "name": resource.name,
            "description": resource.description,
            "mimeType": resource.mime_type,
        }
        for resource in RESOURCE_SPECS.values()
    ]


def read_mcp_resource(uri: str) -> dict[str, Any]:
    if uri not in RESOURCE_SPECS:
        raise ValueError(f"unknown resource uri: {uri}")

    resource = RESOURCE_SPECS[uri]
    return {
        "contents": [
            {
                "uri": resource.uri,
                "mimeType": resource.mime_type,
                "text": _read_resource_text(uri),
            }
        ]
    }


def _read_resource_text(uri: str) -> str:
    if uri == "thesis://summary":
        return (
            "Thesis Defense Agent is a local learning project for building an "
            "auditable thesis defense training Agent. It covers RAG, Tool "
            "Calling, Agent Harness, Task State, Memory, Sub-Agent governance, "
            "LangGraph side-by-side learning, FastAPI, observability, MCP, "
            "Docker, PostgreSQL, and Qdrant integration."
        )

    if uri == "thesis://readme":
        return _read_text_file(Path("README.md"))

    if uri == "thesis://progress":
        return _read_text_file(Path("docs/01-当前进度.md"))

    raise ValueError(f"unknown resource uri: {uri}")


def _read_text_file(path: Path) -> str:
    if not path.exists():
        raise ValueError(f"resource file does not exist: {path}")

    return path.read_text(encoding="utf-8")
