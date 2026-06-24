# Examples

Everything here uses the `pluginkit` library; none of it is part of the published
package. Three ways to learn it, from quickest to most complete:

| Directory | What it is | Run it |
| --- | --- | --- |
| [`recipes/`](recipes/) | Standalone single-file scripts, one realistic host each | `uv run python examples/recipes/quickstart.py` |
| [`tour/`](tour/) | A guided CLI walkthrough that demos one mechanism at a time on a single host (the "smoothie kitchen") | `uv run pluginkit-tour run all` |
| [`external-plugin/`](external-plugin/) | A separate distribution that the tour discovers via entry points - shows cross-package plugin loading | installed automatically; see `tour/` demo 6 |

Start with `recipes/quickstart.py` for the smallest possible example, or run the
tour for a narrated pass through every feature.
