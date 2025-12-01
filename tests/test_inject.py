import asyncio
from collections.abc import AsyncIterator

from cyclopts import App
from dishka import FromDishka, Provider, Scope, make_async_container, provide

from dishka_cyclopts import inject, setup_dishka


class _Provider(Provider):
    @provide(scope=Scope.APP)
    def number(self) -> int:
        return 7


def test_setup_dishka_and_inject() -> None:
    async def runner() -> None:
        app = App(result_action="return_value")
        container = make_async_container(_Provider())
        setup_dishka(container, app)

        @app.command
        @inject
        async def main(value: FromDishka[int]) -> int:
            return value

        result = await app.run_async(["main"])
        assert result == 7

    asyncio.run(runner())


def test_inject_with_positional_user_args() -> None:
    async def runner() -> None:
        app = App(result_action="return_value")
        container = make_async_container(_Provider())
        setup_dishka(container, app)

        @app.command
        @inject
        async def main(foo: FromDishka[int], bar: int) -> int:
            return foo + bar

        result = await app.run_async(["main", "5"])
        assert result == 12

    asyncio.run(runner())


def test_container_finalizes_on_run() -> None:
    closed: list[str] = []

    class ClosingProvider(Provider):
        @provide(scope=Scope.APP)
        async def iterator(self) -> AsyncIterator[str]:
            try:
                yield "value"
            finally:
                closed.append("closed")

    async def runner() -> None:
        app = App(result_action="return_value")
        container = make_async_container(ClosingProvider())
        setup_dishka(container, app)

        @app.command
        @inject
        async def main(value: FromDishka[str]) -> str:
            return value

        result = await app.run_async(["main"])
        assert result == "value"

    asyncio.run(runner())
    assert closed == ["closed"]
