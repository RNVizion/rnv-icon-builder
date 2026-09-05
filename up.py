#!/usr/bin/env python3
"""
RNV-STATUS-TOOL-DO-NOT-SWEEP

Move rnv-icon-builder onto the RNV status family, and give the watcher's
status label a colour that knows which mode it is in.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file


WHY

The register replaced Bootstrap's status colours on 2026-09-03. The amber read
1.63 on #ffffff and 1.49 on #f5f5f5 against a 3:1 fill floor; success and error
sat about 4 apart under deuteranopia, one olive. The RNV family leaves the
red-green axis entirely.

    success  #28a745  ->  #926c89      warning  #ffc107  ->  #a2703c

and publishes six TEXT variants, because nothing in the fill band can carry
text: a value that works as a fill on a dark AND a light ground sits at
L* 48-59 by arithmetic, and a mid-tone reaches 4.5:1 on neither side.

    success-text  #ad85a3    success-text-light  #825d79
    warning-text  #bc8752    warning-text-light  #8e5e2b

This application carries no error value, so the red is not in its scope.


THE FINDING: STATUS_ACTIVE_COLOR CANNOT BE A CONSTANT

    STATUS_ACTIVE_COLOR: Final[str] = STATUS_SUCCESS

is painted in exactly one place:

    ui/settings_dialog.py
        self.watch_status_label.setStyleSheet(f"color: {STATUS_ACTIVE_COLOR};")

That is TEXT, in a dialog that runs in dark, light and image mode -- and a
module-level constant does not know which. One value cannot be legal on all
three grounds: the dark text variant #ad85a3 reads 5.52 on #1a1a1a and 3.15 on
#ffffff. This is the same shape as the CONTRAST_ON_DARK finding earlier in this
programme: the answer is not a better value, it is resolving per mode.

So `status_active` becomes a PALETTE KEY, resolved by get_theme_colors() like
every other colour this dialog paints, and the call site reads it from the
theme it is already holding. get_theme_colors is imported in that file
already; the change at the call site is one line.

THE ALIAS SURVIVES, IN THE PLACE THAT CAN STILL HOLD IT. The existing guard
records why STATUS_ACTIVE_COLOR is an alias rather than a copy -- "running" is
not "succeeded", the register has no name for the first, and holding it as an
alias keeps the borrowing visible. That reasoning is untouched and is now
carried by the palette entries, which point at the text variants rather than
at a literal.


THE TWO PALETTE KEYS ARE DEAD, AND STILL GET THE NEW VALUES

'success' and 'warning' are looked up nowhere in this application -- zero
elements in the fleet colour tree, no consumer outside the palettes. They are
on the standing dead-key list (3 in this repository) and this pass does not
wire them to anything; that is a separate decision about whether they should
exist at all. They still move to the registered values, because a palette that
carries a colour should carry the right one, and leaving two Bootstrap values
in a file whose guard says every status value is the register's would make the
guard false.


LIGHT WAS ALREADY WRONG

Both palettes held the same #28a745 and #ffc107. As text on this app's light
dialog ground #f5f5f5 that is 2.87 and 1.50 -- illegal, and invisible because
the keys are unused. The light palette now carries the light siblings, so if
either key is ever wired up it is legal on arrival.


THE BOUNDARY THIS PASS WAITED ON, NOW CLOSED

RNV-STATUS-LIGHT-FLOOR was open while these scripts were written. The three
LIGHT text variants had been walked to clear 4.5:1 on #f5f5f5, which the
register's rule called "the worst light ground". It was not: rev 27 had put
APP hover-light #eeeeee, GOLD_TEXT_GROUND_FLOOR #e8e8e8 and pressed-light
#e0e0e0 below it, and because the rule takes the FIRST step that clears, each
value stopped at 4.52 with no margin and all three failed one rung down.

Register rev 31 (2026-09-05) re-walked them against #e8e8e8:

    success-text-light  #8a6581 -> #825d79
    warning-text-light  #976633 -> #8e5e2b
    error-text-light    #b84e58 -> #ae4650

AND THE DECIDING REASON IS NOT THE ONE THIS CHAT GAVE. The argument here was
from cost -- a small move, the same three colours. True, and not sufficient,
because #e0e0e0 would have been affordable too. The register's reason is
better: #e8e8e8 is where BRAND_DARK_GOLD_DEEP already stops.

    on #e8e8e8   gold-deep 4.53   the three 4.52 / 4.53 / 4.52   pass
    on #e0e0e0   gold-deep 4.21   the three 4.20 / 4.20 / 4.20   fail

ONE boundary for every brand text family instead of two. Walking to #e0e0e0
would have covered the pressed plate and left an author having to remember
which family they were in to know where text stops.

So the boundary tests are not narrowed. They run the full four rungs, and they
pass -- which is the point of the re-walk being visible in the test rather than
only in the register.


ONE THING IS STILL OPEN, AND IT IS THE OTHER SIDE OF THE SAME FAULT

The three DARK text variants were derived against APP card #2a2a2a. Rev 29
then registered panel-hover #3a3a3a, which is LIGHTER and therefore worse for
light text on a dark ground. All three fail there:

    success-text 3.61   warning-text 3.64   error-text 3.58   floor 4.5
    BRAND_GOLD clears every dark surface at 6.15

Same two-boundary asymmetry, other side. The register left it open rather than
fixing it in rev 31, because the fix is not symmetric: on light the worst
surface is a PRESSED plate and ruling that running text is not carried on a
transient state is defensible, while on dark the worst is a HOVER, which a
label sits under for as long as a cursor rests there. The walk would cost
CIEDE2000 6.53-7.06 -- inside the 8.40 bar, but more than double the light
move, and it lightens all three toward the ink ramp.

WHAT THIS CHAT CAN ADD: the fleet's exposure today is ZERO. The element sweep
across all five applications resolves four status elements, all of them plain
dialog labels painted with an inline `color:` on a dialog ground; not one
status key is painted in a selector carrying :hover. So this is a register
question about where the boundary should be, not a live defect in these apps
-- and if a status label is ever put on a hover row, the dark-ground
assertions in the guard are where it should surface.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-icon-builder"
DESCRIPTION = "move onto the RNV status family; make status_active mode-aware"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "RNV-STATUS-FAMILY"
# The existing status guard IS what this pass rewrites, so it is the
# guard rather than a second file beside it. One place to look.
GUARD = "tests/test_status_register.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "settings_dialog.py"}

SUITES = [
    ("pytest tests/",
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ("unittest suite",
     [sys.executable, "-m", "unittest", "test_rnv_icon_builder"]),
]

# role -> (fill, text on a dark ground, text on a light ground)
FAMILY = {
    "SUCCESS": ("#926c89", "#ad85a3", "#825d79"),
    "WARNING": ("#a2703c", "#bc8752", "#8e5e2b"),
}
RETIRED = ("#28a745", "#ffc107", "#4caf50")


GUARD_SOURCE = r'''"""Every status value in this application is the register's. RNV-STATUS-GUARD

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

REGISTERED = {
    "STATUS_SUCCESS": "#926c89",
    "STATUS_WARNING": "#a2703c",
    "STATUS_SUCCESS_TEXT": "#ad85a3",
    "STATUS_WARNING_TEXT": "#bc8752",
    "STATUS_SUCCESS_TEXT_LIGHT": "#825d79",
    "STATUS_WARNING_TEXT_LIGHT": "#8e5e2b",
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
    other would pass on six wrong colours."""
    for name, value in REGISTERED.items():
        assert getattr(colors, name) == value, name


def test_a_fill_cannot_carry_text_and_that_is_the_point():
    """Why there are six values and not two.

    STATUS_SUCCESS and STATUS_WARNING are fills. Every fill in this family
    sits at L* 48-59, which is exactly what lets ONE value clear 3:1 on a dark
    AND a light ground -- and a mid-tone reaches 4.5:1 on neither. If either
    ever clears the text floor, the register has moved it out of the band and
    somebody needs to know rather than quietly benefiting.
    """
    for name in ("STATUS_SUCCESS", "STATUS_WARNING"):
        value = getattr(colors, name)
        for ground in ("#1a1a1a", "#2a2a2a", "#f5f5f5", "#ffffff"):
            assert _contrast(value, ground) >= FILL_FLOOR, f"{name} {ground}"
            assert _contrast(value, ground) < TEXT_FLOOR, (
                f"{name} now clears the text floor on {ground}. Do not relax "
                f"this -- find out whether the register moved it.")


def test_the_text_variants_carry_text_on_their_own_ground():
    """RNV-STATUS-LIGHT-FLOOR, closed 2026-09-05 at register rev 31.

    The light pair was briefly checked on #ffffff and #f5f5f5 only. It did not
    reach the registered rungs below: walked against #f5f5f5 as "the worst
    light ground" and taken at the first step that cleared, both stopped at
    4.52 with no margin, and read 4.25 on APP hover-light #eeeeee and 4.02 on
    GOLD_TEXT_GROUND_FLOOR #e8e8e8.

    The register re-walked them against #e8e8e8, and the reason is not the
    size of the move. It is that #e8e8e8 is where BRAND_DARK_GOLD_DEEP already
    stops -- gold-deep 4.53 there and 4.21 on #e0e0e0, the re-walked three
    4.52 and 4.20. ONE boundary for every brand text family instead of two.
    Below #e8e8e8, no brand text of any family.

    THE DARK PAIR HAS THE SAME FAULT AND IT IS STILL OPEN. Both were derived
    against APP card #2a2a2a; rev 29 then registered panel-hover #3a3a3a,
    which is LIGHTER and therefore worse for light text. They read 3.61 and
    3.64 there against a 4.5 floor, while BRAND_GOLD clears every dark surface
    at 6.15 -- the same two-boundary asymmetry, other side. Nothing in this
    application paints status text on a hover plate today (the sweep resolves
    no status element with :hover in any of the five), so the dark grounds
    below are the ones this app actually uses. If a status label is ever put
    on a hover row, this test is where the shortfall should surface.
    """
    for name in ("STATUS_SUCCESS_TEXT", "STATUS_WARNING_TEXT"):
        for ground in ("#1a1a1a", "#2a2a2a"):
            ratio = _contrast(getattr(colors, name), ground)
            assert ratio >= TEXT_FLOOR, f"{name} on {ground} = {ratio:.4f}"
    for name in ("STATUS_SUCCESS_TEXT_LIGHT", "STATUS_WARNING_TEXT_LIGHT"):
        for ground in ("#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"):
            ratio = _contrast(getattr(colors, name), ground)
            assert ratio >= TEXT_FLOOR, f"{name} on {ground} = {ratio:.4f}"


def test_the_watcher_green_is_an_alias_not_a_copy():
    """"Running" is not "succeeded", and the register has no name for the
    first. Holding it as an alias keeps the borrowing visible: if status-active
    is ever registered, one line moves. A copied literal would hide that this
    app is borrowing at all.

    Unchanged in intent since 2026-09-02. What changed is that the alias is no
    longer what gets PAINTED -- see the next test.
    """
    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")
    assert "STATUS_ACTIVE_COLOR: Final[str] = STATUS_SUCCESS_TEXT" in src
    assert colors.STATUS_ACTIVE_COLOR == colors.STATUS_SUCCESS_TEXT
    assert colors.STATUS_ACTIVE_COLOR != colors.STATUS_SUCCESS, (
        "the alias points at the FILL again. It is painted with `color:` and "
        "the fill reads 3.91 on BRAND_BLACK against a 4.5 text floor -- it was "
        "safe under Bootstrap only because that green happened to be light "
        "enough to double as text.")


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
    src = (ROOT / "ui" / "settings_dialog.py").read_text(encoding="utf-8-sig")
    assert "get_theme_colors()['status_active']" in src
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


def test_the_palettes_are_wired_through_the_constants_not_rewritten():
    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")
    for key, const in (("success", "STATUS_SUCCESS"),
                       ("warning", "STATUS_WARNING")):
        found = len(re.findall(r"'%s':\s+%s\b" % (key, const), src))
        assert found == 2, (
            f"{key} is wired through {const} in {found} palettes, not 2")


def test_the_family_matches_the_rest_of_the_fleet():
    """The whole point of the ruling. Written as the literals the other
    applications hold, so this fails if either side drifts rather than only
    if this one does."""
    assert colors.STATUS_SUCCESS == "#926c89"
    assert colors.STATUS_WARNING == "#a2703c"
    assert colors.STATUS_SUCCESS_TEXT == "#ad85a3"


SWEPT = ("ui/colors.py", "ui/settings_dialog.py")
LIVE_VALUE = "#926c89"


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
'''

NEW_CONSTANTS = r'''STATUS_SUCCESS: Final[str] = "#926c89"
"""MIRRORS the register's STATUS["success"]. A FILL.

RNV-STATUS-FAMILY (2026-09-03): was #28a745, Bootstrap's green. Retired
because it and Bootstrap's red collapsed to one olive under deuteranopia at
about 4 apart -- success and error are the two most consequential colours in
an interface, and roughly 8% of men could not tell them apart.

It is a FILL and cannot carry text: 3.92 on #1a1a1a, 3.23 on #2a2a2a, above
the 3:1 fill floor and below the 4.5:1 text floor. That is not a shortcoming,
it is the fill band -- a value that works on a dark AND a light ground sits at
L* 48-59 by arithmetic, and a mid-tone reaches 4.5 on neither side.

RNV-STATUS-REGISTER (2026-09-02): both palettes already held this value,
written out rather than named. Named here so it has one home. Defined above
the palettes because they consume it.
"""

STATUS_WARNING: Final[str] = "#a2703c"
"""MIRRORS the register's STATUS["warning"]. A FILL.

RNV-STATUS-FAMILY (2026-09-03): was #ffc107, retired on arithmetic rather
than taste -- it read 1.63 on #ffffff and 1.49 on #f5f5f5 against a 3:1 fill
floor, so it could not legally carry a boundary on a light ground at all.
"""

STATUS_SUCCESS_TEXT: Final[str] = "#ad85a3"
STATUS_WARNING_TEXT: Final[str] = "#bc8752"
"""MIRROR the register's STATUS["success-text"] and ["warning-text"].
TEXT on a dark ground: 4.55 and 4.60 on APP card #2a2a2a.

REGISTERED, not derived. The register's rule -- hold hue and chroma, move
lightness only, take the first step that clears 4.5 on the worst ground -- is
published as PROVENANCE so the choice is auditable. It is not re-run here. A
rule held live becomes an edit anyone can make, and retuning it would silently
change what a warning looks like in five applications.
"""

STATUS_SUCCESS_TEXT_LIGHT: Final[str] = "#825d79"
STATUS_WARNING_TEXT_LIGHT: Final[str] = "#8e5e2b"
"""MIRROR the register's STATUS["*-text-light"]. TEXT on a light ground:
4.52 on #f5f5f5, this application's light dialog background.

RNV-STATUS-LIGHT-FLOOR, CLOSED 2026-09-05 at register rev 31. The three
light text variants were first walked against #f5f5f5 as "the worst light
ground". It was not the worst: rev 27 had put APP hover-light #eeeeee,
GOLD_TEXT_GROUND_FLOOR #e8e8e8 and pressed-light #e0e0e0 below it, and each
value was taken at the FIRST step that cleared -- 4.52 -- so none had margin
and one rung down they failed together.

They were re-walked against #e8e8e8, and the deciding reason is not the small
size of the move. It is that #e8e8e8 is where BRAND_DARK_GOLD_DEEP already
stops:

    on #e8e8e8   gold-deep 4.53   the three 4.52 / 4.53 / 4.52   all pass
    on #e0e0e0   gold-deep 4.21   the three 4.20 / 4.20 / 4.20   all fail

ONE boundary for every brand text family rather than two. Walking to #e0e0e0
was affordable and would have covered the pressed plate, at the cost of an
author having to remember which family they were in to know where text stops.
Below #e8e8e8, no brand text of any family.

WHY THIS APPLICATION HAS THEM AT ALL. Both palettes previously held the same
#28a745 and #ffc107. As text on #f5f5f5 that is 2.87 and 1.50 -- illegal, and
invisible only because the two keys are unused. Light now carries its own
siblings, so the keys are legal on arrival if they are ever wired up.
"""
'''


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
    import io
    import tokenize
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


def edits(tree) -> None:
    # --- 1. the constant block. Anchored on the first and last line of the
    # pair as they stand, so a moved file fails here rather than composing a
    # wrong replacement out of anchors that still happen to match.
    src = tree.read("ui/colors.py")
    start_anchor = 'STATUS_SUCCESS: Final[str] = "#28a745"'
    end_anchor = ('STATUS_WARNING: Final[str] = "#ffc107"\n'
                  '"""MIRRORS the register\'s STATUS["warning"]. '
                  'Value unchanged."""\n')
    if src.count(start_anchor) != 1 or end_anchor not in src:
        raise SystemExit("ui/colors.py: the STATUS_SUCCESS / STATUS_WARNING "
                         "block is not where this script expects it")
    start = src.index(start_anchor)
    end = src.index(end_anchor) + len(end_anchor)
    tree.write("ui/colors.py", src[:start] + NEW_CONSTANTS + src[end:])

    # --- 2. the dark palette. These two keys are dead -- zero elements in the
    # fleet colour tree -- and are not wired to anything by this pass. They
    # still move, because a palette that carries a colour should carry the
    # right one, and this file's own guard says every status value here is the
    # register's.
    tree.sub("ui/colors.py",
             "    # Success/Warning/Error\n"
             "    'success': STATUS_SUCCESS,\n"
             "    'warning': STATUS_WARNING,\n"
             "}\n\n\n# ==================== Light Theme Colors",
             "    # Success/Warning/Error\n"
             "    # RNV-STATUS-FAMILY: the fills, unwired. Both keys are looked\n"
             "    # up nowhere in this application and are on the dead-key list;\n"
             "    # whether they should exist is a separate question. If either\n"
             "    # is ever painted as TEXT it must take the _TEXT variant\n"
             "    # instead -- a fill sits at L* 48-59 and cannot reach 4.5:1.\n"
             "    'success': STATUS_SUCCESS,\n"
             "    'warning': STATUS_WARNING,\n"
             "    # RNV-STATUS-FAMILY: the watcher's label is TEXT, and a module\n"
             "    # constant cannot know which mode it is being painted in.\n"
             "    'status_active': STATUS_SUCCESS_TEXT,\n"
             "}\n\n\n# ==================== Light Theme Colors", 1)

    # --- 3. the light palette. It held the DARK values for both keys, which as
    # text on #f5f5f5 read 2.87 and 1.50.
    tree.sub("ui/colors.py",
             "    # Success/Warning/Error\n"
             "    'success': STATUS_SUCCESS,\n"
             "    'warning': STATUS_WARNING,\n"
             "}\n\n\n# ==================== Image Mode Colors",
             "    # Success/Warning/Error\n"
             "    # RNV-STATUS-FAMILY: light's own siblings. This palette held\n"
             "    # the dark values, which as text on #f5f5f5 read 2.87 and 1.50.\n"
             "    'success': STATUS_SUCCESS,\n"
             "    'warning': STATUS_WARNING,\n"
             "    'status_active': STATUS_SUCCESS_TEXT_LIGHT,\n"
             "}\n\n\n# ==================== Image Mode Colors", 1)

    # --- 4. STATUS_ACTIVE_COLOR. Two things change: what it points AT, and
    # whether it is what gets painted.
    #
    # It aliased STATUS_SUCCESS -- a FILL -- and the register ruled on
    # 2026-09-04 that an active label aliases success-text, not success. The
    # alias was safe only by accident: Bootstrap's green happened to be light
    # enough to double as text at 5.55 on BRAND_BLACK. The RNV fills are
    # mid-tones BY DESIGN, and #926c89 reads 3.91 there. An alias onto a fill
    # is a fill used as text, and it survived only while the fill was not
    # really a fill.
    tree.sub("ui/colors.py",
             "STATUS_ACTIVE_COLOR: Final[str] = STATUS_SUCCESS\n",
             "STATUS_ACTIVE_COLOR: Final[str] = STATUS_SUCCESS_TEXT\n", 1)
    tree.sub("ui/colors.py",
             'It is an ALIAS rather than a copy because "running" is not '
             '"succeeded" and\n',
             "RNV-STATUS-FAMILY (2026-09-03): this constant is no longer what\n"
             "gets painted. ui/settings_dialog.py wrote `color: "
             "{STATUS_ACTIVE_COLOR}`\n"
             "on the watch label -- TEXT, in a dialog that runs in three modes --\n"
             "and a module-level constant does not know which mode it is in. One\n"
             "value cannot be legal on all three grounds: the dark text variant\n"
             "reads 5.52 on #1a1a1a and 3.15 on #ffffff. The palettes now carry a\n"
             "`status_active` key resolved per mode, and the call site reads the\n"
             "theme it was already holding. This constant remains as the\n"
             "REGISTER-FACING alias below, which is what it was always for.\n"
             "\n"
             "AND IT NOW ALIASES success-text RATHER THAN success, ruled by the\n"
             "register 2026-09-04. It pointed at the FILL, which was safe only by\n"
             "accident: Bootstrap's green read 5.55 on BRAND_BLACK and doubled as\n"
             "text. The RNV fills are mid-tones by design and #926c89 reads 3.91\n"
             "there, so the alias would have failed the 4.5 text floor on the day\n"
             "the family landed. An alias onto a fill is a fill used as text.\n"
             "\n"
             'It is an ALIAS rather than a copy because "running" is not '
             '"succeeded" and\n', 1)

    # --- 5. the call site. `get_theme_colors` is already imported in this
    # file, so the dialog is asking for its theme a few lines away from here.
    tree.sub("ui/settings_dialog.py",
             "            self.watch_status_label.setStyleSheet("
             'f"color: {STATUS_ACTIVE_COLOR};")\n',
             "            # RNV-STATUS-FAMILY: read per mode. This was\n"
             "            # STATUS_ACTIVE_COLOR, a module constant, on a label\n"
             "            # that is painted in dark, light and image mode.\n"
             "            _active = get_theme_colors()['status_active']\n"
             "            self.watch_status_label.setStyleSheet("
             'f"color: {_active};")\n', 1)

    # --- 6. the import. STATUS_ACTIVE_COLOR is no longer read here, and an
    # import left behind for a name nothing uses is how a reader concludes it
    # is still what gets painted.
    tree.sub("ui/settings_dialog.py",
             "    swatch_edge, STATUS_ACTIVE_COLOR,\n",
             "    swatch_edge,\n", 1)

    # --- 7. __all__
    tree.sub("ui/colors.py",
             "    'STATUS_SUCCESS',\n"
             "    'STATUS_WARNING',\n"
             "    'STATUS_ACTIVE_COLOR',\n",
             "    'STATUS_SUCCESS',\n"
             "    'STATUS_WARNING',\n"
             "    'STATUS_SUCCESS_TEXT',\n"
             "    'STATUS_WARNING_TEXT',\n"
             "    'STATUS_SUCCESS_TEXT_LIGHT',\n"
             "    'STATUS_WARNING_TEXT_LIGHT',\n"
             "    'STATUS_ACTIVE_COLOR',\n", 1)

    # --- 8. the gold guard's exemption list.
    #
    # tests/test_brand_contrast.py walks every palette for values that look
    # gold -- r > g > b with at least 30 between r and b -- and fails on any
    # that is not a registered gold. It carried one exemption, for the
    # Bootstrap amber.
    #
    # THE NEW WARNING NEEDS THE EXEMPTION MORE, NOT LESS. #ffc107 was a bright
    # yellow sitting 17.7 CIEDE2000 from the nearest brand gold -- it tripped
    # the r > g > b shape test and nothing else. #a2703c is a brown-gold
    # because it IS half brand dark gold: the register mixed it 50% toward
    # BRAND_DARK_GOLD in OKLab, and it lands 9.1 from that gold. That clears
    # the register's own 8.40 "clearly different" bar by 0.7, which is the
    # margin the register measured and accepted when it chose 50% over 60%.
    #
    # The old entry is REMOVED rather than left beside the new one: this file
    # has a test asserting the exemption list names nothing dead, on the
    # principle that a dead exemption is a licence waiting for a future defect.
    tree.sub("tests/test_brand_contrast.py",
             'NOT_BRAND_GOLD = {\n'
             '    "#ffc107": "Material amber -- the semantic warning colour, '
             'not brand gold",\n'
             '}\n',
             'NOT_BRAND_GOLD = {\n'
             '    "#a2703c": "STATUS warning -- the semantic warning colour, '
             'not brand gold. "\n'
             '               "RNV-STATUS-FAMILY (2026-09-03): it reads as gold '
             'to the r > g > b "\n'
             '               "shape test because it half IS one -- the register '
             'derives it 50% "\n'
             '               "toward BRAND_DARK_GOLD in OKLab. CIEDE2000 9.1 '
             'from that gold, "\n'
             '               "clearing the register\'s own 8.40 threshold by '
             '0.7. Replaced "\n'
             '               "#ffc107, which sat 17.7 away and tripped only the '
             'shape test.",\n'
             '}\n', 1)

    # --- 9. the theme-key snapshots. Adding status_active adds a key to three
    # palettes, and this file pins each palette's key set. Inserted in sorted
    # position because the lists are sorted and the repository's own helper
    # writes them that way.
    _add_snapshot_key(tree)

    # --- 10. a defect in this repository's own ink guard, batched here
    # because this pass is what surfaced it.
    #
    # tests/test_ink_rule.py has two sweeps over the same sources.
    # test_no_call_site_measures_brightness_by_hand strips comments and
    # strings first, and its docstring says exactly why: "the explanations
    # above each replaced call site -- which name the arithmetic they retired
    # -- do not fail the sweep that forbids it".
    #
    # test_the_retired_names_are_gone, four lines below it, does not. So the
    # file knows the answer and applies it to one of its two guards. Any
    # comment explaining why a name was retired fails the other one -- which
    # is what happened when this script's own provenance mentioned
    # CONTRAST_ON_DARK by name. The fix is the one the file already made.
    tree.sub("tests/test_ink_rule.py",
             "def test_the_retired_names_are_gone():\n"
             "    strays = []\n"
             "    for path, text in _sources():\n"
             "        for old in RETIRED:\n"
             "            if re.search(r\"\\b%s\\b\" % re.escape(old), text):\n",
             "def test_the_retired_names_are_gone():\n"
             '    """Reads code with comments and strings removed, for the same\n'
             "    reason the sweep above does: an explanation of why a name was\n"
             "    retired has to be allowed to say the name. Until 2026-09-03\n"
             "    this sweep read raw text while its sibling four lines up did\n"
             "    not, so the file held both answers to one question.\n"
             '    """\n'
             "    strays = []\n"
             "    for path, text in _sources():\n"
             "        code = _code_only(text)\n"
             "        for old in RETIRED:\n"
             "            if re.search(r\"\\b%s\\b\" % re.escape(old), code):\n", 1)

    print("  10 edit groups composed")


def _add_snapshot_key(tree) -> None:
    """Add status_active to the three theme-key snapshots.

    Rewritten rather than regenerated with the repository's own snapshot
    helper, because a regeneration would also absorb any other drift sitting
    in the file and present it as part of this change. The three lists are
    sorted, so the key goes in sorted position and the file stays byte-
    comparable with what the helper would produce.
    """
    import json
    rel = "tests/snapshots.json"
    snap = json.loads(tree.read(rel))
    touched = []
    for name in ("dark_theme_keys", "light_theme_keys", "image_mode_keys"):
        keys = snap[name]
        if keys != sorted(keys):
            raise SystemExit(f"{rel}: {name} is not sorted; regenerate it with "
                             f"the repository's own helper and re-derive this "
                             f"edit")
        if "status_active" in keys:
            raise SystemExit(f"{rel}: {name} already holds status_active")
        snap[name] = sorted(keys + ["status_active"])
        touched.append(name)
    if len(touched) != 3:
        raise SystemExit(f"{rel}: expected three theme-key snapshots")
    tree.write(rel, json.dumps(snap, indent=2) + "\n")


def checks(tree) -> None:
    colors_src = tree.read("ui/colors.py")
    dialog = tree.read("ui/settings_dialog.py")

    for dead in RETIRED:
        if f'"{dead}"' in colors_src or f"'{dead}'" in colors_src:
            raise SystemExit(f"{dead} survives as a value in ui/colors.py")

    for role, (fill, dark, light) in FAMILY.items():
        for name, want in ((f"STATUS_{role}", fill),
                           (f"STATUS_{role}_TEXT", dark),
                           (f"STATUS_{role}_TEXT_LIGHT", light)):
            if f'{name}: Final[str] = "{want}"' not in colors_src:
                raise SystemExit(f"{name} is not defined as {want}")

    # the alias is kept -- the existing guard's reasoning depends on it
    if "STATUS_ACTIVE_COLOR: Final[str] = STATUS_SUCCESS_TEXT" not in colors_src:
        raise SystemExit("STATUS_ACTIVE_COLOR does not alias STATUS_SUCCESS_TEXT. "
                         "The alias is kept -- it is what keeps this app's "
                         "borrowing visible -- but it must point at the TEXT "
                         "value: it is painted with `color:`, and the fill reads "
                         "3.91 on BRAND_BLACK against a 4.5 floor.")

    # and it is no longer what gets painted
    if re.search(r"\bSTATUS_ACTIVE_COLOR\b", _code_only(dialog)):
        raise SystemExit("ui/settings_dialog.py still paints with the "
                         "mode-blind STATUS_ACTIVE_COLOR")
    if "get_theme_colors()['status_active']" not in dialog:
        raise SystemExit("the watch label does not read status_active from "
                         "the theme")

    # every mode resolves status_active, including image through the splat
    if colors_src.count("'status_active':") != 2:
        raise SystemExit("status_active should be set in exactly two palettes "
                         "-- image inherits dark's through **DARK_THEME_COLORS")

    if SENTINEL not in colors_src:
        raise SystemExit("the ruling note did not land in ui/colors.py")
    print("  guards: 3 retired values gone, 6 registered values in, "
          "status_active resolves per mode")


# ------------------------------------------------------------------ plumbing
def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        sys.exit(f"refusing to run as {name} -- it would shadow a module on "
                 f"sys.path. Rename to up.py and run again.")


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise SystemExit(f"missing file: {rel}")
            self.files[rel] = p.read_text(encoding="utf-8")
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise SystemExit(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.")
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = text.encode("utf-8")
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort" or "env" -- only exit code 1 means a test failed.

    pytest exits 0 passed, 1 tests failed, 2 interrupted, 3 internal error,
    4 usage error, 5 nothing collected; a native abort arrives as 134 or -6.
    Treating every non-zero code as a failing assertion is how a tool reports
    a regression that never happened.
    """
    if code == 0:
        return "pass"
    if code in (-9, 137, -15, 143):
        return "killed"
    if code in (134, -6, 139, -11) or "Fatal Python error" in out:
        return "abort"
    if code == 1 and "INTERNALERROR" not in out:
        return "fail"
    return "env"


ENV_HELP = """\
THE ENVIRONMENT IS NOT READY. NO TEST DISAGREED WITH THIS CHANGE -- the run
did not get far enough to ask one.

PyQt6 needs system libraries a fresh container does not ship; the give-away is
`ImportError: libGL.so.1`. Install those, then the Python packages:

    sudo apt-get update
    sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\
      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\
      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \\
      libxcb-xfixes0 libxcb-xkb1

    pip install -r requirements.txt -r tests/requirements-dev.txt
    python up.py --verify
"""

ABORT_HELP = """\
PYTHON ABORTED NATIVELY. That is not a failing assertion. On offscreen Linux
these suites can abort in Qt's thread teardown -- it surfaces during whatever
work is in flight and reads exactly like a regression in it.

Re-run:

    python up.py --verify

If it aborts every time on the same test, that is worth looking at. If it
comes and goes, this change is not involved.
"""


KILLED_HELP = """\
THE TEST PROCESS WAS KILLED FROM OUTSIDE. No test failed and nothing crashed --
something stopped the run, and on a small runner that is almost always the
out-of-memory killer arriving part way through a long Qt suite.

Re-run:

    python up.py --verify

If it keeps dying at roughly the same point, run the suite on its own so you
can watch it, and close anything else heavy first:

    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
"""


def run(label: str, args: list[str]) -> tuple[int, str]:
    """Stream to a temp file rather than capture_output: a long Qt suite emits
    megabytes, and buffering that in memory can get the run killed, which looks
    exactly like a failure."""
    print(f"  {label} ...", flush=True)
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8",
                                errors="replace") as fh:
        proc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.seek(0)
        out = fh.read()
    return proc.returncode, out


def _step(label: str, args: list[str]) -> int:
    code, out = run(label, args)
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass"
          else "\n".join(out.strip().splitlines()[-3:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
    elif verdict == "abort":
        print("\n" + ABORT_HELP)
    elif verdict == "killed":
        print("\n" + KILLED_HELP)
    elif verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows exactly what landed.")
    return code


def verify() -> int:
    code = _step("guard",
                 [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                  GUARD])
    if code != 0:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != 0:
            return code
    print("\nGreen.")
    return 0


def apply(check_only: bool) -> int:
    root = Path.cwd()
    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise SystemExit(globals().get("MISSING_HELP") or
                         f"run this from the root of a {REPO} checkout "
                         f"(no {SENTINEL_FILE} here)")
    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8"):
        raise SystemExit(f"already applied -- {SENTINEL!r} is present in "
                         f"{SENTINEL_FILE}")

    tree = Tree(root)
    edits(tree)
    tree.write(GUARD, GUARD_SOURCE)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        return 0

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    return verify()


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    refuse_to_shadow()
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    if args.finish:
        finish()
        return 0
    if args.verify:
        return verify()
    return apply(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
