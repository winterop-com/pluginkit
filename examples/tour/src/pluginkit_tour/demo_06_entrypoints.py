"""Demo 6: discover external plugins via entry points, using the stdlib only.

PluginManager.load_entrypoints("kitchen") reads importlib.metadata entry points,
so any installed distribution that advertises itself under the "kitchen" group is
registered without the host importing it. Here honey ships inside this package
and smoothie-extra is a separate uv project under plugins/.
"""

from pluginkit import PluginManager
from pluginkit_tour import hookspecs
from pluginkit_tour.markers import PROJECT_NAME


def build_plugin_manager() -> PluginManager:
    """Create a manager and load every plugin advertised under the project name."""
    pm = PluginManager(PROJECT_NAME)
    pm.add_hookspecs(hookspecs)
    loaded = pm.load_entrypoints(PROJECT_NAME)
    print(f"Discovered {loaded} plugin(s) via entry points")
    return pm


def make_smoothie(pm: PluginManager | None = None) -> list[str]:
    """Collect ingredients contributed by entry-point plugins."""
    pm = pm or build_plugin_manager()
    base = ["water", "ice"]
    contributed = pm.caller(hookspecs.add_ingredients)(base=base)
    return base + [item for plugin_result in contributed for item in plugin_result]


def main() -> None:
    """Run the entry-point discovery demo."""
    pm = build_plugin_manager()
    print("Registered plugins:", pm.plugin_names())
    print("Smoothie:", ", ".join(make_smoothie(pm)))
