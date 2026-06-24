# FastAPI

A realistic use of pluginkit: make a web app **extensible**, so features are added
by installing a plugin rather than editing the app. The host owns one hook,
`register_routes`, and each plugin attaches its own endpoints to a shared router.

Full runnable example:
[`examples/integrations/fastapi_app.py`](https://github.com/winterop-com/pluginkit/blob/main/examples/integrations/fastapi_app.py).

## The hook

```python
from fastapi import APIRouter, FastAPI
from pluginkit import HookimplMarker, HookspecMarker, PluginManager

hookspec = HookspecMarker("webapp")
hookimpl = HookimplMarker("webapp")


class Specs:
    @staticmethod
    @hookspec
    def register_routes(router: APIRouter) -> None:
        """Attach endpoints to the shared router."""
```

## A plugin

A plugin is any object whose method carries `@hookimpl`. It adds routes to the
router it is handed - it never imports or edits the host app:

```python
class GreetingPlugin:
    @hookimpl
    def register_routes(self, router: APIRouter) -> None:
        @router.get("/hello/{name}")
        def hello(name: str) -> dict[str, str]:
            return {"message": f"hello {name}"}
```

## Assembling the app

The host registers its plugins, fires the hook once over a shared router, and
mounts it. Adding a feature later means registering one more plugin here (or, with
[entry-point discovery](../mechanisms/entrypoints.md), installing a package):

```python
def build_app(*plugins: object) -> FastAPI:
    pm = PluginManager("webapp")
    pm.add_hookspecs(Specs)
    for plugin in plugins or (HealthPlugin(), GreetingPlugin()):
        pm.register(plugin)
    router = APIRouter()
    pm.hook.register_routes(router=router)
    app = FastAPI()
    app.include_router(router)
    return app
```

Because `build_app` takes its plugins as arguments, tests assemble an app from
exactly the plugins under test:

```python
from fastapi.testclient import TestClient

def test_routes():
    client = TestClient(build_app())
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/hello/Ada").json() == {"message": "hello Ada"}
```

## Why route through a hook

- **No edits to the core.** New endpoints arrive with a plugin, so the app file
  stays stable as features grow.
- **Entry-point discovery.** Swap `pm.register(...)` for
  `pm.load_entrypoints("webapp")` and any installed distribution advertising the
  `webapp` group contributes routes - the cross-package pattern shown in
  [entry-point discovery](../mechanisms/entrypoints.md).
- **Testable in isolation.** Each plugin is a plain object; assemble an app from
  one plugin and exercise just its routes.
