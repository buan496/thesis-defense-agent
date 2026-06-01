from app.document_cleaner import remove_table_of_contents_lines


def test_remove_table_of_contents_lines():
    text = """目录
4.2 数据准备模块        38
4.3 模型训练模块        39
这是正文内容。
参考文献        43
"""

    cleaned = remove_table_of_contents_lines(text)

    assert "4.2 数据准备模块" not in cleaned
    assert "4.3 模型训练模块" not in cleaned
    assert "参考文献        43" not in cleaned
    assert "这是正文内容。" in cleaned