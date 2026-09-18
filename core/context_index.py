from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from memory.memory_manager import get_base_dir

DB_PATH = get_base_dir() / "memory" / "context_index.db"


def _reset_database_if_needed() -> None:
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute("SELECT COUNT(*) FROM files").fetchone()
        except Exception:
            conn.close()
            DB_PATH.unlink(missing_ok=True)
            return
        finally:
            if conn:
                conn.close()
    except Exception:
        DB_PATH.unlink(missing_ok=True)


def _connect() -> sqlite3.Connection:
    _reset_database_if_needed()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("CREATE TABLE IF NOT EXISTS files(path TEXT, name TEXT, ext TEXT, mtime REAL, project TEXT)")
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(name, content='files', content_rowid='rowid')")
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN INSERT INTO files_fts(rowid, name) VALUES (new.rowid, new.name); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN INSERT INTO files_fts(files_fts, rowid, name) VALUES('delete', old.rowid, old.name); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN INSERT INTO files_fts(files_fts, rowid, name) VALUES('delete', old.rowid, old.name); INSERT INTO files_fts(rowid, name) VALUES (new.rowid, new.name); END"
    )
    return conn


def index_exists() -> bool:
    if not DB_PATH.exists():
        return False
    try:
        conn = _connect()
        try:
            row = conn.execute("SELECT COUNT(*) FROM files").fetchone()
            return bool(row and row[0] > 0)
        finally:
            conn.close()
    except Exception:
        return False


def rebuild_index(roots: list[Path]) -> None:
    if not roots:
        return

    _reset_database_if_needed()
    conn = _connect()
    try:
        conn.execute("BEGIN")
        conn.execute("DELETE FROM files")
        conn.execute("DELETE FROM files_fts")
        for root in roots:
            if not root or not isinstance(root, Path):
                continue
            if not root.exists() or not root.is_dir():
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [
                    d for d in dirnames
                    if d not in {".git", "node_modules", "__pycache__"}
                    and not d.startswith(".")
                ]
                for filename in filenames:
                    full_path = Path(dirpath) / filename
                    if not full_path.is_file():
                        continue
                    try:
                        stat = full_path.stat()
                    except OSError:
                        continue
                    name = full_path.name
                    ext = full_path.suffix.lower().lstrip(".")
                    project = root.name or ""
                    conn.execute(
                        "INSERT INTO files(path, name, ext, mtime, project) VALUES (?, ?, ?, ?, ?)",
                        (str(full_path), name, ext, float(stat.st_mtime), project),
                    )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def query(text: str, max_results: int = 5) -> list[dict]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    conn = _connect()
    try:
        matcher = " ".join(cleaned.split())
        query_text = matcher.replace('"', ' ')
        rows = conn.execute(
            """
            SELECT f.name, f.path, f.mtime, 1.0 AS score
            FROM files_fts AS fts
            JOIN files AS f ON f.rowid = fts.rowid
            WHERE files_fts MATCH ?
            ORDER BY f.mtime DESC
            LIMIT ?
            """,
            (query_text, max_results),
        ).fetchall()

        results: list[dict] = []
        for name, path, mtime, score in rows:
            results.append({
                "name": name,
                "path": path,
                "score": float(score) if score is not None else 1.0,
                "mtime": float(mtime) if mtime is not None else 0.0,
            })
        return results
    except Exception:
        return []
    finally:
        conn.close()


__all__ = ["DB_PATH", "index_exists", "rebuild_index", "query"]
