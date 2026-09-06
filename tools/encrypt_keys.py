"""Gera config/api_keys.enc a partir do api_keys.json existente, para o pendrive."""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.crypto_vault import encrypt_file

BASE  = Path(__file__).resolve().parent.parent
plain = BASE / "config" / "api_keys.json"
enc   = BASE / "config" / "api_keys.enc"

if not plain.exists():
    print("config/api_keys.json não encontrado.")
    sys.exit(1)

pw  = getpass.getpass("Defina a senha mestra do pendrive: ")
pw2 = getpass.getpass("Confirme a senha: ")
if pw != pw2:
    print("Senhas não coincidem.")
    sys.exit(1)

encrypt_file(plain, enc, pw)
print(f"Criado: {enc}")
print("Copie api_keys.enc para o pendrive. NUNCA copie api_keys.json em texto puro.")
