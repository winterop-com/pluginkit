"""Demo 2: firstresult specs -- the first plugin to answer (non-None) wins."""

from pluginkit import PluginManager
from pluginkit_tour import hookspecs
from pluginkit_tour.markers import PROJECT_NAME, hookimpl


class SmallCupPlugin:
    """Only serves small drinks."""

    @hookimpl
    def choose_cup(self, size: str) -> str | None:
        """Answer for the small size, otherwise abstain by returning None."""
        return "8oz paper cup" if size == "small" else None


class LargeCupPlugin:
    """Only serves large drinks."""

    @hookimpl
    def choose_cup(self, size: str) -> str | None:
        """Answer for the large size."""
        return "20oz tumbler" if size == "large" else None


class FallbackCupPlugin:
    """Catch-all, marked trylast so the specific plugins are asked first."""

    @hookimpl(trylast=True)
    def choose_cup(self, size: str) -> str | None:
        """Always provide a generic cup."""
        return "16oz default cup"


def build_plugin_manager() -> PluginManager:
    """Register the cup plugins; trylast puts the fallback at the end."""
    pm = PluginManager(PROJECT_NAME)
    pm.add_hookspecs(hookspecs)
    pm.register(FallbackCupPlugin(), name="fallback")
    pm.register(SmallCupPlugin(), name="small")
    pm.register(LargeCupPlugin(), name="large")
    return pm


def choose_cup(size: str) -> str:
    """Return the single cup chosen for the requested size."""
    pm = build_plugin_manager()
    cup = pm.caller(hookspecs.choose_cup)(size=size)
    assert cup is not None  # the default plugin always answers
    return cup


def main() -> None:
    """Run the firstresult demo across several sizes."""
    for size in ("small", "large", "medium"):
        print(f"{size:>6} -> {choose_cup(size)}")
