from typing import List


def detect_and_format_tables(text: str) -> str:
    """
    Detect contiguous blocks of tab-separated values (TSV) within the input text
    and convert those blocks into GitHub-flavored Markdown tables. Non-tabular
    content is preserved as-is.

    The first row of a TSV block is treated as the header row. The number of
    columns is derived from the widest row in the block; narrower rows are
    padded with empty cells to keep the table rectangular.
    """
    if not text or "\t" not in text:
        return text

    lines = text.split("\n")
    result_lines: List[str] = []

    i = 0
    n = len(lines)
    while i < n:
        if _is_tsv_row(lines[i]):
            # Start of a TSV block
            start = i
            end = i
            while end + 1 < n and _is_tsv_row(lines[end + 1]):
                end += 1

            block = lines[start : end + 1]
            # Only convert if we have at least 2 rows or at least one row with 2+ columns
            if _should_convert_block(block):
                md_block = _convert_tsv_block_to_markdown(block)
                # Surround table with blank lines to ensure proper Markdown rendering
                if result_lines and result_lines[-1].strip() != "":
                    result_lines.append("")
                result_lines.extend(md_block.split("\n"))
                if end + 1 < n and lines[end + 1].strip() != "":
                    result_lines.append("")
            else:
                # Not confident it's a table; keep original lines
                result_lines.extend(block)

            i = end + 1
        else:
            result_lines.append(lines[i])
            i += 1

    return "\n".join(result_lines)


def _is_tsv_row(line: str) -> bool:
    if "\t" not in line:
        return False
    # Consider it TSV if it yields at least 2 columns after splitting
    parts = line.split("\t")
    return len(parts) > 1


def _should_convert_block(block_lines: List[str]) -> bool:
    """
    Heuristic to reduce false positives:
    - Treat as table if there are at least 2 TSV rows, or
    - A single TSV row with >= 3 columns (common for compact single-row outputs)
    """
    if len(block_lines) >= 2:
        return True
    # Single line: require 3+ columns to avoid accidental conversion
    parts = block_lines[0].split("\t")
    return len(parts) >= 3


def _convert_tsv_block_to_markdown(block_lines: List[str]) -> str:
    rows = [
        [cell.strip() for cell in line.split("\t")] for line in block_lines
    ]
    max_cols = max(len(r) for r in rows) if rows else 0
    if max_cols <= 1:
        return "\n".join(block_lines)

    # Normalize row widths and escape pipes
    norm_rows: List[List[str]] = []
    for r in rows:
        padded = r + [""] * (max_cols - len(r))
        escaped = [_escape_markdown_cell(c) for c in padded]
        norm_rows.append(escaped)

    # Treat first row as header
    header = norm_rows[0]
    body = norm_rows[1:] if len(norm_rows) > 1 else []

    md_lines: List[str] = []
    md_lines.append("| " + " | ".join(header) + " |")
    md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")
    for row in body:
        md_lines.append("| " + " | ".join(row) + " |")

    return "\n".join(md_lines)


def _escape_markdown_cell(text: str) -> str:
    # Escape pipes to keep table structure intact; leave other characters alone
    return text.replace("|", "\\|")


