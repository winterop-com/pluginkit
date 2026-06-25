"""Project-bound extension_point / extension markers for the smoothie-kitchen host."""

from pluginkit import Extension, ExtensionPoint

# The project name ties specs, impls and entry points together, exactly like pluggy.
PROJECT_NAME = "kitchen"

extension_point = ExtensionPoint(PROJECT_NAME)
extension = Extension(PROJECT_NAME)
