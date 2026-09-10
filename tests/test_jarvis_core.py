"""
tests/test_jarvis_core.py
Roda com: python -m pytest tests/ -v
"""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.crypto_vault import (
    decrypt_archive,
    decrypt_bytes,
    decrypt_file,
    encrypt_archive,
    encrypt_bytes,
    encrypt_file,
)


def test_encrypt_decrypt_bytes_roundtrip():
    data = b"JARVIS test payload \x00\xFF"
    enc = encrypt_bytes(data, "senha_teste")
    assert enc != data
    assert decrypt_bytes(enc, "senha_teste") == data


def test_decrypt_bytes_wrong_password():
    enc = encrypt_bytes(b"segredo", "correta")
    with pytest.raises(Exception):
        decrypt_bytes(enc, "errada")


def test_encrypt_decrypt_file_roundtrip(tmp_path):
    plain = tmp_path / "plain.json"
    enc = tmp_path / "plain.enc"
    payload = {"gemini_api_key": "gsk_test", "groq_api_key": "sk_test"}
    plain.write_text(json.dumps(payload), encoding="utf-8")

    encrypt_file(plain, enc, "senha123")
    assert enc.exists()
    assert decrypt_file(enc, "senha123") == payload


def test_decrypt_file_wrong_password(tmp_path):
    plain = tmp_path / "k.enc"
    source = tmp_path / "k.json"
    source.write_text('{"x": 1}', encoding="utf-8")
    encrypt_file(source, plain, "certa")
    with pytest.raises(Exception):
        decrypt_file(plain, "errada")


def test_encrypt_archive_roundtrip(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')", encoding="utf-8")
    (src / "sub").mkdir()
    (src / "sub" / "note.md").write_text("# Nota", encoding="utf-8")

    out = tmp_path / "vault.enc"
    encrypt_archive(src, out, "senha_vault")
    dst = tmp_path / "dst"
    decrypt_archive(out, dst, "senha_vault")
    assert (dst / "main.py").read_text() == "print('hello')"
    assert (dst / "sub" / "note.md").read_text() == "# Nota"


def test_encrypt_archive_wrong_password(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "f.txt").write_text("x")
    out = tmp_path / "v.enc"
    encrypt_archive(src, out, "ok")
    with pytest.raises(Exception):
        decrypt_archive(out, tmp_path / "dst", "wrong")


def test_pbkdf2_deterministic():
    from core.crypto_vault import _derive_key
    assert _derive_key("abc") == _derive_key("abc")
    assert _derive_key("abc") != _derive_key("ABC")


import core.knowledge_vault as kv_module


@pytest.fixture(autouse=True)
def tmp_knowledge_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(kv_module, "KNOWLEDGE_DIR", tmp_path)
    yield tmp_path


def test_write_and_read_note():
    kv_module.write_note("teste", "conteúdo da nota")
    assert kv_module.read_note("teste") == "conteúdo da nota\n"


def test_append_note():
    kv_module.write_note("log", "linha 1")
    kv_module.write_note("log", "linha 2", append=True)
    content = kv_module.read_note("log")
    assert "linha 1" in content
    assert "linha 2" in content


def test_read_nonexistent_note():
    result = kv_module.read_note("nao_existe")
    assert "não encontrada" in result.lower()


def test_list_notes_empty():
    assert kv_module.list_notes() == []


def test_list_notes_populated():
    kv_module.write_note("a", "x")
    kv_module.write_note("b", "y")
    assert sorted(kv_module.list_notes()) == ["a", "b"]


def test_search_finds_match():
    kv_module.write_note("demo", "Matt Murdock é o Demolidor")
    assert "demo" in kv_module.search_notes("Demolidor")


def test_search_no_match():
    kv_module.write_note("nota", "conteúdo irrelevante")
    assert "Nada encontrado" in kv_module.search_notes("Thanos")


def test_unicode_note_name():
    kv_module.write_note("Revisão_Cálculo", "derivada de x²")
    assert kv_module.read_note("Revisão_Cálculo") == "derivada de x²\n"


def test_invalid_note_name():
    with pytest.raises(ValueError):
        kv_module.write_note("../../etc/passwd", "exploit")


from core.sync_manager import _obfuscate_key, _resolve_password


def test_resolve_password_uses_manual_if_set():
    cfg = {"supabase_service_key": "sk_abc", "sync_password": "manual_pw"}
    assert _resolve_password(cfg) == "manual_pw"


def test_resolve_password_derives_from_service_key():
    cfg = {"supabase_service_key": "sk_abc"}
    pw = _resolve_password(cfg)
    assert isinstance(pw, str) and len(pw) == 64


def test_resolve_password_deterministic():
    cfg = {"supabase_service_key": "sk_abc"}
    assert _resolve_password(cfg) == _resolve_password(cfg)


def test_resolve_password_different_keys_differ():
    assert _resolve_password({"supabase_service_key": "sk_1"}) != _resolve_password({"supabase_service_key": "sk_2"})


def test_resolve_password_missing_key_raises():
    with pytest.raises(RuntimeError):
        _resolve_password({})


def test_obfuscate_key_deterministic():
    assert _obfuscate_key("knowledge/nota.md") == _obfuscate_key("knowledge/nota.md")


def test_obfuscate_key_different_inputs():
    assert _obfuscate_key("a.md") != _obfuscate_key("b.md")


def test_obfuscate_key_hides_filename():
    key = _obfuscate_key("Senha_banco_itau.md")
    assert "Senha" not in key
    assert "itau" not in key
