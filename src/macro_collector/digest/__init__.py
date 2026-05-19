"""digest 子包——辅助工具与 LLM 输入格式化。

当前主摘要管线位于 :mod:`macro_collector.models.digest`，本子包仅暴露
原始数据加载/LLM 提示词构造，以及基于 DB 的去重工具。
"""

from macro_collector.digest.dedup import dedup_articles
from macro_collector.digest.generator import format_for_llm, load_raw_data, save_digest

__all__ = ["dedup_articles", "format_for_llm", "load_raw_data", "save_digest"]
