# Specs and implementations

The markers are the smallest part of the framework but they set up everything
else. Source: [`pluginkit/markers.py`](../api-reference.md#markers).

## How a marker works

A marker is a callable bound to a project name. When it decorates a function it
stamps a small frozen dataclass of options onto that function under a
project-namespaced attribute. Nothing else happens at decoration time - the
manager reads those attributes later by introspection.

```python
extension_point = ExtensionPoint("kitchen")   # stamps  func.kitchen_spec = ExtensionPointOpts(...)
extension = Extension("kitchen")   # stamps  func.kitchen_impl = ExtensionOpts(...)
```

Because the marker only sets an attribute and returns the function unchanged, a
decorated function is still perfectly callable on its own - handy for testing a
plugin method directly.

## Bare vs called forms

Both markers support `@extension` and `@extension(...)`. This is expressed with
`typing.overload` so a type checker understands both:

```python
@extension                       # bare form
def add_ingredients(self, base): ...

@extension(tryfirst=True)        # called form with options
def prep_step(self, steps): ...
```

## Spec options

`@extension_point` accepts:

| Option | Meaning |
| --- | --- |
| `firstresult` | Stop at the first non-`None` result and return it directly. See [First result](../mechanisms/firstresult.md). |
| `historic` | Remember calls and replay them to plugins registered later. See [Historic hooks](../mechanisms/historic.md). |

A spec cannot be both `historic` and `firstresult`; the manager rejects that
combination when the specs are added.

## Implementation options

`@extension` accepts:

| Option | Meaning |
| --- | --- |
| `tryfirst` | Run earlier than normal implementations. |
| `trylast` | Run later than normal implementations. |
| `wrapper` | This implementation is a generator that wraps the others. See [Wrappers](../mechanisms/wrappers.md). |
| `optional` | Do not error if the host never declared a matching spec. |
| `target` | Bind to a spec whose name differs from the method name. |

## Empty spec bodies

Spec bodies are intentionally empty - a docstring and nothing more. The manager
never calls them; they exist only to declare a name and signature. The type
checkers are told to ignore the "missing return" complaint for the specs module.

```python
@extension_point
def choose_cup(size: str) -> str | None:
    """Pick a cup for the size; the first plugin to answer wins."""
    # no body on purpose
```

## A structural contract with Protocol

The specs module also defines a `typing.Protocol` so a checker can confirm,
structurally, that a plugin's method lines up with the hook it implements - no
base class or registration needed:

```python
@runtime_checkable
class IngredientProvider(Protocol):
    def add_ingredients(self, base: list[str]) -> list[str]: ...
```

This pairs nicely with the runtime validation the manager performs at
registration: the Protocol catches signature drift in the type checker, and the
manager catches it again at run time.
