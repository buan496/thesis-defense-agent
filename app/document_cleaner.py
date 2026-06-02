import re


def remove_table_of_contents_lines(text: str) -> str:
    toc_pattern = re.compile(r".+\s+\d+$")

    cleaned_lines = []

    for line in text.splitlines():
        stripped_line = line.strip()

        if toc_pattern.match(stripped_line):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)

def remove_invalid_unicode(text: str) -> str:
    return text.encode("utf-8", errors="ignore").decode("utf-8")


import re


def normalize_pdf_line_breaks(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"(?<=[\u4e00-\u9fff])\n(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text