"""topics 提取与 Markdown 解析单元测试（无需 LLM / 网络）。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from minitrader.db import get_topics_by_date, init_db, store_topics
from minitrader.db.models import DB_PATH
from minitrader.frontend.markdown_render import render_markdown_html
from minitrader.models import Article
from minitrader.models.digest import (
    _direction_judgement,
    extract_topics_from_articles,
    generate_digest_markdown,
    parse_topics_from_markdown,
)


class TopicsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_db = DB_PATH
        import minitrader.db.models as db_models

        db_models.DB_PATH = str(Path(self._tmpdir.name) / "test.db")
        init_db()

    def tearDown(self) -> None:
        import minitrader.db.models as db_models

        db_models.DB_PATH = self._orig_db
        self._tmpdir.cleanup()

    def _sample_articles(self) -> list[Article]:
        return [
            Article(
                title="黄金走强",
                account="测试号",
                keyword_found="黄金",
                url="https://example.com/gold",
                content="黄金看多，短期上行，配置价值提升。",
                source="test",
            ),
            Article(
                title="原油承压",
                account="测试号",
                keyword_found="原油",
                url="https://example.com/oil",
                content="原油看空，油价回落，风险加大。",
                source="test",
            ),
        ]

    def test_direction_judgement_keywords(self) -> None:
        bullish = Article(
            title="黄金上调目标价",
            account="测试",
            keyword_found="黄金",
            url="https://example.com/1",
            content="机构上调金价预测，维持看多，短期上行。",
            source="test",
        )
        bearish = Article(
            title="原油大跌",
            account="测试",
            keyword_found="原油",
            url="https://example.com/2",
            content="国际油价大跌，利空压制，油价回落。",
            source="test",
        )
        ticker = Article(
            title="股指",
            account="测试",
            keyword_found="",
            url="https://example.com/3",
            content="印尼基准股指日内跌幅达1%。",
            source="test",
        )
        self.assertEqual(_direction_judgement(bullish), "看多")
        self.assertEqual(_direction_judgement(bearish), "看空")
        self.assertEqual(_direction_judgement(ticker), "看空")

    def test_extract_topics_from_articles(self) -> None:
        arts = self._sample_articles()
        rows = extract_topics_from_articles(arts, "2026-05-19")
        self.assertGreaterEqual(len(rows), 2)
        keywords = {r["keyword"] for r in rows}
        self.assertTrue(any("黄金" in k for k in keywords))

    def test_parse_topics_from_markdown_roundtrip(self) -> None:
        arts = self._sample_articles()
        md = generate_digest_markdown(arts, "2026-05-20")
        self.assertNotIn("[原文链接]", md)
        parsed = parse_topics_from_markdown(md, "2026-05-20")
        self.assertGreater(len(parsed), 0)
        self.assertIn("direction", parsed[0])
        rel = __import__("json").loads(parsed[0]["related_articles"])
        self.assertEqual(rel[0]["url"], "https://example.com/gold")

    def test_store_and_get_topics(self) -> None:
        arts = self._sample_articles()
        rows = extract_topics_from_articles(arts, "2026-05-21")
        n = store_topics("2026-05-21", rows)
        self.assertEqual(n, len(rows))
        loaded = get_topics_by_date("2026-05-21")
        self.assertEqual(len(loaded), n)
        self.assertIsInstance(loaded[0]["related_articles_list"], list)

    def test_render_markdown_html_escapes_script(self) -> None:
        html = render_markdown_html("# 标题\n\n<script>alert(1)</script>\n\n[链接](https://x.com)")
        self.assertIn("<h1>", html)
        self.assertNotIn("<script>", html.lower())
        self.assertIn("https://x.com", html)


if __name__ == "__main__":
    unittest.main()
