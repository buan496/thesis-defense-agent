from app.embeddings import create_fake_embedding


def test_create_fake_embedding():
    vector = create_fake_embedding("论文答辩系统")

    assert vector == [6.0, 1.0, 1.0]