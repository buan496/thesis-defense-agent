from app.llm import chat_with_llm


def rewrite_answer(
    question: str,
    student_answer: str,
    evaluation: str | None = None,
) -> str:
    evaluation_text = ""

    if evaluation:
        evaluation_text = f"""
    评价反馈：{evaluation}
    """

    user_message = f"""
    
    请根据下面的问题和答案，帮学生润色和改写答案，使其更符合论文答辩的风格和要求。
    重要限制：
    1. 严禁编造实验数据、专家人数、用户人数、准确率、百分比、评分结果。
    2. 如果学生回答中没有提供实验数据，只能说“可以补充某类实验设计”，不能虚构实验结果。
    3. 参考回答必须基于学生已经提供的信息。
    4. 对于没有数据支撑的内容，要使用“可以从……角度设计评估”，不能写成“已经完成……实验”。
    不要虚构具体实验人数、样本数量、评分结果或百分比。
    如果需要提出实验设计，只能使用“若干名专家”“若干篇论文”“评分量表”等模糊表述。
    要求：
    1. 不要编造实验数据
    2. 不要改变学生原意
    3. 可以补充表达结构和逻辑
    4. 如果原回答信息不足，要用“可以从……角度说明”，不要写成已经完成
    只输出改写后的答辩回答正文，不要输出解释、标题、分隔线或“根据您的回答”之类的话。
    如果学生回答是“不清楚”“不知道”或信息极少，不要替学生编造具体技术方案。
    只能把回答改写为：目前尚未明确，并建议可以从哪些方向补充思考。
    问题：{question}
    答案：{student_answer}
    {evaluation_text}
    """
    
    rewritten_answer = chat_with_llm(user_message)
    return rewritten_answer
