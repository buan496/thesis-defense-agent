from app.vector_store_io import save_vector_store, load_vector_store


def test_save_and_load_vector_store(tmp_path):
    file_path = tmp_path / "store.json"

    store = [
        {
            "id": 0,
            "text": "论文系统",
            "source": "data/thesis.txt",
            "embedding": [0.1, 0.2, 0.3],
        }
    ]

    save_vector_store(store, str(file_path))
    loaded = load_vector_store(str(file_path))

    assert loaded == store