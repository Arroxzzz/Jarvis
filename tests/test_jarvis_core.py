"""
tests/test_jarvis_core.py
Roda com: python -m pytest tests/ -v
"""
import json
from pathlib import Path
import sys
import time

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


def test_obsidian_vault_is_configured():
    assert kv_module.OBSIDIAN_VAULT == Path(r"D:\MEMORIA_JARVIS")


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


@pytest.mark.asyncio
async def test_run_tool_bound_timeout_message():
    from main import _run_tool_bound

    result = await _run_tool_bound(lambda: time.sleep(0.2) or "ok", 0.05, "demo")
    assert "demo excedeu" in result
    assert "cancelado" in result


def test_resilient_text_call_falls_back_after_groq_retry_after(monkeypatch):
    import core.llm_client as llm_client

    def fake_call_llm_text(prompt, system=None, model=None, timeout=120, force_provider=None):
        if force_provider == "groq":
            raise llm_client.ProviderRequestError("groq", "429 Too Many Requests", 429, 7)
        return "fallback-ok"

    monkeypatch.setattr(llm_client, "call_llm_text", fake_call_llm_text)
    result = llm_client.resilient_text_call("teste", system="sys", task_type="general", timeout=15)
    assert result == "fallback-ok"


def test_provider_circuit_breaker_tracks_retry_window(monkeypatch):
    import core.llm_client as llm_client

    llm_client._PROVIDER_STATE.clear()
    exc = llm_client.ProviderRequestError("openrouter", "429 Too Many Requests", 429, 9)
    llm_client._register_provider_failure("openrouter", exc)

    assert llm_client._provider_is_open("openrouter") is False
    assert llm_client._provider_next_retry("openrouter") > 0


def test_background_panel_result_is_only_reinjected_once():
    from main import JarvisLive

    live = object.__new__(JarvisLive)
    live._panel_context_cache = {}

    first = live._panel_result_already_seen("SEARCH", "resultado ABC")
    second = live._panel_result_already_seen("SEARCH", "resultado ABC")
    third = live._panel_result_already_seen("SEARCH", "resultado XYZ")

    assert first is False
    assert second is True
    assert third is False


def test_audio_queue_snapshot_reports_backlog_and_underrun():
    import asyncio
    from main import JarvisLive

    live = object.__new__(JarvisLive)
    live.audio_in_queue = asyncio.Queue()
    live.out_queue = asyncio.Queue()
    live.audio_in_queue.put_nowait(b"a")
    live.audio_in_queue.put_nowait(b"b")
    live.out_queue.put_nowait({"data": b"c"})

    data = live._audio_queue_snapshot("play")
    assert data["in_q"] == 2
    assert data["out_q"] == 1
    assert data["underrun"] in (0, 1)


def test_file_delete_requires_explicit_confirmation(tmp_path):
    from actions.file_controller import file_controller

    target = tmp_path / "delete_me.txt"
    target.write_text("x", encoding="utf-8")

    result = file_controller({"action": "delete", "path": str(tmp_path), "name": "delete_me.txt"})
    assert "confirm" in result.lower()

    confirm = file_controller({"action": "delete", "path": str(tmp_path), "name": "delete_me.txt", "confirmed": "yes"})
    assert "delete" in confirm.lower() or "removed" in confirm.lower() or "trash" in confirm.lower()


def test_runtime_config_reads_key_and_writes_cache(tmp_path):
    from core.runtime_config import get_api_key, read_config, write_config_key

    config_path = tmp_path / "api_keys.json"
    config_path.write_text('{"gemini_api_key": "test-key"}', encoding="utf-8")

    assert get_api_key(config_path) == "test-key"
    write_config_key(config_path, "live_model_id_cache", "models/test-live")
    assert read_config(config_path)["live_model_id_cache"] == "models/test-live"


def test_runtime_config_prompt_falls_back_when_missing(tmp_path):
    from core.runtime_config import DEFAULT_SYSTEM_PROMPT, load_system_prompt

    assert load_system_prompt(tmp_path / "missing-prompt.txt") == DEFAULT_SYSTEM_PROMPT
