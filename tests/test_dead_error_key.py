"""The orphaned 'error' key stays gone.

It held RETIRED_ERROR_RED in every palette and nothing drew it. An unread wrong value
is still a wrong value waiting for a reader -- and a palette key that exists
is an invitation to use it, which is how a color nobody ruled ends up on
screen.

This app renders no error text at all, so there is nothing to replace it
with. If one is ever needed, take the derived value the family ruled --
lighten(RETIRED_ERROR_RED, -20) for light grounds -- rather than reviving this.
"""

import pytest

from ui import colors
# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that
# are not the application's colors are named once, in tests/color_values.py.
from tests.color_values import RETIRED_ERROR_RED

PALETTES = ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS")


@pytest.mark.parametrize("name", PALETTES)
def test_the_dead_error_key_is_gone(name):
    palette = getattr(colors, name)
    assert "error" not in palette, (
        f"{name} has an 'error' key again. It was deleted as an orphan: "
        f"nothing in the app read it across 968 tests.")


@pytest.mark.parametrize("name", PALETTES)
def test_image_mode_did_not_reintroduce_it_through_the_splat(name):
    """IMAGE_MODE_COLORS is built as {**DARK_THEME_COLORS, ...}, so a key
    added back to DARK reappears here without anyone editing this palette.
    Asserted separately because that is the route a reintroduction would
    take."""
    assert "error" not in getattr(colors, name)


def test_that_check_is_actually_looking():
    """Guard the guard.

    The assertions above pass trivially against an empty dict. If a palette
    ever turns up empty -- a refactor, a rename, an import that silently
    yields the wrong object -- they would report clean while checking
    nothing.
    """
    for name in PALETTES:
        palette = getattr(colors, name)
        assert len(palette) > 40, f"{name} has only {len(palette)} keys"
        assert "window_bg" in palette, f"{name} does not look like a palette"
    planted = {"error": RETIRED_ERROR_RED}
    assert "error" in planted, \
        "the membership check no longer detects a known offender"


def test_no_palette_still_carries_the_value_under_another_name():
    """Deleting the key is not the same as removing the value. If RETIRED_ERROR_RED
    reappears on some other key it is back on screen under a new name, which
    is exactly how a retired color survives a rename sweep."""
    retired = RETIRED_ERROR_RED
    for name in PALETTES:
        offenders = [k for k, v in getattr(colors, name).items()
                     if isinstance(v, str) and v.lower() == retired]
        assert not offenders, f"{name} carries {retired} on {offenders}"
