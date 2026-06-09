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
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}