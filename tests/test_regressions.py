"""Regression tests for the caller-correctness fixes."""

import asyncio
from collections.abc import Iterator

import pytest

from pluginkit import Extension, ExtensionPoint, PluginManager
from pluginkit.aio import AsyncPluginManager


def test_spec_default_args_are_optional_at_call_time():
    """A spec param with a default may be omitted; it is filled in for the impls."""
    extension_point = ExtensionPoint("def_demo")
    extension = Extension("def_demo")

    class Specs:
        @staticmethod
        @extension_point
        def greet(name: str, loud: bool = False) -> str: ...

    class Greeter:
        @extension
        def greet(self, name: str, loud: bool) -> str:
            return name.upper() if loud else name

    pm = PluginManager("def_demo")
    pm.add_extension_points(Specs)
    pm.register(Greeter())
    caller = pm.caller(Specs.greet)

    assert caller(name="Ada") == ["Ada"]  # default filled at call time
    assert caller(name="Ada", loud=True) == ["ADA"]

    # Required args are still enforced and unknown args still rejected (via the
    # untyped relay, which the type checker does not guard).
    with pytest.raises(TypeError, match="missing"):
        pm.hook.greet()
    with pytest.raises(TypeError, match="unknown"):
        pm.hook.greet(name="Ada", bogus=1)


def test_async_call_extra_validates_unknown_args():
    """AsyncHookCaller.call_extra rejects an extra impl with a clean TypeError, like sync."""
    extension_point = ExtensionPoint("ace")

    class Specs:
        @staticmethod
        @extension_point
        def fetch(topic: str) -> str: ...

    pm = AsyncPluginManager("ace")
    pm.add_extension_points(Specs)
    caller = pm.caller(Specs.fetch)

    async def bad(topic: str, bogus: int) -> str:  # declares an arg outside the spec
        return "x"

    async def run() -> None:
        with pytest.raises(TypeError, match="unknown argument"):
            await caller.call_extra([bad], {"topic": "t"})

    asyncio.run(run())


def test_double_yield_wrapper_still_unwinds_siblings():
    """A misbehaving wrapper does not abort teardown of the other wrappers."""
    extension_point = ExtensionPoint("dy")
    extension = Extension("dy")
    teardown_ran: list[str] = []

    class Specs:
        @staticmethod
        @extension_point
        def act() -> int: ...

    class Inner:
        @extension
        def act(self) -> int:
            return 1

    class GoodWrapper:
        @extension(wrapper=True)
        def act(self) -> Iterator[None]:
            try:
                yield
            finally:
                teardown_ran.append("good")

    class BadWrapper:
        @extension(wrapper=True)
        def act(self) -> Iterator[None]:
            yield
            yield  # violates the one-yield contract

    pm = PluginManager("dy")
    pm.add_extension_points(Specs)
    pm.register(Inner())
    pm.register(GoodWrapper())
    pm.register(BadWrapper())

    with pytest.raises(RuntimeError, match="must yield exactly once"):
        pm.caller(Specs.act)()
    # The good wrapper's finally ran during unwind, not deferred to GC.
    assert teardown_ran == ["good"]


def test_historic_caller_replays_and_rejects_direct_call():
    """A historic spec brands a HistoricCaller: call_historic works, a plain call raises."""
    extension_point = ExtensionPoint("hist")
    extension = Extension("hist")
    seen: list[str] = []

    class Specs:
        @staticmethod
        @extension_point(historic=True)
        def opened(name: str) -> None: ...

    class Plugin:
        @extension
        def opened(self, name: str) -> None:
            seen.append(name)

    pm = PluginManager("hist")
    pm.add_extension_points(Specs)
    pm.register(Plugin())

    pm.caller(Specs.opened).call_historic({"name": "Main Street"})
    assert seen == ["Main Street"]

    with pytest.raises(TypeError, match="call_historic"):
        pm.hook.opened(name="x")


def test_register_rolls_back_when_historic_replay_raises():
    """If wiring a plugin fails mid-way (historic replay raising), registration undoes itself."""
    extension_point = ExtensionPoint("rollback")
    extension = Extension("rollback")

    class Specs:
        @staticmethod
        @extension_point(historic=True)
        def event(value: int) -> None: ...

    pm = PluginManager("rollback")
    pm.add_extension_points(Specs)
    pm.caller(Specs.event).call_historic({"value": 1})  # a recorded call to replay

    class Boom:
        @extension
        def event(self, value: int) -> None:
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        pm.register(Boom())

    assert pm.plugin_names() == []  # rolled back, not left half-registered
    assert pm.get_plugin("Boom") is None
