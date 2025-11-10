# judge_ai.py — マルチAI審議用ジャッジクラス

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import json

from llm_router import call_with_fallback


class JudgeAI:
    """
    複数モデルの応答を比較して「どちらがより良いか」を判定するクラス。

    責務:
        - llm_meta["models"] から比較対象モデルを選ぶ
        - LLM に評価を依頼する
        - winner / score_diff / comment を含む dict を返す
        - 必要であれば llm_meta["judge"] に結果を書き込む

    UI（Streamlit 等）には一切依存しません。
    """

    def __init__(self) -> None:
        # 将来的に「審判専用モデル」を切り替えたくなった場合、
        # ここに設定を増やす余地を残しておきます。
        pass

    def run(self, llm_meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        llm_meta を受け取り、models から 2 つを選んで審議を行います。

        - models が 2 つ未満の場合は None を返します
        - 成功時は judge dict を返し、llm_meta["judge"] にも同じものを格納します
        """
        if not isinstance(llm_meta, dict):
            return None

        models = llm_meta.get("models")
        if not isinstance(models, dict) or len(models) < 2:
            return None

        a_key, b_key = self._choose_pair(models)

        prompt = llm_meta.get("prompt_preview") or ""
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

    def _choose_pair(self, models: Dict[str, Any]) -> Tuple[str, str]:
        """
        比較対象とする 2 モデルのキーを選びます。

        優先順位:
            1. "gpt4o" と "hermes" の組み合わせが両方あれば固定でそれを使う
            2. そうでなければ models の先頭 2 件
        """
        if "gpt4o" in models and "hermes" in models:
            return "gpt4o", "hermes"

        keys = list(models.keys())
        if len(keys) >= 2:
            return keys[0], keys[1]

        # ここに来るのは len(models) < 2 のときだけですが、
        # 型安全のため一応同じキーを返しておきます。
        return keys[0], keys[0]

    def _evaluate_pair(
        self,
        prompt: str,
        reply_a: str,
        reply_b: str,
        label_a: str,
        label_b: str,
    ) -> Dict[str, Any]:
        """
        実際に LLM に A/B 比較を依頼し、判定結果を dict で返します。

        戻り値の例:
            {
                "winner": "gpt4o",
                "score_diff": 0.6,
                "comment": "...",
                "raw_json": {...}  # 解析済みJSON
                "raw_text": "...",  # LLMの生テキスト
                "raw": {... または 文字列 ...}  # 後方互換用
                "route": "gpt",
                "pair": {"A": "gpt4o", "B": "hermes"},
            }
        """
        system_prompt = (
            "あなたは物語文の審査員です。\n"
            "同じプロンプトに対する 2 つの応答 A / B を比較し、"
            "どちらがより優れているかを判定してください。\n"
            "評価軸の例:\n"
            "  - 文体の自然さ\n"
            "  - 情景描写の豊かさ\n"
            "  - 感情表現の説得力\n"
            "  - これまでの文脈との整合性\n"
            "\n"
            "必ず次の JSON 形式だけを出力してください:\n"
            "{\n"
            '  \"winner\": \"A\" または \"B\",\n'
            '  \"score_diff\": 0.0〜1.0 の数値,\n'
            '  \"comment\": \"日本語で 1〜3 文の理由\"\n'
            "}\n"
        )

        user_content = (
            "【プロンプト】\n"
            f"{prompt}\n\n"
            "【応答A】\n"
            f"{reply_a}\n\n"
            "【応答B】\n"
            f"{reply_b}\n\n"
            "上記を比較し、指定された JSON 形式のみを出力してください。"
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

        # まずは最低限の枠だけ用意しておく
        result: Dict[str, Any] = {
            "winner": None,
            "score_diff": 0.0,
            "comment": "",
            # 🔸 生テキストは必ず保持
            "raw_text": text,
            # 🔸 解析に成功したらここに dict を入れる
            "raw_json": None,
            # 🔸 既存コードとの互換用（後で raw_json or raw_text を詰める）
            "raw": None,
            "route": meta.get("route"),
            "pair": {"A": label_a, "B": label_b},
        }

        parsed = self._safe_parse_json(text)

        if isinstance(parsed, dict):
            # パースに成功したら、JSON の中身で上書き
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

            # 解析済みJSONはここに
            result["raw_json"] = parsed
            # raw（互換用）には JSON を入れておく
            result["raw"] = parsed
        else:
            # JSON として読めなかった場合は、生テキストを raw に入れる
            result["raw"] = text

        # winner が決まらなかった場合のフォールバック
        if result["winner"] is None:
            result["winner"] = label_a
            result["score_diff"] = 0.0
            if not result["comment"]:
                result["comment"] = (
                    "JSON の解析に失敗したため、暫定的に A 側を選択しました。"
                )

        return result

    def _safe_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        LLM の出力から JSON らしき部分を抜き出してパースする簡易ヘルパ。
        """
        try:
            stripped = text.strip()
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            json_str = stripped[start : end + 1]
            return json.loads(json_str)
        except Exception:
            return None
