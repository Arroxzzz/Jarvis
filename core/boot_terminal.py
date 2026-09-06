"""
core/boot_terminal.py — Sequência de boot P7a: senha → decrypt →
banner + specs → ENTER → fecha console → sobe UI.
"""
import ctypes
import getpass
import json
import os
import time
import platform
import socket
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.crypto_vault import decrypt_file
from memory.memory_manager import load_memory, save_memory

BASE_DIR   = Path(__file__).resolve().parent.parent
ENC_PATH   = BASE_DIR / "config" / "api_keys.enc"
PLAIN_PATH = BASE_DIR / "config" / "api_keys.json"
MAX_ATTEMPTS = 3

def _mac_address() -> str:
    mac = uuid.getnode()
    return ":".join(f"{(mac >> e) & 0xff:02x}" for e in range(40, -8, -8))

def _local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "N/A"

def _gpu_names() -> list[str]:
    try:
        out = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get", "name"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        names = [l.strip() for l in out.splitlines() if l.strip() and l.strip().lower() != "name"]
        return names or ["Não detectada"]
    except Exception:
        return ["Não detectada"]

def _print_specs() -> None:
    try:
        import psutil
        ram = psutil.virtual_memory()
        ram_str = f"{ram.total/1024**3:.1f} GB total, {ram.available/1024**3:.1f} GB disponível"
        disk_str = f"{psutil.disk_usage(str(BASE_DIR.anchor)).total/1024**3:.1f} GB"
    except Exception:
        ram_str = disk_str = "N/A"

    print(f"Hoje é dia: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"Sistema Operacional: {platform.platform()}")
    print(f"Processador: {platform.processor() or 'N/A'}")
    for gpu in _gpu_names():
        print(f"Placa de Vídeo: {gpu}")
    print(f"Memória RAM: {ram_str}")
    print(f"Armazenamento do Sistema: {disk_str}")
    print(f"Endereço MAC: {_mac_address()}")
    print(f"Endereço IP: {_local_ip()}")
    print(f"Nome da Máquina: {platform.node()}")
    print("=" * 54)

def _check_environment_change() -> None:
    memory = load_memory()
    last_host = memory.get("identity", {}).get("last_known_host", {}).get("value", "")
    current_host = platform.node()
    if last_host and last_host != current_host:
        os.environ["JARVIS_NEW_ENVIRONMENT"] = "1"
    memory.setdefault("identity", {})["last_known_host"] = {"value": current_host}
    save_memory(memory)

def run() -> None:
    print()
    print("  J . A . R . V . I . S")
    print("  Just A Rather Very Intelligent System")
    print("-" * 54)
    time.sleep(0.4)
    print("Inicializando protocolos de segurança do núcleo...")
    time.sleep(0.5)
    print("Ambiente não verificado. Autenticação requerida.\n")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        pw = getpass.getpass("Frase de segurança: ")
        try:
            keys = decrypt_file(ENC_PATH, pw)
            break
        except Exception:
            restantes = MAX_ATTEMPTS - attempt
            if restantes > 0:
                print(f"Credencial não reconhecida. {restantes} tentativa(s) restante(s).\n")
            else:
                print("\nCredenciais esgotadas. Protocolo de bloqueio acionado.")
    else:
        sys.exit(1)

    PLAIN_PATH.write_text(json.dumps(keys, indent=2), encoding="utf-8")

    print()
    time.sleep(0.3)
    print("=" * 54)
    print("   Identidade confirmada. Bem-vindo, Senhor Paulo.")
    print("=" * 54)
    time.sleep(0.4)
    print("\nRealizando reconhecimento do ambiente hospedeiro...\n")
    time.sleep(0.3)
    _print_specs()
    _check_environment_change()

    print("\nTodos os sistemas nominais. Interface visual pronta para ativação.")
    input("Pressione ENTER para prosseguir, Senhor...")

    try:
        ctypes.windll.kernel32.FreeConsole()
    except Exception:
        pass

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    pythonw = Path(sys.executable).parent / "pythonw.exe"
    exe = str(pythonw) if pythonw.exists() else sys.executable
    subprocess.Popen(
        [exe, str(BASE_DIR / "main.py")],
        cwd=str(BASE_DIR), env=env,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

if __name__ == "__main__":
    run()
