from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable, Optional


@dataclass
class ModelEntry:
    key: str
    label: str
    enabled: bool = True


class MultiAIDisplayConfig:
    """
    どのAIをどのラベルで、どの順で表示するかを管理するクラス。
    UIには依存しない設定層。
    """

    def __init__(self, initial: Optional[Dict[str, str]] = None) -> None:
        self._entries: Dict[str, ModelEntry] = {}
        if initial:
            for k, v in initial.items():
                self._entries[k] = ModelEntry(key=k, label=v, enabled=True)

    def register(self, key: str, label: str, enabled: bool = True) -> None:
        self._entries[key] = ModelEntry(key=key, label=label, enabled=enabled)

    def remove(self, key: str) -> None:
        self._entries.pop(key, None)

    def enable(self, key: str) -> None:
        if key in self._entries:
            self._entries[key].enabled = True

    def disable(self, key: str) -> None:
        if key in self._entries:
            self._entries[key].enabled = False

    def ordered_keys(self) -> List[str]:
        return list(self._entries.keys())

    def set_order(self, keys: Iterable[str]) -> None:
        new_entries: Dict[str, ModelEntry] = {}
        for k in keys:
            if k in self._entries:
                new_entries[k] = self._entries[k]
        for k, e in self._entries.items():
            if k not in new_entries:
                new_entries[k] = e
        self._entries = new_entries

    def get_visible_models(
        self,
        available_models: Dict[str, object],
    ) -> List[Tuple[str, str]]:
        result: List[Tuple[str, str]] = []
        for key, entry in self._entries.items():
            if not entry.enabled:
                continue
            if key not in available_models:
                continue
            result.append((entry.key, entry.label))
        return result

    def ensure_from_models(self, models: Dict[str, object]) -> None:
        for key in models.keys():
            if key not in self._entries:
                self._entries[key] = ModelEntry(key=key, label=key, enabled=True)
