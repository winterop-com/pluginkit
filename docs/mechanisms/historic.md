# Historic hooks

A spec marked `historic` remembers its calls and replays them to plugins
registered **after** the call happened. This suits one-off events - startup,
configuration loaded - where some plugins may load late (for example via
entry-point discovery that runs after the event already fired).

```python
@extension_point(historic=True)
def kitchen_opened(name: str) -> None:
    """Announce the kitchen opened; late plugins still hear it."""
```

## Calling a historic hook

A historic hook is **not** called like a normal one. Use `call_historic`, passing
the keyword arguments as a dict and an optional callback for each result:

```python
pm.caller(Specs.kitchen_opened).call_historic(
    kwargs={"name": "Main Street"},
    result_callback=log.append,
)
```

Calling a historic hook with the plain `pm.caller(Specs.kitchen_opened)(...)` form
raises a `TypeError`, and vice versa - the two calling styles are kept distinct on
purpose.

## Replay to late plugins

Any plugin registered after the call immediately receives it:

```python
pm.register(early, name="early")
pm.caller(Specs.kitchen_opened).call_historic(kwargs={"name": "Main Street"})
pm.register(late, name="late")     # 'late' still runs kitchen_opened("Main Street")
```

The `result_callback` fires once per implementation - for plugins present at call
time, and again for each late plugin as it is registered.

## Constraints

- A historic hook cannot be `firstresult` (replay has no single "winner"); the
  manager rejects that combination at `add_extension_points` time.

## Run it

```bash
make run DEMO=historic
```

```text
Early plugin greeting: Early staff ready at Main Street
Late plugin greeting:  Late staff caught up at Main Street (registered after the event)
result_callback saw:  ['Early staff ready at Main Street', 'Late staff caught up at Main Street']
```

The [app lifecycle example](../index.md) uses a historic `configure` hook so a
late-loading cache plugin still receives the application settings.
