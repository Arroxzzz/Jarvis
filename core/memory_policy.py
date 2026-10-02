from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

import core.knowledge_vault as knowledge_vault
from core import memory_store

MemoryMode = Literal["automatic", "suggested", "explicit", "ignore"]

_SECRET_PATTERNS = (
    r"\b(?:api[_ -]?key|apikey|token|secret|senha|password|passphrase|bearer|auth\s*key)\b",
    r"\b(?:ghp_[A-Za-z0-9]+|sk-[A-Za-z0-9_-]+|AIza[0-9A-Za-z\-_]+|gsk_[A-Za-z0-9]+|xox[baprs]-[A-Za-z0-9-]+)\b",
)

_EXPLICIT_PATTERNS = (
    r"\b(?:lembre|anote|salve|registre|gravar|crie\s+uma\s+nota|registre\s+isso)\b",
    r"\b(?:lembrar|anotar|salvar|registrar)\b",
)

_AUTOMATIC_KEYWORDS = (
    "objetivo",
    "projeto",
    "stack",
    "decidimos",
    "decisão",
    "arquitetura",
    "próximo passo",
    "próximos passos",
    "preferência",
    "preferencias",
    "mudança de direção",
    "modelo",
    "provedor",
    "meta",
    "foco",
    "alvo",
    "estrutura",
)

_CASUAL_PATTERNS = (
    r"\b(?:oi|ol[áa]|hello|hey|tudo\s+bem|como\s+você\s+está|bom\s+dia|boa\s+noite|boa\s+tarde)\b",
    r"\b(?:estou\s+bem|legal|tranquilo|show|muito\s+útil|me\s+parece|muito\s+útil\s+hoje|você\s+me\s+parece)\b",
)


@dataclass
class MemoryProposal:
    text: str
    mode: MemoryMode = "ignore"
    title: str = ""
    content: str = ""
    category: str = "geral"
    project: str = "JARVIS"
    origin: str = "user"
    date: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    confidence: float = 0.0
    priority: str = "low"
    requires_confirmation: bool = False
    can_write: bool = False
    key: str = ""


def _looks_like_secret(text: str) -> bool:
    lower = text.lower()
    if any(re.search(pattern, lower) for pattern in _SECRET_PATTERNS):
        return True

    if re.search(r"(?:key|token|senha|password)[^\n]{0,20}[:=]\s*[A-Za-z0-9_\-./+=]{6,}", lower):
        return True

    if re.search(r"(?:bearer|token)\s+[A-Za-z0-9._~+\-=/]{8,}", lower):
        return True

    return False


def _extract_project(text: str) -> str:
    lower = text.lower()
    if "jarvis" in lower or "projeto" in lower or "sistema" in lower:
        return "JARVIS"
    if "supabase" in lower or "banco" in lower:
        return "infraestrutura"
    if "site" in lower or "web" in lower or "ui" in lower:
        return "frontend"
    return "JARVIS"


def _looks_like_casual(text: str) -> bool:
    lower = text.strip().lower()
    if not lower:
        return True
    if len(lower.split()) <= 8 and any(re.search(pattern, lower) for pattern in _CASUAL_PATTERNS):
        return True
    return False


def _looks_like_automatic(text: str) -> bool:
    lower = text.lower()
    if any(keyword in lower for keyword in _AUTOMATIC_KEYWORDS):
        return True

    if any(token in lower for token in ("objetivo do projeto", "decidimos usar", "mudou a direção", "próximo passo")):
        return True

    return False


def _looks_like_action_or_context_command(text: str) -> bool:
    lower = text.lower()

    if any(phrase in lower for phrase in (
        "não é lembrança",
        "não precisa salvar",
        "não precisa gravar",
        "esquece isso de notas",
        "esquece isso",
        "ignora isso",
        "não é anotação",
        "é uma ordem",
        "sem perguntar",
    )):
        return True

    if re.search(r"\b(?:mostra|mostre|mostrar|mostrando|onde\s+est[aá]|qual\s+(?:é|foi|a|o)|analisa|analise|analisar|apaga|apague|deleta|delete|lista|abre|abrir|verifica|checa|me\s+diz|me\s+mostra)\b", lower):
        return True

    if any(word in lower for word in ("área de trabalho", "downloads", "arquivo", "pdf", "projeto atual", "me mostra", "o que tem")):
        return True

    return False


def _looks_like_explicit_command(text: str) -> bool:
    lower = text.lower()
    if _looks_like_action_or_context_command(lower):
        return False
    if any(re.search(pattern, lower) for pattern in _EXPLICIT_PATTERNS):
        return True
    if lower.startswith("jarvis") and any(word in lower for word in ("lembre", "anote", "salve", "registre", "crie")):
        return True
    return False


def _title_from_text(text: str) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= 80:
        return normalized
    return normalized[:77].rstrip() + "..."


def _category_for(text: str) -> str:
    lower = text.lower()
    if re.search(r"\b(?:amigo|amiga|irm[aã]o|irmã|mãe|pai|esposa|marido|filho|filha|parceir[oa]|colega)\b", lower):
        return "relationships"
    if re.search(r"\b(?:prefere|preferência|preferencias|gosta|favorito|favorita|favorite|hobby)\b", lower):
        return "preferences"
    if re.search(r"\b(?:desej|gostaria|sonho|pretende|planos?\s+para\s+o\s+futuro|wish|want)\b", lower):
        return "wishes"
    if re.search(r"\b(?:nome|name|idade|age|aniversário|birthday|cidade|city|idioma|language|nacionalidade|nationality|telefone|phone|email)\b", lower):
        return "identity"
    if "objetivo" in lower or "meta" in lower:
        return "projects"
    if "decid" in lower or "usamos" in lower or "escolh" in lower:
        return "projects"
    if "stack" in lower or "tecnologia" in lower or "python" in lower or "gemini" in lower:
        return "projects"
    if "projeto" in lower or "project" in lower:
        return "projects"
    return "notes"


def classify_memory(text: str, *, confirmed: bool = False, project: str | None = None, origin: str = "user") -> MemoryProposal:
    """Classifica uma informação em um dos modos da política de memória.

    A decisão não grava arquivos: ela apenas produz a proposta de memória para que a
    camada de persistência decida o que escrever.
    """
    cleaned = " ".join(str(text).strip().split())
    if not cleaned:
        return MemoryProposal(text="", mode="ignore", title="", content="", category="geral", project=project or "JARVIS", origin=origin, confidence=0.0, priority="low", requires_confirmation=False, can_write=False)

    if _looks_like_secret(cleaned):
        return MemoryProposal(
            text=cleaned,
            mode="ignore",
            title="Conteúdo sensível rejeitado",
            content=cleaned,
            category="segredo",
            project=project or "JARVIS",
            origin=origin,
            confidence=0.0,
            priority="low",
            requires_confirmation=False,
            can_write=False,
        )

    if _looks_like_action_or_context_command(cleaned):
        return MemoryProposal(
            text=cleaned,
            mode="ignore",
            title="Comando de ação ou contexto",
            content=cleaned,
            category="comando",
            project=project or "JARVIS",
            origin=origin,
            confidence=0.0,
            priority="low",
            requires_confirmation=False,
            can_write=False,
        )

    if _looks_like_explicit_command(cleaned):
        mode: MemoryMode = "explicit"
        confidence = 0.95
        priority = "high"
        requires_confirmation = False
        can_write = True
    elif _looks_like_automatic(cleaned):
        mode = "automatic"
        confidence = 0.88
        priority = "high"
        requires_confirmation = False
        can_write = True
    elif _looks_like_casual(cleaned):
        mode = "ignore"
        confidence = 0.05
        priority = "low"
        requires_confirmation = False
        can_write = False
    else:
        mode = "suggested"
        confidence = 0.72
        priority = "normal"
        requires_confirmation = True
        can_write = False

    if mode == "suggested" and confirmed:
        mode = "automatic"
        confidence = 0.8
        priority = "high"
        requires_confirmation = False
        can_write = True

    proposal = MemoryProposal(
        text=cleaned,
        mode=mode,
        title=_title_from_text(cleaned),
        content=cleaned,
        category=_category_for(cleaned),
        project=project or _extract_project(cleaned),
        origin=origin,
        confidence=confidence,
        priority=priority,
        requires_confirmation=requires_confirmation,
        can_write=can_write,
    )

    return proposal


def _safe_note_name(title: str, project: str) -> str:
    base = re.sub(r"[^\w\-\s]+", " ", title.strip())
    base = re.sub(r"\s+", " ", base).strip()
    if not base:
        base = f"memoria_{project.lower()}"
    name = base[:50].strip()
    return name or f"memoria_{project.lower()}"


def _note_slug(category: str, content: str) -> str:
    patterns = {
        "projects": r"(?i:\bprojeto\b)\s+(?:(?i:chamado|nomeado|denominado)\s+)?[\"'“]?([A-ZÀ-ÖØ-Þ][\wÀ-ÿ-]*(?:\s+[A-ZÀ-ÖØ-Þ][\wÀ-ÿ-]*){0,2})",
        "relationships": r"(?i:\b(?:amigo|amiga|irm[aã]o|irmã|mãe|pai|esposa|marido|filho|filha|parceiro|parceira|colega)\b)\s+(?:(?i:chamado|chamada)\s+)?[\"'“]?([A-ZÀ-ÖØ-Þ][\wÀ-ÿ-]*(?:\s+[A-ZÀ-ÖØ-Þ][\wÀ-ÿ-]*){0,2})",
    }
    name = ""
    quoted = re.search(r"[\"“]([^\"”]{1,80})[\"”]", content)
    if quoted:
        name = quoted[1].strip()
    elif category in patterns:
        match = re.search(patterns[category], content)
        if match:
            candidate = match[1].strip()
            if candidate.split()[0].casefold() not in {
                "é", "de", "do", "da", "para", "que", "um", "uma", "the",
            }:
                name = candidate

    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    if slug:
        return slug[:60].strip("-")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:10]
    prefix = "projeto" if category == "projects" else "pessoa"
    return f"{prefix}-{digest}"


def _fact_key(proposal: MemoryProposal) -> str:
    if proposal.key.strip():
        return proposal.key
    normalized = unicodedata.normalize("NFKD", proposal.title or proposal.content)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text.lower()).strip("_")[:60] or "fact"


def persist_memory_proposal(proposal: MemoryProposal, *, confirmed: bool = False) -> dict:
    """Persiste propostas elegíveis no armazenamento correspondente à categoria."""
    if proposal.mode == "ignore":
        return {"saved": False, "reason": "ignored", "mode": proposal.mode}

    if proposal.mode == "suggested":
        if not confirmed:
            return {"saved": False, "reason": "pending_confirmation", "mode": proposal.mode}
        proposal.mode = "automatic"
        proposal.can_write = True
        proposal.requires_confirmation = False
        proposal.confidence = max(proposal.confidence, 0.8)
        proposal.priority = "high"

    if not proposal.can_write:
        return {"saved": False, "reason": "not_writable", "mode": proposal.mode}

    category = proposal.category
    if category in {"identity", "preferences", "wishes"}:
        memory_store.upsert_fact(
            category, _fact_key(proposal), proposal.content
        )
        note_name = {
            "identity": "Identidade",
            "preferences": "Preferencias",
            "wishes": "Desejos",
        }[category]
        path = str(knowledge_vault._resolve(note_name))
    else:
        content = (
            f"# {proposal.title or 'Memória'}\n\n{proposal.content}\n\n"
            f"- categoria: {proposal.category}\n"
            f"- projeto: {proposal.project}\n"
            f"- origem: {proposal.origin}\n"
            f"- data: {proposal.date}\n"
            f"- confiança: {proposal.confidence}\n"
            f"- modo: {proposal.mode}\n"
            f"- prioridade: {proposal.priority}"
        )
        if category in {"projects", "relationships"}:
            note_name = _note_slug(category, proposal.content)
            writer = (
                memory_store.write_project_note
                if category == "projects"
                else memory_store.write_person_note
            )
            writer(note_name, content)
            path = str(
                knowledge_vault._resolve(
                    f"{'Projetos' if category == 'projects' else 'Pessoas'}/{note_name}"
                )
            )
        else:
            note_name = _safe_note_name(
                proposal.title or proposal.content, proposal.project
            )
            knowledge_vault.write_note(note_name, content)
            path = str(knowledge_vault._resolve(note_name))

    return {
        "saved": True,
        "reason": "persisted",
        "mode": proposal.mode,
        "note": note_name,
        "path": path,
    }


def record_memory(text: str, *, confirmed: bool = False, project: str | None = None, origin: str = "user") -> dict:
    """Adaptador mínimo: classifica e persiste a proposta com a política vigente."""
    proposal = classify_memory(text, confirmed=confirmed, project=project, origin=origin)
    return persist_memory_proposal(proposal, confirmed=confirmed)


def handle_memory_request(text: str, *, confirmed: bool = False, project: str | None = None, origin: str = "user") -> dict:
    """Interface mínima para uma solicitação de memória pelo usuário ou tool."""
    proposal = classify_memory(text, confirmed=confirmed, project=project, origin=origin)
    if proposal.mode == "ignore":
        return {"saved": False, "reason": "ignored", "mode": proposal.mode, "proposal": proposal}

    if proposal.mode == "suggested" and not confirmed:
        return {"saved": False, "reason": "pending_confirmation", "mode": proposal.mode, "proposal": proposal}

    result = persist_memory_proposal(proposal, confirmed=confirmed or proposal.mode in {"automatic", "explicit"})
    result["proposal"] = proposal
    result["mode"] = proposal.mode
    return result


__all__ = ["MemoryMode", "MemoryProposal", "classify_memory", "persist_memory_proposal", "record_memory", "handle_memory_request"]
