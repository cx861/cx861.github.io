import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTER_TOOL = REPO_ROOT / "tools" / "content_converter.py"


class ContentConverterCliTests(unittest.TestCase):
    def run_converter(self, source: Path, output: Path):
        return subprocess.run(
            [
                sys.executable,
                str(CONVERTER_TOOL),
                "convert",
                "--input",
                str(source),
                "--output",
                str(output),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

    def test_convert_writes_headings_paragraphs_and_math(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "probability.md"
            output = temp / "probability.html"
            source.write_text(
                """# 概率论

## 随机事件

设 $P(A)=1$，则 **A 是必然事件**。

## 随机事件

原始标签 <script>alert(1)</script> 必须转义。
""",
                encoding="utf-8",
            )

            result = self.run_converter(source, output)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn('<h1 id="概率论">概率论</h1>', rendered)
            self.assertIn('<h2 id="随机事件">随机事件</h2>', rendered)
            self.assertIn('<h2 id="随机事件-2">随机事件</h2>', rendered)
            self.assertIn('$P(A)=1$', rendered)
            self.assertIn("<strong>A 是必然事件</strong>", rendered)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", rendered)

    def test_convert_handles_tables_with_pipes_and_fenced_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "table-and-code.md"
            output = temp / "table-and-code.html"
            source.write_text(
                """## 条件概率

| 公式 | 说明 |
| --- | :---: |
| `$P(A|B)$` | **条件概率** |

```python
if a < b:
    print("A&B")
```
""",
                encoding="utf-8",
            )

            result = self.run_converter(source, output)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn('<div class="table-wrapper">', rendered)
            self.assertIn("<th>公式</th>", rendered)
            self.assertIn("<th>说明</th>", rendered)
            self.assertIn("<code>$P(A|B)$</code>", rendered)
            self.assertIn("<td><strong>条件概率</strong></td>", rendered)
            self.assertIn('<pre><code class="language-python">', rendered)
            self.assertIn("if a &lt; b:", rendered)
            self.assertIn('print(&quot;A&amp;B&quot;)', rendered)

    def test_convert_handles_study_note_blocks_and_lists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "blocks.md"
            output = temp / "blocks.html"
            source.write_text(
                r"""$$
\int_0^1 x^2\,dx
$$

> 注意：先判断 **收敛性**。

- 写出定义域
- 检查端点

1. 求导
2. 判断符号

---
""",
                encoding="utf-8",
            )

            result = self.run_converter(source, output)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn('<div class="math-block">$$\n\\int_0^1 x^2\\,dx\n$$</div>', rendered)
            self.assertIn("<blockquote>注意：先判断 <strong>收敛性</strong>。</blockquote>", rendered)
            self.assertIn("<ul>\n<li>写出定义域</li>\n<li>检查端点</li>\n</ul>", rendered)
            self.assertIn("<ol>\n<li>求导</li>\n<li>判断符号</li>\n</ol>", rendered)
            self.assertIn("<hr>", rendered)

    def test_convert_rejects_missing_input_without_creating_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "missing.md"
            output = temp / "generated" / "missing.html"

            result = self.run_converter(source, output)

            self.assertEqual(result.returncode, 2)
            self.assertIn("Input Markdown file not found", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
