# auth/auth_manager.py

from importlib.metadata import version as _pkg_version

def _stauth_major_minor() -> tuple[int, int]:
    try:
        v = _pkg_version("streamlit-authenticator").split(".")
        return int(v[0]), int(v[1])
    except Exception:
        return (0, 0)

class AuthManager:
    # ...（__init__ はそのまま）...

    def render_login(self, location: str = "main"):
        allowed = ("main", "sidebar", "unrendered")
        loc = (location or "main").strip().lower()
        if loc not in allowed:
            loc = "main"

        form_name = "Lyra System ログイン"
        ver = _stauth_major_minor()

        try:
            # v0.3 以降は「第2引数=location」の位置引数が安定
            if ver >= (0, 3):
                name, auth_status, username = self.authenticator.login(form_name, loc)
            else:
                # 旧版はキーワードの方が安定
                name, auth_status, username = self.authenticator.login(form_name, location=loc)
        except Exception:
            # 最終フォールバック：強制 main で両パターンを順に試す
            try:
                if ver >= (0, 3):
                    name, auth_status, username = self.authenticator.login(form_name, "main")
                else:
                    name, auth_status, username = self.authenticator.login(form_name, location="main")
            except Exception as _:
                # それでも失敗したら明示エラー
                import streamlit as st
                st.error("ログインフォームの描画に失敗しました。streamlit-authenticator のバージョン互換を確認してください。")
                raise

        return type("AuthResult", (), {
            "name": name,
            "status": auth_status,
            "username": username,
        })
