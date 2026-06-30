import pytest

from app.mcp_resources import (
    list_mcp_resource_schemas,
    read_mcp_resource,
)


def test_list_mcp_resource_schemas_includes_summary_readme_progress():
    resources = list_mcp_resource_schemas()
    uris = [resource["uri"] for resource in resources]

    assert "thesis://summary" in uris
    assert "thesis://readme" in uris
    assert "thesis://progress" in uris


def test_read_mcp_summary_resource():
    result = read_mcp_resource("thesis://summary")

    assert result["contents"][0]["uri"] == "thesis://summary"
    assert result["contents"][0]["mimeType"] == "text/plain"
    assert "Thesis Defense Agent" in result["contents"][0]["text"]


def test_read_mcp_readme_resource():
    result = read_mcp_resource("thesis://readme")

    assert result["contents"][0]["uri"] == "thesis://readme"
    assert result["contents"][0]["mimeType"] == "text/markdown"
    assert "Thesis Defense Agent" in result["contents"][0]["text"]


def test_read_mcp_resource_rejects_unknown_uri():
    with pytest.raises(ValueError, match="unknown resource uri"):
        read_mcp_resource("thesis://missing")
