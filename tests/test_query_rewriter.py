from app.query_rewriter import rewrite_query


def test_rewrite_query_adds_system_architecture_terms():
    rewritten = rewrite_query("系统有哪些模块？")

    assert "系统有哪些模块？" in rewritten
    assert "系统架构" in rewritten
    assert "特征处理" in rewritten
    assert "训练" in rewritten


def test_rewrite_query_adds_dataset_terms():
    rewritten = rewrite_query("论文使用了哪些数据集？")

    assert "AISHELL" in rewritten
    assert "LibriSpeech" in rewritten
    assert "train-clean" in rewritten


def test_rewrite_query_adds_laf_terms():
    rewritten = rewrite_query("语言感知前端包括什么？")

    assert "LanguageAwareFrontend" in rewritten
    assert "BiLSTM" in rewritten
    assert "注意力池化" in rewritten


def test_rewrite_query_adds_future_work_terms():
    rewritten = rewrite_query("后续有哪些改进方向？")

    assert "预训练微调" in rewritten
    assert "流式识别" in rewritten
    assert "模型压缩" in rewritten


def test_rewrite_query_does_not_duplicate_existing_terms():
    rewritten = rewrite_query("系统架构有哪些模块？")

    assert rewritten.count("系统架构") == 1
    assert rewritten.count("模块") == 1


def test_rewrite_query_returns_original_when_no_rule_matches():
    query = "论文题目是什么？"

    assert rewrite_query(query) == query
