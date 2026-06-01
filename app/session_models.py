from dataclasses import dataclass


@dataclass
class DefenseSession:
    training_query: str
    retrieved_context: str
    question: str
    student_answer: str
    evaluation: str
    rewritten_answer: str
    follow_up_question: str
    follow_up_answer: str
    follow_up_evaluation: str