# Pipeline dispatch

A spec marked `pipeline` threads its **first argument** through every
implementation: each one receives the running value and returns the next. The
hook call returns the final value. This is a fold / middleware chain - something
neither a collecting nor a `firstresult` hook expresses.

!!! note "Beyond pluggy"
    Pipeline dispatch is a pluginkit addition; pluggy has no built-in equivalent.
    In pluggy you would collect results and fold them yourself.

```python
@extension_point(pipeline=True)
def transform(text: str) -> str:
    """Transform the running text and return the next value."""
```

Each implementation transforms and returns the value; ordering (`tryfirst` /
`trylast`) decides the stage order:

```python
class StripStage:
    @extension(tryfirst=True)
    def transform(self, text: str) -> str:
        return text.strip()

class TitleCaseStage:
    @extension
    def transform(self, text: str) -> str:
        return text.title()
```

## Passing through

An implementation that returns `None` leaves the value unchanged and hands it to
the next stage - handy for conditional stages that only sometimes act.

## Calling it

Call the hook with the threaded argument by name; the result is the final value,
not a list:

```python
pm.caller(Specs.transform)(text="  hello   world  ")   # 'Hello World!'
```

## Constraints

- `pipeline` cannot combine with `firstresult` or `historic` (rejected at
  `add_extension_points`).
- A pipeline spec must declare at least one argument - the one that gets threaded.
- Wrappers still wrap the whole pipeline and receive the final value.

## Try it

The [`text_pipeline.py` example](../index.md) builds a four-stage text cleaner:

```bash
uv run python examples/recipes/text_pipeline.py
```

```text
in:  '   hello    wonderful   world   '
out: 'Hello Wonderful World!'
```
