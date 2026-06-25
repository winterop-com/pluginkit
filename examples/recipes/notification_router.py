"""Route a notification to the first channel that accepts it.

Shows:

- a firstresult hook (`deliver`) where the first channel to answer wins;
- ordering (`tryfirst`) so an urgent channel is tried before the rest;
- runtime control: blocking a channel with `set_blocked` removes it from routing.

Run: python examples/notification_router.py
"""
# mypy: disable-error-code="empty-body"
# pyright: reportReturnType=false

from pluginkit import Extension, ExtensionPoint, PluginManager

extension_point = ExtensionPoint("notify")
extension = Extension("notify")


class Specs:
    """The notification host's contract."""

    @staticmethod
    @extension_point(firstresult=True)
    def deliver(message: str, urgent: bool) -> str | None:
        """Deliver the message and return a receipt, or None to defer to others."""


class SmsChannel:
    """Sends SMS, but only for urgent messages; tried first."""

    @extension(tryfirst=True)
    def deliver(self, message: str, urgent: bool) -> str | None:
        """Handle only urgent messages."""
        return f"SMS sent: {message!r}" if urgent else None


class EmailChannel:
    """Sends email for anything."""

    @extension
    def deliver(self, message: str, urgent: bool) -> str | None:
        """Handle any message."""
        return f"Email sent: {message!r}"


class SlackChannel:
    """A fallback chat channel."""

    @extension(trylast=True)
    def deliver(self, message: str, urgent: bool) -> str | None:
        """Handle any message, but only if nothing else did."""
        return f"Slack posted: {message!r}"


def build_plugin_manager() -> PluginManager:
    """Create a manager with all channels registered."""
    pm = PluginManager("notify")
    pm.add_extension_points(Specs)
    pm.register(SmsChannel(), name="sms")
    pm.register(EmailChannel(), name="email")
    pm.register(SlackChannel(), name="slack")
    return pm


def route(pm: PluginManager, message: str, *, urgent: bool) -> str:
    """Return the receipt from the first channel that accepted the message."""
    receipt = pm.caller(Specs.deliver)(message=message, urgent=urgent) or ""
    return receipt


def main() -> None:
    """Demonstrate routing, then block the email channel and route again."""
    pm = build_plugin_manager()
    print("urgent   ->", route(pm, "Server down!", urgent=True))
    print("normal   ->", route(pm, "Weekly digest", urgent=False))

    # Operations decides email is noisy and blocks it at runtime.
    pm.set_blocked("email")
    print("after blocking email:")
    print("normal   ->", route(pm, "Weekly digest", urgent=False))


if __name__ == "__main__":
    main()
