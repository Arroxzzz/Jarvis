import json
import re
import shutil
import threading
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from core.paths import get_base_dir, get_home_dir


_SAFE_ROOTS = [get_home_dir()]


def is_write_allowed(action: str, target: Path | None) -> bool:
    if target is None:
        return False
    try:
        resolved = target.resolve()
        return any(
            resolved == root.resolve() or resolved.is_relative_to(root.resolve())
            for root in _SAFE_ROOTS
        )
    except Exception:
        return False


def log_action(action: str, target: str, allowed: bool) -> None:
    audit_path = get_base_dir() / "memory" / "audit_log.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "target": target,
        "allowed": allowed,
    }
    with open(audit_path, "a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def backup_file(path: Path) -> Path | None:
    """Copia o arquivo existente para memory/backups/<timestamp>_<nome>.bak antes de sobrescrever.
    Não levanta exceção: se o backup falhar, devolve None e a escrita segue."""
    try:
        if not path.is_file():
            return None
        dest_dir = get_base_dir() / "memory" / "backups"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{path.name}.bak"
        shutil.copy2(path, dest)
        return dest
    except Exception as e:
        print(f"[WriteGuard] ⚠️ Backup falhou para {path.name}: {e}")
        return None


# ── Confirmação por voz, validada pelo código ────────────────────────────────
CONFIRM_WINDOW_SEC = 20.0
MAX_MISSES = 1
MAX_CONFIRM_WORDS = 4
DONE_COOLDOWN_SEC = 60.0
_CANCEL_WORDS = {"nao", "cancela", "cancele", "cancelar", "pare", "deixa", "esquece",
                 "desisto", "errado", "nunca"}

_gate_lock = threading.Lock()
_pending: dict | None = None
_last_done: tuple[str, float] | None = None


def _norm_words(text: str) -> list[str]:
    t = unicodedata.normalize("NFKD", (text or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9\s]", " ", t).split()


def request_confirmation(key: str, summary: str, run: Callable[[], str],
                         player=None, audit: tuple[str, str] | None = None,
                         silent_result: bool = False) -> str:
    """Registra um pedido pendente; `run` só é chamado após confirmação do usuário."""
    global _pending
    now = time.monotonic()
    with _gate_lock:
        if _last_done and _last_done[0] == key and now - _last_done[1] < DONE_COOLDOWN_SEC:
            return ("[JA_EXECUTADO] Esta ação já foi executada agora há pouco. "
                    "NÃO repita; informe o Senhor em uma frase.")
        if (_pending and _pending["key"] == key
                and not (_pending["armed"] and now > _pending["expires"])):
            return ("[AGUARDANDO_CONFIRMACAO] Este mesmo pedido já está aguardando. "
                    "NÃO chame a ferramenta de novo; aguarde o 'confirmo' do Senhor.")
        _pending = {"key": key, "summary": summary, "run": run, "audit": audit,
                    "armed": False, "armed_at": 0.0, "expires": 0.0, "misses": 0,
                    "silent_result": silent_result}
    if audit:
        log_action(audit[0], audit[1], False)
    if player:
        try:
            player.write_log(f"SYS: Aguardando confirmação — {summary}")
            player.show_content("CONFIRMAR", f"{summary}\n\nDiga 'confirmo' ou 'cancela'.")
        except Exception:
            pass
    return (f"[AGUARDANDO_CONFIRMACAO] Nada foi executado. AÇÃO: {summary}. "
            "Leia essa ação ao Senhor em uma frase e peça para confirmar dizendo \"confirmo\" (ou \"cancela\"). "
            "Após o \"confirmo\" NÃO chame a ferramenta de novo nem diga que foi feito: o sistema executa e avisa.")


def clear_pending() -> None:
    global _pending
    with _gate_lock:
        _pending = None


def _judge(text: str, utter_at: float | None):
    """None | ("confirm"|"retry"|"cancel", pedido, motivo). Chamar com _gate_lock preso e _pending armado."""
    global _pending, _last_done
    p = _pending
    now = time.monotonic()
    if (utter_at or now) > p["expires"]:
        _pending = None
        return ("cancel", p, "expirou")
    if not (text or "").strip():
        return None
    if utter_at and utter_at < p["armed_at"]:
        return None
    words = _norm_words(text)
    if set(words) & _CANCEL_WORDS:
        _pending = None
        return ("cancel", p, "negacao")
    if "confirmo" in words and len(words) <= MAX_CONFIRM_WORDS:
        _pending = None
        _last_done = (p["key"], now)
        return ("confirm", p, "")
    p["misses"] += 1
    if p["misses"] > MAX_MISSES:
        _pending = None
        return ("cancel", p, "nao_entendi")
    return ("retry", p, "")


def on_turn_complete(text: str, utter_at: float | None = None):
    """O primeiro turno após o registro arma a janela; os seguintes julgam a fala."""
    with _gate_lock:
        if _pending is None:
            return None
        if not _pending["armed"]:
            _pending["armed"] = True
            _pending["armed_at"] = time.monotonic()
            _pending["expires"] = _pending["armed_at"] + CONFIRM_WINDOW_SEC
            return None
        return _judge(text, utter_at)


def on_typed(text: str):
    """Julga texto digitado no chat somente depois de a janela estar armada."""
    with _gate_lock:
        if _pending is None or not _pending["armed"]:
            return None
        return _judge(text, None)