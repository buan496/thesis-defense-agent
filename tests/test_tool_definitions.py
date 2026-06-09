from app.tools import THESIS_SEARCH_TOOL


def test_thesis_search_tool_definition():
    function = THESIS_SEARCH_TOOL["function"]
    parameters = function["parameters"]

    assert THESIS_SEARCH_TOOL["type"] == "function"
    assert function["name"] == "search_thesis"
    assert "query" in parameters["properties"]
    assert "query" in parameters["required"]