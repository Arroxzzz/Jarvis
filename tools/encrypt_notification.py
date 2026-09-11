"""
Gera payload criptografado para testar o Coulson sem celular.
Uso: python tools/encrypt_notification.py
Cole o resultado como body do POST no MacroDroid ou no curl de teste.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from actions.coulson_listener import encrypt_notification

cfg   = json.loads((Path(__file__).parent.parent / "config" / "api_keys.json").read_text())
topic = cfg.get("ntfy_topic", "")
if not topic:
    print("ntfy_topic não configurado em api_keys.json")
    sys.exit(1)

payload = {"source": "whatsapp", "contact": "Maria", "content": "Você vai na festa?"}
enc = encrypt_notification(payload, topic)
print(f"Payload cifrado:\n{enc}")
print(f"\nCurl de teste:")
print(f'curl -d "{enc}" https://ntfy.sh/{topic}')
