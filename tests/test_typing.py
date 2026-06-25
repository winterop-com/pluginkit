"""Type-level tests: PluginManager.caller derives mode-correct return types.

assert_type is a no-op at runtime but is verified by mypy and pyright, so these
double as both a behavioural test and a guarantee that the typing holds.
"""

import asyncio
from typing import assert_type

from pluginkit import AsyncPluginManager, HookimplMarker, HookspecMarker, PluginManager

hookspec = HookspecMarker("typing_demo")
hookimpl = HookimplMarker("typing_demo")


class Specs:
    """Hook specs across all three dispatch modes."""

    @staticmethod
    @hookspec
    def collect(value: int) -> str: ...

    @staticmethod
    @hookspec(firstresult=True)
    def first(value: int) -> str | None: ...

    @staticmethod
    @hookspec(pipeline=True)
    def pipe(value: int) -> int: ...


class Plugin:
    """One implementation of each hook."""

    @staticmethod
    @hookimpl
    def collect(value: int) -> str:
        """Return a label for the value."""
        return f"v{value}"

    @staticmethod
    @hookimpl
    def pipe(value: int) -> int:
        """Double the threaded value."""
        return value * 2


def test_caller_return_types_and_runtime() -> None:
    pm = PluginManager("typing_demo")
    pm.add_hookspecs(Specs)
    pm.register(Plugin())

    collected = pm.caller(Specs.collect)(value=1)
    assert_type(collected, list[str])
    assert collected == ["v1"]

    chosen = pm.caller(Specs.first)(value=1)
    assert_type(chosen, str | None)
    assert chosen is None  # no firstresult impl registered

    piped = pm.caller(Specs.pipe)(value=3)
    assert_type(piped, int)
    assert piped == 6


def test_async_caller_return_types() -> None:
    async def run() -> None:
        pm = AsyncPluginManager("typing_demo")
        pm.add_hookspecs(Specs)
        pm.register(Plugin())

        collected = await pm.caller(Specs.collect)(value=2)
        assert_type(collected, list[str])
        assert collected == ["v2"]

        piped = await pm.caller(Specs.pipe)(value=4)
        assert_type(piped, int)
        assert piped == 8

    asyncio.run(run())
