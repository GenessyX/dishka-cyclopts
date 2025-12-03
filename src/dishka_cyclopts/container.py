from __future__ import annotations

from functools import update_wrapper
from inspect import signature
from typing import TYPE_CHECKING, Any, Final, TypeVar

from dishka import AsyncContainer
from dishka.integrations.base import wrap_injection

from dishka_cyclopts.state import get_current_app, patch_app

if TYPE_CHECKING:
    from collections.abc import Callable

    from cyclopts import App

T = TypeVar("T")

CONTAINER_NAME: Final = "dishka_container"
CLOSED_KEY: Final = "_dishka_closed_containers"


def _get_container(_: tuple[Any, ...], __: dict[str, Any]) -> "AsyncContainer":
    app = get_current_app()
    if app is None:
        msg = "Cyclopts App context not found. Call setup_dishka before invoking commands."
        raise RuntimeError(msg)

    try:
        container = app.state[CONTAINER_NAME]  # type: ignore[attr-defined]
    except KeyError as exc:
        msg = "Dishka container is not configured for the current Cyclopts App."
        raise RuntimeError(msg) from exc

    if not isinstance(container, AsyncContainer):
        msg = "Cyclopts App context has invalid container reference."
        raise TypeError(msg)

    return container


def inject(func: "Callable[..., T]") -> "Callable[..., T]":
    injected = wrap_injection(
        func=func,
        container_getter=_get_container,
        remove_depends=True,
        is_async=True,
        manage_scope=True,
    )

    injected_signature = signature(injected)

    async def _kwargs_only_wrapper(*args: Any, **kwargs: Any) -> T:  # noqa: ANN401
        bound = injected_signature.bind_partial(*args, **kwargs)
        return await injected(**bound.arguments)  # type: ignore[misc, no-any-return]

    async def _closing_wrapper(*args: Any, **kwargs: Any) -> T:  # noqa: ANN401
        app = get_current_app()
        container = None
        closed_set: set[int] | None = None
        if app is not None:
            container = app.state.get(CONTAINER_NAME)  # type: ignore[attr-defined]
            closed_set = app.state.setdefault(CLOSED_KEY, set())  # type: ignore[attr-defined]
        result = await _kwargs_only_wrapper(*args, **kwargs)
        try:
            return result
        finally:
            if container is not None:
                if closed_set is not None:
                    if id(container) in closed_set:
                        return result  # noqa: B012
                    closed_set.add(id(container))
                await container.close()

    update_wrapper(_closing_wrapper, injected)
    _closing_wrapper.__signature__ = injected_signature  # type: ignore[attr-defined]
    _closing_wrapper.__dishka_injected__ = True  # type: ignore[attr-defined]
    _closing_wrapper.__dishka_orig_func__ = getattr(  # type: ignore[attr-defined]
        injected,
        "__dishka_orig_func__",
        func,
    )

    return _closing_wrapper  # type: ignore[return-value]


def setup_dishka(
    container: "AsyncContainer",
    app: "App",
) -> None:
    patch_app()
    app.state[CONTAINER_NAME] = container  # type: ignore[attr-defined]
    app.state.setdefault(CLOSED_KEY, set())  # type: ignore[attr-defined]
