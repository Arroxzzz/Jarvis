"""
core/crypto_vault.py — AES-256-GCM + PBKDF2 (mesmos primitivos da Fase 3
em dashboard/server.py) para criptografar config/api_keys.json → .enc.
"""
import base64
import json
import os
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
