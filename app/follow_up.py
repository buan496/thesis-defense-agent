from app.llm import chat_with_llm

def generate_follow_up_question(question, student_answer):
    user_message = f"""
    
    请根据下面的问题和答案，生成1个追问。
    参考回答必须围绕当前论文问题，不要使用电商、订单、评论等与论文无关的业务案例。
    如果需要举例，应使用问题中已有的模块或论文相关模块。            

    要求：
    请根据原始答辩问题和学生回答，生成 1 个有针对性的中文追问。
    追问要聚焦回答中的模糊、不充分或值得深入的地方。
    不要评价学生回答，只输出追问问题。
    
    问题：{question}
    答案：{student_answer}
    """
    
    follow_up_question = chat_with_llm(user_message)
    return follow_up_question