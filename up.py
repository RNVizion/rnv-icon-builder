#!/usr/bin/env python3
"""
RNV-NAMING-TOOL-DO-NOT-SWEEP

One rule for which ink goes on a colour, and the edge grey named for its
colour rather than its job.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHY

Chris, reading the colour tree on 2026-09-02:

    "_DRAG_HIGHLIGHT_GOLD reads as a constant but it should read as a key --
     the constant should denote the colour, as that is what will change to
     affect the rest of the app elements, not the keys."

That is the naming half of rule 1: a constant names a COLOUR, a key names a
ROLE. CONTRAST_ON_DARK and SWATCH_BORDER_ON_LIGHT name roles.

The survey proposed turning them into palette keys. Reading the call sites
showed that was wrong, and the name is what misled it: "on dark" does not
mean "in dark mode", it means "on a dark GROUND", and the ground here is a
colour the user picked at run time. A per-swatch runtime choice cannot be a
palette key. Ruled by Chris: make it a function.

TWO PLACES, TWO ANSWERS

    ui/settings_dialog.py:825   (r + g + b) / 3 > 128
    ui/preview_utils.py:1025    (299r + 587g + 114b) / 1000 > 128

Same application, same question, two rules -- and neither is a contrast
measurement. They part company on saturated colour, because 601 weights green
587/1000 where the mean weights it 333. On pure green the mean calls it dark
and puts WHITE on it at 1.37:1 where the right answer is black at 15.30:1.

Rendered for Chris beside the greys and ruled: unify on WCAG relative
luminance, the same maths as the ladder and the 4.5 floor. rnv-color-picker
carries the identical block, so the two applications now agree by
construction rather than by coincidence.

WHAT MOVES

Swatch inks and swatch edges, and only where the old rule was wrong: mid
greys (a swatch at #808080 goes from white text at 3.95:1 to black at 5.32:1)
and saturated colour. Nothing on a brand surface. Nothing in any palette.

ALSO HERE

    SWATCH_BORDER_ON_DARK "#ccc"  ->  GREY_CC "#cccccc"

Three digits is why the census never saw it. TRUE_BLACK, WHITE and APP_BORDER
were defined but missing from __all__; they are exported now, because the
functions return them and a caller doing `from ui.colors import *` would
otherwise get the rule without the values.

THE TESTS CHANGE SHAPE, NOT SIDES

The suite asserted CONTRAST_ON_LIGHT == "#000000" and that the two swatch
borders were non-empty strings. Neither could have caught two brightness
rules disagreeing. They are replaced by tests that ask the question --
contrast_ink("#00ff00") is black -- which is the assertion that would have
failed before this ruling.
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
DESCRIPTION = "one ink rule, and the edge grey named for its colour"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "RNV-INK-RULE"
GUARD = "tests/test_ink_rule.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ('unittest suite',
     [sys.executable, "-m", "unittest", "test_rnv_icon_builder"]),
]

RETIRED = ("CONTRAST_ON_DARK", "CONTRAST_ON_LIGHT",
           "SWATCH_BORDER_ON_DARK", "SWATCH_BORDER_ON_LIGHT")

EDITS = [
    ('ui/colors.py',
     'CONTRAST_ON_LIGHT: Final[str] = "#000000"\n"""Black — used as contrast text on light/bright backgrounds (e.g. color swatches)"""\n\nCONTRAST_ON_DARK: Final[str] = "#ffffff"\n"""White — used as contrast text on dark/dim backgrounds (e.g. color swatches)"""\n\nSWATCH_BORDER_ON_LIGHT: Final[str] = "#333"\n"""Dark border for color swatch buttons on light-colored swatches"""\n\nSWATCH_BORDER_ON_DARK: Final[str] = "#ccc"\n"""Light border for color swatch buttons on dark-colored swatches"""\n',
     'GREY_CC: Final[str] = "#cccccc"\n"""Grey cc. The light edge swatch_edge() reaches for on a dark ground.\n\nRNV-INK-RULE (2026-09-02). It used to be three digits under a role name,\nwhich is why a census that reads six-digit hexes never saw it.\n"""\n\n\n# ── Which ink goes on this ground ──\n#\n# RNV-INK-RULE (2026-09-02, ruled by Chris). This application asked the\n# question in two places and answered it two different ways:\n#\n#     ui/settings_dialog.py     (r + g + b) / 3 > 128\n#     ui/preview_utils.py       ITU-R 601 luma > 128\n#\n# Neither is a contrast measurement, and they part company on saturated\n# colour, because 601 weights green 587/1000 where the mean weights it 333.\n# On pure green the mean calls it dark and puts WHITE on it at 1.37:1, where\n# the right answer is black at 15.30:1.\n#\n# One rule now, stated as a real comparison rather than a threshold --\n# whichever candidate has the higher contrast ratio against the ground wins.\n# A threshold would have to be re-derived for every pair of candidates; a\n# ratio does not, which is what lets swatch_edge() share the rule with\n# contrast_ink().\n#\n# The same maths as the surface ladder and the 4.5 floor. rnv-color-picker\n# carries the identical block.\n\n\ndef _channel(value: float) -> float:\n    """One sRGB channel, 0-255, linearised."""\n    c = value / 255.0\n    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4\n\n\ndef _rgb(color: "str | tuple[int, int, int]") -> tuple[int, int, int]:\n    """Accept either shape. Callers hold hex strings and RGB triples both."""\n    if isinstance(color, str):\n        h = color.lstrip("#")\n        if len(h) == 3:\n            h = "".join(ch * 2 for ch in h)\n        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))\n    return (int(color[0]), int(color[1]), int(color[2]))\n\n\ndef relative_luminance(color: "str | tuple[int, int, int]") -> float:\n    """WCAG 2.x relative luminance, 0.0 (black) to 1.0 (white)."""\n    r, g, b = _rgb(color)\n    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)\n\n\ndef contrast_ratio(a: "str | tuple[int, int, int]",\n                   b: "str | tuple[int, int, int]") -> float:\n    """WCAG contrast ratio between two colours, 1.0 to 21.0."""\n    la, lb = relative_luminance(a), relative_luminance(b)\n    hi, lo = (la, lb) if la >= lb else (lb, la)\n    return (hi + 0.05) / (lo + 0.05)\n\n\ndef better_on(background: "str | tuple[int, int, int]", *candidates: str) -> str:\n    """Whichever candidate reads best on this ground. Ties go to the first."""\n    return max(candidates, key=lambda c: contrast_ratio(background, c))\n\n\ndef contrast_ink(background: "str | tuple[int, int, int]") -> str:\n    """Text colour for an arbitrary ground: WHITE or TRUE_BLACK.\n\n    For a colour the USER chose -- a swatch, a preview background. Not for\n    brand surfaces: what sits on a brand gold is a ruling, not a measurement,\n    and the two are only 0.08 apart on BRAND_DARK_GOLD.\n    """\n    return better_on(background, TRUE_BLACK, WHITE)\n\n\ndef prefers_dark_ink(background: "str | tuple[int, int, int]") -> bool:\n    """True when TRUE_BLACK reads better on this ground than WHITE does."""\n    return contrast_ink(background) == TRUE_BLACK\n\n\ndef swatch_edge(background: "str | tuple[int, int, int]") -> str:\n    """Outline for a swatch of an arbitrary colour: GREY_CC or APP_BORDER."""\n    return better_on(background, APP_BORDER, GREY_CC)\n',
     1),
    ('ui/colors.py',
     "    'CONTRAST_ON_LIGHT',\n    'CONTRAST_ON_DARK',\n    'SWATCH_BORDER_ON_LIGHT',\n    'SWATCH_BORDER_ON_DARK',\n",
     "    'TRUE_BLACK',\n    'WHITE',\n    'APP_BORDER',\n    'GREY_CC',\n    'relative_luminance',\n    'contrast_ratio',\n    'better_on',\n    'contrast_ink',\n    'prefers_dark_ink',\n    'swatch_edge',\n",
     1),
    ('ui/settings_dialog.py',
     '    BRAND_GOLD, get_theme_colors,\n    SWATCH_BORDER_ON_LIGHT, SWATCH_BORDER_ON_DARK, STATUS_ACTIVE_COLOR,\n',
     '    BRAND_GOLD, get_theme_colors,\n    swatch_edge, STATUS_ACTIVE_COLOR,\n',
     1),
    ('ui/settings_dialog.py',
     '        border_color = SWATCH_BORDER_ON_LIGHT if (r + g + b) / 3 > 128 else SWATCH_BORDER_ON_DARK\n',
     '        # RNV-INK-RULE: was (r + g + b) / 3 > 128, which is not a contrast\n        # measurement and disagreed with preview_utils.py on saturated colour.\n        border_color = swatch_edge((r, g, b))\n',
     1),
    ('ui/preview_utils.py',
     '    BRAND_GOLD, BRAND_DARK_GOLD, get_theme_colors,\n    CONTRAST_ON_LIGHT, CONTRAST_ON_DARK, DARK_THEME_COLORS,\n',
     '    BRAND_GOLD, BRAND_DARK_GOLD, get_theme_colors,\n    contrast_ink, DARK_THEME_COLORS,\n',
     1),
    ('ui/preview_utils.py',
     '        brightness = (color[0] * 299 + color[1] * 587 + color[2] * 114) / 1000\n        text_color = CONTRAST_ON_LIGHT if brightness > 128 else CONTRAST_ON_DARK\n',
     '        # RNV-INK-RULE: was ITU-R 601 perceived brightness, a photographic\n        # weighting rather than a contrast measurement.\n        text_color = contrast_ink(color)\n',
     1),
    ('test_rnv_icon_builder.py',
     '    DEFAULT_CUSTOM_BG_COLOR, CONTRAST_ON_LIGHT, CONTRAST_ON_DARK,\n    SWATCH_BORDER_ON_LIGHT, SWATCH_BORDER_ON_DARK, STATUS_ACTIVE_COLOR,\n',
     '    DEFAULT_CUSTOM_BG_COLOR, STATUS_ACTIVE_COLOR,\n    TRUE_BLACK, WHITE, APP_BORDER, GREY_CC,\n    contrast_ink, swatch_edge, contrast_ratio,\n',
     1),
    ('test_rnv_icon_builder.py',
     '    def test_contrast_on_light_is_black(self):\n        self.assertEqual(CONTRAST_ON_LIGHT, "#000000")\n\n    def test_contrast_on_dark_is_white(self):\n        self.assertEqual(CONTRAST_ON_DARK, "#ffffff")\n',
     '    def test_contrast_ink_picks_black_on_a_light_ground(self):\n        """RNV-INK-RULE: the pair used to be two constants named for the\n        ground they sat on. The question is now asked, not answered in\n        advance, so the test asks it too."""\n        self.assertEqual(contrast_ink("#ffffff"), TRUE_BLACK)\n        self.assertEqual(contrast_ink((0, 255, 0)), TRUE_BLACK)\n\n    def test_contrast_ink_picks_white_on_a_dark_ground(self):\n        self.assertEqual(contrast_ink("#000000"), WHITE)\n        self.assertEqual(contrast_ink((0, 0, 128)), WHITE)\n',
     1),
    ('test_rnv_icon_builder.py',
     '    def test_swatch_borders_nonempty(self):\n        self.assertGreater(len(SWATCH_BORDER_ON_LIGHT), 0)\n        self.assertGreater(len(SWATCH_BORDER_ON_DARK), 0)\n',
     '    def test_swatch_edge_shares_the_ink_rule(self):\n        """The same question with a different pair of candidates. A\n        len() > 0 assertion could not have caught either of the two\n        disagreeing brightness rules this replaced."""\n        self.assertEqual(swatch_edge("#ffffff"), APP_BORDER)\n        self.assertEqual(swatch_edge("#000000"), GREY_CC)\n        for ground in ("#ffffff", "#000000", "#8c7337", "#00ff00", "#777777"):\n            edge = swatch_edge(ground)\n            other = GREY_CC if edge == APP_BORDER else APP_BORDER\n            self.assertGreaterEqual(contrast_ratio(ground, edge),\n                                    contrast_ratio(ground, other))\n',
     1),
]


def edits(tree) -> None:
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    print(f"  {len(EDITS)} edit(s) composed")


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if SENTINEL not in src:
        raise SystemExit("the ruling note did not land")

    root = Path(tree.root)
    strays = []
    for path in sorted(root.rglob("*.py")):
        if any(p in {".git", "build", "dist", ".venv", "__pycache__"}
               for p in path.parts):
            continue
        if path.name in ("up.py", "up1.py", "up2.py"):
            continue
        rel = str(path.relative_to(root))
        text = tree.files.get(rel)
        if text is None:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        if "RNV-NAMING-TOOL-DO-NOT-SWEEP" in text or "RNV-INK-RULE-GUARD" in text:
            continue
        for old in RETIRED:
            if re.search(r"\b%s\b" % re.escape(old), text):
                strays.append(f"{rel}: {old}")
    if strays:
        raise SystemExit("retired names survived:\n  " + "\n  ".join(strays))

    for name in ("GREY_CC", "TRUE_BLACK", "WHITE", "APP_BORDER", "contrast_ink",
                 "prefers_dark_ink", "swatch_edge", "relative_luminance",
                 "contrast_ratio", "better_on"):
        if f"'{name}'," not in src:
            raise SystemExit(f"{name} is not exported from {SENTINEL_FILE}")

    for m in re.finditer(r"""['"]#[0-9a-fA-F]{3}['"]""", src):
        raise SystemExit(f"{SENTINEL_FILE} still writes a three-digit hex: "
                         f"{m.group(0)}")

    print(f"  guards: {len(RETIRED)} names retired, ink rule stated once")


GUARD_SOURCE = r'''"""One rule for which ink goes on a ground. RNV-INK-RULE-GUARD

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
'''


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
