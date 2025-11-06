# personas/__init__.py — Persona ローダー
import importlib
from typing import Dict
from dataclasses import dataclass

# Persona型をここでも宣言しておく（インポートのたびに参照されるため）
@dataclass
class Persona:
    char_id: str
    name: str
    system_prompt: str
    starter_hint: str


# 登録済み人格リスト（拡張可）
PERSONA_MAP: Dict[str, str] = {
    "floria_ja": "personas.persona_floria_ja",
    # 将来的にここへ追加していく：
    # "lunaria_en": "personas.persona_lunaria_en",
    # "noa_ja": "personas.persona_noa_ja",
}


def get_persona(char_id: str = "floria_ja") -> Persona:
    """人格IDを指定してPersonaオブジェクトを返す"""
    module_path = PERSONA_MAP.get(char_id)
    if not module_path:
        raise ValueError(f"Persona '{char_id}' は登録されていません。")

    mod = importlib.import_module(module_path)
    # 各モジュールの get_persona() を呼び出して Persona を返す
    return mod.get_persona()
