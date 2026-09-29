import threading
import time
import uuid


class BackgroundTaskTracker:
    def __init__(self):
        self._pending = 0
        self._lock = threading.Lock()
        self._panel_cache: dict[str, set[str]] = {}
        self._tasks: dict[str, dict] = {}

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

    def start(self, name: str, fn, cancel_event: threading.Event | None = None) -> str:
        """Roda fn(cancel_event) numa thread própria e devolve um ID curto para status/cancelamento.
        fn deve checar cancel_event.is_set() nos pontos que já suporta (cooperativo — não mata a
        thread à força)."""
        task_id = uuid.uuid4().hex[:8]
        cancel_event = cancel_event or threading.Event()
        self._tasks[task_id] = {
            "name": name, "status": "running", "started": time.monotonic(),
            "cancel_event": cancel_event, "result": None,
        }

        def _runner():
            try:
                result = fn(cancel_event)
                self._tasks[task_id]["status"] = "cancelled" if cancel_event.is_set() else "done"
                self._tasks[task_id]["result"] = result
            except Exception as e:
                self._tasks[task_id]["status"] = "error"
                self._tasks[task_id]["result"] = str(e)

        threading.Thread(target=_runner, daemon=True, name=f"task-{name}-{task_id}").start()
        return task_id

    def get(self, task_id: str) -> dict | None:
        return self._tasks.get(task_id)

    def snapshot(self) -> str:
        """Resumo curto: tarefas rodando ou concluídas nos últimos 60s."""
        now = time.monotonic()
        lines = []
        for t in self._tasks.values():
            if t["status"] == "running" or now - t["started"] < 60:
                lines.append(f"{t['name']}: {t['status']}, {int(now - t['started'])}s")
        return "\n".join(lines) if lines else "Nenhuma tarefa em segundo plano."

    def cancel_all_running(self) -> int:
        """Sinaliza cancelamento cooperativo a todas as tarefas em execução. Devolve quantas."""
        n = 0
        for t in self._tasks.values():
            if t["status"] == "running":
                t["cancel_event"].set()
                n += 1
        return n

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