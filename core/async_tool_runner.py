import asyncio


async def run_tool_bound(fn, timeout: float, label: str, default=None):
    """Run a synchronous tool in an executor with an explicit timeout."""
    loop = asyncio.get_running_loop()
    try:
        value = await asyncio.wait_for(loop.run_in_executor(None, fn), timeout=timeout)
        if value is None and default is not None:
            return default
        return value
    except asyncio.TimeoutError:
        return default or f"{label} excedeu {timeout:.0f}s e foi cancelado, Senhor."


async def run_bounded(loop, fn, timeout: float, label: str) -> str:
    try:
        return await asyncio.wait_for(loop.run_in_executor(None, fn), timeout=timeout)
    except asyncio.TimeoutError:
        return f"{label} excedeu {timeout:.0f}s e foi cancelado, Senhor."
