"""涨停数据采集——通过 AKShare 获取东方财富涨停板数据"""

import json
import os
from datetime import date
from typing import Optional

from minitrader.db import (
    get_limitup_records,
    get_theme_heat,
    store_limitup,
    store_theme_heat,
)

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# 东方财富 stock_zt_pool_em 接口需要的日期格式
_AKDATE_FMT = "%Y%m%d"


def _format_akdate(target_date: str) -> str:
    """将 ISO 日期 YYYY-MM-DD 转为 akshare 需要的 YYYYMMDD。"""
    return target_date.replace("-", "")


def collect_limitup_data(target_date: Optional[str] = None) -> dict:
    """采集涨停数据并入库

    使用 AKShare 的 stock_zt_pool_em 接口获取东方财富涨停板数据。
    返回: {"date": str, "total": int, "stored": int, "records": list, "themes": list}
    """
    if target_date is None:
        target_date = date.today().isoformat()

    # 同一天重复运行时直接复用 DB 中的统计，避免反复请求
    existing = get_limitup_records(target_date)
    if existing:
        themes_existing = get_theme_heat(target_date)
        return {
            "date": target_date,
            "total": len(existing),
            "stored": 0,
            "records": existing,
            "themes": [
                {
                    "theme": t["theme"],
                    "count": t["limitup_count"],
                    "leading_stock": t.get("leading_stock", ""),
                }
                for t in themes_existing
            ],
            "note": "already_collected",
        }

    try:
        import akshare as ak
    except ImportError:
        return {"date": target_date, "total": 0, "stored": 0, "records": [], "themes": [], "error": "akshare not installed"}

    try:
        df = ak.stock_zt_pool_em(date=_format_akdate(target_date))
    except Exception as e:
        return {"date": target_date, "total": 0, "stored": 0, "records": [], "themes": [], "error": str(e)}

    if df is None or df.empty:
        return {"date": target_date, "total": 0, "stored": 0, "records": [], "themes": [], "note": "no_data"}

    stored = 0
    records = []
    theme_map: dict[str, dict] = {}

    def _num(row, *names, default=0):
        for n in names:
            v = row.get(n)
            if v is None:
                continue
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
        return default

    for _, row in df.iterrows():
        stock_code = str(row.get("代码", ""))
        stock_name = str(row.get("名称", ""))
        consecutive = int(_num(row, "连板数"))
        price = _num(row, "最新价", "现价")
        turnover = _num(row, "换手率")
        market_cap = _num(row, "总市值") / 1e8
        sealed_amt = _num(row, "封板资金", "封单额") / 1e8
        first_time = str(row.get("首次封板时间", "") or "")
        # 东方财富涨停板池不再返回「涨停原因」字段，仅剩「所属行业」（申万行业分类）
        industry = str(row.get("所属行业") or "").strip()
        # 行业名有时被截断（如"自动化设"），保留原样
        # 连板数>1时估算启动涨幅；价格缺失时退化为 0，避免除零
        start_price_est = 0.0
        gain = 0.0
        if consecutive > 1 and price > 0:
            start_price_est = price / ((1 + 0.1) ** (consecutive - 1))
            if start_price_est > 0:
                gain = round((price / start_price_est - 1) * 100, 2)

        ok = store_limitup(
            date_str=target_date,
            stock_code=stock_code,
            stock_name=stock_name,
            consecutive_days=consecutive,
            start_price=round(start_price_est, 2),
            current_price=round(price, 2),
            gain_since_start=round(gain, 2),
            themes=industry,
            first_limit_time=first_time,
            market_cap=round(market_cap, 2),
            sealed_amount=round(sealed_amt, 2),
            turnover_rate=round(turnover, 2),
            is_new_high=1 if consecutive >= 3 else 0,
        )
        if ok:
            stored += 1

        records.append({
            "code": stock_code,
            "name": stock_name,
            "consecutive": consecutive,
            "price": round(price, 2),
            "themes": industry,
            "first_limit_time": first_time,
            "gain_since_start": round(gain, 2),
        })

        # 统计题材（基于所属行业）
        if industry:
            # 拆分多个题材
            for t in industry.replace("，", ",").replace("、", ",").split(","):
                t = t.strip()
                if len(t) >= 2:
                    if t not in theme_map:
                        theme_map[t] = {"count": 0, "stocks": []}
                    theme_map[t]["count"] += 1
                    theme_map[t]["stocks"].append(stock_name)

    # 存储题材热度 TOP15
    themes = []
    sorted_themes = sorted(theme_map.items(), key=lambda x: -x[1]["count"])[:15]
    for theme, info in sorted_themes:
        store_theme_heat(
            date_str=target_date,
            theme=theme,
            limitup_count=info["count"],
            leading_stock=info["stocks"][0] if info["stocks"] else "",
            avg_consecutive=1.0,
            total_market_cap=0,
        )
        themes.append({
            "theme": theme,
            "count": info["count"],
            "leading_stock": info["stocks"][0] if info["stocks"] else "",
        })

    return {
        "date": target_date,
        "total": len(df),
        "stored": stored,
        "records": records,
        "themes": themes,
    }
