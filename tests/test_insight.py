import unittest

from minitrader.models import Article
from minitrader.models.digest import (
    build_article_insight,
    generate_digest_markdown,
    _extract_actor,
)


class InsightTestCase(unittest.TestCase):
    def test_actor_from_title_prefix(self) -> None:
        a = Article(
            title="美国银行调查：若美债大幅波动 30年期收益率或升至6%以上",
            account="华尔街见闻",
            keyword_found="",
            url="https://example.com/1",
            content="美国银行认为美债收益率可能升至6%。",
            source="wallstreetcn",
        )
        self.assertEqual(_extract_actor(a), "美国银行调查")

    def test_build_article_insight_line(self) -> None:
        a = Article(
            title="黄金走强",
            account="国投瑞银基金",
            keyword_found="黄金",
            url="https://example.com/gold",
            content="黄金看多，短期上行，建议超配黄金ETF。",
            source="test",
        )
        ins = build_article_insight(a)
        self.assertEqual(ins["actor"], "国投瑞银基金")
        self.assertIn("黄金", ins["instruments"])
        self.assertEqual(ins["direction"], "看多")
        self.assertIn("短期", ins["horizon"])
        self.assertIn("国投瑞银基金", ins["viewpoint"])
        self.assertIn("看多", ins["viewpoint"])

    def test_digest_contains_core_viewpoint(self) -> None:
        a = Article(
            title="原油承压",
            account="测试研究",
            keyword_found="原油",
            url="https://example.com/oil",
            content="原油看空，油价回落，中期承压。",
            source="test",
        )
        md = generate_digest_markdown([a], "2026-05-19")
        self.assertIn("**核心观点**", md)
        self.assertIn("**主体**", md)
        self.assertIn("本节观点速览", md)


if __name__ == "__main__":
    unittest.main()
