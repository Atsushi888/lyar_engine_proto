# auth/auth_manager.py
from __future__ import annotations
import streamlit as st
import streamlit_authenticator as stauth
from copy import deepcopy

from .roles import Role

class AuthManager:
    def __init__(self) -> None:
        # --- secrets -> plain dict に変換（読み取り専用オブジェクトを避ける）
        def _to_dict(sec):
            if hasattr(sec, "to_dict"):
                return sec.to_dict()
            # SecretsはMappingなのでこれでもOK
            return {k: (v.to_dict() if hasattr(v, "to_dict") else deepcopy(v))
                    for k, v in sec.items()}

        # [credentials]（usernames配下を含む）と [cookie] を辞書化
        creds_sec  = st.secrets["credentials"]
        cookie_sec = st.secrets.get("cookie", {})

        credentials = _to_dict(creds_sec)
        cookie      = _to_dict(cookie_sec)

        # 念のため存在チェック
        if "usernames" not in credentials:
            raise RuntimeError("secrets の [credentials.usernames] が見つかりません。")

        self.authenticator = stauth.Authenticate(
            credentials=credentials,             # ← ここが“普通のdict”になった
            cookie_name=cookie.get("name", "lyra_auth"),
            key=cookie.get("key", "change_me"),
            cookie_expiry_days=int(cookie.get("expiry_days", 30)),
        )

    def role(self) -> Role:
        return Role.ADMIN if st.session_state.get("role") == "ADMIN" else (
               Role.USER  if st.session_state.get("authentication_status") else Role.GUEST)

    def render_login(self) -> None:
        name, auth_status, username = self.authenticator.login("Lyra System ログイン", "main")
        if auth_status:
            # 認証OK。ロールをセッションに
            usernames = st.secrets["credentials"]["usernames"]
            # usernames は Secrets なので読み取りのみ：値だけ参照
            role = usernames[username]["role"]
            st.session_state["role"] = role
            st.success(f"ログイン：{name}（{role}）")
        elif auth_status is False:
            st.error("メール / パスワードが違います。")
        else:
            st.info("メール / パスワードを入力してください。")
