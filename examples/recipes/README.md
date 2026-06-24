# Recipes

Self-contained scripts using the `pluginkit` library directly. Each one is a
small, realistic host in a different domain. Run any of them:

```bash
uv run python examples/recipes/quickstart.py
uv run python examples/recipes/report_builder.py
uv run python examples/recipes/notification_router.py
uv run python examples/recipes/validation_rules.py
uv run python examples/recipes/text_pipeline.py
uv run python examples/recipes/app_lifecycle.py
uv run python examples/recipes/async_fetch.py
uv run python examples/recipes/fastapi_app.py
```

| Example | Domain | pluginkit features |
| --- | --- | --- |
| `quickstart.py` | Greeter | the minimum: one spec, two impls, one collecting call |
| `report_builder.py` | Document assembly | collecting hook, `tryfirst`/`trylast` ordering, a `wrapper` that frames output |
| `notification_router.py` | Message routing | `firstresult` selection, `tryfirst`, runtime `set_blocked` |
| `validation_rules.py` | Rules engine | collecting hook, one-off `call_extra`, runtime `unregister` |
| `text_pipeline.py` | Text processing | `pipeline` dispatch: each stage transforms the running value |
| `app_lifecycle.py` | App startup | `historic` config replayed to late plugins, collecting health check, `get_hookcallers` introspection |
| `async_fetch.py` | Async aggregation | `AsyncPluginManager` awaiting coroutine sources, observe-only async wrapper |
| `fastapi_app.py` | Web API | a hook that lets plugins contribute FastAPI routes - see [docs](../../docs/integrations/fastapi.md) |

Each script exposes a `run(...)` (or `build_plugin_manager()`/`build_app()`) function
so the behaviour is covered by `tests/test_examples.py`.

For a single host that walks through every mechanism one at a time, see the
bundled demo: `uv run pluginkit-tour run all`.
