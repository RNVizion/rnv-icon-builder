"""The button keys say where the button lives.

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
