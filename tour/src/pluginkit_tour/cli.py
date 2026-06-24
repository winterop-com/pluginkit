"""Typer CLI to run each from-scratch plugin demo from the command line."""

from collections.abc import Callable

import typer

from pluginkit_tour import (
    demo_01_direct,
    demo_02_firstresult,
    demo_03_ordering,
    demo_04_wrapper,
    demo_05_historic,
    demo_06_entrypoints,
)

DEMOS: dict[str, tuple[str, Callable[[], None]]] = {
    "direct": ("Register plugins directly; type them against a Protocol", demo_01_direct.main),
    "firstresult": ("firstresult specs: the first plugin to answer wins", demo_02_firstresult.main),
    "ordering": ("tryfirst / trylast ordering", demo_03_ordering.main),
    "wrapper": ("Generator wrappers that decorate other implementations", demo_04_wrapper.main),
    "historic": ("Historic hooks replayed to late-registered plugins", demo_05_historic.main),
    "entrypoints": ("Discover plugins via stdlib entry points", demo_06_entrypoints.main),
}

app = typer.Typer(help="Demos of a from-scratch plugin framework.", no_args_is_help=True)


@app.command("list")
def list_demos() -> None:
    """List the available demos."""
    for name, (summary, _) in DEMOS.items():
        typer.echo(f"{name:<12} {summary}")


@app.command()
def run(name: str = typer.Argument(..., help="Demo name, or 'all' to run every demo.")) -> None:
    """Run a single demo by name, or 'all' to run them in order."""
    targets = DEMOS if name == "all" else {name: DEMOS.get(name)} if name in DEMOS else {}
    if not targets:
        typer.echo(f"Unknown demo: {name!r}. Try 'list'.", err=True)
        raise typer.Exit(code=1)
    for demo_name, entry in targets.items():
        assert entry is not None
        summary, func = entry
        typer.echo(f"\n=== {demo_name}: {summary} ===")
        func()


def main() -> None:
    """Entry point for the pluginkit-tour script."""
    app()
