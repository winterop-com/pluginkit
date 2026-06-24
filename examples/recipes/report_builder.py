"""A report builder where plugins contribute sections and a wrapper frames output.

Shows three mechanisms together:

- collecting hook (`section`) gathers a block of text from every plugin;
- ordering (`tryfirst` / `trylast`) puts the title first and the footer last;
- a wrapper (`render`) frames the assembled body with a banner.

Run: python examples/report_builder.py
"""
# mypy: disable-error-code="empty-body"
# pyright: reportReturnType=false

from collections.abc import Generator

from pluginkit import HookimplMarker, HookspecMarker, PluginManager

hookspec = HookspecMarker("report")
hookimpl = HookimplMarker("report")


class Specs:
    """The report host's contract."""

    @staticmethod
    @hookspec
    def section(data: dict[str, int]) -> str:
        """Return one section of the report for the given data."""

    @staticmethod
    @hookspec(firstresult=True)
    def render(body: str) -> str:
        """Render the assembled body into the final document."""


class TitlePlugin:
    """Emits the report title; must come first."""

    @hookimpl(tryfirst=True)
    def section(self, data: dict[str, int]) -> str:
        """Return the title line."""
        return "# Daily Sales Report"


class BodyPlugin:
    """Emits the data rows."""

    @hookimpl
    def section(self, data: dict[str, int]) -> str:
        """Return one line per data entry."""
        return "\n".join(f"- {label}: {value}" for label, value in data.items())


class TotalPlugin:
    """Emits the total; must come last."""

    @hookimpl(trylast=True)
    def section(self, data: dict[str, int]) -> str:
        """Return the total line."""
        return f"**Total: {sum(data.values())}**"


class RenderPlugin:
    """Joins sections into the document body."""

    @hookimpl
    def render(self, body: str) -> str:
        """Return the body unchanged (the wrapper frames it)."""
        return body


class BannerWrapper:
    """Frames the rendered document with a banner."""

    @hookimpl(wrapper=True)
    def render(self, body: str) -> Generator[None, str, str]:
        """Wrap the rendered body between two rules."""
        rendered = yield
        rule = "=" * 32
        return f"{rule}\n{rendered}\n{rule}"


def build_plugin_manager() -> PluginManager:
    """Create a manager with the report plugins registered."""
    pm = PluginManager("report")
    pm.add_hookspecs(Specs)
    # Registered out of order on purpose; tryfirst/trylast decide section order.
    pm.register(TotalPlugin(), name="total")
    pm.register(BodyPlugin(), name="body")
    pm.register(TitlePlugin(), name="title")
    pm.register(RenderPlugin(), name="render")
    pm.register(BannerWrapper(), name="banner")
    return pm


def run(data: dict[str, int]) -> str:
    """Assemble the sections and render the final report."""
    pm = build_plugin_manager()
    body = "\n\n".join(pm.hook.section(data=data))
    document: str = pm.hook.render(body=body)
    return document


def main() -> None:
    """Print a sample report."""
    print(run({"apples": 12, "pears": 7, "plums": 3}))


if __name__ == "__main__":
    main()
