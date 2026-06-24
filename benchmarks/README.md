# benchmarks

A head-to-head micro-benchmark of `pluginkit` against `pluggy`. Both libraries
expose the same surface, so each scenario is built from one factory and timed
identically (best-of-repeats).

```bash
make bench
# or
uv run python benchmarks/bench.py
```

`pluggy` is a dev-only dependency used solely here; the `pluginkit` library
itself has zero runtime dependencies.

See [docs/production/benchmarks.md](../docs/production/benchmarks.md) for
representative numbers and how to interpret them.
