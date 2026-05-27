from app.defense_questions import _clean_json_text


def test_clean_json_text_plain_json():
    text = '{"questions": ["问题1"]}'
    expected = '{"questions": ["问题1"]}'
    assert _clean_json_text(text) == expected


def test_clean_json_text_markdown_json_block():
    text = '''```json
{"questions": ["问题1"]}
```'''
    expected = '{"questions": ["问题1"]}'
    assert _clean_json_text(text) == expected


def test_clean_json_text_extra_text():
    text = '''下面是 JSON：
{"questions": ["问题1"]}
希望对你有帮助'''
    expected = '{"questions": ["问题1"]}'
    assert _clean_json_text(text) == expected