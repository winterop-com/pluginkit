# pluginkit

A small plugin architecture built **from scratch** with modern Python, to show
what a [pluggy](https://pluggy.readthedocs.io/en/latest/)-style system actually
does under the hood - hardened enough to use.

The entire library is three small files under `src/pluginkit/`:

- **markers.py** - the `@hookspec` / `@hookimpl` decorators.
- **manager.py** - the `PluginManager`, `HookRelay`, and `HookCaller`.
- **exceptions.py** - `PluginValidationError`.

It has **zero runtime dependencies** (standard library only) and ships a
`py.typed` marker.

## Why read this

pluggy is the right choice for production (it powers pytest, tox, and datasette).
This project exists to make its ideas legible: every concept - hook specs,
implementations, ordering, wrappers, historic replay, entry-point discovery - is
implemented in a few dozen lines you can read end to end.

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
