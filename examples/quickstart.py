"""Smallest possible pluginkit usage: declare a hook, implement it, call it.

Run: python examples/quickstart.py
"""
# Spec bodies are intentionally empty; pluginkit never runs them.
# mypy: disable-error-code="empty-body"
# pyright: reportReturnType=false

from pluginkit import HookimplMarker, HookspecMarker, PluginManager

hookspec = HookspecMarker("greeter")
hookimpl = HookimplMarker("greeter")


class Specs:
    """The contract this tiny app exposes to plugins."""

    @staticmethod
    @hookspec
    def greeting(name: str) -> str:
        """Return a greeting for the given name."""


class FormalPlugin:
    """Greets formally."""

    @hookimpl
    def greeting(self, name: str) -> str:
        """Return a formal greeting."""
        return f"Good day, {name}."


class CasualPlugin:
    """Greets casually."""

    @hookimpl
    def greeting(self, name: str) -> str:
        """Return a casual greeting."""
        return f"hey {name}!"


def run(name: str = "Ada") -> list[str]:
    """Register both plugins and collect their greetings."""
    pm = PluginManager("greeter")
    pm.add_hookspecs(Specs)
    pm.register(FormalPlugin(), name="formal")
    pm.register(CasualPlugin(), name="casual")
    greetings: list[str] = pm.hook.greeting(name=name)
    return greetings


def main() -> None:
    """Print the collected greetings."""
    for line in run():
        print(line)


if __name__ == "__main__":
    main()
