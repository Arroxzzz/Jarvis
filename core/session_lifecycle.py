import asyncio
from datetime import datetime

from core import memory_store
from core.llm_client import gemini_call_resilient
from core.runtime_constants import TZ_BR as _TZ_BR


async def send_boot_greeting(jarvis) -> None:
    """Saudação mínima no boot, em primeira pessoa e sem citar o próprio nome."""
    await asyncio.sleep(0.3)
    if not jarvis.session:
        return
    last = await asyncio.to_thread(memory_store.pop_last_session)
    style = "Em PT-BR, em primeira pessoa, SEM dizer o seu próprio nome e sem a palavra 'online'."
    if last:
        try:
            delta = (
                datetime.now(_TZ_BR).date()
                - datetime.strptime(last["date"], "%Y-%m-%d").date()
            ).days
            when = (
                "hoje mais cedo"
                if delta == 0
                else ("ontem" if delta == 1 else f"há {delta} dias")
            )
        except Exception:
            when = "da última vez"
        prompt = (
            f"{style} Faça uma saudação de até 4 palavras (ex.: 'Às ordens, Senhor.') e, em seguida, "
            f"uma frase curta lembrando que {when}: {last['summary']} Máximo 25 palavras no total."
        )
    elif __import__("os").environ.get("JARVIS_NEW_ENVIRONMENT") == "1":
        prompt = (
            f"{style} Note em uma frase que estamos em um ambiente diferente do habitual (outra máquina) "
            "e pergunte como o Senhor quer chamar este local. Máximo 2 frases curtas."
        )
    else:
        prompt = (
            f"{style} Faça UMA saudação de até 5 palavras informando que está pronto "
            "(ex.: 'Às ordens, Senhor.' ou 'Pronto, Senhor.')."
        )
    try:
        await jarvis._safe_send_content([{"text": prompt}])
    except Exception as exc:
        print(f"[Boot] Greeting failed: {exc}")


async def save_session_summary(jarvis) -> None:
    """Summarise the current session and append it to Sessoes.md."""
    log = jarvis._session_log
    if len(log) < 3:
        return
    jarvis._session_log = []

    lang = memory_store.read_facts("identity").get("language", "").strip()
    lang = lang or "English"
    convo = "\n".join(log[-40:])
    prompt = (
        f"Summarize this conversation in 1-2 sentences in {lang}. "
        "Focus on what the user accomplished or discussed. "
        "Refer to the assistant only in the first person ('I'), never by name. "
        "Output ONLY the summary text, nothing else:\n\n" + convo
    )
    try:
        summary = await asyncio.to_thread(
            gemini_call_resilient, prompt, None, "gemini-flash-latest", "general"
        )
        if summary and not summary.startswith("Não foi possível obter resposta"):
            memory_store.save_session_summary(summary, lang)
    except Exception as exc:
        print(f"[Memory] ⚠️ Session summary failed: {exc}")
