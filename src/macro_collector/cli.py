"""macro-collector CLI — collect / digest / limitup / frontend / all"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from macro_collector import __about__
from macro_collector.collectors import ALL_COLLECTORS
from macro_collector.collectors.wechat import WeChatCollector
from macro_collector.db import init_db
from macro_collector.config import wechat_enabled
from macro_collector.db.sync import persist_articles, persist_digest, persist_topics
from macro_collector.models.digest import (
    extract_topics_from_articles,
    generate_digest_markdown,
    load_raw,
    parse_topics_from_markdown,
    save_digest,
    save_raw,
)


def _dedupe_articles(articles: list) -> list:
    seen: set[str] = set()
    out = []
    for a in articles:
        key = (getattr(a, "url", None) or "").strip() or f"{a.title}\0{a.account}"
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def _collectors_for_args(args: argparse.Namespace):
    for c in ALL_COLLECTORS:
        if isinstance(c, WeChatCollector):
            if not wechat_enabled():
                continue
            yield WeChatCollector(
                keywords=args.keywords,
                per_keyword=args.per_keyword,
                max_total=args.max_total,
            )
        else:
            yield c


# ── 采集 ──────────────────────────────────────────────


def do_collect(args: argparse.Namespace):
    """执行采集，保存原始 JSON 并同步入库"""
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"=== 宏观资产配置资讯采集: {today} ===\n")

    all_articles = []
    for collector in _collectors_for_args(args):
        print(f"\n--- {collector.source_name} ---")
        try:
            articles = collector.fetch()
            all_articles.extend(articles)
            print(f"  采集 {len(articles)} 条")
        except Exception as e:
            print(f"  ⚠️ 失败: {e}")

    merged = _dedupe_articles(all_articles)
    print(f"\n=== 采集完成: 共 {len(merged)} 条（去重后）===")
    path = save_raw(merged, target_date=today)
    print(f"\n原始数据路径: {path}")

    inserted, skipped = persist_articles(merged)
    print(f"入库 articles: 新增 {inserted} 条，跳过重复 {skipped} 条")
    return path


# ── 摘要 ──────────────────────────────────────────────


def do_digest(args: argparse.Namespace):
    """基于原始数据生成本地 Markdown 摘要文件（默认规则引擎；--llm 可选）"""
    target_date = getattr(args, "date", None) or datetime.now().strftime("%Y-%m-%d")
    use_llm = getattr(args, "llm", False)

    try:
        articles = load_raw(target_date)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(f"已加载 {target_date} 共 {len(articles)} 篇文章")
    if use_llm:
        from macro_collector.digest.llm import generate_digest_via_llm

        md = generate_digest_via_llm(articles, target_date)
        topics = parse_topics_from_markdown(md, target_date)
    else:
        md = generate_digest_markdown(articles, target_date)
        topics = extract_topics_from_articles(articles, target_date)

    path = save_digest(md, target_date)
    persist_digest(target_date, md, raw_path=path)
    n_topics = persist_topics(target_date, topics)
    print(f"\n完成。摘要文件: {path}")
    print(f"入库 digests({target_date}) → macro.db")
    if n_topics:
        print(f"入库 topics({target_date}): {n_topics} 条")
    return path


# ── 涨停复盘 ──────────────────────────────────────────


def do_limitup(args: argparse.Namespace):
    """采集涨停数据并入库"""
    from macro_collector.limitup import collect_limitup_data

    init_db()
    print("=== 涨停复盘数据采集 ===")
    result = collect_limitup_data()
    print(f"日期: {result['date']}")
    print(f"涨停总数: {result['total']}")
    print(f"新增入库: {result['stored']}")
    if result.get("note"):
        print(f"说明: {result['note']}")
    if result.get("error"):
        print(f"⚠️ 错误: {result['error']}")
    if result.get("themes"):
        print(f"\n题材热点 TOP5:")
        for t in result["themes"][:5]:
            print(f"  - {t['theme']}: {t['count']}只涨停 (龙头: {t.get('leading_stock','')})")
    return result


# ── 前端 ──────────────────────────────────────────────


def do_frontend(args: argparse.Namespace):
    """启动 FastAPI 前端（前台，等同 serve start -f）"""
    from macro_collector.service import start_server

    host = getattr(args, "host", None)
    port = getattr(args, "port", None)
    start_server(host=host, port=port, foreground=True)


def do_serve(args: argparse.Namespace):
    """管理 FastAPI 后端：start / stop / restart / status"""
    from macro_collector.service import restart_server, start_server, status_server, stop_server

    action = args.serve_action
    if action == "start":
        code = start_server(
            host=getattr(args, "host", None),
            port=getattr(args, "port", None),
            foreground=getattr(args, "foreground", False),
        )
    elif action == "stop":
        code = stop_server()
    elif action == "restart":
        code = restart_server(
            host=getattr(args, "host", None),
            port=getattr(args, "port", None),
        )
    else:
        code = status_server()
    sys.exit(code)


# ── 全流程 ────────────────────────────────────────────


def do_all(args: argparse.Namespace):
    """采集 → 摘要 → 涨停复盘(带入库) → 展示结果"""
    today = datetime.now().strftime("%Y-%m-%d")
    init_db()

    # 采集
    do_collect(args)

    # 摘要
    args.date = today
    do_digest(args)

    print("\n=== 涨停复盘 ===")
    try:
        from macro_collector.limitup import collect_limitup_data

        result = collect_limitup_data(target_date=today)
        print(f"日期: {result['date']}  涨停: {result['total']} 只  新增: {result['stored']} 只")
        if result.get("note"):
            print(f"  说明: {result['note']}")
        if result.get("error"):
            print(f"  ⚠️ 错误: {result['error']}")
        if result.get("themes"):
            print("  题材热点 TOP5:")
            for t in result["themes"][:5]:
                print(f"    - {t['theme']}: {t['count']} 只 (龙头: {t.get('leading_stock','')})")
    except Exception as e:
        print(f"  ⚠️ 涨停数据采集失败: {e}")


# ── CLI ──────────────────────────────────────────────


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="macro-collector",
        description="每日宏观资产配置资讯采集、涨停复盘与摘要生成",
    )
    parser.add_argument("--version", action="version", version=__about__.__version__)

    sub = parser.add_subparsers(dest="command", required=True)

    # collect
    p_collect = sub.add_parser("collect", help="多源采集并保存原始 JSON")
    p_collect.add_argument("--keywords", nargs="+", default=None, help="微信搜索关键词（仅微信公众号源）")
    p_collect.add_argument("--per-keyword", type=int, default=4, help="每个关键词取几篇（微信）")
    p_collect.add_argument("--max-total", type=int, default=25, help="微信源最多采集条数上限")
    p_collect.set_defaults(func=do_collect)

    # digest
    p_digest = sub.add_parser("digest", help="由 raw JSON 生成 Markdown 摘要")
    p_digest.add_argument("--date", default=None, help="日期 YYYY-MM-DD，默认今天")
    p_digest.add_argument(
        "--llm",
        action="store_true",
        help="使用 LLM 生成摘要（需 MACRO_LLM_API_KEY 或 OPENAI_API_KEY）",
    )
    p_digest.set_defaults(func=do_digest)

    p_digest_llm = sub.add_parser("digest-llm", help="等同 digest --llm")
    p_digest_llm.add_argument("--date", default=None, help="日期 YYYY-MM-DD，默认今天")
    p_digest_llm.set_defaults(func=do_digest, llm=True)

    # limitup
    p_limitup = sub.add_parser("limitup", help="涨停复盘（采集+入库+分析）")
    p_limitup.set_defaults(func=do_limitup)

    # frontend
    p_frontend = sub.add_parser("frontend", help="前台启动 Web 界面（等同 serve start -f）")
    p_frontend.add_argument("--host", default=None, help="监听地址")
    p_frontend.add_argument("--port", type=int, default=None, help="端口")
    p_frontend.set_defaults(func=do_frontend)

    # serve — 后台服务管理
    p_serve = sub.add_parser("serve", help="管理 Web 后端：start / stop / restart / status")
    serve_sub = p_serve.add_subparsers(dest="serve_action", required=True)

    p_s_start = serve_sub.add_parser("start", help="启动服务（默认后台）")
    p_s_start.add_argument("--host", default=None)
    p_s_start.add_argument("--port", type=int, default=None)
    p_s_start.add_argument("-f", "--foreground", action="store_true", help="前台运行")
    p_s_start.set_defaults(func=do_serve, serve_action="start")

    p_s_stop = serve_sub.add_parser("stop", help="停止后台服务")
    p_s_stop.set_defaults(func=do_serve, serve_action="stop")

    p_s_restart = serve_sub.add_parser("restart", help="重启后台服务")
    p_s_restart.add_argument("--host", default=None)
    p_s_restart.add_argument("--port", type=int, default=None)
    p_s_restart.set_defaults(func=do_serve, serve_action="restart")

    p_s_status = serve_sub.add_parser("status", help="查看运行状态")
    p_s_status.set_defaults(func=do_serve, serve_action="status")

    # all
    p_all = sub.add_parser("all", help="采集 + 摘要 + 涨停复盘 + 入库")
    p_all.add_argument("--keywords", nargs="+", default=None)
    p_all.add_argument("--per-keyword", type=int, default=4)
    p_all.add_argument("--max-total", type=int, default=25)
    p_all.set_defaults(func=do_all)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
