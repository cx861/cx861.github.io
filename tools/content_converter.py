#!/usr/bin/env python3
"""Convert Markdown study notes into safe HTML content fragments."""

from __future__ import annotations

import argparse
import html
import re
import sys
import unicodedata
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
INLINE_MATH_RE = re.compile(r"(?<!\\)(\$(?!\$).+?(?<!\\)\$)")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")
UNORDERED_LIST_RE = re.compile(r"^\s*[-+*]\s+(.+)$")
ORDERED_LIST_RE = re.compile(r"^\s*\d+[.)]\s+(.+)$")
HORIZONTAL_RULE_RE = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")


def slugify(text: str) -> str:
    """Return a deterministic, URL-friendly heading identifier."""
    plain = re.sub(r"[`*_~$]", "", text)
    normalized = unicodedata.normalize("NFKC", plain).strip().lower()
    slug = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", normalized, flags=re.UNICODE)
    return slug.strip("-") or "section"


def render_inline(text: str) -> str:
    code_tokens: list[str] = []
    math_tokens: list[str] = []

    def keep_code(match: re.Match[str]) -> str:
        code_tokens.append(f"<code>{html.escape(match.group(1), quote=False)}</code>")
        return f"@@CODE{len(code_tokens) - 1}@@"

    def keep_math(match: re.Match[str]) -> str:
        math_tokens.append(html.escape(match.group(1), quote=False))
        return f"@@MATH{len(math_tokens) - 1}@@"

    rendered = INLINE_CODE_RE.sub(keep_code, text)
    rendered = INLINE_MATH_RE.sub(keep_math, rendered)
    rendered = html.escape(rendered, quote=False)
    rendered = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", rendered)
    for index, token in enumerate(math_tokens):
        rendered = rendered.replace(f"@@MATH{index}@@", token)
    for index, token in enumerate(code_tokens):
        rendered = rendered.replace(f"@@CODE{index}@@", token)
    return rendered


def split_table_row(line: str) -> list[str]:
    """Split a Markdown table row without breaking pipes in math or code."""
    row = line.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]

    cells: list[str] = []
    current: list[str] = []
    in_code = False
    in_math = False
    escaped = False
    for character in row:
        if escaped:
            current.append(character)
            escaped = False
            continue
        if character == "\\":
            current.append(character)
            escaped = True
            continue
        if character == "`" and not in_math:
            in_code = not in_code
        elif character == "$" and not in_code:
            in_math = not in_math
        if character == "|" and not in_code and not in_math:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    cells.append("".join(current).strip())
    return cells


def is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines) or "|" not in lines[index]:
        return False
    separators = split_table_row(lines[index + 1])
    return bool(separators) and all(
        TABLE_SEPARATOR_RE.fullmatch(cell) for cell in separators
    )


def render_table(lines: list[str], start: int) -> tuple[str, int]:
    headers = split_table_row(lines[start])
    rows: list[list[str]] = []
    index = start + 2
    while index < len(lines) and lines[index].strip() and "|" in lines[index]:
        rows.append(split_table_row(lines[index]))
        index += 1

    output = ['<div class="table-wrapper">', "<table>", "<thead>", "<tr>"]
    output.extend(f"<th>{render_inline(cell)}</th>" for cell in headers)
    output.extend(["</tr>", "</thead>", "<tbody>"])
    for row in rows:
        output.append("<tr>")
        padded = row + [""] * max(0, len(headers) - len(row))
        output.extend(f"<td>{render_inline(cell)}</td>" for cell in padded[: len(headers)])
        output.append("</tr>")
    output.extend(["</tbody>", "</table>", "</div>"])
    return "\n".join(output), index


def convert_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    used_slugs: dict[str, int] = {}

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    index = 0
    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            index += 1
            continue
        if line.startswith("```"):
            flush_paragraph()
            language = line[3:].strip()
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            language_attribute = (
                f' class="language-{html.escape(language, quote=True)}"'
                if language
                else ""
            )
            code = html.escape("\n".join(code_lines), quote=True)
            output.append(f"<pre><code{language_attribute}>{code}</code></pre>")
            continue
        if line == "$$":
            flush_paragraph()
            math_lines = ["$$"]
            index += 1
            while index < len(lines) and lines[index].strip() != "$$":
                math_lines.append(lines[index])
                index += 1
            if index < len(lines):
                math_lines.append("$$")
                index += 1
            math = html.escape("\n".join(math_lines), quote=False)
            output.append(f'<div class="math-block">{math}</div>')
            continue
        if line.startswith(">"):
            flush_paragraph()
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].lstrip())
                index += 1
            quote_content = "<br>\n".join(
                render_inline(item) for item in quote_lines
            )
            output.append(f"<blockquote>{quote_content}</blockquote>")
            continue
        if HORIZONTAL_RULE_RE.fullmatch(line):
            flush_paragraph()
            output.append("<hr>")
            index += 1
            continue
        unordered = UNORDERED_LIST_RE.match(raw_line)
        ordered = ORDERED_LIST_RE.match(raw_line)
        if unordered or ordered:
            flush_paragraph()
            list_pattern = UNORDERED_LIST_RE if unordered else ORDERED_LIST_RE
            tag = "ul" if unordered else "ol"
            items: list[str] = []
            while index < len(lines):
                item = list_pattern.match(lines[index])
                if not item:
                    break
                items.append(item.group(1))
                index += 1
            output.append(
                "\n".join(
                    [f"<{tag}>", *(f"<li>{render_inline(item)}</li>" for item in items), f"</{tag}>"]
                )
            )
            continue
        if is_table_start(lines, index):
            flush_paragraph()
            table, index = render_table(lines, index)
            output.append(table)
            continue
        heading = HEADING_RE.match(line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            label = heading.group(2)
            base_slug = slugify(label)
            count = used_slugs.get(base_slug, 0) + 1
            used_slugs[base_slug] = count
            heading_id = base_slug if count == 1 else f"{base_slug}-{count}"
            output.append(
                f'<h{level} id="{html.escape(heading_id, quote=True)}">'
                f"{render_inline(label)}</h{level}>"
            )
            index += 1
            continue
        paragraph.append(line)
        index += 1

    flush_paragraph()
    return "\n".join(output) + ("\n" if output else "")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert Markdown study notes to an HTML fragment."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    convert = subparsers.add_parser("convert", help="Convert one Markdown file.")
    convert.add_argument("--input", type=Path, required=True)
    convert.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "convert":
        if not args.input.is_file():
            print(f"Input Markdown file not found: {args.input}", file=sys.stderr)
            return 2
        if args.input.resolve() == args.output.resolve():
            print("Input and output paths must be different.", file=sys.stderr)
            return 2
        markdown = args.input.read_text(encoding="utf-8")
        rendered = convert_markdown(markdown)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"Converted {args.input} -> {args.output}")
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
