"""One rule for which ink goes on a ground. RNV-INK-RULE-GUARD

Ruled by Chris on 2026-09-02 after seeing the rules rendered side by side.
This application asked the question in two places and answered it two
different ways, neither of them a contrast measurement. The guard exists
because that is a failure that reappears -- the next person who needs an ink
for a swatch will reach for (r+g+b)/3 unless something stops them.

rnv-color-picker carries the same guard against the same block.
"""
from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path

from ui import colors

ROOT = Path(__file__).resolve().parent.parent
RETIRED = ('CONTRAST_ON_DARK', 'CONTRAST_ON_LIGHT', 'SWATCH_BORDER_ON_DARK', 'SWATCH_BORDER_ON_LIGHT')
SKIP = {".git", "build", "dist", ".venv", "__pycache__"}


def _code_only(text: str) -> str:
    """The file with every comment and string literal removed.

    A guard that sweeps for the thing it forbids must be able to tell a use
    from a mention. Every earlier attempt at that in this programme did it by
    excluding files, which stops working the moment a third file has a
    legitimate reason to say the word. Tokenising needs no list."""
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text
    return " ".join(out)


def _sources():
    for path in sorted(ROOT.rglob("*.py")):
        if any(p in SKIP for p in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if "RNV-INK-RULE-GUARD" in text or "RNV-NAMING-TOOL-DO-NOT-SWEEP" in text:
            continue
        yield path, text


def test_the_rule_is_a_real_contrast_measurement():
    assert colors.contrast_ink("#ffffff") == colors.TRUE_BLACK
    assert colors.contrast_ink("#000000") == colors.WHITE
    assert round(colors.contrast_ratio("#ffffff", "#000000"), 2) == 21.0
    assert round(colors.contrast_ratio("#777777", "#777777"), 2) == 1.0


def test_the_rule_gets_saturated_colour_right():
    """The case (r+g+b)/3 got wrong. Pure green is a LIGHT ground -- 71% of
    the luminance of white -- and the mean called it dark because it only
    counted how many channels were lit."""
    assert colors.contrast_ink((0, 255, 0)) == colors.TRUE_BLACK
    assert colors.contrast_ratio((0, 255, 0), colors.TRUE_BLACK) > 15
    assert sum((0, 255, 0)) / 3 < 128       # what the old rule saw


def test_the_two_call_sites_now_agree():
    """settings_dialog picked an edge and preview_utils picked an ink, and on
    a saturated ground they disagreed about which way the ground faced. They
    cannot any more: both ask the same function."""
    for ground in ("#00ff00", "#ffff00", "#20b0b0", "#808080", "#101010"):
        dark_ink = colors.contrast_ink(ground) == colors.TRUE_BLACK
        dark_edge = colors.swatch_edge(ground) == colors.APP_BORDER
        assert dark_ink == dark_edge, (
            f"{ground}: ink and edge disagree about which way it faces")


def test_it_takes_a_hex_string_or_an_rgb_triple():
    assert colors.contrast_ink("#00ff00") == colors.contrast_ink((0, 255, 0))
    assert colors.contrast_ink("#0f0") == colors.contrast_ink("#00ff00")


def test_the_edge_rule_shares_the_ink_rule():
    assert colors.swatch_edge("#ffffff") == colors.APP_BORDER
    assert colors.swatch_edge("#000000") == colors.GREY_CC
    for ground in ("#ffffff", "#000000", "#8c7337", "#00ff00", "#777777"):
        edge = colors.swatch_edge(ground)
        other = colors.GREY_CC if edge == colors.APP_BORDER else colors.APP_BORDER
        assert colors.contrast_ratio(ground, edge) >= \
            colors.contrast_ratio(ground, other)


def test_no_call_site_measures_brightness_by_hand():
    """The rule is only one rule while nothing else computes its own.

    Reads code with comments and strings removed, so the explanations above
    each replaced call site -- which name the arithmetic they retired -- do
    not fail the sweep that forbids it."""
    mean = re.compile(r"sum \( colou?r \) / 3|\( r \+ g \+ b \) / 3")
    luma = re.compile(r"\* 299\b|\* 587\b|\* 114\b")
    strays = []
    for path, text in _sources():
        code = _code_only(text)
        if mean.search(code) or luma.search(code):
            strays.append(str(path.relative_to(ROOT)))
    assert not strays, f"hand-rolled brightness rules are back in: {strays}"


def test_the_retired_names_are_gone():
    strays = []
    for path, text in _sources():
        for old in RETIRED:
            if re.search(r"\b%s\b" % re.escape(old), text):
                strays.append(f"{path.relative_to(ROOT)}: {old}")
    assert not strays, "retired names are still in use:\n  " + "\n  ".join(strays)


def test_no_three_digit_hex_in_the_palette():
    """One of the retired constants was "#ccc". The census reads six-digit
    hexes, so a three-digit one is a value the chart cannot see."""
    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")
    hits = re.findall(r"""['"]#[0-9a-fA-F]{3}['"]""", src)
    assert not hits, f"three-digit hexes are back: {hits}"


def test_the_rule_matches_the_pickers():
    """Two applications, one block. If they drift, the fleet has two rules
    again and the drift will be invisible until a swatch looks wrong in one
    app and right in the other."""
    for ground in ("#ffffff", "#000000", "#808080", "#00ff00", "#d2bc93",
                   "#8c7337", "#20b0b0", "#9a9a30", "#3060d0"):
        want_black = colors.relative_luminance(ground) > 0.1791287
        assert (colors.contrast_ink(ground) == colors.TRUE_BLACK) == want_black
