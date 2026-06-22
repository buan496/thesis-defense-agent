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

ANSWER_EVALUATION_TOOL = {
    "type": "function",
    "function": {
        "name": "evaluate_student_answer",
        "description": (
            "根据答辩问题和学生回答，评价回答质量并给出改进建议。"
            "适用于用户要求评分、诊断回答不足或生成参考回答时。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "需要评价的论文答辩问题",
                    "maxLength": 4000,
                },
                "student_answer": {
                    "type": "string",
                    "description": "学生对该答辩问题的回答",
                    "maxLength": 8000,
                },
            },
            "required": ["question", "student_answer"],
            "additionalProperties": False,
        },
    },
}

FOLLOW_UP_TOOL = {
    "type": "function",
    "function": {
        "name": "generate_follow_up",
        "description": (
            "根据答辩问题、学生回答以及可选评价反馈生成一个有针对性的追问。"
            "适用于用户要求继续追问、深入追问或模拟评委追问时。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "原始论文答辩问题",
                    "maxLength": 4000,
                },
                "student_answer": {
                    "type": "string",
                    "description": "学生对原始问题的回答",
                    "maxLength": 8000,
                },
                "evaluation": {
                    "type": "string",
                    "description": "可选的回答评价反馈",
                    "maxLength": 8000,
                },
                "rewritten_answer": {
                    "type": "string",
                    "description": "可选的改写后参考回答",
                    "maxLength": 8000,
                },
            },
            "required": ["question", "student_answer"],
            "additionalProperties": False,
        },
    },
}

TRAINING_RECORD_TOOL = {
    "type": "function",
    "function": {
        "name": "query_training_record",
        "description": (
            "根据 task_id 查询已经保存的论文答辩训练记录摘要，"
            "包括原问题、学生回答、评价、追问、追问评价和训练总结。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "需要查询的 DefenseTask ID",
                },
            },
            "required": ["task_id"],
            "additionalProperties": False,
        },
    },
}
