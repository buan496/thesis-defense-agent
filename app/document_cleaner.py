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