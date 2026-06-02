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
    
from app.document_cleaner import normalize_pdf_line_breaks


def test_normalize_pdf_line_breaks_joins_chinese_lines():
    text = "训\n练控制"

    cleaned = normalize_pdf_line_breaks(text)

    assert "训练控制" in cleaned
    
    
def test_normalize_pdf_line_breaks_keeps_non_chinese_newline():
    text = "第 4 章\n4.1 系统架构"

    cleaned = normalize_pdf_line_breaks(text)

    assert "第 4 章" in cleaned
    assert "4.1 系统架构" in cleaned