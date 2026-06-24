"""Project-bound hookspec / hookimpl markers for the smoothie-kitchen host."""

from pluginkit import HookimplMarker, HookspecMarker

# The project name ties specs, impls and entry points together, exactly like pluggy.
PROJECT_NAME = "kitchen"

hookspec = HookspecMarker(PROJECT_NAME)
hookimpl = HookimplMarker(PROJECT_NAME)
