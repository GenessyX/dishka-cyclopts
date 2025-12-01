from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from typing import NewType

from cyclopts import App
from dishka import FromDishka, Provider, Scope, make_async_container, provide

from dishka_cyclopts import inject, setup_dishka

FromAsyncIterator = NewType("FromAsyncIterator", str)

SYNC_ITERATOR_CLOSED = False
ASYNC_ITERATOR_CLOSED = False


class AppProvider(Provider):
    scope = Scope.APP

    @provide
    def number(self) -> int:
        return 42

    @provide
    def provided_iterator(self) -> Iterator[str]:
        global SYNC_ITERATOR_CLOSED  # noqa: PLW0603
        print("Opened sync")
        yield "from sync iterator"
        SYNC_ITERATOR_CLOSED = True
        print("Closed sync")

    @provide
    async def provided_async_iterator(self) -> AsyncIterator[FromAsyncIterator]:
        global ASYNC_ITERATOR_CLOSED  # noqa: PLW0603
        print("Opened async")
        yield FromAsyncIterator("from async iterator")
        print("Closed from async")
        ASYNC_ITERATOR_CLOSED = True

    @provide(scope=Scope.REQUEST)
    def request_scope(self) -> bool:
        return True


@dataclass
class Foo:
    bar: int


def create_app() -> App:
    app = App()
    container = make_async_container(AppProvider())
    setup_dishka(container, app)

    @app.command
    @inject
    async def main(
        foo: FromDishka[int],
        provided_iterator: FromDishka[str],
        provided_async_iterator: FromDishka[FromAsyncIterator],
        request_scope: FromDishka[bool],
        bar: int,
    ) -> Foo:
        assert request_scope is True
        print("request_scope: ", request_scope)
        print(provided_iterator)
        print(provided_async_iterator)
        return Foo(foo + bar)

    @app.command
    async def no_inject(bar: int) -> Foo:
        return Foo(bar)

    return app


if __name__ == "__main__":
    app = create_app()
    app()
