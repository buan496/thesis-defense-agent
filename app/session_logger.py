from pathlib import Path
from datetime import datetime




def save_session_markdown(
    question, 
    student_answer, 
    evaluation, 
    rewritten_answer, 
    follow_up_question, 
    follow_up_answer, 
    follow_up_evaluation
    ):
    session_dir = Path("data") / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    file_path = session_dir / f"{timestamp}.md"

    content = f"""
    # 论文答辩训练记录

    ## 答辩问题

    {question}

    ## 学生回答

    {student_answer}

    ## 评价反馈

    {evaluation}

    ## 改写后的回答

    {rewritten_answer}

    ## 追问

    {follow_up_question}

    ## 追问回答

    {follow_up_answer}

    ## 追问评价

    {follow_up_evaluation}
    """

    file_path.write_text(content, encoding="utf-8")

    return file_path