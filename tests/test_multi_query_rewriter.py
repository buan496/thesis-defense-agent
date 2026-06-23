from app.multi_query_rewriter import generate_multi_queries


def test_generate_multi_queries_includes_original_query():
    queries = generate_multi_queries("论文题目是什么？")

    assert queries == ["论文题目是什么？"]


def test_generate_multi_queries_adds_rewritten_query():
    queries = generate_multi_queries("系统有哪些模块？")

    assert queries[0] == "系统有哪些模块？"
    assert any("系统架构" in query for query in queries)
    assert any("特征处理" in query for query in queries)


def test_generate_multi_queries_adds_dataset_query():
    queries = generate_multi_queries("论文使用了哪些数据集？")

    assert any("AISHELL" in query for query in queries)
    assert any("LibriSpeech" in query for query in queries)


def test_generate_multi_queries_adds_laf_query():
    queries = generate_multi_queries("语言感知前端包括什么？")

    assert any("LanguageAwareFrontend" in query for query in queries)
    assert any("BiLSTM" in query for query in queries)


def test_generate_multi_queries_adds_future_work_query():
    queries = generate_multi_queries("后续有哪些改进方向？")

    assert any("预训练微调" in query for query in queries)
    assert any("流式识别" in query for query in queries)


def test_generate_multi_queries_deduplicates_queries():
    queries = generate_multi_queries("AISHELL LibriSpeech 数据集")

    assert len(queries) == len(set(queries))
