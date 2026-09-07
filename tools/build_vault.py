"""Empacota o projeto inteiro (exceto python-embed/veracrypt/tools) em
project.enc — rodar sempre que atualizar código antes de copiar pro pendrive."""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.crypto_vault import encrypt_archive

BASE = Path(__file__).resolve().parent.parent
OUT  = BASE / "project.enc"

EXCLUDE = {"python-embed", "veracrypt", "tools", "__pycache__",
          ".git", "project.enc", ".ai"}

pw  = getpass.getpass("Senha mestra do pendrive: ")
pw2 = getpass.getpass("Confirme: ")
if pw != pw2:
    print("Senhas não coincidem.")
    sys.exit(1)

encrypt_archive(BASE, OUT, pw, exclude_names=EXCLUDE)
print(f"Criado: {OUT}")
print("Copie project.enc + python-embed/ para o pendrive.")
