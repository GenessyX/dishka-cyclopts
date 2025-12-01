from __future__ import annotations

import asyncio
import inspect
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

from cyclopts import App
from cyclopts.app_stack import AppStack

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Sequence

_app_state: dict[tuple[str, ...], dict[Any, Any]] = {}
_current_app: ContextVar[App | None] = ContextVar("dishka_cyclopts_app", default=None)
FINALIZERS_KEY = "_dishka_finalizers"


def get_app_state(app: App) -> dict[Any, Any]:
    return _app_state.setdefault(app.name, {})


def _get_state(self: App) -> dict[str, Any]:
    return _app_state.setdefault(self.name, {})


def _set_state(self: App, value: dict[str, Any]) -> None:
    _app_state[self.name] = value


def get_current_app() -> App | None:
    """Return app currently being executed inside cyclopts app stack."""
    return _current_app.get()


def patch_app() -> None:
    if not hasattr(App, "state"):
        App.state = property(_get_state, _set_state)  # type: ignore[attr-defined]

    if getattr(AppStack, "_dishka_cyclopts_patched", False):
        return

    original_call: "Callable[..., Any]" = AppStack.__call__

    @contextmanager
    def wrapped_call(
        self: AppStack,
        apps: "Sequence[App | str]",
        overrides: dict[Any, Any] | None = None,
    ) -> "Generator[Any, Any, None]":
        should_finalize = bool(apps)
        with original_call(self, apps, overrides) as context:
            token = _current_app.set(
                self.current_frame[-1] if self.stack else None,
            )
            try:
                yield context
            finally:
                app = _current_app.get()
                _current_app.reset(token)
                if should_finalize and app:
                    state = get_app_state(app)
                    finalizers: list["Callable[[], Any]"] = state.get(
                        FINALIZERS_KEY,
                        [],
                    )
                    for finalize in finalizers:
                        result = finalize()
                        if inspect.isawaitable(result):
                            try:
                                loop = asyncio.get_running_loop()
                            except RuntimeError:
                                asyncio.run(result)  # type: ignore[arg-type]
                            else:
                                task: asyncio.Task[Any] = loop.create_task(result)  # type: ignore[arg-type]
                                state.setdefault("_dishka_tasks", []).append(
                                    task,
                                )

    AppStack.__call__ = wrapped_call  # type: ignore[method-assign]
    AppStack._dishka_cyclopts_patched = True  # type: ignore[attr-defined]  # noqa: SLF001
