# pluginkit

[![PyPI](https://img.shields.io/pypi/v/pluginkit.svg)](https://pypi.org/project/pluginkit/)
[![Python](https://img.shields.io/pypi/pyversions/pluginkit.svg)](https://pypi.org/project/pluginkit/)
[![CI](https://github.com/winterop-com/pluginkit/actions/workflows/ci.yml/badge.svg)](https://github.com/winterop-com/pluginkit/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-pages-blue.svg)](https://winterop-com.github.io/pluginkit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A small, **strictly-typed**, generics-first plugin framework for **Python 3.13+**.
Declare extension points, let plugins implement them, discover plugins via entry
points - and, unlike untyped hook systems, get the **right return type for every
call**, derived from the spec and checked by your type checker.

`pm.caller(spec)` hands back a caller whose result type matches the dispatch mode -
`list[R]` for collecting, `R | None` for firstresult, `R` for pipeline - with no
hand-annotations and no drift. Zero runtime dependencies, a `py.typed` marker, and a
few readable files.

```bash
uv add pluginkit   # or: pip install pluginkit
```

```python
from pluginkit import Extension, ExtensionPoint, PluginManager

extension_point = ExtensionPoint("greeter")
extension = Extension("greeter")


class Specs:
    @staticmethod
    @extension_point
    def greeting(name: str) -> str:
        """Return a greeting for the given name."""


class Casual:
    @extension
    def greeting(self, name: str) -> str:
        return f"hey {name}!"


pm = PluginManager("greeter")
pm.add_extension_points(Specs)
pm.register(Casual(), name="casual")

greetings = pm.caller(Specs.greeting)(name="Ada")   # typed list[str] - derived, not asserted
print(greetings)                                     # ['hey Ada!']
```

## What it supports

- collecting, `firstresult`, and **pipeline** (fold/middleware) hooks;
- call ordering with `tryfirst` / `trylast`, plus `optional` and `target`;
- generator **wrappers** that decorate results and observe exceptions safely;
- **historic** hooks replayed to plugins registered later;
- **async** dispatch via `AsyncPluginManager` (awaits coroutine impls);
- plugin lifecycle: `register`, `unregister` (by name or object), `set_blocked`,
  lookup, `call_extra`;
- registration-time validation and call-time argument checking (failures are loud);
- external plugin discovery via the stdlib `importlib.metadata` (no setuptools);
- thread-safe registry mutation.

## Layout

```
src/pluginkit/             the library (pure - no demo code)
examples/                  everything that uses the library (not shipped):
  cookbook/                  worked examples: bite-size scripts + full apps
  tour/                      pluginkit-tour: a guided CLI walkthrough
  external-plugin/           a separate distribution discovered via entry points
docs/                      mkdocs + Material documentation
tests/                     library, tour, and cookbook tests
```

Everything that demonstrates the library lives under `examples/`. The **cookbook**
holds standalone examples (from one-mechanism snippets to complete FastAPI/Click/pytest
apps); the **tour** is a guided walkthrough on one host; the **external-plugin** shows
cross-package discovery via entry points.

## Use it

```bash
make install              # uv sync (library + tour + external plugin)
make test                 # pytest (framework, tour, examples)
make lint                 # ruff + mypy + pyright
make docs-serve           # serve the docs at http://127.0.0.1:8000
make docs-build           # build the docs (strict)
```

## Two ways to learn it

**The tour** (`examples/tour/`) walks through one mechanism at a time on a single host:

```bash
make run                  # run every step
make run DEMO=wrapper      # run one
uv run pluginkit-tour list
```

**The cookbook** applies the library to realistic domains and frameworks - see
[`examples/cookbook/`](examples/cookbook/README.md):

```bash
uv run python examples/cookbook/report_builder.py
uv run python examples/cookbook/fastapi_app.py
uv run python examples/cookbook/cli_app.py --help
uv run python examples/cookbook/app_lifecycle.py
```

## Documentation

Full docs (concepts, one page per mechanism, production/hardening notes, and a
generated API reference) live under [`docs/`](docs/index.md). Serve them with
`make docs-serve`.

## Is it production ready?

It is solid - exception-safe wrappers, fail-fast validation, lifecycle management,
resilient discovery, thread-safe mutation, strict typing, and a test suite. But
for anything you ship, prefer **pluggy** itself: it is maintained and battle
tested by pytest, tox, and datasette. See
[docs/production/vs-pluggy.md](docs/production/vs-pluggy.md) for the honest
inventory of what differs.
