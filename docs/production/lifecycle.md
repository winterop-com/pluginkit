# Lifecycle and validation

This page covers the runtime behaviour a host relies on: how registration
validates plugins, how removal and blocking work, and the threading model.

## Registration is validated up front

`register` discovers a plugin's implementations, validates every one, and only
then wires them in. If any implementation is invalid, the call raises and the
plugin is **not** partially registered.

```python
try:
    pm.register(plugin, name="acme")
except PluginValidationError as error:
    log.warning("skipping %s: %s", error.plugin_name, error)
```

Validation covers:

| Problem | Result |
| --- | --- |
| implements a hook that has no spec | `PluginValidationError` (unless `optionalhook`) |
| declares an argument the spec lacks | `PluginValidationError` |
| duplicate plugin name | `ValueError` |
| same plugin object registered twice | `ValueError` |

## Removal and blocking

```python
pm.unregister("acme")        # remove it and all its hook implementations
pm.set_blocked("acme")       # remove it AND refuse to register it again
pm.is_blocked("acme")        # True
```

Blocking is checked by both `register` and `load_entrypoints`, so a blocked name
cannot sneak back in through entry-point discovery.

## Introspection

```python
pm.plugin_names()            # ['acme', 'widget']
pm.get_plugin("acme")        # the object, or None
pm.get_name(plugin)          # 'acme', or None
pm.get_hookcallers(plugin)   # the hooks this plugin contributes to
pm.hook.add_ingredients.implementations()   # impls in call order
repr(pm)                     # "<PluginManager 'kitchen' plugins=2>"
```

## One-off implementations

`call_extra` runs additional implementations for a single call without
registering them - handy in tests or for injecting a temporary behaviour:

```python
def temporary_rule(record):
    return None if record.get("ok") else "not ok"

problems = pm.hook.check.call_extra([temporary_rule], {"record": record})
```

The extra implementations do not persist; the next ordinary call sees only the
registered ones.

## Threading model

Registry mutations - `add_hookspecs`, `register`, `unregister`, `set_blocked` -
are serialised by a re-entrant lock, so plugins can be loaded concurrently.

Hook **calls** are deliberately not locked. Locking every dispatch would serialise
the whole application for no benefit in the common case, where plugins are loaded
once at startup and called many times afterwards. If your host can register
plugins while hooks are being called from other threads, guard those calls
yourself.
