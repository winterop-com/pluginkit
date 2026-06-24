"""Exceptions raised by the plugin framework."""


class PluginValidationError(Exception):
    """Raised when a plugin or one of its hook implementations is invalid."""

    def __init__(self, plugin_name: str, message: str) -> None:
        """Record the offending plugin name alongside the message."""
        self.plugin_name = plugin_name
        super().__init__(f"plugin {plugin_name!r}: {message}")
