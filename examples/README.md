# Examples

Everything here uses the `pluginkit` library; none of it is part of the published
package. Three ways to learn it:

| Directory | What it is | Run it |
| --- | --- | --- |
| [`cookbook/`](cookbook/) | Worked examples - bite-size single-file scripts plus complete FastAPI / Click / pytest apps | `uv run python examples/cookbook/quickstart.py` |
| [`tour/`](tour/) | A guided CLI walkthrough that demos one mechanism at a time on a single host (the "smoothie kitchen") | `uv run pluginkit-tour run all` |
| [`external-plugin/`](external-plugin/) | A separate distribution that the tour discovers via entry points - shows cross-package plugin loading | installed automatically; see `tour/` demo 6 |

Start with `cookbook/quickstart.py` for the smallest possible example, the rest of the
`cookbook/` for fuller apps, or run the tour for a narrated pass through every feature.
