"""
macro_collector/frontend/app.py — FastAPI 前端
运行: uv run python src/macro_collector/frontend/app.py
访问: http://localhost:8000
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

# 确保项目在 PYTHONPATH 中
PROJECT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_DIR))

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from macro_collector.db import (
    init_db,
    get_digests,
    get_digest,
    get_topics_by_date,
    get_article_by_id,
    get_articles_by_date,
    get_limitup_records,
    get_limitup_dates,
    get_theme_heat,
    search_articles,
    search_limitup,
)
from macro_collector.frontend.markdown_render import render_markdown_html
from macro_collector.frontend.preview import plain_digest_preview

app = FastAPI(title="宏观资产配置日报")

# 模板路径
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """首页——摘要时间线"""
    digests = get_digests(limit=30)
    for d in digests:
        d["preview_plain"] = plain_digest_preview(d.get("preview") or "")
    return templates.TemplateResponse(
        request,
        "index.html",
        {"digests": digests},
    )


@app.get("/article/{article_id}", response_class=HTMLResponse)
def article_detail(request: Request, article_id: int):
    """单篇文章详情（站内阅读）"""
    article = get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    collected = (article.get("collected_at") or "")[:10]
    return templates.TemplateResponse(
        request,
        "article.html",
        {
            "article": article,
            "focus_date": collected,
        },
    )


@app.get("/digest/{date_str}", response_class=HTMLResponse)
def digest_detail(request: Request, date_str: str):
    """某天的摘要详情"""
    digest = get_digest(date_str)
    articles = get_articles_by_date(date_str)
    limitups = get_limitup_records(date_str)
    themes = get_theme_heat(date_str)

    summary = ""
    summary_html = ""
    if digest:
        summary = digest.get("summary", "")
        summary_html = render_markdown_html(summary)

    topics = get_topics_by_date(date_str)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "digest": digest,
            "articles": articles,
            "limitups": limitups,
            "themes": themes,
            "topics": topics,
            "summary": summary,
            "summary_html": summary_html,
            "focus_date": date_str,
        },
    )


@app.get("/limitup", response_class=HTMLResponse)
def limitup_page(request: Request):
    """涨停复盘页"""
    dates = get_limitup_dates(limit=30)
    selected = request.query_params.get("date", "")
    records = []
    themes = []
    if selected:
        records = get_limitup_records(selected)
        themes = get_theme_heat(selected)
    elif dates:
        selected = dates[0]["date"]
        records = get_limitup_records(selected)
        themes = get_theme_heat(selected)

    return templates.TemplateResponse(
        request,
        "limitup.html",
        {
            "request": request,
            "dates": dates,
            "selected_date": selected,
            "records": records,
            "themes": themes,
        },
    )


@app.get("/search", response_class=HTMLResponse)
def search_page(
    request: Request,
    q: str = Query("", description="搜索关键字"),
):
    """搜索页"""
    articles = []
    limitups = []
    if q:
        articles = search_articles(q)
        limitups = search_limitup(q)

    return templates.TemplateResponse(
        request,
        "search.html",
        {
            "request": request,
            "query": q,
            "articles": articles,
            "limitups": limitups,
        },
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "macro-collector"}


@app.get("/api/digests")
def api_digests():
    return get_digests(limit=30)


@app.get("/api/limitup/{date_str}")
def api_limitup(date_str: str):
    return {
        "records": get_limitup_records(date_str),
        "themes": get_theme_heat(date_str),
    }


def main():
    from macro_collector.service import server_host, server_port, start_server

    start_server(host=server_host(), port=server_port(), foreground=True)


if __name__ == "__main__":
    main()
