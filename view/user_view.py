# views/user_view.py
from __future__ import annotations
import streamlit as st

class UserView:
    def render(self) -> None:
        st.caption("公開向けの軽量設定のみを表示")
        col1, col2 = st.columns(2)
        with col1:
            st.toggle("字幕を表示", key="ui_show_subtitle", value=st.session_state.get("ui_show_subtitle", True))
        with col2:
            st.toggle("効果音を有効にする", key="ui_sfx", value=st.session_state.get("ui_sfx", True))
