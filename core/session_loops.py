import asyncio
import time
from datetime import datetime

from actions.background_monitor import check_all as monitor_check_all
from core import context_index, memory_store, write_guard
from core.hw_sensors import get_idle_seconds, is_foreground_fullscreen
from core.runtime_constants import TZ_BR as _TZ_BR
from core.transcript_utils import _watchdog_should_reconnect


async def run_turn_watchdog(jarvis) -> None:
    """Reconecta após uma solicitação sem resposta, fora de tools ativas/background."""
    response_timeout = 20.0
    while True:
        await asyncio.sleep(5)
        bg_tasks_pending = jarvis._tasks.pending_count()
        if jarvis._active_tool_tasks or bg_tasks_pending > 0:
            jarvis._last_turn_activity = time.monotonic()
            continue
        if (
            jarvis._vision_answer_pending
            and jarvis._vision_started_at
            and time.monotonic() - jarvis._vision_started_at > 30
        ):
            jarvis.ui.write_log(
                "SYS: ⚠️ A análise da tela demorou demais; reconectando a sessão."
            )
            jarvis._pending_vision = None
            jarvis._vision_answer_pending = False
            jarvis._vision_busy = False
            jarvis._vision_started_at = 0.0
            jarvis._vision_close_pending = False
            raise RuntimeError("Watchdog: vision response timeout")
        now = time.monotonic()
        if _watchdog_should_reconnect(
            jarvis._awaiting_response,
            jarvis._last_turn_activity,
            now,
            response_timeout,
        ):
            jarvis.ui.write_log(
                f"SYS: ⚠️ Sem resposta do modelo há {response_timeout:.0f}s — reconectando."
            )
            jarvis._awaiting_response = False
            raise RuntimeError("Watchdog: sem resposta do modelo — reconectando.")


async def run_system_monitor(jarvis) -> None:
    """Background task: voice alerts when metrics exceed thresholds."""
    while True:
        await asyncio.sleep(10)
        alert = await asyncio.to_thread(jarvis._sys_monitor.check)
        if not alert or not jarvis.session:
            continue
        with jarvis._speaking_lock:
            speaking = jarvis._is_speaking
        if (
            speaking
            or (time.monotonic() - jarvis._last_user_speech) < 10
            or is_foreground_fullscreen()
        ):
            continue
        try:
            await jarvis._safe_send_content([{"text": alert}])
        except Exception as exc:
            print(f"[Monitor] ⚠️ Could not send alert: {exc}")


async def run_background_monitor(jarvis) -> None:
    """Check user-configured topics periodically and speak new headlines."""
    await asyncio.sleep(300)
    while True:
        if jarvis.session:
            with jarvis._speaking_lock:
                speaking = jarvis._is_speaking
            recent_speech = (time.monotonic() - jarvis._last_user_speech) < 30
            if not speaking and not recent_speech and not is_foreground_fullscreen():
                try:
                    alerts = await asyncio.to_thread(monitor_check_all)
                    lang = (
                        memory_store.read_facts("identity")
                        .get("language", "")
                        .strip()
                        or "English"
                    )
                    for alert in alerts:
                        msg = (
                            f"{alert}\n\n"
                            f"Inform the user about this development naturally in {lang}. "
                            "One brief sentence only."
                        )
                        await jarvis._safe_send_content([{"text": msg}])
                        jarvis.ui.write_log("SYS: Monitor alert sent.")
                        await asyncio.sleep(6)
                except Exception as exc:
                    print(f"[Monitor] ⚠️ Background check error: {exc}")
        await asyncio.sleep(1800)


async def run_context_reindex(jarvis) -> None:
    """Refresh the local file index every 15 minutes without blocking Live."""
    await asyncio.sleep(5)
    while True:
        try:
            try:
                from core.context_resolver import _default_roots

                roots = _default_roots()
            except Exception:
                roots = []
            if roots:
                await asyncio.to_thread(context_index.rebuild_index, roots)
        except Exception as exc:
            print(f"[ContextIndex] ⚠️ Reindex failed: {exc}")
        await asyncio.sleep(900)


async def run_proactive_mode(jarvis) -> None:
    """Proatividade local opt-in: regras de uso contínuo e hora decidem quando falar."""
    while True:
        await asyncio.sleep(60)
        if not jarvis.session:
            continue
        now_dt = datetime.now(_TZ_BR)
        jarvis._proactive.observe(get_idle_seconds())
        if not jarvis._proactive.enabled:
            continue
        with jarvis._speaking_lock:
            speaking = jarvis._is_speaking
        if speaking or (time.monotonic() - jarvis._last_user_speech) < 30:
            continue
        trigger = jarvis._proactive.due_trigger(now_dt)
        if not trigger:
            continue
        try:
            await jarvis._safe_send_content(
                [{"text": jarvis._proactive.build_prompt(trigger, now_dt)}]
            )
        except Exception as exc:
            print(f"[Proactive] ⚠️ {exc}")
            continue
        jarvis._proactive.mark_fired(trigger, now_dt)
        write_guard.log_action("proactive", trigger, True)
        jarvis.ui.write_log(f"SYS: Aviso proativo ({trigger}).")
