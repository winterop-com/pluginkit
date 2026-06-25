# Wrappers

An implementation marked `wrapper=True` wraps every non-wrapper implementation of
the same hook. It is a generator:

- code before `yield` runs first;
- the value sent back to `yield` is the result of the inner implementations;
- whatever the generator `return`s replaces that result.

```python
class FoamWrapper:
    @extension(wrapper=True)
    def blend(self, contents: list[str]) -> Generator[None, str, str]:
        result = yield
        return f"{result} topped with foam"
```

## What a wrapper sees

For a `firstresult` hook the wrapper receives the single inner value; for a
collecting hook it receives the list of results. The `blend` hook in the demo is
`firstresult`, so the wrapper gets one string to decorate.

## Wrappers observe exceptions

This is the important production property. If an inner implementation raises, the
exception is thrown **into** each wrapper at its `yield`, so a wrapper can clean up
or recover. This is what makes wrappers safe for resources:

```python
class TimingWrapper:
    @extension(wrapper=True)
    def blend(self, contents):
        start = perf_counter()
        try:
            return (yield)            # propagate the inner result
        finally:
            record(perf_counter() - start)   # always runs, even on error
```

A wrapper may also swallow the exception by returning a value instead of
re-raising, which becomes the result the caller sees:

```python
@extension(wrapper=True)
def blend(self, contents):
    try:
        return (yield)
    except RuntimeError:
        return "fallback blend"
```

!!! warning "One yield only"
    A wrapper must `yield` exactly once. Yielding zero or more than once raises a
    `RuntimeError` - the framework will not silently swallow a malformed wrapper.

## Run it

```bash
make run DEMO=wrapper
```

```text
  [trace] blending 3 item(s)...
  [trace] done: 'mango + yogurt + ice blend'
Result: mango + yogurt + ice blend topped with foam
```

The [report builder example](../index.md) uses a wrapper to frame a document with
a banner.
