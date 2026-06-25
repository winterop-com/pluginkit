# Cookbook

Worked examples of using `pluginkit` - copy one as a starting point. These are
*examples*, not shipped integrations: pluginkit has no framework-specific code, just
the small typed core. Two kinds:

## Basics

Bite-size, single-file scripts with **no third-party dependencies** - each is a small
realistic host demonstrating one mechanism:

```bash
uv run python examples/cookbook/quickstart.py
uv run python examples/cookbook/report_builder.py
uv run python examples/cookbook/notification_router.py
uv run python examples/cookbook/validation_rules.py
uv run python examples/cookbook/text_pipeline.py
uv run python examples/cookbook/app_lifecycle.py
uv run python examples/cookbook/async_fetch.py
```

| Example | Domain | pluginkit features |
| --- | --- | --- |
| `quickstart.py` | Greeter | the minimum: one spec, two extensions, one collecting call |
| `report_builder.py` | Document assembly | collecting hook, `tryfirst`/`trylast` ordering, a `wrapper` that frames output |
| `notification_router.py` | Message routing | `firstresult` selection, `tryfirst`, runtime `set_blocked` |
| `validation_rules.py` | Rules engine | collecting hook, one-off `call_extra`, runtime `unregister` |
| `text_pipeline.py` | Text processing | `pipeline` dispatch: each stage transforms the running value |
| `app_lifecycle.py` | App startup | `historic` config replayed to late plugins, collecting health check, `get_hookcallers` introspection |
| `async_fetch.py` | Async aggregation | `AsyncPluginManager` awaiting coroutine sources, observe-only async wrapper |

## Apps

Complete worked examples making a real framework **extensible** - features arrive by
registering a plugin rather than editing the app. Each owns one extension point,
plugins attach to a shared object, and the host fires it once while assembling:

```bash
uv run python examples/cookbook/fastapi_app.py     # serves on :8000
uv run python examples/cookbook/cli_app.py --help
uv run pytest examples/cookbook/pytest_plugin.py
```

| Example | Framework | Extension point | Docs |
| --- | --- | --- | --- |
| `fastapi_app.py` | FastAPI | `register_routes(router)` - plugins add endpoints | [FastAPI](../../docs/cookbook/fastapi.md) |
| `cli_app.py` | Click | `register_commands(cli)` - plugins add subcommands | [Click CLI](../../docs/cookbook/click.md) |
| `pytest_plugin.py` | pytest | `check(value)` - plugins add reusable test checks | [pytest](../../docs/cookbook/pytest.md) |

Each exposes a `run(...)` / `build_*()` factory so the behaviour is covered by
`tests/test_examples.py`. Swap `pm.register(...)` for `pm.load_entrypoints(...)` and
any installed package advertising the group contributes - the cross-package pattern
from [entry-point discovery](../../docs/mechanisms/entrypoints.md). For a single host
that walks through every mechanism, see `uv run pluginkit-tour run all`.
