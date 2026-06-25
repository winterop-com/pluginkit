"""Application startup where plugins may load before or after configuration.

Shows:

- a historic hook (`configure`) whose call is replayed to plugins registered
  later, so a plugin loaded after startup still receives the settings;
- a collecting hook (`health_check`) to poll every plugin's status;
- plugin introspection with `get_hookcallers`.

Run: python examples/app_lifecycle.py
"""
# mypy: disable-error-code="empty-body"
# pyright: reportReturnType=false

from pluginkit import HookimplMarker, HookspecMarker, PluginManager

hookspec = HookspecMarker("app")
hookimpl = HookimplMarker("app")

Settings = dict[str, str]


class Specs:
    """The application host's contract."""

    @staticmethod
    @hookspec(historic=True)
    def configure(settings: Settings) -> None:
        """Receive application settings once, at startup."""

    @staticmethod
    @hookspec
    def health_check() -> str:
        """Report the plugin's health."""


class DatabasePlugin:
    """Connects using the configured DSN."""

    def __init__(self) -> None:
        """Start unconfigured."""
        self.dsn = ""

    @hookimpl
    def configure(self, settings: Settings) -> None:
        """Capture the database DSN from settings."""
        self.dsn = settings.get("dsn", "")

    @hookimpl
    def health_check(self) -> str:
        """Report whether a DSN was configured."""
        return f"database: {'ok' if self.dsn else 'unconfigured'}"


class CachePlugin:
    """A plugin that loads late (e.g. discovered after startup)."""

    def __init__(self) -> None:
        """Start unconfigured."""
        self.ttl = ""

    @hookimpl
    def configure(self, settings: Settings) -> None:
        """Capture the cache TTL from settings."""
        self.ttl = settings.get("cache_ttl", "")

    @hookimpl
    def health_check(self) -> str:
        """Report the configured TTL."""
        return f"cache: ttl={self.ttl or 'unset'}"


def run() -> list[str]:
    """Start the app, configure it, then load a late plugin and poll health."""
    pm = PluginManager("app")
    pm.add_hookspecs(Specs)

    database = DatabasePlugin()
    pm.register(database, name="database")

    # Startup fires the historic event with only the database plugin present.
    pm.caller(Specs.configure).call_historic(kwargs={"settings": {"dsn": "postgres://...", "cache_ttl": "60"}})

    # The cache plugin loads afterwards but still receives the replayed settings.
    pm.register(CachePlugin(), name="cache")

    # Introspection: which hooks does the cache plugin contribute to?
    cache_hooks = pm.get_hookcallers(pm.get_plugin("cache"))
    assert cache_hooks is not None
    print("cache contributes to:", sorted(caller.name for caller in cache_hooks))

    statuses = pm.caller(Specs.health_check)()
    return statuses


def main() -> None:
    """Print each plugin's health after configuration."""
    for status in run():
        print(status)


if __name__ == "__main__":
    main()
