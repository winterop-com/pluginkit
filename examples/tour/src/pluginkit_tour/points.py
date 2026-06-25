"""Hook specifications for the host, plus a Protocol documenting the contract.

The @extension_point functions are what the manager discovers. The Protocol classes are
a modern-Python touch: they let a type checker verify, structurally, that a
plugin's method signatures line up with the hooks they implement -- no base class
or inheritance required.
"""

from typing import Protocol, runtime_checkable

from pluginkit_tour.markers import extension_point

# Hook specs are intentionally empty (signature + docstring only); the manager
# never runs their bodies, so the "must return a value" check does not apply.
# pyright: reportReturnType=false


@extension_point
def add_ingredients(base: list[str]) -> list[str]:
    """Offer ingredients to add; results are collected into a list."""


@extension_point(firstresult=True)
def choose_cup(size: str) -> str | None:
    """Pick a cup for the size; the first plugin to answer (non-None) wins."""


@extension_point
def prep_step(steps: list[str]) -> None:
    """Append a preparation step in place; cross-plugin ordering is the point."""


@extension_point(firstresult=True)
def blend(contents: list[str]) -> str | None:
    """Blend the contents into one drink; wrappers decorate that single result."""


@extension_point(historic=True)
def kitchen_opened(name: str) -> None:
    """Announce the kitchen opened; late-registered plugins still hear it."""


@runtime_checkable
class IngredientProvider(Protocol):
    """Structural type of any plugin that contributes ingredients."""

    def add_ingredients(self, base: list[str]) -> list[str]:
        """Return ingredients to add to the smoothie."""
        ...
