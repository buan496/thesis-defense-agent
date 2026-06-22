from app.llm import chat_with_llm


def summarize_training(
    question: str,
    answer: str,
    evaluation: str,
    rewritten_answer: str,
    follow_up_question: str,
    follow_up_answer: str,
    follow_up_evaluation: str,
) -> str:
    user_message = f"""
    请根据下面一轮论文答辩训练记录，总结本轮训练表现。

    重要限制：
    1. 只能基于给定训练记录总结，不要编造实验数据、用户人数、准确率或评分结果。
    2. 如果学生没有提供足够信息，要指出“目前尚未明确”，不要替学生编造技术细节。
    3. 总结要包含：本轮整体表现、主要薄弱点、下一轮训练建议。
    4. 输出中文正文即可，不要输出 Markdown 代码块。

    原始答辩问题：{question}
    学生回答：{answer}
    回答评价：{evaluation}
    改写后的回答：{rewritten_answer}
    追问：{follow_up_question}
    追问回答：{follow_up_answer}
    追问评价：{follow_up_evaluation}
    """

    return chat_with_llm(user_message)
