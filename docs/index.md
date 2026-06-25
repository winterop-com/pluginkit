# pluginkit

A small, **strictly-typed**, generics-first plugin framework for **Python 3.13+**.
Declare extension points, let plugins implement them, discover plugins via entry
points - and, unlike untyped hook systems, get the **right return type for every
call**, derived from the spec and checked by your type checker.

The library is a few small files under `src/pluginkit/` (`markers.py`, `manager.py`,
`aio.py`, `exceptions.py`), has **zero runtime dependencies** (standard library
only), and ships a `py.typed` marker.

```bash
pip install pluginkit
```

## What you get

`pm.caller(spec)` returns a caller whose result type matches the dispatch mode -
`list[R]` for collecting, `R | None` for firstresult, `R` for pipeline - so hook
calls are checked, not asserted. Every plugin concept (specs, impls, ordering,
wrappers, pipeline dispatch, historic replay, async, entry-point discovery) in a
library small enough to read end to end. See
[pluginkit vs pluggy](production/vs-pluggy.md) if you are weighing the two.

## A 30-second tour

```python
from pluginkit import ExtensionPoint, Extension, PluginManager

extension_point = ExtensionPoint("kitchen")
extension = Extension("kitchen")


class Specs:
    """The contract the host declares."""

    @staticmethod
    @extension_point
    def add_ingredients(base: list[str]) -> list[str]:
        """Offer ingredients to add to the smoothie."""


class BerryPlugin:
    """A plugin that fulfils the contract."""

    @extension
    def add_ingredients(self, base: list[str]) -> list[str]:
        """Contribute berries."""
        return ["blueberry", "strawberry"]


pm = PluginManager("kitchen")
pm.add_extension_points(Specs)
pm.register(BerryPlugin(), name="berry")

ingredients = pm.caller(Specs.add_ingredients)(base=["banana"])  # typed list[list[str]]
print(ingredients)  # [['blueberry', 'strawberry']]
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
