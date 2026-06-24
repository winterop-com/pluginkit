"""Unit tests for the from-scratch framework internals."""

import asyncio

import pytest

from pluginkit import (
    AsyncPluginManager,
    HookimplMarker,
    HookspecMarker,
    PluginManager,
    PluginValidationError,
)
from pluginkit.manager import HookCaller, HookImpl
from pluginkit.markers import HookimplOpts, HookspecOpts


def _project(name: str) -> tuple[HookspecMarker, HookimplMarker]:
    return HookspecMarker(name), HookimplMarker(name)


def _manager_with_specs(specs: object, project: str = "demo") -> PluginManager:
    pm = PluginManager(project)
    pm.add_hookspecs(specs)
    return pm


def test_marker_supports_bare_and_called_forms():
    hookimpl = HookimplMarker("demo")

    @hookimpl
    def bare() -> None: ...

    @hookimpl(tryfirst=True, specname="other")
    def called() -> None: ...

    assert getattr(bare, "demo_impl") == HookimplOpts()
    assert getattr(called, "demo_impl") == HookimplOpts(tryfirst=True, specname="other")


def test_impl_only_receives_declared_kwargs():
    impl = HookImpl.from_function("p", lambda base: base, HookimplOpts())
    # Extra kwargs (size) are filtered out; only declared ones reach the function.
    assert impl.call({"base": ["x"], "size": "large"}) == ["x"]


def test_collecting_hook_drops_none_results():
    caller = HookCaller("h", HookspecOpts(), argnames=frozenset())
    caller.add_impl(HookImpl.from_function("a", lambda: "kept", HookimplOpts()))
    caller.add_impl(HookImpl.from_function("b", lambda: None, HookimplOpts()))
    assert caller() == ["kept"]


def test_unknown_hook_registration_raises():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec
        def known() -> None: ...

    pm = _manager_with_specs(Specs)

    class Bad:
        @hookimpl
        def unknown(self) -> None: ...

    with pytest.raises(PluginValidationError, match="unknown hook"):
        pm.register(Bad())


def test_optionalhook_tolerates_unknown_hook():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec
        def known() -> None: ...

    pm = _manager_with_specs(Specs)

    class Optional:
        @hookimpl(optionalhook=True)
        def not_specified(self) -> None: ...

    # Registration succeeds even though the host never specified the hook.
    assert pm.register(Optional(), name="optional") == "optional"


def test_specname_binds_impl_to_a_differently_named_spec():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec
        def greet(name: str) -> str: ...

    pm = _manager_with_specs(Specs)

    class Plugin:
        @hookimpl(specname="greet")
        def my_greet(self, name: str) -> str:
            return f"hi {name}"

    pm.register(Plugin(), name="p")
    assert pm.hook.greet(name="ada") == ["hi ada"]


def test_impl_with_unknown_argument_is_rejected():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec
        def greet(name: str) -> str: ...

    pm = _manager_with_specs(Specs)

    class Typo:
        @hookimpl
        def greet(self, nam: str) -> str:  # misspelled argument
            return nam

    with pytest.raises(PluginValidationError, match="unknown argument"):
        pm.register(Typo(), name="typo")


def test_duplicate_name_and_object_registration_raise():
    pm = PluginManager("demo")
    plugin = object()
    pm.register(plugin, name="dup")
    with pytest.raises(ValueError, match="name 'dup' is already registered"):
        pm.register(object(), name="dup")
    with pytest.raises(ValueError, match="object .* is already registered"):
        pm.register(plugin, name="other")


def test_unregister_removes_impls():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec
        def add(base: list[str]) -> list[str]: ...

    pm = _manager_with_specs(Specs)

    class Plugin:
        @hookimpl
        def add(self, base: list[str]) -> list[str]:
            return ["x"]

    pm.register(Plugin(), name="p")
    assert pm.hook.add(base=[]) == [["x"]]
    pm.unregister("p")
    assert pm.hook.add(base=[]) == []
    assert pm.plugin_names() == []


def test_set_blocked_unregisters_and_prevents_registration():
    pm = PluginManager("demo")
    pm.register(object(), name="p")
    pm.set_blocked("p")
    assert pm.is_blocked("p")
    assert pm.get_plugin("p") is None
    with pytest.raises(ValueError, match="blocked"):
        pm.register(object(), name="p")


def test_lookup_helpers():
    pm = PluginManager("demo")
    plugin = object()
    pm.register(plugin, name="p")
    assert pm.is_registered(plugin)
    assert pm.get_plugin("p") is plugin
    assert pm.get_name(plugin) == "p"


def test_wrapper_cleanup_runs_when_inner_impl_raises():
    hookspec, hookimpl = _project("demo")
    closed: list[str] = []

    class Specs:
        @staticmethod
        @hookspec
        def work() -> str: ...

    pm = _manager_with_specs(Specs)

    class Worker:
        @hookimpl
        def work(self) -> str:
            raise RuntimeError("boom")

    class Wrapper:
        @hookimpl(wrapper=True)
        def work(self):
            try:
                yield
            finally:
                # This must run even though the inner impl raised.
                closed.append("cleaned up")

    pm.register(Worker(), name="worker")
    pm.register(Wrapper(), name="wrapper")

    with pytest.raises(RuntimeError, match="boom"):
        pm.hook.work()
    assert closed == ["cleaned up"]


def test_wrapper_can_suppress_inner_exception():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec(firstresult=True)
        def work() -> str: ...

    pm = _manager_with_specs(Specs)

    class Worker:
        @hookimpl
        def work(self) -> str:
            raise RuntimeError("boom")

    class Recover:
        @hookimpl(wrapper=True)
        def work(self):
            try:
                return (yield)
            except RuntimeError:
                return "recovered"

    pm.register(Worker(), name="worker")
    pm.register(Recover(), name="recover")
    assert pm.hook.work() == "recovered"


def test_call_time_argument_validation():
    hookspec, _ = _project("demo")

    class Specs:
        @staticmethod
        @hookspec
        def greet(name: str) -> str: ...

    pm = _manager_with_specs(Specs)
    with pytest.raises(TypeError, match="unknown"):
        pm.hook.greet(name="x", extra=1)
    with pytest.raises(TypeError, match="missing"):
        pm.hook.greet()


def test_unregister_by_object():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec
        def add(base: list[str]) -> list[str]: ...

    pm = _manager_with_specs(Specs)

    class Plugin:
        @hookimpl
        def add(self, base: list[str]) -> list[str]:
            return ["x"]

    plugin = Plugin()
    pm.register(plugin, name="p")
    assert pm.unregister(plugin) is plugin
    assert pm.plugin_names() == []
    assert pm.unregister(object()) is None


def test_wrapper_on_historic_hook_is_rejected():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec(historic=True)
        def started(name: str) -> None: ...

    pm = _manager_with_specs(Specs)

    class Bad:
        @hookimpl(wrapper=True)
        def started(self, name: str):
            yield

    with pytest.raises(PluginValidationError, match="historic hook .* cannot have a wrapper"):
        pm.register(Bad(), name="bad")


def test_call_extra_runs_unregistered_impls_for_one_call():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec
        def add(base: list[str]) -> list[str]: ...

    pm = _manager_with_specs(Specs)

    class Plugin:
        @hookimpl
        def add(self, base: list[str]) -> list[str]:
            return ["registered"]

    pm.register(Plugin(), name="p")

    def extra(base: list[str]) -> list[str]:
        return ["temporary"]

    assert pm.hook.add.call_extra([extra], {"base": []}) == [["registered"], ["temporary"]]
    # The extra impl does not persist.
    assert pm.hook.add(base=[]) == [["registered"]]

    # An extra that declares an argument the spec lacks is rejected.
    def bad(base: list[str], oops: int) -> list[str]:
        return []

    with pytest.raises(TypeError, match="unknown argument"):
        pm.hook.add.call_extra([bad], {"base": []})


def test_get_hookcallers_reports_a_plugins_hooks():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec
        def add(base: list[str]) -> list[str]: ...

    pm = _manager_with_specs(Specs)

    class Plugin:
        @hookimpl
        def add(self, base: list[str]) -> list[str]:
            return ["x"]

    plugin = Plugin()
    pm.register(plugin, name="p")
    callers = pm.get_hookcallers(plugin)
    assert callers is not None
    assert [caller.name for caller in callers] == ["add"]
    assert pm.get_hookcallers(object()) is None


def test_repr_is_informative():
    pm = PluginManager("demo")
    assert "demo" in repr(pm)
    assert "plugins=0" in repr(pm)


def test_pipeline_threads_value_through_impls():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec(pipeline=True)
        def transform(value: int) -> int: ...

    pm = _manager_with_specs(Specs)

    class Doubler:
        @hookimpl(tryfirst=True)
        def transform(self, value: int) -> int:
            return value * 2

    class AddTen:
        @hookimpl
        def transform(self, value: int) -> int:
            return value + 10

    class NoOp:
        @hookimpl
        def transform(self, value: int) -> int | None:
            return None  # passes the value through unchanged

    pm.register(AddTen(), name="add")
    pm.register(NoOp(), name="noop")
    pm.register(Doubler(), name="double")
    # tryfirst doubles 5 -> 10, then +10 -> 20, noop leaves it.
    assert pm.hook.transform(value=5) == 20


def test_pipeline_cannot_combine_with_other_modes():
    hookspec = HookspecMarker("demo")

    class Specs:
        @staticmethod
        @hookspec(pipeline=True, firstresult=True)
        def bad(value: int) -> int: ...

    pm = PluginManager("demo")
    with pytest.raises(ValueError, match="cannot combine"):
        pm.add_hookspecs(Specs)


def test_pipeline_requires_an_argument():
    hookspec = HookspecMarker("demo")

    class Specs:
        @staticmethod
        @hookspec(pipeline=True)
        def bad() -> int: ...

    pm = PluginManager("demo")
    with pytest.raises(ValueError, match="must declare at least one argument"):
        pm.add_hookspecs(Specs)


def test_async_manager_collects_from_async_and_sync_impls():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec
        def fetch(topic: str) -> str: ...

    pm = AsyncPluginManager("demo")
    pm.add_hookspecs(Specs)

    class AsyncSource:
        @hookimpl
        async def fetch(self, topic: str) -> str:
            await asyncio.sleep(0)
            return f"async:{topic}"

    class SyncSource:
        @hookimpl
        def fetch(self, topic: str) -> str:
            return f"sync:{topic}"

    pm.register(AsyncSource(), name="a")
    pm.register(SyncSource(), name="s")
    result = asyncio.run(pm.hook.fetch(topic="x"))
    assert set(result) == {"async:x", "sync:x"}


def test_async_pipeline_and_firstresult():
    hookspec, hookimpl = _project("demo")

    class Specs:
        @staticmethod
        @hookspec(pipeline=True)
        def step(value: int) -> int: ...

        @staticmethod
        @hookspec(firstresult=True)
        def pick(size: str) -> str: ...

    pm = AsyncPluginManager("demo")
    pm.add_hookspecs(Specs)

    class Plugin:
        @hookimpl
        async def step(self, value: int) -> int:
            await asyncio.sleep(0)
            return value + 1

        @hookimpl
        async def pick(self, size: str) -> str:
            return f"chosen:{size}"

    pm.register(Plugin(), name="p")
    assert asyncio.run(pm.hook.step(value=10)) == 11
    assert asyncio.run(pm.hook.pick(size="L")) == "chosen:L"


def test_async_wrapper_teardown_runs_on_error():
    hookspec, hookimpl = _project("demo")
    closed: list[str] = []

    class Specs:
        @staticmethod
        @hookspec
        def work() -> str: ...

    pm = AsyncPluginManager("demo")
    pm.add_hookspecs(Specs)

    class Worker:
        @hookimpl
        async def work(self) -> str:
            raise RuntimeError("boom")

    class Wrapper:
        @hookimpl(wrapper=True)
        async def work(self):
            try:
                yield
            finally:
                closed.append("cleaned up")

    pm.register(Worker(), name="worker")
    pm.register(Wrapper(), name="wrapper")

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(pm.hook.work())
    assert closed == ["cleaned up"]


def test_historic_and_firstresult_combo_is_rejected():
    hookspec = HookspecMarker("demo")

    class Specs:
        @staticmethod
        @hookspec(historic=True, firstresult=True)
        def bad() -> None: ...

    pm = PluginManager("demo")
    with pytest.raises(ValueError, match="cannot combine"):
        pm.add_hookspecs(Specs)
