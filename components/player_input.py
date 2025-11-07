# components/player_input.py

from typing import Optional
import streamlit as st


class PlayerInput:
    def __init__(self) -> None:
        # ここでは何もしない
        pass

    def render(self) -> str:
        """
        入力欄と「送信」ボタンを描画し、
        送信されたときだけテキストを返す。
        送信されていなければ "" を返す。
        """

        st.write("あなたの発言を入力:")

        # ★ key を付けない＆ value="" にしておく
        #    → rerun のたびに毎回まっさらな入力欄になる
        user_text: str = st.text_area(
            label="",
            height=160,
            value="",      # 常に空からスタート
        )

        send = st.button("送信", type="primary")

        if send:
            text_to_send = (user_text or "").strip()
            if not text_to_send:
                return ""
            return text_to_send

        return ""
