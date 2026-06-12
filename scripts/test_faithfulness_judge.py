from app.faithfulness_evaluator import evaluate_faithfulness


question = "系统是否已经实现流式识别？"

evidence = """
论文指出，当前 Conformer 仍偏离线。
流式识别属于后续改进方向，需要改造成支持 chunk 级增量计算的结构。
"""

answers = [
    "当前系统尚未实现流式识别，它属于后续改进方向。",
    "当前系统已经完整实现了流式识别。",
]

for answer in answers:
    result = evaluate_faithfulness(
        question=question,
        answer=answer,
        evidence=evidence,
    )

    print("回答：", answer)
    print("分数：", result["score"])
    print("是否通过：", result["passed"])
    print("原因：", result["reason"])
    print("无依据声明：", result["unsupported_claims"])
    print("矛盾内容：", result["contradictions"])
    print("-" * 50)