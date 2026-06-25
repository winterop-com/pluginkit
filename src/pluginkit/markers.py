"""Decorators that declare extension points and the extensions that fulfil them.

A marker stamps a small frozen dataclass of options onto the decorated function
under a project-namespaced attribute, so the manager can later recognise extension
points and extensions by introspection.

`@extension_point` is **typed by dispatch mode**: it returns a branded spec type
(`CollectingSpec` / `FirstResultSpec` / `PipelineSpec` / `HistoricSpec`) that carries
the call signature (`P`) and per-extension return type (`R`). `PluginManager.caller`
reads that brand to hand back a caller whose result type is exactly right for the
mode - `list[R]`, `R | None`, or `R`. The brand classes are type-level only; they are
never instantiated (an extension point is a declaration, not a callable you invoke
directly).
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, overload


@dataclass(frozen=True, slots=True)
class ExtensionPointOpts:
    """Options attached to an extension point."""

    firstresult: bool = False
    historic: bool = False
    pipeline: bool = False


@dataclass(frozen=True, slots=True)
class ExtensionOpts:
    """Options attached to an extension."""

    tryfirst: bool = False
    trylast: bool = False
    wrapper: bool = False
    optional: bool = False
    target: str | None = None


class CollectingSpec[**P, R]:
    """A collecting extension point: a call collects each extension's `R` into `list[R]`."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Declarations are called via PluginManager.caller(extension_point)."""
        raise NotImplementedError("an extension point is a declaration; call it via PluginManager.caller(...)")


class FirstResultSpec[**P, R]:
    """A firstresult extension point: a call returns the first non-None `R`, or `None`."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Declarations are called via PluginManager.caller(extension_point)."""
        raise NotImplementedError("an extension point is a declaration; call it via PluginManager.caller(...)")


class PipelineSpec[**P, R]:
    """A pipeline extension point: a call threads `R` through the extensions and returns it."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Declarations are called via PluginManager.caller(extension_point)."""
        raise NotImplementedError("an extension point is a declaration; call it via PluginManager.caller(...)")


class HistoricSpec[**P, R]:
    """A historic extension point: replayed to late plugins, driven via `call_historic`."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Declarations are called via PluginManager.caller(extension_point)."""
        raise NotImplementedError("an extension point is a declaration; call it via PluginManager.caller(...)")


class ExtensionPoint:
    """Creates the @extension_point decorator bound to a project name."""

    def __init__(self, project_name: str) -> None:
        """Bind the marker to a project name used for the stamped attribute."""
        self.project_name = project_name
        self.attribute = f"{project_name}_extension_point"

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
        self, function: None = ..., *, historic: Literal[True]
    ) -> Callable[[Callable[P, R]], HistoricSpec[P, R]]: ...
    @overload
    def __call__[**P, R](
        self, function: None = ..., *, historic: Literal[False] = ...
    ) -> Callable[[Callable[P, R]], CollectingSpec[P, R]]: ...
    def __call__(
        self,
        function: Callable[..., Any] | None = None,
        *,
        firstresult: bool = False,
        historic: bool = False,
        pipeline: bool = False,
    ) -> Any:
        """Stamp ExtensionPointOpts onto the function; supports bare and called forms."""

        def mark(func: Callable[..., Any]) -> Callable[..., Any]:
            setattr(
                func, self.attribute, ExtensionPointOpts(firstresult=firstresult, historic=historic, pipeline=pipeline)
            )
            return func

        return mark(function) if function is not None else mark


class Extension:
    """Creates the @extension decorator bound to a project name."""

    def __init__(self, project_name: str) -> None:
        """Bind the marker to a project name used for the stamped attribute."""
        self.project_name = project_name
        self.attribute = f"{project_name}_extension"

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
        optional: bool = ...,
        target: str | None = ...,
    ) -> Callable[[F], F]: ...
    def __call__[F: Callable[..., Any]](
        self,
        function: F | None = None,
        *,
        tryfirst: bool = False,
        trylast: bool = False,
        wrapper: bool = False,
        optional: bool = False,
        target: str | None = None,
    ) -> F | Callable[[F], F]:
        """Stamp ExtensionOpts onto the function; supports bare and called forms."""

        def mark(func: F) -> F:
            setattr(
                func,
                self.attribute,
                ExtensionOpts(
                    tryfirst=tryfirst,
                    trylast=trylast,
                    wrapper=wrapper,
                    optional=optional,
                    target=target,
                ),
            )
            return func

        return mark(function) if function is not None else mark
