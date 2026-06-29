import logging
import time
from pathlib import Path

from app.config import (
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RAG_MIN_CHUNK_SIZE,
    RAG_VECTOR_STORE_PATH,
    EMBEDDING_MODEL, 
    RAG_VECTOR_STORE_META_PATH,
    VECTOR_STORE_BACKEND,
)
from app.document_cleaner import (
    normalize_pdf_line_breaks,
    remove_invalid_unicode,
    remove_table_of_contents_lines,
)
from app.embeddings import create_embedding
from app.pdf_loader import read_pdf_file
from app.text_splitter import split_text_by_paragraphs_with_metadata
from app.vector_store_metadata import (
    save_vector_store_metadata,
    load_vector_store_metadata,
    is_vector_store_metadata_match,
)
from app.vector_store_repository import (
    JsonVectorStoreRepository,
    VectorStoreRepository,
    create_vector_store_repository,
)



logger = logging.getLogger(__name__)

def build_pdf_vector_store(
    file_path: str = "data/thesis.pdf",
    chunk_size: int = RAG_CHUNK_SIZE,
    overlap: int = RAG_CHUNK_OVERLAP,
    min_chunk_size: int = RAG_MIN_CHUNK_SIZE,  
    force: bool = False,
    vector_store_repository: VectorStoreRepository | None = None,
    ) -> None:
    
    start_time = time.perf_counter()

    text = read_pdf_file(file_path)
    text = remove_invalid_unicode(text)
    text = normalize_pdf_line_breaks(text)
    text = remove_table_of_contents_lines(text)

    meta_path = Path(RAG_VECTOR_STORE_META_PATH)

    if meta_path.exists():
        metadata = load_vector_store_metadata(RAG_VECTOR_STORE_META_PATH)

        if not is_vector_store_metadata_match(
            metadata,
            source_file=file_path,
            embedding_model=EMBEDDING_MODEL,
            chunk_size=chunk_size,
            overlap=overlap,
            min_chunk_size=min_chunk_size,
        ):
            logger.warning("当前构建参数与已有向量库元信息不一致")
            logger.warning("已有元信息: %s", metadata)
            logger.warning(
                "当前参数: source_file=%s, embedding_model=%s, chunk_size=%s, overlap=%s, min_chunk_size=%s",
                file_path,
                EMBEDDING_MODEL,
                chunk_size,
                overlap,
                min_chunk_size,
            )
        
        if not force:
            raise ValueError(
                "向量库元信息与当前构建参数不一致，不能断点恢复。"
                "请先删除 data/vector_store.json 和 data/vector_store_meta.json，"
                "或后续使用 --force 重新构建。"
            )    
        logger.warning("已启用 force，将删除旧向量库并重新构建")
        vector_store_path = Path(RAG_VECTOR_STORE_PATH)
        meta_path = Path(RAG_VECTOR_STORE_META_PATH)

        if vector_store_path.exists():
            vector_store_path.unlink()

        if meta_path.exists():
            meta_path.unlink()
                    
    chunks = split_text_by_paragraphs_with_metadata(
        text,
        source=file_path,
        chunk_size=chunk_size,
        overlap=overlap,
        min_chunk_size=min_chunk_size,
    )

    logger.info("chunk 数量: %s", len(chunks))

    repository = vector_store_repository or create_vector_store_repository(
        backend=VECTOR_STORE_BACKEND,
        vector_store_path=RAG_VECTOR_STORE_PATH,
    )
    store_path = Path(RAG_VECTOR_STORE_PATH)

    if store_path.exists() and isinstance(repository, JsonVectorStoreRepository):
        logger.info("发现已有向量库，尝试断点恢复: %s", RAG_VECTOR_STORE_PATH)
        store = repository.load()
    else:
        if store_path.exists():
            logger.info(
                "当前向量库后端不支持本地 JSON 断点恢复，将从头构建: %s",
                VECTOR_STORE_BACKEND,
            )
        store = []

    existing_ids = {item["id"] for item in store}

    save_every = 5
    processed_since_save = 0

    for chunk in chunks:
        if chunk["id"] in existing_ids:
            logger.info("跳过已处理 chunk: %s", chunk["id"])
            continue

        logger.info("正在生成 embedding: chunk %s/%s", chunk["id"], len(chunks))

        item = {
            "id": chunk["id"],
            "text": chunk["text"],
            "source": chunk["source"],
            "length": chunk["length"],
            "embedding": create_embedding(chunk["text"]),
        }

        store.append(item)
        existing_ids.add(chunk["id"])
        processed_since_save += 1

        if processed_since_save >= save_every:
            repository.save(store)
            logger.info("已保存断点，当前向量数量: %s", len(store))
            processed_since_save = 0

    repository.save(store)
    save_vector_store_metadata(
    RAG_VECTOR_STORE_META_PATH,
        source_file=file_path,
        embedding_model=EMBEDDING_MODEL,
        chunk_size=chunk_size,
        overlap=overlap,
        min_chunk_size=min_chunk_size,
    )
    
    logger.info("向量库已保存: %s", RAG_VECTOR_STORE_PATH)
    logger.info("向量库元信息已保存: %s", RAG_VECTOR_STORE_META_PATH)
