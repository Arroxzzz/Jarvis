"""
core/knowledge_vault.py — Vault de conhecimento estilo Obsidian: notas em
Markdown puro, leitura/escrita local instantânea. Complementa (não
substitui) memory/long_term.json, que continua guardando dados
estruturados (identity/preferences/etc).
"""
import re
from pathlib import Path

OBSIDIAN_VAULT = Path(r"D:\Memoria_Jarvis")

KNOWLEDGE_DIR = OBSIDIAN_VAULT
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

_SAFE_NAME = re.compile(r"^[\w\-\s]+$", re.UNICODE)


def _resolve(name: str) -> Path:
    name = name.strip().removesuffix(".md")
    if not name or not _SAFE_NAME.match(name):
        raise ValueError("Nome de nota inválido.")
    return KNOWLEDGE_DIR / f"{name}.md"


def write_note(name: str, content: str, append: bool = False) -> str:
    path = _resolve(name)
    if append and path.exists():
        existing = path.read_text(encoding="utf-8")
        content = existing.rstrip() + "\n\n" + content
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return f"Nota '{path.stem}' salva."


def read_note(name: str) -> str:
    path = _resolve(name)
    if not path.exists():
        return f"Nota '{name}' não encontrada."
    return path.read_text(encoding="utf-8")


def list_notes() -> list[str]:
    return sorted(p.relative_to(KNOWLEDGE_DIR).with_suffix("").as_posix() for p in KNOWLEDGE_DIR.rglob("*.md"))


def search_notes(query: str, max_results: int = 5) -> str:
    """Busca textual simples (grep) — sem embeddings, leve e gratuito."""
    query_low = query.lower()
    hits = []
    for path in KNOWLEDGE_DIR.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if query_low in text.lower():
            idx = text.lower().find(query_low)
            snippet = text[max(0, idx - 60):idx + 100].replace("\n", " ")
            hits.append(f"[{path.stem}] ...{snippet}...")
        if len(hits) >= max_results:
            break
    return "\n".join(hits) if hits else f"Nada encontrado sobre '{query}'."


def search_context(query: str, max_results: int = 5) -> list[dict]:
    """Busca contextual mínima no vault local.

    Retorna uma lista de notas relevantes com título, caminho e trecho de evidência.
    """
    cleaned = (query or "").strip()
    if not cleaned:
        return []

    query_low = cleaned.lower()
    results = []

    for path in KNOWLEDGE_DIR.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        lower_text = text.lower()
        if query_low not in lower_text:
            continue

        idx = lower_text.find(query_low)
        snippet = text[max(0, idx - 80):idx + 140].replace("\n", " ").strip()
        title = path.stem
        rel = path.relative_to(KNOWLEDGE_DIR).as_posix()
        results.append({
            "title": title,
            "path": rel,
            "snippet": snippet,
            "score": 1.0,
        })
        if len(results) >= max_results:
            break

    return results


def build_memory_context(query: str, max_results: int = 3) -> str:
    """Formata a busca contextual em um bloco curto para uso futuro no prompt."""
    context = search_context(query, max_results=max_results)
    if not context:
        return ""

    lines = ["[MEMÓRIA LOCAL RELEVANTE]"]
    for item in context:
        lines.append(f"- {item['title']} ({item['path']}): {item['snippet']}")
    return "\n".join(lines)
