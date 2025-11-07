# player_input.py

from typing import Optional
import streamlit as st


class PlayerInput:
    # テキストのセッションキー
    TEXT_KEY = "player_input_text"
    # 「次のターンで入力欄までスクロールしてね」フラグ
    SCROLL_FLAG_KEY = "scroll_to_input"

    def __init__(self, label: str = "あなたの発言を入力:") -> None:
        self.label = label

    def render(self) -> Optional[str]:
        # 入力欄の位置マーカー（ここまでスクロールさせる）
        st.markdown(
            '<div id="player-input-anchor"></div>',
            unsafe_allow_html=True,
        )

        # 初期値が無ければ空文字で作っておく
        if self.TEXT_KEY not in st.session_state:
            st.session_state[self.TEXT_KEY] = ""

        st.markdown(f"### {self.label}")

        text = st.text_area(
            "",
            key=self.TEXT_KEY,
            height=160,
            placeholder="フローリアに語りかけてください…",
        )

        # ▼ フラグが立っていたら一度だけスクロールを実行
        if st.session_state.get(self.SCROLL_FLAG_KEY):
            st.markdown(
                """
<script>
const anchor = document.getElementById("player-input-anchor");
if (anchor) {
    anchor.scrollIntoView({behavior: "smooth", block: "center"});
}
</script>
""",
                unsafe_allow_html=True,
            )
            # 一回スクロールしたらフラグを戻す
            st.session_state[self.SCROLL_FLAG_KEY] = False

        send = st.button("送信", type="primary")

        if send and text.strip():
            user_text = text.strip()
            # 入力欄をクリア
            st.session_state[self.TEXT_KEY] = ""
            return user_text

        return None
