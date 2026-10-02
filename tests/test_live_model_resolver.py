import asyncio


def test_resolve_prioritizes_cached_model(monkeypatch):
    import core.live_model_resolver as resolver_module
    from core.live_model_resolver import LiveModelResolver

    class UI:
        def write_log(self, message):
            pass

    monkeypatch.setattr(
        resolver_module,
        "_discover_live_models",
        lambda _api_key: ["discovered-model"],
    )
    resolver = LiveModelResolver(
        UI(),
        get_config=lambda: {"live_cache": "cached-model"},
        fallbacks=["fallback-model"],
        cache_key="live_cache",
    )

    asyncio.run(resolver.resolve("test-key"))

    assert resolver.current() == "cached-model"
    assert resolver.candidates == [
        "cached-model",
        "discovered-model",
        "fallback-model",
    ]


def test_advance_rotates_through_candidates():
    from core.live_model_resolver import LiveModelResolver

    class UI:
        def write_log(self, _message):
            pass

    resolver = LiveModelResolver(UI(), dict, ["fallback"], "cache")
    resolver.candidates = ["first", "second"]

    resolver.advance()
    assert resolver.idx == 1
    assert resolver.current() == "second"
    resolver.advance()
    assert resolver.idx == 0


def test_current_uses_first_fallback_when_no_candidates():
    from core.live_model_resolver import LiveModelResolver

    resolver = LiveModelResolver(None, dict, ["fallback-model"], "cache")

    assert resolver.current() == "fallback-model"
