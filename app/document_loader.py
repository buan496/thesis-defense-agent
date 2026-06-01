from pathlib import Path


def read_text_file(file_path: str) -> str:
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{file_path}")
    
    if not path.is_file():
        raise ValueError(f"路径不是一个文件：{file_path}")
    
    return path.read_text(encoding="utf-8")
