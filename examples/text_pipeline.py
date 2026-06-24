"""A text-transformation pipeline using pluginkit's pipeline dispatch.

A `pipeline` hook threads its first argument through every implementation: each
one receives the running value and returns the next. Returning None passes the
value through unchanged. Ordering (`tryfirst` / `trylast`) controls the stages.

This is a middleware/fold chain - something neither a collecting nor a
firstresult hook expresses.

Run: python examples/text_pipeline.py
"""
# mypy: disable-error-code="empty-body"
# pyright: reportReturnType=false

from pluginkit import HookimplMarker, HookspecMarker, PluginManager

hookspec = HookspecMarker("textkit")
hookimpl = HookimplMarker("textkit")


class Specs:
    """The text host's contract."""

    @staticmethod
    @hookspec(pipeline=True)
    def transform(text: str) -> str:
        """Transform the running text and return the next value."""


class StripStage:
    """Trims surrounding whitespace; runs first."""

    @hookimpl(tryfirst=True)
    def transform(self, text: str) -> str:
        """Strip the text."""
        return text.strip()


class CollapseSpacesStage:
    """Collapses runs of internal whitespace."""

    @hookimpl
    def transform(self, text: str) -> str:
        """Collapse whitespace to single spaces."""
        return " ".join(text.split())


class TitleCaseStage:
    """Title-cases the text."""

    @hookimpl
    def transform(self, text: str) -> str:
        """Title-case the text."""
        return text.title()


class ExclaimStage:
    """Adds emphasis; runs last."""

    @hookimpl(trylast=True)
    def transform(self, text: str) -> str:
        """Append an exclamation mark unless one is already there."""
        return text if text.endswith("!") else f"{text}!"


def build_plugin_manager() -> PluginManager:
    """Create a manager with the pipeline stages registered out of order."""
    pm = PluginManager("textkit")
    pm.add_hookspecs(Specs)
    pm.register(ExclaimStage(), name="exclaim")
    pm.register(TitleCaseStage(), name="title")
    pm.register(StripStage(), name="strip")
    pm.register(CollapseSpacesStage(), name="collapse")
    return pm


def run(text: str) -> str:
    """Push text through the full transformation pipeline."""
    pm = build_plugin_manager()
    result: str = pm.hook.transform(text=text)
    return result


def main() -> None:
    """Transform a messy string through the pipeline."""
    messy = "   hello    wonderful   world   "
    print(f"in:  {messy!r}")
    print(f"out: {run(messy)!r}")


if __name__ == "__main__":
    main()
