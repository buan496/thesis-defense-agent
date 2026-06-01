import pytest
from app.text_splitter import split_text, split_text_with_metadata, split_by_paragraph,split_text_by_paragraphs_with_limit,split_text_by_paragraphs_with_metadata


def test_split_text_basic():
    text = "abcdefghij"
    chunks = split_text(text, chunk_size=4, overlap=1)

    assert chunks == ["abcd", "defg", "ghij", "j"]
    
def test_split_text_invalid_overlap():
    with pytest.raises(ValueError):
        split_text("abc", chunk_size=3, overlap=3)
        
        
        
def test_split_text_with_metadata():
    text = "abcdefghij"

    chunks = split_text_with_metadata(
        text,
        source="data/thesis.txt",
        chunk_size=4,
        overlap=1,
    )

    assert chunks[0]["id"] == 0
    assert chunks[0]["text"] == "abcd"
    assert chunks[0]["start"] == 0
    assert chunks[0]["end"] == 4
    assert chunks[0]["source"] == "data/thesis.txt"

    assert chunks[1]["id"] == 1
    assert chunks[1]["text"] == "defg"
    assert chunks[1]["start"] == 3
    assert chunks[1]["end"] == 7      
    
    
def test_split_by_paragraph():
    text = "第一段。\n\n第二段。\n\n第三段。"

    paragraphs = split_by_paragraph(text)

    assert paragraphs == ["第一段。", "第二段。", "第三段。"]
    
    
# def test_split_text_by_paragraphs_with_limit():
#     text = "短段。\n\nabcdefghij"

#     chunks = split_text_by_paragraphs_with_limit(
#         text,
#         chunk_size=4,
#         overlap=1,
#     )

#     assert chunks == ["短段。", "abcd", "defg", "ghij", "j"]
    
    
def test_split_text_by_paragraphs_filters_short_chunks():
    text = "短\n\n这是一个足够长的段落"

    chunks = split_text_by_paragraphs_with_limit(
        text,
        chunk_size=100,
        overlap=10,
        min_chunk_size=5,
    )

    assert chunks == ["这是一个足够长的段落"]
    
    
def test_split_text_by_paragraphs_with_metadata():
    text = "这是一个足够长的第一段。\n\n这是一个足够长的第二段。"

    chunks = split_text_by_paragraphs_with_metadata(
        text,
        source="data/thesis.txt",
        chunk_size=100,
        overlap=10,
        min_chunk_size=5,
    )

    assert chunks[0]["id"] == 0
    assert chunks[0]["text"] == "这是一个足够长的第一段。"
    assert chunks[0]["source"] == "data/thesis.txt"
    assert chunks[0]["length"] == len("这是一个足够长的第一段。")

    assert chunks[1]["id"] == 1
    assert chunks[1]["text"] == "这是一个足够长的第二段。"