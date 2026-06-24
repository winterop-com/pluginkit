"""Make a FastAPI app pluggable: plugins contribute routes through a hook.

The host owns one `register_routes` hook. Each plugin attaches its own endpoints
to a shared router, and the host mounts the result - so features are added by
registering a plugin, never by editing the app.

Run: python examples/recipes/fastapi_app.py   (serves on http://127.0.0.1:8000)
"""

from fastapi import APIRouter, FastAPI

from pluginkit import HookimplMarker, HookspecMarker, PluginManager

hookspec = HookspecMarker("webapp")
hookimpl = HookimplMarker("webapp")


class Specs:
    """The contract the app exposes to route plugins."""

    @staticmethod
    @hookspec
    def register_routes(router: APIRouter) -> None:
        """Attach endpoints to the shared router."""


class HealthPlugin:
    """Adds a liveness endpoint."""

    @hookimpl
    def register_routes(self, router: APIRouter) -> None:
        """Mount GET /health."""

        @router.get("/health")
        def health() -> dict[str, str]:
            return {"status": "ok"}


class GreetingPlugin:
    """Adds a greeting endpoint."""

    @hookimpl
    def register_routes(self, router: APIRouter) -> None:
        """Mount GET /hello/{name}."""

        @router.get("/hello/{name}")
        def hello(name: str) -> dict[str, str]:
            return {"message": f"hello {name}"}


def build_app(*plugins: object) -> FastAPI:
    """Build a FastAPI app whose routes come entirely from registered plugins."""
    pm = PluginManager("webapp")
    pm.add_hookspecs(Specs)
    for plugin in plugins or (HealthPlugin(), GreetingPlugin()):
        pm.register(plugin)
    router = APIRouter()
    pm.hook.register_routes(router=router)
    app = FastAPI(title="pluginkit-powered API")
    app.include_router(router)
    return app


app = build_app()


def main() -> None:
    """Serve the assembled app."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
