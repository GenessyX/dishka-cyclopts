# Dishka × Cyclopts

Async Dishka integration for Cyclopts. It injects dependencies into async CLI commands using the familiar `@inject` decorator.

## Features

- **Automatic scope management**: async containers are closed after each command, so async generators/iterators are finalized.
- **Drop-in decorator**: use `@inject` on Cyclopts commands; annotate parameters with `FromDishka[...]`.
- **Positional-friendly**: injected params can precede user arguments; binding is normalized to kwargs.

## Installation

Install using `pip`

```sh
pip install dishka-cyclopts
```

Or with `uv`

```sh
uv add dishka-cyclopts
```

## Usage

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

`setup_dishka` patches Cyclopts to track the current app and stores the provided `AsyncContainer` inside `app.state`. After each command completes the container is closed, finalizing APP/REQUEST scoped resources (including async generators).

## Requirements

- Python 3.10+
- Cyclopts >= 4.3.0
- Dishka >= 1.7.2

## More Examples

Check out the [examples](https://github.com/GenessyX/dishka-cyclopts/tree/main/examples)
directory for more detailed examples.
