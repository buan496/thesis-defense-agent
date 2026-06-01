

def split_text(text: str,chunk_size: int = 500,overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    
    if overlap < 0:
        raise ValueError("overlap must be a non-negative integer")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks
        
    
def split_text_with_metadata(
    text: str,
    source: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap must be greater than or equal to 0")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    
    chunks = []
    start = 0
    chunk_id = 0
    
    while start < len(text):
        end = min(start + chunk_size,len(text))
        chunk_text = text[start:end]
        
        chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "start": start,
            "end": end,
            "source": source,
        })
        
        start = end - overlap
        chunk_id += 1
        
        if end == len(text):
            break
        
    return chunks

def split_by_paragraph(text: str) -> list[str]:
    paragraphs = text.split("\n\n")
    
    cleaned_parapraphs = []
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        
        if paragraph:
            cleaned_parapraphs.append(paragraph)
            
    return cleaned_parapraphs

def split_text_by_paragraphs_with_limit(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    min_chunk_size: int = 30,
) -> list[str]:
    chunks = []
    
    paragraphs = split_by_paragraph(text)
    
    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            if len(paragraph) >= min_chunk_size:
                chunks.append(paragraph)
        else:
            paragraph_chunks = split_text(
                paragraph,
                chunk_size=chunk_size,
                overlap=overlap
            )
            for chunk in paragraph_chunks:
                if len(chunk) >= min_chunk_size:
                    chunks.append(chunk)
            
    return chunks


def split_text_by_paragraphs_with_metadata(
    text: str,
    source: str,
    chunk_size: int = 500,
    overlap: int = 50,
    min_chunk_size: int = 30,
) -> list[dict]:
    chunk_texts = split_text_by_paragraphs_with_limit(
        text,
        chunk_size=chunk_size,
        overlap=overlap,
        min_chunk_size=min_chunk_size,
    )

    chunks = []

    for index, chunk_text in enumerate(chunk_texts):
        chunks.append({
            "id": index,
            "text": chunk_text,
            "source": source,
            "length": len(chunk_text),
        })

    return chunks