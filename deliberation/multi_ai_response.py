from __future__ import annotations

from typing import Any, Dict
import streamlit as st

from components.multi_ai_display_config import MultiAIDisplayConfig
from components.multi_ai_model_viewer import MultiAIModelViewer
from components.multi_ai_judge_result_view import MultiAIJudgeResultView
from deliberation.judge_ai import JudgeAI

# このプロジェクトで審議対象にするモデル一覧
PARTICIPATING_MODELS: Dict[str, str] = {
    "gpt4o": "GPT-4o",
    "hermes": "Hermes",
}


class MultiAIResponse:
    """
    マルチAIレスポンスシステムの中核クラス。
    - models の表示
    - Judge の実行と表示
    をまとめて扱う。
    """

    def __init__(self) -> None:
        self.display_config = MultiAIDisplayConfig(initial=PARTICIPATING_MODELS)
        self.model_viewer = MultiAIModelViewer(self.display_config)
        self.judge_view = MultiAIJudgeResultView()
        self.judge_ai = JudgeAI()

    # ---- 内部ヘルパ ----
    def _ensure_models(self, llm_meta: Dict[str, Any]) -> Dict[str, Any] | None:
        models = llm_meta.get("models")
        if isinstance(models, dict) and models:
            return models
        return None

    def _ensure_judge(self, llm_meta: Dict[str, Any]) -> Dict[str, Any] | None:
        judge = llm_meta.get("judge")
        if isinstance(judge, dict):
            return judge

        models = self._ensure_models(llm_meta)
        if not models or len(models) < 2:
            # 2 モデル未満なら審議しない
            return None

        # JudgeAI 側で llm_meta["judge"] も埋めてくれる
        judge = self.judge_ai.run(llm_meta)
        return judge

    # ---- 表示エントリポイント ----
    def render(self, llm_meta: Dict[str, Any] | None) -> None:
        st.markdown("#### ✏️ マルチAIレスポンス")

        if not isinstance(llm_meta, dict) or not llm_meta:
            st.caption("（models 情報がありません）")
            return

        models = self._ensure_models(llm_meta)

        # モデル応答比較
        with st.expander("💬 モデル応答比較", expanded=True):
            if isinstance(models, dict) and models:
                # 新しいモデルが来たら自動で DisplayConfig に登録
                self.display_config.ensure_from_models(models)
                self.model_viewer.render(models)
            else:
                st.caption("（models 情報がありません）")

        # 審議結果
        with st.expander("⚖️ マルチAI審議結果", expanded=True):
            judge = self._ensure_judge(llm_meta)
            self.judge_view.render(judge)
