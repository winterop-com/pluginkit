"""Hook specifications for the host, plus a Protocol documenting the contract.

The @hookspec functions are what the manager discovers. The Protocol classes are
a modern-Python touch: they let a type checker verify, structurally, that a
plugin's method signatures line up with the hooks they implement -- no base class
or inheritance required.
"""

from typing import Protocol, runtime_checkable

from pluginkit_tour.markers import hookspec

# Hook specs are intentionally empty (signature + docstring only); the manager
# never runs their bodies, so the "must return a value" check does not apply.
# pyright: reportReturnType=false


@hookspec
def add_ingredients(base: list[str]) -> list[str]:
    """Offer ingredients to add; results are collected into a list."""


@hookspec(firstresult=True)
def choose_cup(size: str) -> str | None:
    """Pick a cup for the size; the first plugin to answer (non-None) wins."""


@hookspec
def prep_step(steps: list[str]) -> None:
    """Append a preparation step in place; cross-plugin ordering is the point."""


@hookspec(firstresult=True)
def blend(contents: list[str]) -> str | None:
    """Blend the contents into one drink; wrappers decorate that single result."""


@hookspec(historic=True)
def kitchen_opened(name: str) -> None:
    """Announce the kitchen opened; late-registered plugins still hear it."""


@runtime_checkable
class IngredientProvider(Protocol):
    """Structural type of any plugin that contributes ingredients."""

    def add_ingredients(self, base: list[str]) -> list[str]:
        """Return ingredients to add to the smoothie."""
        ...
