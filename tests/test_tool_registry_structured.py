import asyncio
import time

from core.tool_registry import ToolSpec, dispatch_tool


def test_dispatch_tool_preserves_structured_return(monkeypatch):
    from core import tool_registry

    expected = {"result": "ok", "silent": True}
    monkeypatch.setitem(
        tool_registry._REGISTRY,
        "structured_test",
        ToolSpec("structured_test", lambda _args, **_kwargs: expected),
    )

    async def run():
        return await dispatch_tool(
            "structured_test",
            {},
            loop=asyncio.get_running_loop(),
        )

    result = asyncio.run(run())

    assert result is expected


def test_execute_tool_impl_preserves_structured_tool_response():
    from main import JarvisLive

    class FakeUI:
        muted = True

        def set_state(self, _state):
            pass

    class FakeFunctionCall:
        id = "find-context-empty"
        name = "find_context"
        args = {"query": ""}

    jarvis = object.__new__(JarvisLive)
    jarvis.ui = FakeUI()
    response = asyncio.run(jarvis._execute_tool_impl(FakeFunctionCall()))

    assert response.response == {
        "result": "Consulta vazia para contexto local.",
        "needs_confirmation": False,
    }


def test_knowledge_note_is_registered_with_timeout(monkeypatch):
    from core import knowledge_vault, tool_registry

    monkeypatch.setattr(
        knowledge_vault,
        "write_note",
        lambda name, content, append=False: (name, content, append),
    )
    assert tool_registry._REGISTRY["knowledge_note"].timeout == 10.0

    async def run():
        return await dispatch_tool(
            "knowledge_note",
            {"action": "write", "name": "Nota", "content": "Conteúdo"},
            loop=asyncio.get_running_loop(),
            kind="advanced",
        )

    assert asyncio.run(run()) == ("Nota", "Conteúdo", False)


def test_dispatch_tool_timeout_reports_without_waiting_for_result(monkeypatch):
    from core import tool_registry

    def slow_tool(_args, **_kwargs):
        time.sleep(0.05)
        return "done"

    monkeypatch.setitem(
        tool_registry._REGISTRY,
        "slow_test",
        ToolSpec("slow_test", slow_tool, timeout=0.001),
    )
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            dispatch_tool("slow_test", {}, loop=loop)
        )
    finally:
        loop.close()

    assert result == (
        "slow_test excedeu 0s; o resultado não será aguardado, Senhor."
    )
