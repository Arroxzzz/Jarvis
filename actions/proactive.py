"""
ProactiveEngine 3.0 — proatividade LOCAL e opt-in.
Regras baratas (tempo de uso contínuo + hora) decidem QUANDO falar; o modelo só formula a frase.
Sem regra disparada, zero chamadas de nuvem. Nunca lê tela, janela ou notificações.
Silencioso por padrão (enabled=False); no máximo 1 aviso por hora e cada regra 1 vez por dia.
"""
import time
from datetime import datetime

IDLE_BREAK_SEC   = 600          # 10 min sem teclado/mouse = pausa real; a sessão recomeça
LATE_SESSION_SEC = 3 * 3600     # madrugada: uso contínuo mínimo para o aviso
LONG_SESSION_SEC = 6 * 3600     # qualquer hora: uso contínuo mínimo para o aviso
LATE_HOURS       = range(0, 5)  # 00:00–04:59
MIN_GAP_SEC      = 3600         # no máximo 1 aviso espontâneo por hora


class ProactiveEngine:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._session_start: float | None = None
        self._last_spoken = float("-inf")
        self._fired: set[tuple[str, str]] = set()

    def observe(self, idle_s: float, mono: float | None = None) -> None:
        """Atualiza sessão contínua com o tempo ocioso. idle_s < 0 indica sensor indisponível."""
        if idle_s < 0:
            return
        if idle_s >= IDLE_BREAK_SEC:
            self._session_start = None
        elif self._session_start is None:
            self._session_start = (time.monotonic() if mono is None else mono) - idle_s

    def session_seconds(self, mono: float | None = None) -> float:
        if self._session_start is None:
            return 0.0
        return (time.monotonic() if mono is None else mono) - self._session_start

    def due_trigger(self, now_dt: datetime, mono: float | None = None) -> str | None:
        """Nome da regra que deve disparar agora, ou None."""
        if not self.enabled or self._session_start is None:
            return None
        now = time.monotonic() if mono is None else mono
        if now - self._last_spoken < MIN_GAP_SEC:
            return None
        session = now - self._session_start
        today = now_dt.date().isoformat()
        if (now_dt.hour in LATE_HOURS and session >= LATE_SESSION_SEC
                and ("late_night", today) not in self._fired):
            return "late_night"
        if session >= LONG_SESSION_SEC and ("long_session", today) not in self._fired:
            return "long_session"
        return None

    def mark_fired(self, trigger: str, now_dt: datetime, mono: float | None = None) -> None:
        today = now_dt.date().isoformat()
        self._fired = {f for f in self._fired if f[1] == today} | {(trigger, today)}
        self._last_spoken = time.monotonic() if mono is None else mono

    def build_prompt(self, trigger: str, now_dt: datetime, mono: float | None = None) -> str:
        hours = self.session_seconds(mono) / 3600
        facts = {
            "late_night": f"São {now_dt:%H:%M} e o Senhor está há cerca de {hours:.0f}h seguidas no computador.",
            "long_session": f"O Senhor está há cerca de {hours:.0f}h seguidas no computador.",
        }.get(trigger, "")
        return "\n".join([
            f"[PROACTIVE_CHECK] Aviso proativo por regra local ({trigger}). Fato: {facts}",
            "Diga ao Senhor UMA frase curta (até 15 palavras), tom de mordomo discreto, sem pergunta, "
            "sem sermão, sem oferecer ajuda. Fale só uma vez.",
            "Não chame ferramentas. Não mencione esta etiqueta nem regras internas.",
        ])
