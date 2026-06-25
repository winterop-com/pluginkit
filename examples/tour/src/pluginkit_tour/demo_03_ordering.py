"""Demo 3: control call order with tryfirst / trylast regardless of registration."""

from pluginkit import PluginManager
from pluginkit_tour import points
from pluginkit_tour.markers import PROJECT_NAME, extension


class WashPlugin:
    """Washing must happen before anything else."""

    @extension(tryfirst=True)
    def prep_step(self, steps: list[str]) -> None:
        """Record the wash step first."""
        steps.append("wash produce")


class ChopPlugin:
    """Ordinary middle step with no ordering preference."""

    @extension
    def prep_step(self, steps: list[str]) -> None:
        """Record the chop step."""
        steps.append("chop fruit")


class GarnishPlugin:
    """Garnishing must happen last."""

    @extension(trylast=True)
    def prep_step(self, steps: list[str]) -> None:
        """Record the garnish step last."""
        steps.append("add garnish")

    @extension(optional=True)
    def not_a_real_hook(self) -> None:
        """Implements a hook the host never specified; optional avoids an error."""


def build_plugin_manager() -> PluginManager:
    """Register plugins out of order to prove the markers decide the outcome."""
    pm = PluginManager(PROJECT_NAME)
    pm.add_extension_points(points)
    pm.register(GarnishPlugin(), name="garnish")
    pm.register(WashPlugin(), name="wash")
    pm.register(ChopPlugin(), name="chop")
    return pm


def prep_steps() -> list[str]:
    """Run every plugin's prep step and return the ordered list."""
    pm = build_plugin_manager()
    steps: list[str] = []
    pm.caller(points.prep_step)(steps=steps)
    return steps


def main() -> None:
    """Run the ordering demo."""
    for index, step in enumerate(prep_steps(), start=1):
        print(f"{index}. {step}")
