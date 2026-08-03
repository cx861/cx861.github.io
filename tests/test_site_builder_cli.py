import json
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_TOOL = REPO_ROOT / "tools" / "site_builder.py"


class SiteBuilderCliTests(unittest.TestCase):
    def test_current_public_pages_match_site_sources(self):
        result = subprocess.run(
            [
                sys.executable,
                str(BUILDER_TOOL),
                "check",
                "--root",
                str(REPO_ROOT),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("public pages match their sources", result.stdout)

    def test_build_renders_a_page_from_manifest_template_and_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            site_dir = project_root / "site"
            (site_dir / "templates").mkdir(parents=True)
            (site_dir / "content").mkdir(parents=True)
            (site_dir / "templates" / "base.html").write_text(
                """<!doctype html><html lang="zh-CN"><head>
<title>$title</title><meta name="description" content="$description">
<link rel="canonical" href="$canonical_url">
<link rel="stylesheet" href="${asset_prefix}assets/css/style.css">
$extra_head</head><body>$navigation$page_content
<div class="site-footer"$footer_attributes>footer</div>
$extra_body_end</body></html>
""",
                encoding="utf-8",
            )
            (site_dir / "content" / "index.html").write_text(
                '<main id="main-content"><h1>测试正文</h1></main>',
                encoding="utf-8",
            )
            (site_dir / "pages.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "site": {
                            "name": "测试站点",
                            "url": "https://notes.example",
                            "description": "测试站点默认描述",
                        },
                        "pages": [
                            {
                                "path": "index.html",
                                "title": "测试站点",
                                "active_nav": "index",
                                "footer_hidden": False,
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            output_dir = project_root / "dist"

            result = subprocess.run(
                [
                    sys.executable,
                    str(BUILDER_TOOL),
                    "build",
                    "--root",
                    str(project_root),
                    "--output",
                    str(output_dir),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            rendered = (output_dir / "index.html").read_text(encoding="utf-8")
            self.assertIn("<title>测试站点</title>", rendered)
            self.assertIn(
                '<meta name="description" content="测试站点默认描述">', rendered
            )
            self.assertIn(
                '<link rel="canonical" href="https://notes.example/">', rendered
            )
            self.assertIn('href="assets/css/style.css"', rendered)
            self.assertIn(
                '<a href="index.html" class="active" aria-current="page">首页</a>',
                rendered,
            )
            self.assertIn('<a class="nav-logo" href="index.html">考研笔记</a>', rendered)
            self.assertIn(
                '<div class="mobile-menu" id="mobile-menu" role="dialog" '
                'aria-modal="true" aria-label="导航菜单" aria-hidden="true" inert>',
                rendered,
            )
            self.assertIn("<h1>测试正文</h1>", rendered)

    def test_build_preserves_nested_urls_and_copies_static_assets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            site_dir = project_root / "site"
            (site_dir / "templates").mkdir(parents=True)
            (site_dir / "content" / "math").mkdir(parents=True)
            (project_root / "assets" / "css").mkdir(parents=True)
            (project_root / "assets" / "js").mkdir(parents=True)
            (project_root / "assets" / "css" / "style.css").write_text(
                "body{}", encoding="utf-8"
            )
            (project_root / "assets" / "js" / "main.js").write_text(
                "void 0;", encoding="utf-8"
            )
            (project_root / ".nojekyll").write_text("", encoding="utf-8")
            (site_dir / "templates" / "base.html").write_text(
                """<!doctype html><html><head><title>$title</title>
<link rel="stylesheet" href="${asset_prefix}assets/css/style.css">$extra_head
</head><body>$navigation$page_content
<div class="site-footer"$footer_attributes></div>$extra_body_end</body></html>
""",
                encoding="utf-8",
            )
            (site_dir / "content" / "math" / "probability.html").write_text(
                "<h1>概率论</h1>", encoding="utf-8"
            )
            (site_dir / "pages.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "site": {
                            "name": "测试站点",
                            "url": "https://notes.example",
                            "description": "测试站点默认描述",
                        },
                        "pages": [
                            {
                                "path": "math/probability.html",
                                "title": "概率论",
                                "active_nav": "knowledge-base",
                                "footer_hidden": False,
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            output_dir = project_root / "dist"

            result = subprocess.run(
                [
                    sys.executable,
                    str(BUILDER_TOOL),
                    "build",
                    "--root",
                    str(project_root),
                    "--output",
                    str(output_dir),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            rendered = (output_dir / "math" / "probability.html").read_text(
                encoding="utf-8"
            )
            self.assertIn('href="../assets/css/style.css"', rendered)
            self.assertIn(
                'href="../knowledge-base.html" class="active" aria-current="page"',
                rendered,
            )
            self.assertIn(
                '<a class="nav-logo" href="../index.html">考研笔记</a>', rendered
            )
            self.assertEqual(
                (output_dir / "assets" / "css" / "style.css").read_text(
                    encoding="utf-8"
                ),
                "body{}",
            )
            self.assertTrue((output_dir / ".nojekyll").exists())
            self.assertIn(
                "Sitemap: https://notes.example/sitemap.xml",
                (output_dir / "robots.txt").read_text(encoding="utf-8"),
            )
            sitemap = (output_dir / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn(
                "<loc>https://notes.example/math/probability.html</loc>", sitemap
            )

    def test_check_reports_when_a_public_page_drifted_from_its_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            site_dir = project_root / "site"
            (site_dir / "templates").mkdir(parents=True)
            (site_dir / "content").mkdir(parents=True)
            (site_dir / "templates" / "base.html").write_text(
                """<!doctype html><html><head><title>$title</title>$extra_head</head>
<body>$navigation$page_content<div$footer_attributes></div>$extra_body_end</body></html>
""",
                encoding="utf-8",
            )
            (site_dir / "content" / "index.html").write_text(
                "<h1>来源正文</h1>", encoding="utf-8"
            )
            (site_dir / "pages.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "pages": [
                            {
                                "path": "index.html",
                                "title": "测试站点",
                                "active_nav": "index",
                                "footer_hidden": False,
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (project_root / "index.html").write_text(
                "<h1>被手工修改的输出</h1>", encoding="utf-8"
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(BUILDER_TOOL),
                    "check",
                    "--root",
                    str(project_root),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("Generated page drift", result.stdout)
            self.assertIn("index.html", result.stdout)

    def test_shared_template_exposes_main_landmark_and_labeled_controls(self):
        template = (REPO_ROOT / "site" / "templates" / "base.html").read_text(
            encoding="utf-8"
        )

        self.assertIn("<main>", template)
        self.assertIn("</main>", template)
        self.assertIn("assets/css/study-archive.css", template)
        self.assertIn('meta name="description"', template)
        self.assertIn('link rel="canonical"', template)
        self.assertIn('property="og:title"', template)
        self.assertIn("${resource_hints}", template)
        self.assertIn('aria-label="返回页面顶部"', template)
        self.assertIn('aria-hidden="true"', template)

    def test_current_discovery_files_cover_the_public_manifest(self):
        manifest = json.loads(
            (REPO_ROOT / "site" / "pages.json").read_text(encoding="utf-8")
        )
        site_url = manifest["site"]["url"].rstrip("/")
        expected_urls = {
            f"{site_url}/" if page["path"] == "index.html"
            else f"{site_url}/{page['path']}"
            for page in manifest["pages"]
        }
        sitemap = ET.parse(REPO_ROOT / "sitemap.xml")
        namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        actual_urls = {
            element.text
            for element in sitemap.findall("sitemap:url/sitemap:loc", namespace)
        }

        self.assertEqual(actual_urls, expected_urls)
        robots = (REPO_ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn(f"Sitemap: {site_url}/sitemap.xml", robots)


if __name__ == "__main__":
    unittest.main()
