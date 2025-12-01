from cyclopts import App

from dishka_cyclopts.state import patch_app


def test_app_state() -> None:
    patch_app()
    app = App(name="state-test")
    assert app.state == {}  # type: ignore[attr-defined]
    app.state["test"] = "test"  # type: ignore[attr-defined]
    assert app.state == {"test": "test"}  # type: ignore[attr-defined]
