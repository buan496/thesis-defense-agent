from pathlib import Path
from datetime import datetime


from app.session_models import DefenseSession


def save_session_markdown(session: DefenseSession) -> Path:
    session_dir = Path("data") / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    file_path = session_dir / f"{timestamp}.md"

    content = f"""
    # 论文答辩训练记录

    ## 训练方向

    {session.training_query}

    ## 检索上下文

    {session.retrieved_context}
    ## 答辩问题

    {session.question}

    ## 学生回答

    {session.student_answer}

    ## 评价反馈

    {session.evaluation}

    ## 改写后的回答

    {session.rewritten_answer}

    ## 追问

    {session.follow_up_question}

    ## 追问回答

    {session.follow_up_answer}

    ## 追问评价

    {session.follow_up_evaluation}
    """

    file_path.write_text(content, encoding="utf-8")

    return file_path