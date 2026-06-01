import pytest
from app.document_loader import read_text_file


def test_read_text_file(tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello", encoding="utf-8")

    content = read_text_file(str(file_path))

    assert content == "hello"
      

def test_read_text_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_text_file("not_exist.txt")