#!/usr/bin/env python3
"""Audit a generated static site through a small command-line interface."""

from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


IGNORED_DIRECTORIES = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "dist",
    "node_modules",
    "output",
    "site",
    "tests",
    "tmp_docx_render",
}
EXTERNAL_SCHEMES = {"data", "http", "https", "javascript", "mailto", "tel"}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.ids: set[str] = set()
        self.references: list[str] = []
        self.lang = ""
        self.h1_count = 0
        self.has_viewport = False
        self.has_main = False
        self.has_site_nav = False
        self.has_site_footer = False
        self.has_skip_link = False
        self.has_toc = False
        self.has_mathjax = False
        self.description = ""
        self.canonical_url = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): value or "" for name, value in attrs}
        classes = set(attributes.get("class", "").split())
        tag = tag.lower()

        if tag == "html":
            self.lang = attributes.get("lang", "")
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.has_main = True
        elif tag == "meta":
            meta_name = attributes.get("name", "").lower()
            if meta_name == "viewport":
                self.has_viewport = True
            elif meta_name == "description":
                self.description = attributes.get("content", "").strip()
        elif tag == "link" and attributes.get("rel", "").lower() == "canonical":
            self.canonical_url = attributes.get("href", "").strip()

        element_id = attributes.get("id")
        if element_id:
            self.ids.add(element_id)

        if "site-nav" in classes:
            self.has_site_nav = True
        if "site-footer" in classes:
            self.has_site_footer = True
        if "skip-link" in classes:
            self.has_skip_link = True
        if "toc" in classes:
            self.has_toc = True

        for attribute in ("href", "src"):
            value = attributes.get(attribute)
            if value:
                self.references.append(value)
                if "mathjax" in value.lower():
                    self.has_mathjax = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())


def discover_pages(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*.html")
            if not any(part in IGNORED_DIRECTORIES for part in path.relative_to(root).parts)
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def is_external(reference: str) -> bool:
    if reference.startswith("//"):
        return True
    return urlsplit(reference).scheme.lower() in EXTERNAL_SCHEMES


def resolve_local_target(root: Path, page: Path, reference: str) -> Path:
    reference_path = unquote(urlsplit(reference).path)
    if reference_path.startswith("/"):
        return (root / reference_path.lstrip("/")).resolve()
    return (page.parent / reference_path).resolve()


def scan_site(root: Path) -> dict[str, object]:
    root = root.resolve()
    page_records: list[dict[str, object]] = []
    broken_targets: list[dict[str, str]] = []
    broken_anchors: list[dict[str, str]] = []
    broken_cross_page_anchors: list[dict[str, str]] = []
    pages = discover_pages(root)
    parsed_pages = {page.resolve(): parse_page(page) for page in pages}

    for page in pages:
        parser = parsed_pages[page.resolve()]
        relative_path = page.relative_to(root).as_posix()
        local_link_count = 0

        for reference in parser.references:
            if is_external(reference):
                continue
            parts = urlsplit(reference)
            if not parts.path:
                if parts.fragment and parts.fragment not in parser.ids:
                    broken_anchors.append({"source": relative_path, "target": reference})
                continue

            local_link_count += 1
            target = resolve_local_target(root, page, reference)
            if not target.exists():
                broken_targets.append({"source": relative_path, "target": reference})
            elif parts.fragment and target.suffix.lower() in {".htm", ".html"}:
                target_parser = parsed_pages.get(target)
                if target_parser is None:
                    target_parser = parse_page(target)
                    parsed_pages[target] = target_parser
                if unquote(parts.fragment) not in target_parser.ids:
                    broken_cross_page_anchors.append(
                        {"source": relative_path, "target": reference}
                    )

        page_records.append(
            {
                "path": relative_path,
                "title": parser.title,
                "lang": parser.lang,
                "h1_count": parser.h1_count,
                "ids": sorted(parser.ids),
                "local_link_count": local_link_count,
                "has_viewport": parser.has_viewport,
                "has_main": parser.has_main,
                "has_site_nav": parser.has_site_nav,
                "has_site_footer": parser.has_site_footer,
                "has_skip_link": parser.has_skip_link,
                "has_toc": parser.has_toc,
                "has_mathjax": parser.has_mathjax,
                "description": parser.description,
                "canonical_url": parser.canonical_url,
            }
        )

    return {
        "version": 1,
        "page_count": len(page_records),
        "broken_local_targets": broken_targets,
        "broken_same_page_anchors": broken_anchors,
        "broken_cross_page_anchors": broken_cross_page_anchors,
        "pages": page_records,
    }


def write_report(report: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def compare_with_baseline(
    current: dict[str, object], baseline: dict[str, object]
) -> list[str]:
    issues: list[str] = []

    for broken in current["broken_local_targets"]:
        issues.append(
            f"Missing local target: {broken['source']} -> {broken['target']}"
        )
    for broken in current["broken_same_page_anchors"]:
        issues.append(
            f"Missing same-page anchor: {broken['source']} -> {broken['target']}"
        )
    for broken in current["broken_cross_page_anchors"]:
        issues.append(
            f"Missing cross-page anchor: {broken['source']} -> {broken['target']}"
        )

    current_pages = {page["path"]: page for page in current["pages"]}
    baseline_pages = {page["path"]: page for page in baseline["pages"]}

    for path in sorted(baseline_pages.keys() - current_pages.keys()):
        issues.append(f"Missing baseline page: {path}")
    for path in sorted(current_pages.keys() - baseline_pages.keys()):
        issues.append(f"Unexpected page not in baseline: {path}")

    for path in sorted(current_pages.keys() & baseline_pages.keys()):
        if current_pages[path] != baseline_pages[path]:
            issues.append(f"Page structure drifted from baseline: {path}")

    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit static HTML pages.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan_parser = subparsers.add_parser("scan", help="Write the current site baseline.")
    scan_parser.add_argument("--root", type=Path, default=Path.cwd())
    scan_parser.add_argument("--output", type=Path, required=True)
    check_parser = subparsers.add_parser("check", help="Check the site against a baseline.")
    check_parser.add_argument("--root", type=Path, default=Path.cwd())
    check_parser.add_argument("--baseline", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "scan":
        report = scan_site(args.root)
        write_report(report, args.output)
        print(f"Scanned {report['page_count']} HTML pages -> {args.output}")
        return 0
    if args.command == "check":
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        current = scan_site(args.root)
        issues = compare_with_baseline(current, baseline)
        if issues:
            print(f"Site audit failed with {len(issues)} issue(s):")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print(f"Site audit passed: {current['page_count']} HTML pages match the baseline.")
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
