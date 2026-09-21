"""
tests/test_jarvis_core.py
Roda com: python -m pytest tests/ -v
"""
import asyncio
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


def test_proactive_prompt_includes_project_context():
    from actions.proactive import ProactiveEngine

    engine = ProactiveEngine(min_silence_secs=0, check_cooldown=0)
    prompt = engine.build_prompt(
        {},
        recent_turns=["turno anterior"],
        project_context="[PROJETO_ATIVO] Projeto ativo: 'jarvis_project' em 'D:/Jarvis-main'.",
    )

    assert "jarvis_project" in prompt.lower()
    assert "Projeto ativo" in prompt
    assert "não chamar ferramentas" in prompt.lower()


def test_proactive_is_disabled_by_default():
    from actions.proactive import ProactiveEngine

    engine = ProactiveEngine()
    assert engine.enabled is False
    assert engine.should_trigger(999999.0) is False


def test_runtime_declares_context_tool():
    import main

    names = {tool["name"] for tool in main.TOOL_DECLARATIONS}
    assert "find_context" in names


def test_tool_registry_declares_core_tools():
    from core.tool_registry import get_declarations

    names = {tool["name"] for tool in get_declarations()}
    assert {"open_app", "weather_report", "web_search", "computer_settings", "file_controller"}.issubset(names)


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


def test_obsidian_vault_is_configured():
    assert kv_module.OBSIDIAN_VAULT == Path(r"D:\Memoria_Jarvis")


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


def _fake_llm(resposta):
    return lambda *a, **k: resposta


def test_addressee_nome_explicito_nao_chama_llm(monkeypatch):
    import core.addressee as ad

    def _nao_deve_chamar(*a, **k):
        raise AssertionError("LLM não deveria ser chamado")

    monkeypatch.setattr(ad, "resilient_text_call", _nao_deve_chamar)
    assert ad.classify_addressee("Jarvis, que horas são?") == "dirigida"
    assert ad.classify_addressee("javis abre o navegador") == "dirigida"


def test_addressee_resposta_sim(monkeypatch):
    import core.addressee as ad

    monkeypatch.setattr(ad, "resilient_text_call", _fake_llm("SIM"))
    assert ad.classify_addressee("que horas são?") == "dirigida"


def test_addressee_resposta_nao_com_acento(monkeypatch):
    import core.addressee as ad

    monkeypatch.setattr(ad, "resilient_text_call", _fake_llm("Não."))
    assert ad.classify_addressee("acho que vou fazer um café") == "nao_dirigida"


def test_addressee_falha_dos_provedores_retorna_none(monkeypatch):
    import core.addressee as ad

    msg = "Não foi possível obter resposta — todos os provedores gratuitos falharam, Senhor."
    monkeypatch.setattr(ad, "resilient_text_call", _fake_llm(msg))
    assert ad.classify_addressee("que horas são?") is None


def test_addressee_excecao_retorna_none(monkeypatch):
    import core.addressee as ad

    def _boom(*a, **k):
        raise RuntimeError("rede")

    monkeypatch.setattr(ad, "resilient_text_call", _boom)
    assert ad.classify_addressee("que horas são?") is None


def test_addressee_texto_vazio_retorna_none():
    import core.addressee as ad

    assert ad.classify_addressee("   ") is None


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
    from core.background_tasks import BackgroundTaskTracker

    tracker = BackgroundTaskTracker()

    first = tracker.result_already_seen("SEARCH", "resultado ABC")
    second = tracker.result_already_seen("SEARCH", "resultado ABC")
    third = tracker.result_already_seen("SEARCH", "resultado XYZ")

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


def _live_addr(monkeypatch, verdict):
    import main

    class DummyUI:
        muted = True

        def write_log(self, *_a, **_k):
            pass

        def set_state(self, *_a, **_k):
            pass

    live = object.__new__(main.JarvisLive)
    live.ui = DummyUI()
    live._metric = lambda *a, **k: None
    live._addr_enabled = True
    live._addr_future = None
    live._addr_text = ""
    live._addr_timer = None
    live._addr_verdict = None
    live._addr_muted = False
    live._addr_fail_streak = 0
    monkeypatch.setattr(main, "classify_addressee", lambda text: verdict)
    return live


def test_addr_gate_descarta_fala_nao_dirigida(monkeypatch):
    live = _live_addr(monkeypatch, "nao_dirigida")
    assert asyncio.run(live._addr_gate("acho que vou fazer um café")) is True


def test_addr_gate_deixa_passar_fala_dirigida_e_falha(monkeypatch):
    live = _live_addr(monkeypatch, "dirigida")
    assert asyncio.run(live._addr_gate("que horas são?")) is False
    live = _live_addr(monkeypatch, None)
    assert asyncio.run(live._addr_gate("que horas são?")) is False
    assert live._addr_verdict == "indeterminado"


def test_addr_gate_sem_texto_nao_bloqueia(monkeypatch):
    live = _live_addr(monkeypatch, "nao_dirigida")
    assert asyncio.run(live._addr_gate("   ")) is False
