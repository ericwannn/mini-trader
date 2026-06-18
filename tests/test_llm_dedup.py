import unittest

from minitrader.digest.llm import _dedup_similar_articles
from minitrader.models import Article


class LlmDedupTestCase(unittest.TestCase):
    def _short(self, title: str, content: str = "") -> Article:
        return Article(
            title=title,
            account="金十",
            keyword_found="",
            url=f"https://flash.jin10.com/#t={title[:8]}",
            content=content or title,
            source="jin10",
        )

    def test_short_articles_merge_at_lower_threshold(self) -> None:
        """两条短快讯标题高度相似时应合并（阈值 0.25，非 0.30）。"""
        a1 = self._short("现货黄金短线走高，日内涨0.3%")
        a2 = self._short("现货黄金短线走高，日内涨0.35%")
        out = _dedup_similar_articles([a1, a2])
        self.assertEqual(len(out), 1)

    def test_different_short_articles_kept(self) -> None:
        a1 = self._short("原油大跌，国际油价回落")
        a2 = self._short("黄金走强，避险需求上升")
        out = _dedup_similar_articles([a1, a2])
        self.assertEqual(len(out), 2)


if __name__ == "__main__":
    unittest.main()
