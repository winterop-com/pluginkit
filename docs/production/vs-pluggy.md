# pluginkit vs pluggy

pluggy is the mature, widely-used hook framework (it powers pytest, tox, and
datasette). pluginkit is a smaller, **strictly-typed** alternative for Python 3.13+
codebases that want hook calls their type checker actually understands. This page is
the honest comparison.

## The headline: typed hooks

In pluggy, `pm.hook.foo(...)` returns `Any` - the type checker sees neither the
hook's arguments nor its result. pluginkit derives both from the spec:

```python
greetings = pm.caller(Specs.greeting)(name="Ada")   # list[str]
cup = pm.caller(Specs.choose_cup)(size="L")          # str | None  (firstresult)
total = pm.caller(Specs.fold)(value=v)               # R           (pipeline)
```

The return type is mode-correct - `list[R]` for collecting, `R | None` for
firstresult, `R` for pipeline - and checked by mypy and pyright, not asserted by
hand. This is the main reason to reach for pluginkit, and it is practical precisely
because it targets only Python 3.13 (PEP 695 generics + ParamSpec).

## Also beyond pluggy

- **[Pipeline dispatch](../mechanisms/pipeline.md)** - a fold/middleware mode where
  each impl transforms the previous result. pluggy has no built-in equivalent.
- **[Async dispatch](async.md)** - an `AsyncPluginManager` that awaits coroutine
  implementations. In pluggy this needs the separate `apluggy` package.
- Zero runtime dependencies and a `py.typed` marker, in a few readable files.

## Behavioural differences

| Area | pluginkit | pluggy |
| --- | --- | --- |
| Order within a bucket | first-registered-first (FIFO) | last-registered-first (LIFO) |
| Dispatch core | plain Python loop | optimised, with a C-accelerated multicall |
| Argument passing | filtered per call via `inspect.signature` | arg lists precomputed once per impl |

The ordering tie-break is the one you might actually notice: pluginkit calls
same-priority implementations in registration order; pluggy calls them in reverse.
Both honour `tryfirst`/`trylast` identically. Dispatch speed is competitive and fast
enough in practice; performance is not a reason to pick one over the other.

## What pluggy has that pluginkit does not

- broad Python-version support (pluginkit is 3.13+ only);
- a C-accelerated multicall, a large test suite, and years of edge-case hardening;
- the legacy `hookwrapper` style (pluginkit has only the modern `wrapper=True`);
- spec enforcement of *required* arguments, warn-on-impl options, call monitoring /
  tracing, `subset_hook_caller`, and other advanced relay manipulation.

pluginkit shares the core surface otherwise: collecting and `firstresult` specs,
`tryfirst`/`trylast`, `optionalhook`, `specname`, generator wrappers with exception
safety, historic hooks, `call_extra`, `unregister`/blocking/lookup, registration- and
call-time validation, and entry-point discovery.

## When to use which

- **pluginkit** - you are on Python 3.13+, you want typed hooks with correct return
  types, and a small dependency-free plugin layer you fully control.
- **pluggy** - you need broad Python-version support, maximum maturity, or the wider
  feature surface above.
