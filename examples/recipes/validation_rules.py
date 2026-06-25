"""A pluggable validation engine where each plugin contributes a rule.

Shows:

- a collecting hook (`check`) that gathers problems from every rule (None = OK);
- `call_extra` to run a one-off rule for a single call without registering it;
- `unregister` to drop a rule at runtime.

Run: python examples/validation_rules.py
"""
# mypy: disable-error-code="empty-body"
# pyright: reportReturnType=false

from pluginkit import HookimplMarker, HookspecMarker, PluginManager

hookspec = HookspecMarker("rules")
hookimpl = HookimplMarker("rules")

Record = dict[str, str]


class Specs:
    """The validation host's contract."""

    @staticmethod
    @hookspec
    def check(record: Record) -> str | None:
        """Return a problem description, or None if the record passes this rule."""


class NameRequiredRule:
    """Requires a non-empty name."""

    @hookimpl
    def check(self, record: Record) -> str | None:
        """Flag a missing or empty name."""
        return None if record.get("name") else "name is required"


class EmailFormatRule:
    """Requires a plausible email address."""

    @hookimpl
    def check(self, record: Record) -> str | None:
        """Flag an email without an '@'."""
        email = record.get("email", "")
        return None if "@" in email else "email looks invalid"


def build_plugin_manager() -> PluginManager:
    """Create a manager with the standard rules registered."""
    pm = PluginManager("rules")
    pm.add_hookspecs(Specs)
    pm.register(NameRequiredRule(), name="name-required")
    pm.register(EmailFormatRule(), name="email-format")
    return pm


def validate(pm: PluginManager, record: Record) -> list[str]:
    """Return all problems found in a record."""
    problems = pm.caller(Specs.check)(record=record)
    return [problem for problem in problems if problem is not None]


def main() -> None:
    """Validate a record, add a one-off rule, then drop a rule."""
    pm = build_plugin_manager()
    record = {"name": "", "email": "nope"}
    print("baseline problems:", validate(pm, record))

    # A one-off rule, applied for a single call via call_extra.
    def adult_only(record: Record) -> str | None:
        """Flag records that are not marked as adult."""
        return None if record.get("adult") == "yes" else "must be an adult"

    extra_problems = pm.caller(Specs.check).call_extra([adult_only], {"record": record})
    print("with one-off rule:", extra_problems)

    # Relax validation at runtime by dropping the email rule.
    pm.unregister("email-format")
    print("after dropping email rule:", validate(pm, record))


if __name__ == "__main__":
    main()
