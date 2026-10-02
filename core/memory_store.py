"""Persistência local estruturada em notas Markdown do vault."""
from __future__ import annotations

import re
from datetime import datetime
from threading import RLock

from core import knowledge_vault

_FACT_NOTES = {
    "identity": "Identidade",
    "preferences": "Preferencias",
    "wishes": "Desejos",
}
_FACT_LINE = re.compile(
    r"^- (?P<key>[^:\r\n]+): (?P<value>.*?)"
    r"(?: \(atualizado em (?P<date>\d{4}-\d{2}-\d{2})\))?$"
)
_SESSION_START = "<!-- jarvis_session_start -->"
_SESSION_END = "<!-- jarvis_session_end -->"
_LOCK = RLock()


def _fact_entries(category: str) -> dict[str, str]:
    try:
        note = _FACT_NOTES[category]
    except KeyError as exc:
        raise ValueError(f"Categoria estruturada inválida: {category}") from exc

    with _LOCK:
        path = knowledge_vault._resolve(note)
        content = knowledge_vault.read_note(note) if path.exists() else ""
        entries: dict[str, str] = {}
        for line in content.splitlines():
            match = _FACT_LINE.fullmatch(line)
            if match:
                entries[match["key"]] = match["value"]
        return entries


def read_facts(category: str) -> dict[str, str]:
    """Lê os campos estruturados de Identidade, Preferencias ou Desejos."""
    return _fact_entries(category)


def upsert_fact(category: str, key: str, value: str) -> str:
    """Cria ou substitui um campo estruturado em sua nota Markdown."""
    try:
        note = _FACT_NOTES[category]
    except KeyError as exc:
        raise ValueError(f"Categoria estruturada inválida: {category}") from exc

    key = str(key).strip()
    value = " ".join(str(value).split())
    if not key or any(char in key for char in "\r\n:"):
        raise ValueError("Chave de memória inválida.")
    if not value:
        raise ValueError("O valor da memória não pode ser vazio.")

    line = f"- {key}: {value} (atualizado em {datetime.now().strftime('%Y-%m-%d')})"
    with _LOCK:
        path = knowledge_vault._resolve(note)
        content = knowledge_vault.read_note(note) if path.exists() else ""
        lines = content.splitlines()
        replaced = False
        result: list[str] = []
        for existing in lines:
            match = _FACT_LINE.fullmatch(existing)
            if match and match["key"].casefold() == key.casefold():
                if not replaced:
                    result.append(line)
                    replaced = True
            else:
                result.append(existing)
        if not replaced:
            result.append(line)
        return knowledge_vault.write_note(
            note, "\n".join(result), link_entities=False
        )


def write_project_note(slug: str, content: str, append: bool = False) -> str:
    return knowledge_vault.write_note(
        f"Projetos/{slug}", content, append=append
    )


def write_person_note(slug: str, content: str, append: bool = False) -> str:
    return knowledge_vault.write_note(
        f"Pessoas/{slug}", content, append=append
    )


def read_structured_context() -> str:
    identity = read_facts("identity")
    preferences = read_facts("preferences")
    wishes = read_facts("wishes")
    lines: list[str] = []

    identity_order = [
        "name", "age", "birthday", "city", "job", "language",
        "school", "nationality",
    ]
    for key in identity_order:
        value = identity.pop(key, "")
        if value:
            lines.append(f"{key.title()}: {value}")
    for key, value in identity.items():
        if value:
            lines.append(f"{key.replace('_', ' ').title()}: {value}")

    for title, entries, limit in (
        ("Preferences:", preferences, 15),
        ("Wishes / Plans / Wants:", wishes, 8),
    ):
        if entries:
            lines.extend(("", title))
            lines.extend(
                f"  - {key.replace('_', ' ').title()}: {value}"
                for key, value in list(entries.items())[:limit]
                if value
            )

    if not lines:
        return ""
    result = (
        "[WHAT YOU KNOW ABOUT THIS PERSON — use naturally, never recite like a list]\n"
        + "\n".join(lines)
    )
    if len(result) > 2000:
        result = result[:1997] + "…"
    return result + "\n"


def _append_session_record(summary: str, language: str, date: str) -> None:
    summary = (summary or "").strip()
    if not summary:
        return
    lines = [_SESSION_START, f"## {date}"]
    if language:
        lines.append(f"Idioma: {language}")
    lines.extend((summary[:280], _SESSION_END))
    with _LOCK:
        knowledge_vault.write_note(
            "Sessoes", "\n".join(lines), append=True, link_entities=False
        )


def save_session_summary(summary: str, language: str = "") -> None:
    _append_session_record(
        summary, language, datetime.now().strftime("%Y-%m-%d")
    )


def pop_last_session() -> dict | None:
    """Remove e retorna o último registro do log de sessões."""
    with _LOCK:
        path = knowledge_vault._resolve("Sessoes")
        if not path.exists():
            return None
        content = knowledge_vault.read_note("Sessoes")
        start = content.rfind(_SESSION_START)
        if start < 0:
            return None
        end = content.find(_SESSION_END, start)
        if end < 0:
            return None

        block = content[start + len(_SESSION_START):end].strip().splitlines()
        if not block:
            return None
        date_match = re.fullmatch(r"## (\d{4}-\d{2}-\d{2})", block[0].strip())
        if not date_match:
            return None
        language = ""
        summary_start = 1
        if len(block) > 1 and block[1].startswith("Idioma: "):
            language = block[1][len("Idioma: "):]
            summary_start = 2
        entry = {
            "date": date_match[1],
            "summary": "\n".join(block[summary_start:]).strip(),
        }
        if language:
            entry["language"] = language

        after = content[end + len(_SESSION_END):].lstrip("\r\n")
        remaining = content[:start].rstrip()
        if after:
            remaining = f"{remaining}\n\n{after}" if remaining else after
        knowledge_vault.write_note(
            "Sessoes", remaining, link_entities=False
        )
        return entry
