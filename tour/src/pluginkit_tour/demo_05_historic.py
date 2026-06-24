"""Demo 5: historic hooks replay past calls to plugins registered later."""

from pluginkit import PluginManager
from pluginkit_tour import hookspecs
from pluginkit_tour.markers import PROJECT_NAME, hookimpl


class EarlyStaffPlugin:
    """Registered before the kitchen opens."""

    def __init__(self) -> None:
        """Start with no greeting."""
        self.greeting = ""

    @hookimpl
    def kitchen_opened(self, name: str) -> str:
        """React to the opening announcement."""
        self.greeting = f"Early staff ready at {name}"
        return self.greeting


class LateStaffPlugin:
    """Registered after the kitchen already opened; still hears the event."""

    def __init__(self) -> None:
        """Start with no greeting."""
        self.greeting = ""

    @hookimpl
    def kitchen_opened(self, name: str) -> str:
        """React to the replayed opening announcement."""
        self.greeting = f"Late staff caught up at {name}"
        return self.greeting


def run() -> tuple[EarlyStaffPlugin, LateStaffPlugin, list[str]]:
    """Open the kitchen, then register a late plugin and show it still reacts."""
    pm = PluginManager(PROJECT_NAME)
    pm.add_hookspecs(hookspecs)

    callback_log: list[str] = []
    early = EarlyStaffPlugin()
    pm.register(early, name="early")

    # Fire the historic event. Only "early" is registered right now.
    pm.hook.kitchen_opened.call_historic(kwargs={"name": "Main Street"}, result_callback=callback_log.append)

    # Register a plugin AFTER the event -- the caller replays the call for it.
    late = LateStaffPlugin()
    pm.register(late, name="late")

    return early, late, callback_log


def main() -> None:
    """Run the historic-hook demo."""
    early, late, callback_log = run()
    print("Early plugin greeting:", early.greeting)
    print("Late plugin greeting: ", late.greeting, "(registered after the event)")
    print("result_callback saw: ", callback_log)
