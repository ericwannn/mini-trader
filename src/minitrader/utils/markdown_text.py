"""Markdown 文本清理——避免换行/方括号破坏链接与标题渲染。"""

from __future__ import annotations

import re

# ### [可能跨行的标题文本](url)
_HEADER_LINK_RE = re.compile(
    r"^(###\s*)\[(.*?)\]\(([^)\s]+)\)\s*$",
    re.MULTILINE | re.DOTALL,
)


def collapse_whitespace(text: str) -> str:
    """将任意空白（含换行）折叠为单个空格。"""
    return re.sub(r"\s+", " ", (text or "").replace("\r\n", "\n").replace("\r", "\n")).strip()


def sanitize_title_text(text: str, max_len: int = 120) -> str:
    """用于文章标题、列表展示（纯文本）。"""
    t = collapse_whitespace(text)
    if len(t) > max_len:
        return t[:max_len].rstrip() + "…"
    return t


def sanitize_markdown_link_text(text: str, max_len: int = 120) -> str:
    """用于 Markdown 链接文字 `[...](url)`，转义方括号并去掉换行。"""
    t = sanitize_title_text(text, max_len=max_len)
    return t.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def make_markdown_header_link(title: str, url: str, *, max_len: int = 120) -> str:
    """生成可放在 `###` 后的单行链接标题。"""
    url = (url or "").strip()
    if not url or url == "#":
        return sanitize_title_text(title, max_len=max_len)
    label = sanitize_markdown_link_text(title, max_len=max_len)
    return f"[{label}]({url})"


def normalize_digest_markdown(text: str) -> str:
    """修复摘要中因标题含换行而损坏的 `### [标题](url)` 行（历史数据兼容）。"""
    if not text:
        return ""

    def _repl(match: re.Match[str]) -> str:
        prefix, link_text, url = match.group(1), match.group(2), match.group(3)
        label = sanitize_markdown_link_text(link_text)
        return f"{prefix}[{label}]({url})"

    return _HEADER_LINK_RE.sub(_repl, text)
