# lyra_engine.py — Lyra Engine Core (GPT-4o + Hermes fallback, Preflight統合)

import os, json, html, time, streamlit as st
from personas import get_persona
from llm_router import call_with_fallback
from preflight import PreflightChecker


# ===============================
# Streamlit セッション初期化
# ===============================
if "user_input" not in st.session_state:
    st.session_state["user_input"] = ""
if "show_hint" not in st.session_state:
    st.session_state["show_hint"] = False

for k, v in {
    "_busy": False,
    "_do_send": False,
    "_pending_text": "",
    "_clear_input": False,
    "_do_reset": False,
    "_ask_reset": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "messages" not in st.session_state:
    st.session_state["messages"] = []


# ===============================
# Lyra Engine Core クラス
# ===============================
class LyraEngine:
    """Main controller of the Lyra Engine system."""

    def __init__(self, persona_id: str = "floria_ja"):
        # === 人格読込 ===
        self.persona = get_persona(persona_id)
        self.system_prompt = self.persona.system_prompt
        self.partner_name = self.persona.name
        self.starter_hint = self.persona.starter_hint

        # === 診断 ===
        self.preflight = PreflightChecker()
        self.results = self.preflight.run_all()

        # === モデル設定 ===
        self.temperature = 0.7
        self.max_tokens = 800
        self.max_log = 500
        self.display_limit = 20000

    # =========================
    # 初期フラグ処理
    # =========================
    def process_flags(self):
        """UI描画前に session_state の管理フラグを処理"""
        if st.session_state.get("_clear_input"):
            st.session_state["_clear_input"] = False
            st.session_state["user_input"] = ""

        if st.session_state.get("_do_reset"):
            st.session_state["_do_reset"] = False
            st.session_state.update({
                "user_input": "",
                "_pending_text": "",
                "_busy": False,
                "_do_send": False,
                "_ask_reset": False,
                "messages": [{"role": "system", "content": self.system_prompt}],
            })

        if not st.session_state["messages"]:
            st.session_state["messages"] = [
                {"role": "system", "content": self.system_prompt}
            ]

    # =========================
    # UI部品
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
        """チャットログを表示"""
        st.subheader("会話ログ")
        for msg in st.session_state["messages"]:
            if msg["role"] == "user":
                st.markdown(
                    f"<div class='chat-bubble user'><b>あなた：</b><br>{html.escape(msg['content'])}</div>",
                    unsafe_allow_html=True,
                )
            elif msg["role"] == "assistant":
                st.markdown(
                    f"<div class='chat-bubble assistant'><b>{self.partner_name}：</b><br>{html.escape(msg['content'])}</div>",
                    unsafe_allow_html=True,
                )

    def render_input(self):
        """入力欄と送信ボタン"""
        hint_col, _ = st.columns([1, 3])
        if hint_col.button("ヒントを入力欄に挿入", disabled=st.session_state["_busy"]):
            st.session_state["user_input"] = self.starter_hint

        st.text_area(
            "あなたの言葉（複数行OK）",
            key="user_input",
            height=160,
            placeholder=self.starter_hint or "",
        )

        c_send, c_new, c_show = st.columns([1, 1, 1])

        if c_send.button("送信", type="primary", disabled=(st.session_state["_busy"] or st.session_state["_ask_reset"])):
            txt = st.session_state.get("user_input", "").strip()
            if txt:
                st.session_state["_pending_text"] = txt
                st.session_state["_do_send"] = True
                st.session_state["_clear_input"] = True
                st.rerun()

        if c_new.button("新しい会話", disabled=st.session_state["_busy"]):
            st.session_state["_do_reset"] = True
            st.rerun()

        if c_show.button("最近10件を表示", disabled=st.session_state["_busy"]):
            st.info("最近10件を下に表示します。")
            recent = [m for m in st.session_state["messages"] if m["role"] in ("user", "assistant")][-10:]
            for m in recent:
                role = "あなた" if m["role"] == "user" else self.partner_name
                st.write(f"**{role}**：{m['content'].strip()}")

        if st.session_state["_do_send"] and not st.session_state["_busy"]:
            st.session_state["_do_send"] = False
            st.session_state["_busy"] = True
            try:
                txt = st.session_state.get("_pending_text", "")
                st.session_state["_pending_text"] = ""
                if txt:
                    self.send_message(txt)
            finally:
                st.session_state["_busy"] = False
                st.rerun()

    # =========================
    # メッセージ処理
    # =========================
    def send_message(self, user_text: str):
        """ユーザー発話を処理してAIに送る"""
        # 履歴を制限
        if len(st.session_state["messages"]) > self.max_log:
            base = st.session_state["messages"][0]
            st.session_state["messages"] = [base] + st.session_state["messages"][-(self.max_log - 1):]

        # 発言を追加
        st.session_state["messages"].append({"role": "user", "content": user_text})
        convo = [st.session_state["messages"][0]] + st.session_state["messages"][-60:]

        with st.spinner(f"{self.partner_name}が考えています…"):
            reply, meta = call_with_fallback(
                convo,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

        st.session_state["_last_call_meta"] = meta
        reply = reply.strip() or "（返答の生成に失敗しました…）"
        st.session_state["messages"].append({"role": "assistant", "content": reply})

    # =========================
    # 実行エントリ
    # =========================
    def run(self):
        """UI構築＋処理ループ"""
        self.process_flags()
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
