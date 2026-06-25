"""pluginkit: a small, strictly-typed, generics-first plugin framework for Python 3.13+.

Unlike untyped hook systems, pluginkit derives a hook call's return type from its
spec: ``pm.caller(spec)`` hands back a caller whose result is ``list[R]``
(collecting), ``R | None`` (firstresult), or ``R`` (pipeline) - checked, not asserted.

Public API:

- :class:`ExtensionPoint` / :class:`Extension` - decorators that declare extension
  points and the extensions that fulfil them. ``@extension_point`` brands the
  declaration by dispatch mode.
- :class:`ExtensionPointOpts` / :class:`ExtensionOpts` - the option records the markers stamp.
- :class:`PluginManager` - registers plugins and dispatches calls; ``caller(spec)``
  returns a typed caller.
- :class:`CollectingSpec` / :class:`FirstResultSpec` / :class:`PipelineSpec` - branded
  spec types, and :class:`CollectingCaller` / :class:`FirstResultCaller` /
  :class:`PipelineCaller` (and the ``Async*`` variants) - the typed callers.
- :class:`HookRelay` / :class:`HookCaller` / :class:`HookImpl` - the dispatch internals.
- :class:`PluginValidationError` - raised when a plugin is invalid.
"""

from importlib.metadata import PackageNotFoundError, version

from pluginkit.aio import (
    AsyncCollectingCaller,
    AsyncFirstResultCaller,
    AsyncHookCaller,
    AsyncPipelineCaller,
    AsyncPluginManager,
)
from pluginkit.exceptions import PluginValidationError
from pluginkit.manager import (
    CollectingCaller,
    FirstResultCaller,
    HistoricCaller,
    HookCaller,
    HookImpl,
    HookRelay,
    PipelineCaller,
    PluginManager,
)
from pluginkit.markers import (
    CollectingSpec,
    Extension,
    ExtensionOpts,
    ExtensionPoint,
    ExtensionPointOpts,
    FirstResultSpec,
    HistoricSpec,
    PipelineSpec,
)

try:
    __version__ = version("pluginkit")
except PackageNotFoundError:  # pragma: no cover - running from a source tree without an install
    __version__ = "0.0.0+unknown"

__all__ = [
    "AsyncCollectingCaller",
    "AsyncFirstResultCaller",
    "AsyncHookCaller",
    "AsyncPipelineCaller",
    "AsyncPluginManager",
    "CollectingCaller",
    "CollectingSpec",
    "Extension",
    "ExtensionOpts",
    "ExtensionPoint",
    "ExtensionPointOpts",
    "FirstResultCaller",
    "FirstResultSpec",
    "HistoricCaller",
    "HistoricSpec",
    "HookCaller",
    "HookImpl",
    "HookRelay",
    "PipelineCaller",
    "PipelineSpec",
    "PluginManager",
    "PluginValidationError",
    "__version__",
]
