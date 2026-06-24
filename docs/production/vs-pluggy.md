# Differences from pluggy

pluginkit implements the ideas behind pluggy in a few readable files. It is solid
enough to use, but it is not a drop-in replacement. This page is the honest
inventory of what differs and what is missing.

## Behavioural differences

| Area | pluginkit | pluggy |
| --- | --- | --- |
| Order within a bucket | first-registered-first (FIFO) | last-registered-first (LIFO) |
| Dispatch core | plain Python loop | optimised, with a C-accelerated multicall |
| Argument passing | filtered per call via `inspect.signature` | arg lists precomputed once per impl |

The ordering tie-break is the one you might actually notice: pluginkit calls
same-priority implementations in the order they were registered; pluggy calls them
in reverse. Both honour `tryfirst`/`trylast` identically - only the within-bucket
tie-break differs.

Dispatch speed is competitive and fast enough in practice; performance is not a
reason to pick one over the other.

## Features pluginkit has

Direct registration, collecting and `firstresult` specs, `tryfirst`/`trylast`,
`optionalhook`, `specname`, generator wrappers with exception safety, historic
hooks, `call_extra`, plugin `unregister`/blocking/lookup, registration-time
validation, call-time argument validation, and entry-point discovery.

## Features pluginkit adds beyond pluggy

- **[Pipeline dispatch](../mechanisms/pipeline.md)** - a fold/middleware mode
  where each impl transforms the previous result. pluggy has no built-in
  equivalent.
- **[Async dispatch](async.md)** - an `AsyncPluginManager` that awaits coroutine
  implementations. In pluggy this needs the separate `apluggy` package.

## Features pluginkit does not have

- the legacy `hookwrapper` style (only the modern `wrapper=True`);
- `specname` validation beyond argument names, and warn-on-impl options;
- spec enforcement of *required* arguments (it checks that impl args are a subset
  of spec args, not that required ones are present);
- call monitoring / tracing hooks for debugging dispatch;
- `subset_hook_caller` and other advanced relay manipulation;
- the breadth of pluggy's test suite, edge-case handling, and Python-version
  coverage.

## When to use which

- **Use pluggy** for anything you ship to production. It is maintained, battle
  tested by pytest and friends, and has all of the above.
- **Use pluginkit** to understand how a system like pluggy works, or as a starting
  point you fully control for a small, embedded plugin layer.

If you find yourself adding the missing items above one by one, you are
re-deriving pluggy - at which point you should just depend on it.
