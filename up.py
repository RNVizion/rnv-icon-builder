#!/usr/bin/env python3
"""
RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP

Replace tests/test_button_key_names.py. One test in it was wrong.

    python up.py             # replace the guard, then verify
    python up.py --check     # rehearse, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

THE RENAME IS FINE. THE GUARD WAS NOT.

test_the_marker_exemption_covers_only_the_two_tools counted the files carrying
a DO-NOT-SWEEP marker and allowed two: the guard itself, and the delivery
script. A working tree holding a second copy of that script -- an old up.py
kept around, a renamed spare, the file saved twice -- puts a third marked file
in the repository and the count fails. Nothing about the application is wrong
when that happens, and a guard that fails on the state of somebody's checkout
is failing on the wrong thing. It did exactly that in rnv-text-transformer.

WHAT IT SHOULD HAVE ASSERTED

Not how many files are exempt, but WHICH. The sweep skips marked files so a
guard that lists the old names in order to forbid them does not report itself.
The risk that creates is an application file gaining a marker and going quiet.
So the test now checks that every marked file other than the guard is a
delivery script, identified by the tool marker in its own header. Any number
of those may be lying in the tree; none of them is application source.

Verified in both directions before shipping: with three tool copies present it
passes, and with a marker planted in an application file it still fails.

This is the ninth use-versus-mention failure this programme has recorded, and
the first where the fix was to stop counting and start naming.

WHAT THIS SCRIPT DOES

Rewrites tests/test_button_key_names.py and nothing else. It refuses to run
unless the rename already landed, so it cannot be mistaken for the pass itself.
If your guard is currently passing, this still replaces it -- the old test
passes by luck of what is in your working tree, not by being right.
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
DESCRIPTION = "replace the button-naming guard's exemption test"
GUARD = "tests/test_button_key_names.py"
SENTINEL_FILE = GUARD
SENTINEL = "test_no_application_file_is_exempt_from_the_sweep"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

PALETTE = "ui/colors.py"
PROOF = "'dialog_btn_bg'"

MISSING_HELP = """\
tests/test_button_key_names.py is not here, so the button key rename has not
run in this checkout yet.

This script only replaces that guard. Run the rename script first -- the one
whose header begins "Rename the two dialog button families, and delete the alias" -- and then run this one. There is no filename
to look for: every script arrives as an attachment and is saved as up.py.
"""

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ('unittest suite',
     [sys.executable, "-m", "unittest", "test_rnv_icon_builder"]),
]

#: The tests the shipped guard already carries. This pass replaces ONE of them;
#: a replacement that quietly dropped the others would be a regression wearing
#: the shape of a fix.
KEEP = (
    'test_no_old_button_key_name_survives',
    'test_all_three_palettes_carry_both_dialog_families',
    'test_the_rename_moved_no_dialog_value',
    'test_the_rename_moved_no_accent_value',
    'test_the_main_family_is_untouched',
    'test_the_theme_dict_no_longer_renames_the_main_family',
    'test_the_main_window_reads_the_main_family',
    'test_dialogs_read_a_dialog_family',
    'test_the_snapshot_key_lists_are_still_sorted',
    'test_the_two_schemes_are_still_different',
)


def edits(tree) -> None:
    if PROOF not in tree.read(PALETTE):
        raise SystemExit(
            f"{PALETTE} does not carry {PROOF}, so the rename has not "
            f"landed. This script replaces the guard only; run the rename "
            f"first.")
    if "test_the_marker_exemption_covers_only_the_two_tools" not in tree.read(GUARD):
        raise SystemExit(
            "the guard in this checkout is not the one this script fixes -- it "
            "does not contain test_the_marker_exemption_covers_only_the_two_"
            "tools. Nothing was written.")
    print("  rename confirmed present; replacing the guard")


def checks(tree) -> None:
    new = tree.read(GUARD)
    if "test_the_marker_exemption_covers_only_the_two_tools" in new:
        raise SystemExit("the old exemption test survived the replacement")
    if SENTINEL not in new:
        raise SystemExit("the replacement guard is missing its new test")
    missing = [name for name in KEEP if name not in new]
    if missing:
        raise SystemExit(
            f"these tests are gone from the replacement: {missing}. This "
            f"pass replaces one test and keeps the rest.")
    print(f"  guards: the {len(KEEP)} passing tests are still there, the "
          f"failing one is replaced")


GUARD_SOURCE = r'''"""The button keys say where the button lives.

RNV-BUTTON-NAMING-GUARD

main_btn_* is the main window at launch. dialog_btn_* is anything that opens
later. This application had both schemes and both names -- and then bridged
them with an alias, so that `theme['button_bg']` meant the MAIN scheme while
`get_theme_colors()['button_bg']` meant the GOLD DIALOG one. Same key, two
schemes, separated only by which function handed you the dict.

The alias is gone. These tests are what stop it coming back.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OLD_DIALOG = ("button_bg", "button_text", "button_hover_bg", "button_hover_text",
              "button_pressed_bg", "button_pressed_text", "button_border",
              "button_hover_border")
OLD_ACCENT = ("accent_button_bg", "accent_button_text", "accent_button_border",
              "accent_button_hover_bg", "accent_button_pressed_bg",
              "accent_button_pressed_text")
OLD = OLD_DIALOG + OLD_ACCENT
NEW_DIALOG = tuple("dialog_btn_" + n[len("button_"):] for n in OLD_DIALOG)
NEW_ACCENT = tuple("dialog_btn_accent_" + n[len("accent_button_"):]
                   for n in OLD_ACCENT)

PINNED_DIALOG = {
    "dark": {"dialog_btn_bg": "#2a2a2a", "dialog_btn_text": "#dddddd",
             "dialog_btn_hover_bg": "#3a3a3a", "dialog_btn_hover_text": "#d2bc93",
             "dialog_btn_pressed_bg": "#d2bc93", "dialog_btn_pressed_text": "#000000",
             "dialog_btn_border": "#333333", "dialog_btn_hover_border": "#d2bc93"},
    "light": {"dialog_btn_bg": "#ffffff", "dialog_btn_text": "#000000",
              "dialog_btn_hover_bg": "#eeeeee", "dialog_btn_hover_text": "#7e6529",
              "dialog_btn_pressed_bg": "#8c7337", "dialog_btn_pressed_text": "#ffffff",
              "dialog_btn_border": "#cccccc", "dialog_btn_hover_border": "#8c7337"},
    "image": {"dialog_btn_bg": "#2a2a2a", "dialog_btn_text": "#dddddd",
              "dialog_btn_hover_bg": "#3a3a3a", "dialog_btn_hover_text": "#d2bc93",
              "dialog_btn_pressed_bg": "#d2bc93", "dialog_btn_pressed_text": "#000000",
              "dialog_btn_border": "#333333", "dialog_btn_hover_border": "#d2bc93"},
}

PINNED_ACCENT = {
    "dark": {"dialog_btn_accent_bg": "#2a2a2a", "dialog_btn_accent_text": "#d2bc93",
             "dialog_btn_accent_border": "#d2bc93",
             "dialog_btn_accent_hover_bg": "#333333",
             "dialog_btn_accent_pressed_bg": "#d2bc93",
             "dialog_btn_accent_pressed_text": "#000000"},
    "light": {"dialog_btn_accent_bg": "#ffffff", "dialog_btn_accent_text": "#7e6529",
              "dialog_btn_accent_border": "#8c7337",
              "dialog_btn_accent_hover_bg": "#eeeeee",
              "dialog_btn_accent_pressed_bg": "#8c7337",
              "dialog_btn_accent_pressed_text": "#ffffff"},
    "image": {"dialog_btn_accent_bg": "#2a2a2a", "dialog_btn_accent_text": "#d2bc93",
              "dialog_btn_accent_border": "#d2bc93",
              "dialog_btn_accent_hover_bg": "#333333",
              "dialog_btn_accent_pressed_bg": "#d2bc93",
              "dialog_btn_accent_pressed_text": "#000000"},
}

PINNED_MAIN = {
    "dark": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",
             "main_btn_border": "#333333", "main_btn_hover_bg": "#333333",
             "main_btn_hover_text": "#dddddd", "main_btn_pressed_bg": "#444444",
             "main_btn_pressed_text": "#000000"},
    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",
              "main_btn_border": "#cccccc", "main_btn_hover_bg": "#333333",
              "main_btn_hover_text": "#000000", "main_btn_pressed_bg": "#444444",
              "main_btn_pressed_text": "#ffffff"},
}

SKIP = {".git", "build", "dist", ".venv", "__pycache__"}

#: A sweep for a name cannot tell a USE from a MENTION. The two files certain
#: to mention the old names are this guard -- which lists them in order to
#: forbid them -- and the delivery script that performs the rename. Skipped by
#: marker, not by filename: the script arrives under whatever name it is saved
#: as.
MARKERS = ("RNV-BUTTON-NAMING-GUARD", "RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP")

MAIN_WINDOW = "RNV_Icon_Builder.py"
DIALOG_FILES = ("ui/settings_dialog.py", "ui/about_dialog.py",
                "ui/base_dialog.py", "ui/context_preview.py",
                "ui/ico_analyzer.py", "ui/preview_utils.py",
                "utils/dialog_helper.py")


def _palettes():
    from ui.colors import (DARK_THEME_COLORS, LIGHT_THEME_COLORS,
                           IMAGE_MODE_COLORS)
    return {"dark": DARK_THEME_COLORS, "light": LIGHT_THEME_COLORS,
            "image": IMAGE_MODE_COLORS}


def _themes():
    from ui.theme_manager import ThemeManager
    return {"dark": ThemeManager.DARK_THEME, "light": ThemeManager.LIGHT_THEME}


def _sources():
    for path in sorted(ROOT.rglob("*")):
        # Prose is not swept: documentation is updated in one pass after
        # alignment settles, so it names the old keys until then.
        if path.is_dir() or path.suffix not in (".py", ".json"):
            continue
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(marker in text for marker in MARKERS):
            continue
        yield path, text


def test_no_old_button_key_name_survives():
    offenders = []
    for path, text in _sources():
        for old in OLD:
            if re.search(r"(['\"])" + old + r"\1", text):
                offenders.append(f"{path.relative_to(ROOT)}: {old}")
    assert not offenders, (
        "these keys must say where the button lives:\n  " + "\n  ".join(offenders))


TOOL_MARKER = "RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP"


def test_no_application_file_is_exempt_from_the_sweep():
    """The exemption is by marker, and the marker is how a file could hide.

    An earlier version of this counted marked files and allowed two. That
    failed in a working tree holding a second copy of the delivery script --
    a guard failing on the state of somebody's checkout rather than on a
    defect in the application, which is the wrong thing to fail on.

    What actually matters is that no APPLICATION file is exempt. This guard
    may carry a marker; it lists the old names in order to forbid them.
    Everything else must be a delivery script, identified by the tool marker
    in its own header -- those arrive under whatever name they are saved as,
    there can be several of them lying around, and none is application source.
    """
    here = Path(__file__).resolve()
    strays = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if not any(marker in text for marker in MARKERS):
            continue
        if path.resolve() == here or TOOL_MARKER in text:
            continue
        strays.append(str(path.relative_to(ROOT)))
    assert not strays, (
        "these files are skipped by the name sweep but are not a delivery "
        f"script: {strays}")
    assert MARKERS[0] in here.read_text(encoding="utf-8-sig"), (
        "this guard lost its own marker and is now sweeping itself")


def test_all_three_palettes_carry_both_dialog_families():
    for mode, palette in _palettes().items():
        missing = [n for n in NEW_DIALOG + NEW_ACCENT if n not in palette]
        assert not missing, f"{mode} palette missing {missing}"


def test_the_rename_moved_no_dialog_value():
    for mode, pins in PINNED_DIALOG.items():
        actual = {k: _palettes()[mode].get(k) for k in pins}
        assert actual == pins, (
            f"the {mode} dialog button values changed.\n"
            f"  wanted {pins}\n  found  {actual}\n"
            "A rename that changes a value is not a rename.")


def test_the_rename_moved_no_accent_value():
    for mode, pins in PINNED_ACCENT.items():
        actual = {k: _palettes()[mode].get(k) for k in pins}
        assert actual == pins, (
            f"the {mode} accent button values changed.\n"
            f"  wanted {pins}\n  found  {actual}")


def test_the_main_family_is_untouched():
    for mode, pins in PINNED_MAIN.items():
        actual = {k: _palettes()[mode].get(k) for k in pins}
        assert actual == pins, (
            f"the {mode} main button values changed. This pass renames the "
            f"DIALOG families and must not reach the main window.\n"
            f"  wanted {pins}\n  found  {actual}")


def test_the_theme_dict_no_longer_renames_the_main_family():
    """The alias is the defect this pass exists to remove.

    ThemeManager used to publish the main button values under button_* names,
    which is how one key name came to mean two schemes inside one application.
    The theme dict now passes them through under the names they already have.
    """
    for mode, theme in _themes().items():
        for key in PINNED_MAIN[mode]:
            if key == "main_btn_border":
                continue  # published as border_color, a separate legacy alias
            assert key in theme, f"{mode} theme lost {key}"
            assert theme[key] == PINNED_MAIN[mode][key], (
                f"{mode} theme's {key} is {theme[key]}, not "
                f"{PINNED_MAIN[mode][key]}")
        for old in OLD_DIALOG:
            assert old not in theme, (
                f"{mode} theme republished {old}. That alias is what made one "
                f"key name mean the main scheme here and the gold dialog "
                f"scheme in get_theme_colors().")


def test_the_main_window_reads_the_main_family():
    src = (ROOT / MAIN_WINDOW).read_text(encoding="utf-8-sig")
    assert "theme['main_btn_bg']" in src, (
        f"{MAIN_WINDOW} no longer reads the main family from its theme dict")


def test_dialogs_read_a_dialog_family():
    for rel in DIALOG_FILES:
        src = (ROOT / rel).read_text(encoding="utf-8-sig")
        assert "dialog_btn_" in src, f"{rel} no longer reads a dialog family"


def test_the_snapshot_key_lists_are_still_sorted():
    """The rename moves fourteen names in each list; leaving them where they
    were would fail the next snapshot run with a diff that reads like a
    regression."""
    data = json.loads((ROOT / "tests" / "snapshots.json").read_text(encoding="utf-8"))
    for name, value in data.items():
        if not name.endswith("_keys") or not isinstance(value, list):
            continue
        assert value == sorted(value), f"{name} is no longer sorted"
        for old in OLD:
            assert old not in value, f"{name} still carries {old}"


def test_the_two_schemes_are_still_different():
    """The main button is black-and-white with an inverting transition; the
    dialog button is gold. If they ever converge the naming carries nothing."""
    for mode, palette in _palettes().items():
        assert palette["main_btn_pressed_bg"] != palette["dialog_btn_pressed_bg"], (
            f"{mode}: the main and dialog pressed plates now hold the same "
            f"value ({palette['main_btn_pressed_bg']}). Two families holding "
            f"one scheme is one family with extra steps.")
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
