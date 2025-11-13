# auth/auth_manager.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import streamlit as st
import bcrypt

from auth.roles import Role

# あるなら使う（無ければ None のまま）
try:
    import streamlit_authenticator as stauth
except Exception:  # ライブラリ未導入 / 壊れている場合も想定
    stauth = None


@dataclass
class AuthResult:
    name: Optional[str]
    status: Optional[bool]
    username: Optional[str]


class AuthManager:
    """
    認証まわりの一本化クラス。

    ・基本は streamlit-authenticator を使う
    ・ダメなら自前フォームでフォールバック
    ・auth.bypass = true なら無条件で ADMIN 扱い（開発用）
    """

    def __init__(self) -> None:
        self._secrets = st.secrets

        raw_creds = self._secrets.get("credentials", {})
        raw_cookie = self._secrets.get("cookie", {})
        raw_auth = self._secrets.get("auth", {})
        raw_preauth = self._secrets.get("preauthorized", [])

        self._creds: Dict[str, Any] = (
            dict(raw_creds) if isinstance(raw_creds, dict) else {}
        )
        self._cookie: Dict[str, Any] = (
            dict(raw_cookie) if isinstance(raw_cookie, dict) else {}
        )
        self._auth_cfg: Dict[str, Any] = (
            dict(raw_auth) if isinstance(raw_auth, dict) else {}
        )
        self._preauth = raw_preauth if isinstance(raw_preauth, list) else []

        # 開発用バイパス（auth.bypass = true なら常に ADMIN）
        self._bypass: bool = bool(self._auth_cfg.get("bypass", False))

        # streamlit-authenticator が使えればインスタンス化
        self.authenticator = None
        if stauth is not None and self._creds:
            try:
                # Authenticate(credentials, cookie_name, key, cookie_expiry_days, preauthorized)
                self.authenticator = stauth.Authenticate(
                    self._creds,
                    self._cookie.get("name", "lyra_auth"),
                    self._cookie.get("key", "lyra_secret"),
                    float(self._cookie.get("expiry_days", 30)),
                    self._preauth,
                )
            except Exception:
                # ここで死なないようにする
                self.authenticator = None

    # ---------- 公開 API ----------

    def render_login(self, location: str = "main") -> AuthResult:
        """
        ログインフォームを描画し、AuthResult を返す。
        LyraSystem 側では戻り値を使わなくてもよい（role() で見る）。
        """
        # 開発用バイパス
        if self._bypass:
            username = self._first_username() or "admin"
            st.session_state["authentication_status"] = True
            st.session_state["name"] = "Bypass Admin"
            st.session_state["username"] = username
            return AuthResult("Bypass Admin", True, username)

        # streamlit-authenticator が使える場合
        if self.authenticator is not None:
            try:
                loc = location if location in ("main", "sidebar", "unrendered") else "main"

                # v0.3.3 以降の仕様：第一引数は location
                result = self.authenticator.login(loc)
                # result は (name, auth_status, username) または None
                if result is None:
                    return AuthResult(None, None, None)
                name, auth_status, username = result
                return AuthResult(name, auth_status, username)
            except Exception as e:
                st.warning(
                    "ログインフォーム（streamlit-authenticator）の描画に失敗しました。\n"
                    "簡易フォームにフォールバックします。\n\n"
                    f"Reason: {type(e).__name__}"
                )

        # ここまで来たら自前フォームで認証
        return self._fallback_login()

    def role(self) -> Role:
        """
        現在のセッションの権限を返す。
        LyraSystem はこれを見て表示可否を制御する。
        """
        # 開発用バイパス
        if self._bypass:
            return Role.ADMIN

        # 認証されてなければ ANON
        if not st.session_state.get("authentication_status"):
            return Role.ANON

        uname = st.session_state.get("username")
        if not uname:
            return Role.USER

        user_tbl: Dict[str, Any] = self._creds.get("usernames", {})
        meta = user_tbl.get(uname, {})
        r = str(meta.get("role", "USER")).upper()

        if r == "ADMIN":
            return Role.ADMIN
        return Role.USER

    def logout(self, location: str = "sidebar") -> None:
        """
        ログアウト処理。  
        streamlit-authenticator があればそれを使い、
        だめなら session_state を直接消す。
        """
        if self.authenticator is not None:
            try:
                loc = location if location in ("main", "sidebar", "unrendered") else "sidebar"
                self.authenticator.logout("Logout", loc)
                return
            except Exception:
                # 失敗しても下の手動ログアウトでフォロー
                pass

        for k in ("authentication_status", "name", "username"):
            st.session_state.pop(k, None)
        st.success("Logged out.")

    # ---------- 内部：フォールバック実装 ----------

    def _fallback_login(self) -> AuthResult:
        st.info("フォールバック・ログイン（簡易管理用 UI）")

        with st.form("fallback_login", clear_on_submit=False):
            uname = st.text_input("Username / ID")
            pwd = st.text_input("Password", type="password")
            ok = st.form_submit_button("Login")

        name: Optional[str] = None
        status: Optional[bool] = None

        if ok:
            user_tbl: Dict[str, Any] = self._creds.get("usernames", {})
            meta = user_tbl.get(uname)
            if not meta:
                st.error("ユーザーが見つかりません。")
                status = False
            else:
                hashed = str(meta.get("password", ""))
                if self._check_bcrypt(pwd, hashed):
                    st.session_state["authentication_status"] = True
                    st.session_state["name"] = meta.get("name") or uname
                    st.session_state["username"] = uname
                    name = st.session_state["name"]
                    status = True
                    st.success("Login success.")
                else:
                    st.error("パスワードが違います。")
                    status = False

        return AuthResult(name, status, st.session_state.get("username"))

    @staticmethod
    def _check_bcrypt(plain: str, hashed: str) -> bool:
        """
        bcrypt でハッシュされたパスワードと照合する。
        secrets には bcrypt 済みの文字列を置く前提。
        """
        try:
            if not plain or not hashed:
                return False
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    def _first_username(self) -> Optional[str]:
        """
        credentials.usernames の先頭キーを返す（bypass 用）。
        """
        user_tbl: Dict[str, Any] = self._creds.get("usernames", {})
        if not isinstance(user_tbl, dict) or not user_tbl:
            return None
        return list(user_tbl.keys())[0]
