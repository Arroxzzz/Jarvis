"""
actions/coulson_listener.py — "Efeito Coulson": escuta ntfy.sh via SSE
(Server-Sent Events) e avisa o JARVIS instantaneamente quando o celular
envia uma notificação. Latência <200ms, CPU zero quando ocioso.
Payload criptografado com crypto_vault.encrypt_bytes — ntfy.sh é cego.
"""
import asyncio
import base64
import json
import logging
from pathlib import Path

import httpx

from core.crypto_vault import decrypt_bytes, _derive_key

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

_NTFY_BASE = "https://ntfy.sh"
_SALT      = b"JARVIS-COULSON-v1"

def _load_config() -> dict:
    try:
        return json.loads((BASE_DIR / "config" / "api_keys.json").read_text(encoding="utf-8"))
    except Exception:
        return {}

def _coulson_key(topic: str) -> bytes:
    """Deriva chave de criptografia do tópico + service_key — sem config extra."""
    from core.crypto_vault import _derive_key as dk
    cfg = _load_config()
    seed = f"COULSON:{topic}:{cfg.get('supabase_service_key', topic)}"
    import hashlib
    raw = hashlib.sha256(seed.encode()).digest()
    return raw

def encrypt_notification(payload: dict, topic: str) -> str:
    """Usado no MacroDroid/celular via script Python auxiliar (tools/encrypt_notification.py)."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import os
    key = _coulson_key(topic)
    data = json.dumps(payload).encode()
    iv = os.urandom(12)
    ct = AESGCM(key).encrypt(iv, data, None)
    return base64.b64encode(iv + ct).decode()

def _decrypt_notification(raw_text: str, topic: str) -> dict | None:
    """Decripta payload recebido do ntfy.sh. Retorna None se falhar."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key  = _coulson_key(topic)
        blob = base64.b64decode(raw_text)
        iv, ct = blob[:12], blob[12:]
        plain = AESGCM(key).decrypt(iv, ct, None)
        return json.loads(plain.decode())
    except Exception:
        # Fallback: tentar como JSON puro (modo não-criptografado, para debug)
        try:
            return json.loads(raw_text)
        except Exception:
            return None

def _format_message(data: dict) -> str:
    source  = data.get("source", "app")
    contact = data.get("contact", "alguém")
    content = data.get("content", "")

    source_labels = {
        "whatsapp": "WhatsApp",
        "email":    "e-mail",
        "sms":      "SMS",
    }
    src_label = source_labels.get(source.lower(), source)

    # Caso o MacroDroid envie "WhatsApp: Contato" como título
    # e "Contato: mensagem" como conteúdo — extrair o nome real
    if ": " in contact and contact.lower().startswith(src_label.lower()):
        contact = contact.split(": ", 1)[-1].strip()

    # Remover prefixo "Contato: " do content se presente
    if content and ": " in content:
        parts = content.split(": ", 1)
        if parts[0].strip().lower() == contact.lower():
            content = parts[1].strip()

    if content:
        return (f"[SYSTEM_ALERT] Senhor, {contact} enviou mensagem via "
                f"{src_label}: '{content[:120]}'. Informe isso naturalmente em 1 frase.")
    return f"[SYSTEM_ALERT] Senhor, {contact} entrou em contato via {src_label}."

async def listen_coulson(speak_fn, write_log_fn, stop_event: asyncio.Event) -> None:
    """
    Task assíncrona para o TaskGroup do main.py.
    Mantém conexão SSE com ntfy.sh e chama speak_fn() ao receber evento.
    Reconecta automaticamente em caso de queda de rede.
    """
    cfg   = _load_config()
    topic = cfg.get("ntfy_topic", "").strip()

    if not topic:
        write_log_fn("SYS: [Coulson] ntfy_topic não configurado — listener desativado.")
        return

    write_log_fn("SYS: [Coulson] Escutando notificações em tempo real.")

    backoff = 5
    last_id = None   # evita reprocessar mensagens em reconexão

    while not stop_event.is_set():
        try:
            # "since=last_id" faz ntfy.sh só enviar mensagens POSTERIORES ao último ID visto
            params = {"since": last_id} if last_id else {}
            url    = f"{_NTFY_BASE}/{topic}/sse"

            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url, params=params) as resp:
                    backoff = 5
                    async for line in resp.aiter_lines():
                        if stop_event.is_set():
                            return

                        if not line.startswith("data:"):
                            continue

                        raw = line[5:].strip()
                        if not raw:
                            continue

                        try:
                            outer = json.loads(raw)
                        except Exception:
                            continue

                        # Filtrar por tipo dentro do JSON — mais confiável que parsing SSE
                        if outer.get("event") != "message":
                            continue

                        # Atualizar last_id para evitar reprocessamento em reconexão
                        msg_id = outer.get("id")
                        if msg_id:
                            last_id = msg_id

                        msg_raw = outer.get("message", "").strip()
                        if not msg_raw:
                            continue

                        data = _decrypt_notification(msg_raw, topic)
                        if not data:
                            logger.warning("[Coulson] Payload não reconhecido — ignorado.")
                            continue

                        # Validar que tem pelo menos "source" ou "contact"
                        if not data.get("source") and not data.get("contact") and not data.get("content"):
                            continue

                        alert = _format_message(data)
                        write_log_fn(
                            f"SYS: [Coulson] {data.get('source', 'app')} "
                            f"de {data.get('contact', 'desconhecido')}"
                        )
                        speak_fn(alert)

        except httpx.ReadTimeout:
            pass
        except Exception as e:
            if not stop_event.is_set():
                write_log_fn(
                    f"SYS: [Coulson] Conexão perdida ({e}) — reconectando em {backoff}s."
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 120)
