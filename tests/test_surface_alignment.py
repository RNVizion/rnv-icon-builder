"""
Panel and input surfaces, and the edges that have to survive aligning them.

RULED 2026-08-27. Light panels are #f5f5f5 in every app; dark input fields are
#1a1a1a, which is what three of the five already used.

WHAT THE ALIGNMENT ACTUALLY DID TO THE EDGES, measured from the adjacency map
rather than assumed:

  LIGHT   panel and card were the same colour here, so a card had no edge
          against the panel it sat on. Moving the panel to #f5f5f5 CREATES
          that edge.

  DARK    the input field was the same colour as the card, so a field sitting
          on a card had no edge either. Moving it to #1a1a1a creates one --
          and makes it equal to the panel, which is how the three apps that
          already used #1a1a1a have always drawn it: the input border is what
          separates a field from the panel, not a fill difference.

That second one is the reason these tests exist. The alignment trades one
missing edge for another arrangement, and the arrangement only works while the
input keeps a border that differs from both. That is asserted below.

IMAGE MODE IS DELIBERATELY UNTOUCHED. It was not part of the three-against-two
comparison this ruling came from, and in one of these two apps its surfaces are
rgba strings rather than flat hex.
"""
from __future__ import annotations

import pytest

from ui.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,
                          LIGHT_THEME_COLORS as LIGHT)

FLAT = {"DARK": DARK, "LIGHT": LIGHT}


def _hex(value) -> bool:
    return isinstance(value, str) and value.startswith("#") and len(value) == 7


def test_both_flat_palettes_carry_the_surface_keys():
    """Guard the guard: every test below reads these."""
    for name, theme in FLAT.items():
        for key in ("window_bg", "panel_bg", "card_bg", "input_bg",
                    "input_border_key_present"):
            if key == "input_border_key_present":
                assert any(k in theme for k in ("input_border", "border_color",
                                                "border_default")), (
                    f"{name} has no border key for the input")
                continue
            assert key in theme, f"{name} has no {key}"
            assert _hex(theme[key]), f"{name} {key} is {theme[key]!r}, not flat hex"


def test_the_light_panel_is_the_agreed_surface():
    assert LIGHT["panel_bg"] == "#f5f5f5", (
        f"light panel is {LIGHT['panel_bg']}, not the #f5f5f5 all five apps use")


def test_the_dark_input_is_the_agreed_surface():
    assert DARK["input_bg"] == "#1a1a1a", (
        f"dark input is {DARK['input_bg']}, not the #1a1a1a all five apps use")


def test_a_card_still_has_an_edge_against_its_panel():
    """This edge did not exist before the alignment in either app -- panel and
    card were the same colour. It exists now and must not be merged away."""
    for name, theme in FLAT.items():
        assert theme["card_bg"] != theme["panel_bg"], (
            f"{name}: card {theme['card_bg']} is the panel colour again, so a "
            f"card sitting on the panel has no edge")


def test_the_input_is_separated_from_the_surface_it_sits_on():
    """Dark deliberately draws the field in the panel colour and relies on the
    border. That only works while the border differs from both."""
    for name, theme in FLAT.items():
        border = (theme.get("input_border") or theme.get("border_default")
                  or theme["border_color"])
        assert border != theme["input_bg"], (
            f"{name}: the input border is the same colour as its fill")
        if theme["input_bg"] == theme["panel_bg"]:
            assert border != theme["panel_bg"], (
                f"{name}: the input fill matches the panel AND the border "
                f"matches the panel -- the field has no visible extent")


def test_image_mode_was_left_alone():
    """Recorded rather than trusted: if image mode is aligned later, this test
    is the thing that has to be deleted on purpose."""
    assert "input_bg" in IMAGE
    assert IMAGE["input_bg"] != "#1a1a1a", (
        "image mode now uses the dark input surface. That was outside the "
        "2026-08-27 ruling -- if it is intended, delete this test and say so.")
