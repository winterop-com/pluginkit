"""Make a Click CLI pluggable: plugins contribute subcommands through a hook.

The host owns one `register_commands` hook and a root command group. Each plugin
attaches its own subcommands, so the CLI grows by registering a plugin rather than
editing the command tree.

Run: python examples/integrations/cli_app.py --help
"""

import click

from pluginkit import HookimplMarker, HookspecMarker, PluginManager

hookspec = HookspecMarker("cli")
hookimpl = HookimplMarker("cli")


class Specs:
    """The contract the CLI exposes to command plugins."""

    @staticmethod
    @hookspec
    def register_commands(cli: click.Group) -> None:
        """Attach subcommands to the root CLI group."""


class GreetPlugin:
    """Adds a `greet` command."""

    @hookimpl
    def register_commands(self, cli: click.Group) -> None:
        """Mount `greet NAME`."""

        @cli.command()
        @click.argument("name")
        def greet(name: str) -> None:
            """Greet someone by name."""
            click.echo(f"hello {name}")


class VersionPlugin:
    """Adds a `version` command."""

    @hookimpl
    def register_commands(self, cli: click.Group) -> None:
        """Mount `version`."""

        @cli.command()
        def version() -> None:
            """Print the app version."""
            click.echo("1.0.0")


def build_cli(*plugins: object) -> click.Group:
    """Build a Click group whose subcommands come entirely from registered plugins."""

    @click.group()
    def cli() -> None:
        """A CLI assembled entirely from plugins."""

    pm = PluginManager("cli")
    pm.add_hookspecs(Specs)
    for plugin in plugins or (GreetPlugin(), VersionPlugin()):
        pm.register(plugin)
    pm.caller(Specs.register_commands)(cli=cli)
    return cli


cli = build_cli()


def main() -> None:
    """Run the assembled CLI."""
    cli()


if __name__ == "__main__":
    main()
