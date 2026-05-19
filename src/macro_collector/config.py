"""环境变量与可选 .env 配置加载（项目根目录 `.env`，不提交版本库）。"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    """从项目根 `.env` 读取 KEY=VALUE，不覆盖已存在的环境变量。"""
    env_path = PROJECT_DIR / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def wechat_enabled() -> bool:
    """MACRO_WECHAT_ENABLED=0 时跳过微信公众号采集。"""
    val = os.environ.get("MACRO_WECHAT_ENABLED", "1").strip().lower()
    return val not in ("0", "false", "no", "off")


def wechat_proxy() -> str | None:
    proxy = os.environ.get("MACRO_WECHAT_PROXY", "").strip()
    return proxy or None


def wechat_cookie() -> str | None:
    cookie = os.environ.get("MACRO_WECHAT_COOKIE", "").strip()
    return cookie or None


def llm_api_key() -> str | None:
    key = os.environ.get("MACRO_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    return (key or "").strip() or None


def llm_base_url() -> str:
    return (
        os.environ.get("MACRO_LLM_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or "https://api.openai.com/v1"
    ).rstrip("/")


def llm_model() -> str:
    return os.environ.get("MACRO_LLM_MODEL", "gpt-4o-mini").strip()
