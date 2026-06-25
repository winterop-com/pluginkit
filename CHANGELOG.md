# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Until 1.0.0 the
public API may change between minor versions.

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
