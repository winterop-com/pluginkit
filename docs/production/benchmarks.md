# Benchmarks

A head-to-head micro-benchmark against pluggy, to quantify the cost of
pluginkit's readable dispatch. Both libraries expose the same surface, so each
scenario is built from one factory and timed identically (best-of-repeats).

Run it yourself:

```bash
make bench
```

## Representative numbers

From one run (Apple Silicon, CPython 3.13, pluggy 1.6, pluginkit 0.1). Absolute
numbers vary by machine; the **ratio** is the point. Lower is better.

| Scenario | pluggy | pluginkit | ratio |
| --- | ---: | ---: | ---: |
| call: collecting, 5 impls | ~1020 ns | ~845 ns | 0.83x |
| call: collecting, 20 impls | ~2800 ns | ~2450 ns | 0.87x |
| call: firstresult, 5 impls | ~580 ns | ~385 ns | 0.66x |
| call: wrapped, 2 wrappers | ~1410 ns | ~1170 ns | 0.83x |
| register: 10 plugins | ~455 us | ~505 us | 1.11x |
| register: 100 plugins | ~2680 us | ~2150 us | 0.80x |

Below 1.0 means pluginkit is faster. After a round of optimisation, pluginkit's
dispatch is now competitive with - and in these micro-benchmarks slightly faster
than - pluggy.

## What made dispatch fast

The first cut was 1.1x-1.7x *slower*. Closing that came down to not paying for
work that is not needed on the hot path - no behaviour changed, the full test
suite passes unchanged:

- **No-wrapper fast path.** Most hooks have no wrappers, so the common call skips
  the wrapper setup, the `try`/`except`, and the generator bookkeeping entirely.
- **Pass-through forwarding.** Each impl records whether it declares exactly the
  spec's arguments. When it does (the common case), the call forwards `kwargs`
  directly instead of rebuilding a filtered dict; a subset impl indexes only the
  few it needs. Both avoid a per-impl membership scan.
- **Allocation-free validation.** Call-time argument checking compares
  `kwargs.keys()` against the spec's argument set directly, with no intermediate
  `frozenset`.
- **Inlined loops.** The collecting and firstresult paths loop directly instead of
  going through a generator.

## Does it matter?

Barely, and that is the real takeaway. For a typical host - tens of plugins, hooks
called thousands of times, not millions - the per-call cost of *any* of these
libraries is dwarfed by the work the implementations do. The benchmark mostly
shows that dispatch overhead is not a reason to avoid pluginkit.

!!! note "Micro-benchmark caveats"
    These measure dispatch overhead with trivial implementations (each returns a
    constant), which maximises the visible difference. Real implementations do
    real work, shrinking any relative gap to noise. pluggy also handles edge cases
    and provides features pluginkit does not - see
    [Differences from pluggy](vs-pluggy.md). Speed is not the reason to pick one.
