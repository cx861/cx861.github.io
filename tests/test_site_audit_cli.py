import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_TOOL = REPO_ROOT / "tools" / "site_audit.py"


class SiteAuditCliTests(unittest.TestCase):
    def test_current_site_matches_the_recorded_baseline(self):
        baseline_path = REPO_ROOT / "tests" / "baseline" / "site-baseline.json"
        result = subprocess.run(
            [
                sys.executable,
                str(AUDIT_TOOL),
                "check",
                "--root",
                str(REPO_ROOT),
                "--baseline",
                str(baseline_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("46 HTML pages match the baseline", result.stdout)

    def test_scan_describes_the_site_through_the_cli(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site_root = Path(temp_dir)
            (site_root / "assets" / "css").mkdir(parents=True)
            (site_root / "assets" / "js").mkdir(parents=True)
            (site_root / "assets" / "css" / "style.css").write_text("", encoding="utf-8")
            (site_root / "assets" / "js" / "main.js").write_text("", encoding="utf-8")
            (site_root / "index.html").write_text(
                """<!doctype html>
<html lang="zh-CN">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="测试页面描述">
  <title>测试首页</title>
  <link rel="canonical" href="https://notes.example/">
  <link rel="stylesheet" href="assets/css/style.css">
  <script src="assets/js/main.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到内容</a>
  <nav class="site-nav"></nav>
  <main id="main-content"><h1>测试首页</h1></main>
  <footer class="site-footer"></footer>
</body>
</html>
""",
                encoding="utf-8",
            )
            report_path = site_root / "baseline.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_TOOL),
                    "scan",
                    "--root",
                    str(site_root),
                    "--output",
                    str(report_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["page_count"], 1)
            self.assertEqual(report["broken_local_targets"], [])
            self.assertEqual(report["broken_same_page_anchors"], [])
            self.assertEqual(report["pages"][0]["path"], "index.html")
            self.assertEqual(report["pages"][0]["title"], "测试首页")
            self.assertEqual(report["pages"][0]["h1_count"], 1)
            self.assertTrue(report["pages"][0]["has_main"])
            self.assertEqual(report["pages"][0]["description"], "测试页面描述")
            self.assertEqual(
                report["pages"][0]["canonical_url"], "https://notes.example/"
            )

    def test_check_fails_when_a_local_target_disappears(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site_root = Path(temp_dir)
            (site_root / "index.html").write_text(
                """<!doctype html><html lang="zh-CN"><head>
<meta name="viewport" content="width=device-width"><title>首页</title></head>
<body><main><h1>首页</h1><a href="notes.html">笔记</a></main></body></html>""",
                encoding="utf-8",
            )
            notes_path = site_root / "notes.html"
            notes_path.write_text(
                """<!doctype html><html lang="zh-CN"><head>
<meta name="viewport" content="width=device-width"><title>笔记</title></head>
<body><main><h1>笔记</h1></main></body></html>""",
                encoding="utf-8",
            )
            baseline_path = site_root / "baseline.json"
            scan_result = subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_TOOL),
                    "scan",
                    "--root",
                    str(site_root),
                    "--output",
                    str(baseline_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )
            self.assertEqual(scan_result.returncode, 0, scan_result.stderr)
            notes_path.unlink()

            check_result = subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_TOOL),
                    "check",
                    "--root",
                    str(site_root),
                    "--baseline",
                    str(baseline_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            self.assertEqual(check_result.returncode, 1)
            self.assertIn("missing local target", check_result.stdout.lower())
            self.assertIn("notes.html", check_result.stdout)

    def test_scan_reports_a_missing_anchor_on_another_page(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site_root = Path(temp_dir)
            (site_root / "index.html").write_text(
                """<!doctype html><html><head><title>首页</title></head>
<body><h1>首页</h1><a href="notes.html#missing">笔记章节</a></body></html>""",
                encoding="utf-8",
            )
            (site_root / "notes.html").write_text(
                """<!doctype html><html><head><title>笔记</title></head>
<body><h1>笔记</h1><h2 id="present">已有章节</h2></body></html>""",
                encoding="utf-8",
            )
            report_path = site_root / "baseline.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_TOOL),
                    "scan",
                    "--root",
                    str(site_root),
                    "--output",
                    str(report_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                report["broken_cross_page_anchors"],
                [{"source": "index.html", "target": "notes.html#missing"}],
            )

    def test_scan_ignores_html_source_fragments(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site_root = Path(temp_dir)
            (site_root / "site" / "content").mkdir(parents=True)
            (site_root / "index.html").write_text(
                "<!doctype html><html><head><title>公开页</title></head><body><h1>公开页</h1></body></html>",
                encoding="utf-8",
            )
            (site_root / "site" / "content" / "index.html").write_text(
                "<h1>来源片段</h1>", encoding="utf-8"
            )
            report_path = site_root / "baseline.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_TOOL),
                    "scan",
                    "--root",
                    str(site_root),
                    "--output",
                    str(report_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["page_count"], 1)


if __name__ == "__main__":
    unittest.main()
