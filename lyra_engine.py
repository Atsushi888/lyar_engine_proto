class LyraEngine:
    MAX_LOG = 500
    DISPLAY_LIMIT = 20000

    def __init__(self):
        persona = get_persona("floria_ja")
        self.system_prompt = persona.system_prompt
        self.starter_hint = persona.starter_hint
        self.partner_name = persona.name

        # キー
        self.openai_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        self.openrouter_key = st.secrets.get("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))

        if not self.openai_key:
            st.error("OPENAI_API_KEY が未設定です。Streamlit → Settings → Secrets で設定してください。")
            st.stop()

        os.environ["OPENAI_API_KEY"] = self.openai_key
        if self.openrouter_key:
            os.environ["OPENROUTER_API_KEY"] = self.openrouter_key

        # ★ UI コンポーネントをここで組み立て
        self.preflight = PreflightChecker(self.openai_key, self.openrouter_key)
        self.debug_panel = DebugPanel()
        self.chat_log = ChatLog(self.partner_name, self.DISPLAY_LIMIT)

        self._init_session_state()

    @property
    def state(self):
        return st.session_state

    # ▼▼▼ ここから新規追記 ▼▼▼
    def render(self):
        """ページ全体の描画をまとめて行う"""

        # Preflight（APIキーなどのチェック）
        st.write("🛫 PreflightChecker.render() 呼び出し前")
        self.preflight.render()
        st.write("🛬 PreflightChecker.render() 呼び出し後")

        # DebugPanel はサイドバーに出しておく
        with st.sidebar:
            self.debug_panel.render()

        # メインエリアにチャット本体
        self.chat_log.render()
    # ▲▲▲ 新規追記ここまで ▲▲▲
