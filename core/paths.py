"""
core/paths.py — Resolução de paths para modo portátil (P7a).
JARVIS_PORTABLE=1 (setado pelo .bat) redireciona toda referência de "home"
para dentro do pendrive — zero rastro no PC hospedeiro. Sem a env var,
comportamento idêntico ao Path.home() atual (zero impacto no PC principal).
"""
import os
import sys
from pathlib import Path

def is_portable() -> bool:
    return os.environ.get("JARVIS_PORTABLE", "").strip() == "1"

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def get_home_dir() -> Path:
    if is_portable():
        jarvis_home = os.environ.get("JARVIS_HOME", "").strip()
        base = Path(jarvis_home) if jarvis_home else get_base_dir()
        home = base / "portable_home"
        home.mkdir(parents=True, exist_ok=True)
        return home
    return Path.home()

def get_desktop_dir() -> Path:
    d = get_home_dir() / "Desktop"
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_downloads_dir() -> Path:
    d = get_home_dir() / "Downloads"
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_documents_dir() -> Path:
    d = get_home_dir() / "Documents"
    d.mkdir(parents=True, exist_ok=True)
    return d
