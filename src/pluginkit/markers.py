"""Decorator markers that tag functions as hook specs or hook implementations.

A marker stamps a small frozen dataclass of options onto the decorated function
under a project-namespaced attribute, so the manager can later recognise specs and
impls by introspection.

The `@hookspec` decorator is **typed by dispatch mode**: it returns a branded spec
type (`CollectingSpec` / `FirstResultSpec` / `PipelineSpec`) that carries the impl
signature (`P`) and per-impl return type (`R`). `PluginManager.caller(spec)` reads
that brand to hand back a caller whose result type is exactly right for the mode -
`list[R]`, `R | None`, or `R`. The brand classes are type-level only; they are never
instantiated (a spec is a declaration, not a callable you invoke directly).
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, overload


@dataclass(frozen=True, slots=True)
class HookspecOpts:
    """Options attached to a hook specification."""

    firstresult: bool = False
    historic: bool = False
    pipeline: bool = False


@dataclass(frozen=True, slots=True)
class HookimplOpts:
    """Options attached to a hook implementation."""

    tryfirst: bool = False
    trylast: bool = False
    wrapper: bool = False
    optionalhook: bool = False
    specname: str | None = None


class CollectingSpec[**P, R]:
    """A collecting hook spec: a call collects each impl's `R` into `list[R]`."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Specs are declarations; obtain a callable via PluginManager.caller(spec)."""
        raise NotImplementedError("a spec is a declaration; call it via PluginManager.caller(spec)")


class FirstResultSpec[**P, R]:
    """A firstresult hook spec: a call returns the first non-None `R`, or `None`."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Specs are declarations; obtain a callable via PluginManager.caller(spec)."""
        raise NotImplementedError("a spec is a declaration; call it via PluginManager.caller(spec)")


class PipelineSpec[**P, R]:
    """A pipeline hook spec: a call threads `R` through the impls and returns it."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Specs are declarations; obtain a callable via PluginManager.caller(spec)."""
        raise NotImplementedError("a spec is a declaration; call it via PluginManager.caller(spec)")


class HookspecMarker:
    """Creates the @hookspec decorator bound to a project name."""

    def __init__(self, project_name: str) -> None:
        """Bind the marker to a project name used for the stamped attribute."""
        self.project_name = project_name
        self.attribute = f"{project_name}_spec"

    @overload
    def __call__[**P, R](self, function: Callable[P, R]) -> CollectingSpec[P, R]: ...
    @overload
    def __call__[**P, R](
        self, function: None = ..., *, firstresult: Literal[True], historic: bool = ...
    ) -> Callable[[Callable[P, R]], FirstResultSpec[P, R]]: ...
    @overload
    def __call__[**P, R](
        self, function: None = ..., *, pipeline: Literal[True], historic: bool = ...
    ) -> Callable[[Callable[P, R]], PipelineSpec[P, R]]: ...
    @overload
    def __call__[**P, R](
        self, function: None = ..., *, historic: bool = ...
    ) -> Callable[[Callable[P, R]], CollectingSpec[P, R]]: ...
    def __call__(
        self,
        function: Callable[..., Any] | None = None,
        *,
        firstresult: bool = False,
        historic: bool = False,
        pipeline: bool = False,
    ) -> Any:
        """Stamp HookspecOpts onto the function; supports bare and called forms."""

        def mark(func: Callable[..., Any]) -> Callable[..., Any]:
            setattr(func, self.attribute, HookspecOpts(firstresult=firstresult, historic=historic, pipeline=pipeline))
            return func

        return mark(function) if function is not None else mark


class HookimplMarker:
    """Creates the @hookimpl decorator bound to a project name."""

    def __init__(self, project_name: str) -> None:
        """Bind the marker to a project name used for the stamped attribute."""
        self.project_name = project_name
        self.attribute = f"{project_name}_impl"

    @overload
    def __call__[F: Callable[..., Any]](self, function: F) -> F: ...
    @overload
    def __call__[F: Callable[..., Any]](
        self,
        function: None = ...,
        *,
        tryfirst: bool = ...,
        trylast: bool = ...,
        wrapper: bool = ...,
        optionalhook: bool = ...,
        specname: str | None = ...,
    ) -> Callable[[F], F]: ...
    def __call__[F: Callable[..., Any]](
        self,
        function: F | None = None,
        *,
        tryfirst: bool = False,
        trylast: bool = False,
        wrapper: bool = False,
        optionalhook: bool = False,
        specname: str | None = None,
    ) -> F | Callable[[F], F]:
        """Stamp HookimplOpts onto the function; supports bare and called forms."""

        def mark(func: F) -> F:
            setattr(
                func,
                self.attribute,
                HookimplOpts(
                    tryfirst=tryfirst,
                    trylast=trylast,
                    wrapper=wrapper,
                    optionalhook=optionalhook,
                    specname=specname,
                ),
            )
            return func

        return mark(function) if function is not None else mark
