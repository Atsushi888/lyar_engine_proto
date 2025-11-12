# auth/auth_manager.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import json
import streamlit as st
import streamlit_authenticator as stauth
from .roles import Role

@dataclass
class AuthResult:
    status: str          # "authenticated" | "unauthenticated" | "forgot" | ...
    username: str | None

class AuthManager:
    def __init__(self) -> None:
        # ---- secrets 取得（無ければデフォルト）----
        raw_credentials = st.secrets.get("credentials", {})
        raw_cookie = st.secrets.get("cookie", {})
        # Secrets は読み取り専用なので、ライブラリに渡す前に“ふつうの dict”へ深いコピー
        # json -> dict で Secrets を完全に剥がす（deepcopy 代わり）
        self._credentials = json.loads(json.dumps(raw_credentials))
        cookie_name = raw_cookie.get("name", "lyra_auth")
        cookie_key  = raw_cookie.get("key", "change_me")
        cookie_expiry_days = int(raw_cookie.get("expiry_days", 30))

        # streamlit_authenticator 本体
        self.authenticator = stauth.Authenticate(
            credentials=self._credentials,   # ← mutable dict を渡す！
            cookie_name=cookie_name,
            key=cookie_key,
            cookie_expiry_days=cookie_expiry_days,
        )

    # ログインフォーム表示
    def render_login(self) -> AuthResult:
        form_name = "Lyra System ログイン"
        # location は 'main' か 'sidebar' か 'unrendered'
        name, auth_status, username = self.authenticator.login(form_name, location="main")
        # 認証結果をセッションにも反映（任意）
        st.session_state["auth_status"] = auth_status
        st.session_state["auth_user"] = username
        return AuthResult(status=auth_status or "unauthenticated", username=username)

    # 現在のロールを返す
    def role(self) -> Role:
        # secrets 側のロール定義を参照（ログインしてから取得）
        if st.session_state.get("auth_status") != True:
            return Role.GUEST
        uname = st.session_state.get("auth_user")
        try:
            user_info = self._credentials["usernames"][uname]
            role_name = (user_info.get("role") or "USER").upper()
        except Exception:
            role_name = "USER"
        if role_name == "ADMIN":
            return Role.ADMIN
        if role_name in ("DEV", "DEVELOPER"):
            return Role.DEV
        return Role.USER

    def logout_button(self) -> None:
        self.authenticator.logout("Logout", location="sidebar")
