"""
tests/test_jarvis_core.py
Roda com: python -m pytest tests/ -v
"""
import asyncio
from pathlib import Path
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.crypto_vault import (
    decrypt_bytes,
    encrypt_bytes,
)


@pytest.fixture(autouse=True)
def reset_confirmation_gate(tmp_path, monkeypatch):
    from core import write_guard

    base = tmp_path / "base"
    monkeypatch.setattr(write_guard, "get_base_dir", lambda: base)
    write_guard._pending = None
    write_guard._last_done = None
    yield
    write_guard._pending = None
    write_guard._last_done = None


def test_encrypt_decrypt_bytes_roundtrip():
    data = b"JARVIS test payload \x00\xFF"
    enc = encrypt_bytes(data, "senha_teste")
    assert enc != data
    assert decrypt_bytes(enc, "senha_teste") == data


def test_decrypt_bytes_wrong_password():
    enc = encrypt_bytes(b"segredo", "correta")
    with pytest.raises(Exception):
        decrypt_bytes(enc, "errada")


def test_pbkdf2_deterministic():
    from core.crypto_vault import _derive_key
    assert _derive_key("abc") == _derive_key("abc")
    assert _derive_key("abc") != _derive_key("ABC")


def test_plugin_desconhecido_nasce_desligado():
    from memory.config_manager import get_plugin_enabled
    assert get_plugin_enabled("plugin_de_terceiro_nunca_visto") is False


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


def test_search_matches_note_title_and_content():
    kv_module.write_note(
        "Instrução de Salvamento Padrão",
        "Instrução permanente: comandos como 'guarda isso' devem salvar.",
    )
    assert "Instrução de Salvamento Padrão" in kv_module.search_notes(
        "Instrução de Salvamento Padrão"
    )
    assert "Instrução de Salvamento Padrão" in kv_module.search_notes("comandos como")


def test_search_no_match():
    kv_module.write_note("nota", "conteúdo irrelevante")
    assert "Nada encontrado" in kv_module.search_notes("Thanos")


def test_search_context_returns_relevant_note_and_snippet():
    kv_module.write_note("Projeto_Jarvis", "A decisão foi manter a memória local em Obsidian e validar a recuperação contextual.")
    results = kv_module.search_context("recuperação contextual")

    assert len(results) >= 1
    assert results[0]["title"] == "Projeto_Jarvis"
    assert "Obsidian" in results[0]["snippet"]
    assert "recuperação contextual" in results[0]["snippet"].lower()


def test_search_context_empty_query_returns_empty_list():
    assert kv_module.search_context("   ") == []


def test_build_memory_context_formats_context_for_prompt():
    kv_module.write_note("Projeto_Jarvis", "A decisão foi manter a memória local em Obsidian e validar a integração mínima.")
    context = kv_module.build_memory_context("integração mínima")

    assert "[MEMÓRIA LOCAL RELEVANTE]" in context
    assert "Projeto_Jarvis" in context
    assert "Obsidian" in context


def test_context_resolver_finds_recent_file_by_name(tmp_path):
    from core.context_resolver import find_context_candidates

    desktop = tmp_path / "Desktop"
    downloads = tmp_path / "Downloads"
    desktop.mkdir()
    downloads.mkdir()

    target = desktop / "jarvis_relatorio_final.pdf"
    target.write_text("ok", encoding="utf-8")
    older = downloads / "arquivo_qualquer.txt"
    older.write_text("x", encoding="utf-8")

    candidates = find_context_candidates("relatorio final", roots=[desktop, downloads], max_results=5)

    assert candidates
    assert candidates[0]["name"] == "jarvis_relatorio_final.pdf"
    assert candidates[0]["path"].endswith("jarvis_relatorio_final.pdf")


def test_context_resolver_returns_empty_when_no_match(tmp_path):
    from core.context_resolver import find_context_candidates

    desktop = tmp_path / "Desktop"
    desktop.mkdir()
    (desktop / "notes.txt").write_text("nada", encoding="utf-8")

    candidates = find_context_candidates("abacaxi gigante", roots=[desktop], max_results=5)
    assert candidates == []


def test_context_resolver_uses_default_roots_when_none_provided(monkeypatch, tmp_path):
    from core.context_resolver import find_context_candidates

    home = tmp_path / "home"
    desktop = home / "Desktop"
    downloads = home / "Downloads"
    desktop.mkdir(parents=True)
    downloads.mkdir(parents=True)

    target = desktop / "relatorio_final_jan_2026.pdf"
    target.write_text("ok", encoding="utf-8")
    other = downloads / "arquivo_qualquer.txt"
    other.write_text("x", encoding="utf-8")

    monkeypatch.setattr("pathlib.Path.home", lambda: home)

    candidates = find_context_candidates("relatorio final pdf")
    assert candidates
    assert candidates[0]["name"] == "relatorio_final_jan_2026.pdf"


def test_context_resolver_default_roots_include_vault(monkeypatch, tmp_path):
    import core.context_resolver as resolver
    from core.knowledge_vault import OBSIDIAN_VAULT

    monkeypatch.setattr(resolver, "OBSIDIAN_VAULT", OBSIDIAN_VAULT)
    assert OBSIDIAN_VAULT in resolver._default_roots()


def test_context_resolver_finds_vault_note_without_explicit_roots(monkeypatch, tmp_path):
    import core.context_resolver as resolver

    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "Nota_Teste.md"
    note.write_text("Instrução de salvamento", encoding="utf-8")
    home = tmp_path / "home"
    monkeypatch.setattr(resolver, "OBSIDIAN_VAULT", vault)
    monkeypatch.setattr("pathlib.Path.home", lambda: home)
    monkeypatch.setattr(resolver.context_index, "index_exists", lambda: False)

    candidates = resolver.find_context_candidates("nota teste")
    assert any(candidate["path"] == str(note) for candidate in candidates)


def test_context_resolver_prefers_exact_extension_and_name_overlap(tmp_path):
    from core.context_resolver import find_context_candidates

    root = tmp_path / "Desktop"
    root.mkdir()

    broad = root / "ideia_relatorio.txt"
    broad.write_text("broad", encoding="utf-8")
    precise = root / "relatorio_final.pdf"
    precise.write_text("exact", encoding="utf-8")

    candidates = find_context_candidates("relatorio final pdf", roots=[root], max_results=5)
    assert candidates[0]["name"] == "relatorio_final.pdf"
    assert candidates[0]["score"] >= candidates[1]["score"]


def test_context_resolver_flags_ambiguous_candidates(tmp_path):
    from core.context_resolver import resolve_context

    root = tmp_path / "Downloads"
    root.mkdir()
    (root / "relatorio_final.pdf").write_text("a", encoding="utf-8")
    (root / "relatorio_final.docx").write_text("b", encoding="utf-8")

    result = resolve_context("relatorio final", roots=[root])

    assert result["needs_confirmation"] is True
    assert len(result["candidates"]) >= 2


def test_context_index_builds_and_queries_files(tmp_path):
    from core.context_index import index_exists, query, rebuild_index

    root = tmp_path / "Desktop"
    root.mkdir()
    target = root / "relatorio_final_2026.pdf"
    target.write_text("novo relatório", encoding="utf-8")

    rebuild_index([root])

    assert index_exists() is True
    hits = query("relatorio final", max_results=5)
    assert hits
    assert hits[0]["name"] == "relatorio_final_2026.pdf"


def test_infer_active_project_detects_local_repo(tmp_path):
    import core.context_resolver as ccr

    root = tmp_path / "Desktop"
    project = root / "jarvis_project"
    project.mkdir(parents=True)
    (project / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (project / "README.md").write_text("Projeto Jarvis\n", encoding="utf-8")
    (project / ".git").mkdir()

    result = ccr.infer_active_project(roots=[root], active_window_title="jarvis_project - VS Code")

    assert result["project_name"] == "jarvis_project"
    assert result["path"].endswith("jarvis_project")
    assert result["confidence"] >= 0.8


def test_build_project_context_includes_project_summary(tmp_path):
    import core.context_resolver as ccr

    root = tmp_path / "Desktop"
    project = root / "jarvis_project"
    project.mkdir(parents=True)
    (project / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (project / "README.md").write_text("Projeto Jarvis\n", encoding="utf-8")
    (project / ".git").mkdir()

    context = ccr.build_project_context(roots=[root], active_window_title="jarvis_project - VS Code")

    assert "jarvis_project" in context
    assert "Projeto ativo" in context
    assert "VS Code" in context


def test_proactive_is_disabled_by_default():
    from datetime import datetime
    from actions.proactive import ProactiveEngine

    engine = ProactiveEngine()
    assert engine.enabled is False
    assert engine.due_trigger(datetime(2026, 1, 1, 3, 0), mono=99999.0) is None


def test_proactive_rules_use_local_session_and_time():
    from datetime import datetime
    from actions.proactive import ProactiveEngine

    late = ProactiveEngine(enabled=True)
    late.observe(0, mono=0)
    assert late.due_trigger(datetime(2026, 1, 1, 3, 0), mono=4 * 3600) == "late_night"

    daytime = ProactiveEngine(enabled=True)
    daytime.observe(0, mono=0)
    dt = datetime(2026, 1, 1, 12, 0)
    assert daytime.due_trigger(dt, mono=4 * 3600) is None
    assert daytime.due_trigger(dt, mono=6 * 3600) == "long_session"


def test_proactive_limits_rule_frequency_per_hour_and_day():
    from datetime import datetime
    from actions.proactive import ProactiveEngine

    engine = ProactiveEngine(enabled=True)
    engine.observe(0, mono=0)
    dt = datetime(2026, 1, 1, 3, 30)
    fired_at = 6.5 * 3600
    assert engine.due_trigger(dt, mono=fired_at) == "late_night"
    engine.mark_fired("late_night", dt, mono=fired_at)
    assert engine.due_trigger(dt, mono=fired_at + 1) is None
    assert engine.due_trigger(dt, mono=fired_at + 3599) is None
    assert engine.due_trigger(dt, mono=fired_at + 3600) == "long_session"

    next_day = ProactiveEngine(enabled=True)
    next_day.observe(0, mono=0)
    first_day = datetime(2026, 1, 1, 3, 0)
    assert next_day.due_trigger(first_day, mono=4 * 3600) == "late_night"
    next_day.mark_fired("late_night", first_day, mono=4 * 3600)
    assert next_day.due_trigger(
        datetime(2026, 1, 2, 3, 0), mono=28 * 3600
    ) == "late_night"


def test_proactive_observe_resets_after_idle_and_ignores_unavailable_sensor():
    from datetime import datetime
    from actions.proactive import ProactiveEngine

    engine = ProactiveEngine(enabled=True)
    engine.observe(0, mono=100)
    start = engine._session_start
    engine.observe(-1.0, mono=200)
    assert engine._session_start == start
    engine.observe(700, mono=4 * 3600)
    assert engine.session_seconds(mono=10 * 3600) == 0
    assert engine.due_trigger(datetime(2026, 1, 1, 3, 0), mono=10 * 3600) is None


def test_proactive_build_prompt_contains_rule_fact():
    from datetime import datetime
    from actions.proactive import ProactiveEngine

    engine = ProactiveEngine(enabled=True)
    engine.observe(0, mono=0)
    prompt = engine.build_prompt("late_night", datetime(2026, 1, 1, 3, 0), mono=4 * 3600)
    assert "PROACTIVE_CHECK" in prompt
    assert "03:00" in prompt
    assert "4h" in prompt
    assert "Não chame ferramentas" in prompt


def test_hw_sensors_report_unsupported_platform(monkeypatch):
    import core.hw_sensors as sensors

    monkeypatch.setattr(sensors, "_OS", "Linux")
    assert sensors.get_idle_seconds() == -1.0
    assert sensors.is_foreground_fullscreen() is False


def test_jarvis_set_proactive_persists_only_state_changes(monkeypatch):
    import main
    from actions.proactive import ProactiveEngine
    from main import JarvisLive

    live = object.__new__(JarvisLive)
    live._proactive = ProactiveEngine()
    calls = []
    monkeypatch.setattr(main, "_write_config_key", lambda key, value: calls.append((key, value)))

    assert live.set_proactive("on") == "Proatividade ativada."
    assert live._proactive.enabled is True
    assert calls == [("proactive_enabled", True)]
    assert live.set_proactive("off") == "Proatividade desativada."
    assert live._proactive.enabled is False
    assert calls == [("proactive_enabled", True), ("proactive_enabled", False)]
    assert live.set_proactive("status") == "Proatividade desativada."
    assert len(calls) == 2


def test_proactive_mode_tool_delegates_to_jarvis():
    from core.tool_registry import _proactive_mode_tool

    class FakeJarvis:
        def __init__(self):
            self.states = []

        def set_proactive(self, state):
            self.states.append(state)
            return f"state={state}"

    jarvis = FakeJarvis()
    assert _proactive_mode_tool({"state": "on"}, jarvis=jarvis) == "state=on"
    assert jarvis.states == ["on"]
    assert _proactive_mode_tool({"state": "on"}) == "Proatividade indisponível."


def test_runtime_declares_context_tool():
    import main

    names = {tool["name"] for tool in main.TOOL_DECLARATIONS}
    assert "find_context" in names


def test_tool_registry_declares_core_tools():
    from core.tool_registry import get_declarations

    names = {tool["name"] for tool in get_declarations()}
    assert {
        "open_app", "weather_report", "web_search", "computer_settings",
        "file_controller", "proactive_mode",
    }.issubset(names)


def test_active_window_title_uses_windows_api(monkeypatch):
    import core.context_resolver as ccr

    class FakeWinDLL:
        def __init__(self):
            self.user32 = self
        def GetForegroundWindow(self):
            return 42
        def GetWindowTextLengthW(self, hwnd):
            return len("Relatório - Excel")
        def GetWindowTextW(self, hwnd, buffer, length):
            buffer.value = "Relatório - Excel"
            return len("Relatório - Excel")

    monkeypatch.setattr(ccr.platform, "system", lambda: "Windows")
    monkeypatch.setattr("ctypes.windll", FakeWinDLL(), raising=False)

    title = ccr.get_active_window_title()
    assert title == "Relatório - Excel"


def test_extract_context_query_detects_file_requests():
    import main

    obj = main.JarvisLive.__new__(main.JarvisLive)
    assert obj._extract_context_query("ache o relatório final") == "relatório final"
    assert obj._extract_context_query("localiza o pdf da reunião") == "reunião"
    assert obj._extract_context_query("como está o tempo") is None


def test_maybe_attach_context_hint_includes_local_context_for_file_lookup(monkeypatch):
    import main

    class FakeResult(dict):
        pass

    fake = FakeResult({
        "candidates": [{"name": "relatorio_final.pdf", "path": "C:/Users/Test/Desktop/relatorio_final.pdf"}],
        "best_match": {"name": "relatorio_final.pdf", "path": "C:/Users/Test/Desktop/relatorio_final.pdf"},
        "needs_confirmation": False,
    })
    monkeypatch.setattr("core.context_resolver.resolve_context", lambda *args, **kwargs: fake)

    obj = main.JarvisLive.__new__(main.JarvisLive)
    result = obj._maybe_attach_context_hint("ache o relatório final")
    assert "relatorio_final.pdf" in result
    assert "CONTEXTO_LOCAL" in result
    assert "C:/" not in result
    assert "área de trabalho" in result.lower() or "downloads" in result.lower() or "documentos" in result.lower()


def test_resolve_context_hides_full_paths_from_user_facing_response():
    from core.context_resolver import resolve_context
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "knowledge"
    result = resolve_context("Lembrete", roots=[root], max_results=3)

    assert result["best_match"] is not None
    assert "C:/" not in str(result["best_match"]["path"])
    assert "Lembrete" in result["best_match"]["name"] or result["best_match"]["name"]


def test_unicode_note_name():
    kv_module.write_note("Revisão_Cálculo", "derivada de x²")
    assert kv_module.read_note("Revisão_Cálculo") == "derivada de x²\n"


def test_invalid_note_name():
    with pytest.raises(ValueError):
        kv_module.write_note("../../etc/passwd", "exploit")


def test_resolve_vault_dir_uses_config_when_set():
    cfg = {"vault_path": r"D:\Memoria_Jarvis"}
    assert kv_module._resolve_vault_dir(cfg, Path("/qualquer")) == Path(r"D:\Memoria_Jarvis")


def test_resolve_vault_dir_falls_back_when_unset():
    assert kv_module._resolve_vault_dir({}, Path("/home/paulo")) == Path("/home/paulo/JarvisVault")


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

    llm_client._PROVIDER_STATE.clear()

    def fake_call_llm_text(prompt, system=None, model=None, timeout=120, force_provider=None, **kwargs):
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
    from core.background_tasks import BackgroundTaskTracker

    tracker = BackgroundTaskTracker()

    first = tracker.result_already_seen("SEARCH", "resultado ABC")
    second = tracker.result_already_seen("SEARCH", "resultado ABC")
    third = tracker.result_already_seen("SEARCH", "resultado XYZ")

    assert first is False
    assert second is True
    assert third is False


def test_call_llm_text_rejects_empty_and_optional_truncation(monkeypatch):
    import core.llm_client as lc

    class FakeResponse:
        def __init__(self, content, finish_reason="stop"):
            self.content = content
            self.finish_reason = finish_reason

        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{
                "message": {"content": self.content},
                "finish_reason": self.finish_reason,
            }]}

    payloads = []
    current = {"content": "", "finish_reason": "stop"}

    def fake_post(url, *, json, **kwargs):
        payloads.append(json)
        return FakeResponse(**current)

    monkeypatch.setattr(lc, "_has_key", lambda provider: True)
    monkeypatch.setattr(lc, "_auth_headers", lambda provider=None: {})
    monkeypatch.setattr(lc.requests, "post", fake_post)

    with pytest.raises(RuntimeError, match="resposta vazia"):
        lc.call_llm_text("prompt", force_provider="groq")

    current.update(content="trecho", finish_reason="length")
    with pytest.raises(RuntimeError, match="cortada"):
        lc.call_llm_text("prompt", force_provider="groq", fail_on_length=True)
    assert lc.call_llm_text("prompt", force_provider="groq", fail_on_length=False) == "trecho"
    lc.call_llm_text("prompt", force_provider="groq", max_tokens=4321)
    assert payloads[-1]["max_tokens"] == 4321


def test_resilient_text_call_retries_empty_and_supports_raise_on_fail(monkeypatch):
    import core.llm_client as lc

    lc._PROVIDER_STATE.clear()
    attempts = []

    def fake_call(prompt, **kwargs):
        attempts.append(kwargs)
        if len(attempts) == 1:
            raise RuntimeError("resposta vazia")
        return "ok"

    monkeypatch.setattr(lc, "call_llm_text", fake_call)
    assert lc.resilient_text_call("prompt", task_type="code") == "ok"
    assert len(attempts) == 2
    assert attempts[0]["max_tokens"] == 4000
    assert attempts[0]["fail_on_length"] is True

    monkeypatch.setattr(lc, "call_llm_text", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline")))
    assert lc.resilient_text_call("prompt") == lc.LLM_FAIL_MSG
    with pytest.raises(lc.LLMUnavailableError, match="provedores"):
        lc.resilient_text_call("prompt", raise_on_fail=True)


def test_backup_file_copies_original_and_skips_missing(tmp_path, monkeypatch):
    from core import write_guard

    base = tmp_path / "base"
    monkeypatch.setattr(write_guard, "get_base_dir", lambda: base)
    original = tmp_path / "important.txt"
    original.write_text("original", encoding="utf-8")

    backup = write_guard.backup_file(original)
    assert backup is not None
    assert backup.read_text(encoding="utf-8") == "original"
    assert backup.parent == base / "memory" / "backups"
    assert write_guard.backup_file(tmp_path / "missing.txt") is None


def test_code_helper_save_file_backs_up_and_rejects_empty(tmp_path, monkeypatch):
    from actions import code_helper

    monkeypatch.setattr(code_helper.write_guard, "get_base_dir", lambda: tmp_path / "base")
    target = tmp_path / "project" / "file.py"
    target.parent.mkdir(parents=True)
    target.write_text("velho", encoding="utf-8")

    result = code_helper._save_file(target, "novo")
    assert result.startswith("Saved to:")
    assert target.read_text(encoding="utf-8") == "novo"
    backups = list((tmp_path / "base" / "memory" / "backups").glob("*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "velho"

    assert code_helper._save_file(target, " \n") == "Could not save: conteúdo vazio."
    assert target.read_text(encoding="utf-8") == "novo"


def test_llm_payload_sets_reasoning_options_and_diagnostic(monkeypatch):
    import core.llm_client as lc

    payloads = []
    current = {"content": "ok", "finish_reason": "stop"}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            if current["content"] == "":
                return {
                    "choices": [{
                        "message": {"content": ""},
                        "finish_reason": "length",
                    }],
                    "usage": {
                        "completion_tokens": 12,
                        "completion_tokens_details": {"reasoning_tokens": 9},
                    },
                }
            return {"choices": [{
                "message": {"content": current["content"]},
                "finish_reason": current["finish_reason"],
            }]}

    def fake_post(url, *, json, **kwargs):
        payloads.append(json)
        return FakeResponse()

    monkeypatch.setattr(lc, "_has_key", lambda provider: True)
    monkeypatch.setattr(lc, "_auth_headers", lambda provider=None: {})
    monkeypatch.setattr(lc.requests, "post", fake_post)

    lc.call_llm_text("prompt", model="openai/gpt-oss-20b", force_provider="groq", reasoning_effort="low")
    assert payloads[-1]["reasoning_effort"] == "low"
    lc.call_llm_text("prompt", model="glm", force_provider="openrouter", reasoning_effort="low")
    assert payloads[-1]["reasoning"] == {"effort": "low"}
    lc.call_llm_text("prompt", model="openai/gpt-oss-20b", force_provider="groq")
    assert "reasoning_effort" not in payloads[-1]
    assert "reasoning" not in payloads[-1]

    current["content"] = ""
    with pytest.raises(lc.LLMOutputError) as exc:
        lc.call_llm_text("prompt", force_provider="groq")
    assert "finish=" in str(exc.value)
    assert "out=" in str(exc.value)


def test_resilient_text_call_breaker_is_per_model(monkeypatch):
    import core.llm_client as lc

    lc._PROVIDER_STATE.clear()
    attempted = []

    def fake_call(prompt, model, force_provider, **kwargs):
        attempted.append(model)
        if model == "openai/gpt-oss-120b":
            raise lc.ProviderRequestError("groq", "429", 429, 30)
        return "ok"

    monkeypatch.setattr(lc, "call_llm_text", fake_call)
    assert lc.resilient_text_call("prompt", task_type="code") == "ok"
    assert attempted == ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]


def test_dev_agent_orders_files_by_dependencies():
    from actions.dev_agent import _order_files

    files = [
        {"path": "main.py", "imports": ["core.engine"]},
        {"path": "core/engine.py", "imports": ["core.game", "utils.helpers"]},
        {"path": "core/game.py", "imports": ["utils.helpers"]},
        {"path": "utils/helpers.py", "imports": []},
    ]
    assert [f["path"] for f in _order_files(files)] == [
        "utils/helpers.py", "core/game.py", "core/engine.py", "main.py",
    ]


def test_dev_agent_auto_install_allowlist_and_project_modules(tmp_path, monkeypatch):
    from actions import dev_agent

    core = tmp_path / "core"
    core.mkdir()
    monkeypatch.setattr(
        dev_agent.subprocess, "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("pip não deveria rodar")),
    )
    assert not dev_agent._try_auto_install("No module named 'core.engine'", tmp_path)
    assert not dev_agent._try_auto_install("No module named 'pacote_inventado'", tmp_path)

    calls = []

    class Result:
        returncode = 0

    monkeypatch.setattr(dev_agent.subprocess, "run", lambda *args, **kwargs: calls.append(args[0]) or Result())
    assert dev_agent._try_auto_install("No module named 'pygame'", tmp_path)
    assert calls[-1][-2:] == ["install", "pygame"]


def test_dev_agent_dependency_install_filters_unknown_packages(monkeypatch, tmp_path):
    from actions import dev_agent

    calls = []

    class Result:
        returncode = 1
        stderr = ""

    def fake_run(command, **kwargs):
        calls.append(command)
        return Result()

    monkeypatch.setattr(dev_agent.subprocess, "run", fake_run)
    dev_agent._install_dependencies(["pygame", "pacote_inventado"], tmp_path)
    installs = [cmd for cmd in calls if "install" in cmd]
    assert len(installs) == 1
    assert "pygame" in installs[0]
    assert "pacote_inventado" not in installs[0]


def test_web_search_returns_untrusted_raw_ddg_results_without_llm(monkeypatch):
    from actions import web_search
    evidence = [{"title": "Fato atual", "snippet": "Resultado encontrado", "url": "https://example.test"}]
    monkeypatch.setattr(web_search, "_ddg_search", lambda query, max_results=6: evidence)
    monkeypatch.setattr(
        web_search, "resilient_text_call",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("LLM chamado")),
    )
    result = web_search._search("x")
    assert result.startswith(web_search._UNTRUSTED)
    assert "Resultado encontrado" in result

    monkeypatch.setattr(web_search, "_search", lambda query: "resultado cru")
    assert web_search.web_search({"query": "x", "mode": "price"}) == "resultado cru"
    assert not hasattr(web_search, "_price")


def test_web_news_never_uses_llm_without_ddg_results(monkeypatch):
    from actions import web_search

    monkeypatch.setattr(web_search, "_ddg_news", lambda query, max_results=8: [])
    monkeypatch.setattr(
        web_search, "resilient_text_call",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("LLM chamado")),
    )
    assert web_search._news("notícias").startswith("No news found")


def test_file_controller_resolves_unique_extension_match(tmp_path, monkeypatch):
    from actions import file_controller

    source = tmp_path / "TESTE123.py"
    source.write_text("conteúdo", encoding="utf-8")
    assert file_controller.resolve_existing(str(tmp_path / "TESTE123")) == source
    assert file_controller.resolve_existing(str(tmp_path / "TESTE123.txt")) == source

    ambiguous = tmp_path / "ambiguous.py"
    (tmp_path / "ambiguous.md").write_text("doc", encoding="utf-8")
    ambiguous.write_text("code", encoding="utf-8")
    requested = tmp_path / "ambiguous.txt"
    assert file_controller.resolve_existing(str(requested)) == requested

    monkeypatch.setattr(file_controller, "_is_safe_path", lambda path: True)
    assert file_controller.file_controller({
        "action": "read", "path": str(tmp_path), "name": "TESTE123",
    }) == "conteúdo"


def test_flight_finder_uses_fallback_parser_without_fixed_dates(monkeypatch):
    from actions import flight_finder
    import core.llm_client as lc

    url = flight_finder._build_google_flights_url("IST", "LHR", "2026-10-01")
    assert "tfs=" not in url

    monkeypatch.setattr(lc, "resilient_text_call", lambda *args, **kwargs: '[{"airline":"Test Air"}]')
    assert flight_finder._parse_flights_with_gemini("page", "IST", "LHR", "2026-10-01") == [
        {"airline": "Test Air"}
    ]
    monkeypatch.setattr(lc, "resilient_text_call", lambda *args, **kwargs: lc.LLM_FAIL_MSG)
    assert flight_finder._parse_flights_with_gemini("page", "IST", "LHR", "2026-10-01") == []


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


def test_file_delete_requires_explicit_confirmation(tmp_path, monkeypatch):
    import actions.file_controller as file_controller_module
    from core import write_guard

    target = tmp_path / "delete_me.txt"
    target.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        file_controller_module,
        "_safe_trash",
        lambda path: (path.unlink(), f"Moved to Trash: {path.name}")[1],
    )

    result = file_controller_module.file_controller(
        {"action": "delete", "path": str(tmp_path), "name": "delete_me.txt"}
    )
    assert "[AGUARDANDO_CONFIRMACAO]" in result
    assert target.exists()

    confirm = file_controller_module.file_controller(
        {"action": "delete", "path": str(tmp_path), "name": "delete_me.txt", "confirmed": "yes"}
    )
    assert "[AGUARDANDO_CONFIRMACAO]" in confirm
    assert target.exists()

    assert write_guard.on_turn_complete("", None) is None
    decision = write_guard.on_turn_complete("Confirmo.", time.monotonic())
    assert decision[0] == "confirm"
    decision[1]["run"]()
    assert not target.exists()


def test_file_actions_use_human_friendly_names(tmp_path):
    from actions.file_controller import delete_file

    target = tmp_path / "config da shaders.txt"
    target.write_text("x", encoding="utf-8")

    result = delete_file(str(tmp_path), name="config da shaders.txt")

    assert "config da shaders.txt" in result.lower()
    assert str(tmp_path) not in result
    assert "lixeira" in result.lower() or "trash" in result.lower()


def test_open_folder_does_not_require_confirmation(tmp_path):
    from actions.file_controller import open_folder

    target = tmp_path / "pasta_para_abrir"
    target.mkdir()

    result = open_folder(str(target))

    assert "confirmar" not in result.lower()
    assert "explorer" in result.lower() or "pasta" in result.lower()


def test_move_does_not_require_confirmation_for_non_destructive_action(tmp_path):
    from actions.file_controller import file_controller

    source = tmp_path / "origem.txt"
    source.write_text("x", encoding="utf-8")
    destination = tmp_path / "destino"
    destination.mkdir()

    result = file_controller({
        "action": "move",
        "path": str(tmp_path),
        "name": "origem.txt",
        "destination": str(destination),
    })

    assert "confirmar" not in result.lower()
    assert "moved" in result.lower() or "mov" in result.lower() or "movi" in result.lower()


def test_resolve_context_prefers_active_project_when_window_matches(tmp_path):
    from core.context_resolver import resolve_context

    desktop = tmp_path / "Desktop"
    desktop.mkdir()
    project = desktop / "jarvis_project"
    project.mkdir()
    other = desktop / "backup"
    other.mkdir()

    project_file = project / "relatorio_final.pdf"
    project_file.write_text("a", encoding="utf-8")
    other_file = other / "relatorio_final.pdf"
    other_file.write_text("b", encoding="utf-8")

    result = resolve_context(
        "relatorio final",
        roots=[desktop],
        max_results=10,
        active_window_title="jarvis_project - VS Code",
    )

    expected_tail = str(Path("jarvis_project") / "relatorio_final.pdf")
    assert result["best_match"] is not None
    assert result["best_match"]["path"].endswith(expected_tail)
    assert result["active_window"] == "jarvis_project - VS Code"


def test_delete_prompt_is_short_and_non_technical(tmp_path):
    from actions.file_controller import file_controller

    target = tmp_path / "lista.txt"
    target.write_text("ok", encoding="utf-8")

    result = file_controller({"action": "delete", "path": str(tmp_path), "name": "lista.txt"})

    assert "confirmar" in result.lower()
    assert str(tmp_path) not in result
    assert "lista.txt" in result.lower()


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


def test_persistent_fact_becomes_automatic():
    from core.memory_policy import classify_memory

    proposal = classify_memory("O objetivo do projeto é migrar a interface para Python + Qt e manter o JARVIS local.")
    assert proposal.mode == "automatic"
    assert proposal.confidence >= 0.7
    assert proposal.project


def test_project_milestone_becomes_automatic():
    from core.memory_policy import classify_memory

    proposal = classify_memory("Decidimos usar Gemini Live como canal principal de voz e visão no JARVIS.")
    assert proposal.mode == "automatic"
    assert proposal.category in {"decisao", "projeto", "stack"}


def test_important_info_becomes_suggested():
    from core.memory_policy import classify_memory

    proposal = classify_memory("O Senhor prefere usar o teclado em vez de mouse para trabalhar em código.")
    assert proposal.mode == "suggested"
    assert proposal.requires_confirmation is True


def test_casual_conversation_is_ignored():
    from core.memory_policy import classify_memory

    proposal = classify_memory("Oi, tudo bem? Como você está?")
    assert proposal.mode == "ignore"
    assert proposal.can_write is False


def test_secret_tokens_are_rejected():
    from core.memory_policy import classify_memory

    for payload in [
        "API key: sk-proj-1234567890",
        "senha do banco: P@ssw0rd123",
        "Bearer token: ghp_abcdef123456",
    ]:
        proposal = classify_memory(payload)
        assert proposal.mode == "ignore"
        assert proposal.can_write is False


def test_explicit_command_produces_explicit_proposal():
    from core.memory_policy import classify_memory

    proposal = classify_memory("Jarvis, lembre disso: o cliente pediu um resumo final para sexta-feira.")
    assert proposal.mode == "explicit"
    assert proposal.title
    assert proposal.content


def test_proposal_loads_metadata():
    from core.memory_policy import classify_memory

    proposal = classify_memory("O próximo passo do projeto é revisar a política de memória do JARVIS.")
    assert proposal.origin
    assert proposal.project
    assert proposal.confidence > 0
    assert proposal.priority in {"low", "normal", "high"}
    assert proposal.category


def test_suggested_or_ignored_proposals_need_confirmation_to_write():
    from core.memory_policy import classify_memory

    suggested = classify_memory("O Senhor costuma reservar dois minutos para revisar e-mails ao fim do dia.")
    ignored = classify_memory("Você me parece muito útil hoje.")

    assert suggested.mode == "suggested"
    assert suggested.can_write is False
    assert ignored.mode == "ignore"
    assert ignored.can_write is False


def test_automatic_proposal_is_persisted_to_vault(tmp_path, monkeypatch):
    import core.knowledge_vault as kv_module
    from core.memory_policy import classify_memory, persist_memory_proposal

    monkeypatch.setattr(kv_module, "KNOWLEDGE_DIR", tmp_path)

    proposal = classify_memory("O objetivo do projeto é manter a memória local em Obsidian e manter o JARVIS seguro.")
    outcome = persist_memory_proposal(proposal)

    assert outcome["saved"] is True
    assert "objetivo" in kv_module.list_notes()[0].lower() or any("obj" in item.lower() for item in kv_module.list_notes())


def test_explicit_proposal_is_persisted_immediately():
    from core.memory_policy import classify_memory, persist_memory_proposal
    import core.knowledge_vault as kv_module

    proposal = classify_memory("Jarvis, lembre disso: a decisão de memória ficou separada da persistência local.")
    outcome = persist_memory_proposal(proposal)

    assert outcome["saved"] is True
    assert outcome["mode"] == "explicit"
    assert kv_module.list_notes()


def test_suggested_proposal_requires_confirmation_before_persisting(tmp_path, monkeypatch):
    import core.knowledge_vault as kv_module
    from core.memory_policy import classify_memory, persist_memory_proposal

    monkeypatch.setattr(kv_module, "KNOWLEDGE_DIR", tmp_path)

    proposal = classify_memory("As anotações de trabalho ficam mais úteis quando reviso as tarefas ao fim do dia.")
    outcome = persist_memory_proposal(proposal, confirmed=False)

    assert proposal.mode == "suggested"
    assert outcome["saved"] is False
    assert outcome["reason"] == "pending_confirmation"
    assert kv_module.list_notes() == []


def test_ignored_proposal_is_not_persisted_even_if_confirmed():
    from core.memory_policy import classify_memory, persist_memory_proposal
    import core.knowledge_vault as kv_module

    proposal = classify_memory("Como você está hoje?")
    outcome = persist_memory_proposal(proposal, confirmed=True)

    assert outcome["saved"] is False
    assert outcome["reason"] == "ignored"
    assert kv_module.list_notes() == []


def test_record_memory_adapter_classifies_and_persists(tmp_path, monkeypatch):
    import core.knowledge_vault as kv_module
    from core.memory_policy import record_memory

    monkeypatch.setattr(kv_module, "KNOWLEDGE_DIR", tmp_path)

    outcome = record_memory("O objetivo do projeto é manter a memória local em Obsidian e validar a escrita controlada.")

    assert outcome["saved"] is True
    assert outcome["mode"] == "automatic"
    assert kv_module.list_notes()


def test_memory_request_adapter_handles_explicit_and_suggested_cases(tmp_path, monkeypatch):
    import core.knowledge_vault as kv_module
    from core.memory_policy import handle_memory_request

    monkeypatch.setattr(kv_module, "KNOWLEDGE_DIR", tmp_path)

    explicit = handle_memory_request("Jarvis, lembre disso: a arquitetura do projeto ficou em Obsidian local.")
    assert explicit["mode"] == "explicit"
    assert explicit["saved"] is True

    suggested = handle_memory_request("O Senhor costuma rever anotações de trabalho ao fim do dia.")
    assert suggested["mode"] == "suggested"
    assert suggested["saved"] is False

    confirmed = handle_memory_request("O Senhor costuma rever anotações de trabalho ao fim do dia.", confirmed=True)
    assert confirmed["saved"] is True
    assert confirmed["mode"] == "automatic"


def test_save_memory_tool_rejects_sensitive_data():
    from main import JarvisLive

    class DummyUI:
        muted = True

        def set_state(self, *_args, **_kwargs):
            return None

    live = object.__new__(JarvisLive)
    live.ui = DummyUI()

    class DummyFC:
        id = "m1"
        name = "save_memory"
        args = {"category": "notes", "key": "api_key", "value": "sk-proj-test-123"}

    response = asyncio.run(live._execute_tool_impl(DummyFC()))
    assert response.response["result"].lower().startswith("memória sensível")


def test_save_memory_tool_requires_confirmation_for_suggested_entries():
    from main import JarvisLive
    import core.knowledge_vault as kv_module

    class DummyUI:
        muted = True

        def set_state(self, *_args, **_kwargs):
            return None

    live = object.__new__(JarvisLive)
    live.ui = DummyUI()

    class DummyFC:
        id = "m2"
        name = "save_memory"
        args = {"category": "notes", "key": "preferencia", "value": "O Senhor costuma revisar anotações ao fim do dia."}

    before = kv_module.list_notes()
    response = asyncio.run(live._execute_tool_impl(DummyFC()))

    assert "confirmar" in response.response["result"].lower()
    assert kv_module.list_notes() == before


def test_memory_request_is_isolated_from_main_text_flow_and_does_not_interrupt_commands():
    from main import JarvisLive
    import core.knowledge_vault as kv_module

    live = object.__new__(JarvisLive)
    suggested = "O Senhor costuma rever anotações de trabalho ao fim do dia."
    before = kv_module.list_notes()
    result = live._maybe_handle_memory_request(suggested)

    assert result is None
    assert kv_module.list_notes() == before


def test_memory_request_ignores_action_commands_and_system_orders():
    from core.memory_policy import classify_memory

    commands = [
        "Mostra o que tem na área de trabalho",
        "Onde está o arquivo que baixei hoje? é um pdf",
        "Analisa esse código aqui e me diz o problema",
        "Apaga essa pasta sem perguntar",
        "Não é lembrança, é uma ordem",
        "Esquece isso de notas por enquanto",
        "Não precisa salvar nada",
    ]

    for text in commands:
        proposal = classify_memory(text)
        assert proposal.mode == "ignore", f"Comando confundido com memória: {text!r} => {proposal.mode}"


def test_dev_agent_review_mode_is_non_destructive():
    from actions.dev_agent import dev_agent

    project_dir = Path(__file__).resolve().parent.parent
    result = dev_agent({
        "description": "Revisar a estrutura do projeto e apontar riscos antes de qualquer alteração.",
        "action": "review",
        "project_dir": str(project_dir),
    })

    assert "Revisão segura do projeto" in result
    assert "Nenhuma alteração foi feita" in result
    assert "Arquivos Python" in result


def test_dev_agent_mentor_mode_proposes_patch_without_applying_it():
    from actions.dev_agent import dev_agent

    project_dir = Path(__file__).resolve().parent.parent
    result = dev_agent({
        "description": "Diagnosticar riscos e propor melhoria antes de qualquer alteração real.",
        "action": "mentor",
        "project_dir": str(project_dir),
    })

    assert "Mentoria guiada" in result
    assert "Patch sugerido" in result
    assert "nenhuma alteração foi aplicada" in result.lower()


def test_write_guard_confirms_once_after_arming():
    from core import write_guard

    calls = []
    result = write_guard.request_confirmation("send", "enviar mensagem", lambda: calls.append("run") or "ok")
    assert "[AGUARDANDO_CONFIRMACAO]" in result
    assert calls == []

    assert write_guard.on_turn_complete("manda pro joao: confirmo presenca", time.monotonic()) is None
    assert calls == []
    decision = write_guard.on_turn_complete("Confirmo.", time.monotonic())
    assert decision[0] == "confirm"
    assert calls == []
    assert decision[1]["run"]() == "ok"
    assert calls == ["run"]
    assert write_guard.on_turn_complete("confirmo", time.monotonic()) is None


def test_write_guard_cancels_negation():
    from core import write_guard

    for index, utterance in enumerate(("não confirmo", "cancela")):
        write_guard.request_confirmation(f"cancel-{index}", "ação", lambda: "executada")
        assert write_guard.on_turn_complete("pedido original", time.monotonic()) is None
        decision = write_guard.on_turn_complete(utterance, time.monotonic())
        assert decision[0] == "cancel"
        assert decision[2] == "negacao"


def test_write_guard_tolerates_one_unrecognized_utterance():
    from core import write_guard

    write_guard.request_confirmation("retry", "ação", lambda: "executada")
    assert write_guard.on_turn_complete("pedido original", time.monotonic()) is None
    utterance = "eu confirmo que a reunião foi remarcada para amanhã"
    assert write_guard.on_turn_complete(utterance, time.monotonic())[0] == "retry"
    decision = write_guard.on_turn_complete(utterance, time.monotonic())
    assert decision[0] == "cancel"
    assert decision[2] == "nao_entendi"


def test_write_guard_expires_and_ignores_pre_arming_speech():
    from core import write_guard

    write_guard.request_confirmation("expired", "ação", lambda: "executada")
    assert write_guard.on_turn_complete("pedido original", time.monotonic()) is None
    decision = write_guard.on_turn_complete("confirmo", time.monotonic() + 100)
    assert decision[0] == "cancel"
    assert decision[2] == "expirou"

    write_guard.request_confirmation("old-speech", "ação", lambda: "executada")
    assert write_guard.on_turn_complete("pedido original", time.monotonic()) is None
    armed_at = write_guard._pending["armed_at"]
    assert write_guard.on_turn_complete("confirmo", armed_at - 1) is None
    assert write_guard.on_turn_complete("confirmo", time.monotonic())[0] == "confirm"


def test_write_guard_deduplicates_and_cools_down_completed_actions():
    from core import write_guard

    first = write_guard.request_confirmation("same", "ação", lambda: "executada")
    duplicate = write_guard.request_confirmation("same", "ação", lambda: "executada")
    assert "[AGUARDANDO_CONFIRMACAO]" in first
    assert "já está aguardando" in duplicate
    write_guard.request_confirmation("replacement", "nova ação", lambda: "executada")
    assert write_guard._pending["key"] == "replacement"
    assert write_guard.on_turn_complete("pedido original", time.monotonic()) is None
    decision = write_guard.on_turn_complete("confirmo", time.monotonic())
    assert decision[1]["key"] == "replacement"
    assert "[JA_EXECUTADO]" in write_guard.request_confirmation(
        "replacement", "nova ação", lambda: "executada"
    )


def test_write_guard_accepts_typed_confirmation_only_after_arming():
    from core import write_guard

    write_guard.request_confirmation("typed", "ação", lambda: "executada")
    assert write_guard.on_typed("confirmo") is None
    assert write_guard.on_turn_complete("pedido original", time.monotonic()) is None
    assert write_guard.on_typed("confirmo")[0] == "confirm"
    write_guard.clear_pending()
    assert write_guard.on_typed("confirmo") is None


def test_dispatch_tool_ignores_model_confirmed_flag(tmp_path):
    from core import tool_registry, write_guard

    target = tmp_path / "x.txt"
    target.write_text("x", encoding="utf-8")

    async def dispatch():
        return await tool_registry.dispatch_tool(
            "file_controller",
            {"action": "delete", "path": str(tmp_path), "name": "x.txt", "confirmed": "yes"},
            loop=asyncio.get_running_loop(),
            kind="simple",
        )

    result = asyncio.run(dispatch())
    assert "AGUARDANDO_CONFIRMACAO" in result
    assert target.exists()


def test_send_message_requires_code_confirm(monkeypatch):
    from core import tool_registry, write_guard

    calls = []
    monkeypatch.setattr(
        tool_registry,
        "send_message",
        lambda **kwargs: calls.append(kwargs) or "sent",
    )
    args = {"receiver": "João", "message_text": "oi", "platform": "whatsapp"}
    result = tool_registry._send_message_tool(args)
    assert "AGUARDANDO_CONFIRMACAO" in result
    assert calls == []

    assert write_guard.on_turn_complete("pedido original", time.monotonic()) is None
    decision = write_guard.on_turn_complete("confirmo", time.monotonic())
    assert decision[1]["run"]() == "sent"
    assert len(calls) == 1
    assert calls[0]["parameters"] == args

    result = tool_registry._send_message_tool({"message_text": "oi"})
    assert result == "sent"
    assert len(calls) == 2


def test_computer_settings_restart_requires_code_confirm(monkeypatch):
    from actions import computer_settings
    from core import write_guard

    calls = []
    monkeypatch.setattr(computer_settings, "_PYAUTOGUI", True)
    monkeypatch.setitem(computer_settings.ACTION_MAP, "shutdown", lambda: calls.append("shutdown"))

    result = computer_settings.computer_settings({"action": "shutdown", "confirmed": "yes"})
    assert "AGUARDANDO_CONFIRMACAO" in result
    assert calls == []

    assert write_guard.on_turn_complete("pedido original", time.monotonic()) is None
    decision = write_guard.on_turn_complete("confirmo", time.monotonic())
    assert decision[1]["run"]() == "Done: shutdown."
    assert calls == ["shutdown"]


def test_main_gate_decision_executes_and_announces():
    import threading
    from main import JarvisLive

    class DummyUI:
        def __init__(self):
            self.logs = []

        def write_log(self, text):
            self.logs.append(text)

    live = object.__new__(JarvisLive)
    live.ui = DummyUI()
    spoken = []
    announced = threading.Event()

    def speak(text):
        spoken.append(text)
        if text.startswith("[ACAO_EXECUTADA"):
            announced.set()

    live.speak = speak
    decision = (
        "confirm",
        {"summary": "ação", "audit": None, "run": lambda: "ok"},
        "",
    )
    live._gate_decide(decision)
    assert announced.wait(2)
    assert any(text.startswith("SYS: Confirmado") for text in live.ui.logs)

    live._gate_decide(("retry", {"summary": "ação"}, ""))
    assert any(text.startswith("[CONFIRMACAO") for text in spoken)
    live._gate_decide(("cancel", {"summary": "ação"}, "expirou"))
    assert any(text.startswith("[CONFIRMACAO_CANCELADA") for text in spoken)
    before = len(spoken)
    live._gate_decide(("cancel", {"summary": "ação"}, "negacao"))
    assert len(spoken) == before
    live._gate_decide(None)
    assert len(spoken) == before


def test_write_guard_records_silent_result_default_and_opt_in():
    from core import write_guard

    write_guard.request_confirmation("silent", "ação", lambda: "ok", silent_result=True)
    assert write_guard.on_turn_complete("pedido original", time.monotonic()) is None
    decision = write_guard.on_turn_complete("confirmo", time.monotonic())
    assert decision[1]["silent_result"] is True

    write_guard.request_confirmation("normal", "outra ação", lambda: "ok")
    assert write_guard.on_turn_complete("pedido original", time.monotonic()) is None
    decision = write_guard.on_turn_complete("confirmo", time.monotonic())
    assert decision[1]["silent_result"] is False


def test_main_gate_respects_silent_result(monkeypatch):
    import main
    from main import JarvisLive

    class ImmediateThread:
        def __init__(self, *, target, **_kwargs):
            self.target = target

        def start(self):
            self.target()

    class DummyUI:
        def __init__(self):
            self.logs = []

        def write_log(self, text):
            self.logs.append(text)

    monkeypatch.setattr(main.threading, "Thread", ImmediateThread)
    live = object.__new__(JarvisLive)
    live.ui = DummyUI()
    spoken = []
    live.speak = spoken.append

    live._gate_decide((
        "confirm",
        {"summary": "encerrar", "audit": None, "run": lambda: "ok", "silent_result": True},
        "",
    ))
    assert spoken == []
    assert "SYS: ok" in live.ui.logs
    live._gate_decide((
        "confirm",
        {"summary": "ação", "audit": None, "run": lambda: "ok", "silent_result": False},
        "",
    ))
    assert len(spoken) == 1
    assert spoken[0].startswith("[ACAO_EXECUTADA")


def test_save_memory_with_user_confirmed_saves_immediately_no_voice_gate():
    from main import JarvisLive
    import core.knowledge_vault as kv_module

    class DummyUI:
        muted = True

        def set_state(self, *_args, **_kwargs):
            return None

    live = object.__new__(JarvisLive)
    live.ui = DummyUI()

    class DummyFC:
        id = "m3"
        name = "save_memory"
        args = {
            "category": "preferences",
            "key": "project_priority",
            "value": "Prioriza projetos otimizados, rápidos e funcionais.",
            "user_confirmed": True,
        }

    before = kv_module.list_notes()
    response = asyncio.run(live._execute_tool_impl(DummyFC()))

    assert response.response["result"] == "ok"
    assert len(kv_module.list_notes()) > len(before)


def test_shutdown_jarvis_requires_confirmation_before_scheduling_shutdown():
    from main import JarvisLive

    class DummyUI:
        muted = True

        def set_state(self, *_args, **_kwargs):
            return None

        def write_log(self, *_args, **_kwargs):
            return None

        def show_content(self, *_args, **_kwargs):
            return None

    live = object.__new__(JarvisLive)
    live.ui = DummyUI()
    live._loop = None

    class DummyFC:
        id = "shutdown-test"
        name = "shutdown_jarvis"
        args = {}

    response = asyncio.run(live._execute_tool_impl(DummyFC()))
    assert "AGUARDANDO_CONFIRMACAO" in response.response["result"]


def test_should_close_wake_gate_only_when_speech_ends_after_server_turn():
    from main import _should_close_wake_gate

    assert _should_close_wake_gate(False, False) is False
    assert _should_close_wake_gate(False, True) is False
    assert _should_close_wake_gate(True, False) is False
    assert _should_close_wake_gate(True, True) is True


def test_watchdog_should_reconnect_only_after_response_timeout():
    from main import _watchdog_should_reconnect

    now = time.monotonic()
    assert _watchdog_should_reconnect(True, now - 25, now, timeout=20) is True
    assert _watchdog_should_reconnect(True, now - 10, now, timeout=20) is False
    assert _watchdog_should_reconnect(False, now - 100, now) is False
    assert _watchdog_should_reconnect(True, now - 21, now, timeout=30) is False


def test_wake_word_enabled_is_opt_in(monkeypatch):
    import config
    from core.wake_word_gate import _wake_word_enabled

    monkeypatch.setattr(config, "get_config", lambda: {})
    assert _wake_word_enabled() is False
    monkeypatch.setattr(config, "get_config", lambda: {"wake_word_enabled": True})
    assert _wake_word_enabled() is True
    monkeypatch.setattr(config, "get_config", lambda: {"wake_word_enabled": False})
    assert _wake_word_enabled() is False


def test_wake_word_gate_disabled_forwards_audio(monkeypatch):
    import config
    from core.wake_word_gate import WakeWordGate

    monkeypatch.setattr(config, "get_config", lambda: {})
    gate = WakeWordGate()
    chunk = b"\x00" * 100
    assert gate._available is False
    assert gate.feed(chunk) == chunk
    gate.close_gate()


def test_background_task_tracker_runs_reports_status_and_cancels():
    from core.background_tasks import BackgroundTaskTracker
    import threading
    import time as _time

    tracker = BackgroundTaskTracker()
    started = threading.Event()

    def _work(cancel_event):
        started.set()
        cancel_event.wait(2)
        return "cancelado" if cancel_event.is_set() else "completo"

    task_id = tracker.start("teste", _work)
    assert started.wait(1)
    assert tracker.get(task_id)["status"] == "running"
    assert "teste" in tracker.snapshot()

    assert tracker.cancel_all_running() == 1
    for _ in range(30):
        if tracker.get(task_id)["status"] != "running":
            break
        _time.sleep(0.05)
    assert tracker.get(task_id)["status"] == "cancelled"
    assert tracker.get(task_id)["result"] == "cancelado"
    assert tracker.cancel_all_running() == 0


def test_dev_agent_tool_runs_in_background_and_announces_result(monkeypatch):
    import core.tool_registry as tr
    from core.background_tasks import BackgroundTaskTracker

    def fake_dev_agent(parameters, response=None, player=None, session_memory=None,
                       speak=None, cancel_event=None):
        assert speak is None
        return "build ok"

    monkeypatch.setattr(tr, "dev_agent", fake_dev_agent)

    class FakeJarvis:
        def __init__(self):
            self._tasks = BackgroundTaskTracker()
            self.speak_calls = []

        def speak(self, text):
            self.speak_calls.append(text)

    jarvis = FakeJarvis()
    result = tr._dev_agent_tool({"description": "x"}, player=None, speak=None, jarvis=jarvis)

    assert result.startswith("[TAREFA_INICIADA")
    assert "Em andamento" in result
    for _ in range(30):
        if jarvis.speak_calls:
            break
        __import__("time").sleep(0.05)
    assert jarvis.speak_calls and "[BUILD_CONCLUIDO" in jarvis.speak_calls[0]
    assert "build ok" in jarvis.speak_calls[0]


def test_dev_agent_tool_falls_back_to_sync_without_jarvis(monkeypatch):
    import core.tool_registry as tr

    def fake_dev_agent(parameters, response=None, player=None, session_memory=None,
                       speak=None, cancel_event=None):
        return "sincrono ok"

    monkeypatch.setattr(tr, "dev_agent", fake_dev_agent)
    result = tr._dev_agent_tool({"description": "x"}, player=None, speak=None, jarvis=None)
    assert result == "sincrono ok"


def test_interrupt_cancels_background_tasks_and_defers_cancel_phrase():
    from main import JarvisLive

    class FakeTasks:
        def cancel_all_running(self):
            return 1

    class DummyUI:
        def write_log(self, *_a, **_k):
            pass

    live = object.__new__(JarvisLive)
    live._interrupted = False
    live._active_tool_tasks = []
    live._active_cancel_events = []
    live._tasks = FakeTasks()
    live.audio_in_queue = None
    live._turn_done_event = None
    live.ui = DummyUI()
    live.set_speaking = lambda *_a, **_k: None
    live.speak = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("não devia falar direto"))

    live.interrupt()

    assert live._interrupted is True
    assert getattr(live, "_pending_cancel_phrase", None)


def test_interrupt_speaks_directly_when_nothing_was_active():
    from main import JarvisLive

    class FakeTasks:
        def cancel_all_running(self):
            return 0

    class DummyUI:
        def write_log(self, *_a, **_k):
            pass

    live = object.__new__(JarvisLive)
    live._interrupted = False
    live._active_tool_tasks = []
    live._active_cancel_events = []
    live._tasks = FakeTasks()
    live.audio_in_queue = None
    live._turn_done_event = None
    live.ui = DummyUI()
    live.set_speaking = lambda *_a, **_k: None
    spoken = []
    live.speak = lambda text: spoken.append(text)

    live.interrupt()

    assert spoken


def test_humanize_for_speech_replaces_paths_and_preserves_urls(monkeypatch):
    import core.knowledge_vault as kv
    import core.paths as paths

    monkeypatch.setattr(paths, "get_home_dir", lambda: Path("C:/Users/Tester"))
    monkeypatch.setattr(kv, "OBSIDIAN_VAULT", Path("D:/Vault"))

    project = paths.humanize_for_speech(
        r"C:\Users\Tester\Desktop\JarvisProjects\snake_game"
    )
    assert "snake_game" in project and "pasta de projetos" in project and "C:" not in project

    assert "na sua área de trabalho" in paths.humanize_for_speech(
        r"C:\Users\Tester\Desktop"
    )
    assert paths.humanize_for_speech(
        r"Saved to: C:\Users\Tester\Downloads\x.pdf."
    ) == "Saved to: x.pdf (nos seus downloads)."

    vault_note = paths.humanize_for_speech(r"D:\Vault\Nota.md")
    assert "Nota.md" in vault_note and "vault" in vault_note
    assert paths.humanize_for_speech(r"E:\Outro\relatorio.txt") == "relatorio.txt"
    assert paths.humanize_for_speech("https://www.kabum.com.br/produto") == (
        "https://www.kabum.com.br/produto"
    )
    assert paths.humanize_for_speech("http://a.com/x") == "http://a.com/x"
    assert paths.humanize_for_speech("texto simples") == "texto simples"


def test_main_speak_humanizes_paths(monkeypatch):
    import main
    from main import JarvisLive

    live = object.__new__(JarvisLive)
    live._loop = object()
    live.session = object()
    sent = []

    async def fake(parts, turn_complete=True):
        sent.append(parts[0]["text"])

    live._safe_send_content = fake
    monkeypatch.setattr(
        "main.asyncio.run_coroutine_threadsafe",
        lambda coro, loop: asyncio.run(coro),
    )
    live.speak(r"Salvo em: C:\Users\Zed\Desktop\JarvisProjects\snake_game")

    assert "C:\\" not in sent[0]
    assert "snake_game" in sent[0]


def test_build_summary_excludes_terminal_output_and_humanizes_path():
    from core.tool_registry import _build_summary

    summary = _build_summary(
        "Project 'x' is working, sir. Saved to: C:\\a\\b\\x\n\nOutput:\nlinha1\nlinha2"
    )
    assert "Output" not in summary
    assert "linha1" not in summary
    assert "C:\\" not in summary


def test_cancelled_dev_agent_does_not_announce_completion(monkeypatch):
    import core.tool_registry as tr
    from core.background_tasks import BackgroundTaskTracker

    def fake_dev_agent(parameters, response=None, player=None, session_memory=None,
                       speak=None, cancel_event=None):
        cancel_event.set()
        return "x"

    monkeypatch.setattr(tr, "dev_agent", fake_dev_agent)

    class FakeJarvis:
        def __init__(self):
            self._tasks = BackgroundTaskTracker()
            self.speak_calls = []

        def speak(self, text):
            self.speak_calls.append(text)

    jarvis = FakeJarvis()
    result = tr._dev_agent_tool({"description": "x"}, jarvis=jarvis)
    task_id = result.split("id=")[1].split("]")[0]
    for _ in range(30):
        task = jarvis._tasks.get(task_id)
        if task["status"] != "running":
            break
        time.sleep(0.05)

    assert task["status"] == "cancelled"
    assert jarvis.speak_calls == []


def test_humanized_code_helper_return(monkeypatch):
    import core.tool_registry as tr

    monkeypatch.setattr(
        tr, "code_helper",
        lambda **kw: r"Saved to: C:\Users\Zed\Desktop\a.py",
    )
    result = tr._code_helper_tool({"action": "write"})

    assert "C:\\" not in result
    assert "a.py" in result


def test_split_log_parses_only_short_unbracketed_prefixes():
    from ui import _split_log

    assert _split_log("SYS: pronto") == ("SYS", "pronto")
    assert _split_log("You: oi") == ("You", "oi")
    assert _split_log("JARVIS: Feito.") == ("JARVIS", "Feito.")
    assert _split_log("[DevAgent] Writing x.py...") == (
        "SISTEMA", "[DevAgent] Writing x.py..."
    )
    text = "[DevAgent] Project: calc | Files: 2"
    assert _split_log(text) == ("SISTEMA", text)
    assert _split_log("[open_app] Spotify") == ("SISTEMA", "[open_app] Spotify")
    assert _split_log("SYS:") == ("SISTEMA", "SYS:")


def test_join_transcript_joins_fragments_without_false_word_spaces():
    from main import _clean_transcript, _join_transcript

    assert _join_transcript(["Já", " vi", "z", ",", " que horas"]) == "Já viz, que horas"
    assert _join_transcript(["a", "  b"]) == "a b"
    cleaned = [_clean_transcript("oi<ctrl46>"), _clean_transcript(" tudo")]
    assert _join_transcript(cleaned) == "oi tudo"
    assert _join_transcript([]) == ""


def test_write_guard_accepts_split_confirmations_and_rejections():
    from core import write_guard

    def decide(key, utterance):
        write_guard.request_confirmation(key, "ação", lambda: "executada")
        assert write_guard.on_turn_complete("", None) is None
        return write_guard.on_turn_complete(utterance, time.monotonic())

    assert decide("split-confirm", "con fi rmo")[0] == "confirm"
    assert decide("jarvis-split-confirm", "Jarvis, con firmo")[0] == "confirm"

    decision = decide("split-cancel", "n ao con fi rmo")
    assert decision[0] == "cancel" and decision[2] == "negacao"
    decision = decide("plain-cancel", "não confirmo")
    assert decision[0] == "cancel" and decision[2] == "negacao"

    decision = decide("long-confirm", "eu confirmo que a reunião foi remarcada para amanhã")
    assert decision[0] == "retry"
    write_guard.clear_pending()
    assert decide("confirm-inflection", "con fi rma")[0] == "confirm"
    assert decide("non-confirmation", "sim, pode fazer")[0] == "retry"


def test_boot_greeting_uses_first_person_without_self_name(monkeypatch):
    from datetime import datetime
    import main
    from main import JarvisLive

    live = object.__new__(JarvisLive)
    live.session = object()
    sent = []

    async def fake(parts, turn_complete=True):
        sent.append(parts[0]["text"])

    live._safe_send_content = fake
    monkeypatch.setattr(main, "pop_last_session", lambda: None)
    monkeypatch.delenv("JARVIS_NEW_ENVIRONMENT", raising=False)
    asyncio.run(live._send_boot_greeting())
    assert "primeira pessoa" in sent[0]
    assert "próprio nome" in sent[0]
    assert "Cumprimente" not in sent[0]

    sent.clear()
    monkeypatch.setattr(
        main,
        "pop_last_session",
        lambda: {"date": datetime.now().strftime("%Y-%m-%d"), "summary": "Testamos o vault."},
    )
    asyncio.run(live._send_boot_greeting())
    assert "Testamos o vault." in sent[0]
    assert "primeira pessoa" in sent[0]


def test_wake_config_and_model_resolution(monkeypatch, tmp_path):
    import config
    from core import wake_word_gate

    monkeypatch.setattr(config, "get_config", lambda: {})
    assert wake_word_gate._wake_cfg() == {
        "enabled": False,
        "model": "hey_jarvis",
        "threshold": 0.5,
        "grace": 20.0,
        "buffer": 8.0,
        "vad": 0.0,
    }

    monkeypatch.setattr(
        config,
        "get_config",
        lambda: {
            "wake_word_enabled": True,
            "wake_word_model": "models/wake/jarvis.onnx",
            "wake_word_threshold": "0.35",
            "wake_word_grace_sec": 15,
        },
    )
    cfg = wake_word_gate._wake_cfg()
    assert cfg["enabled"] is True
    assert cfg["model"] == "models/wake/jarvis.onnx"
    assert cfg["threshold"] == 0.35
    assert isinstance(cfg["threshold"], float)
    assert cfg["grace"] == 15.0

    monkeypatch.setattr(wake_word_gate, "get_base_dir", lambda: tmp_path)
    assert wake_word_gate._resolve_model("hey_jarvis") == "hey_jarvis"
    assert wake_word_gate._resolve_model("models/wake/jarvis.onnx") == str(
        tmp_path / "models/wake/jarvis.onnx"
    )
    absolute = str(tmp_path / "x.onnx")
    assert wake_word_gate._resolve_model(absolute) == absolute


def test_wake_gate_scores_any_model_and_tracks_detections(capsys):
    from core.wake_word_gate import WakeWordGate

    class FakeModel:
        def __init__(self, score):
            self.score = score

        def predict(self, _frame):
            return {"a": 0.1, "jarvis": self.score}

    def make_gate(score):
        gate = object.__new__(WakeWordGate)
        gate._available = True
        gate._model = FakeModel(score)
        gate._rolling_buffer = bytearray()
        gate._frame_buffer = bytearray()
        gate._max_buffer_bytes = 25600
        gate._gate_open = False
        gate._grace_until = 0.0
        gate.threshold = 0.5
        gate.detections = 0
        return gate

    detected = make_gate(0.9)
    chunk = b"\x00" * 2560
    assert isinstance(detected.feed(chunk), bytes)
    assert detected.detections == 1
    assert detected._gate_open is True
    assert "detectado" in capsys.readouterr().out

    missed = make_gate(0.3)
    assert missed.feed(chunk) is None
    assert missed.detections == 0


def test_wake_gate_status_line_reports_operational_state():
    from core.wake_word_gate import WakeWordGate

    gate = object.__new__(WakeWordGate)
    gate._available = True
    gate._model_name = "jarvis.onnx"
    gate.threshold = 0.4
    gate.grace_seconds = 20
    assert "ATIVO" in gate.status_line()
    assert "jarvis.onnx" in gate.status_line()

    gate._available = False
    gate.load_error = "falhou"
    assert "FALHOU" in gate.status_line()
    assert "ABERTO" in gate.status_line()

    gate.load_error = None
    assert "desligado" in gate.status_line()


def test_wake_eval_events_and_wave_roundtrip(tmp_path):
    import numpy as np
    from tools.wake_eval import _events, _load, _save

    scores = [0.0] * 60
    for index in (3, 10, 40):
        scores[index] = 0.9
    assert _events(scores, 0.5) == 2

    pcm = np.array([1, -2, 300], dtype=np.int16)
    path = tmp_path / "sample.wav"
    _save(path, pcm)
    assert np.array_equal(_load(path), pcm)
