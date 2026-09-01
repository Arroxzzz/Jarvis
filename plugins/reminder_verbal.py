import threading
import time

PLUGIN = {
    "name": "verbal_reminder",
    "description": (
        "Use esta ferramenta para criar lembretes verbais. "
        "O usuário definirá o tempo (em segundos) e a mensagem. "
        "O Jarvis falará a mensagem quando o tempo acabar."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "segundos": {"type": "INTEGER", "description": "Tempo em segundos para o lembrete"},
            "mensagem": {"type": "STRING", "description": "O texto que o Jarvis deve falar"},
        },
        "required": ["segundos", "mensagem"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    segundos = parameters.get("segundos", 60)
    mensagem = parameters.get("mensagem", "Lembrete sem descrição.")

    def aguardar_e_falar():
        time.sleep(segundos)
        if player:
            player.request_say(f"Senhor, aqui está o seu lembrete: {mensagem}")

    # Thread separada — não trava o loop principal do Jarvis
    threading.Thread(target=aguardar_e_falar, daemon=True).start()

    return f"Lembrete agendado para daqui a {segundos} segundos, Senhor."
