"""External plugin distribution for the from-scratch kitchen host."""

from pluginkit import Extension

# Bind the marker to the host's project name. An external distribution only needs
# pluginkit and the agreed project name, never the host package itself.
extension = Extension("kitchen")


@extension
def add_ingredients(base: list[str]) -> list[str]:
    """Contribute extras from a separately installed package."""
    return ["chia seeds", "almond butter"]
