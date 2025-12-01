## Dishka × Cyclopts

Async Dishka integration for Cyclopts. It injects dependencies into async CLI commands using the familiar `@inject` decorator.

### Usage

```python
from cyclopts import App
from dishka import FromDishka, Provider, Scope, make_async_container, provide
from dishka_cyclopts import inject, setup_dishka


class Dependencies(Provider):
    @provide(scope=Scope.APP)
    def meaning(self) -> int:
        return 42


app = App(result_action="return_value")
setup_dishka(make_async_container(Dependencies()), app)


@app.command
@inject
async def main(value: FromDishka[int]) -> int:
    return value


if __name__ == "__main__":
    print(app())
```

`setup_dishka` patches Cyclopts to track the current app and stores the provided `AsyncContainer` inside `app.state`.
