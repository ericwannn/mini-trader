"""微信公众号文章采集器（通过搜狗微信搜索）"""

from __future__ import annotations

import re
from datetime import datetime
from html import unescape
from typing import Optional

import requests

from macro_collector.collectors.base import BaseCollector
from macro_collector.models import Article
from macro_collector.utils import make_session, gentle_delay

# 搜索关键词 — 覆盖宏观资产配置主要方向
DEFAULT_KEYWORDS = [
    "大类资产配置 周报",
    "宏观策略 A股 港股",
    "美联储 利率 资产配置",
    "黄金 原油 大宗商品",
    "债券 利率 汇率 人民币",
    "全球宏观 投资策略 2026",
]


class WeChatCollector(BaseCollector):
    """搜狗微信搜索 → 公众号文章采集"""

    @property
    def source_name(self) -> str:
        return "微信公众号"

    def __init__(
        self,
        keywords: list[str] | None = None,
        per_keyword: int = 4,
        max_total: int = 25,
    ) -> None:
        self._keywords_override = keywords
        self._per_keyword = per_keyword
        self._max_total = max_total
        self.session = make_session()
        # warmup
        try:
            self.session.get("https://weixin.sogou.com/", timeout=8)
        except Exception:
            pass

    # ── 搜狗搜索 ────────────────────────────────────────

    def search(self, keyword: str, max_articles: int = 5) -> list[dict]:
        """搜索一个关键词，返回文章元数据列表"""
        encoded = requests.utils.quote(keyword)
        url = f"https://weixin.sogou.com/weixin?type=2&s_from=input&query={encoded}"

        try:
            r = self.session.get(url, timeout=15)
        except Exception as e:
            print(f"  ⚠️ 搜索 '{keyword}' 出错: {e}")
            return []

        if "验证码" in r.text or "checkcode" in r.text.lower():
            print(f"  ⚠️ 触发验证码 (搜索词: {keyword})")
            return []

        raw_articles = re.findall(
            r'<div class="txt-box">.*?<h3[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            r.text, re.DOTALL,
        )

        results = []
        for link, title_html in raw_articles[:max_articles]:
            clean_title = unescape(re.sub(r"<[^>]+>", "", title_html).strip())
            clean_link = link.replace("amp;", "")

            # 公众号名
            acc_match = re.search(
                rf'<div class="txt-box">.*?<a[^>]*href="{re.escape(link)}".*?</div>.*?'
                r'<div class="s-p">(.*?)</div>',
                r.text, re.DOTALL,
            )
            account = ""
            if acc_match:
                account = unescape(re.sub(r"<[^>]+>", "", acc_match.group(1)).strip())
                account = re.sub(r"document\.write\(.*?\)", "", account).strip()
                account = re.sub(r"[)）]\s*$", "", account).strip()

            # 摘要
            abs_match = re.search(
                rf'<div class="txt-box">.*?<a[^>]*href="{re.escape(link)}".*?</div>.*?'
                r'<p class="str_info[^"]*">(.*?)</p>',
                r.text, re.DOTALL,
            )
            abstract = ""
            if abs_match:
                abstract = unescape(re.sub(r"<[^>]+>", "", abs_match.group(1)).strip())

            results.append({
                "title": clean_title,
                "account": account,
                "abstract": abstract,
                "sogou_link": f"https://weixin.sogou.com{clean_link}",
            })

        return results

    # ── 正文提取 ────────────────────────────────────────

    @staticmethod
    def _extract_wechat_url(html: str) -> Optional[str]:
        """从搜狗重定向页 JS 片段拼接出微信文章真实 URL"""
        fragments = re.findall(r"url\s*\+=\s*'([^']+)'", html)
        if fragments:
            return "".join(fragments)
        return None

    def _fetch_article(self, wechat_url: str) -> Optional[dict]:
        """访问微信文章页面，提取标题/公众号/正文/时间"""
        headers = {
            "User-Agent": self.session.headers["User-Agent"],
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://weixin.sogou.com/",
        }
        try:
            r = self.session.get(wechat_url, headers=headers, timeout=15)
        except Exception as e:
            print(f"   请求失败: {e}")
            return None
        if r.status_code != 200:
            print(f"   HTTP {r.status_code}")
            return None

        html = r.text

        # 标题
        title = ""
        m = re.search(
            r'<h1[^>]*class="rich_media_title[^"]*"[^>]*>(.*?)</h1>',
            html, re.DOTALL,
        )
        if m:
            title = unescape(re.sub(r"<[^>]+>", "", m.group(1)).strip())

        # 公众号名称
        account = ""
        m = re.search(
            r'<strong[^>]*class="rich_media_meta[^"]*rich_media_meta_nickname[^"]*"[^>]*>'
            r"(.*?)</strong>",
            html, re.DOTALL,
        )
        if m:
            account = unescape(re.sub(r"<[^>]+>", "", m.group(1)).strip())
            account = re.sub(r"[)）]\s*$", "", account).strip()

        # 发布时间
        pub_time = ""
        m = re.search(r'em[^>]*id="publish_time"[^>]*>(.*?)</em', html, re.DOTALL)
        if not m:
            m = re.search(r'"create_time"[^:]*:\s*"(\d+)"', html)
            if m:
                ts = int(m.group(1))
                pub_time = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        else:
            pub_time = m.group(1).strip()

        # 正文
        content = ""
        m = re.search(
            r'<div[^>]*class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<(?:script|div)',
            html, re.DOTALL,
        )
        if not m:
            m = re.search(
                r'id="js_content"[^>]*>(.*?)</div>\s*<(?:script|div)',
                html, re.DOTALL,
            )
        if m:
            text = unescape(re.sub(r"<[^>]+>", "", m.group(1)))
            content = re.sub(r"\s+", " ", text).strip()[:5000]

        if not content:
            m = re.search(
                r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
                html,
            )
            if m:
                content = unescape(m.group(1))[:1000]

        return {
            "title": title or "未知标题",
            "account": account,
            "publish_time": pub_time,
            "content": content[:5000],
        }

    def _fetch_via_sogou(self, sogou_link: str) -> Optional[Article]:
        """通过搜狗链接 → 重定向 → 微信原文"""
        try:
            r = self.session.get(sogou_link, timeout=15, allow_redirects=True)
            wechat_url = self._extract_wechat_url(r.text)
            if not wechat_url:
                return None
            data = self._fetch_article(wechat_url)
            if not data:
                return None
            return Article(
                title=data["title"],
                account=data["account"],
                keyword_found="",        # filled by caller
                url=wechat_url,
                content=data["content"],
                publish_time=data["publish_time"],
                source="sogou_wechat",
            )
        except Exception as e:
            print(f"   解析失败: {e}")
            return None

    # ── 批量采集 ────────────────────────────────────────

    def fetch(self, max_items: int | None = None) -> list[Article]:
        """实现 BaseCollector：执行采集（关键词与上限由构造参数决定）"""
        cap = max_items if max_items is not None else self._max_total
        return self.collect(
            keywords=self._keywords_override,
            per_keyword=self._per_keyword,
            max_total=cap,
        )

    def collect(
        self,
        keywords: list[str] | None = None,
        per_keyword: int = 4,
        max_total: int = 25,
    ) -> list[Article]:
        """完整采集流程：搜索 → 去重 → 获取正文"""
        kw_list = (
            keywords
            if keywords is not None
            else (self._keywords_override if self._keywords_override is not None else DEFAULT_KEYWORDS)
        )
        articles: list[Article] = []
        seen_titles: set[str] = set()

        for kw in kw_list:
            gentle_delay(1.0, 2.5)
            print(f"\n🔍 搜索: {kw}")
            results = self.search(kw, max_articles=per_keyword)
            if not results:
                continue

            for sr in results:
                dedup_key = sr["title"][:30]
                if dedup_key in seen_titles:
                    continue
                seen_titles.add(dedup_key)

                print(f"  📥 {sr['title'][:55]}...")
                article = self._fetch_via_sogou(sr["sogou_link"])
                if article:
                    article.keyword_found = kw
                    articles.append(article)
                else:
                    articles.append(
                        Article(
                            title=sr["title"],
                            account=sr["account"],
                            keyword_found=kw,
                            url=sr["sogou_link"],
                            content=sr["abstract"],
                            source="sogou_wechat_fallback",
                        )
                    )

                if len(articles) >= max_total:
                    break

            if len(articles) >= max_total:
                break

        return articles


def collect(
    keywords: list[str] | None = None,
    per_keyword: int = 4,
    max_total: int = 25,
) -> list[Article]:
    """便捷入口函数"""
    return WeChatCollector().collect(keywords, per_keyword, max_total)
