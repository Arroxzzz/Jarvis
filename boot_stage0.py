import io
import os
import sys
import shutil
import zipfile
import subprocess
import getpass
import platform
import socket
import datetime
from pathlib import Path

# Definindo a raiz do pendrive
PENDRIVE_ROOT = Path(__file__).parent.resolve()
RUNTIME_DIR = PENDRIVE_ROOT / ".runtime"
VAULT_ENC = PENDRIVE_ROOT / "project.enc"
PYTHON_EMBED = PENDRIVE_ROOT / "python-embed" / "python.exe"
PYTHONW_EMBED = PENDRIVE_ROOT / "python-embed" / "pythonw.exe"

# Constantes para derivação e criptografia inline
_SALT = b"JARVIS-VAULT-v1-PBKDF2"
_ITERATIONS = 200_000


def _derive_key(password: str) -> bytes:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def _decrypt_archive(enc_path: Path, out_dir: Path, password: str) -> None:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _derive_key(password)
    raw = enc_path.read_bytes()
    iv, ct = raw[:12], raw[12:]
    plain = AESGCM(key).decrypt(iv, ct, None)
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(plain)) as zf:
        zf.extractall(out_dir)


def _secure_wipe(path: Path) -> None:
    try:
        for f in path.rglob("*"):
            if f.is_file():
                size = f.stat().st_size
                with open(f, "r+b") as fh:
                    fh.write(b"\x00" * size)
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        shutil.rmtree(path, ignore_errors=True)


def _cleanup_stale_sessions() -> None:
    if not RUNTIME_DIR.exists():
        return
    import psutil
    for stale in RUNTIME_DIR.iterdir():
        if not stale.is_dir():
            continue
        try:
            pid = int(stale.name.rsplit("_", 1)[-1])
            if psutil.pid_exists(pid):
                continue
        except (ValueError, IndexError):
            pass
        shutil.rmtree(stale, ignore_errors=True)
def get_system_specs():
    specs = {}
    specs["date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    specs["os"] = f"{platform.system()}-{platform.release()}-{platform.version()}"
    specs["cpu"] = platform.processor() or "Não detectado"
    specs["gpu"] = "Não detectada"

    try:
        import psutil
        ram = psutil.virtual_memory()
        specs["ram"] = f"{ram.total / (1024**3):.1f} GB total, {ram.available / (1024**3):.1f} GB disponível"
    except Exception:
        specs["ram"] = "Não foi possível obter informações de RAM"

    try:
        import psutil
        disk = psutil.disk_usage(str(PENDRIVE_ROOT))
        specs["disk"] = f"{disk.free / (1024**3):.1f} GB"
    except Exception:
        specs["disk"] = "Não foi possível obter informações do pendrive"

    try:
        import uuid
        mac = ":".join(["{:02x}".format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 2)][::-1])
        specs["mac"] = mac
    except Exception:
        specs["mac"] = "Não detectado"

    try:
        hostname = socket.gethostname()
        specs["ip"] = socket.gethostbyname(hostname)
        specs["hostname"] = hostname
    except Exception:
        specs["ip"] = "Não detectado"
        specs["hostname"] = "Não detectado"

    return specs


def run():
    print("  J . A . R . V . I . S")
    print("  Just A Rather Very Intelligent System")
    print("-" * 54)
    print("Inicializando protocolos de segurança do núcleo...")
    print("Ambiente não verificado. Autenticação requerida.\n")

    if not VAULT_ENC.exists():
        print(f"[ERRO CRÍTICO] Arquivo cofre '{VAULT_ENC.name}' não encontrado na raiz!")
        input("\nPressione ENTER para fechar...")
        sys.exit(1)

    _cleanup_stale_sessions()
    session_dir = RUNTIME_DIR / f"session_{os.getpid()}"

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            pw = getpass.getpass("Frase de segurança: ")
            _decrypt_archive(VAULT_ENC, session_dir, pw)
            break
        except Exception:
            print(f"[-] Acesso negado. Tentativa {attempt}/{max_attempts}\n")
            if attempt == max_attempts:
                print("[!] Limite de tentativas excedido. Bloqueando sistema.")
                sys.exit(1)

    print("\n======================================================")
    print("   Identidade confirmada. Bem-vindo, Senhor Paulo.")
    print("======================================================\n")
    print("Realizando reconhecimento do ambiente hospedeiro...\n")

    specs = get_system_specs()
    print(f"Hoje é dia: {specs['date']}")
    print(f"Sistema Operacional: {specs['os']}")
    print(f"Processador: {specs['cpu']}")
    print(f"Placa de Vídeo: {specs['gpu']}")
    print(f"Memória RAM: {specs['ram']}")
    print(f"Armazenamento do Sistema: {specs['disk']}")
    print(f"Endereço MAC: {specs['mac']}")
    print(f"Endereço IP: {specs['ip']}")
    print(f"Nome da Máquina: {specs['hostname']}")
    print("======================================================\n")
    print("Todos os sistemas nominais. Interface visual pronta para ativação.")
    input("Pressione ENTER para prosseguir, Senhor...")

    try:
        env = os.environ.copy()
        
        exe = str(PYTHONW_EMBED) if PYTHONW_EMBED.exists() else str(PYTHON_EMBED)
        abs_session = session_dir.resolve()
        main_script = abs_session / "main.py"
        site_packages = PENDRIVE_ROOT / "python-embed" / "Lib" / "site-packages"

        # Comando inline que força a injeção do caminho da sessão e dos pacotes no sys.path
        python_inline_code = (
            f"import sys; "
            f"sys.path.insert(0, r'{site_packages}'); "
            f"sys.path.insert(0, r'{abs_session}'); "
            f"import runpy; "
            f"runpy.run_path(r'{main_script}', run_name='__main__')"
        )

        cmd = [exe, "-c", python_inline_code]

        import atexit
        import signal as _signal

        def _emergency_wipe():
            _secure_wipe(session_dir)

        def _exit_on_signal(_signum, _frame):
            raise SystemExit(0)

        atexit.register(_emergency_wipe)
        for _s in (_signal.SIGTERM, _signal.SIGINT):
            _signal.signal(_s, _exit_on_signal)

        subprocess.run(cmd, cwd=str(abs_session), env=env)
    finally:
        _secure_wipe(session_dir)


if __name__ == "__main__":
    run()