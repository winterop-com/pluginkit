# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Until 1.0.0 the
public API may change between minor versions.

## [0.4.6] - 2026-06-25

### Fixed

- `call_historic` now dispatches to the current implementations **before** recording the
  event, so when an implementation raises, the failed call is not added to the replay
  history - a plugin registered later no longer replays an event whose original dispatch
  failed.
- `call_extra` reports an invalid temporary-implementation signature (`*args` / `**kwargs`)
  as `TypeError`, consistent with its other call-time validation, instead of leaking a
  `ValueError`.

## [0.4.5] - 2026-06-25

### Fixed

- `add_extension_points` is now **atomic**: every caller is built and validated before
  any is registered, so a namespace containing an invalid spec (or, on
  `AsyncPluginManager`, a historic one) no longer leaves a partially-configured manager.
- An invalid implementation signature now raises `PluginValidationError` from
  `register()`, consistent with the unknown-extension-point and unknown-argument errors,
  instead of a plain `ValueError`.

## [0.4.4] - 2026-06-25

### Fixed

- Extension-point and extension parameters that cannot be passed by keyword
  (positional-only, `*args`, `**kwargs`) are now **rejected at registration** instead of
  a positional-only spec type-checking but raising at call time. Keyword-only spec
  params can no longer be bound positionally, so a positional call binds exactly the
  arguments the ParamSpec allows - keeping the typed caller and runtime in lockstep.
- `AsyncPluginManager.add_extension_points` now rejects `historic=True` extension points
  with a clear `ValueError` (historic replay needs synchronous dispatch), instead of
  building a caller whose every call path raised.

## [0.4.3] - 2026-06-25

### Fixed

- Re-adding an already-registered extension point now raises `ValueError` instead of
  silently replacing the caller and **dropping every implementation wired to it**.
- Historic events are **snapshotted** at `call_historic` time, so mutating the caller's
  dict afterwards no longer changes what plugins registered later replay.

### Changed

- Contributor docs corrected to Python 3.13 (they still said 3.11+ with a 3.11-3.13 CI
  matrix).

## [0.4.2] - 2026-06-25

### Fixed

- Typed callers can now be invoked **positionally** at runtime, matching what the
  ParamSpec advertised - `pm.caller(spec)("x")` previously type-checked but raised a
  `TypeError`. Too many positionals or a positional/keyword clash are rejected cleanly.
- The built wheel and sdist now **include the LICENSE file**, via SPDX
  `license`/`license-files` metadata (which also clears the deprecated-license-classifier
  build warning).

### Changed

- `make lint` is now **check-only** (no file mutation: `ruff format --check`, `ruff check`,
  mypy, pyright); use the new `make fmt` to format and autofix. CI runs the check-only
  lint and installs with `uv sync --frozen` so the committed lockfile is enforced.

## [0.4.1] - 2026-06-25

### Changed

- Documentation and examples reorganised: the "Integrations" section and
  `examples/integrations/` are merged with `examples/recipes/` into a single
  **Cookbook** (`examples/cookbook/`), since the FastAPI/Click/pytest examples are
  illustrative examples, not shipped integrations. No library code changes.

## [0.4.0] - 2026-06-25

### Changed (breaking)

- Renamed the decorators to self-describing names, dropping the pluggy-inherited
  vocabulary: `HookspecMarker` -> `ExtensionPoint` (`@extension_point`) and
  `HookimplMarker` -> `Extension` (`@extension`). The option records become
  `ExtensionPointOpts` / `ExtensionOpts`, `PluginManager.add_hookspecs` becomes
  `add_extension_points`, and the `@extension` options `optionalhook` / `specname`
  become `optional` / `target`. No backward-compat aliases (a deliberate clean break).

## [0.3.1] - 2026-06-25

### Fixed

- Spec arguments with a default are now optional at the call site (filled in at call
  time), matching what the typed caller advertises - omitting one previously raised a
  runtime `TypeError`.
- `AsyncPluginManager` `call_extra` now validates extra-impl arguments like the sync
  path, raising a clear `TypeError` instead of a later `KeyError`.
- A wrapper that yields more than once no longer aborts teardown of the other
  wrappers; the rest unwind before the error propagates (sync and async).
- `register` rolls back if wiring a plugin fails part-way (e.g. a historic replay
  raising), so registration is all-or-nothing.

### Changed

- `@hookspec(historic=True)` now brands a `HistoricSpec`, so `caller(spec)` returns a
  `HistoricCaller` (replayed via `call_historic`) instead of a collecting caller whose
  typed call form always raised.

## [0.3.0] - 2026-06-25

### Added

- Typed hook calls: `PluginManager.caller(spec)` returns a caller whose result type
  is derived from the spec's dispatch mode - `list[R]` (collecting), `R | None`
  (firstresult), or `R` (pipeline) - checked by mypy and pyright, not asserted by hand.
- `@hookspec` now brands the spec by mode (`CollectingSpec` / `FirstResultSpec` /
  `PipelineSpec`); the matching typed callers (`CollectingCaller` / `FirstResultCaller`
  / `PipelineCaller`, plus `Async*` variants) are exported.

### Changed

- Require **Python 3.13** (was 3.11+). The branded specs and typed callers use PEP 695
  generics and ParamSpec; CI targets 3.13 only.
- Repositioned as a strictly-typed, generics-first alternative to untyped hook systems
  rather than a from-scratch pluggy explainer.

### Fixed

- `__version__` now derives from the installed package metadata, so it can no longer
  drift from the packaged version (0.2.0 had shipped a stale `0.1.0` literal).

## [0.2.0] - 2026-06-24

### Added

- Python 3.11 and 3.12 support (previously 3.13-only). CI now tests across 3.11,
  3.12, and 3.13.
- Integration examples under `examples/integrations/` - FastAPI, Click CLI, and
  pytest - each with a docs page in a new Integrations section.

### Changed

- Reorganised examples: dependency-free recipes under `examples/recipes/`, framework
  integrations under `examples/integrations/`.
- Documentation: README badges and `pip install` snippet; docs home rewritten to
  describe pluginkit on its own terms.

## [0.1.0] - 2026-06-24

Initial public release.

### Added

- Hook markers (`HookspecMarker`, `HookimplMarker`) with `@overload`-typed bare and
  called forms.
- `PluginManager`: register / unregister / block plugins, lookup, and entry-point
  discovery (`load_entrypoints`), with registration-time and call-time validation.
- Dispatch modes: collecting, `firstresult`, and `pipeline` (fold/middleware), plus
  `tryfirst` / `trylast` ordering, `optionalhook`, and `specname`.
- Generator-based wrappers with exception-safe unwinding.
- Historic hooks replayed to plugins registered later (`call_historic`).
- `AsyncPluginManager` for awaiting coroutine implementations.
- Thread-safe registry mutation; `py.typed`; zero runtime dependencies.
- Documentation (mkdocs Material) and runnable examples.
