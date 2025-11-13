# council/council_manager.py

from __future__ import annotations
from typing import Any, Dict, List

import streamlit as st
from personas.persona_floria_ja import get_persona


class CouncilManager:
    """
    会談システムの中核クラス。
    ・状態管理（session_state）
    ・UI描画（render）
    をすべてここに集約する。
    """

    SESSION_PREFIX = "council_"

    def __init__(self, state: Dict[str, Any]) -> None:
        self.state = state
        self.persona = get_persona()
        self._ensure_state()

    # ===== 内部：状態初期化 =====
    def _ensure_state(self) -> None:
        s = self.state
        s.setdefault(self.SESSION_PREFIX + "log", [])          # List[Dict[str,str]]
        s.setdefault(self.SESSION_PREFIX + "round", 0)         # int
        s.setdefault(self.SESSION_PREFIX + "mode", "idle")     # "idle" / "running" / "finished"
        s.setdefault(self.SESSION_PREFIX + "speaker", "player")  # "player" / "floria" / "system"

    # ===== プロパティ =====
    @property
    def log(self) -> List[Dict[str, str]]:
        return self.state[self.SESSION_PREFIX + "log"]

    @property
    def round(self) -> int:
        return int(self.state[self.SESSION_PREFIX + "round"])

    @property
    def mode(self) -> str:
        return str(self.state[self.SESSION_PREFIX + "mode"])

    @property
    def speaker(self) -> str:
        return str(self.state[self.SESSION_PREFIX + "speaker"])

    # ===== 状態操作メソッド =====
    def reset(self) -> None:
        """会談をリセットして導入テキストをセット。"""
        self.state[self.SESSION_PREFIX + "log"] = []
        self.state[self.SESSION_PREFIX + "round"] = 0
        self.state[self.SESSION_PREFIX + "mode"] = "running"
        self.state[self.SESSION_PREFIX + "speaker"] = "system"

        intro = (
            "君は今、ある田舎町の近くにいる。人通りは多くないが、"
            "どこか張り詰めた気配が漂っている。"
        )
        self.append_entry("system", intro)

        # 次はプレイヤーのターン
        self.state[self.SESSION_PREFIX + "speaker"] = "player"

    def append_entry(self, speaker: str, text: str) -> None:
        self.log.append(
            {
                "speaker": speaker,
                "text": text,
            }
        )

    def can_player_speak(self) -> bool:
        return (self.mode == "running") and (self.speaker == "player")

    def handle_player_utterance(self, text: str) -> None:
        """
        プレイヤーの発言処理。
        今はモックとしてフローリア固定応答を返す。
        後で LLM / Referee / Fortuna をここに差し込む。
        """
        text = text.strip()
        if not text:
            return

        # プレイヤー発言
        self.append_entry("player", text)
        self.state[self.SESSION_PREFIX + "round"] += 1

        # フローリアの仮応答
        mock_reply = (
            "……ううん、その言い方、ずるいよ。"
            "でも、そうやって悩んでくれるのは、ちょっと嬉しい。"
        )
        self.append_entry("floria", mock_reply)

        # ひとまずまたプレイヤーのターン（後でターン制ロジックを洗練）
        self.state[self.SESSION_PREFIX + "speaker"] = "player"

    # ===== メイン描画 =====
    def render(self) -> None:
        """
        会談システムの UI をまとめて描画。
        View 側は manager.render() を呼ぶだけ。
        """
        st.title("🗣 会談システム（Council Prototype）")
        st.caption("※ ロジックとUIはCouncilManagerに集約。ここから拡張していく。")

        col_top_left, col_top_right = st.columns([2, 1])

        # ---- 右上：コントロール ----
        with col_top_right:
            if st.button("🔁 会談リセット / 開始", use_container_width=True):
                self.reset()
                st.rerun()

            st.markdown("---")
            st.write(f"ラウンド: {self.round}")
            st.write(f"話者: {self.speaker}")
            st.write(f"モード: {self.mode}")

        # ---- 左上：ログ表示 ----
        with col_top_left:
            st.subheader("会談ログ")

            if not self.log:
                st.caption("（まだ会談が始まっていません。「会談リセット / 開始」でスタート）")
            else:
                for entry in self.log:
                    speaker = entry.get("speaker", "system")
                    text = entry.get("text", "")

                    if speaker == "player":
                        css = "background-color:#e8f2ff;border-left:4px solid #66aaff;"
                        label = "あなた"
                    elif speaker == "floria":
                        css = "background-color:#f9f0ff;border-left:4px solid #cc66ff;"
                        label = self.persona.name
                    else:
                        css = "background-color:#f2f2f2;border-left:4px solid #999999;"
                        label = "（システム）"

                    st.markdown(
                        f"""
<div style="
    margin:6px 0;
    padding:6px 10px;
    border-radius:6px;
    {css}
">
  <div style="font-size:0.8rem;color:#555;">{label}</div>
  <div>{text}</div>
</div>
""",
                        unsafe_allow_html=True,
                    )

        # ---- 下部：プレイヤー入力 ----
        st.markdown("---")
        st.subheader("プレイヤー入力")

        if not self.can_player_speak():
            st.caption("（今はプレイヤーのターンではありません。会談を開始してから話してね）")
            return

        user_text = st.text_area(
            "あなたの発言",
            key=self.SESSION_PREFIX + "input",
            placeholder="封印のこと、フローリアの気持ち、自分の覚悟……何を話す？",
        )

        if st.button("▶ この内容で発言する", use_container_width=True):
            if not user_text.strip():
                st.warning("何か話してあげて。")
                return

            self.handle_player_utterance(user_text)
            # 入力欄クリア
            self.state[self.SESSION_PREFIX + "input"] = ""
            st.rerun()
