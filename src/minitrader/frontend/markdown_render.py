"""将 Markdown 摘要安全渲染为 HTML（服务端）。"""

from __future__ import annotations

import bleach
import markdown

from minitrader.utils.markdown_text import normalize_digest_markdown


_ALLOWED_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "br", "hr",
    "ul", "ol", "li",
    "strong", "em", "code", "pre",
    "blockquote",
    "a",
    "table", "thead", "tbody", "tr", "th", "td",
]
_ALLOWED_ATTRS = {"a": ["href", "title", "rel"]}


def render_markdown_html(text: str) -> str:
    """Markdown → HTML，并用 bleach 白名单过滤。"""
    if not text:
        return ""
    text = normalize_digest_markdown(text)
    raw_html = markdown.markdown(
        text,
        extensions=["extra", "nl2br", "sane_lists"],
        output_format="html5",
    )
    cleaned = bleach.clean(
        raw_html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
    # 外链在新标签打开，避免用户误以为「没跳转」
    return cleaned.replace("<a href=", '<a target="_blank" rel="noopener noreferrer" href=')
