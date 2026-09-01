#!/usr/bin/env python3
"""
RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP

Rename the two dialog button families, and delete the alias that made one key
name mean two different schemes inside this one application.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

NOT ONE PIXEL MOVES. This is a rename and a deletion of indirection.

THE ALIAS

ui/theme_manager.py built the main window's theme dict like this:

    # Main window buttons use inverse system -- see colors.py main_btn_* keys
    'button_bg': DARK_THEME_COLORS['main_btn_bg'],
    'button_text': DARK_THEME_COLORS['main_btn_text'],
    ...

So `theme['button_bg']` was the MAIN scheme and
`get_theme_colors()['button_bg']` was the GOLD DIALOG scheme -- the same key
name, two schemes, separated only by which function handed you the dict. The
comment existed because the names could not carry the distinction.

That block is not a design decision. It is a bridge between two naming
conventions, and with both sides named properly it has nothing left to do:
the six entries fold into the passthrough comprehension directly above them,
under the names they already have.

WHAT MOVES

    button_*          ->  dialog_btn_*          8 keys
    accent_button_*   ->  dialog_btn_accent_*   6 keys
    the alias block   ->  six passthrough names in the comprehension above it

164 quoted dialog occurrences and 61 accent ones across fourteen files, plus
twelve alias lines that stop existing and twelve reads in RNV_Icon_Builder.py
that now name the main family directly.

main_btn_* in ui/colors.py does not move. platform_btn_* and clear_btn_bg do
not move either: they are component keys inside the settings dialog, not a
scheme, and folding them into dialog_btn_* would claim a generality they do
not have.

THE TEST MODULE IS SPLIT BY HAND, NOT SWEPT

test_rnv_icon_builder.py names both families. One key list belongs to the
75-key palettes in ui/colors.py and becomes the dialog family; another belongs
to the ThemeManager themes and becomes the main one; six assertions read
tm.DARK_THEME / tm.LIGHT_THEME directly and are main. A blanket substitution
over that file would put six main-window assertions onto the dialog family and
still pass, because before this pass both names resolved. Each is anchored
individually and counted.

THE SNAPSHOT IS REGENERATED, NOT SUBSTITUTED

tests/snapshots.json records each palette as a sorted key list. Fourteen names
per list move, and dialog_btn_* does not sort where button_* and
accent_button_* sorted. The file is reloaded, renamed, re-sorted and written
back with the same json.dumps(indent=2) the repository's own regeneration
helper uses, so the formatting is identical by construction rather than by
hand.

DOCUMENTATION IS NOT TOUCHED, ON PURPOSE

The docs pass runs once, after alignment settles. The guard sweeps code and
snapshots, not prose.

WHAT THE GUARD ASSERTS

tests/test_button_key_names.py fails if an old name comes back anywhere, if a
palette loses a key, if any of the twenty-four dialog values or eighteen accent
values or fourteen main values moved, if the theme dict republishes a button_*
name, if a snapshot list stops being sorted, or if the two schemes converge.
It reads the palettes by importing them: two of these values are derived
through lighten(), and a static resolver returns None for those and then
compares None with None and passes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-icon-builder"
DESCRIPTION = "rename the dialog button families and delete the theme alias"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "'dialog_btn_bg'"
GUARD = "tests/test_button_key_names.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ('unittest suite',
     [sys.executable, "-m", "unittest", "test_rnv_icon_builder"]),
]

DIALOG_KEYS = ("button_bg", "button_text", "button_hover_bg", "button_hover_text",
               "button_pressed_bg", "button_pressed_text", "button_border",
               "button_hover_border")
ACCENT_KEYS = ("accent_button_bg", "accent_button_text", "accent_button_border",
               "accent_button_hover_bg", "accent_button_pressed_bg",
               "accent_button_pressed_text")
MAIN_KEYS = ("button_bg", "button_text", "button_hover_bg", "button_hover_text",
             "button_pressed_bg", "button_pressed_text")

RENAME_DIALOG = {k: "dialog_btn_" + k[len("button_"):] for k in DIALOG_KEYS}
RENAME_ACCENT = {k: "dialog_btn_accent_" + k[len("accent_button_"):]
                 for k in ACCENT_KEYS}
RENAME_MAIN = {k: "main_" + k.replace("button_", "btn_") for k in MAIN_KEYS}

#: file -> (dialog count, accent count). Written down so the script refuses to
#: run against a tree that has moved under it.
DIALOG_FILES = {
    "ui/colors.py": (16, 12),
    "ui/settings_dialog.py": (25, 20),
    "ui/preview_utils.py": (14, 0),
    "utils/dialog_helper.py": (14, 0),
    "ui/ico_analyzer.py": (7, 8),
    "ui/about_dialog.py": (7, 0),
    "ui/context_preview.py": (6, 0),
    "ui/base_dialog.py": (5, 0),
    "tests/test_brand_contrast.py": (2, 2),
    "tests/test_ladder_and_plate.py": (2, 1),
    "tests/test_app_mirror.py": (1, 0),
}

#: The main window reads its theme dict, and every button key in this file is
#: one of those reads.
MAIN_FILES = {"RNV_Icon_Builder.py": 12}

#: The alias, folded into the comprehension above it. One per palette.
ALIAS_OLD = """        )},
        # Main window buttons use inverse system — see colors.py main_btn_* keys
        'button_bg': {P}['main_btn_bg'],
        'button_text': {P}['main_btn_text'],
        'button_hover_bg': {P}['main_btn_hover_bg'],
        'button_hover_text': {P}['main_btn_hover_text'],
        'button_pressed_bg': {P}['main_btn_pressed_bg'],
        'button_pressed_text': {P}['main_btn_pressed_text'],
"""
ALIAS_NEW = """            # The main window's buttons, passed through under the names
            # they already have. Until 2026-09-01 these six were republished
            # as button_* -- which is how one key name came to mean the main
            # scheme here and the gold dialog scheme in get_theme_colors().
            'main_btn_bg', 'main_btn_text', 'main_btn_hover_bg',
            'main_btn_hover_text', 'main_btn_pressed_bg',
            'main_btn_pressed_text',
        )},
"""

#: test_rnv_icon_builder.py names both families; each site is anchored.
TEST_ANCHORS = [
    # the 75-key palettes in ui/colors.py -> dialog
    ("        'button_bg', 'button_text', 'button_hover_bg', 'button_pressed_bg',\n"
     "        'button_pressed_text', 'button_border',",
     "        'dialog_btn_bg', 'dialog_btn_text', 'dialog_btn_hover_bg',\n"
     "        'dialog_btn_pressed_bg', 'dialog_btn_pressed_text',\n"
     "        'dialog_btn_border',", 1),
    # the ThemeManager themes -> main
    ("                      'button_bg', 'button_text', 'button_hover_bg',\n"
     "                      'button_pressed_bg', 'button_pressed_text']",
     "                      'main_btn_bg', 'main_btn_text', 'main_btn_hover_bg',\n"
     "                      'main_btn_pressed_bg', 'main_btn_pressed_text']", 1),
    ("DARK_THEME.get('button_hover_bg', '')",
     "DARK_THEME.get('main_btn_hover_bg', '')", 3),
    ("LIGHT_THEME.get('button_hover_bg', '')",
     "LIGHT_THEME.get('main_btn_hover_bg', '')", 1),
    ("DARK_THEME['button_pressed_text']", "DARK_THEME['main_btn_pressed_text']", 1),
    ("LIGHT_THEME['button_pressed_text']", "LIGHT_THEME['main_btn_pressed_text']", 1),
]

_D_RE = re.compile(r"(?<!accent_)(['\"])("
                   + "|".join(sorted(DIALOG_KEYS, key=len, reverse=True)) + r")\1")
_A_RE = re.compile(r"(['\"])("
                   + "|".join(sorted(ACCENT_KEYS, key=len, reverse=True)) + r")\1")
_M_RE = re.compile(r"(?<!accent_)(['\"])("
                   + "|".join(sorted(MAIN_KEYS, key=len, reverse=True)) + r")\1")


def _sub(pattern, mapping, text):
    hits = 0

    def swap(m):
        nonlocal hits
        hits += 1
        return f"{m.group(1)}{mapping[m.group(2)]}{m.group(1)}"

    return pattern.sub(swap, text), hits


def _rename_snapshot(text: str) -> str:
    """Rename inside the JSON and re-sort, then write it the way the repo's own
    regeneration helper writes it."""
    data = json.loads(text)
    both = {**RENAME_DIALOG, **RENAME_ACCENT}
    for name, value in data.items():
        if name.endswith("_keys") and isinstance(value, list):
            data[name] = sorted(both.get(k, k) for k in value)
    return json.dumps(data, indent=2) + "\n"


def edits(tree) -> None:
    dialog = accent = 0
    for rel, (want_d, want_a) in DIALOG_FILES.items():
        src = tree.read(rel)
        src, got_a = _sub(_A_RE, RENAME_ACCENT, src)
        src, got_d = _sub(_D_RE, RENAME_DIALOG, src)
        if (got_d, got_a) != (want_d, want_a):
            raise SystemExit(f"{rel}: expected {want_d} dialog and {want_a} "
                             f"accent key(s), found {got_d} and {got_a}. The "
                             f"file moved; re-derive this edit.")
        tree.write(rel, src)
        dialog += got_d
        accent += got_a

    for rel, want in MAIN_FILES.items():
        src, got = _sub(_M_RE, RENAME_MAIN, tree.read(rel))
        if got != want:
            raise SystemExit(f"{rel}: expected {want} main key(s), found {got}")
        tree.write(rel, src)

    for palette in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS"):
        tree.sub("ui/theme_manager.py",
                 ALIAS_OLD.replace("{P}", palette),
                 ALIAS_NEW, 1)

    for old, new, times in TEST_ANCHORS:
        tree.sub("test_rnv_icon_builder.py", old, new, times)

    tree.write("tests/snapshots.json",
               _rename_snapshot(tree.read("tests/snapshots.json")))

    print(f"  renamed {dialog} dialog and {accent} accent keys, "
          f"{sum(MAIN_FILES.values())} main reads, folded 2 alias blocks, "
          f"regenerated the snapshot")


def checks(tree) -> None:
    old_names = set(DIALOG_KEYS) | set(ACCENT_KEYS)
    for rel in list(DIALOG_FILES) + list(MAIN_FILES) + \
            ["ui/theme_manager.py", "test_rnv_icon_builder.py",
             "tests/snapshots.json"]:
        text = tree.read(rel)
        for old in old_names:
            if re.search(r"(['\"])" + old + r"\1", text):
                raise SystemExit(f"{rel}: {old!r} survived the rename")

    manager = tree.read("ui/theme_manager.py")
    if "main_btn_* keys" in manager:
        raise SystemExit("the alias comment survived; the block it explained "
                         "is gone and the comment would outlive its reason")
    if manager.count("'main_btn_bg', 'main_btn_text', 'main_btn_hover_bg',") != 2:
        raise SystemExit("expected the folded passthrough in both palettes")

    data = json.loads(tree.read("tests/snapshots.json"))
    for name, value in data.items():
        if name.endswith("_keys") and isinstance(value, list):
            if value != sorted(value):
                raise SystemExit(f"{name} is not sorted after regeneration")
    for name in ("dark_theme_keys", "light_theme_keys", "image_mode_keys"):
        entries = [k for k in data[name] if "dialog_btn_" in k]
        if len(entries) != 14:
            raise SystemExit(f"{name} carries {len(entries)} dialog keys, "
                             f"expected 14")

    original = json.loads((Path.cwd() / "tests" / "snapshots.json")
                          .read_text(encoding="utf-8"))
    for name, value in original.items():
        if not (name.endswith("_keys") and isinstance(value, list)):
            continue
        if len(data[name]) != len(value):
            raise SystemExit(f"{name} changed length: {len(value)} -> "
                             f"{len(data[name])}. A rename adds and removes "
                             f"nothing.")

    main_window = tree.read("RNV_Icon_Builder.py")
    if "theme['main_btn_bg']" not in main_window:
        raise SystemExit("the main window no longer names the main family")
    print("  guards: no old name survives, the alias is folded away, the "
          "snapshot is sorted and the same length")


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


def test_the_marker_exemption_covers_only_the_two_tools():
    marked = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(marker in text for marker in MARKERS):
            marked.append(path.relative_to(ROOT))
    assert len(marked) <= 2, f"unexpected marked file(s): {marked}"
    assert Path(__file__).relative_to(ROOT) in marked


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
