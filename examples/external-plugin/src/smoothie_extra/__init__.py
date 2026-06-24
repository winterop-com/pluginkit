"""External plugin distribution for the from-scratch kitchen host."""

from pluginkit_tour.markers import hookimpl


@hookimpl
def add_ingredients(base: list[str]) -> list[str]:
    """Contribute extras from a separately installed package."""
    return ["chia seeds", "almond butter"]
