# Integrations

Worked examples of pluginkit making a real framework **extensible** - features
arrive by registering a plugin rather than editing the app. Each follows the same
shape: the host owns one hook, plugins attach to a shared object, and the host fires
the hook once while assembling.

| Example | Framework | Hook | Docs |
| --- | --- | --- | --- |
| `fastapi_app.py` | FastAPI | `register_routes(router)` - plugins add endpoints | [FastAPI](../../docs/integrations/fastapi.md) |
| `cli_app.py` | Click | `register_commands(cli)` - plugins add subcommands | [Click CLI](../../docs/integrations/click.md) |
| `pytest_plugin.py` | pytest | `check(value)` - plugins add reusable test checks | [pytest](../../docs/integrations/pytest.md) |

```bash
uv run python examples/integrations/fastapi_app.py     # serves on :8000
uv run python examples/integrations/cli_app.py --help
uv run pytest examples/integrations/pytest_plugin.py
```

Each exposes a `build_*()` factory taking its plugins as arguments, so tests
assemble an app/CLI/checker from exactly the plugins under test
(`tests/test_examples.py`). Swap `pm.register(...)` for `pm.load_entrypoints(...)`
and any installed package advertising the group contributes - the cross-package
pattern from [entry-point discovery](../../docs/mechanisms/entrypoints.md).
