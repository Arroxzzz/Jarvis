from datetime import datetime


def build_system_instruction(
    asst_name: str,
    mem_str: str,
    vault_digest: str,
    sys_prompt: str,
    now: datetime,
) -> str:
    time_str = now.strftime("%A, %d de %B de %Y — %H:%M")
    time_context = (
        f"[CURRENT DATE & TIME]\n"
        f"Right now it is: {time_str} (horário de Brasília, BRT, UTC-3).\n"
        f"ALWAYS report time in BRT — NEVER say UTC or any other timezone.\n"
        f"Use this to calculate exact times for reminders.\n\n"
    )
    identity_context = (
        f"[IDENTITY]\n"
        f"Seu nome é {asst_name}. Você foi criado por Senhor Paulo "
        f"e existe para servi-lo com lealdade absoluta — não é um produto "
        f"genérico, é a criação pessoal dele.\n"
        "ADDRESS: Sempre trate o usuário como 'Senhor'. "
        "Nunca use 'Senhor Paulo', nunca 'sir', nunca 'efendim'.\n\n"
    )
    parts = [time_context, identity_context]
    if mem_str:
        parts.append(mem_str)
    if vault_digest:
        parts.append(vault_digest)
    parts.append(sys_prompt)
    return "\n".join(parts)
