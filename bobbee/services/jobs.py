"""Small in-process job runner for user-triggered demo work."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Callable


class JobManager:
    def __init__(self, workers: int = 2):
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="bobbee")
        self._lock = RLock()
        self._jobs: dict[str, dict] = {}

    def status(self, name: str) -> dict:
        with self._lock:
            return deepcopy(self._jobs.get(name, {
                "active": False,
                "done": False,
                "phase": "idle",
                "message": "Not started",
                "error": None,
                "counts": {},
            }))

    def update(self, name: str, **values) -> None:
        with self._lock:
            current = self.status(name)
            current.update(values)
            current["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._jobs[name] = current

    def start(self, name: str, work: Callable[[Callable[..., None]], None]) -> bool:
        with self._lock:
            if self.status(name)["active"]:
                return False
            self.update(
                name,
                active=True,
                done=False,
                phase="starting",
                message="Starting…",
                error=None,
                counts={},
            )

        def run() -> None:
            try:
                work(lambda **values: self.update(name, **values))
                current = self.status(name)
                if current["active"]:
                    self.update(name, active=False, done=True, phase="done")
            except Exception as exc:  # surfaced through the job status API
                self.update(
                    name,
                    active=False,
                    done=False,
                    phase="error",
                    message=f"Stopped: {exc}",
                    error=str(exc),
                )

        self._executor.submit(run)
        return True

