from app.embeddings import create_embedding

vector = create_embedding("论文答辩训练系统")

print(type(vector))
print(len(vector))
print(vector[:5])