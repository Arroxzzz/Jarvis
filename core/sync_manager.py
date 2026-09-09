"""
core/sync_manager.py — Sincronização criptografada por arquivo com
Supabase Storage (bucket privado). Só executa sob comando explícito
("Jarvis, sincronize") — nunca automático.
Estratégia: comparação por mtime local vs. sync_state.json (metadado
não-criptografado com hash+timestamp por arquivo, guardado local).
"""
import hashlib
import json
import time
from pathlib import Path

import requests

from core.paths import get_base_dir
from core.crypto_vault import encrypt_bytes, decrypt_bytes
from core.knowledge_vault import KNOWLEDGE_DIR

BASE_DIR = get_base_dir()
STATE_PATH = BASE_DIR / "memory" / "sync_state.json"
MEMORY_JSON = BASE_DIR / "memory" / "long_term.json"


def _config() -> dict:
    try:
        return json.loads((BASE_DIR / "config" / "api_keys.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def _bucket_url(cfg: dict, remote_key: str) -> str:
    return f"{cfg['supabase_url']}/storage/v1/object/{cfg['supabase_bucket']}/{remote_key}"


def _headers(cfg: dict) -> dict:
    return {"Authorization": f"Bearer {cfg['supabase_service_key']}"}


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sync_one(path: Path, remote_key: str, password: str, cfg: dict,
             state: dict, hostname: str) -> str:
    local_hash = _file_hash(path) if path.exists() else None
    local_mtime = path.stat().st_mtime if path.exists() else 0
    known = state.get(remote_key, {})

    r = requests.get(_bucket_url(cfg, remote_key), headers=_headers(cfg), timeout=15)
    remote_exists = r.status_code == 200

    if remote_exists:
        try:
            remote_plain = decrypt_bytes(r.content, password)
            remote_hash = hashlib.sha256(remote_plain).hexdigest()
        except Exception:
            return f"⚠ {remote_key}: falha ao decifrar remoto (senha incorreta?)"
    else:
        remote_hash = None

    if local_hash == known.get("hash") and remote_hash == known.get("hash"):
        return f"= {remote_key}: já sincronizado"

    if (local_hash and local_hash != known.get("hash")
            and remote_hash and remote_hash != known.get("hash")
            and local_hash != remote_hash):
        return (
            f"⚠ CONFLITO em {remote_key}: editado localmente e na nuvem "
            f"desde o último sync. Mantendo versão LOCAL, backup remoto preservado."
        )

    if path.exists() and (not remote_exists or local_hash != remote_hash):
        enc = encrypt_bytes(path.read_bytes(), password)
        requests.put(
            _bucket_url(cfg, remote_key),
            headers={**_headers(cfg), "Content-Type": "application/octet-stream", "x-upsert": "true"},
            data=enc,
            timeout=30,
        )
        state[remote_key] = {"hash": local_hash, "updated": time.time(), "origin": hostname}
        return f"↑ {remote_key}: enviado para a nuvem"

    if remote_exists and remote_hash != local_hash:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(remote_plain)
        state[remote_key] = {"hash": remote_hash, "updated": time.time(), "origin": "cloud"}
        return f"↓ {remote_key}: baixado da nuvem"

    return f"= {remote_key}: nada a fazer"


def sync_all(password: str) -> str:
    cfg = _config()
    if not cfg.get("supabase_url") or not cfg.get("supabase_service_key"):
        return "Supabase não configurado — verifique config/api_keys.json."

    import platform
    hostname = platform.node()
    state = _load_state()
    results = []

    results.append(_sync_one(MEMORY_JSON, "long_term.json", password, cfg, state, hostname))
    for note in KNOWLEDGE_DIR.glob("*.md"):
        results.append(_sync_one(note, f"knowledge/{note.name}", password, cfg, state, hostname))

    _save_state(state)
    return "\n".join(results)
