def rewrite_query(query: str) -> str:
    additions = []

    if "系统" in query or "模块" in query:
        additions.extend(
            [
                "系统架构",
                "模块",
                "特征处理",
                "数据与词表",
                "模型",
                "训练",
                "推理",
                "Web服务",
            ]
        )

    if "数据集" in query or "数据" in query:
        additions.extend(
            [
                "AISHELL",
                "LibriSpeech",
                "train-clean",
                "dev-clean",
                "test-clean",
            ]
        )

    if "语言感知" in query or "LAF" in query:
        additions.extend(
            [
                "LanguageAwareFrontend",
                "卷积",
                "BiLSTM",
                "注意力池化",
                "语言嵌入",
                "语言分类",
            ]
        )

    if "改进" in query or "未来" in query or "后续" in query:
        additions.extend(
            [
                "预训练微调",
                "流式识别",
                "数据扩展",
                "模型压缩",
            ]
        )

    if not additions:
        return query

    unique_additions = []

    for item in additions:
        if item not in unique_additions and item not in query:
            unique_additions.append(item)

    if not unique_additions:
        return query

    return query + " " + " ".join(unique_additions)
