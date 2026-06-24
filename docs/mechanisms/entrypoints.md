# Entry-point discovery

The most realistic packaging story: a plugin is a **separate installed
distribution** the host has never heard of. The host discovers it through a
named entry-point group with one call:

```python
pm.load_entrypoints("kitchen")
```

This reads `importlib.metadata` entry points - the **standard library**, no
setuptools and no third-party dependency. Any installed package that advertises
itself under the group is registered without the host importing it.

## Declaring a plugin

A plugin package declares its entry point in `pyproject.toml`:

```toml
[project.entry-points.kitchen]
extra = "smoothie_extra"
```

After a plain install, `load_entrypoints("kitchen")` finds it. The host code does
not change. This repo ships two such plugins:

- `pluginkit_tour.contrib.honey` - an entry point inside the host's own
  distribution.
- `examples/external-plugin/` - an **external** uv project, installed alongside.

## Resilient loading

A broken plugin should not take down discovery. `load_entrypoints` loads each
plugin in isolation and, by default, raises a `PluginValidationError` naming the
offending plugin. Pass `ignore_errors=True` to skip failures instead:

```python
loaded = pm.load_entrypoints("kitchen", ignore_errors=True)
```

Already-registered and [blocked](../concepts/plugin-manager.md#blocking) names are
skipped automatically.

## Run it

```bash
make run DEMO=entrypoints
```

```text
Discovered 2 plugin(s) via entry points
Registered plugins: ['honey', 'extra']
Smoothie: water, ice, honey, oats, chia seeds, almond butter
```

## Why "entry points" and not "setuptools"

The method reads package metadata that every modern build backend writes
(`uv_build`, hatchling, flit, setuptools). The name is historical; the mechanism
is the `importlib.metadata` standard. setuptools is not installed in this
project.
