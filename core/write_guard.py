import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from core.paths import get_base_dir, get_home_dir


_SAFE_ROOTS = [get_home_dir()]
DESTRUCTIVE_ACTIONS = {"delete", "restart", "shutdown", "move"}


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


def require_confirmation(action: str, label: str, confirmed: bool) -> str | None:
    if action in DESTRUCTIVE_ACTIONS and not confirmed:
        return f"Confirmar {action} de '{label}'?"
    return None


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