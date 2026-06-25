"""An async data aggregator: plugins are async sources, collected by an await call.

Shows the AsyncPluginManager:

- a collecting hook whose implementations are `async def` and are awaited;
- an observe-only async wrapper (an async generator) that times the call;
- the same markers, registration and validation as the synchronous manager.

Run: python examples/async_fetch.py
"""
# mypy: disable-error-code="empty-body"
# pyright: reportReturnType=false

import asyncio
from collections.abc import AsyncGenerator

from pluginkit import AsyncPluginManager, HookimplMarker, HookspecMarker

hookspec = HookspecMarker("feed")
hookimpl = HookimplMarker("feed")


class Specs:
    """The aggregator's contract."""

    @staticmethod
    @hookspec
    def fetch(topic: str) -> str:
        """Fetch a headline for the topic from one source."""


class WeatherSource:
    """An async source with a little latency."""

    @hookimpl
    async def fetch(self, topic: str) -> str:
        """Return a weather headline after a simulated await."""
        await asyncio.sleep(0.01)
        return f"weather[{topic}]: clear skies"


class NewsSource:
    """Another async source."""

    @hookimpl
    async def fetch(self, topic: str) -> str:
        """Return a news headline after a simulated await."""
        await asyncio.sleep(0.01)
        return f"news[{topic}]: all quiet"


class StaticSource:
    """A plain (non-async) source; returning a value works too."""

    @hookimpl
    def fetch(self, topic: str) -> str:
        """Return a static line without awaiting."""
        return f"static[{topic}]: cached"


class TimingWrapper:
    """An observe-only async wrapper that announces the call."""

    @hookimpl(wrapper=True)
    async def fetch(self, topic: str) -> AsyncGenerator[None, list[str]]:
        """Print before and after the awaited fetch; does not change the result."""
        print(f"  [async] fetching {topic!r}...")
        try:
            yield
        finally:
            print(f"  [async] done fetching {topic!r}")


def build_plugin_manager() -> AsyncPluginManager:
    """Create an async manager with three sources and a timing wrapper."""
    pm = AsyncPluginManager("feed")
    pm.add_hookspecs(Specs)
    pm.register(WeatherSource(), name="weather")
    pm.register(NewsSource(), name="news")
    pm.register(StaticSource(), name="static")
    pm.register(TimingWrapper(), name="timing")
    return pm


async def gather(topic: str) -> list[str]:
    """Await every source and return their collected headlines."""
    pm = build_plugin_manager()
    headlines = await pm.caller(Specs.fetch)(topic=topic)
    return headlines


def main() -> None:
    """Run the async aggregator for one topic."""
    for line in asyncio.run(gather("harbor")):
        print(line)


if __name__ == "__main__":
    main()
