"""Atomic persistence for the local demo aggregate."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock
from typing import Any, Callable

from bobbee.domain.models import empty_state


class JsonRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock = RLock()
        self._cache: dict[str, Any] | None = None
        self._mtime_ns: int | None = None

    def load(self) -> dict[str, Any]:
        with self._lock:
            if not self.path.exists():
                return empty_state()
            mtime_ns = self.path.stat().st_mtime_ns
            if self._cache is not None and self._mtime_ns == mtime_ns:
                return deepcopy(self._cache)
            try:
                state = json.loads(self.path.read_text(encoding="utf-8"))
                self._cache = state
                self._mtime_ns = mtime_ns
                return deepcopy(state)
            except (json.JSONDecodeError, OSError):
                return empty_state()

    def save(self, state: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = deepcopy(state)
            with NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.flush()
                temporary = Path(handle.name)
            temporary.replace(self.path)
            self._cache = payload
            self._mtime_ns = self.path.stat().st_mtime_ns
            return deepcopy(payload)

    def update(self, change: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        with self._lock:
            state = self.load()
            change(state)
            return self.save(state)

    def reset(self) -> None:
        self.save(empty_state())
