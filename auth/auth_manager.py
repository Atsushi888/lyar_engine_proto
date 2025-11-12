# auth/auth_manager.py
from __future__ import annotations
import traceback
import streamlit as st

try:
    import streamlit_authenticator as stauth
    AUTH_AVAILABLE = True
except Exception:
    AUTH_AVAILABLE = False

# 任意のロール数値（必要に応じて調整）
ROLE_MAP = {"ADMIN": 9, "DEV": 7, "USER": 5, "VIEWER": 1}

def _get_role_from_secrets(username: str) -> int:
    try:
        creds = st.secrets["credentials"]
        users = creds.get("usernames") or {}
        role = (users.get(username, {}) or {}).get("role", "USER")
        return ROLE_MAP.get(str(role).upper(), ROLE_MAP["USER"])
    except Exception:
        return ROLE_MAP["ADMIN"]  # フォールバック（あとでUSERに下げてもOK）

class AuthManager:
    """Secrets/Authenticatorが無くても絶対に落ちないログイン管理。"""

    def __init__(self) -> None:
        self._auth_ok = False
        self._username: str | None = None
        self._role: int = ROLE_MAP["ADMIN"]  # フォールバックの初期値
        self._error: str | None = None

        # ここでは何もしない（遅延初期化）
        # 画面描画時に初期化＆フォールバック判定を行う

    # ---- 公開API ---------------------------------------------------------
    def role(self) -> int:
        return self._role

    def username(self) -> str | None:
        return self._username

    def render_login(self, location: str = "main") -> None:
        """タイトル＋必要ならフォームを描画。例外時はフォールバックして継続。"""
        st.title("🔐 Lyra System ログイン")
        st.caption("※ 現在ログインシステムは段階的に復帰中です。")

        # すでに認証済なら何もしない
        if st.session_state.get("_lyra_auth_ok"):
            self._auth_ok = True
            self._username = st.session_state.get("_lyra_username")
            self._role = st.session_state.get("_lyra_role", ROLE_MAP["USER"])
            return

        try:
            # 認証器の用意を試みる
            if AUTH_AVAILABLE and "credentials" in st.secrets:
                creds = st.secrets["credentials"]
                cookie = st.secrets.get("cookie", {})
                auth = stauth.Authenticate(
                    credentials=creds,          # ここは dict をそのまま渡せばOK
                    cookie_name=cookie.get("name", "lyra_auth"),
                    key=cookie.get("key", "lyra_secret"),
                    cookie_expiry_days=int(cookie.get("expiry_days", 30)),
                    auto_hash=False,            # ハッシュは事前生成（Hashed値）
                )
                # フォーム描画（location: 'main' or 'sidebar'）
                name, auth_status, username = auth.login("Lyra System ログイン", location)
                if auth_status:
                    self._auth_ok = True
                    self._username = username
                    self._role = _get_role_from_secrets(username or "")
                    st.session_state["_lyra_auth_ok"] = True
                    st.session_state["_lyra_username"] = self._username
                    st.session_state["_lyra_role"] = self._role
                    st.success(f"ようこそ、{name} さん")
                elif auth_status is False:
                    st.error("認証に失敗しました。ユーザー名/パスワードをご確認ください。")
                else:
                    st.info("ユーザー名とパスワードを入力してください。")
            else:
                # Secrets なし／パッケージなし → フォールバック
                st.warning("Credentials 未設定のため、簡易モードで継続します。")
                self._auth_ok = True
                self._username = "guest"
                self._role = ROLE_MAP["ADMIN"]  # とりあえず通す（後でUSERに変更可）
                st.session_state["_lyra_auth_ok"] = True
                st.session_state["_lyra_username"] = self._username
                st.session_state["_lyra_role"] = self._role

        except Exception as e:
            self._error = f"{type(e).__name__}: {e}"
            st.caption("⚠ ログインフォームの標準描画に失敗。フォールバックに切替えます。")
            with st.expander("詳細（デバッグ）", expanded=False):
                st.code("".join(traceback.format_exc()), language="text")

            # フォールバックで通す（開発優先）
            self._auth_ok = True
            self._username = "guest"
            self._role = ROLE_MAP["ADMIN"]
            st.session_state["_lyra_auth_ok"] = True
            st.session_state["_lyra_username"] = self._username
            st.session_state["_lyra_role"] = self._role
