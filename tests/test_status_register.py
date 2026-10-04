"""Every status value in this application is the register's. RNV-STATUS-GUARD

Ruled by Chris on 2026-09-02, reading the STATUS family across the fleet, and
again on 2026-09-03 when the register replaced the family outright.

A status colour is not decoration. It carries MEANING -- success, warning,
error -- and the meaning is the same in every RNV product, which is why the
register owns the value and an application must not have a second opinion.
This guard is the thing that stops the second opinion coming back.

REWRITTEN, NOT PATCHED, on 2026-09-03. Three of the assertions here pinned
#28a745 and #ffc107 by hex and explained at length why those were THE green
and THE amber. Changing the hex inside a docstring that argues for it would
have left the argument standing for a value that lost it: the green collapsed
with Bootstrap's red under deuteranopia, and the amber could not clear a 3:1
fill floor on any light ground. What replaced them, and why, is below.
"""
from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path

from ui import colors

ROOT = Path(__file__).resolve().parent.parent


def _code_only(text: str) -> str:
    """Source with comments and DOCSTRINGS removed -- and nothing else.

    Why this exists: every value these guards forbid is named, in words, in
    the provenance explaining why it was retired. A sweep that cannot tell a
    value being USED from a value being MENTIONED forces the fix to be silence
    about what changed, which is the opposite of what the provenance is for.

    Why it is fussier than it looks: an earlier version dropped every STRING
    token. In Python a colour value IS a string literal -- `X = "#926c89"` --
    so that version removed the uses along with the mentions and the sweep
    could never find anything. It passed on every input, including a file that
    had just put a retired value back. This file's own guard-the-guard is what
    caught it, which is the entire reason for writing guards that check the
    guard can still see.

    So: a STRING token is dropped only when it STARTS a statement -- a
    docstring, or a bare string expression, which is prose either way. A string
    on the right of an assignment, in a dict, or in a call is kept, because
    that is what a value looks like.
    """
    out = []
    # ENCODING behaves like the start of a line for this purpose.
    at_statement_start = True
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.STRING and at_statement_start:
                at_statement_start = False
                continue
            if tok.type in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                            tokenize.DEDENT, tokenize.ENCODING):
                at_statement_start = True
            else:
                at_statement_start = False
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError):
        # Falling back to the raw text can only make a sweep STRICTER, never
        # looser, so it fails safe.
        return text
    return " ".join(out)


def _palettes():
    from ui.colors import (DARK_THEME_COLORS as D, LIGHT_THEME_COLORS as L,
                           IMAGE_MODE_COLORS as I)
    return {"dark": D, "light": L, "image": I}


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


TEXT_FLOOR = 4.5
FILL_FLOOR = 3.0

# #4caf50 was Material's green, held here for the watcher where the register
# published a different one; ruled onto the register's on 2026-09-02. The
# other two are Bootstrap's, retired by the register on 2026-09-03.
STRAYS = {
    "#4caf50": "Material's green, ruled out on 2026-09-02",
    "#28a745": "Bootstrap's green, retired -- it and Bootstrap's red were one "
               "olive under deuteranopia, about 4 apart",
    "#ffc107": "Bootstrap's amber, retired -- 1.63 on #ffffff against a 3:1 "
               "fill floor",
}

# RNV-NAMED-AND-USED, 2026-10-04: the two this application draws. It draws
# one status colour, the folder watcher's label, as text in dark and in
# light. The family's two fills and the warning's two text values were held
# here too; nothing in the application read them, and they went. The
# register holds the family.
REGISTERED = {
    "STATUS_SUCCESS_TEXT": "#ad85a3",
    "STATUS_SUCCESS_TEXT_LIGHT": "#825d79",
}


def test_no_retired_status_value_is_in_any_palette():
    for mode, palette in _palettes().items():
        bad = {k: v for k, v in palette.items()
               if isinstance(v, str) and v.lower() in STRAYS}
        assert not bad, f"{mode} still holds a retired value: {bad}"


def test_the_status_values_are_the_register_s():
    """Not "some purple" -- THE one. An application that picks its own status
    colour has an opinion about what success means, which is the register's
    job. Pinned by value: a test asserting only that these differ from each
    other would pass on two wrong colours."""
    for name, value in REGISTERED.items():
        assert getattr(colors, name) == value, name


# RNV-NAMED-AND-USED, 2026-10-04: a test stood here on the arithmetic of the
# two fills -- that each clears 3:1 on both grounds and 4.5:1 on neither.
# This application draws no fill and no longer carries them; the
# arithmetic is the register's, where the fills are.


def test_the_text_variants_carry_text_on_their_own_ground():
    """RNV-STATUS-LIGHT-FLOOR -- READ BEFORE ADDING GROUNDS.

    The light pair is checked on #ffffff and #f5f5f5 only. They do NOT reach
    the lighter registered rungs: on APP hover-light #eeeeee they read 4.25
    and 4.24, on GOLD_TEXT_GROUND_FLOOR #e8e8e8 4.02, on pressed-light
    #e0e0e0 3.74. The cause is in the register's own rule, which walks the
    light variants against #f5f5f5 as "the worst light ground" -- rev 27 put
    three rungs below it. Both were walked to the FIRST step that clears, so
    there is no margin.

    This is an open question with the brand chat, not a loosened test. If the
    register re-walks against #e8e8e8 the answers are #825d79 and #8e5e2b,
    each moving less than its own 8.40 threshold; the fix here is to add the
    darker rungs back and update REGISTERED.
    """
    for name in ("STATUS_SUCCESS_TEXT",):
        for ground in ("#1a1a1a", "#2a2a2a"):
            ratio = _contrast(getattr(colors, name), ground)
            assert ratio >= TEXT_FLOOR, f"{name} on {ground} = {ratio:.4f}"
    for name in ("STATUS_SUCCESS_TEXT_LIGHT",):
        # Restored at rev 31: the re-walked pair reaches all four rungs.
        # #e0e0e0 is deliberately absent -- BRAND_DARK_GOLD_DEEP fails
        # there too, so it is the boundary for every brand text family.
        for ground in ("#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"):
            ratio = _contrast(getattr(colors, name), ground)
            assert ratio >= TEXT_FLOOR, f"{name} on {ground} = {ratio:.4f}"


# RNV-NAMED-AND-USED, 2026-10-04: a test stood here holding
# STATUS_ACTIVE_COLOR as an alias of the success text. Nothing painted from
# the alias after 2026-09-03 -- the label reads status_active, per mode, as
# the next three tests hold -- and it went.


def test_status_active_resolves_per_mode():
    """The finding this pass fixed.

    ui/settings_dialog.py painted the watch label with

        color: {STATUS_ACTIVE_COLOR}

    -- TEXT, from a module-level constant, in a dialog that runs in dark,
    light and image mode. No single value is legal on all three grounds: the
    dark text variant reads 5.52 on #1a1a1a and 3.15 on #ffffff. Same shape as
    the CONTRAST_ON_DARK finding: the answer is resolving per mode, not a
    better constant.
    """
    palettes = _palettes()
    for mode in ("dark", "light", "image"):
        assert "status_active" in palettes[mode], mode
    assert palettes["dark"]["status_active"] == colors.STATUS_SUCCESS_TEXT
    assert palettes["light"]["status_active"] == colors.STATUS_SUCCESS_TEXT_LIGHT
    # image inherits dark's through **DARK_THEME_COLORS, which is correct:
    # image mode is dark with transparency, and its grounds are dark.
    assert palettes["image"]["status_active"] == colors.STATUS_SUCCESS_TEXT


def test_the_watch_label_reads_the_theme_rather_than_a_constant():
    # RNV-WATCH-LABEL 2026-09-28: and the dialog's own mode. This pinned
    # get_theme_colors() with no mode -- the default palette, dark's -- so
    # a dialog in light drew dark's value. The label as drawn in each mode
    # is held by tests/test_watch_label_follows_a_switch.py.
    src = (ROOT / "ui" / "settings_dialog.py").read_text(encoding="utf-8-sig")
    assert "get_theme_colors(is_dark=self._current_theme_is_dark)['status_active']" in src
    assert not re.search(r"get_theme_colors\s*\(\s*\)\s*\[\s*'status_active'", _code_only(src)), (
        "the watch label asks for the default palette again")
    assert not re.search(r"\bSTATUS_ACTIVE_COLOR\b", _code_only(src)), (
        "the mode-blind constant is back in the dialog")


def test_status_active_is_legal_in_every_mode_it_is_painted_in():
    """The end-to-end assertion. A per-mode key that resolves to an illegal
    value in one mode has moved the bug rather than fixed it."""
    grounds = {"dark": "#1a1a1a", "light": "#f5f5f5", "image": "#1a1a1a"}
    for mode, ground in grounds.items():
        value = _palettes()[mode]["status_active"]
        ratio = _contrast(value, ground)
        assert ratio >= TEXT_FLOOR, f"{mode}: {value} on {ground} = {ratio:.4f}"


# RNV-NAMED-AND-USED, 2026-10-04: a test stood here holding the palettes'
# success and warning keys to their constants. Nothing read the keys, so
# they went, and the constants with them.


def test_the_family_matches_the_rest_of_the_fleet():
    """The whole point of the ruling. Written as the literals the other
    applications hold, so this fails if either side drifts rather than only
    if this one does."""
    assert colors.STATUS_SUCCESS_TEXT == "#ad85a3"
    assert colors.STATUS_SUCCESS_TEXT_LIGHT == "#825d79"


SWEPT = ("ui/colors.py", "ui/settings_dialog.py")
# the success text: a value ui/colors.py holds. It was the success fill's
# until RNV-NAMED-AND-USED, 2026-10-04, when the fill went.
LIVE_VALUE = "#ad85a3"


def test_this_guard_can_still_see():
    """Guard the guard, and it has already earned its place.

    _code_only exists so provenance can name a retired value without failing
    the sweep that forbids it. An earlier version dropped EVERY string token,
    which in Python also drops the values -- so a sweep for a retired hex
    could never find one and passed on every input, including a file that had
    just put one back. This assertion is what caught that.
    """
    src = (ROOT / SWEPT[0]).read_text(encoding="utf-8-sig")
    code = _code_only(src)
    assert len(code) > 2000, "the tokeniser returned almost nothing"
    assert LIVE_VALUE in code, (
        f"the code-only sweep cannot see {LIVE_VALUE}, which is definitely a "
        f"value in {SWEPT[0]}. Any sweep built on it would be vacuous.")
