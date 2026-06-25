# Click CLI

The command-line counterpart of the [FastAPI example](fastapi.md): make a Click CLI
**extensible**, so subcommands arrive with a plugin rather than by editing the
command tree. The host owns one hook, `register_commands`, and each plugin attaches
its own commands to the root group.

Full runnable example:
[`examples/integrations/cli_app.py`](https://github.com/winterop-com/pluginkit/blob/main/examples/integrations/cli_app.py).

## The hook

```python
import click
from pluginkit import HookimplMarker, HookspecMarker, PluginManager

hookspec = HookspecMarker("cli")
hookimpl = HookimplMarker("cli")


class Specs:
    @staticmethod
    @hookspec
    def register_commands(cli: click.Group) -> None:
        """Attach subcommands to the root CLI group."""
```

## A plugin

```python
class GreetPlugin:
    @hookimpl
    def register_commands(self, cli: click.Group) -> None:
        @cli.command()
        @click.argument("name")
        def greet(name: str) -> None:
            click.echo(f"hello {name}")
```

## Assembling the CLI

The host builds the root group, registers its plugins, and fires the hook once so
each plugin mounts its commands:

```python
def build_cli(*plugins: object) -> click.Group:
    @click.group()
    def cli() -> None:
        """A CLI assembled entirely from plugins."""

    pm = PluginManager("cli")
    pm.add_hookspecs(Specs)
    for plugin in plugins or (GreetPlugin(), VersionPlugin()):
        pm.register(plugin)
    pm.caller(Specs.register_commands)(cli=cli)
    return cli
```

Testing uses Click's `CliRunner` against an app built from chosen plugins:

```python
from click.testing import CliRunner

def test_commands():
    cli = build_cli()
    runner = CliRunner()
    assert runner.invoke(cli, ["greet", "Ada"]).output.strip() == "hello Ada"
```

Swap `pm.register(...)` for `pm.load_entrypoints("cli")` and any installed package
advertising the `cli` group contributes subcommands - the same
[entry-point discovery](../mechanisms/entrypoints.md) pattern the FastAPI example
uses, applied to the command line.
