from app.tools import (
    ANSWER_EVALUATION_TOOL,
    DEFENSE_QUESTION_TOOL,
    FOLLOW_UP_TOOL,
    THESIS_SEARCH_TOOL,
    TRAINING_RECORD_TOOL,
)


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


def test_answer_evaluation_tool_definition():
    function = ANSWER_EVALUATION_TOOL["function"]
    parameters = function["parameters"]
    properties = parameters["properties"]

    assert ANSWER_EVALUATION_TOOL["type"] == "function"
    assert function["name"] == "evaluate_student_answer"
    assert parameters["required"] == [
        "question",
        "student_answer",
    ]
    assert parameters["additionalProperties"] is False
    assert properties["question"]["type"] == "string"
    assert properties["question"]["maxLength"] == 4000
    assert properties["student_answer"]["type"] == "string"
    assert properties["student_answer"]["maxLength"] == 8000


def test_follow_up_tool_definition():
    function = FOLLOW_UP_TOOL["function"]
    parameters = function["parameters"]
    properties = parameters["properties"]

    assert FOLLOW_UP_TOOL["type"] == "function"
    assert function["name"] == "generate_follow_up"
    assert parameters["required"] == [
        "question",
        "student_answer",
    ]
    assert parameters["additionalProperties"] is False
    assert properties["question"]["type"] == "string"
    assert properties["question"]["maxLength"] == 4000
    assert properties["student_answer"]["type"] == "string"
    assert properties["student_answer"]["maxLength"] == 8000
    assert properties["evaluation"]["type"] == "string"
    assert properties["rewritten_answer"]["type"] == "string"


def test_training_record_tool_definition():
    function = TRAINING_RECORD_TOOL["function"]
    parameters = function["parameters"]
    properties = parameters["properties"]

    assert TRAINING_RECORD_TOOL["type"] == "function"
    assert function["name"] == "query_training_record"
    assert parameters["required"] == ["task_id"]
    assert parameters["additionalProperties"] is False
    assert properties["task_id"]["type"] == "string"
