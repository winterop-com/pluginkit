"""Type-level tests: PluginManager.caller derives mode-correct return types.

assert_type is a no-op at runtime but is verified by mypy and pyright, so these
double as both a behavioural test and a guarantee that the typing holds.
"""

import asyncio
from typing import assert_type

from pluginkit import AsyncPluginManager, Extension, ExtensionPoint, PluginManager

extension_point = ExtensionPoint("typing_demo")
extension = Extension("typing_demo")


class Specs:
    """Hook specs across all three dispatch modes."""

    @staticmethod
    @extension_point
    def collect(value: int) -> str: ...

    @staticmethod
    @extension_point(firstresult=True)
    def first(value: int) -> str | None: ...

    @staticmethod
    @extension_point(pipeline=True)
    def pipe(value: int) -> int: ...


class Plugin:
    """One implementation of each hook."""

    @staticmethod
    @extension
    def collect(value: int) -> str:
        """Return a label for the value."""
        return f"v{value}"

    @staticmethod
    @extension
    def pipe(value: int) -> int:
        """Double the threaded value."""
        return value * 2


def test_caller_return_types_and_runtime() -> None:
    pm = PluginManager("typing_demo")
    pm.add_extension_points(Specs)
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
        pm.add_extension_points(Specs)
        pm.register(Plugin())

        collected = await pm.caller(Specs.collect)(value=2)
        assert_type(collected, list[str])
        assert collected == ["v2"]

        piped = await pm.caller(Specs.pipe)(value=4)
        assert_type(piped, int)
        assert piped == 8

    asyncio.run(run())
