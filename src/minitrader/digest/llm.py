"""通过 OpenAI 兼容 API 生成 Markdown 摘要（streaming 模式，避免非 streaming 挂起）。"""

from __future__ import annotations

import json
import sys
import time

import httpx

from minitrader.config import llm_api_key, llm_base_url, llm_model
from minitrader.digest.generator import format_for_llm
from minitrader.models import Article
from minitrader.models.digest import generate_intro_prompt


_SYSTEM_PROMPT = (
    "你是专业的宏观资产配置分析师。根据用户提供的当日资讯列表，"
    "生成结构化 Markdown 日报。要求：\n"
    "1. 标题为 `# 每日宏观资产配置摘要 — <日期>`\n"
    "2. 含 `## 总体概述` 段落\n"
    "3. 按 3-8 个核心议题分节，每节使用 `## N. 议题名`\n"
    "4. 每条资讯：`### [标题](URL)`，含 **主体**、**核心观点**（谁对何标的持何观点、周期多长）、"
    "来源、内容摘要、涉及品种、方向判断、预测周期、分析逻辑\n"
    "5. 各议题节首可加「本节观点速览」 bullet 列表\n"
    "6. 仅输出 Markdown，不要代码块包裹"
)


def _articles_to_llm_payload(articles: list[Article], target_date: str) -> str:
    """优先使用带正文的文章构造 prompt；若无则回退到 generator 格式化。"""
    with_body = [a for a in articles if a.content and len(a.content) > 80]
    if with_body:
        return generate_intro_prompt(with_body, target_date)
    data = {
        "date": target_date,
        "articles": [a.to_dict() for a in articles],
        "sources": {},
    }
    return format_for_llm(data)


def generate_digest_via_llm(articles: list[Article], target_date: str) -> str:
    """调用 LLM 生成摘要 Markdown（streaming 模式）；无 API Key 时打印错误并 exit(1)。"""
    api_key = llm_api_key()
    if not api_key:
        print(
            "❌ 未配置 LLM API Key。请设置 MINITRADER_LLM_API_KEY（或 DEEPSEEK_API_KEY / OPENAI_API_KEY）。\n"
            "   可选：MINITRADER_LLM_BASE_URL（OpenAI 兼容端点，DeepSeek 见 .env.example）、"
            "MINITRADER_LLM_MODEL"
        )
        sys.exit(1)

    user_content = _articles_to_llm_payload(articles, target_date)
    url = f"{llm_base_url()}/chat/completions"
    payload = {
        "model": llm_model(),
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.4,
        "stream": True,  # streaming 避免 DeepSeek 非 streaming 挂起
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"正在调用 LLM ({llm_model()}) …")
    print(f"  prompt 大小: {len(user_content)} 字符 / {len(user_content) // 2} tokens", flush=True)

    full_text = ""
    chunk_count = 0
    start_time = time.time()
    try:
        with httpx.Client(timeout=600.0) as client:
            with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        chunk = json.loads(raw)
                        delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if delta:
                            full_text += delta
                            chunk_count += 1
                            # 每 50 个 chunk 显示一次进度
                            if chunk_count % 50 == 0:
                                elapsed = time.time() - start_time
                                print(f"  ... 已接收 {chunk_count} 个 chunk ({elapsed:.0f}s)", flush=True)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
    except httpx.HTTPStatusError as e:
        body = e.response.text[:500] if e.response is not None else ""
        print(f"❌ LLM 请求失败 HTTP {e.response.status_code}: {body}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ LLM 请求失败: {type(e).__name__}: {e}")
        sys.exit(1)

    elapsed = time.time() - start_time
    print(f"  ✓ LLM 响应完成: {len(full_text)} 字符, {chunk_count} chunks, 耗时 {elapsed:.0f}s", flush=True)

    text = (full_text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    if not text.startswith("#"):
        text = f"# 每日宏观资产配置摘要 — {target_date}\n\n{text}"
    return text.rstrip() + "\n"
