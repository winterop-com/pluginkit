# Ordering

By default implementations run in registration order. Two markers override that
without touching registration:

- `@extension(tryfirst=True)` runs earlier;
- `@extension(trylast=True)` runs later.

```python
class WashPlugin:
    @extension(tryfirst=True)
    def prep_step(self, steps: list[str]) -> None:
        steps.append("wash produce")

class GarnishPlugin:
    @extension(trylast=True)
    def prep_step(self, steps: list[str]) -> None:
        steps.append("add garnish")
```

## The exact rule

Implementations are grouped into three buckets and called in this order:

1. `tryfirst`,
2. normal,
3. `trylast`.

Within each bucket, order is **registration order** (first registered runs
first). The demo registers the plugins out of order on purpose to prove the
markers, not registration, decide the outcome.

!!! note "Difference from pluggy"
    pluggy orders within a bucket **last-registered-first** (LIFO). pluginkit uses
    first-registered-first (FIFO) because it is easier to reason about in a
    teaching implementation. Both honour `tryfirst`/`trylast` the same way; only
    the tie-break within a bucket differs. See
    [Differences from pluggy](../production/vs-pluggy.md).

## optional

A plugin may implement a hook the host never declared. Normally that is an error
(it usually means a typo), but `optional=True` makes it tolerated - useful
when one plugin targets several host versions:

```python
class GarnishPlugin:
    @extension(optional=True)
    def not_a_real_hook(self) -> None:
        """Ignored cleanly if the host never specified this hook."""
```

## Run it

```bash
make run DEMO=ordering
```

```text
1. wash produce
2. chop fruit
3. add garnish
```
