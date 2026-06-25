"""The plugin manager: registers plugins and dispatches calls to their hooks.

A compact but hardened reimplementation of the pluggy ideas worth understanding:

- introspection-based discovery of specs and impls via stamped attributes;
- registration-time validation that impl arguments exist in the spec;
- per-impl keyword-argument filtering so an impl declares only what it needs;
- call ordering with tryfirst / trylast;
- collecting vs firstresult dispatch;
- generator wrappers that decorate the result and observe exceptions safely;
- historic hooks replayed to plugins registered later;
- plugin lifecycle: unregister, blocking, and lookup;
- external plugin discovery via the stdlib importlib.metadata.

The manager is safe to mutate (register / unregister / block) from multiple
threads; hook *calls* are not internally locked and should be coordinated by the
caller if they can race with registration.
"""

import inspect
import threading
from collections.abc import Callable, Generator, Iterator
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from types import GeneratorType
from typing import Any, NoReturn, Self, overload

from pluginkit.exceptions import PluginValidationError
from pluginkit.markers import (
    CollectingSpec,
    ExtensionOpts,
    ExtensionPointOpts,
    FirstResultSpec,
    HistoricSpec,
    PipelineSpec,
)

# Sentinel distinguishing "no result yet" from a legitimate None result.
_UNSET: Any = object()

# pluginkit dispatches by keyword (each impl receives the subset of named arguments it
# declares), so every parameter must be addressable by name.
_KEYWORD_DISPATCHABLE = frozenset({inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY})


def _positional_arity(signature: inspect.Signature, label: str, name: str) -> int:
    """Validate that every parameter can be passed by keyword and return the positional arity.

    Rejects positional-only, `*args`, and `**kwargs` parameters (none are addressable by a
    fixed name), and returns how many leading parameters may *also* be passed positionally -
    so a positional call binds exactly the arguments the ParamSpec allows positionally.
    """
    arity = 0
    for param_name, parameter in signature.parameters.items():
        if parameter.kind not in _KEYWORD_DISPATCHABLE:
            raise ValueError(
                f"{label} {name!r} parameter {param_name!r} is {parameter.kind.description}; "
                f"pluginkit dispatches by keyword, so only positional-or-keyword and keyword-only "
                f"parameters are supported"
            )
        if parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
            arity += 1
    return arity


@dataclass(slots=True)
class HookImpl:
    """One plugin's implementation of a hook, plus the kwargs it accepts."""

    plugin_name: str
    function: Callable[..., Any]
    opts: ExtensionOpts
    accepts: frozenset[str]
    params: tuple[str, ...]
    # Set by the caller once it knows the hook's full argument set: True when this
    # impl declares exactly those arguments, so kwargs can be forwarded directly.
    passthrough: bool = False

    @classmethod
    def from_function(cls, plugin_name: str, function: Callable[..., Any], opts: ExtensionOpts) -> Self:
        """Build an impl, recording which keyword arguments the function declares."""
        signature = inspect.signature(function)
        _positional_arity(signature, "implementation", getattr(function, "__qualname__", plugin_name))
        params = tuple(signature.parameters)
        return cls(plugin_name=plugin_name, function=function, opts=opts, accepts=frozenset(params), params=params)

    def call(self, kwargs: dict[str, Any]) -> Any:
        """Invoke the function, passing only the arguments it declares.

        The caller guarantees every declared argument is present in kwargs, so the
        common "takes all the spec's arguments" case forwards kwargs directly and a
        subset impl indexes the few it wants - both avoiding a membership scan.
        """
        if self.passthrough:
            return self.function(**kwargs)
        return self.function(**{name: kwargs[name] for name in self.params})

    @property
    def order_key(self) -> int:
        """Sort key: tryfirst impls run first (0), normal next (1), trylast last (2)."""
        match self.opts:
            case ExtensionOpts(tryfirst=True):
                return 0
            case ExtensionOpts(trylast=True):
                return 2
            case _:
                return 1


@dataclass(slots=True)
class HookCaller:
    """Holds every implementation of one hook and dispatches calls to them."""

    name: str
    spec: ExtensionPointOpts
    params: tuple[str, ...] = ()
    argnames: frozenset[str] = frozenset()
    # Default values for spec params that declare one. A call may omit these (the
    # branded caller's ParamSpec makes them optional); they are filled in at call
    # time so the type checker and the runtime agree.
    defaults: dict[str, Any] = field(default_factory=dict)
    # How many leading params may be passed positionally (the rest are keyword-only);
    # -1 means "derive as all params" for callers built directly without kind info.
    positional_arity: int = -1
    _impls: list[HookImpl] = field(default_factory=list)
    _wrappers: list[HookImpl] = field(default_factory=list)
    _nonwrappers: list[HookImpl] = field(default_factory=list)
    _history: list[tuple[dict[str, Any], Callable[[Any], None] | None]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Derive the argument-name set from the ordered parameters when given."""
        if self.params and not self.argnames:
            self.argnames = frozenset(self.params)
        if self.positional_arity < 0:
            self.positional_arity = len(self.params)

    def check_arguments(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Fill any omitted defaulted args, then validate the call against the spec.

        Returns the completed kwargs (defaults filled). Spec params with a default
        are optional at the call site; required params and unknown args are still
        rejected.
        """
        if self.defaults:
            kwargs = {**self.defaults, **kwargs}
        # dict_keys compares as a set against the frozenset without allocating one.
        if kwargs.keys() == self.argnames:
            return kwargs
        provided = frozenset(kwargs)
        problems: list[str] = []
        missing = self.argnames - provided
        unknown = provided - self.argnames
        if missing:
            problems.append(f"missing {sorted(missing)}")
        if unknown:
            problems.append(f"unknown {sorted(unknown)}")
        raise TypeError(f"hook {self.name!r} called with {'; '.join(problems)}; expects {sorted(self.argnames)}")

    def add_impl(self, impl: HookImpl) -> None:
        """Add an impl in priority order and replay any historic calls to it."""
        impl.passthrough = impl.accepts == self.argnames
        self._impls.append(impl)
        self._reindex()
        for kwargs, callback in self._history:
            outcome = impl.call(kwargs)
            if outcome is not None and callback is not None:
                callback(outcome)

    def remove_plugin(self, plugin_name: str) -> bool:
        """Drop every impl contributed by a plugin; return True if any were removed."""
        before = len(self._impls)
        self._impls = [impl for impl in self._impls if impl.plugin_name != plugin_name]
        removed = len(self._impls) != before
        if removed:
            self._reindex()
        return removed

    def has_plugin(self, plugin_name: str) -> bool:
        """Return whether the named plugin contributes any impl to this hook."""
        return any(impl.plugin_name == plugin_name for impl in self._impls)

    def _prepare_extra(self, functions: list[Callable[..., Any]]) -> list[HookImpl]:
        """Build one-off impls for call_extra, validating their args against the spec."""
        extra: list[HookImpl] = []
        for function in functions:
            impl = HookImpl.from_function("<call_extra>", function, ExtensionOpts())
            unknown = impl.accepts - self.argnames
            if unknown:
                raise TypeError(f"call_extra impl for {self.name!r} declares unknown argument(s) {sorted(unknown)}")
            impl.passthrough = impl.accepts == self.argnames
            extra.append(impl)
        return extra

    def _bind(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Bind positional args to the spec's params (in order) and merge with kwargs.

        Lets a typed caller be invoked positionally - `caller(value)` as well as
        `caller(name=value)` - matching what the ParamSpec advertises.
        """
        if not args:
            return kwargs
        if len(args) > self.positional_arity:
            raise TypeError(f"hook {self.name!r} takes at most {self.positional_arity} positional argument(s)")
        positional = dict(zip(self.params[: self.positional_arity], args, strict=False))
        clash = positional.keys() & kwargs.keys()
        if clash:
            raise TypeError(f"hook {self.name!r} got multiple values for {sorted(clash)}")
        return {**positional, **kwargs}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the hook: a list, a single value (firstresult), or the threaded value (pipeline)."""
        if self.spec.historic:
            raise TypeError(f"historic hook {self.name!r} must be called via call_historic()")
        kwargs = self.check_arguments(self._bind(args, kwargs))
        return self._execute(kwargs, self._nonwrappers)

    def call_extra(self, functions: list[Callable[..., Any]], kwargs: dict[str, Any]) -> Any:
        """Call the hook with extra one-off implementations that are not registered.

        The extra functions run as normal-priority implementations for this call
        only, ordered after the already-registered ones. Useful for tests and for
        injecting a temporary implementation without mutating the manager.
        """
        if self.spec.historic:
            raise TypeError(f"historic hook {self.name!r} must be called via call_historic()")
        kwargs = self.check_arguments(kwargs)
        combined = sorted(
            [*self._nonwrappers, *self._prepare_extra(functions)], key=lambda candidate: candidate.order_key
        )
        return self._execute(kwargs, combined)

    def call_historic(self, kwargs: dict[str, Any], result_callback: Callable[[Any], None] | None = None) -> None:
        """Call a historic hook now and remember it for plugins registered later."""
        if not self.spec.historic:
            raise TypeError(f"hook {self.name!r} is not historic")
        kwargs = self.check_arguments(kwargs)
        # Snapshot the event so a later mutation of the caller's dict can't change
        # what plugins registered after this call replay.
        self._history.append((dict(kwargs), result_callback))
        for outcome in self._collect(kwargs):
            if result_callback is not None:
                result_callback(outcome)

    def _reindex(self) -> None:
        """Re-sort impls by priority and refresh the wrapper / non-wrapper split."""
        # Stable sort keeps registration order within each priority bucket.
        self._impls.sort(key=lambda candidate: candidate.order_key)
        self._wrappers = [impl for impl in self._impls if impl.opts.wrapper]
        self._nonwrappers = [impl for impl in self._impls if not impl.opts.wrapper]

    def _execute(self, kwargs: dict[str, Any], nonwrappers: list[HookImpl]) -> Any:
        """Run the inner impls, wrapped by any wrappers, unwinding exception-safely."""
        # Fast path: with no wrappers there is nothing to unwind, so skip the
        # try/except and generator bookkeeping entirely and let errors propagate.
        if not self._wrappers:
            return self._core(kwargs, nonwrappers)
        started: list[Generator[Any, Any, Any]] = []
        try:
            for wrapper in self._wrappers:
                generator = wrapper.call(kwargs)
                if not isinstance(generator, GeneratorType):
                    raise TypeError(f"wrapper {wrapper.plugin_name}.{self.name} must be a generator function")
                next(generator)  # advance to the yield
                started.append(generator)
            result = self._core(kwargs, nonwrappers)
        except BaseException as exc:  # noqa: BLE001 - re-raised after wrappers observe it
            return self._teardown(started, exc=exc)
        return self._teardown(started, result=result)

    def _core(self, kwargs: dict[str, Any], nonwrappers: list[HookImpl]) -> Any:
        """Apply the spec's dispatch strategy to the non-wrapper impls."""
        if self.spec.pipeline:
            return self._run_pipeline(kwargs, nonwrappers)
        if self.spec.firstresult:
            for impl in nonwrappers:
                outcome = impl.call(kwargs)
                if outcome is not None:
                    return outcome
            return None
        results: list[Any] = []
        for impl in nonwrappers:
            outcome = impl.call(kwargs)
            if outcome is not None:
                results.append(outcome)
        return results

    def _run_pipeline(self, kwargs: dict[str, Any], nonwrappers: list[HookImpl]) -> Any:
        """Thread the first argument through each impl, feeding its result to the next."""
        param = self.params[0]
        value = kwargs[param]
        current = dict(kwargs)
        for impl in nonwrappers:
            current[param] = value
            outcome = impl.call(current)
            if outcome is not None:  # None means "pass the value through unchanged"
                value = outcome
        return value

    def _collect(self, kwargs: dict[str, Any]) -> list[Any]:
        """Return the non-None results of the non-wrapper impls as a list."""
        return list(self._collect_iter(kwargs, self._nonwrappers))

    def _collect_iter(self, kwargs: dict[str, Any], nonwrappers: list[HookImpl]) -> Iterator[Any]:
        """Yield non-None results from the given non-wrapper impls, honouring firstresult."""
        for impl in nonwrappers:
            outcome = impl.call(kwargs)
            if outcome is None:
                continue
            yield outcome
            if self.spec.firstresult:
                return

    def _teardown(
        self, started: list[Generator[Any, Any, Any]], *, result: Any = _UNSET, exc: BaseException | None = None
    ) -> Any:
        """Resume each wrapper in reverse, letting it replace the result or handle the error."""
        for generator in reversed(started):
            try:
                if exc is not None:
                    generator.throw(exc)
                else:
                    generator.send(result)
            except StopIteration as stop:
                # A wrapper that returns after the yield ends here.
                if exc is not None:
                    # The wrapper swallowed the exception and supplied a result.
                    exc = None
                    result = stop.value
                elif stop.value is not None:
                    result = stop.value
            except BaseException as new_exc:  # noqa: BLE001 - propagate the wrapper's error onward
                exc = new_exc
            else:
                # The generator yielded a second time, violating the one-yield contract.
                # Capture the error but keep unwinding so the remaining wrappers still
                # tear down; the error propagates through them and is raised at the end.
                generator.close()
                exc = RuntimeError(f"wrapper for {self.name!r} must yield exactly once")
        if exc is not None:
            raise exc
        return result

    def implementations(self) -> list[HookImpl]:
        """Return this hook's implementations in call order (wrappers excluded)."""
        return list(self._nonwrappers)

    def __repr__(self) -> str:
        """Show the hook name and how many implementations it has."""
        return f"<HookCaller {self.name!r} impls={len(self._impls)}>"


# Typed views returned by PluginManager.caller(). The runtime object is always a
# plain HookCaller; these subclasses are never instantiated - they exist only to
# refine the static return type of a call per dispatch mode, deriving the impl
# ParamSpec P and return R from the branded spec.
class CollectingCaller[**P, R](HookCaller):
    """A collecting hook's typed caller: a call returns `list[R]`."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> list[R]:
        """Call the collecting hook, returning each impl's result as `list[R]`."""
        raise NotImplementedError  # pragma: no cover - the runtime object is a HookCaller


class FirstResultCaller[**P, R](HookCaller):
    """A firstresult hook's typed caller: a call returns `R | None`."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R | None:
        """Call the firstresult hook, returning the first non-None `R` or `None`."""
        raise NotImplementedError  # pragma: no cover - the runtime object is a HookCaller


class PipelineCaller[**P, R](HookCaller):
    """A pipeline hook's typed caller: a call returns `R`."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Call the pipeline hook, returning the threaded value `R`."""
        raise NotImplementedError  # pragma: no cover - the runtime object is a HookCaller


class HistoricCaller[**P, R](HookCaller):
    """A historic hook's typed caller. Replay it with `call_historic({...})`.

    Calling it directly raises - historic hooks have no plain call form - so the
    typed `__call__` is `NoReturn` rather than a value it never produces.
    """

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> NoReturn:
        """Historic hooks cannot be called directly; use `call_historic`."""
        raise NotImplementedError  # pragma: no cover - the runtime object is a HookCaller


class HookRelay:
    """Attribute-style access to hook callers, e.g. pm.hook.add_ingredients(...)."""

    def __init__(self) -> None:
        """Start with no registered callers."""
        self._callers: dict[str, HookCaller] = {}

    def _add_caller(self, caller: HookCaller) -> None:
        """Register a caller under its hook name."""
        self._callers[caller.name] = caller

    def _get_caller(self, name: str) -> HookCaller | None:
        """Return the caller for a hook name, or None if undefined."""
        return self._callers.get(name)

    def _all_callers(self) -> list[HookCaller]:
        """Return every registered caller."""
        return list(self._callers.values())

    def __getattr__(self, name: str) -> HookCaller:
        """Resolve pm.hook.<name> to its HookCaller, or raise AttributeError."""
        try:
            return self._callers[name]
        except KeyError:
            raise AttributeError(f"no hook named {name!r}") from None


class PluginManager:
    """Registers plugins and exposes their hooks via a HookRelay."""

    def __init__(self, project_name: str) -> None:
        """Bind the manager to a project name shared with the markers."""
        self.project_name = project_name
        self.hook = HookRelay()
        self._spec_attribute = f"{project_name}_extension_point"
        self._impl_attribute = f"{project_name}_extension"
        self._name2plugin: dict[str, object] = {}
        self._blocked: set[str] = set()
        self._lock = threading.RLock()

    def add_extension_points(self, namespace: object) -> None:
        """Scan a module (or object) for extension points and create callers."""
        with self._lock:
            for member_name in dir(namespace):
                member = getattr(namespace, member_name)
                spec = getattr(member, self._spec_attribute, None)
                if not isinstance(spec, ExtensionPointOpts):
                    continue
                signature = inspect.signature(member)
                arity = _positional_arity(signature, "extension point", member_name)
                params = tuple(signature.parameters)
                defaults = {
                    name: parameter.default
                    for name, parameter in signature.parameters.items()
                    if parameter.default is not inspect.Parameter.empty
                }
                if self.hook._get_caller(member_name) is not None:
                    raise ValueError(
                        f"extension point {member_name!r} is already registered; "
                        f"re-adding it would drop the implementations already wired to it"
                    )
                self._validate_spec(member_name, spec, params)
                self.hook._add_caller(self._make_caller(member_name, spec, params, defaults, arity))

    def _make_caller(
        self, name: str, spec: ExtensionPointOpts, params: tuple[str, ...], defaults: dict[str, Any], arity: int
    ) -> HookCaller:
        """Build the caller for a spec; overridden by AsyncPluginManager."""
        return HookCaller(name=name, spec=spec, params=params, defaults=defaults, positional_arity=arity)

    @overload
    def caller[**P, R](self, spec: FirstResultSpec[P, R]) -> FirstResultCaller[P, R]: ...
    @overload
    def caller[**P, R](self, spec: PipelineSpec[P, R]) -> PipelineCaller[P, R]: ...
    @overload
    def caller[**P, R](self, spec: HistoricSpec[P, R]) -> HistoricCaller[P, R]: ...
    @overload
    def caller[**P, R](self, spec: CollectingSpec[P, R]) -> CollectingCaller[P, R]: ...
    def caller(self, spec: object) -> HookCaller:
        """Return the typed caller for an `@extension_point`-decorated function.

        The result is a plain `HookCaller`, but its static type carries the extension
        point's dispatch mode, so a call returns `list[R]` (collecting), `R | None`
        (firstresult), or `R` (pipeline) - derived from the declaration, not asserted.
        """
        return self._caller(spec)

    def _caller(self, spec: object) -> HookCaller:
        """Resolve an extension point to its registered caller (shared by subclasses)."""
        name = getattr(spec, "__name__", None)
        if not isinstance(name, str):
            raise TypeError("caller() expects an @extension_point-decorated function")
        found = self.hook._get_caller(name)
        if found is None:
            raise PluginValidationError(
                self.project_name, f"unknown extension point {name!r}; call add_extension_points() first"
            )
        return found

    @staticmethod
    def _validate_spec(name: str, spec: ExtensionPointOpts, params: tuple[str, ...]) -> None:
        """Reject contradictory or impossible spec option combinations."""
        modes = [
            mode
            for mode, on in (
                ("firstresult", spec.firstresult),
                ("historic", spec.historic),
                ("pipeline", spec.pipeline),
            )
            if on
        ]
        if len(modes) > 1:
            raise ValueError(f"hook {name!r} cannot combine {' and '.join(modes)}")
        if spec.pipeline and not params:
            raise ValueError(f"pipeline hook {name!r} must declare at least one argument to thread through")

    def register(self, plugin: object, name: str | None = None) -> str:
        """Register a plugin object, wiring up every hook implementation it carries."""
        with self._lock:
            plugin_name = name or self.get_canonical_name(plugin)
            if plugin_name in self._blocked:
                raise ValueError(f"plugin {plugin_name!r} is blocked")
            if plugin_name in self._name2plugin:
                raise ValueError(f"plugin name {plugin_name!r} is already registered")
            if any(existing is plugin for existing in self._name2plugin.values()):
                raise ValueError(f"plugin object {plugin!r} is already registered")

            impls = self._collect_impls(plugin_name, plugin)
            self._name2plugin[plugin_name] = plugin
            try:
                for caller, impl in impls:
                    caller.add_impl(impl)
            except BaseException:
                # add_impl can fail mid-loop (e.g. a historic replay raising). Roll the
                # partial wiring back so registration is all-or-nothing.
                self._name2plugin.pop(plugin_name, None)
                for caller in self.hook._all_callers():
                    caller.remove_plugin(plugin_name)
                raise
            return plugin_name

    def unregister(self, name_or_plugin: str | object) -> object | None:
        """Remove a plugin by name or by object; return the removed plugin or None."""
        with self._lock:
            name = name_or_plugin if isinstance(name_or_plugin, str) else self.get_name(name_or_plugin)
            if name is None:
                return None
            plugin = self._name2plugin.pop(name, None)
            if plugin is None:
                return None
            for caller in self.hook._all_callers():
                caller.remove_plugin(name)
            return plugin

    def set_blocked(self, name: str) -> None:
        """Block a plugin name: unregister it if present and refuse future registration."""
        with self._lock:
            self._blocked.add(name)
            self.unregister(name)

    def is_blocked(self, name: str) -> bool:
        """Return whether a plugin name is blocked."""
        return name in self._blocked

    def is_registered(self, plugin: object) -> bool:
        """Return whether a plugin object is currently registered."""
        return any(existing is plugin for existing in self._name2plugin.values())

    def get_plugin(self, name: str) -> object | None:
        """Return the plugin registered under a name, or None."""
        return self._name2plugin.get(name)

    def get_name(self, plugin: object) -> str | None:
        """Return the registered name of a plugin object, or None."""
        for registered_name, registered_plugin in self._name2plugin.items():
            if registered_plugin is plugin:
                return registered_name
        return None

    def get_canonical_name(self, plugin: object) -> str:
        """Derive a default name for a plugin from its __name__ or type."""
        return getattr(plugin, "__name__", None) or type(plugin).__name__

    def plugin_names(self) -> list[str]:
        """Return the names of all registered plugins, in registration order."""
        return list(self._name2plugin)

    def get_hookcallers(self, plugin: object) -> list[HookCaller] | None:
        """Return the hooks a registered plugin contributes to, or None if unknown."""
        name = self.get_name(plugin)
        if name is None:
            return None
        return [caller for caller in self.hook._all_callers() if caller.has_plugin(name)]

    def __repr__(self) -> str:
        """Show the project name and number of registered plugins."""
        return f"<PluginManager {self.project_name!r} plugins={len(self._name2plugin)}>"

    def load_entrypoints(self, group: str, *, ignore_errors: bool = False) -> int:
        """Discover and register external plugins advertised under an entry-point group.

        Args:
            group: The entry-point group name to scan.
            ignore_errors: When True, skip plugins that fail to load or register
                instead of raising, so one broken plugin cannot block discovery.

        Returns:
            The number of plugins successfully registered.

        Note:
            With ``ignore_errors=False``, a failure part-way through leaves the
            plugins registered before it registered; this method does not roll back
            across plugins.
        """
        count = 0
        for entry_point in entry_points(group=group):
            if entry_point.name in self._name2plugin or entry_point.name in self._blocked:
                continue
            try:
                plugin = entry_point.load()
                self.register(plugin, name=entry_point.name)
            except Exception as error:
                if ignore_errors:
                    continue
                raise PluginValidationError(entry_point.name, f"failed to load entry point: {error}") from error
            count += 1
        return count

    def _collect_impls(self, plugin_name: str, plugin: object) -> list[tuple[HookCaller, HookImpl]]:
        """Find and validate every hook implementation a plugin carries."""
        collected: list[tuple[HookCaller, HookImpl]] = []
        for member_name in dir(plugin):
            member = getattr(plugin, member_name)
            opts = getattr(member, self._impl_attribute, None)
            if not isinstance(opts, ExtensionOpts):
                continue
            hook_name = opts.target or member_name
            caller = self.hook._get_caller(hook_name)
            if caller is None:
                if opts.optional:
                    continue
                raise PluginValidationError(plugin_name, f"implements unknown extension point {hook_name!r}")
            if opts.wrapper and caller.spec.historic:
                raise PluginValidationError(plugin_name, f"historic hook {hook_name!r} cannot have a wrapper")
            impl = HookImpl.from_function(plugin_name, member, opts)
            unknown = impl.accepts - caller.argnames
            if unknown:
                raise PluginValidationError(
                    plugin_name,
                    f"hook {hook_name!r} impl declares unknown argument(s) {sorted(unknown)}; "
                    f"spec accepts {sorted(caller.argnames)}",
                )
            collected.append((caller, impl))
        return collected
