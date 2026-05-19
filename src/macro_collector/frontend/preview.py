"""摘要列表预览文本处理"""

from __future__ import annotations

import re


def plain_digest_preview(summary: str, max_len: int = 140) -> str:
    """去掉 Markdown 标记，生成首页「最近摘要」可读预览。"""
    if not summary:
        return ""
    text = summary
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`>|]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        return text[:max_len].rstrip() + "…"
    return text
