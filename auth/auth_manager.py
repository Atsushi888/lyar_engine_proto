# auth/auth_manager.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Tuple
import json
import streamlit as st
import streamlit_authenticator as stauth

@dataclass
class AuthResult:
    status: Any
    username: str | None

class AuthManager:
    def __init__(self) -> None:
        # secrets から credentials を辞書で取得（.toml → dict）
        raw_creds = st.secrets.get("credentials")
        if not isinstance(raw_creds, dict):
            # toml 全体を JSON 経由で dict 化（型ブレ対策）
            raw_creds = json.loads(json.dumps(st.secrets["credentials"]))
        cookie = st.secrets.get("cookie", {})
        self.cookie_name = cookie.get("name", "lyra_auth")
        self.cookie_key  = cookie.get("key",  "some_random_secret_key")
        self.cookie_expiry = int(cookie.get("expiry_days", 30))

        # streamlit-authenticator 0.4系/0.3系 互換
        self.authenticator = stauth.Authenticate(
            raw_creds,
            self.cookie_name,
            self.cookie_key,
            self.cookie_expiry,
        )

    # --- 互換ログイン: location と 戻り値 どちらも吸収 ---
    def render_login(self, *, form_name: str = "Lyra System ログイン",
                     location: str = "main") -> AuthResult:
        if location not in ("main", "sidebar", "unrendered"):
            location = "main"

        try:
            ret = self.authenticator.login(form_name, location=location)
        except TypeError:
            # 古い版で location を受けない
            ret = self.authenticator.login(form_name)

        name = username = None
        auth_status = None

        if isinstance(ret, tuple):
            # 典型: (name, authentication_status, username)
            if len(ret) == 3:
                name, auth_status, username = ret
            elif len(ret) == 2:
                auth_status, username = ret
        else:
            auth_status = getattr(ret, "authentication_status", None)
            username    = getattr(ret, "username", None)
            name        = getattr(ret, "name", None)

        st.session_state["auth_status"] = auth_status
        st.session_state["auth_user"] = username
        return AuthResult(status=auth_status or "unauthenticated", username=username)

    def role(self) -> int:
        # ロールは secrets の credentials.usernames.<id>.role を読む想定
        username = st.session_state.get("auth_user")
        creds = st.secrets.get("credentials", {}).get("usernames", {})
        role_map = {"ADMIN": 2, "USER": 1, "DEV": 2}
        if isinstance(creds, dict) and username in creds:
            role = creds[username].get("role", "USER")
            return role_map.get(str(role).upper(), 1)
        return 0  # 未ログイン
