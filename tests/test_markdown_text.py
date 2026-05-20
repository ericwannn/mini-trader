import unittest

from minitrader.frontend.markdown_render import render_markdown_html
from minitrader.models.digest import generate_digest_markdown
from minitrader.models import Article
from minitrader.utils.markdown_text import (
    make_markdown_header_link,
    normalize_digest_markdown,
    sanitize_title_text,
)


class MarkdownTextTestCase(unittest.TestCase):
    def test_sanitize_title_collapses_newlines(self) -> None:
        raw = "上证指数早盘收报4132.46点，涨0.02%。\n深证成指早盘收报15408.72点，跌0.78%。\n\n创业板指早盘收"
        t = sanitize_title_text(raw, max_len=80)
        self.assertNotIn("\n", t)
        self.assertIn("上证指数", t)

    def test_header_link_single_line(self) -> None:
        raw = "line1\nline2"
        md = f"### {make_markdown_header_link(raw, 'https://example.com/x')}\n"
        self.assertEqual(md.count("\n"), 1)

    def test_normalize_digest_multiline_header(self) -> None:
        broken = """## 3. A股/港股

### [上证指数早盘收报4132.46点，涨0.02%。
深证成指早盘收报15408.72点，跌0.78%。

创业板指早盘收](https://wallstreetcn.com/livenews/3105767)
- **来源**: 华尔街见闻
"""
        fixed = normalize_digest_markdown(broken)
        self.assertNotIn("\n深证成指", fixed.split("### [")[1].split("](")[0])
        html = render_markdown_html(fixed)
        self.assertIn('href="https://wallstreetcn.com/livenews/3105767"', html)
        self.assertNotIn("[上证指数", html)

    def test_generate_digest_no_multiline_header(self) -> None:
        a = Article(
            title="上证涨0.02%\n深证跌0.78%",
            account="华尔街见闻",
            keyword_found="",
            url="https://wallstreetcn.com/livenews/1",
            content="盘面分化。",
            source="wallstreetcn",
        )
        md = generate_digest_markdown([a], "2026-05-19")
        header_lines = [ln for ln in md.splitlines() if ln.startswith("### [")]
        self.assertEqual(len(header_lines), 1)
        self.assertNotIn("\n", header_lines[0])


if __name__ == "__main__":
    unittest.main()
