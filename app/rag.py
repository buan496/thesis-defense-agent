from app.llm import chat_with_llm



def build_context_from_results(results: list[dict]) -> str:
    context_parts = []

    for result in results:
        context_parts.append(
            f"Chunk ID：{result['id']}\n"
            f"Score：{result['score']}\n"
            f"来源：{result['source']}\n"
            f"内容：{result['text']}"
        )

    return "\n\n---\n\n".join(context_parts)





def answer_with_context(question: str, context: str) -> str:
    user_message = f"""
请根据给定论文片段回答问题。

要求：
1. 只能依据论文片段回答。
2. 如果论文片段中没有相关信息，请回答“论文片段中没有提供足够信息”。
3. 不要编造论文中没有的内容。

论文片段：
{context}

问题：
{question}
"""

    return chat_with_llm(user_message)