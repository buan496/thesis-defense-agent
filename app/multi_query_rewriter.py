from app.query_rewriter import rewrite_query


def generate_multi_queries(query: str) -> list[str]:
    queries = [query]
    rewritten_query = rewrite_query(query)

    if rewritten_query != query:
        queries.append(rewritten_query)

    if "系统" in query or "模块" in query:
        queries.append("系统架构 模块 特征处理 数据与词表 模型 训练 推理 Web服务")

    if "数据集" in query or "数据" in query:
        queries.append("AISHELL LibriSpeech train-clean dev-clean test-clean")

    if "语言感知" in query or "LAF" in query:
        queries.append(
            "LanguageAwareFrontend 卷积 BiLSTM 注意力池化 语言嵌入 语言分类"
        )

    if "改进" in query or "未来" in query or "后续" in query:
        queries.append("预训练微调 流式识别 数据扩展 模型压缩")

    return _deduplicate_queries(queries)


def _deduplicate_queries(queries: list[str]) -> list[str]:
    unique_queries = []

    for query in queries:
        normalized_query = query.strip()

        if not normalized_query:
            continue

        if normalized_query not in unique_queries:
            unique_queries.append(normalized_query)

    return unique_queries
