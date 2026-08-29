# The plugin manager

`PluginManager` is the run-time hub. Source:
[`pluginkit/manager.py`](../api-reference.md#manager).

## Lifecycle of a call

```mermaid
sequenceDiagram
    participant Host
    participant PM as PluginManager
    participant HC as HookCaller
    participant Impl as Implementations
    Host->>PM: add_extension_points(specs)
    PM->>HC: create one caller per spec
    Host->>PM: register(plugin)
    PM->>HC: add validated HookImpls
    Host->>PM: pm.caller(Specs.add_ingredients)(base=...)
    PM->>HC: __call__(**kwargs)
    HC->>Impl: call each, filtering kwargs
    Impl-->>HC: results
    HC-->>Host: list (or single value)
```

## Adding specs

`add_extension_points(namespace)` scans a module or object for functions carrying the
project's spec attribute and creates one `HookCaller` per spec. It also records
each spec's argument names, which are used later to validate implementations.

```python
pm = PluginManager("kitchen")
pm.add_extension_points(points)  # a module is fine
```

## Registering plugins

`register(plugin, name=None)` discovers the plugin's implementations, validates
each one, then wires them into the matching callers. The plugin may be a class
instance or a module; implementations may be methods or module-level functions.

Registration is validated up front and fails loudly:

- an implementation for an unknown hook raises `PluginValidationError`
  (unless it is marked `optional`);
- an implementation that declares an argument the spec does not have raises
  `PluginValidationError` - this catches typos that would otherwise silently
  never receive their value;
- a duplicate plugin name, or the same plugin object twice, raises `ValueError`.

## Looking plugins up and removing them

The manager tracks names to plugin objects, so the usual lifecycle operations are
available:

```python
pm.is_registered(plugin)  # bool
pm.get_plugin("berry")  # object | None
pm.get_name(plugin)  # str | None
pm.plugin_names()  # ['berry', 'greens']
pm.unregister("berry")  # remove it and all its impls
```

## Blocking

`set_blocked(name)` unregisters a plugin if present and refuses any future
registration under that name - useful to keep a known-bad or superseded plugin
out, including ones that would otherwise arrive via entry-point discovery.

```python
pm.set_blocked("greens")
pm.is_blocked("greens")  # True
```

## Thread safety

Registry mutations - `register`, `unregister`, `set_blocked`, `add_extension_points` -
are guarded by a re-entrant lock, so plugins can be loaded from multiple threads.
Hook **calls** are deliberately not locked: locking every dispatch would serialise
the whole application. Coordinate calls yourself if they can race with
registration.

## Calling a hook

`pm.caller(spec)` is the typed entry point: it returns a caller whose result type is
derived from the spec's dispatch mode (`list[R]` for collecting, `R | None` for
firstresult, `R` for pipeline), checked by mypy and pyright.
The spec must be the exact extension-point object previously registered with this
manager; foreign, undecorated, and merely same-named functions are rejected.

```python
results = pm.caller(Specs.add_ingredients)(base=["banana"])  # typed list[list[str]]
```

### Preserving plugin attribution

A collecting host that needs provenance can retain the registered plugin name for
every non-`None` result without inspecting marker internals:

```python
results = pm.caller(Specs.add_ingredients).collect_with_plugins(base=["banana"])
for result in results:  # PluginResult[list[str]]
    print(result.plugin_name, result.value)
```

Ordering, filtering, and wrappers are the same as for an ordinary collecting
call. Because wrappers receive and may replace the complete result, a wrapper used
with this mode must preserve or deliberately construct `PluginResult` records.

## The hook relay

`pm.hook` is a `HookRelay` - the untyped shorthand. Attribute access resolves to the
`HookCaller` for that hook name via `__getattr__`, which is what makes
`pm.hook.add_ingredients(...)` read so naturally; it returns `Any`. An unknown name
raises `AttributeError`. `pm.caller(spec)` resolves to the same `HookCaller`, so the
two share one manager - use `pm.caller` when you want the type checker's help.

## Public low-level objects

`HookCaller`, `HookImpl`, and `HookRelay` are public for inspection and advanced
integration. Their documented attributes and methods follow normal compatibility
rules, but hosts should prefer manager and caller operations over invoking
`HookImpl.call()` directly. The mode-specific caller classes are static typing
facades: the runtime object is `HookCaller` (or `AsyncHookCaller`), so do not use
`isinstance(caller, CollectingCaller)` to determine dispatch mode.
