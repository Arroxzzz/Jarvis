from __future__ import annotations

import os
import re
import platform
from pathlib import Path
from typing import Iterable


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if token}


def _describe_path_location(path_value: str | os.PathLike[str] | None) -> str:
    """Converte um caminho absoluto em um rótulo curto e natural para o usuário."""
    if not path_value:
        return "no diretório relevante"

    path = Path(path_value)
    parts = [part.lower() for part in path.parts]

    if "desktop" in parts:
        return "na área de trabalho"
    if "downloads" in parts:
        return "nos downloads"
    if "documents" in parts or "documentos" in parts:
        return "nos documentos"
    if "home" in parts or "usuario" in parts:
        return "na pasta pessoal"
    if path.parent.name:
        return f"em {path.parent.name}"
    return "no diretório relevante"


def _default_roots() -> list[Path]:
    home = Path.home()
    return [
        home / "Desktop",
        home / "Downloads",
        home / "Documents",
    ]


def find_context_candidates(query: str, roots: Iterable[str | os.PathLike[str]] | None = None, max_results: int = 5) -> list[dict]:
    """Resolve candidatos mínimos de contexto local por nome aproximado e raiz.

    Regras mÍnimas:
    - não varre tudo o disco;
    - só considera as raízes passadas;
    - ordena por nome e recência;
    - sem automação visual; sem coleta contínua.
    """
    cleaned = _normalize_text(query)
    if not cleaned:
        return []

    tokens = _tokenize(cleaned)
    root_list = [Path(root) for root in (roots or _default_roots())]
    if not root_list:
        return []

    matches: list[dict] = []

    for root in root_list:
        if not root.exists():
            continue
        for path in root.rglob('*'):
            if not path.is_file():
                continue
            name = path.name.lower()
            stem = path.stem.lower()
            extension = path.suffix.lower().lstrip(".")
            stem_tokens = _tokenize(stem)
            name_tokens = _tokenize(name)

            overlap = sorted(token for token in tokens if token in name_tokens)
            stem_overlap = sorted(token for token in tokens if token in stem_tokens)
            score = 0

            if overlap:
                score += len(overlap) * 12
            if stem_overlap:
                score += len(stem_overlap) * 6
            if len(tokens) and set(tokens) <= name_tokens:
                score += 18
            if extension and extension in tokens:
                score += 25
            if extension and not extension.startswith("tmp") and tokens and any(token in stem_tokens for token in tokens):
                score += 8
            if len(tokens) == 1:
                token = next(iter(tokens))
                if token in name:
                    score += 4
            if score <= 0:
                continue

            try:
                mtime = path.stat().st_mtime
            except OSError:
                mtime = 0
            matches.append({
                "name": path.name,
                "path": str(path),
                "score": score,
                "mtime": mtime,
            })

    matches.sort(key=lambda item: (-item["score"], -item["mtime"]))
    unique: list[dict] = []
    seen: set[str] = set()
    for item in matches:
        if item["path"] in seen:
            continue
        seen.add(item["path"])
        unique.append(item)
        if len(unique) >= max_results:
            break

    return unique


def get_active_window_title() -> str | None:
    """Retorna o título da janela ativa, sob demanda e sem monitoramento contínuo."""
    if platform.system() != "Windows":
        return None

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None

        length = user32.GetWindowTextLengthW(hwnd) + 1
        buffer = wintypes.WCHAR * length
        text = buffer()
        if user32.GetWindowTextW(hwnd, text, length) == 0:
            return None
        title = text.value.strip()
        return title or None
    except Exception:
        return None


def resolve_context(
    query: str,
    roots: Iterable[str | os.PathLike[str]] | None = None,
    max_results: int = 5,
    active_window_title: str | None = None,
) -> dict:
    """Resolve um pedido local de contexto com confirmação em caso de ambiguidade."""
    candidates = find_context_candidates(query, roots=roots, max_results=max_results)
    active_window = active_window_title or get_active_window_title()
    active_tokens = _tokenize((active_window or ""))

    if active_tokens:
        boosted: list[dict] = []
        for item in candidates:
            path = Path(str(item.get("path") or ""))
            path_tokens = _tokenize(str(path.parent.name) + " " + str(path.stem))
            window_match = bool(active_tokens & path_tokens)
            score = item["score"]
            if window_match:
                score += 25
            boosted.append({**item, "score": score})
        boosted.sort(key=lambda item: (-item["score"], -item["mtime"]))
        candidates = boosted[:max_results]

    if not candidates:
        return {
            "query": query,
            "candidates": [],
            "best_match": None,
            "needs_confirmation": False,
            "active_window": active_window,
            "reason": "nenhum candidato relevante encontrado",
        }

    top_score = candidates[0]["score"]
    close_matches = [item for item in candidates if item["score"] >= max(1, top_score - 10)]
    needs_confirmation = len(close_matches) > 1

    best_match = candidates[0] if candidates else None
    if best_match is not None:
        best_match = dict(best_match)
        best_match["display_location"] = _describe_path_location(best_match.get("path"))
        best_match["user_label"] = f"'{best_match.get('name')}' {best_match['display_location']}"

    return {
        "query": query,
        "candidates": candidates,
        "best_match": best_match,
        "needs_confirmation": needs_confirmation,
        "active_window": active_window,
        "reason": "mais de um candidato forte" if needs_confirmation else "candidato único suficientemente claro",
    }


def infer_active_project(
    roots: Iterable[str | os.PathLike[str]] | None = None,
    active_window_title: str | None = None,
    max_results: int = 5,
) -> dict:
    """Infere o projeto ativo a partir de diretórios relevantes, janela atual e artefatos locais."""
    roots_to_scan = [Path(root) for root in (roots or _default_roots())]
    window_title = (active_window_title or get_active_window_title() or "").strip()
    window_lower = window_title.lower()
    candidates: list[dict] = []

    for root in roots_to_scan:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_dir():
                continue
            name = path.name.strip()
            if not name or name.startswith(".") and name not in {".git"}:
                continue

            score = 0
            lower_name = name.lower()
            if window_lower and lower_name in window_lower:
                score += 35
            if (path / ".git").exists():
                score += 25
            if (path / "main.py").exists() or (path / "app.py").exists() or (path / "pyproject.toml").exists():
                score += 18
            if (path / "README.md").exists() or (path / "readme.md").exists():
                score += 12
            if any((path / marker).exists() for marker in ["requirements.txt", "package.json", "setup.py", ".vscode"]):
                score += 10
            if any((path / marker).exists() for marker in ["src", "core", "actions", "ui.py", "main.py"]):
                score += 8

            if score <= 0:
                continue

            try:
                files = [item for item in path.rglob("*") if item.is_file()]
                mtime = max((item.stat().st_mtime for item in files), default=path.stat().st_mtime)
            except OSError:
                mtime = 0

            candidates.append({
                "project_name": name,
                "path": str(path),
                "score": score,
                "mtime": mtime,
                "active_window": window_title or None,
            })

    if not candidates:
        return {
            "project_name": None,
            "path": None,
            "confidence": 0.0,
            "active_window": window_title or None,
            "reason": "nenhum diretório de projeto foi encontrado",
            "candidates": [],
        }

    candidates.sort(key=lambda item: (-item["score"], -item["mtime"]))
    best = candidates[0]
    confidence = min(0.99, max(0.0, best["score"] / 100.0))

    return {
        "project_name": best["project_name"],
        "path": best["path"],
        "confidence": round(confidence, 2),
        "active_window": window_title or None,
        "reason": "projeto ativo inferido por diretório e janela",
        "candidates": candidates[:max_results],
    }


def build_project_context(
    roots: Iterable[str | os.PathLike[str]] | None = None,
    active_window_title: str | None = None,
) -> str:
    """Gera um resumo curto e seguro do projeto ativo para ser injetado no prompt do turno."""
    project = infer_active_project(roots=roots, active_window_title=active_window_title)
    project_name = project.get("project_name")
    project_path = project.get("path")
    confidence = float(project.get("confidence", 0.0) or 0.0)
    active_window = project.get("active_window") or active_window_title

    if not project_name or confidence < 0.75:
        return ""

    window_part = f" com janela ativa '{active_window}'" if active_window else ""
    return (
        f"[PROJETO_ATIVO] Projeto ativo: '{project_name}' em '{project_path}'. "
        f"Confiança: {confidence:.2f}.{window_part} "
        "Use esse contexto como referência do ambiente de trabalho; não trate como confirmação automática de ação."
    )


__all__ = ["find_context_candidates", "resolve_context", "infer_active_project", "build_project_context", "get_active_window_title"]
