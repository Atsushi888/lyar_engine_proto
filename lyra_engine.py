# lyra_engine.py — Lyra Engine Core (GPT-4o + Hermes fallback)

import os, json, html, time, streamlit as st
from personas import get_persona
from llm_router import call_with_fallback
from preflight import PreflightChecker


class LyraEngine:
    """Main controller of the Lyra Engine system."""

    def __init__(self, persona_id: str = "floria_ja"):
        # === 基本設定 ===
        self.persona = get_persona(persona_id)
        self.system_prompt = self.persona.system_prompt
        self.partner_name = self.persona.name
        self.starter_hint = self.persona.starter_hint

        # === 環境変数と診断 ===
        self.preflight = PreflightChecker()
        self.results = self.preflight.run_all()

        # === モデル設定 ===
        self.temperature = 0.7
        self.max_tokens = 800
        self.max_log = 500
        self.display_limit = 20000

        # === セッション管理 ===
        self._init_state()

    # =========================
    # セッション初期化
    # =========================
    def _init_state(self):
        """Streamlit セッション初期化"""
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "system", "content": self.system_prompt}]
        defaults = {"_busy": False, "_do_send": False, "_pending_text": ""}
        for k, v in defaults.items():
            st.session_state.setdefault(k, v)

    # =========================
    # UI部
    # =========================
    def render_header(self):
        st.set_page_config(page_title=f"Lyra Engine / {self.partner_name}", layout="wide")
        st.title(f"❄️ Lyra Engine — {self.partner_name}")
        st.caption("Streamlit Edition · Powered by GPT-4o + Hermes")

    def render_preflight(self):
        """起動前診断結果を表示"""
        with st.expander("起動前診断 (Preflight)", expanded=True):
            for key, r in self.results.items():
                mark = "✅" if r.ok else "❌"
                st.write(f"{mark} **{key.upper()}**: {r.message}")
            if not all(r.ok for r in self.results.values()):
                st.warning("一部の診断に失敗しました。APIキーや環境設定を確認してください。")

    def render_settings(self):
        with st.expander("接続設定", expanded=False):
            c1, c2 = st.columns(2)
            self.temperature = c1.slider("temperature", 0.0, 1.5, self.temperature, 0.05)
            self.max_tokens = c2.slider("max_tokens（1レス上限）", 64, 4096, self.max_tokens, 16)

    def render_chat(self):
        """チャットログ表示"""
        st.subheader("会話ログ")
        for msg in st.session_state["messages"]:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-bubble user'><b>あなた：</b><br>{html.escape(msg['content'])}</div>", unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                st.markdown(f"<div class='chat-bubble assistant'><b>{self.partner_name}：</b><br>{html.escape(msg['content'])}</div>", unsafe_allow_html=True)

    def render_input(self):
        """入力欄"""
        st.text_area("あなたの言葉（複数行OK）", key="user_input", height=160,
                     placeholder=self.starter_hint or "")
        if st.button("送信"):
            txt = st.session_state["user_input"].strip()
            if txt:
                self.send_message(txt)
                st.session_state["user_input"] = ""

    # =========================
    # メッセージ処理
    # =========================
    def send_message(self, user_text: str):
        """ユーザー発話を処理しAIへ送信"""
        st.session_state["messages"].append({"role": "user", "content": user_text})
        convo = st.session_state["messages"][-60:]

        with st.spinner(f"{self.partner_name}が考えています…"):
            reply, meta = call_with_fallback(
                convo,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

        st.session_state["_last_call_meta"] = meta
        st.session_state["messages"].append({"role": "assistant", "content": reply or "（返答なし）"})

    # =========================
    # 実行
    # =========================
    def run(self):
        self.render_header()
        self.render_preflight()
        self.render_settings()
        self.render_chat()
        self.render_input()


# =========================
# エントリーポイント
# =========================
if __name__ == "__main__":
    engine = LyraEngine("floria_ja")
    engine.run()
