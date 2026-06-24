# Hardening notes

pluginkit started as a teaching reimplementation. This page records what was done
to move it past a toy, and why each item matters in a real plugin host.

## Wrapper exception safety

The single most important fix. A wrapper holds control across its `yield`, so if
an inner implementation raises, the wrapper must still be resumed - otherwise any
`try/finally` or `with` it holds would leak.

The dispatch loop runs the inner implementations inside a `try`, then unwinds the
started wrappers in reverse, throwing the exception **into** each one. A wrapper
may clean up and re-raise, or swallow the exception by returning a value. Only
after every wrapper has been resumed is the exception re-raised (if still
pending). See [`HookCaller._teardown`](../api-reference.md#manager).

Covered by `test_wrapper_cleanup_runs_when_inner_impl_raises` and
`test_wrapper_can_suppress_inner_exception`.

## Fail-fast validation

Two checks run at registration, turning silent misbehaviour into loud errors:

- **unknown hook** - an implementation whose name matches no spec raises
  `PluginValidationError` (unless marked `optionalhook`).
- **unknown argument** - an implementation that declares a parameter the spec does
  not have raises `PluginValidationError`. Without this, a typo like `def
  greet(self, nam)` would silently never receive its value, because the kwarg
  filter would simply drop it.

## Plugin lifecycle

A real host needs to remove and disable plugins, not just add them:

- `unregister(name)` drops a plugin and all its implementations;
- `set_blocked(name)` removes it and refuses future registration (including via
  entry-point discovery);
- `is_registered`, `get_plugin`, `get_name`, `get_hookcallers`, and `plugin_names`
  cover inspection.

## Resilient discovery

`load_entrypoints` isolates each plugin load. A broken third-party plugin raises a
`PluginValidationError` that names it, or is skipped entirely with
`ignore_errors=True`, so one bad package cannot block all discovery.

## Thread-safe mutation

Registry mutations are guarded by a re-entrant lock, so plugins can be loaded from
multiple threads. Hook **calls** are intentionally lock-free; see
[Lifecycle and validation](lifecycle.md) for the rationale.

## Spec-combination validation

A `historic` spec cannot also be `firstresult` (replay has no single winner); the
manager rejects the combination when specs are added, rather than failing
mysteriously at call time.

## Packaging quality

- **zero runtime dependencies** - the library is standard-library only;
- ships a `py.typed` marker so downstreams get the types;
- a curated public API in `pluginkit/__init__.py` with `__version__`;
- strict `ruff` + `mypy` + `pyright`, and a test suite covering the happy paths,
  the error paths, and the examples.

## What is deliberately still out of scope

See [Differences from pluggy](vs-pluggy.md) for the features pluginkit does not
implement and when you should reach for pluggy instead.
