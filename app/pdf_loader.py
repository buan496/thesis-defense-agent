from pathlib import Path
from pypdf import PdfReader


def read_pdf_file(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF 文件不存在：{file_path}")

    if not path.is_file():
        raise ValueError(f"路径不是文件：{file_path}")

    reader = PdfReader(str(path))

    pages_text = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            pages_text.append(page_text)

    return "\n\n".join(pages_text)