# auth/auth_manager.py
from __future__ import annotations
import streamlit as st
import streamlit_authenticator as stauth
from copy import deepcopy

class AuthManager:
    def __init__(self) -> None:
        def _to_dict(sec):
            if hasattr(sec, "to_dict"):
                return sec.to_dict()
            return {k: (v.to_dict() if hasattr(v, "to_dict") else deepcopy(v))
                    for k, v in sec.items()}

        credentials = _to_dict(st.secrets["credentials"])
        cookie = _to_dict(st.secrets.get("cookie", {}))

        self.authenticator = stauth.Authenticate(
            credentials=credentials,
            cookie_name=cookie.get("name", "lyra_auth"),
            key=cookie.get("key", "change_me"),
            cookie_expiry_days=int(cookie.get("expiry_days", 30)),
        )

    def role(self):
        if st.session_state.get("authentication_status"):
            return st.secrets["credentials"]["usernames"] \
                .get(st.session_state.get("username", ""), {}) \
                .get("role", "USER")
        return "GUEST"

    def render_login(self) -> None:
        # まず新API（0.4.x 以降想定）で試す
        try:
            name, auth_status, username = self.authenticator.login(
                location="main",           # 必須
                key="lyra_auth_login",     # 任意
                fields={"Form name": "Lyra System ログイン"}  # 任意
            )
        except TypeError:
            # 旧API（0.3.x 以前）：login(form_name, location)
            name, auth_status, username = self.authenticator.login(
                "Lyra System ログイン", "main"
            )

        # 状態の保持
        st.session_state["authentication_status"] = auth_status
        st.session_state["name"] = name
        st.session_state["username"] = username

        if auth_status:
            st.success(f"Logged in: {name}")
        elif auth_status is False:
            st.error("メール / パスワードが違います。")
        else:
            st.info("メール / パスワードを入力してください。")
