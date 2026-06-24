"""Tests that each usage example runs and produces its documented result."""

import asyncio

import app_lifecycle
import async_fetch
import cli_app
import fastapi_app
import notification_router
import pytest_plugin
import quickstart
import report_builder
import text_pipeline
import validation_rules
from click.testing import CliRunner
from fastapi.testclient import TestClient


def test_quickstart_collects_both_greetings():
    assert quickstart.run("Ada") == ["Good day, Ada.", "hey Ada!"]


def test_fastapi_app_mounts_plugin_routes():
    client = TestClient(fastapi_app.build_app())
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/hello/Ada").json() == {"message": "hello Ada"}


def test_cli_app_mounts_plugin_commands():
    runner = CliRunner()
    cli = cli_app.build_cli()
    assert runner.invoke(cli, ["greet", "Ada"]).output.strip() == "hello Ada"
    assert runner.invoke(cli, ["version"]).output.strip() == "1.0.0"


def test_pytest_plugin_checker_collects_failures():
    checker = pytest_plugin.build_checker()
    assert checker.errors("") == ["value is empty"]
    assert checker.errors(None) == ["value is None"]
    assert checker.errors("ok") == []


def test_report_builder_orders_sections_and_frames_body():
    report = report_builder.run({"apples": 12, "pears": 7})
    lines = report.splitlines()
    assert lines[0] == "=" * 32 and lines[-1] == "=" * 32  # banner wrapper
    body = report.strip("=").strip()
    assert body.startswith("# Daily Sales Report")  # tryfirst
    assert body.endswith("**Total: 19**")  # trylast


def test_notification_router_picks_first_accepting_channel():
    pm = notification_router.build_plugin_manager()
    assert notification_router.route(pm, "x", urgent=True).startswith("SMS")
    assert notification_router.route(pm, "x", urgent=False).startswith("Email")
    pm.set_blocked("email")
    assert notification_router.route(pm, "x", urgent=False).startswith("Slack")


def test_validation_rules_collect_call_extra_and_unregister():
    pm = validation_rules.build_plugin_manager()
    record = {"name": "", "email": "nope"}
    assert validation_rules.validate(pm, record) == ["name is required", "email looks invalid"]

    def adult_only(record: dict[str, str]) -> str | None:
        return None if record.get("adult") == "yes" else "must be an adult"

    extra = pm.hook.check.call_extra([adult_only], {"record": record})
    assert "must be an adult" in extra

    pm.unregister("email-format")
    assert validation_rules.validate(pm, record) == ["name is required"]


def test_text_pipeline_threads_through_stages():
    assert text_pipeline.run("   hello    wonderful   world   ") == "Hello Wonderful World!"


def test_async_fetch_awaits_every_source():
    headlines = asyncio.run(async_fetch.gather("harbor"))
    assert any(h.startswith("weather[harbor]") for h in headlines)
    assert any(h.startswith("news[harbor]") for h in headlines)
    assert any(h.startswith("static[harbor]") for h in headlines)


def test_app_lifecycle_replays_config_to_late_plugin():
    statuses = app_lifecycle.run()
    assert "database: ok" in statuses
    # The cache plugin loaded after startup but still saw the replayed settings.
    assert "cache: ttl=60" in statuses
