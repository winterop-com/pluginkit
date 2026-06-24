"""Make test helpers pluggable: share reusable checks across suites via a hook.

A host collects "checks" contributed by plugins and runs them over a value. Expose
`build_checker()` through a pytest fixture (in your conftest) and any installed
package advertising the "checks" group can add assertions - without the test suite
importing it. Swap `pm.register(...)` for `pm.load_entrypoints("checks")` for the
cross-package version.

Run the demonstration test: pytest examples/integrations/pytest_plugin.py
"""

import pytest

from pluginkit import HookimplMarker, HookspecMarker, PluginManager

hookspec = HookspecMarker("checks")
hookimpl = HookimplMarker("checks")


class Specs:
    """The contract a check plugin implements."""

    @staticmethod
    @hookspec
    def check(value: object) -> str | None:
        """Return an error message if value fails this check, else None."""


class NonEmptyPlugin:
    """Rejects empty containers and strings."""

    @hookimpl
    def check(self, value: object) -> str | None:
        """Flag empty values."""
        return "value is empty" if value in ("", [], {}) else None


class NotNonePlugin:
    """Rejects None."""

    @hookimpl
    def check(self, value: object) -> str | None:
        """Flag None."""
        return "value is None" if value is None else None


class Checker:
    """Runs every registered check over a value and collects the failures."""

    def __init__(self, pm: PluginManager) -> None:
        """Wrap a configured plugin manager."""
        self._pm = pm

    def errors(self, value: object) -> list[str]:
        """Return the messages from checks that failed (empty == all passed)."""
        return [message for message in self._pm.hook.check(value=value) if message]


def build_checker(*plugins: object) -> Checker:
    """Assemble a checker from the given plugins (or the defaults)."""
    pm = PluginManager("checks")
    pm.add_hookspecs(Specs)
    for plugin in plugins or (NonEmptyPlugin(), NotNonePlugin()):
        pm.register(plugin)
    return Checker(pm)


@pytest.fixture
def checker() -> Checker:
    """A checker assembled from the default plugins; register your own per test."""
    return build_checker()


def test_checker_flags_empty_and_none(checker: Checker) -> None:
    """The bundled checks reject empty and None, and pass a real value."""
    assert checker.errors("") == ["value is empty"]
    assert checker.errors(None) == ["value is None"]
    assert checker.errors("ok") == []
