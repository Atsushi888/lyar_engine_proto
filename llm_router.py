# deliberation/llm_router.py

import os
from typing import Any, Dict, List, Tuple
from openai import OpenAI, BadRequestError

# ===== GPT-4o =====
OPENAI_API_KEY_INITIAL = os.getenv("OPENAI_API_KEY")
MAIN_MODEL = os.getenv("OPENAI_MAIN_MODEL", "gpt-4o")

# ===== Hermes / OpenRouter =====
OPENROUTER_API_KEY_INITIAL = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
HERMES_MODEL = os.getenv("OPENROUTER_HERMES_MODEL", "nousresearch/hermes-4-70b")


def _call_gpt(messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> Tuple[str, Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY_INITIAL
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY が設定されていません。")

    client_openai = OpenAI(api_key=api_key)
    resp = client_openai.chat.completions.create(
        model=MAIN_MODEL,
        messages=messages,
        temperature=float(temperature),
        max_tokens=int(max_tokens),
    )

    text = resp.choices[0].message.content or ""
    usage: Dict[str, Any] = {}
    if getattr(resp, "usage", None) is not None:
        usage = {
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
            "completion_tokens": getattr(resp.usage, "completion_tokens", None),
            "total_tokens": getattr(resp.usage, "total_tokens", None),
        }
    return text, usage


def _call_hermes(messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> Tuple[str, Dict[str, Any]]:
    api_key = os.getenv("OPENROUTER_API_KEY") or OPENROUTER_API_KEY_INITIAL
    if not api_key:
        return "[Hermes: OPENROUTER_API_KEY 未設定]", {"error": "OPENROUTER_API_KEY not set"}

    client_or = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
    try:
        resp = client_or.chat.completions.create(
            model=HERMES_MODEL,
            messages=messages,
            temperature=float(temperature),
            max_tokens=int(max_tokens),
        )
    except BadRequestError as e:
        return f"[Hermes BadRequestError: {e}]", {"error": str(e)}
    except Exception as e:
        return f"[Hermes Error: {e}]", {"error": str(e)}

    text = resp.choices[0].message.content or ""
    usage: Dict[str, Any] = {}
    if getattr(resp, "usage", None) is not None:
        usage = {
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
            "completion_tokens": getattr(resp.usage, "completion_tokens", None),
            "total_tokens": getattr(resp.usage, "total_tokens", None),
        }
    return text, usage


def call_with_fallback(messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 800) -> Tuple[str, Dict[str, Any]]:
    meta: Dict[str, Any] = {}
    try:
        text, usage = _call_gpt(messages, temperature, max_tokens)
        meta["route"] = "gpt"
        meta["model_main"] = MAIN_MODEL
        meta["usage_main"] = usage
        return text, meta
    except Exception as e:
        meta["route"] = "error"
        meta["gpt_error"] = str(e)
        return "", meta


def call_hermes(messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 800) -> Tuple[str, Dict[str, Any]]:
    text, usage = _call_hermes(messages, temperature, max_tokens)
    meta: Dict[str, Any] = {
        "route": "openrouter",
        "model_main": HERMES_MODEL,
        "usage_main": usage,
    }
    return text, meta
