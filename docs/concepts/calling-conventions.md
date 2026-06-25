# Calling conventions

Once plugins are registered, calling a hook runs a small dispatch engine inside
`HookCaller`. This page explains the rules that engine follows; each rule has a
dedicated [mechanism page](../mechanisms/direct.md) with a runnable demo.

## Typed calls: `pm.caller`

`pm.caller(spec)` returns a caller whose result type is derived from the spec's
dispatch mode and checked by mypy and pyright - no hand annotations:

```python
ingredients = pm.caller(Specs.add_ingredients)(base=["banana"])  # list[list[str]]
cup = pm.caller(Specs.choose_cup)(size="small")                  # str | None
```

`pm.hook.<name>(...)` works too and is more concise, but it is untyped (returns
`Any`). Use `pm.hook` for quick scripts and `pm.caller` when you want the type
checker's help; both share one `PluginManager`, so you never need a manager per spec.

## Keyword-only calls

Hooks are always called with keyword arguments:

```python
pm.caller(Specs.add_ingredients)(base=["banana"])   # good
pm.caller(Specs.add_ingredients)(["banana"])        # not how hooks are called
```

This is what lets each implementation declare **only the arguments it cares
about**. The caller passes the full set of kwargs; each implementation receives
the subset matching its own signature, computed once at registration with
`inspect.signature`.

```python
@extension
def add_ingredients(self):          # ignores base entirely
    return ["honey"]

@extension
def add_ingredients(self, base):    # receives base
    return [] if "berry" in base else ["blueberry"]
```

## Collecting vs first result

By default a hook is **collecting**: every implementation runs and the non-`None`
results are returned as a list.

```python
pm.caller(Specs.add_ingredients)(base=["banana"])
# [['blueberry', 'strawberry'], ['spinach', 'kale']]   # typed list[list[str]]
```

A spec marked `firstresult` stops at the first implementation that returns a
non-`None` value and returns that value directly - not a list (typed `R | None`):

```python
pm.caller(Specs.choose_cup)(size="small")   # '8oz paper cup'
```

`None` results are skipped in both modes, so an implementation can abstain simply
by returning `None`.

A third mode, [`pipeline`](../mechanisms/pipeline.md), threads the result of each
implementation into the next and returns the final value - a fold/middleware
chain.

## Order

Within a hook, implementations run in this order:

1. everything marked `tryfirst`,
2. then normal implementations,
3. then everything marked `trylast`.

Inside each of those three buckets, order is **registration order** (first
registered runs first). See [Ordering](../mechanisms/ordering.md) for the full
story and the difference from pluggy.

## Wrappers

An implementation marked `wrapper=True` is a generator that wraps the call: code
before its `yield` runs first, the value sent back to the `yield` is the result of
the inner (non-wrapper) implementations, and whatever the generator returns
replaces that result. Wrappers also observe exceptions. See
[Wrappers](../mechanisms/wrappers.md).

## Historic calls

A `historic` hook is called through `call_historic` instead of a plain call. The
caller remembers the call and replays it to any plugin registered afterwards, so
late-loading plugins still see one-off startup events. See
[Historic hooks](../mechanisms/historic.md).
