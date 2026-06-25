"""Demo 4: generator wrappers that decorate the result of other implementations.

A wrapper is a generator: code before `yield` runs first, the value sent back to
the `yield` is the inner result, and whatever the generator returns replaces it.
blend is firstresult, so the wrapper receives a single string to decorate.
"""

from collections.abc import Generator

from pluginkit import PluginManager
from pluginkit_tour import points
from pluginkit_tour.markers import PROJECT_NAME, extension


class BlenderPlugin:
    """The real worker: turns contents into a drink."""

    @extension
    def blend(self, contents: list[str]) -> str:
        """Blend the contents into a single drink description."""
        return " + ".join(contents) + " blend"


class FoamWrapper:
    """Wraps the blend result to add foam on top."""

    @extension(wrapper=True)
    def blend(self, contents: list[str]) -> Generator[None, str, str]:
        """Let the inner plugins blend, then decorate their result."""
        result = yield
        return f"{result} topped with foam"


class TraceWrapper:
    """Wraps the blend call to announce before and after."""

    @extension(wrapper=True)
    def blend(self, contents: list[str]) -> Generator[None, str, str]:
        """Print around the wrapped call, passing the result through unchanged."""
        print(f"  [trace] blending {len(contents)} item(s)...")
        result = yield
        print(f"  [trace] done: {result!r}")
        return result


def build_plugin_manager() -> PluginManager:
    """Register the worker plus two wrappers around it."""
    pm = PluginManager(PROJECT_NAME)
    pm.add_extension_points(points)
    pm.register(BlenderPlugin(), name="blender")
    pm.register(FoamWrapper(), name="foam")
    pm.register(TraceWrapper(), name="trace")
    return pm


def blend(contents: list[str]) -> str:
    """Run the wrapped blend hook and return the final decorated result."""
    pm = build_plugin_manager()
    final = pm.caller(points.blend)(contents=contents) or ""
    return final


def main() -> None:
    """Run the wrapper demo."""
    print("Result:", blend(["mango", "yogurt", "ice"]))
