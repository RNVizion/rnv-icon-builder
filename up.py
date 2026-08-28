#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Align rnv-icon-builder's light panel and dark input to the surfaces the other
apps use.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHAT MOVES

  LIGHT panel_bg   #ffffff -> #f5f5f5     three apps already use it
  DARK  input_bg   #2a2a2a -> #1a1a1a     three apps already use it

BOTH CHANGES CREATE AN EDGE THAT WAS NOT THERE

This app painted the light panel, the card and the input all #ffffff, so a card
sitting on a panel had no edge at all. It does now. The same in dark: the input
was the card colour, so a field on a card was invisible except for its border.
At #1a1a1a it has an edge against the card -- and matches the panel, which is
how the three apps that already use it draw a field. The border is what
separates a field from the panel there, not a fill difference, and the guard
asserts that border still differs from both.

ONE EXEMPTION IS RE-KEYED, NOT ADDED

tests/test_brand_contrast.py carries `("#aaaaaa", "#ffffff")` for disabled
control text, which WCAG 1.4.3 exempts. Moving the panel moves that ground, so
the pair becomes `("#aaaaaa", "#f5f5f5")` at 2.1309 -- the same text on the
same control, one step of ground away. The app's own guard caught both halves
of this on the first run: the new pair as an unaccepted failure, and the old
key as an exemption that no longer matches anything. Nothing was hidden; the
key was moved and the reason recorded beside it.

IMAGE MODE IS DELIBERATELY UNTOUCHED. Its surfaces here are rgba strings rather
than flat hex, and it was not part of the comparison this ruling came from.
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
DESCRIPTION = "align the light panel and dark input surfaces"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "'panel_bg': '#f5f5f5'"
GUARD = "tests/test_surface_alignment.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}
CONTRAST = "tests/test_brand_contrast.py"

SUITES = [
    ("pytest tests/ (about 5 minutes)",
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ("unittest suite",
     [sys.executable, "-m", "unittest", "test_rnv_icon_builder"]),
]

OLD_EXEMPTION = '''    ("#aaaaaa", "#ffffff"):
        "disabled control text. WCAG 1.4.3 exempts disabled controls.",'''
NEW_EXEMPTION = '''    ("#aaaaaa", "#f5f5f5"):
        "disabled control text. WCAG 1.4.3 exempts disabled controls. Re-keyed "
        "from #ffffff on 2026-08-27 when the light panel moved to #f5f5f5 to "
        "match the other four apps -- the same text on the same control, one "
        "step of ground away.",'''


LIGHT_PANEL = "'#f5f5f5'"
DARK_INPUT = "'#1a1a1a'"


def _bounds(lines):
    """The three palettes carry identical key lines, so a plain string replace
    cannot tell dark from image. Every edit is scoped to its own dict."""
    starts = {}
    for i, line in enumerate(lines):
        m = re.match(r"^(DARK_THEME_COLORS|LIGHT_THEME_COLORS|IMAGE_MODE_COLORS)\s*:", line)
        if m:
            starts[m.group(1)] = i
    if len(starts) != 3:
        raise SystemExit(f"expected three theme dicts, found {sorted(starts)}")
    order = sorted(starts.items(), key=lambda kv: kv[1])
    return {n: (st, order[i + 1][1] if i + 1 < len(order) else len(lines))
            for i, (n, st) in enumerate(order)}


def _set(lines, span, key, expect, value):
    st, en = span
    hits = [i for i in range(st, en) if lines[i].strip().startswith(f"'{key}':")]
    if len(hits) != 1:
        raise SystemExit(f"expected one '{key}' in that palette, found {len(hits)}")
    if expect not in lines[hits[0]]:
        raise SystemExit(f"'{key}' is not {expect}: {lines[hits[0]].strip()!r}")
    lines[hits[0]] = lines[hits[0]].replace(expect, value)


def edits(tree) -> None:
    lines = tree.read(SENTINEL_FILE).splitlines(keepends=True)
    b = _bounds(lines)
    _set(lines, b["LIGHT_THEME_COLORS"], "panel_bg", "'#ffffff'", LIGHT_PANEL)
    _set(lines, b["DARK_THEME_COLORS"], "input_bg", "'#2a2a2a'", DARK_INPUT)
    tree.write(SENTINEL_FILE, "".join(lines))
    tree.sub(CONTRAST, OLD_EXEMPTION, NEW_EXEMPTION)


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if src.count("'panel_bg': '#f5f5f5',") != 1:
        raise SystemExit("expected exactly one light panel at #f5f5f5")
    if src.count("'input_bg': '#1a1a1a',") != 1:
        raise SystemExit("expected exactly one dark input at #1a1a1a")
    guard = tree.read(CONTRAST)
    if '("#aaaaaa", "#ffffff")' in guard:
        raise SystemExit("the stale exemption key survives")
    if guard.count('("#aaaaaa", "#f5f5f5")') != 1:
        raise SystemExit("the re-keyed exemption is not present exactly once")


GUARD_SOURCE = '"""\nPanel and input surfaces, and the edges that have to survive aligning them.\n\nRULED 2026-08-27. Light panels are #f5f5f5 in every app; dark input fields are\n#1a1a1a, which is what three of the five already used.\n\nWHAT THE ALIGNMENT ACTUALLY DID TO THE EDGES, measured from the adjacency map\nrather than assumed:\n\n  LIGHT   panel and card were the same colour here, so a card had no edge\n          against the panel it sat on. Moving the panel to #f5f5f5 CREATES\n          that edge.\n\n  DARK    the input field was the same colour as the card, so a field sitting\n          on a card had no edge either. Moving it to #1a1a1a creates one --\n          and makes it equal to the panel, which is how the three apps that\n          already used #1a1a1a have always drawn it: the input border is what\n          separates a field from the panel, not a fill difference.\n\nThat second one is the reason these tests exist. The alignment trades one\nmissing edge for another arrangement, and the arrangement only works while the\ninput keeps a border that differs from both. That is asserted below.\n\nIMAGE MODE IS DELIBERATELY UNTOUCHED. It was not part of the three-against-two\ncomparison this ruling came from, and in one of these two apps its surfaces are\nrgba strings rather than flat hex.\n"""\nfrom __future__ import annotations\n\nimport pytest\n\nfrom ui.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\n\nFLAT = {"DARK": DARK, "LIGHT": LIGHT}\n\n\ndef _hex(value) -> bool:\n    return isinstance(value, str) and value.startswith("#") and len(value) == 7\n\n\ndef test_both_flat_palettes_carry_the_surface_keys():\n    """Guard the guard: every test below reads these."""\n    for name, theme in FLAT.items():\n        for key in ("window_bg", "panel_bg", "card_bg", "input_bg",\n                    "input_border_key_present"):\n            if key == "input_border_key_present":\n                assert any(k in theme for k in ("input_border", "border_color",\n                                                "border_default")), (\n                    f"{name} has no border key for the input")\n                continue\n            assert key in theme, f"{name} has no {key}"\n            assert _hex(theme[key]), f"{name} {key} is {theme[key]!r}, not flat hex"\n\n\ndef test_the_light_panel_is_the_agreed_surface():\n    assert LIGHT["panel_bg"] == "#f5f5f5", (\n        f"light panel is {LIGHT[\'panel_bg\']}, not the #f5f5f5 all five apps use")\n\n\ndef test_the_dark_input_is_the_agreed_surface():\n    assert DARK["input_bg"] == "#1a1a1a", (\n        f"dark input is {DARK[\'input_bg\']}, not the #1a1a1a all five apps use")\n\n\ndef test_a_card_still_has_an_edge_against_its_panel():\n    """This edge did not exist before the alignment in either app -- panel and\n    card were the same colour. It exists now and must not be merged away."""\n    for name, theme in FLAT.items():\n        assert theme["card_bg"] != theme["panel_bg"], (\n            f"{name}: card {theme[\'card_bg\']} is the panel colour again, so a "\n            f"card sitting on the panel has no edge")\n\n\ndef test_the_input_is_separated_from_the_surface_it_sits_on():\n    """Dark deliberately draws the field in the panel colour and relies on the\n    border. That only works while the border differs from both."""\n    for name, theme in FLAT.items():\n        border = (theme.get("input_border") or theme.get("border_default")\n                  or theme["border_color"])\n        assert border != theme["input_bg"], (\n            f"{name}: the input border is the same colour as its fill")\n        if theme["input_bg"] == theme["panel_bg"]:\n            assert border != theme["panel_bg"], (\n                f"{name}: the input fill matches the panel AND the border "\n                f"matches the panel -- the field has no visible extent")\n\n\ndef test_image_mode_was_left_alone():\n    """Recorded rather than trusted: if image mode is aligned later, this test\n    is the thing that has to be deleted on purpose."""\n    assert "input_bg" in IMAGE\n    assert IMAGE["input_bg"] != "#1a1a1a", (\n        "image mode now uses the dark input surface. That was outside the "\n        "2026-08-27 ruling -- if it is intended, delete this test and say so.")\n'



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
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                p.write_text(text, encoding="utf-8")
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
        raise SystemExit(f"run this from the root of a {REPO} checkout "
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
