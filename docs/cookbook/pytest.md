# pytest

pytest itself runs on a plugin system, so this is not about replacing it - it is
about making **your own test helpers pluggable**. A host collects reusable *checks*
contributed by plugins and runs them over a value; expose it through a fixture and
other installed packages can add assertions without your suite importing them.

Full runnable example:
[`examples/cookbook/pytest_plugin.py`](https://github.com/winterop-com/pluginkit/blob/main/examples/cookbook/pytest_plugin.py).

## The hook and a plugin

```python
from pluginkit import Extension, ExtensionPoint, PluginManager

extension_point = ExtensionPoint("checks")
extension = Extension("checks")


class Specs:
    @staticmethod
    @extension_point
    def check(value: object) -> str | None:
        """Return an error message if value fails this check, else None."""


class NotNonePlugin:
    @extension
    def check(self, value: object) -> str | None:
        return "value is None" if value is None else None
```

## Exposing it as a fixture

`build_checker` assembles a checker from its plugins; a fixture in your `conftest.py`
hands it to tests:

```python
import pytest

def build_checker(*plugins: object) -> Checker:
    pm = PluginManager("checks")
    pm.add_extension_points(Specs)
    for plugin in plugins or (NonEmptyPlugin(), NotNonePlugin()):
        pm.register(plugin)
    return Checker(pm)


@pytest.fixture
def checker() -> Checker:
    return build_checker()


def test_rejects_none(checker):
    assert checker.errors(None) == ["value is None"]
```

Swap `pm.register(...)` for `pm.load_entrypoints("checks")` and any installed
package advertising the `checks` group contributes assertions to every suite that
uses the fixture - the cross-package
[entry-point discovery](../mechanisms/entrypoints.md) pattern, applied to testing.
