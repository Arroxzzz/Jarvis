import threading


class BackgroundTaskTracker:
    def __init__(self):
        self._pending = 0
        self._lock = threading.Lock()
        self._panel_cache: dict[str, set[str]] = {}

    def spawn(self, fn, loop, task_name: str = "background") -> None:
        def _runner():
            with self._lock:
                self._pending += 1
            try:
                fn()
            finally:
                with self._lock:
                    self._pending = max(0, self._pending - 1)
                print(f"[JARVIS] 🔄 {task_name} finished")

        loop.run_in_executor(None, _runner)

    def pending_count(self) -> int:
        with self._lock:
            return self._pending

    def result_already_seen(self, kind: str, payload: str) -> bool:
        cache = self._panel_cache.setdefault(kind, set())
        token = payload.strip().lower()
        if not token:
            return True
        if token in cache:
            return True
        cache.add(token)
        return False

    def deliver_panel_result(
        self, ui, kind: str, label: str, payload: str, body: str,
        context_prefix: str, send_content_fn,
    ) -> None:
        panel_key = f"{kind.lower()}::{payload[:220]}"
        if self.result_already_seen(kind, panel_key):
            return
        ui.show_content(label, body)
        ui.write_log(f"SYS: {label} disponível no painel.")
        send_content_fn(
            f"[{context_prefix} — não leia em voz alta, use como memória]\n{body[:2000]}"
        )