# components/player_input.py
import streamlit as st


class PlayerInput:
    """ユーザーの入力欄 + 送信ボタンを担当"""

    def __init__(
        self,
        key_input: str = "user_input_box",
        key_button: str = "send_button",
    ) -> None:
        self.key_input = key_input
        self.key_button = key_button

    def render(self) -> str:
        """入力欄を表示して、送信されたテキストを返す（なければ空文字）"""

        # テキストエリア（高さはお好みで調整してね）
        user_input = st.text_area(
            "あなたの発言を入力:",
            key=self.key_input,
            height=160,
        )

        # 送信ボタン
        send_clicked = st.button("送信", key=self.key_button)

        if send_clicked:
            text = user_input.strip()

            # ★ここがポイント：送信後に入力欄をクリア
            st.session_state[self.key_input] = ""

            # 空じゃなければ返す（LyraEngine 側で LLM 呼び出し）
            if text:
                return text

        # 送信されていない / 空文字のときは何も返さない
        return ""
