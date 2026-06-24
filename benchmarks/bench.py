"""Head-to-head micro-benchmark of pluginkit against pluggy on identical hosts.

Both libraries expose the same surface (HookspecMarker / HookimplMarker /
PluginManager / pm.hook.<name>), so each scenario is built once per library from
the same factory and timed the same way. Results are best-of-repeats to reduce
noise. Run: python benchmarks/bench.py
"""

import time
from collections.abc import Callable
from typing import Any

import pluggy

import pluginkit

ADAPTERS: dict[str, Any] = {
    "pluggy": pluggy,
    "pluginkit": pluginkit,
}


def build_markers(lib: Any) -> tuple[Any, Any, Callable[[str], Any]]:
    """Return (hookspec, hookimpl, PluginManager) for a library module."""
    return lib.HookspecMarker("bench"), lib.HookimplMarker("bench"), lib.PluginManager


def make_collecting(lib: Any, n_impls: int) -> Any:
    """Build a manager with a collecting hook and n_impls plugins."""
    hookspec, hookimpl, manager_cls = build_markers(lib)

    class Specs:
        @staticmethod
        @hookspec
        def work(x: int) -> int:
            """Collecting hook."""

    class Plugin:
        @hookimpl
        def work(self, x: int) -> int:
            """Return a constant."""
            return 1

    pm = manager_cls("bench")
    pm.add_hookspecs(Specs)
    for index in range(n_impls):
        pm.register(Plugin(), name=f"p{index}")
    return pm


def make_firstresult(lib: Any, n_impls: int) -> Any:
    """Build a manager with a firstresult hook and n_impls answering plugins."""
    hookspec, hookimpl, manager_cls = build_markers(lib)

    class Specs:
        @staticmethod
        @hookspec(firstresult=True)
        def work(x: int) -> int:
            """Firstresult hook."""

    class Plugin:
        @hookimpl
        def work(self, x: int) -> int:
            """Always answer."""
            return 1

    pm = manager_cls("bench")
    pm.add_hookspecs(Specs)
    for index in range(n_impls):
        pm.register(Plugin(), name=f"p{index}")
    return pm


def make_wrapped(lib: Any, n_wrappers: int) -> Any:
    """Build a manager with one worker wrapped by n_wrappers generator wrappers."""
    hookspec, hookimpl, manager_cls = build_markers(lib)

    class Specs:
        @staticmethod
        @hookspec
        def work(x: int) -> int:
            """Hook wrapped by generator wrappers."""

    class Worker:
        @hookimpl
        def work(self, x: int) -> int:
            """Do the work."""
            return 1

    class Wrapper:
        @hookimpl(wrapper=True)
        def work(self, x: int) -> Any:
            """Pass the result through untouched."""
            result = yield
            return result

    pm = manager_cls("bench")
    pm.add_hookspecs(Specs)
    pm.register(Worker(), name="worker")
    for index in range(n_wrappers):
        pm.register(Wrapper(), name=f"w{index}")
    return pm


def time_call(pm: Any, iterations: int, repeats: int = 5) -> float:
    """Return the best-of-repeats nanoseconds per pm.hook.work(x=1) call."""
    hook = pm.hook.work
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter_ns()
        for _ in range(iterations):
            hook(x=1)
        elapsed = time.perf_counter_ns() - start
        best = min(best, elapsed / iterations)
    return best


def time_registration(lib: Any, n_impls: int, repeats: int = 5) -> float:
    """Return the best-of-repeats microseconds to build a manager and register n_impls."""
    hookspec, hookimpl, manager_cls = build_markers(lib)

    class Specs:
        @staticmethod
        @hookspec
        def work(x: int) -> int:
            """Collecting hook."""

    class Plugin:
        @hookimpl
        def work(self, x: int) -> int:
            """Return a constant."""
            return 1

    plugins = [Plugin() for _ in range(n_impls)]
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter_ns()
        pm = manager_cls("bench")
        pm.add_hookspecs(Specs)
        for index, plugin in enumerate(plugins):
            pm.register(plugin, name=f"p{index}")
        elapsed = time.perf_counter_ns() - start
        best = min(best, elapsed / 1000)
    return best


def report(title: str, unit: str, results: dict[str, float]) -> None:
    """Print one scenario's per-library result and the pluginkit/pluggy ratio."""
    pluggy_value = results["pluggy"]
    pluginkit_value = results["pluginkit"]
    ratio = pluginkit_value / pluggy_value if pluggy_value else float("inf")
    print(f"{title:<34} pluggy={pluggy_value:8.1f}{unit}  pluginkit={pluginkit_value:8.1f}{unit}  ({ratio:.2f}x)")


def main() -> None:
    """Run every scenario for both libraries and print a comparison table."""
    iterations = 200_000
    print(f"versions: pluggy {pluggy.__version__}, pluginkit {pluginkit.__version__}")
    print(f"call scenarios: {iterations:,} iterations, best of 5; ratio = pluginkit / pluggy (lower is better)\n")

    scenarios: list[tuple[str, Callable[[Any], Any]]] = [
        ("call: collecting, 5 impls", lambda lib: make_collecting(lib, 5)),
        ("call: collecting, 20 impls", lambda lib: make_collecting(lib, 20)),
        ("call: firstresult, 5 impls", lambda lib: make_firstresult(lib, 5)),
        ("call: wrapped, 2 wrappers", lambda lib: make_wrapped(lib, 2)),
    ]
    for title, factory in scenarios:
        results = {name: time_call(factory(lib), iterations) for name, lib in ADAPTERS.items()}
        report(title, "ns", results)

    print()
    for n_impls in (10, 100):
        results = {name: time_registration(lib, n_impls) for name, lib in ADAPTERS.items()}
        report(f"register: {n_impls} plugins", "us", results)


if __name__ == "__main__":
    main()
