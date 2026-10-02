"""Estado volátil do runtime, separado da memória pessoal."""
from __future__ import annotations

import json
from threading import RLock

from core.paths import get_base_dir

RUNTIME_STATE_PATH = get_base_dir() / "memory" / "runtime_state.json"
_LOCK = RLock()


def load_runtime_state() -> dict:
    with _LOCK:
        if not RUNTIME_STATE_PATH.exists():
            return {}
        data = json.loads(RUNTIME_STATE_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("runtime_state.json deve conter um objeto JSON.")
        return data


def save_runtime_state(state: dict) -> None:
    if not isinstance(state, dict):
        raise TypeError("O estado de runtime deve ser um objeto.")
    with _LOCK:
        RUNTIME_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        RUNTIME_STATE_PATH.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def update_runtime_state(section: str, value: object) -> None:
    with _LOCK:
        state = load_runtime_state()
        state[section] = value
        save_runtime_state(state)
