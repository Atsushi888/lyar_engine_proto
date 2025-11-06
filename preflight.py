# preflight.py — Lyra Engine / Preflight Diagnostics

import os, requests
from dataclasses import dataclass
from typing import Dict

@dataclass
class CheckResult:
    ok: bool
    message: str
    extra: Dict = None

class PreflightChecker:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")

    def check_openai(self) -> CheckResult:
        if not self.openai_key:
            return CheckResult(False, "OPENAI_API_KEY が設定されていません。")

        url = "https://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {self.openai_key}"}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return CheckResult(True, "OpenAI API キーは有効です。")
            if r.status_code == 401:
                return CheckResult(False, "OpenAI API キーが無効です（401）。")
            if r.status_code == 429:
                return CheckResult(
                    False,
                    "OpenAI API の利用上限（quota）を超過しています（429）。"
                )
            return CheckResult(False, f"OpenAI API 応答異常: {r.status_code}")
        except Exception as e:
            return CheckResult(False, f"OpenAI 接続エラー: {e}")

    def check_openrouter(self) -> CheckResult:
        if not self.openrouter_key:
            return CheckResult(False, "OPENROUTER_API_KEY が設定されていません。")

        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {self.openrouter_key}"}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                has_hermes = any(
                    "hermes" in m.get("id", "")
                    for m in data.get("data", [])
                )
                if has_hermes:
                    return CheckResult(True, "OpenRouter キー有効（Hermes 利用可）。")
                else:
                    return CheckResult(True, "OpenRouter キー有効（Hermes は見つからず）。")
            if r.status_code == 401:
                return CheckResult(False, "OpenRouter API キーが無効です（401）。")
            return CheckResult(False, f"OpenRouter 応答異常: {r.status_code}")
        except Exception as e:
            return CheckResult(False, f"OpenRouter 接続エラー: {e}")

    def run_all(self) -> Dict[str, CheckResult]:
        return {
            "openai": self.check_openai(),
            "openrouter": self.check_openrouter(),
        }
