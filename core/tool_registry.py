from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Callable

from actions.browser_control import browser_control, open_url_on_monitor
from actions.code_helper import code_helper
from actions.computer_control import computer_control
from actions.computer_settings import computer_settings
from actions.desktop import desktop_control
from actions.dev_agent import dev_agent
from actions.file_controller import file_controller, open_folder
from actions.file_processor import file_processor
from actions.flight_finder import flight_finder
from actions.open_app import open_app
from actions.reminder import reminder
from actions.send_message import send_message
from actions.system_monitor import get_system_status
from actions.web_search import web_search as web_search_action
from actions.weather_report import weather_action
from actions.youtube_video import youtube_video
from core.tool_declarations import TOOL_DECLARATIONS


@dataclass(frozen=True)
class ToolSpec:
    name: str
    func: Callable[..., Any]
    declaration: dict[str, Any] | None = None
    kind: str = "simple"


_REGISTRY: dict[str, ToolSpec] = {}
_SIMPLE_TOOL_NAMES: set[str] = set()
_ADVANCED_TOOL_NAMES: set[str] = set()


def register_tool(name: str, *, declaration: dict[str, Any] | None = None, kind: str = "simple"):
    def _decorator(func: Callable[..., Any]):
        _REGISTRY[name] = ToolSpec(name=name, func=func, declaration=declaration, kind=kind)
        if kind == "simple":
            _SIMPLE_TOOL_NAMES.add(name)
        else:
            _ADVANCED_TOOL_NAMES.add(name)
        return func

    return _decorator


def _decl(name: str) -> dict[str, Any]:
    for item in TOOL_DECLARATIONS:
        if item.get("name") == name:
            return item
    return {
        "name": name,
        "description": f"Registered tool: {name}",
        "parameters": {"type": "OBJECT", "properties": {}},
    }


@register_tool("open_app", declaration=_decl("open_app"), kind="simple")
def _open_app_tool(args: dict, *, player=None, session_memory=None, **_extra):
    return open_app(parameters=args, response=None, player=player, session_memory=session_memory)


@register_tool("weather_report", declaration=_decl("weather_report"), kind="simple")
def _weather_report_tool(args: dict, *, player=None, session_memory=None, **_extra):
    return weather_action(parameters=args, player=player, session_memory=session_memory)


@register_tool("browser_control", declaration=_decl("browser_control"), kind="simple")
def _browser_control_tool(args: dict, *, player=None, session_memory=None, **_extra):
    return browser_control(parameters=args, player=player, session_memory=session_memory)


@register_tool("open_on_monitor", declaration=_decl("open_on_monitor"), kind="simple")
def _open_on_monitor_tool(args: dict, *, player=None, session_memory=None, **_extra):
    service_urls = {
        "gmail": "https://mail.google.com",
        "youtube": "https://youtube.com",
        "whatsapp": "https://web.whatsapp.com",
        "calendar": "https://calendar.google.com",
        "drive": "https://drive.google.com",
        "notion": "https://notion.so",
        "github": "https://github.com",
    }
    url = args.get("url") or service_urls.get((args.get("service") or "").lower(), "")
    if not url:
        return "Qual URL ou serviço deseja abrir, Senhor?"
    return open_url_on_monitor(url, args.get("monitor", "secondary"))


@register_tool("file_controller", declaration=_decl("file_controller"), kind="simple")
def _file_controller_tool(args: dict, *, player=None, session_memory=None, **_extra):
    return file_controller(parameters=args, player=player)


@register_tool("open_folder", declaration=_decl("open_folder"), kind="simple")
def _open_folder_tool(args: dict, *, player=None, session_memory=None, **_extra):
    confirmed = str(args.get("confirmed", "")).lower() in ("yes", "true", "1", "confirm")
    return open_folder(args.get("path", ""), confirmed=confirmed)


@register_tool("send_message", declaration=_decl("send_message"), kind="simple")
def _send_message_tool(args: dict, *, player=None, session_memory=None, **_extra):
    return send_message(parameters=args, response=None, player=player, session_memory=session_memory)


@register_tool("reminder", declaration=_decl("reminder"), kind="simple")
def _reminder_tool(args: dict, *, player=None, session_memory=None, **_extra):
    return reminder(parameters=args, response=None, player=player, session_memory=session_memory)


@register_tool("youtube_video", declaration=_decl("youtube_video"), kind="simple")
def _youtube_video_tool(args: dict, *, player=None, session_memory=None, speak=None, **_extra):
    return youtube_video(parameters=args, response=None, player=player, session_memory=session_memory, speak=speak)


@register_tool("computer_settings", declaration=_decl("computer_settings"), kind="advanced")
def _computer_settings_tool(args: dict, *, player=None, **_extra):
    return computer_settings(parameters=args, response=None, player=player)


@register_tool("desktop_control", declaration=_decl("desktop_control"), kind="advanced")
def _desktop_control_tool(args: dict, *, player=None, **_extra):
    return desktop_control(parameters=args, player=player)


@register_tool("code_helper", declaration=_decl("code_helper"), kind="advanced")
def _code_helper_tool(args: dict, *, player=None, speak=None, **_extra):
    return code_helper(parameters=args, player=player, speak=speak)


@register_tool("dev_agent", declaration=_decl("dev_agent"), kind="advanced")
def _dev_agent_tool(args: dict, *, player=None, speak=None, **_extra):
    return dev_agent(parameters=args, player=player, speak=speak, cancel_event=None)


@register_tool("web_search", declaration=_decl("web_search"), kind="advanced")
def _web_search_tool(args: dict, *, player=None, session_memory=None, **_extra):
    return web_search_action(parameters=args, player=player, session_memory=session_memory)


@register_tool("file_processor", declaration=_decl("file_processor"), kind="advanced")
def _file_processor_tool(args: dict, *, player=None, speak=None, **_extra):
    return file_processor(parameters=args, player=player, speak=speak)


@register_tool("computer_control", declaration=_decl("computer_control"), kind="advanced")
def _computer_control_tool(args: dict, *, player=None, **_extra):
    return computer_control(parameters=args, player=player)


@register_tool("flight_finder", declaration=_decl("flight_finder"), kind="advanced")
def _flight_finder_tool(args: dict, *, player=None, **_extra):
    return flight_finder(parameters=args, player=player)


@register_tool("system_status", declaration=_decl("system_status"), kind="advanced")
def _system_status_tool(args: dict, **_extra):
    return str(get_system_status())


@register_tool("manage_monitor", declaration=_decl("manage_monitor"), kind="advanced")
def _manage_monitor_tool(args: dict, **_extra):
    from actions.background_monitor import add_monitor, remove_monitor, list_monitors
    action = (args.get("action") or "").lower().strip()
    topic = (args.get("topic") or "").strip()
    if action == "add" and topic:
        return add_monitor(topic)
    if action == "remove" and topic:
        return remove_monitor(topic)
    if action == "list":
        result = list_monitors()
        return ("Monitoring: " + ", ".join(result)) if result else "No topics are being monitored."
    return "Specify action (add/remove/list) and a topic."


@register_tool("deep_reasoning", declaration=_decl("deep_reasoning"), kind="advanced")
async def _deep_reasoning_tool(args: dict, *, jarvis=None, loop=None, **_extra):
    query = args.get("query", "")
    task_type = args.get("task_type", "general").strip().lower()
    from core.llm_client import FREE_MODELS, call_llm_text

    if task_type not in FREE_MODELS:
        task_type = "general"

    def _ask_openrouter() -> str:
        last_err = None
        for model in FREE_MODELS[task_type]:
            try:
                return call_llm_text(
                    query,
                    system="Você é um especialista em raciocínio técnico. Responda em PT-BR, direto e completo.",
                    model=model,
                    timeout=25,
                    force_provider="openrouter",
                )
            except Exception as e:
                last_err = e
                continue
        raise RuntimeError(f"Todos os modelos gratuitos falharam: {last_err}")

    try:
        loop = loop or asyncio.get_running_loop()
        return await asyncio.wait_for(loop.run_in_executor(None, _ask_openrouter), timeout=80)
    except asyncio.TimeoutError:
        return "deep_reasoning demorou demais e foi cancelado, Senhor. Tente novamente ou reformule a pergunta."
    except Exception as e:
        return f"deep_reasoning falhou, Senhor: {e}"


def get_declarations() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = list(TOOL_DECLARATIONS)
    seen = {item.get("name") for item in items if item.get("name")}
    for name, spec in _REGISTRY.items():
        if name in seen:
            continue
        if spec.declaration:
            items.append(spec.declaration)
        else:
            items.append({
                "name": name,
                "description": f"Registered tool: {name}",
                "parameters": {"type": "OBJECT", "properties": {}},
            })
        seen.add(name)
    return items


async def dispatch_tool(name: str, args: dict, *, loop, jarvis=None, kind: str | None = None) -> Any | None:
    spec = _REGISTRY.get(name)
    if spec is None:
        return None
    if kind is not None and spec.kind != kind:
        return None

    player = getattr(jarvis, "ui", None) if jarvis else None
    speak = getattr(jarvis, "speak", None) if jarvis else None
    session_memory = getattr(jarvis, "session_memory", None) if jarvis else None

    try:
        if inspect.iscoroutinefunction(spec.func):
            result = spec.func(
                args,
                player=player,
                session_memory=session_memory,
                speak=speak,
                jarvis=jarvis,
                loop=loop,
            )
            return await result
        result = await loop.run_in_executor(
            None,
            lambda: spec.func(
                args,
                player=player,
                session_memory=session_memory,
                speak=speak,
                jarvis=jarvis,
                loop=loop,
            ),
        )
        if asyncio.iscoroutine(result):
            return await result
        return result
    except TypeError:
        try:
            if inspect.iscoroutinefunction(spec.func):
                result = spec.func(
                    args,
                    player=player,
                    session_memory=session_memory,
                )
                return await result
            result = await loop.run_in_executor(
                None,
                lambda: spec.func(
                    args,
                    player=player,
                    session_memory=session_memory,
                ),
            )
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as _e:
            import traceback as _tb
            print(f"[tool_registry] ❌ {name} falhou (fallback de assinatura): {_e}")
            _tb.print_exc()
            return f"Erro interno ao executar {name}, Senhor: {_e}"
    except Exception as _e:
        import traceback as _tb
        print(f"[tool_registry] ❌ {name} falhou: {_e}")
        _tb.print_exc()
        return f"Erro interno ao executar {name}, Senhor: {_e}"
