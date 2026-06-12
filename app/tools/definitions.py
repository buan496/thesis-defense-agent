THESIS_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_thesis",
        "description": "根据用户问题检索论文中的相关内容，并返回最相关的论文片段。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "需要从论文中检索的问题或主题",
                },
                "top_k": {
                    "type": "integer",
                    "description": "需要返回的论文片段数量",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}

DEFENSE_QUESTION_TOOL = {
    "type": "function",
    "function": {
        "name": "create_defense_questions",
        "description": (
            "根据已经检索到的论文片段生成中文论文答辩问题。"
            "调用前应先通过 search_thesis 获取论文内容。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "context": {
                    "type": "string",
                    "description": "用于生成答辩问题的论文原文片段",
                    "maxLength": 12000,
                },
            },
            "required": ["context"],
            "additionalProperties": False,
        },
    },
}
