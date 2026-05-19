"""数据库操作模块——SQLite 存储所有采集数据、摘要、涨停记录"""

import json
import os
import sqlite3
from datetime import date, datetime
from typing import Optional

DB_DIR = os.path.dirname(os.path.abspath(__file__))  # src/macro_collector/db/
PROJECT_DIR = os.path.abspath(os.path.join(DB_DIR, "..", "..", ".."))  # project root
DB_PATH = os.path.join(PROJECT_DIR, "macro.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化数据库表结构"""
    if not os.path.exists(SCHEMA_PATH):
        return
    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()


# ── 文章去重 ──────────────────────────────────────────

def article_exists(url: str) -> bool:
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM articles WHERE url = ?", (url,)).fetchone()
    conn.close()
    return row is not None


def article_exists_by_title(title: str, source: str) -> bool:
    """标题模糊去重——同一来源同一标题视为重复"""
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM articles WHERE source = ? AND title = ?",
        (source, title),
    ).fetchone()
    conn.close()
    return row is not None


def store_article(url: str, title: str, source: str, content: str = "",
                  published_at: str = "") -> bool:
    """存储一篇文章，返回是否真的插入了（False 表示重复）"""
    if article_exists(url):
        return False
    if article_exists_by_title(title, source):
        return False
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO articles (url, title, source, content, published_at) VALUES (?, ?, ?, ?, ?)",
            (url, title, source, content, published_at),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_recent_articles(limit: int = 100, source: Optional[str] = None):
    """获取最近文章"""
    conn = get_connection()
    if source:
        rows = conn.execute(
            "SELECT * FROM articles WHERE source = ? ORDER BY collected_at DESC LIMIT ?",
            (source, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM articles ORDER BY collected_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_articles_by_date(target_date: str):
    """获取某天的所有文章"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM articles WHERE date(collected_at) = ? ORDER BY source, collected_at",
        (target_date,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_article_by_id(article_id: int) -> Optional[dict]:
    """按主键获取单篇文章"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── 摘要 ──────────────────────────────────────────────

def store_digest(date_str: str, summary: str, raw_data: str = ""):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO digests (date, summary, raw_data) VALUES (?, ?, ?)",
        (date_str, summary, raw_data),
    )
    conn.commit()
    conn.close()


def get_digest(date_str: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM digests WHERE date = ?", (date_str,)).fetchone()
    conn.close()
    return dict(row) if row else None


def store_topics(digest_date: str, topics: list[dict]) -> int:
    """写入某日议题行（先删后插）。"""
    conn = get_connection()
    conn.execute("DELETE FROM topics WHERE digest_date = ?", (digest_date,))
    for t in topics:
        conn.execute(
            """INSERT INTO topics
               (digest_date, keyword, instruments, direction, forecast_cycle, logic, related_articles)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                digest_date,
                t.get("keyword", ""),
                t.get("instruments", ""),
                t.get("direction", ""),
                t.get("forecast_cycle", ""),
                t.get("logic", ""),
                t.get("related_articles", ""),
            ),
        )
    conn.commit()
    conn.close()
    return len(topics)


def get_topics_by_date(digest_date: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM topics WHERE digest_date = ? ORDER BY id",
        (digest_date,),
    ).fetchall()
    conn.close()
    out: list[dict] = []
    for r in rows:
        item = dict(r)
        raw = item.get("related_articles") or "[]"
        try:
            item["related_articles_list"] = json.loads(raw)
        except json.JSONDecodeError:
            item["related_articles_list"] = []
        out.append(item)
    return out


def get_digests(limit: int = 30):
    conn = get_connection()
    rows = conn.execute(
        "SELECT date, substr(summary, 1, 200) as preview, created_at "
        "FROM digests ORDER BY date DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 涨停数据 ──────────────────────────────────────────

def get_latest_limitup_date() -> Optional[str]:
    conn = get_connection()
    row = conn.execute(
        "SELECT date FROM limitup_records ORDER BY date DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row["date"] if row else None


def store_limitup(date_str: str, stock_code: str, stock_name: str,
                  consecutive_days: int = 1, start_price: float = 0,
                  current_price: float = 0, gain_since_start: float = 0,
                  themes: str = "", first_limit_time: str = "",
                  market_cap: float = 0, sealed_amount: float = 0,
                  turnover_rate: float = 0, is_new_high: int = 0) -> bool:
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO limitup_records
               (date, stock_code, stock_name, consecutive_days, start_price,
                current_price, gain_since_start, themes, first_limit_time,
                market_cap, sealed_amount, turnover_rate, is_new_high)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (date_str, stock_code, stock_name, consecutive_days, start_price,
             current_price, gain_since_start, themes, first_limit_time,
             market_cap, sealed_amount, turnover_rate, is_new_high),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_limitup_records(date_str: str):
    """获取某天的涨停记录，按连板数降序"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM limitup_records WHERE date = ? ORDER BY consecutive_days DESC, sealed_amount DESC",
        (date_str,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_limitup_dates(limit: int = 30):
    """获取有涨停数据的日期列表"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT date, COUNT(*) as count FROM limitup_records GROUP BY date ORDER BY date DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 题材热度 ──────────────────────────────────────────

def store_theme_heat(date_str: str, theme: str, limitup_count: int,
                     leading_stock: str = "", avg_consecutive: float = 1.0,
                     total_market_cap: float = 0):
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO theme_heat
           (date, theme, limitup_count, leading_stock, avg_consecutive, total_market_cap)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (date_str, theme, limitup_count, leading_stock, avg_consecutive, total_market_cap),
    )
    conn.commit()
    conn.close()


def get_theme_heat(date_str: str):
    """获取某天的题材热度排行"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM theme_heat WHERE date = ? ORDER BY limitup_count DESC",
        (date_str,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 全文搜索 ──────────────────────────────────────────

def search_articles(keyword: str, limit: int = 50):
    """全文搜索文章标题和内容"""
    conn = get_connection()
    pattern = f"%{keyword}%"
    rows = conn.execute(
        "SELECT id, title, source, url, substr(content, 1, 200) as snippet, "
        "collected_at FROM articles WHERE title LIKE ? OR content LIKE ? "
        "ORDER BY collected_at DESC LIMIT ?",
        (pattern, pattern, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_limitup(keyword: str, limit: int = 50):
    """搜索涨停记录中的股票或题材"""
    conn = get_connection()
    pattern = f"%{keyword}%"
    rows = conn.execute(
        "SELECT date, stock_code, stock_name, consecutive_days, gain_since_start, themes "
        "FROM limitup_records WHERE stock_name LIKE ? OR stock_code LIKE ? OR themes LIKE ? "
        "ORDER BY date DESC LIMIT ?",
        (pattern, pattern, pattern, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
