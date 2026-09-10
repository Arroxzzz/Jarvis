"""
core/knowledge_vault.py — Vault de conhecimento estilo Obsidian: notas em
Markdown puro, leitura/escrita local instantânea. Complementa (não
substitui) memory/long_term.json, que continua guardando dados
estruturados (identity/preferences/etc).
"""
import re
from pathlib import Path

from core.paths import get_base_dir

KNOWLEDGE_DIR = get_base_dir() / "knowledge"
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
    return sorted(p.stem for p in KNOWLEDGE_DIR.glob("*.md"))


def search_notes(query: str, max_results: int = 5) -> str:
    """Busca textual simples (grep) — sem embeddings, leve e gratuito."""
    query_low = query.lower()
    hits = []
    for path in KNOWLEDGE_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if query_low in text.lower():
            idx = text.lower().find(query_low)
            snippet = text[max(0, idx - 60):idx + 100].replace("\n", " ")
            hits.append(f"[{path.stem}] ...{snippet}...")
        if len(hits) >= max_results:
            break
    return "\n".join(hits) if hits else f"Nada encontrado sobre '{query}'."
