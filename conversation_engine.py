# conversation_engine.py
from typing import Any, Dict, List, Tuple
from llm_router import call_with_fallback


class LLMConversation:
    def __init__(
        self,
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> None:
        self.system_prompt = system_prompt
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)

        self.style_hint = (
            "ユーザーは日本語で物語の本文（地の文と会話文）だけを送ります。\n"
            "あなたはフローリアという女性キャラクターとして、その物語世界の中に存在しています。\n"
            "直前のユーザーの文章をよく読み、その続きとして自然につながる内容を書いてください。\n"
            "・ユーザーの最後の文を繰り返さないこと。\n"
            "・地の文と、必要ならフローリアや他の登場人物の台詞を混ぜても構いません。\n"
            "・長さは日本語で2〜4文程度にしてください。\n"
            "・舞台指示や 'onstage:' 'onscreen:' などの英語のタグは絶対に使わないこと。"
        )

    def build_messages(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        system_content = self.system_prompt
        if self.style_hint:
            system_content += "\n\n" + self.style_hint

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_content}
        ]

        # ここは「直近 user だけ使う」か「履歴全部送る」か、好きな方でOK
        # 今は例として history 全部を投げる版：
        messages.extend(history)
        return messages

    def generate_reply(
        self,
        history: List[Dict[str, str]],
    ) -> Tuple[str, Dict[str, Any]]:
        # 🔴 ここで実際に LLM に渡す messages を作る
        messages = self.build_messages(history)

        # LLM 呼び出し
        text, meta = call_with_fallback(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        # 🔴 デバッグ用に、「何を投げたか」を meta に埋め込む
        meta = dict(meta)  # 念のためコピー
        meta["prompt_messages"] = messages  # 生 messages
        # 人間が読みやすいテキスト版も
        meta["prompt_preview"] = "\n\n".join(
            f"[{m['role']}] {m['content'][:200]}"
            for m in messages
        )

        return text, meta
