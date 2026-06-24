"""pluginkit: a small, dependency-free, pluggy-style plugin framework.

Public API:

- :class:`HookspecMarker` / :class:`HookimplMarker` - decorators that declare hook
  specifications and implementations.
- :class:`HookspecOpts` / :class:`HookimplOpts` - the option records the markers stamp.
- :class:`PluginManager` - registers plugins and dispatches hook calls.
- :class:`HookRelay` / :class:`HookCaller` / :class:`HookImpl` - the dispatch internals.
- :class:`PluginValidationError` - raised when a plugin is invalid.
"""

from pluginkit.aio import AsyncHookCaller, AsyncPluginManager
from pluginkit.exceptions import PluginValidationError
from pluginkit.manager import HookCaller, HookImpl, HookRelay, PluginManager
from pluginkit.markers import (
    HookimplMarker,
    HookimplOpts,
    HookspecMarker,
    HookspecOpts,
)

__version__ = "0.1.0"

__all__ = [
    "AsyncHookCaller",
    "AsyncPluginManager",
    "HookCaller",
    "HookImpl",
    "HookRelay",
    "HookimplMarker",
    "HookimplOpts",
    "HookspecMarker",
    "HookspecOpts",
    "PluginManager",
    "PluginValidationError",
    "__version__",
]
