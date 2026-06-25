# Async dispatch

`AsyncPluginManager` is a drop-in variant whose hook **calls** are coroutines.
Registration, validation, ordering and lifecycle are identical to the synchronous
manager - only the calling path is awaited.

```python
import asyncio
from pluginkit import AsyncPluginManager, HookspecMarker, HookimplMarker

hookspec = HookspecMarker("feed")
hookimpl = HookimplMarker("feed")


class Specs:
    @staticmethod
    @hookspec
    def fetch(topic: str) -> str:
        """Fetch a headline for the topic."""


class WeatherSource:
    @hookimpl
    async def fetch(self, topic: str) -> str:
        await asyncio.sleep(0.01)
        return f"weather[{topic}]: clear skies"


pm = AsyncPluginManager("feed")
pm.add_hookspecs(Specs)
pm.register(WeatherSource(), name="weather")

headlines = asyncio.run(pm.caller(Specs.fetch)(topic="harbor"))
```

## Sync and async implementations mix

An implementation may be an ordinary function or a coroutine function. The manager
awaits results that are awaitable and uses plain return values as-is, so a hook
can have both kinds of implementation.

## Supported dispatch modes

Collecting, `firstresult`, and `pipeline` all work and await each implementation in
order. Implementations run **sequentially** (awaited one at a time) to keep
ordering and `firstresult` short-circuiting well defined.

## Wrappers are observe-only

Async wrappers are async generators:

```python
class TimingWrapper:
    @hookimpl(wrapper=True)
    async def fetch(self, topic: str):
        start = monotonic()
        try:
            yield
        finally:
            record(monotonic() - start)   # runs even if an impl raised
```

They run setup before `yield`, teardown after it (including in a `finally`), and
observe exceptions thrown back in. Because async generators cannot return a value,
an async wrapper **cannot replace** the result - use the synchronous manager when
a wrapper must transform the result.

## Not supported

- **Historic hooks** - `call_historic` on an async hook raises `NotImplementedError`
  (replay-on-register would need to await during registration). Use the
  synchronous manager for historic hooks.

!!! note "Beyond pluggy"
    pluggy itself is synchronous; async support comes from the separate `apluggy`
    package. pluginkit bundles a small async manager directly.

## Try it

The [`async_fetch.py` example](../index.md) aggregates three async sources behind a
timing wrapper:

```bash
uv run python examples/recipes/async_fetch.py
```
