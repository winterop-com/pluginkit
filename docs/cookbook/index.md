# Cookbook

Worked examples of using pluginkit - copy one as a starting point. These are
**examples, not shipped integrations**: pluginkit has no framework-specific code, just
the small typed core. The full sources live in
[`examples/cookbook/`](https://github.com/winterop-com/pluginkit/tree/main/examples/cookbook).

## Basics

Bite-size, dependency-free scripts - each a small host demonstrating one mechanism:

| Example | Domain | Shows |
| --- | --- | --- |
| `quickstart.py` | Greeter | the minimum: one extension point, two extensions, one collecting call |
| `report_builder.py` | Document assembly | collecting, `tryfirst`/`trylast`, a `wrapper` that frames output |
| `notification_router.py` | Message routing | `firstresult`, `tryfirst`, runtime `set_blocked` |
| `validation_rules.py` | Rules engine | collecting, one-off `call_extra`, runtime `unregister` |
| `text_pipeline.py` | Text processing | `pipeline` dispatch |
| `app_lifecycle.py` | App startup | `historic` replay, health check, `get_hookcallers` |
| `async_fetch.py` | Async aggregation | `AsyncPluginManager`, observe-only async wrapper |

```bash
uv run python examples/cookbook/quickstart.py
```

## Apps

Complete worked examples making a real framework **extensible** - features arrive by
registering a plugin rather than editing the app. Each owns one extension point,
plugins attach to a shared object, and the host fires it once while assembling:

- **[FastAPI](fastapi.md)** - plugins contribute routes.
- **[Click CLI](click.md)** - plugins contribute subcommands.
- **[pytest](pytest.md)** - plugins contribute reusable test checks.

Each exposes a `build_*()` factory, so tests assemble an app from exactly the plugins
under test. Swap `pm.register(...)` for `pm.load_entrypoints(...)` and any installed
package advertising the group contributes - the cross-package pattern from
[entry-point discovery](../mechanisms/entrypoints.md).
