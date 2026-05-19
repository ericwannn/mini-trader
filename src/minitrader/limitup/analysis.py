"""涨停数据分析——梯队划分、题材热度排行、龙头识别"""

from typing import Optional


def analyze_limitup(records: list[dict], themes: list[dict]) -> dict:
    """分析涨停数据，生成结构化的复盘信息"""
    if not records:
        return {"summary": "暂无涨停数据", "tiers": {}, "top_themes": [], "dragons": []}

    # 梯队划分
    tiers = {"首板": 0, "二板": 0, "三板": 0, "四板及以上": 0}
    tier_details = {"首板": [], "二板": [], "三板": [], "四板及以上": []}

    for r in records:
        c = r.get("consecutive", 0)
        if c <= 1:
            tiers["首板"] += 1
            tier_details["首板"].append(r)
        elif c == 2:
            tiers["二板"] += 1
            tier_details["二板"].append(r)
        elif c == 3:
            tiers["三板"] += 1
            tier_details["三板"].append(r)
        else:
            tiers["四板及以上"] += 1
            tier_details["四板及以上"].append(r)

    # 龙头识别（连板数 >= 3 且 封板时间早）
    dragons = []
    for r in records:
        if r.get("consecutive", 0) >= 3:
            dragons.append(r)
    dragons.sort(key=lambda x: (-x.get("consecutive", 0), x.get("first_limit_time", "99:99")))

    # 封板时间分析
    early_stocks = []
    for r in records:
        ft = r.get("first_limit_time", "")
        if ft and ft <= "10:00":
            early_stocks.append({
                "name": r.get("name", ""),
                "time": ft,
                "consecutive": r.get("consecutive", 0),
            })

    return {
        "total": len(records),
        "tiers": tiers,
        "tier_details": tier_details,
        "dragons": dragons[:10],
        "early_stocks": early_stocks[:10],
        "top_themes": themes[:10] if themes else [],
    }
