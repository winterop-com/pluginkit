# pluginkit

A small, **dependency-free**, [pluggy](https://pluggy.readthedocs.io/en/latest/)-style
plugin framework built from scratch with modern Python. It shows what a plugin
system like pluggy actually does under the hood, and is hardened enough to use.

The library is three files under `src/pluginkit/` (`markers.py`, `manager.py`,
`exceptions.py`), has **zero runtime dependencies** (standard library only), and
ships a `py.typed` marker.

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
src/pluginkit/          the library (pure - no demo code)
tour/                   pluginkit-tour: a guided CLI walkthrough, one step per mechanism
examples/               standalone single-file recipes, run directly
plugins/smoothie-extra/ an external plugin distribution (its own uv project)
benchmarks/             head-to-head benchmark against pluggy
docs/                   mkdocs + Material documentation
tests/                  library, tour, and example tests
```

The **tour** and **examples** are two complementary ways to learn it: the tour is
a guided walkthrough on one host (`pluginkit-tour run all`), while the examples
are independent, real-world recipes you run on their own.

## Use it

```bash
make install              # uv sync (library + tour + external plugin)
make test                 # pytest (framework, tour, examples)
make lint                 # ruff + mypy + pyright
make bench                # benchmark against pluggy
make docs-serve           # serve the docs at http://127.0.0.1:8000
make docs-build           # build the docs (strict)
```

## Two ways to learn it

**The tour** (`tour/`) walks through one mechanism at a time on a single host:

```bash
make run                  # run every step
make run DEMO=wrapper      # run one
uv run pluginkit-tour list
```

**The examples** apply the library to different realistic domains - see
[`examples/`](examples/README.md):

```bash
uv run python examples/report_builder.py
uv run python examples/notification_router.py
uv run python examples/validation_rules.py
uv run python examples/app_lifecycle.py
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
