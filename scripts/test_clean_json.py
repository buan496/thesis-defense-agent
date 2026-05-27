from app.defense_questions import _clean_json_text

expected = '{"questions": ["问题1"]}'

case1 = '{"questions": ["问题1"]}'
case2 = '''```json
{"questions": ["问题1"]}
```'''
case3 = '''下面是 JSON：
{"questions": ["问题1"]}
希望对你有帮助'''

assert _clean_json_text(case1) == expected
assert _clean_json_text(case2) == expected
assert _clean_json_text(case3) == expected

print("所有 _clean_json_text 测试通过")