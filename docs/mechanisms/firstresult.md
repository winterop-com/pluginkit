# First result

A spec marked `firstresult` stops at the first implementation that returns a
non-`None` value and returns that value directly - not a list. It is the right
shape for **selection** and **resolution**: cup choosers, routers, resolvers.

```python
@extension_point(firstresult=True)
def choose_cup(size: str) -> str | None:
    """Pick a cup for the size; the first plugin to answer wins."""
```

## Abstaining

An implementation opts out of a particular call by returning `None`. The next
implementation in order is then given a chance.

```python
class SmallCupPlugin:
    @extension
    def choose_cup(self, size: str) -> str | None:
        return "8oz paper cup" if size == "small" else None   # abstain otherwise
```

## A fallback that always answers

Mark a catch-all `trylast` so the specific plugins are consulted first and the
fallback only runs when they all abstain:

```python
class FallbackCupPlugin:
    @extension(trylast=True)
    def choose_cup(self, size: str) -> str | None:
        return "16oz default cup"
```

## Run it

```bash
make run DEMO=firstresult
```

```text
 small -> 8oz paper cup
 large -> 20oz tumbler
medium -> 16oz default cup
```

## Notes

- If every implementation abstains, the call returns `None`.
- `firstresult` cannot be combined with `historic`; the manager rejects that at
  `add_extension_points` time.

See also the [notification router example](../index.md), which routes a message
to the first channel that accepts it.
