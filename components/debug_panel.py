# components/debug_panel.py
from typing import Any, Dict
import streamlit as st
from .model_viewer import MultiModelViewer


class DebugPanel:
    def __init__(self) -> None:
        self.model_viewer = MultiModelViewer("モデル比較：GPT-4o vs Hermes")

    def render(self, llm_meta: Dict[str, Any] | None) -> None:
        st.subheader("🧠 LLM デバッグ")

        # ルート（gpt / openrouter）や token 使用量など、
        # 既存のデバッグ表示があればここに書く

        # モデルごとの返答ビューは専用クラスにお任せ
        self.model_viewer.render(llm_meta)
