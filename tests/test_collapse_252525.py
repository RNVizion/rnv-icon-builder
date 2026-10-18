"""RETIRED_DARK_STRAY_GRAY no longer exists in this application. RNV-COLLAPSE-GUARD

Ruled 2026-09-02: RETIRED_DARK_STRAY_GRAY collapses onto APP_CARD. This guard
pins the ruling in both directions: the keys hold the new value, and they
hold it THROUGH the constant.
"""
from __future__ import annotations

import re
from pathlib import Path

from tests.color_values import RETIRED_DARK_STRAY_GRAY

ROOT = Path(__file__).resolve().parent.parent
#: RNV-COLOR-SYNC, #53 A (2026-10-17): named once, in tests/color_values.py,
#: which carries this guard's marker because it quotes the value to forbid it.
OLD_HEX = RETIRED_DARK_STRAY_GRAY
#: RNV-COLOR-SYNC, 2026-10-16: the value the keys were ruled onto is read
#: from CONST, where it was written here as NEW_HEX, its hex code, so a brand
#: move needs no edit here.
CONST = "APP_CARD"
KEYS = ['platform_btn_bg', 'scrollbar_bg', 'list_alt_bg']
EXPECT = {'dark': ['platform_btn_bg', 'scrollbar_bg', 'list_alt_bg'], 'image': ['platform_btn_bg', 'list_alt_bg']}
PALETTE_FILE = "utils/colors.py"


def _palettes():
    from utils.colors import DARK_THEME_COLORS as D, IMAGE_MODE_COLORS as I; P={'dark':D,'image':I}
    return P


def _new_value():
    """The constant the keys were ruled onto, as the value it holds."""
    from utils import colors
    return getattr(colors, CONST)


def test_the_ruled_keys_hold_the_new_value():
    new = _new_value()
    for mode, keys in EXPECT.items():
        palette = _palettes()[mode]
        for key in keys:
            assert palette[key] == new, (
                f"{mode}[{key}] is {palette[key]}, ruled onto {CONST} {new}")


def test_the_old_value_is_gone_from_every_palette():
    for mode, palette in _palettes().items():
        holders = [k for k, v in palette.items() if str(v).lower() == OLD_HEX]
        assert not holders, f"{mode} still holds {OLD_HEX} under {holders}"


def test_the_keys_are_wired_through_the_constant_not_rewritten():
    """Swapping one literal for another passes the value check and defeats
    the point. The constant is what a later substitution changes."""
    src = (ROOT / PALETTE_FILE).read_text(encoding="utf-8-sig")
    for key in KEYS:
        assert re.search(r"'%s':\s+%s\b" % (key, CONST), src), (
            f"{key} is not written as {CONST} in {PALETTE_FILE}")


def test_the_old_value_is_not_written_anywhere_in_source():
    """A sweep for the literal AS A STRING -- quoted. The palette file records
    that each ruled key was RETIRED_DARK_STRAY_GRAY, in a comment beside it, and
    that mention is the provenance, not a use. The first version of this test matched the bare
    text and failed on its own script's comment: use versus mention, again.
    Excludes this guard and the delivery script, which quote the value in
    order to forbid it."""
    strays = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(p in {".git", "build", "dist", ".venv", "__pycache__"} for p in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if "RNV-COLLAPSE-GUARD" in text or "RNV-COLLAPSE-TOOL-DO-NOT-SWEEP" in text:
            continue
        if re.search(r"""['"]%s['"]""" % OLD_HEX, text, re.I):
            strays.append(str(path.relative_to(ROOT)))
    assert not strays, f"{OLD_HEX} is still written as a literal in: {strays}"
