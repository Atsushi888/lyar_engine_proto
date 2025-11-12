# deliberation/ai_response_collector.py

from __future__ import annotations
from typing import Any, Dict, Optional

from deliberation.multi_ai_response import PARTICIPATING_MODELS
from personas.persona_floria_ja import Persona


class AIResponseCollector:
    """
    将来的に「複数AIから一括でレスポンスを集める」係。
    今は最低限、llm_meta["models"] を組み立てる実装。

    ★ persona.model_params から、モデルごとの temperature 等を読み取り、
      llm_meta["models"][key]["params"] に入れておく。
    """

    def __init__(self) -> None:
        self.participating_models = PARTICIPATING_MODELS

    # ---- モデル別パラメータ抽出 ----
    def _resolve_params_for_model(
        self,
        persona: Optional[Persona],
        model_key: str,
    ) -> Dict[str, Any]:
        if persona is None:
            return {}

        mp_all = getattr(persona, "model_params", None)
        if not isinstance(mp_all, dict):
            return {}

        mp = mp_all.get(model_key)
        if not isinstance(mp, dict):
            return {}

        result: Dict[str, Any] = {}

        t_cfg = mp.get("temperature")
        if isinstance(t_cfg, dict):
            if "default" in t_cfg:
                result["temperature"] = float(t_cfg["default"])
        elif isinstance(t_cfg, (int, float)):
            result["temperature"] = float(t_cfg)

        if "max_tokens" in mp:
            try:
                result["max_tokens"] = int(mp["max_tokens"])
            except Exception:
                pass

        for k in ("top_p", "presence_penalty", "frequency_penalty"):
            if k in mp:
                result[k] = mp[k]

        return result

    # ---- models セクション構築 ----
    def attach_models(
        self,
        llm_meta: Dict[str, Any],
        base_reply_text: str,
        base_usage: Dict[str, Any] | None,
        persona: Optional[Persona] = None,
    ) -> None:
        if base_usage is None:
            base_usage = {}

        models: Dict[str, Any] = {}

        # GPT-4o
        gpt_params = self._resolve_params_for_model(persona, "gpt4o")
        models["gpt4o"] = {
            "reply": base_reply_text,
            "usage": base_usage,
            "route": llm_meta.get("route", "gpt"),
            "model_name": llm_meta.get("model_main", "gpt-4o"),
            "params": gpt_params,
        }

        # Hermes
        hermes_params = self._resolve_params_for_model(persona, "hermes")
        models["hermes"] = {
            "reply": base_reply_text,
            "usage": base_usage,
            "route": "openrouter",
            "model_name": "nousresearch/hermes-4-70b",
            "params": hermes_params,
        }

        llm_meta["models"] = models
