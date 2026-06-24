# pluginkit

A small, **dependency-free** plugin framework for Python: declare hook
specifications, let plugins implement them, and discover plugins via entry points.
Sync and async dispatch, hook ordering, wrappers, pipeline (fold) dispatch, and
historic hooks - in a few readable files.

The entire library is three small files under `src/pluginkit/`:

- **markers.py** - the `@hookspec` / `@hookimpl` decorators.
- **manager.py** - the `PluginManager`, `HookRelay`, and `HookCaller`.
- **exceptions.py** - `PluginValidationError`.

It has **zero runtime dependencies** (standard library only), runs on Python 3.11+,
and ships a `py.typed` marker.

```bash
pip install pluginkit
```

## What you get

Every plugin concept - hook specs, implementations, ordering, wrappers, pipeline
dispatch, historic replay, async, and entry-point discovery - in a strictly typed
library small enough to read end to end. See
[Differences from pluggy](production/vs-pluggy.md) if you are weighing the two.

## A 30-second tour

```python
from pluginkit import HookspecMarker, HookimplMarker, PluginManager

hookspec = HookspecMarker("kitchen")
hookimpl = HookimplMarker("kitchen")


class Specs:
    """The contract the host declares."""

    @staticmethod
    @hookspec
    def add_ingredients(base: list[str]) -> list[str]:
        """Offer ingredients to add to the smoothie."""


class BerryPlugin:
    """A plugin that fulfils the contract."""

    @hookimpl
    def add_ingredients(self, base: list[str]) -> list[str]:
        """Contribute berries."""
        return ["blueberry", "strawberry"]


pm = PluginManager("kitchen")
pm.add_hookspecs(Specs)
pm.register(BerryPlugin(), name="berry")

print(pm.hook.add_ingredients(base=["banana"]))  # [['blueberry', 'strawberry']]
```

## Where to go next

- [Concepts / Overview](concepts/overview.md) - the three moving parts and how
  they fit together.
- [Mechanisms](mechanisms/direct.md) - one page per calling convention, each with
  a runnable demo.
- [Production](production/hardening.md) - what was done to move this past a toy,
  and where it still differs from pluggy.
- [API Reference](api-reference.md) - generated from the source docstrings.

## Install and run

```bash
make install            # uv sync (host + the external smoothie-extra plugin)
make run                # run every demo
make run DEMO=wrapper   # run one
make test               # pytest
make docs-serve         # serve these docs locally
```
