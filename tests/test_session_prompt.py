from datetime import datetime, timezone


def test_build_system_instruction_contains_identity_and_time():
    from core.session_prompt import build_system_instruction

    instruction = build_system_instruction(
        "JARVIS",
        "",
        "",
        "Base prompt",
        datetime(2026, 10, 2, 16, 30, tzinfo=timezone.utc),
    )

    assert "Seu nome é JARVIS" in instruction
    assert "2026" in instruction
    assert "16:30" in instruction
    assert instruction.endswith("Base prompt")


def test_build_system_instruction_includes_memory_only_when_present():
    from core.session_prompt import build_system_instruction

    now = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
    without_memory = build_system_instruction("JARVIS", "", "", "Prompt", now)
    with_memory = build_system_instruction(
        "JARVIS", "[MEMÓRIA]\nFato", "", "Prompt", now
    )

    assert "[MEMÓRIA]" not in without_memory
    assert "[MEMÓRIA]\nFato" in with_memory
