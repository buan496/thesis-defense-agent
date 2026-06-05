from app.vector_store_metadata import is_vector_store_metadata_match


def test_vector_store_metadata_match():
    metadata = {
        "source_file": "data/thesis.pdf",
        "embedding_model": "BAAI/bge-m3",
        "chunk_size": 800,
        "overlap": 100,
        "min_chunk_size": 30,
    }

    assert is_vector_store_metadata_match(
        metadata,
        source_file="data/thesis.pdf",
        embedding_model="BAAI/bge-m3",
        chunk_size=800,
        overlap=100,
        min_chunk_size=30,
    )


def test_vector_store_metadata_not_match():
    metadata = {
        "source_file": "data/thesis.pdf",
        "embedding_model": "BAAI/bge-m3",
        "chunk_size": 800,
        "overlap": 100,
        "min_chunk_size": 30,
    }

    assert not is_vector_store_metadata_match(
        metadata,
        source_file="data/other.pdf",
        embedding_model="BAAI/bge-m3",
        chunk_size=800,
        overlap=100,
        min_chunk_size=30,
    )