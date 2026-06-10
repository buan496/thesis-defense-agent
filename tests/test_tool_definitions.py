from app.tools import DEFENSE_QUESTION_TOOL, THESIS_SEARCH_TOOL


def test_thesis_search_tool_definition():
    function = THESIS_SEARCH_TOOL["function"]
    parameters = function["parameters"]

    assert THESIS_SEARCH_TOOL["type"] == "function"
    assert function["name"] == "search_thesis"
    assert "query" in parameters["properties"]
    assert "query" in parameters["required"]
    
    
def test_thesis_search_tool_limits_top_k():
    top_k_schema = (
        THESIS_SEARCH_TOOL["function"]
        ["parameters"]
        ["properties"]
        ["top_k"]
    )

    assert top_k_schema["minimum"] == 1
    assert top_k_schema["maximum"] == 10


def test_defense_question_tool_definition():
    function = DEFENSE_QUESTION_TOOL["function"]
    parameters = function["parameters"]
    context_schema = parameters["properties"]["context"]

    assert DEFENSE_QUESTION_TOOL["type"] == "function"
    assert function["name"] == "create_defense_questions"
    assert parameters["required"] == ["context"]
    assert parameters["additionalProperties"] is False
    assert context_schema["type"] == "string"
    assert context_schema["maxLength"] == 12000
