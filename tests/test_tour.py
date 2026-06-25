"""Tests asserting each from-scratch demo behaves as documented."""

from pluginkit_tour import (
    demo_01_direct,
    demo_02_firstresult,
    demo_03_ordering,
    demo_04_wrapper,
    demo_05_historic,
    demo_06_entrypoints,
)
from pluginkit_tour.points import IngredientProvider


def test_direct_collects_from_every_plugin():
    smoothie = demo_01_direct.make_smoothie()
    assert smoothie[:2] == ["banana", "milk"]
    assert {"blueberry", "strawberry", "spinach", "kale"} <= set(smoothie)


def test_direct_plugins_satisfy_protocol():
    # The runtime_checkable Protocol confirms the structural contract holds.
    assert isinstance(demo_01_direct.BerryPlugin(), IngredientProvider)
    assert isinstance(demo_01_direct.GreensPlugin(), IngredientProvider)


def test_firstresult_specific_plugins_win():
    assert demo_02_firstresult.choose_cup("small") == "8oz paper cup"
    assert demo_02_firstresult.choose_cup("large") == "20oz tumbler"


def test_firstresult_falls_back_when_specific_plugins_abstain():
    assert demo_02_firstresult.choose_cup("medium") == "16oz default cup"


def test_ordering_respects_tryfirst_and_trylast():
    assert demo_03_ordering.prep_steps() == ["wash produce", "chop fruit", "add garnish"]


def test_wrapper_decorates_inner_result():
    assert demo_04_wrapper.blend(["mango", "ice"]) == "mango + ice blend topped with foam"


def test_historic_replays_to_late_plugin():
    early, late, callback_log = demo_05_historic.run()
    assert early.greeting == "Early staff ready at Main Street"
    assert late.greeting == "Late staff caught up at Main Street"
    assert callback_log == [
        "Early staff ready at Main Street",
        "Late staff caught up at Main Street",
    ]


def test_entrypoints_discovers_external_plugins():
    pm = demo_06_entrypoints.build_plugin_manager()
    assert {"honey", "extra"} <= set(pm.plugin_names())
    smoothie = demo_06_entrypoints.make_smoothie()
    assert {"honey", "oats", "chia seeds", "almond butter"} <= set(smoothie)
