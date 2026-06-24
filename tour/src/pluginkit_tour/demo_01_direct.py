"""Demo 1: register plugins directly, and type them against a Protocol.

The host hands plugin objects to the manager itself. The IngredientProvider
Protocol from hookspecs lets a checker confirm each plugin's add_ingredients
signature matches, structurally, without any shared base class.
"""

from pluginkit import PluginManager
from pluginkit_tour import hookspecs
from pluginkit_tour.hookspecs import IngredientProvider
from pluginkit_tour.markers import PROJECT_NAME, hookimpl


class BerryPlugin:
    """A plugin defined as a class instance."""

    @hookimpl
    def add_ingredients(self, base: list[str]) -> list[str]:
        """Contribute berries unless they are already in the base."""
        return ["blueberry", "strawberry"] if "berry" not in base else []


class GreensPlugin:
    """Another class-based plugin."""

    @hookimpl
    def add_ingredients(self, base: list[str]) -> list[str]:
        """Contribute leafy greens."""
        return ["spinach", "kale"]


def build_plugin_manager() -> PluginManager:
    """Create a manager and register two plugins directly."""
    pm = PluginManager(PROJECT_NAME)
    pm.add_hookspecs(hookspecs)
    # The annotation documents (and lets a checker verify) the structural contract.
    berry: IngredientProvider = BerryPlugin()
    greens: IngredientProvider = GreensPlugin()
    pm.register(berry, name="berry")
    pm.register(greens, name="greens")
    return pm


def make_smoothie() -> list[str]:
    """Collect ingredients from every registered plugin."""
    pm = build_plugin_manager()
    base = ["banana", "milk"]
    contributed = pm.hook.add_ingredients(base=base)
    return base + [item for plugin_result in contributed for item in plugin_result]


def main() -> None:
    """Run the direct-registration demo."""
    print("Registered plugins:", build_plugin_manager().plugin_names())
    print("Smoothie:", ", ".join(make_smoothie()))
