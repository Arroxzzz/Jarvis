import json
import os
import tempfile
from pathlib import Path


DEFAULT_SYSTEM_PROMPT = (
    "You are JARVIS, Tony Stark's AI assistant. "
    "Be concise, direct, and always use the provided tools to complete tasks. "
    "Never simulate or guess results — always call the appropriate tool."
)


def get_api_key(api_config_path: Path) -> str:
    with open(api_config_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)["gemini_api_key"]


def load_system_prompt(prompt_path: Path) -> str:
    try:
        return prompt_path.read_text(encoding="utf-8")
    except Exception:
        return DEFAULT_SYSTEM_PROMPT


def read_config(api_config_path: Path) -> dict:
    try:
        return json.loads(api_config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_config_key(api_config_path: Path, key: str, value) -> None:
    data = read_config(api_config_path)
    data[key] = value
    with tempfile.NamedTemporaryFile(
        "w",
        dir=api_config_path.parent,
        delete=False,
        encoding="utf-8",
        suffix=".tmp",
    ) as config_file:
        json.dump(data, config_file, indent=4)
        temporary_path = config_file.name
    os.replace(temporary_path, str(api_config_path))
