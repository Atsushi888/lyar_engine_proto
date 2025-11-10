# deliberation/judge_ai.py

from __future__ import annotations
from typing import Any, Dict, Tuple

from llm_router import call_with_fallback
import json


class JudgeAI:
    """
    マルチAI応答の「評価システム」中核。

    ・llm_meta を受け取って、models から比較対象を取り出し
    ・LLM に審査させ、winner / score_diff / comment を生成
    ・結果を llm_meta["judge"] に突っ込む役目を担う
    """

    def __init__(self) -> None:
        # 将来「審判用モデル」を変えたくなったらここに設定を持たせる
        pass

    # === 外から呼ぶのは基本これだけ ===
    def run(self, llm_meta: Dict[str, Any]) -> Dict[str, Any] | None:
        """
        llm_meta を受け取り、judge結果を生成して
        llm_meta["judge"] に書き込む。

        2つ以上のモデル応答がなければ何もしない。
        戻り値は作成した judge dict（または None）
        """
        models: Dict[str, Any] = llm_meta.get("models") or {}
        if not isinstance(models, dict) or len(models) < 2:
            return None

        # TODO: 今は gpt4o vs hermes 固定。将来は柔軟に選べるようにしても良い。
        if "gpt4o" in models and "hermes" in models:
            a_key, b_key = "gpt4o", "hermes"
        else:
            # 手抜きで、最初の2つを比較する
            keys = list(models.keys())
            a_key, b_key = keys[0], keys[1]

        prompt = llm_meta.get("prompt_preview", "")
        reply_a = str(models[a_key].get("reply") or models[a_key].get("text") or "")
        reply_b = str(models[b_key].get("reply") or models[b_key].get("text") or "")

        judge = self._evaluate_pair(
            prompt=prompt,
            reply_a=reply_a,
            reply_b=reply_b,
            label_a=a_key,
            label_b=b_key,
        )

        llm_meta["judge"] = judge
        return judge

    # === 以下は内部専用：実際の判定ロジック ===
    def _evaluate_pair(
        self,
        prompt: str,
        reply_a: str,
        reply_b: str,
        label_a: str,
        label_b: str,
    ) -> Dict[str, Any]:
        """
        実際に LLM を使って A/B を比較し、
        winner / score_diff / comment を含む dict を返す。
        """

        system_prompt = (
            "あなたは物語文の審査員です。\n"
            "これから、同じプロンプトに対する二つの応答が与えられます。\n"
            "どちらの応答が、文体の自然さ・情景描写・感情表現・世界観整合性の点で"
            "より優れているかを判断してください。\n"
            "\n"
            "出力フォーマットは必ず次のJSON形式にしてください:\n"
            "{\n"
            '  \"winner\": \"A\" または \"B\",\n'
            '  \"score_diff\": 0.0〜1.0の数値,\n'
            '  \"comment\": \"日本語で、どちらを選んだ理由を1〜3文で説明\"\n'
            "}\n"
        )

        user_content = (
            "【プロンプト】\n"
            f"{prompt}\n\n"
            "【応答A】\n"
            f"{reply_a}\n\n"
            "【応答B】\n"
            f"{reply_b}\n\n"
            "上記を比較し、指定されたJSON形式のみを出力してください。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        text, meta = call_with_fallback(
            messages=messages,
            temperature=0.0,
            max_tokens=300,
        )

        result: Dict[str, Any] = {
            "winner": None,
            "score_diff": 0.0,
            "comment": "",
            "raw": text,
            "route": meta.get("route"),
            "pair": {"A": label_a, "B": label_b},
        }

        parsed = None
        try:
            stripped = text.strip()
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_str = stripped[start : end + 1]
                parsed = json.loads(json_str)
        except Exception:
            parsed = None

        if isinstance(parsed, dict):
            winner_raw = parsed.get("winner")
            if winner_raw == "A":
                result["winner"] = label_a
            elif winner_raw == "B":
                result["winner"] = label_b

            try:
                result["score_diff"] = float(parsed.get("score_diff", 0.0))
            except Exception:
                result["score_diff"] = 0.0

            comment = parsed.get("comment")
            if isinstance(comment, str):
                result["comment"] = comment.strip()

        # winner が取れなかった場合のフォールバック
        if result["winner"] is None:
            result["winner"] = label_a
            result["score_diff"] = 0.0
            if not result["comment"]:
                result["comment"] = "JSON解析に失敗したため暫定でAを選択しました。"

        return result
