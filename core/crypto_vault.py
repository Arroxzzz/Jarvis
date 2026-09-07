"""
core/crypto_vault.py — AES-256-GCM + PBKDF2 (mesmos primitivos da Fase 3
em dashboard/server.py) para criptografar config/api_keys.json → .enc.
"""
import base64
import io
import json
import os
import shutil
import zipfile
from pathlib import Path

_SALT = b'JARVIS-VAULT-v1-PBKDF2'
_ITERATIONS = 200_000

def _derive_key(password: str) -> bytes:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=_SALT, iterations=_ITERATIONS)
    return kdf.derive(password.encode("utf-8"))

def encrypt_file(plain_path: Path, enc_path: Path, password: str) -> None:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = _derive_key(password)
    data = plain_path.read_bytes()
    iv = os.urandom(12)
    ct = AESGCM(key).encrypt(iv, data, None)
    enc_path.write_bytes(base64.b64encode(iv + ct))

def decrypt_file(enc_path: Path, password: str) -> dict:
    """Levanta exceção em senha errada."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = _derive_key(password)
    raw = base64.b64decode(enc_path.read_bytes())
    iv, ct = raw[:12], raw[12:]
    plain = AESGCM(key).decrypt(iv, ct, None)
    return json.loads(plain.decode("utf-8"))

def encrypt_archive(source_dir: Path, out_path: Path, password: str,
                    exclude_names: set[str] = frozenset()) -> None:
    """Zipa source_dir (ignorando exclude_names na raiz) e criptografa o
    zip inteiro com AES-256-GCM. Usado pelo build do pendrive (tools/build_vault.py)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in source_dir.rglob("*"):
            if item.is_dir():
                continue
            rel = item.relative_to(source_dir)
            if rel.parts and rel.parts[0] in exclude_names:
                continue
            zf.write(item, rel)

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = _derive_key(password)
    iv  = os.urandom(12)
    ct  = AESGCM(key).encrypt(iv, buf.getvalue(), None)
    out_path.write_bytes(iv + ct)   # sem base64 — arquivo binário direto, mais compacto

def decrypt_archive(enc_path: Path, out_dir: Path, password: str) -> None:
    """Descriptografa e extrai o zip em out_dir. Levanta exceção em senha errada."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = _derive_key(password)
    raw = enc_path.read_bytes()
    iv, ct = raw[:12], raw[12:]
    plain = AESGCM(key).decrypt(iv, ct, None)
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(plain)) as zf:
        zf.extractall(out_dir)

def secure_wipe(path: Path) -> None:
    """Best-effort: sobrescreve arquivos com zeros antes de deletar (sem
    admin não há wipe forense real, mas evita recuperação trivial via lixeira)."""
    try:
        for f in path.rglob("*"):
            if f.is_file():
                size = f.stat().st_size
                with open(f, "r+b") as fh:
                    fh.write(b"\x00" * size)
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        shutil.rmtree(path, ignore_errors=True)
