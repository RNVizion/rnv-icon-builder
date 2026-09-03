"""Every status value in this application is the register's. RNV-STATUS-GUARD

Ruled by Chris on 2026-09-02, reading the STATUS family across the fleet.
Three values disagreed with the register; all three collapse.

A status colour is not decoration. It carries MEANING -- success, warning,
error -- and the meaning is the same in every RNV product, which is why the
register owns the value and an application must not have a second opinion.
This guard is the thing that stops the second opinion coming back.
"""
from __future__ import annotations

import re
from pathlib import Path

from ui import colors

ROOT = Path(__file__).resolve().parent.parent


def _palettes():
    from ui.colors import DARK_THEME_COLORS as D, LIGHT_THEME_COLORS as L, IMAGE_MODE_COLORS as I; P={'dark':D,'light':L,'image':I}
    return P


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hexv):
    h = hexv.lstrip("#")
    t = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return 0.2126 * _lin(t[0]) + 0.7152 * _lin(t[1]) + 0.0722 * _lin(t[2])


def _contrast(a, b):
    la, lb = _luminance(a), _luminance(b)
    hi, lo = (la, lb) if la >= lb else (lb, la)
    return (hi + 0.05) / (lo + 0.05)


STRAYS = {"#4caf50"}


def test_the_stray_green_is_gone_from_every_palette():
    for mode, palette in _palettes().items():
        bad = {k: v for k, v in palette.items()
               if isinstance(v, str) and v.lower() in STRAYS}
        assert not bad, f"{mode} still holds the retired green: {bad}"


def test_the_status_values_are_the_register_s():
    """Not "some green" -- THE green. An app that picks its own status colour
    has an opinion about what success means, which is the register's job."""
    assert colors.STATUS_SUCCESS == "#28a745"
    assert colors.STATUS_WARNING == "#ffc107"


def test_the_watcher_green_is_an_alias_not_a_copy():
    """"Running" is not "succeeded", and the register has no name for the
    first. Holding it as an alias keeps the borrowing visible: if
    status-active is ever registered, one line moves. A copied literal would
    hide that this app is borrowing at all."""
    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")
    assert "STATUS_ACTIVE_COLOR: Final[str] = STATUS_SUCCESS" in src
    assert colors.STATUS_ACTIVE_COLOR == colors.STATUS_SUCCESS


def test_the_palettes_are_wired_through_the_constants_not_rewritten():
    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")
    for key, const in (("success", "STATUS_SUCCESS"), ("warning", "STATUS_WARNING")):
        found = len(re.findall(r"'%s':\s+%s\b" % (key, const), src))
        assert found == 2, f"{key} is wired through {const} in {found} palettes, not 2"


def test_the_green_matches_the_picker():
    """The whole point of the ruling. Written as the literal the picker holds
    so this fails if either app drifts, not merely if this one does."""
    assert colors.STATUS_SUCCESS == "#28a745", (
        "rnv-color-picker holds #28a745 for the same role")
