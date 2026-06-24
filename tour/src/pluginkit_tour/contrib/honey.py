"""An entry-point plugin in the host's own distribution; the host never imports it.

Wired to the "kitchen" group in pyproject.toml and discovered at runtime via
PluginManager.load_entrypoints("kitchen"), which uses the stdlib only.
"""

from pluginkit_tour.markers import hookimpl


@hookimpl
def add_ingredients(base: list[str]) -> list[str]:
    """Contribute a sweetener; a module-level function works as a plugin too."""
    return ["honey", "oats"]
