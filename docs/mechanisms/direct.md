# Direct registration

The most basic mechanism: the host knows its plugin objects and hands them to the
manager itself. Source:
[`demo_01_direct.py`](../api-reference.md).

```python
from pluginkit import PluginManager
from pluginkit_tour.hookspecs import IngredientProvider

pm = PluginManager("kitchen")
pm.add_hookspecs(hookspecs)

berry: IngredientProvider = BerryPlugin()
greens: IngredientProvider = GreensPlugin()
pm.register(berry, name="berry")
pm.register(greens, name="greens")

contributed = pm.hook.add_ingredients(base=["banana", "milk"])
```

## What it shows

- A plugin can be a **class instance** (or a module, or anything with marked
  members).
- `add_ingredients` is a **collecting** hook: every plugin runs and the results
  come back as a list, which the host flattens.
- The plugins are annotated as `IngredientProvider`, a `runtime_checkable`
  `Protocol`. The annotation documents the structural contract and lets a type
  checker verify it - no shared base class.

## Run it

```bash
make run DEMO=direct
```

```text
Registered plugins: ['berry', 'greens']
Smoothie: banana, milk, blueberry, strawberry, spinach, kale
```

## When to use it

Direct registration is right when the host owns the list of plugins - built-in
extensions, plugins selected from configuration, or tests. When plugins ship as
independent packages, prefer [entry-point discovery](entrypoints.md).
