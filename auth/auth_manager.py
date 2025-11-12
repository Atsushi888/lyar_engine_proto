import streamlit as st

class AuthManager:
    """タイトル表示だけ残した最小稼働版"""

    def __init__(self) -> None:
        pass

    def render_login(self, location: str = "main") -> None:
        """タイトルだけを描画する。フォームは一切出さない。"""
        st.title("🔐 Lyra System ログイン")
        st.caption("※ 現在ログインシステムは調整中です。")

    def role(self) -> int:
        """暫定的に全員ADMIN扱い"""
        return 9
