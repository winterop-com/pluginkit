"""Decorator markers that tag functions as hook specs or hook implementations.

Mirrors pluggy's HookspecMarker / HookimplMarker. A marker stamps a small frozen
dataclass of options onto the decorated function under a project-namespaced
attribute, so the manager can later recognise specs and impls by introspection.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar, overload

F = TypeVar("F", bound=Callable[..., Any])


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


class HookspecMarker:
    """Creates the @hookspec decorator bound to a project name."""

    def __init__(self, project_name: str) -> None:
        """Bind the marker to a project name used for the stamped attribute."""
        self.project_name = project_name
        self.attribute = f"{project_name}_spec"

    @overload
    def __call__(self, function: F) -> F: ...

    @overload
    def __call__(
        self, function: None = ..., *, firstresult: bool = ..., historic: bool = ..., pipeline: bool = ...
    ) -> Callable[[F], F]: ...

    def __call__(
        self,
        function: F | None = None,
        *,
        firstresult: bool = False,
        historic: bool = False,
        pipeline: bool = False,
    ) -> F | Callable[[F], F]:
        """Stamp HookspecOpts onto the function; supports bare and called forms."""

        def mark(func: F) -> F:
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
    def __call__(self, function: F) -> F: ...

    @overload
    def __call__(
        self,
        function: None = ...,
        *,
        tryfirst: bool = ...,
        trylast: bool = ...,
        wrapper: bool = ...,
        optionalhook: bool = ...,
        specname: str | None = ...,
    ) -> Callable[[F], F]: ...

    def __call__(
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
