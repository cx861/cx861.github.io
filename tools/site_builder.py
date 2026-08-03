#!/usr/bin/env python3
"""Build the static site from one shared shell and page-specific fragments."""

from __future__ import annotations

import argparse
import html
import json
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from string import Template


NAV_ITEMS = (
    ("index", "index.html", "首页"),
    ("knowledge-base", "knowledge-base.html", "知识库"),
    ("notes", "notes.html", "个人笔记"),
    ("mistakes", "mistakes.html", "错题本"),
    ("exam-types", "exam-types.html", "常考题型及解法"),
)

DEFAULT_SITE_NAME = "考研笔记"
DEFAULT_SITE_URL = "https://example.invalid"
DEFAULT_DESCRIPTION = "个人使用的考研知识库，系统整理数学、408 计算机、英语和政治复习笔记。"


def validate_route(route: str) -> PurePosixPath:
    path = PurePosixPath(route)
    if path.is_absolute() or ".." in path.parts or path.suffix.lower() != ".html":
        raise ValueError(f"Invalid page path: {route}")
    return path


def asset_prefix(route: PurePosixPath) -> str:
    return "../" * len(route.parent.parts)


def canonical_url(site_url: str, route: PurePosixPath) -> str:
    public_path = "" if route.as_posix() == "index.html" else route.as_posix()
    return f"{site_url.rstrip('/')}/{public_path}"


def page_description(page: dict[str, object], default_description: str) -> str:
    explicit = str(page.get("description", "")).strip()
    if explicit:
        return explicit
    if page["path"] == "index.html":
        return default_description
    subject = str(page["title"]).removesuffix(" - 考研笔记")
    return f"{subject}的个人复习笔记与知识整理，服务于考研备考、回顾和查漏补缺。"


def write_discovery_files(
    output: Path,
    routes: list[PurePosixPath],
    site_url: str,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    output.joinpath(".nojekyll").write_text("", encoding="utf-8")
    output.joinpath("robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {site_url.rstrip('/')}/sitemap.xml\n",
        encoding="utf-8",
        newline="\n",
    )
    locations = "\n".join(
        f"  <url><loc>{html.escape(canonical_url(site_url, route))}</loc></url>"
        for route in routes
    )
    output.joinpath("sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{locations}\n"
        "</urlset>\n",
        encoding="utf-8",
        newline="\n",
    )


def render_navigation(prefix: str, active_nav: str) -> str:
    desktop_links = []
    mobile_links = []
    for key, target, label in NAV_ITEMS:
        current = ' class="active" aria-current="page"' if key == active_nav else ""
        desktop_links.append(f'        <a href="{prefix}{target}"{current}>{label}</a>')
        mobile_links.append(f'    <a href="{prefix}{target}"{current}>{label}</a>')

    return "\n".join(
        [
            '<nav class="site-nav" aria-label="主导航">',
            '    <div class="site-nav-inner">',
            f'        <a class="nav-logo" href="{prefix}index.html">考研笔记</a>',
            *desktop_links,
            '        <div class="nav-controls">',
            '            <button class="theme-toggle" type="button" aria-label="切换深色/浅色模式"><span class="theme-toggle-icon">🌙</span></button>',
            '            <button class="hamburger" type="button" aria-label="打开导航菜单" aria-expanded="false" aria-controls="mobile-menu">',
            '                <span></span><span></span><span></span>',
            "            </button>",
            "        </div>",
            "    </div>",
            "</nav>",
            "",
            "<!-- 移动端菜单 -->",
            '<div class="mobile-nav-overlay" aria-hidden="true"></div>',
            '<div class="mobile-menu" id="mobile-menu" role="dialog" aria-modal="true" aria-label="导航菜单" aria-hidden="true" inert>',
            *mobile_links,
            '    <button class="menu-theme-toggle" type="button"><span class="menu-theme-icon">🌙</span> 切换深色/浅色模式</button>',
            "</div>",
        ]
    )


def read_optional_fragment(site_dir: Path, folder: str, route: PurePosixPath) -> str:
    fragment_path = site_dir / folder / Path(*route.parts)
    if not fragment_path.exists():
        return ""
    return fragment_path.read_text(encoding="utf-8").strip()


def build_site(root: Path, output: Path) -> list[Path]:
    root = root.resolve()
    output = output.resolve()
    site_dir = root / "site"
    manifest = json.loads((site_dir / "pages.json").read_text(encoding="utf-8"))
    if manifest.get("version") != 1:
        raise ValueError("Unsupported site manifest version")

    site = manifest.get("site", {})
    site_name = str(site.get("name", DEFAULT_SITE_NAME)).strip() or DEFAULT_SITE_NAME
    site_url = str(site.get("url", DEFAULT_SITE_URL)).strip() or DEFAULT_SITE_URL
    default_description = (
        str(site.get("description", DEFAULT_DESCRIPTION)).strip()
        or DEFAULT_DESCRIPTION
    )
    routes = [validate_route(page["path"]) for page in manifest["pages"]]

    template = Template((site_dir / "templates" / "base.html").read_text(encoding="utf-8"))
    written: list[Path] = []

    if output != root:
        assets = root / "assets"
        if assets.exists():
            shutil.copytree(assets, output / "assets", dirs_exist_ok=True)
    write_discovery_files(output, routes, site_url)

    for page in manifest["pages"]:
        route = validate_route(page["path"])
        prefix = asset_prefix(route)
        content_path = site_dir / "content" / Path(*route.parts)
        page_content = content_path.read_text(encoding="utf-8").strip()
        description = page_description(page, default_description)
        page_url = canonical_url(site_url, route)
        extra_head = read_optional_fragment(site_dir, "head", route)
        resource_hints = ""
        if "cdn.jsdelivr.net" in extra_head:
            resource_hints = (
                '    <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>\n'
                '    <link rel="dns-prefetch" href="//cdn.jsdelivr.net">'
            )
        rendered = template.substitute(
            title=html.escape(page["title"]),
            description=html.escape(description, quote=True),
            canonical_url=html.escape(page_url, quote=True),
            site_name=html.escape(site_name, quote=True),
            asset_prefix=prefix,
            navigation=render_navigation(prefix, page["active_nav"]),
            page_content=page_content,
            resource_hints=resource_hints,
            extra_head=extra_head,
            extra_body_end=read_optional_fragment(site_dir, "tail", route),
            footer_attributes=' style="display:none"' if page.get("footer_hidden") else "",
        )
        destination = output / Path(*route.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8", newline="\n")
        written.append(destination)

    return written


def check_site(root: Path) -> list[str]:
    root = root.resolve()
    issues: list[str] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        generated_root = Path(temp_dir)
        generated_pages = build_site(root, generated_root)
        for generated in generated_pages:
            route = generated.relative_to(generated_root)
            public_page = root / route
            if not public_page.exists():
                issues.append(f"Missing generated page: {route.as_posix()}")
            elif public_page.read_bytes() != generated.read_bytes():
                issues.append(f"Generated page drift: {route.as_posix()}")
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the kaoyan static site.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="Render pages into an output directory.")
    build.add_argument("--root", type=Path, default=Path.cwd())
    build.add_argument("--output", type=Path, required=True)
    check = subparsers.add_parser("check", help="Verify public pages match their sources.")
    check.add_argument("--root", type=Path, default=Path.cwd())
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "build":
        written = build_site(args.root, args.output)
        print(f"Built {len(written)} HTML pages -> {args.output}")
        return 0
    if args.command == "check":
        issues = check_site(args.root)
        if issues:
            print(f"Site build check failed with {len(issues)} issue(s):")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print("Site build check passed: public pages match their sources.")
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
