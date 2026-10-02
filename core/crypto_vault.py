"""
core/crypto_vault.py — primitivas AES-256-GCM + PBKDF2 para criptografia de bytes.
"""
import os

_SALT = b'JARVIS-VAULT-v1-PBKDF2'
_ITERATIONS = 600_000

def _derive_key(password: str) -> bytes:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=_SALT, iterations=_ITERATIONS)
    return kdf.derive(password.encode("utf-8"))

def encrypt_bytes(data: bytes, password: str) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = _derive_key(password)
    iv = os.urandom(12)
    return iv + AESGCM(key).encrypt(iv, data, None)


def decrypt_bytes(enc: bytes, password: str) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = _derive_key(password)
    iv, ct = enc[:12], enc[12:]
    return AESGCM(key).decrypt(iv, ct, None)
