import json

json_text = """
{
  "questions": [
    "你的系统如何生成答辩问题？",
    "你的系统如何评价学生回答？",
    "你的系统如何生成追问？"
  ]
}
"""


data = json.loads(json_text)

questions = data["questions"]

print(questions)
print(questions[0])