# pluginkit

[![PyPI](https://img.shields.io/pypi/v/pluginkit.svg)](https://pypi.org/project/pluginkit/)
[![Python](https://img.shields.io/pypi/pyversions/pluginkit.svg)](https://pypi.org/project/pluginkit/)
[![CI](https://github.com/winterop-com/pluginkit/actions/workflows/ci.yml/badge.svg)](https://github.com/winterop-com/pluginkit/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-pages-blue.svg)](https://winterop-com.github.io/pluginkit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A small, **dependency-free** plugin framework for Python: declare hook
specifications, let plugins implement them, and discover plugins via entry points.
Supports sync and async dispatch, hook ordering, wrappers, pipeline (fold)
dispatch, and historic hooks - in a few readable files.

The library is three files under `src/pluginkit/` (`markers.py`, `manager.py`,
`exceptions.py`), has **zero runtime dependencies** (standard library only), runs on
**Python 3.11+**, and ships a `py.typed` marker.

```bash
pip install pluginkit   # or: uv add pluginkit
```

```python
from pluginkit import HookspecMarker, HookimplMarker, PluginManager

hookspec = HookspecMarker("greeter")
hookimpl = HookimplMarker("greeter")


class Specs:
    @staticmethod
    @hookspec
    def greeting(name: str) -> str:
        """Return a greeting for the given name."""


class Casual:
    @hookimpl
    def greeting(self, name: str) -> str:
        return f"hey {name}!"


pm = PluginManager("greeter")
pm.add_hookspecs(Specs)
pm.register(Casual(), name="casual")
print(pm.hook.greeting(name="Ada"))   # ['hey Ada!']
```

## What it supports

- collecting, `firstresult`, and **pipeline** (fold/middleware) hooks;
- call ordering with `tryfirst` / `trylast`, plus `optionalhook` and `specname`;
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
  recipes/                   standalone single-file scripts, run directly
  tour/                      pluginkit-tour: a guided CLI walkthrough
  external-plugin/           a separate distribution discovered via entry points
docs/                      mkdocs + Material documentation
tests/                     library, tour, and recipe tests
```

Everything that demonstrates the library lives under `examples/`. The **recipes**
are independent scripts you run on their own; the **tour** is a guided walkthrough
on one host; the **external-plugin** shows cross-package discovery via entry points.

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

**The recipes** apply the library to different realistic domains - see
[`examples/`](examples/README.md):

```bash
uv run python examples/recipes/report_builder.py
uv run python examples/recipes/notification_router.py
uv run python examples/recipes/validation_rules.py
uv run python examples/recipes/app_lifecycle.py
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
