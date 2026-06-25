# pluginkit-tour

A worked example host - the "smoothie kitchen" - that walks through every
pluginkit mechanism one at a time on a single host. It is a separate distribution
that depends on the [`pluginkit`](../) library, so the library package stays free
of demo code.

```bash
uv run pluginkit-tour list
uv run pluginkit-tour run all
uv run pluginkit-tour run wrapper
```

The host's extension points live in `src/pluginkit_tour/points.py`; each
`demo_0N_*.py` module is a focused walkthrough of one mechanism. The
`contrib/honey.py` module is an entry-point plugin (declared in this project's
`pyproject.toml`), and `examples/external-plugin/` is a separate uv project - an
external plugin distribution discovered the same way.
