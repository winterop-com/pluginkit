"""Async dispatch: an AsyncPluginManager that awaits coroutine implementations.

The registration, validation and lifecycle machinery is reused unchanged from the
synchronous manager; only the *calling* path is asynchronous. Implementations may
be plain functions or coroutine functions - their results are awaited when
awaitable. Collecting, firstresult and pipeline dispatch are all supported.

Wrappers in the async manager are **async generators** and are observe-only: they
run setup before `yield` and teardown after it (including in a `finally`), and
they observe exceptions thrown back in, but - because async generators cannot
return a value - they do not replace the result. Use the synchronous manager when
a wrapper must transform the result.
"""

import inspect
from collections.abc import Callable
from types import AsyncGeneratorType
from typing import Any, overload

from pluginkit.manager import _UNSET, HookCaller, HookImpl, PluginManager
from pluginkit.markers import (
    CollectingSpec,
    FirstResultSpec,
    HookspecOpts,
    PipelineSpec,
)


class AsyncHookCaller(HookCaller):
    """A HookCaller whose calls are coroutines that await async implementations."""

    async def __call__(self, **kwargs: Any) -> Any:
        """Await the hook: a list, a single value (firstresult), or the threaded value (pipeline)."""
        if self.spec.historic:
            raise TypeError(f"historic hook {self.name!r} must be called via call_historic()")
        kwargs = self.check_arguments(kwargs)
        return await self._execute_async(kwargs, self._nonwrappers)

    async def call_extra(self, functions: list[Callable[..., Any]], kwargs: dict[str, Any]) -> Any:
        """Await the hook with extra one-off implementations that are not registered."""
        if self.spec.historic:
            raise TypeError(f"historic hook {self.name!r} must be called via call_historic()")
        kwargs = self.check_arguments(kwargs)
        combined = sorted(
            [*self._nonwrappers, *self._prepare_extra(functions)], key=lambda candidate: candidate.order_key
        )
        return await self._execute_async(kwargs, combined)

    def call_historic(self, kwargs: dict[str, Any], result_callback: Callable[[Any], None] | None = None) -> None:
        """Historic hooks are not supported by the async manager."""
        raise NotImplementedError("historic hooks are not supported by AsyncPluginManager")

    async def _execute_async(self, kwargs: dict[str, Any], nonwrappers: list[HookImpl]) -> Any:
        """Start async wrappers, run the impls, then unwind wrappers exception-safely."""
        started: list[AsyncGeneratorType[Any, Any]] = []
        try:
            for wrapper in self._wrappers:
                generator = wrapper.call(kwargs)
                if not isinstance(generator, AsyncGeneratorType):
                    raise TypeError(f"async wrapper {wrapper.plugin_name}.{self.name} must be an async generator")
                await generator.__anext__()  # advance to the yield
                started.append(generator)
            result = await self._core_async(kwargs, nonwrappers)
        except BaseException as exc:  # noqa: BLE001 - re-raised after wrappers observe it
            return await self._teardown_async(started, exc=exc)
        return await self._teardown_async(started, result=result)

    async def _core_async(self, kwargs: dict[str, Any], nonwrappers: list[HookImpl]) -> Any:
        """Apply the spec's dispatch strategy, awaiting any awaitable results."""
        if self.spec.pipeline:
            return await self._run_pipeline_async(kwargs, nonwrappers)
        results: list[Any] = []
        for impl in nonwrappers:
            outcome = await _maybe_await(impl.call(kwargs))
            if outcome is None:
                continue
            results.append(outcome)
            if self.spec.firstresult:
                break
        return (results[0] if results else None) if self.spec.firstresult else results

    async def _run_pipeline_async(self, kwargs: dict[str, Any], nonwrappers: list[HookImpl]) -> Any:
        """Thread the first argument through each impl, awaiting awaitable results."""
        param = self.params[0]
        value = kwargs[param]
        current = dict(kwargs)
        for impl in nonwrappers:
            current[param] = value
            outcome = await _maybe_await(impl.call(current))
            if outcome is not None:
                value = outcome
        return value

    async def _teardown_async(
        self, started: list[AsyncGeneratorType[Any, Any]], *, result: Any = _UNSET, exc: BaseException | None = None
    ) -> Any:
        """Resume each async wrapper in reverse so its teardown runs and it observes errors."""
        for generator in reversed(started):
            try:
                if exc is not None:
                    await generator.athrow(exc)
                else:
                    await generator.asend(result)
            except StopAsyncIteration:
                pass  # normal completion; async wrappers cannot replace the result
            except BaseException as new_exc:  # noqa: BLE001 - propagate the wrapper's error onward
                exc = new_exc
            else:
                # Double yield: capture the error but keep unwinding the remaining
                # wrappers so their teardown still runs; raised after the loop.
                await generator.aclose()
                exc = RuntimeError(f"async wrapper for {self.name!r} must yield exactly once")
        if exc is not None:
            raise exc
        return result


# Async typed views returned by AsyncPluginManager.caller(); never instantiated
# (the runtime object is an AsyncHookCaller). Awaiting a call yields the mode type.
class AsyncCollectingCaller[**P, R](AsyncHookCaller):
    """A collecting async hook's typed caller: `await` a call to get `list[R]`."""

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> list[R]:
        """Await the collecting hook, returning each impl's result as `list[R]`."""
        raise NotImplementedError  # pragma: no cover - the runtime object is an AsyncHookCaller


class AsyncFirstResultCaller[**P, R](AsyncHookCaller):
    """A firstresult async hook's typed caller: `await` a call to get `R | None`."""

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R | None:
        """Await the firstresult hook, returning the first non-None `R` or `None`."""
        raise NotImplementedError  # pragma: no cover - the runtime object is an AsyncHookCaller


class AsyncPipelineCaller[**P, R](AsyncHookCaller):
    """A pipeline async hook's typed caller: `await` a call to get `R`."""

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Await the pipeline hook, returning the threaded value `R`."""
        raise NotImplementedError  # pragma: no cover - the runtime object is an AsyncHookCaller


class AsyncPluginManager(PluginManager):
    """A PluginManager whose hooks are awaited; impls may be coroutine functions."""

    def _make_caller(
        self, name: str, spec: HookspecOpts, params: tuple[str, ...], defaults: dict[str, Any]
    ) -> HookCaller:
        """Build an AsyncHookCaller instead of the synchronous one."""
        return AsyncHookCaller(name=name, spec=spec, params=params, defaults=defaults)

    @overload  # type: ignore[override]  # async manager returns awaitable callers
    def caller[**P, R](self, spec: FirstResultSpec[P, R]) -> AsyncFirstResultCaller[P, R]: ...
    @overload
    def caller[**P, R](self, spec: PipelineSpec[P, R]) -> AsyncPipelineCaller[P, R]: ...
    @overload
    def caller[**P, R](self, spec: CollectingSpec[P, R]) -> AsyncCollectingCaller[P, R]: ...
    def caller(  # pyright: ignore[reportIncompatibleMethodOverride]  # async returns awaitable callers
        self, spec: object
    ) -> HookCaller:
        """Return the typed async caller for a `@hookspec`-decorated spec function."""
        return self._caller(spec)


async def _maybe_await(value: Any) -> Any:
    """Await a value if it is awaitable, otherwise return it unchanged."""
    if inspect.isawaitable(value):
        return await value
    return value
