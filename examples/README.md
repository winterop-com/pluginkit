# Examples

Everything here uses the `pluginkit` library; none of it is part of the published
package. Four ways to learn it, from quickest to most complete:

| Directory | What it is | Run it |
| --- | --- | --- |
| [`recipes/`](recipes/) | Standalone single-file scripts (no third-party deps), one realistic host each | `uv run python examples/recipes/quickstart.py` |
| [`integrations/`](integrations/) | Real-framework integrations - FastAPI, Click, pytest | `uv run python examples/integrations/cli_app.py --help` |
| [`tour/`](tour/) | A guided CLI walkthrough that demos one mechanism at a time on a single host (the "smoothie kitchen") | `uv run pluginkit-tour run all` |
| [`external-plugin/`](external-plugin/) | A separate distribution that the tour discovers via entry points - shows cross-package plugin loading | installed automatically; see `tour/` demo 6 |

Start with `recipes/quickstart.py` for the smallest possible example, the
`integrations/` for plugging into a real framework, or run the tour for a narrated
pass through every feature.
