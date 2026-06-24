"""Demo 3: control call order with tryfirst / trylast regardless of registration."""

from pluginkit import PluginManager
from pluginkit_tour import hookspecs
from pluginkit_tour.markers import PROJECT_NAME, hookimpl


class WashPlugin:
    """Washing must happen before anything else."""

    @hookimpl(tryfirst=True)
    def prep_step(self, steps: list[str]) -> None:
        """Record the wash step first."""
        steps.append("wash produce")


class ChopPlugin:
    """Ordinary middle step with no ordering preference."""

    @hookimpl
    def prep_step(self, steps: list[str]) -> None:
        """Record the chop step."""
        steps.append("chop fruit")


class GarnishPlugin:
    """Garnishing must happen last."""

    @hookimpl(trylast=True)
    def prep_step(self, steps: list[str]) -> None:
        """Record the garnish step last."""
        steps.append("add garnish")

    @hookimpl(optionalhook=True)
    def not_a_real_hook(self) -> None:
        """Implements a hook the host never specified; optionalhook avoids an error."""


def build_plugin_manager() -> PluginManager:
    """Register plugins out of order to prove the markers decide the outcome."""
    pm = PluginManager(PROJECT_NAME)
    pm.add_hookspecs(hookspecs)
    pm.register(GarnishPlugin(), name="garnish")
    pm.register(WashPlugin(), name="wash")
    pm.register(ChopPlugin(), name="chop")
    return pm


def prep_steps() -> list[str]:
    """Run every plugin's prep step and return the ordered list."""
    pm = build_plugin_manager()
    steps: list[str] = []
    pm.hook.prep_step(steps=steps)
    return steps


def main() -> None:
    """Run the ordering demo."""
    for index, step in enumerate(prep_steps(), start=1):
        print(f"{index}. {step}")
