# llm_router.py
# OpenAI / OpenRouter まわりの生呼び出しをまとめた層

from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

from openai import OpenAI, BadRequestError

# ========= 環境変数 =========

# 会話本体（フローリア）のメインモデル
OPENAI_API_KEY_INITIAL = os.getenv("OPENAI_API_KEY")
MAIN_MODEL = os.getenv("OPENAI_MAIN_MODEL", "gpt-4o")

# Judge 用モデル（デフォルトは MAIN_MODEL と同じにしておく）
JUDGE_MODEL = os.getenv("OPENAI_JUDGE_MODEL", MAIN_MODEL)

# OpenRouter / Hermes 用
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_KEY_INITIAL = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
HERMES_MODEL = os.getenv("OPENROUTER_HERMES_MODEL", "nousresearch/hermes-4-70b")


# ========= 共通 OpenAI 呼び出しヘルパ =========

def _ensure_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY_INITIAL
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY が設定されていません。")
    return OpenAI(api_key=api_key)


def _call_openai_model(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> Tuple[str, Dict[str, Any]]:
    client = _ensure_openai_client()

    resp = client.chat.completions.create(
        model=model,
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


# ========= GPT-4o（物語本体） =========

def _call_gpt(
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> Tuple[str, Dict[str, Any]]:
    return _call_openai_model(MAIN_MODEL, messages, temperature, max_tokens)


# ========= Judge 用モデル（GPT-5.1 想定） =========

def _call_judge_model(
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> Tuple[str, Dict[str, Any]]:
    """
    審判用モデル呼び出し。
    実際に使うモデル名は環境変数 OPENAI_JUDGE_MODEL で差し替え可能。
    """
    return _call_openai_model(JUDGE_MODEL, messages, temperature, max_tokens)


# ========= OpenRouter / Hermes =========

def _call_hermes(
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> Tuple[str, Dict[str, Any]]:
    api_key = os.getenv("OPENROUTER_API_KEY") or OPENROUTER_API_KEY_INITIAL
    if not api_key:
        # キーが無いなら即ダミー返し
        return "[Hermes: OPENROUTER_API_KEY 未設定]", {
            "error": "OPENROUTER_API_KEY not set",
        }

    client_or = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )
    try:
        resp = client_or.chat.completions.create(
            model=HERMES_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except BadRequestError as e:
        # 400 系はここでテキスト化して返す
        return f"[Hermes BadRequestError: {e}]", {
            "error": str(e),
        }
    except Exception as e:  # noqa: BLE001
        return f"[Hermes Error: {e}]", {
            "error": str(e),
        }

    text = resp.choices[0].message.content or ""
    usage: Dict[str, Any] = {}
    if getattr(resp, "usage", None) is not None:
        usage = {
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
            "completion_tokens": getattr(resp.usage, "completion_tokens", None),
            "total_tokens": getattr(resp.usage, "total_tokens", None),
        }
    return text, usage


# ========= 公開 API =========

def call_with_fallback(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 800,
) -> Tuple[str, Dict[str, Any]]:
    """
    以前は GPT → Hermes フォールバックだったが、
    今は GPT-4o 単体のみをメインとして返す。
    """
    meta: Dict[str, Any] = {}
    try:
        text, usage = _call_gpt(messages, temperature, max_tokens)
        meta["route"] = "gpt"
        meta["model_main"] = MAIN_MODEL
        meta["usage_main"] = usage
        return text, meta
    except Exception as e:  # noqa: BLE001
        meta["route"] = "error"
        meta["gpt_error"] = str(e)
        return "", meta


def call_hermes(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 800,
) -> Tuple[str, Dict[str, Any]]:
    """
    Hermes 単体呼び出し。
    """
    text, usage = _call_hermes(messages, temperature, max_tokens)
    meta: Dict[str, Any] = {
        "route": "openrouter",
        "model_main": HERMES_MODEL,
        "usage_main": usage,
    }
    return text, meta


def call_judge_model(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 800,
) -> Tuple[str, Dict[str, Any]]:
    """
    Judge 用モデル（GPT-5.1 想定）呼び出し。
    - Multi AI の 3つ目の候補としても利用可能
    - JudgeAI 内部から審判用としても利用
    """
    text, usage = _call_judge_model(messages, temperature, max_tokens)
    meta: Dict[str, Any] = {
        "route": "gpt-judge",
        "model_main": JUDGE_MODEL,
        "usage_main": usage,
    }
    return text, meta
