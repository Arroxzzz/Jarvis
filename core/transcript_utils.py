import re

_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)


def _clean_transcript(text: str) -> str:
    text = _CTRL_RE.sub("", text)
    return re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)


def _join_transcript(parts: list[str]) -> str:
    """Concatena fragmentos de transcrição sem inserir espaços entre palavras."""
    return " ".join("".join(parts).split())


def _should_close_wake_gate(was_speaking: bool, server_turn_done: bool) -> bool:
    """Fecha o gate só na transição de fala para silêncio após o turno do servidor."""
    return was_speaking and server_turn_done


def _watchdog_should_reconnect(
    awaiting_response: bool,
    last_activity: float,
    now: float,
    timeout: float = 20.0,
) -> bool:
    """Indica se uma resposta pendente excedeu o timeout."""
    return awaiting_response and (now - last_activity) > timeout
