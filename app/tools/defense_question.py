from collections.abc import Callable

from app.defense_questions import generate_questions_from_context


def create_defense_questions(
    context: str,
    generator_fn: Callable[[str], list[str]] = generate_questions_from_context,
) -> list[str]:
    if not context.strip():
        raise ValueError("context 不能为空")

    if len(context) > 12000:
        raise ValueError("context 长度不能超过 12000 个字符")

    return generator_fn(context)