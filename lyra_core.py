# lyra_core.py — Lyra Engine の会話制御コア
#
# 役割：
#   ・Streamlit の state から messages を取り出す
#   ・ユーザー発言を履歴に追加
#   ・LLMConversation に投げて応答と meta をもらう
#   ・アシスタント発言を履歴に追加して返す
#
#   ★ マルチAIまわりの構造は全部 LLMConversation 側に任せる。
#     ここでは llm_meta を一切ラップしない。

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from conversation_engine import LLMConversation


class LyraCore:
    def __init__(self, conversation: LLMConversation) -> None:
        self.conversation = conversation

    def proceed_turn(
        self,
        user_text: str,
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
        """
        1ターン分の会話を進める。

        入力:
          user_text : ユーザーの最新発言（テキスト）
          state     : st.session_state をそのまま渡してくる想定

        戻り値:
          updated_messages : 更新後の messages リスト
          llm_meta         : LLM 側メタ情報（LLMConversation から返ってきたものをそのまま）
        """
        # これまでの履歴を取得（なければ空で初期化）
        messages: List[Dict[str, str]] = state.get("messages", [])
        # コピーを作って操作しておくと安心
        messages = list(messages)

        # ユーザー発言を履歴に追加
        messages.append({"role": "user", "content": user_text})

        # LLMConversation に丸投げして、応答と meta を受け取る
        reply_text, meta = self.conversation.generate_reply(messages)

        # アシスタント発言を履歴に追加
        messages.append({"role": "assistant", "content": reply_text})

        # ここがポイント：
        #   以前のように
        #   llm_meta = {"gpt4o": {"reply": ..., "meta": meta}, ...}
        #   というラップは一切しない。
        #
        #   generate_reply() が返した meta を、そのまま llm_meta として返す。
        llm_meta: Dict[str, Any] = dict(meta)

        return messages, llm_meta
