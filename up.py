"""every colour named, and every name used: the icon builder's unread palette keys and constants go

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-icon-builder, derived against a fresh clone at the live head (7e7da3d).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-04, items 6 to 9 of decisions-pending-2026-09-29.md:

  "As long as a color exist in the app it should be named and used no
   hardcoded or pointless literals should exist, only literals with a
   purpose, like data or comparison are allowed. Colors are name for swap
   ability and alignment."

USED. Five palette keys no mode read go from the dark and light palettes
(image inherits them): dialog_border, hover_bg, success, tab_border,
warning. Four more -- dropzone_bg, dropzone_border, statusbar_bg and
statusbar_border -- were read by image mode alone, from the image palette
by name; they stay in that palette alone. Image mode's card_bg override
goes: every reader of card_bg takes the dark or the light palette. The main
window's own two palettes, in ThemeManager, held six copies nothing looked
up -- text_primary, border_default, hover_bg, checkbox_bg, checkbox_border
and the alias hover_color; they go. Seven constants nothing in the
application read go: BRAND_GOLD_RGB, BRAND_DARK_GOLD_RGB, STATUS_SUCCESS,
STATUS_WARNING, STATUS_WARNING_TEXT, STATUS_WARNING_TEXT_LIGHT and
STATUS_ACTIVE_COLOR.

NAMED. The colours the code spelled out each get a name in ui/colors.py at
the value they had: the transparency checkerboard's two squares, the white
and black preview grounds, the six simulated grounds an icon is composited
onto in the context preview, and the fill of a size with no image. The
background selector's starting grey was written out beside
DEFAULT_CUSTOM_BG_COLOR, the name it always had and nothing read; it is
read from that name.

THE ROOT SUITE. Five of its tests read a constant that went, and one list
required four keys the dark and light palettes no longer hold. Ruled: "for
the locked key test if we don't use these values we Can fix the test and
remove unused values". Every test stays; each takes the value from where
the application reads it.

PROVEN BEFORE BUILDING. No line of the application looks up any of the five
keys, on any receiver. Every lookup of the four image keys is on the image
palette, by name. The main window looks up ten keys on the palette it is
handed, and those ten are what its two palettes now hold. And the
application draws what it drew: every window, tab and combo in every mode,
the five compositing functions pixel for pixel, the preview with sizes
missing and autofilled, and every tab of the context preview.

FOUND ON THE WAY, AND NOT CHANGED. The ICO analyzer sets Qt's dark green on
a PNG row's cell, and it is never drawn: the table's stylesheet colours
every cell, and the sheet wins. Set to magenta, or to nothing, the table is
the same pixels in all three modes. It is left as written and listed in the
guard as held; whether to draw the mark or drop the line is a ruling.
"""
from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = 'rnv-icon-builder'
SENTINEL = 'RNV-NAMED-AND-USED'
SENTINEL_FILE = 'ui/colors.py'
GUARD = 'tests/test_named_and_used.py'
GUARD_FILES = ['tests/test_named_and_used.py', 'tests/test_brand_contrast.py', 'tests/test_derived_values.py', 'tests/test_ladder_and_plate.py', 'tests/test_light_rewalk.py', 'tests/test_snapshots.py', 'tests/test_status_register.py']
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_named_and_used.py', 'tests/test_brand_contrast.py', 'tests/test_derived_values.py', 'tests/test_ladder_and_plate.py', 'tests/test_light_rewalk.py', 'tests/test_snapshots.py', 'tests/test_status_register.py']
DESCRIPTION = "every colour named, and every name used: the icon builder's unread palette keys and constants go"

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest.
SUITES = [("run_tests.py -- what both CI workflows run",
           [sys.executable, "run_tests.py"])]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': 'a25e73acb05f7498f1e3a9520ac4d5470fb50dc629deac7113759ee13502a25b', '.github/workflows/tests-windows.yml': 'eeb17b6a4fb8ba4a92b9ee6b182b16614bda3266c8a3e12da21cefc2f808ebd0'}

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py", "theme_manager.py", "preview_utils.py", "context_preview.py", "test_rnv_icon_builder.py"}

LEFT_ALONE = ["the ICO analyzer's dark green on a PNG row: set on the cell and never drawn, because the table's stylesheet colours every cell. Not named, since a name for it would paint nothing; listed in the guard as held. Drawing the mark, or dropping the line, is a ruling of its own.", "the colours a generated manifest and browserconfig declare, the fill and border a generated icon starts with, and what a preview background choice is called: data, each listed with its reason in the guard's DATA table.", "OS_SIM_COLORS: the simulated chrome of other systems, fixed values that do not follow the application's theme. The grounds made from it are named; its entries are as written.", "image mode's entries as KEYS: they come through the spread with dark's values, read where image mode reads them and unwritten where it does not.", "clear: 'transparent', alpha 0 and Qt's transparent are how a widget is told to paint nothing, and are left as written.", 'the stay-removed tests of earlier rounds: each restricts a name that was ruled away, and is not a list of what is unused.']


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/colors.py',
             "DARK_THEME_COLORS: Final[dict[str, str]] = {\n    # Base colors\n    'window_bg': TRUE_BLACK,\n    'panel_bg': BRAND_BLACK,\n    'card_bg': APP_CARD,\n    'input_bg': BRAND_BLACK,\n    'hover_bg': APP_PANEL_HOVER,\n    'pressed_bg': APP_BORDER,\n    'selected_bg': BRAND_GOLD,\n    \n    # Text colors\n    'text_primary': APP_TEXT,\n    'text_secondary': GREY_88,\n    'text_muted': GREY_88,\n    'text_disabled': GREY_55,\n    'accent_hover': BRAND_GOLD_HOVER,\n    'text_accent': BRAND_GOLD,\n    'text_on_accent': TRUE_BLACK,\n    \n    # Border colors\n    'border_default': APP_BORDER,\n    'border_focus': BRAND_GOLD,\n    'border_hover': GREY_44,\n    'border_accent': BRAND_GOLD,\n    'input_border': APP_BORDER,\n    \n    # Button colors (dialog buttons - gold accent system)\n    'dialog_btn_bg': APP_CARD,\n    'dialog_btn_hover_bg': APP_PANEL_HOVER,\n    'dialog_btn_pressed_bg': BRAND_GOLD,\n    'dialog_btn_text': APP_TEXT,\n    'dialog_btn_hover_text': BRAND_GOLD,\n    'dialog_btn_pressed_text': TRUE_BLACK,\n    'dialog_btn_border': APP_BORDER,\n    'dialog_btn_hover_border': BRAND_GOLD,\n\n    # Main window buttons - color inverse system (no brand gold)\n    # Dark: rest=#1a1a1a bg / hover=#333333 bg / pressed=#444444 bg\n    'main_btn_bg': BRAND_BLACK,\n    'main_btn_text': APP_TEXT,\n    'main_btn_border': APP_BORDER,\n    'main_btn_hover_bg': APP_BORDER,\n    'main_btn_hover_text': APP_TEXT,\n    'main_btn_pressed_bg': GREY_44,\n    'main_btn_pressed_text': TRUE_BLACK,\n\n    # Accent button (gold border)\n    'dialog_btn_accent_bg': APP_CARD,\n    'dialog_btn_accent_text': BRAND_GOLD,\n    'dialog_btn_accent_border': BRAND_GOLD,\n    'dialog_btn_accent_hover_bg': APP_BORDER,\n    'dialog_btn_accent_pressed_bg': BRAND_GOLD,\n    'dialog_btn_accent_pressed_text': TRUE_BLACK,\n    \n    # Platform button\n    # RNV-COLLAPSE-252525 (2026-09-02): was #252525, a value a third of\n    # the way from panel to card and on neither ladder nor grid. Ruled\n    # onto the card rung. Image mode inherits this through the splat.\n    'platform_btn_bg': APP_CARD,\n    'platform_btn_hover_bg': APP_BORDER,\n    \n    # Clear/subtle button\n    'clear_btn_bg': APP_CARD,\n    \n    # Checkbox\n    'checkbox_bg': APP_CARD,\n    'checkbox_border': GREY_55,\n    'checkbox_checked_bg': BRAND_GOLD,\n    'checkbox_checked_border': BRAND_GOLD,\n    'checkbox_hover_border': BRAND_GOLD,\n    \n    # Tab widget\n    'tab_bg': APP_CARD,\n    'tab_selected_bg': APP_BORDER,\n    'tab_hover_bg': APP_BORDER,\n    'tab_border': APP_BORDER,\n    'tab_indicator': BRAND_GOLD,\n    \n    # Scrollbar\n    'scrollbar_bg': APP_CARD,   # was #252525, see platform_btn_bg\n    'scrollbar_handle': GREY_44,\n    'scrollbar_handle_hover': BRAND_GOLD,\n    'scrollbar_border': APP_BORDER,\n    \n    # List/Table\n    'list_bg': BRAND_BLACK,\n    'list_alt_bg': APP_CARD,   # was #252525, see platform_btn_bg\n    'list_selected_bg': BRAND_GOLD,\n    'list_hover_bg': APP_PANEL_HOVER,\n    'list_header_bg': APP_CARD,\n    'list_grid': APP_BORDER,\n    \n    # Dialog\n    'dialog_bg': BRAND_BLACK,\n    'dialog_border': APP_BORDER,\n    \n    # Status bar\n    'statusbar_bg': BRAND_BLACK,\n    'statusbar_border': APP_BORDER,\n    \n    # Drop zone\n    'dropzone_bg': BRAND_BLACK,\n    'dropzone_border': APP_BORDER,\n    'dropzone_active_bg': translucent(BRAND_GOLD, DROPZONE_ALPHA_DARK),\n    \n    # Tooltip\n    'tooltip_bg': APP_CARD,\n    'tooltip_border': BRAND_GOLD,\n    'tooltip_text': APP_TEXT,\n    \n    # Success/Warning/Error\n    # RNV-STATUS-FAMILY: the fills, unwired. Both keys are looked\n    # up nowhere in this application and are on the dead-key list;\n    # whether they should exist is a separate question. If either\n    # is ever painted as TEXT it must take the _TEXT variant\n    # instead -- a fill sits at L* 48-59 and cannot reach 4.5:1.\n    'success': STATUS_SUCCESS,\n    'warning': STATUS_WARNING,\n    # RNV-STATUS-FAMILY: the watcher's label is TEXT, and a module\n    # constant cannot know which mode it is being painted in.\n    'status_active': STATUS_SUCCESS_TEXT,\n}\n\n\n",
             "DARK_THEME_COLORS: Final[dict[str, str]] = {\n    # Base colors\n    'window_bg': TRUE_BLACK,\n    'panel_bg': BRAND_BLACK,\n    'card_bg': APP_CARD,\n    'input_bg': BRAND_BLACK,\n    'pressed_bg': APP_BORDER,\n    'selected_bg': BRAND_GOLD,\n    \n    # Text colors\n    'text_primary': APP_TEXT,\n    'text_secondary': GREY_88,\n    'text_muted': GREY_88,\n    'text_disabled': GREY_55,\n    'accent_hover': BRAND_GOLD_HOVER,\n    'text_accent': BRAND_GOLD,\n    'text_on_accent': TRUE_BLACK,\n    \n    # Border colors\n    'border_default': APP_BORDER,\n    'border_focus': BRAND_GOLD,\n    'border_hover': GREY_44,\n    'border_accent': BRAND_GOLD,\n    'input_border': APP_BORDER,\n    \n    # Button colors (dialog buttons - gold accent system)\n    'dialog_btn_bg': APP_CARD,\n    'dialog_btn_hover_bg': APP_PANEL_HOVER,\n    'dialog_btn_pressed_bg': BRAND_GOLD,\n    'dialog_btn_text': APP_TEXT,\n    'dialog_btn_hover_text': BRAND_GOLD,\n    'dialog_btn_pressed_text': TRUE_BLACK,\n    'dialog_btn_border': APP_BORDER,\n    'dialog_btn_hover_border': BRAND_GOLD,\n\n    # Main window buttons - color inverse system (no brand gold)\n    # Dark: rest=#1a1a1a bg / hover=#333333 bg / pressed=#444444 bg\n    'main_btn_bg': BRAND_BLACK,\n    'main_btn_text': APP_TEXT,\n    'main_btn_border': APP_BORDER,\n    'main_btn_hover_bg': APP_BORDER,\n    'main_btn_hover_text': APP_TEXT,\n    'main_btn_pressed_bg': GREY_44,\n    'main_btn_pressed_text': TRUE_BLACK,\n\n    # Accent button (gold border)\n    'dialog_btn_accent_bg': APP_CARD,\n    'dialog_btn_accent_text': BRAND_GOLD,\n    'dialog_btn_accent_border': BRAND_GOLD,\n    'dialog_btn_accent_hover_bg': APP_BORDER,\n    'dialog_btn_accent_pressed_bg': BRAND_GOLD,\n    'dialog_btn_accent_pressed_text': TRUE_BLACK,\n    \n    # Platform button\n    # RNV-COLLAPSE-252525 (2026-09-02): was #252525, a value a third of\n    # the way from panel to card and on neither ladder nor grid. Ruled\n    # onto the card rung. Image mode inherits this through the splat.\n    'platform_btn_bg': APP_CARD,\n    'platform_btn_hover_bg': APP_BORDER,\n    \n    # Clear/subtle button\n    'clear_btn_bg': APP_CARD,\n    \n    # Checkbox\n    'checkbox_bg': APP_CARD,\n    'checkbox_border': GREY_55,\n    'checkbox_checked_bg': BRAND_GOLD,\n    'checkbox_checked_border': BRAND_GOLD,\n    'checkbox_hover_border': BRAND_GOLD,\n    \n    # Tab widget\n    'tab_bg': APP_CARD,\n    'tab_selected_bg': APP_BORDER,\n    'tab_hover_bg': APP_BORDER,\n    'tab_indicator': BRAND_GOLD,\n    \n    # Scrollbar\n    'scrollbar_bg': APP_CARD,   # was #252525, see platform_btn_bg\n    'scrollbar_handle': GREY_44,\n    'scrollbar_handle_hover': BRAND_GOLD,\n    'scrollbar_border': APP_BORDER,\n    \n    # List/Table\n    'list_bg': BRAND_BLACK,\n    'list_alt_bg': APP_CARD,   # was #252525, see platform_btn_bg\n    'list_selected_bg': BRAND_GOLD,\n    'list_hover_bg': APP_PANEL_HOVER,\n    'list_header_bg': APP_CARD,\n    'list_grid': APP_BORDER,\n    \n    # Dialog\n    'dialog_bg': BRAND_BLACK,\n    \n    # Drop zone, while a file is dragged over it. RNV-NAMED-AND-USED\n    # (2026-10-04): the drop zone's and the status bar's ground and edge\n    # stood here too. Dark and light never read them from a palette -- the\n    # main window writes those two widgets from the theme it holds -- so\n    # they are in IMAGE_MODE_COLORS alone, which is where they are read.\n    'dropzone_active_bg': translucent(BRAND_GOLD, DROPZONE_ALPHA_DARK),\n    \n    # Tooltip\n    'tooltip_bg': APP_CARD,\n    'tooltip_border': BRAND_GOLD,\n    'tooltip_text': APP_TEXT,\n    \n    # Status\n    # RNV-STATUS-FAMILY: the watcher's label is TEXT, and a module\n    # constant cannot know which mode it is being painted in.\n    'status_active': STATUS_SUCCESS_TEXT,\n}\n\n\n")
    tree.sub('ui/colors.py',
             "LIGHT_THEME_COLORS: Final[dict[str, str]] = {\n    # Base colors\n    'window_bg': APP_SURFACE_LIGHT_3,\n    'panel_bg': APP_SURFACE_LIGHT_3,\n    'card_bg': WHITE,\n    'input_bg': WHITE,\n    'hover_bg': APP_HOVER_LIGHT,\n    'pressed_bg': APP_PRESSED_LIGHT,\n    'selected_bg': BRAND_DARK_GOLD,\n    \n    # Text colors\n    'text_primary': TRUE_BLACK,\n    'text_secondary': GREY_66,\n    'text_muted': GREY_66,\n    'text_disabled': APP_TEXT_DIM,\n    'accent_hover': BRAND_DARK_GOLD_DEEP,\n    'text_accent': BRAND_DARK_GOLD_DEEP,\n    'text_on_accent': WHITE,\n    \n    # Border colors\n    'border_default': GREY_CC,\n    'border_focus': BRAND_DARK_GOLD,\n    'border_hover': APP_TEXT_DIM,\n    'border_accent': BRAND_DARK_GOLD,\n    'input_border': GREY_CC,\n    \n    # Button colors (dialog buttons - gold accent system)\n    'dialog_btn_bg': WHITE,\n    'dialog_btn_hover_bg': APP_HOVER_LIGHT,\n    'dialog_btn_pressed_bg': BRAND_DARK_GOLD,\n    'dialog_btn_text': TRUE_BLACK,\n    'dialog_btn_hover_text': BRAND_DARK_GOLD_DEEP,\n    'dialog_btn_pressed_text': WHITE,\n    'dialog_btn_border': GREY_CC,\n    'dialog_btn_hover_border': BRAND_DARK_GOLD,\n\n    # Main window buttons - color inverse system (no brand gold)\n    # Light: rest=#ffffff bg / hover=#333333 bg / pressed=#444444 bg\n    'main_btn_bg': WHITE,\n    'main_btn_text': TRUE_BLACK,\n    'main_btn_border': GREY_CC,\n    'main_btn_hover_bg': APP_BORDER,\n    'main_btn_hover_text': TRUE_BLACK,\n    'main_btn_pressed_bg': GREY_44,\n    'main_btn_pressed_text': WHITE,\n\n    # Accent button (gold border)\n    'dialog_btn_accent_bg': WHITE,\n    'dialog_btn_accent_text': BRAND_DARK_GOLD_DEEP,\n    'dialog_btn_accent_border': BRAND_DARK_GOLD,\n    'dialog_btn_accent_hover_bg': APP_HOVER_LIGHT,\n    'dialog_btn_accent_pressed_bg': BRAND_DARK_GOLD,\n    'dialog_btn_accent_pressed_text': WHITE,\n    \n    # Platform button\n    'platform_btn_bg': APP_SURFACE_LIGHT_2,   # was #fafafa, collapsed onto #fbfbfb\n    'platform_btn_hover_bg': APP_HOVER_LIGHT,   # was #f0f0f0, collapsed onto #eeeeee\n    \n    # Clear/subtle button\n    'clear_btn_bg': APP_SURFACE_LIGHT_3,\n    \n    # Checkbox\n    'checkbox_bg': WHITE,\n    'checkbox_border': APP_TEXT_DIM,\n    'checkbox_checked_bg': BRAND_DARK_GOLD,\n    'checkbox_checked_border': BRAND_DARK_GOLD,\n    'checkbox_hover_border': BRAND_DARK_GOLD,\n    \n    # Tab widget\n    'tab_bg': GREY_E0,\n    'tab_selected_bg': WHITE,\n    'tab_hover_bg': APP_HOVER_LIGHT,\n    'tab_border': GREY_CC,\n    'tab_indicator': BRAND_DARK_GOLD,\n    \n    # Scrollbar\n    'scrollbar_bg': GREY_E0,\n    'scrollbar_handle': APP_TEXT_DIM,\n    'scrollbar_handle_hover': BRAND_DARK_GOLD,\n    'scrollbar_border': GREY_CC,\n    \n    # List/Table\n    'list_bg': WHITE,\n    'list_alt_bg': APP_SURFACE_LIGHT_2,   # was #f8f8f8, collapsed onto #fbfbfb\n    'list_selected_bg': BRAND_DARK_GOLD,\n    'list_hover_bg': APP_HOVER_LIGHT,\n    'list_header_bg': GREY_EE,   # was #f0f0f0, collapsed onto #eeeeee\n    'list_grid': GREY_DD,\n    \n    # Dialog\n    'dialog_bg': APP_SURFACE_LIGHT_3,\n    'dialog_border': GREY_CC,\n    \n    # Status bar\n    'statusbar_bg': APP_SURFACE_LIGHT_3,\n    'statusbar_border': GREY_CC,\n    \n    # Drop zone\n    'dropzone_bg': WHITE,\n    'dropzone_border': GREY_CC,\n    'dropzone_active_bg': translucent(BRAND_GOLD, DROPZONE_ALPHA_LIGHT),\n    \n    # Tooltip\n    'tooltip_bg': WHITE,\n    'tooltip_border': BRAND_DARK_GOLD,\n    'tooltip_text': TRUE_BLACK,\n    \n    # Success/Warning/Error\n    # RNV-STATUS-FAMILY: light's own siblings. This palette held\n    # the dark values, which as text on #f5f5f5 read 2.87 and 1.50.\n    'success': STATUS_SUCCESS,\n    'warning': STATUS_WARNING,\n    'status_active': STATUS_SUCCESS_TEXT_LIGHT,\n}\n\n\n",
             "LIGHT_THEME_COLORS: Final[dict[str, str]] = {\n    # Base colors\n    'window_bg': APP_SURFACE_LIGHT_3,\n    'panel_bg': APP_SURFACE_LIGHT_3,\n    'card_bg': WHITE,\n    'input_bg': WHITE,\n    'pressed_bg': APP_PRESSED_LIGHT,\n    'selected_bg': BRAND_DARK_GOLD,\n    \n    # Text colors\n    'text_primary': TRUE_BLACK,\n    'text_secondary': GREY_66,\n    'text_muted': GREY_66,\n    'text_disabled': APP_TEXT_DIM,\n    'accent_hover': BRAND_DARK_GOLD_DEEP,\n    'text_accent': BRAND_DARK_GOLD_DEEP,\n    'text_on_accent': WHITE,\n    \n    # Border colors\n    'border_default': GREY_CC,\n    'border_focus': BRAND_DARK_GOLD,\n    'border_hover': APP_TEXT_DIM,\n    'border_accent': BRAND_DARK_GOLD,\n    'input_border': GREY_CC,\n    \n    # Button colors (dialog buttons - gold accent system)\n    'dialog_btn_bg': WHITE,\n    'dialog_btn_hover_bg': APP_HOVER_LIGHT,\n    'dialog_btn_pressed_bg': BRAND_DARK_GOLD,\n    'dialog_btn_text': TRUE_BLACK,\n    'dialog_btn_hover_text': BRAND_DARK_GOLD_DEEP,\n    'dialog_btn_pressed_text': WHITE,\n    'dialog_btn_border': GREY_CC,\n    'dialog_btn_hover_border': BRAND_DARK_GOLD,\n\n    # Main window buttons - color inverse system (no brand gold)\n    # Light: rest=#ffffff bg / hover=#333333 bg / pressed=#444444 bg\n    'main_btn_bg': WHITE,\n    'main_btn_text': TRUE_BLACK,\n    'main_btn_border': GREY_CC,\n    'main_btn_hover_bg': APP_BORDER,\n    'main_btn_hover_text': TRUE_BLACK,\n    'main_btn_pressed_bg': GREY_44,\n    'main_btn_pressed_text': WHITE,\n\n    # Accent button (gold border)\n    'dialog_btn_accent_bg': WHITE,\n    'dialog_btn_accent_text': BRAND_DARK_GOLD_DEEP,\n    'dialog_btn_accent_border': BRAND_DARK_GOLD,\n    'dialog_btn_accent_hover_bg': APP_HOVER_LIGHT,\n    'dialog_btn_accent_pressed_bg': BRAND_DARK_GOLD,\n    'dialog_btn_accent_pressed_text': WHITE,\n    \n    # Platform button\n    'platform_btn_bg': APP_SURFACE_LIGHT_2,   # was #fafafa, collapsed onto #fbfbfb\n    'platform_btn_hover_bg': APP_HOVER_LIGHT,   # was #f0f0f0, collapsed onto #eeeeee\n    \n    # Clear/subtle button\n    'clear_btn_bg': APP_SURFACE_LIGHT_3,\n    \n    # Checkbox\n    'checkbox_bg': WHITE,\n    'checkbox_border': APP_TEXT_DIM,\n    'checkbox_checked_bg': BRAND_DARK_GOLD,\n    'checkbox_checked_border': BRAND_DARK_GOLD,\n    'checkbox_hover_border': BRAND_DARK_GOLD,\n    \n    # Tab widget\n    'tab_bg': GREY_E0,\n    'tab_selected_bg': WHITE,\n    'tab_hover_bg': APP_HOVER_LIGHT,\n    'tab_indicator': BRAND_DARK_GOLD,\n    \n    # Scrollbar\n    'scrollbar_bg': GREY_E0,\n    'scrollbar_handle': APP_TEXT_DIM,\n    'scrollbar_handle_hover': BRAND_DARK_GOLD,\n    'scrollbar_border': GREY_CC,\n    \n    # List/Table\n    'list_bg': WHITE,\n    'list_alt_bg': APP_SURFACE_LIGHT_2,   # was #f8f8f8, collapsed onto #fbfbfb\n    'list_selected_bg': BRAND_DARK_GOLD,\n    'list_hover_bg': APP_HOVER_LIGHT,\n    'list_header_bg': GREY_EE,   # was #f0f0f0, collapsed onto #eeeeee\n    'list_grid': GREY_DD,\n    \n    # Dialog\n    'dialog_bg': APP_SURFACE_LIGHT_3,\n    \n    # Drop zone, while a file is dragged over it\n    'dropzone_active_bg': translucent(BRAND_GOLD, DROPZONE_ALPHA_LIGHT),\n    \n    # Tooltip\n    'tooltip_bg': WHITE,\n    'tooltip_border': BRAND_DARK_GOLD,\n    'tooltip_text': TRUE_BLACK,\n    \n    # Status: light's own sibling of the watcher's label.\n    'status_active': STATUS_SUCCESS_TEXT_LIGHT,\n}\n\n\n")
    tree.sub('ui/colors.py',
             "IMAGE_MODE_COLORS: Final[dict[str, str]] = {\n    **DARK_THEME_COLORS,\n    # Override with transparent backgrounds\n    'window_bg': translucent(BRAND_BLACK, SCRIM_ALPHA),\n    'panel_bg': translucent(BRAND_BLACK, SCRIM_ALPHA),\n    'card_bg': translucent(APP_CARD, SCRIM_ALPHA),\n    'input_bg': translucent(APP_CARD, SCRIM_ALPHA),\n    'dropzone_bg': translucent(BRAND_BLACK, SCRIM_ALPHA),\n    'scrollbar_bg': 'transparent',\n    # RNV-COLLAPSE-505050 closed here, 2026-09-24. This read\n    # rgba(80, 80, 80, 150) -- #505050 at 150 -- which the 2026-09-02\n    # ruling collapsed onto GREY_44 and which survived because the alpha\n    # form was written out and no sweep in the fleet decodes rgba().\n    # Composites to #333333 on the image ground, where #505050 gave\n    # #3a3a3a: a 2.26 CIEDE2000 step, rendered before it was ruled.\n    'scrollbar_handle': translucent(GREY_44, SCROLLBAR_HANDLE_ALPHA),\n    'scrollbar_handle_hover': BRAND_GOLD,\n    'scrollbar_border': translucent(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n}\n\n\n",
             "IMAGE_MODE_COLORS: Final[dict[str, str]] = {\n    **DARK_THEME_COLORS,\n    # Override with transparent backgrounds.\n    # RNV-NAMED-AND-USED (2026-10-04): a card_bg override stood here, the\n    # card at the scrim's alpha. Nothing in image mode read it: every reader\n    # of card_bg takes the dark or the light palette.\n    'window_bg': translucent(BRAND_BLACK, SCRIM_ALPHA),\n    'panel_bg': translucent(BRAND_BLACK, SCRIM_ALPHA),\n    'input_bg': translucent(APP_CARD, SCRIM_ALPHA),\n    'scrollbar_bg': 'transparent',\n    # RNV-COLLAPSE-505050 closed here, 2026-09-24. This read\n    # rgba(80, 80, 80, 150) -- #505050 at 150 -- which the 2026-09-02\n    # ruling collapsed onto GREY_44 and which survived because the alpha\n    # form was written out and no sweep in the fleet decodes rgba().\n    # Composites to #333333 on the image ground, where #505050 gave\n    # #3a3a3a: a 2.26 CIEDE2000 step, rendered before it was ruled.\n    'scrollbar_handle': translucent(GREY_44, SCROLLBAR_HANDLE_ALPHA),\n    'scrollbar_handle_hover': BRAND_GOLD,\n    'scrollbar_border': translucent(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n    # RNV-NAMED-AND-USED (2026-10-04). The drop zone and the status bar: the\n    # four keys image mode alone reads, in the one palette they are read\n    # from. The ground of the drop zone is the scrim, as it was; the other\n    # three came through the spread from dark, at these values.\n    'dropzone_bg': translucent(BRAND_BLACK, SCRIM_ALPHA),\n    'dropzone_border': APP_BORDER,\n    'statusbar_bg': BRAND_BLACK,\n    'statusbar_border': APP_BORDER,\n}\n\n\n")
    tree.sub('ui/colors.py',
             'BRAND_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_GOLD)\n"""Brand gold as an RGB tuple, derived from the hex above.\n\nDerived rather than written down: a hardcoded tuple is invisible to every\nhex-based search, so it survives sweeps that catch every other reference.\n"""\n\nBRAND_DARK_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_DARK_GOLD)\n"""Brand dark gold as an RGB tuple, derived from the hex above."""\n',
             '# RNV-NAMED-AND-USED (2026-10-04): the two golds as integer triples stood\n# here, and nothing in the application read either. _to_rgb() above still\n# derives a triple where one is needed.\n')
    tree.sub('ui/colors.py',
             'STATUS_SUCCESS: Final[str] = "#926c89"\n"""MIRRORS the register\'s STATUS["success"]. A FILL.\n\nRNV-STATUS-FAMILY (2026-09-03): was #28a745, Bootstrap\'s green. Retired\nbecause it and Bootstrap\'s red collapsed to one olive under deuteranopia at\nabout 4 apart -- success and error are the two most consequential colours in\nan interface, and roughly 8% of men could not tell them apart.\n\nIt is a FILL and cannot carry text: 3.92 on #1a1a1a, 3.23 on #2a2a2a, above\nthe 3:1 fill floor and below the 4.5:1 text floor. That is not a shortcoming,\nit is the fill band -- a value that works on a dark AND a light ground sits at\nL* 48-59 by arithmetic, and a mid-tone reaches 4.5 on neither side.\n\nRNV-STATUS-REGISTER (2026-09-02): both palettes already held this value,\nwritten out rather than named. Named here so it has one home. Defined above\nthe palettes because they consume it.\n"""\n\nSTATUS_WARNING: Final[str] = "#a2703c"\n"""MIRRORS the register\'s STATUS["warning"]. A FILL.\n\nRNV-STATUS-FAMILY (2026-09-03): was #ffc107, retired on arithmetic rather\nthan taste -- it read 1.63 on #ffffff and 1.49 on #f5f5f5 against a 3:1 fill\nfloor, so it could not legally carry a boundary on a light ground at all.\n"""\n\n',
             "# RNV-NAMED-AND-USED (2026-10-04): the family's two fills, success and\n# warning, stood here, and the warning's two text values beside the\n# success text below. This application draws one status colour, the\n# folder watcher's label, as TEXT; nothing read the fills or the warning\n# text, so it carries none of them. The register holds the family.\n\n")
    tree.sub('ui/colors.py',
             'STATUS_SUCCESS_TEXT: Final[str] = "#ad85a3"\nSTATUS_WARNING_TEXT: Final[str] = "#bc8752"\n"""MIRROR the register\'s STATUS["success-text"] and ["warning-text"].\nTEXT on a dark ground: 4.55 and 4.60 on APP card #2a2a2a.\n',
             'STATUS_SUCCESS_TEXT: Final[str] = "#ad85a3"\n"""MIRRORS the register\'s STATUS["success-text"].\nTEXT on a dark ground: 4.55 on APP card #2a2a2a.\n')
    tree.sub('ui/colors.py',
             'STATUS_SUCCESS_TEXT_LIGHT: Final[str] = "#825d79"\nSTATUS_WARNING_TEXT_LIGHT: Final[str] = "#8e5e2b"\n"""MIRROR the register\'s STATUS["*-text-light"]. TEXT on a light ground:\n4.52 on #f5f5f5, this application\'s light dialog background.\n',
             'STATUS_SUCCESS_TEXT_LIGHT: Final[str] = "#825d79"\n"""MIRRORS the register\'s STATUS["success-text-light"]. TEXT on a light\nground: 4.52 on #f5f5f5, this application\'s light dialog background.\n')
    tree.sub('ui/colors.py',
             'STATUS_ACTIVE_COLOR: Final[str] = STATUS_SUCCESS_TEXT\n"""The folder watcher, running. RNV-STATUS-REGISTER (2026-09-02): was\n#4caf50, Material\'s green, where the register publishes #28a745 and where\nrnv-color-picker\'s identically-named constant already used the register\'s.\nTwo applications, one role, two greens; ruled onto one.\n\nRNV-STATUS-FAMILY (2026-09-03): this constant is no longer what\ngets painted. ui/settings_dialog.py wrote `color: {STATUS_ACTIVE_COLOR}`\non the watch label -- TEXT, in a dialog that runs in three modes --\nand a module-level constant does not know which mode it is in. One\nvalue cannot be legal on all three grounds: the dark text variant\nreads 5.52 on #1a1a1a and 3.15 on #ffffff. The palettes now carry a\n`status_active` key resolved per mode, and the call site reads the\ntheme it was already holding. This constant remains as the\nREGISTER-FACING alias below, which is what it was always for.\n\nAND IT NOW ALIASES success-text RATHER THAN success, ruled by the\nregister 2026-09-04. It pointed at the FILL, which was safe only by\naccident: Bootstrap\'s green read 5.55 on BRAND_BLACK and doubled as\ntext. The RNV fills are mid-tones by design and #926c89 reads 3.91\nthere, so the alias would have failed the 4.5 text floor on the day\nthe family landed. An alias onto a fill is a fill used as text.\n\nIt is an ALIAS rather than a copy because "running" is not "succeeded" and\nthe register has no name for the first. If status-active is ever\nregistered, this line is the only one that moves.\n"""\n\n\n',
             "# RNV-NAMED-AND-USED (2026-10-04): an alias for the running folder watcher's\n# colour stood here. Since 2026-09-03 the label reads the palettes'\n# status_active, resolved per mode, and nothing read the alias.\n\n\n")
    tree.sub('ui/colors.py',
             "    'BRAND_GOLD_RGB',\n    'BRAND_DARK_GOLD_RGB',\n",
             '')
    tree.sub('ui/colors.py',
             "    'STATUS_SUCCESS',\n    'STATUS_WARNING',\n    'STATUS_SUCCESS_TEXT',\n    'STATUS_WARNING_TEXT',\n    'STATUS_SUCCESS_TEXT_LIGHT',\n    'STATUS_WARNING_TEXT_LIGHT',\n    'STATUS_ACTIVE_COLOR',\n]\n",
             "    'STATUS_SUCCESS_TEXT',\n    'STATUS_SUCCESS_TEXT_LIGHT',\n    'OS_SIM_GROUNDS_RGB',\n    'PREVIEW_CHECKER_LIGHT',\n    'PREVIEW_CHECKER_DARK',\n    'PREVIEW_GROUND_WHITE',\n    'PREVIEW_GROUND_BLACK',\n    'DEFAULT_CUSTOM_BG_RGB',\n    'PREVIEW_MISSING_FILL',\n]\n")
    tree.sub('ui/colors.py',
             "    'desktop_icon_text':         '#ffffff',\n    'desktop_icon_label_bg':     'rgba(0,0,0,0.3)',\n}\n",
             '    \'desktop_icon_text\':         \'#ffffff\',\n    \'desktop_icon_label_bg\':     \'rgba(0,0,0,0.3)\',\n}\n\nOS_SIM_GROUNDS_RGB: Final[dict[str, tuple[int, int, int]]] = {\n    key: _to_rgb(OS_SIM_COLORS[key]) for key in (\n        \'taskbar_dark_bg\', \'taskbar_light_bg\', \'explorer_bg\', \'finder_bg\',\n        \'chrome_active_tab_bg\', \'bookmarks_bg\',\n    )\n}\n"""The simulated grounds an icon is composited onto, as the RGB tuples PIL\ntakes. Made from OS_SIM_COLORS, so the ground behind an icon and the ground\nof the widget it sits in are one value.\n\nRNV-NAMED-AND-USED (2026-10-04): each was written out as a tuple beside the\nwidget that read the entry above -- (32, 32, 32), (240, 240, 240),\n(255, 255, 255) twice, (245, 245, 245) and (248, 249, 250)."""\n')
    tree.sub('ui/colors.py',
             'DEFAULT_CUSTOM_BG_COLOR: Final[str] = "#808080"\n"""Default custom preview background color (neutral gray starting value)"""\n',
             'DEFAULT_CUSTOM_BG_COLOR: Final[str] = "#808080"\n"""Default custom preview background color (neutral gray starting value)"""\n\nDEFAULT_CUSTOM_BG_RGB: Final[tuple[int, int, int]] = _to_rgb(DEFAULT_CUSTOM_BG_COLOR)\n"""The same starting grey as the tuple the background selector holds.\nRNV-NAMED-AND-USED (2026-10-04): the selector wrote (128, 128, 128) out\nbeside the name above, which nothing read. It reads this."""\n\n# ==================== Preview Grounds ====================\n# RNV-NAMED-AND-USED (2026-10-04). Ruled: "As long as a color exist in the\n# app it should be named and used no hardcoded or pointless literals should\n# exist". What a preview is composited onto and the fill of a size that is\n# missing were written out where they are used.\n# Each is named here at the value it had: NO PIXEL MOVES. One whose value is\n# a colour this file already names is LINKED to that name; one with a value\n# of its own holds it, and is this application\'s alone. PIL takes a tuple\n# for a ground, so the grounds are tuples.\n\nPREVIEW_CHECKER_LIGHT: Final[tuple[int, int, int]] = _to_rgb(WHITE)\n"""The transparency checkerboard\'s light square. Was (255, 255, 255): linked."""\n\nPREVIEW_CHECKER_DARK: Final[tuple[int, int, int]] = _to_rgb(GREY_CC)\n"""Its dark square. Was (204, 204, 204), which is GREY_CC: linked."""\n\nPREVIEW_GROUND_WHITE: Final[tuple[int, int, int]] = _to_rgb(WHITE)\n"""The "White" preview background, and what an image is composited onto\nwhen no ground is given. Was (255, 255, 255): linked."""\n\nPREVIEW_GROUND_BLACK: Final[tuple[int, int, int]] = _to_rgb(TRUE_BLACK)\n"""The "Black" preview background. Was (0, 0, 0): linked."""\n\nPREVIEW_MISSING_FILL: Final[str] = "#c8c8c8"\n"""The grey a size with no image of its own is previewed as. Was\n(200, 200, 200, 255), which PIL reads this as. App-owned."""\n')
    tree.sub('ui/__init__.py',
             '    BRAND_GOLD, BRAND_DARK_GOLD,\n    BRAND_GOLD_RGB, BRAND_DARK_GOLD_RGB,\n',
             '    BRAND_GOLD, BRAND_DARK_GOLD,\n')
    tree.sub('ui/__init__.py',
             "    'BRAND_GOLD', 'BRAND_DARK_GOLD',\n    'BRAND_GOLD_RGB', 'BRAND_DARK_GOLD_RGB',\n",
             "    'BRAND_GOLD', 'BRAND_DARK_GOLD',\n")
    tree.sub('ui/theme_manager.py',
             "        **{k: DARK_THEME_COLORS[k] for k in (\n            'window_bg', 'text_primary', 'border_default', 'hover_bg',\n            'checkbox_bg', 'checkbox_border',\n",
             "        **{k: DARK_THEME_COLORS[k] for k in (\n            'window_bg',\n")
    tree.sub('ui/theme_manager.py',
             "        'border_color': DARK_THEME_COLORS['main_btn_border'],\n        'hover_color': DARK_THEME_COLORS['hover_bg'],\n",
             "        'border_color': DARK_THEME_COLORS['main_btn_border'],\n")
    tree.sub('ui/theme_manager.py',
             "        **{k: LIGHT_THEME_COLORS[k] for k in (\n            'window_bg', 'text_primary', 'border_default', 'hover_bg',\n            'checkbox_bg', 'checkbox_border',\n",
             "        **{k: LIGHT_THEME_COLORS[k] for k in (\n            'window_bg',\n")
    tree.sub('ui/theme_manager.py',
             "        'border_color': LIGHT_THEME_COLORS['main_btn_border'],\n        'hover_color': LIGHT_THEME_COLORS['hover_bg'],\n",
             "        'border_color': LIGHT_THEME_COLORS['main_btn_border'],\n")
    tree.sub('ui/theme_manager.py',
             '    # ==================== Theme Definitions ====================\n    # Color values sourced from utils/colors.py — do not hardcode here.\n',
             '    # ==================== Theme Definitions ====================\n    # Color values sourced from utils/colors.py — do not hardcode here.\n    #\n    # RNV-NAMED-AND-USED (2026-10-04): these two are what get_current_theme()\n    # hands the main window, and they hold what the main window looks up.\n    # Five more keys were copied across and one alias made, and nothing read\n    # any of the six: the dialogs take their colours from ui/colors.py.\n')
    tree.sub('ui/preview_utils.py',
             '    contrast_ink, DARK_THEME_COLORS,\n    DEFAULT_CUSTOM_BG_COLOR,\n)\n',
             '    contrast_ink, DARK_THEME_COLORS,\n    # RNV-NAMED-AND-USED (2026-10-04): the grounds a preview is composited\n    # onto, by name. Each was an integer tuple written out in this file.\n    DEFAULT_CUSTOM_BG_RGB, PREVIEW_CHECKER_DARK, PREVIEW_CHECKER_LIGHT,\n    PREVIEW_GROUND_BLACK, PREVIEW_GROUND_WHITE,\n)\n')
    tree.sub('ui/preview_utils.py',
             '    color1: tuple[int, int, int] = (255, 255, 255),\n    color2: tuple[int, int, int] = (204, 204, 204)\n',
             '    color1: tuple[int, int, int] = PREVIEW_CHECKER_LIGHT,\n    color2: tuple[int, int, int] = PREVIEW_CHECKER_DARK\n', times=2)
    tree.sub('ui/preview_utils.py',
             '    image: Image.Image,\n    color: tuple[int, int, int] = (255, 255, 255)\n',
             '    image: Image.Image,\n    color: tuple[int, int, int] = PREVIEW_GROUND_WHITE\n')
    tree.sub('ui/preview_utils.py',
             '        return composite_on_color(image, (255, 255, 255))\n',
             '        return composite_on_color(image, PREVIEW_GROUND_WHITE)\n')
    tree.sub('ui/preview_utils.py',
             '        return composite_on_color(image, (0, 0, 0))\n',
             '        return composite_on_color(image, PREVIEW_GROUND_BLACK)\n')
    tree.sub('ui/preview_utils.py',
             '        self.custom_color: tuple[int, int, int] = (128, 128, 128)  # Gray default\n',
             '        self.custom_color: tuple[int, int, int] = DEFAULT_CUSTOM_BG_RGB  # Gray default\n')
    tree.sub('ui/context_preview.py',
             'from ui.colors import BRAND_GOLD, BRAND_DARK_GOLD, OS_SIM_COLORS, get_theme_colors\n',
             'from ui.colors import BRAND_GOLD, BRAND_DARK_GOLD, OS_SIM_COLORS, OS_SIM_GROUNDS_RGB, get_theme_colors\n')
    tree.sub('ui/context_preview.py',
             '            bg = (32, 32, 32) if dark else (240, 240, 240)\n',
             "            # RNV-NAMED-AND-USED (2026-10-04): the taskbar's own ground, by name.\n            bg = OS_SIM_GROUNDS_RGB['taskbar_dark_bg'] if dark else OS_SIM_GROUNDS_RGB['taskbar_light_bg']\n")
    tree.sub('ui/context_preview.py',
             '                # White background for explorer\n                from ui.preview_utils import composite_on_color\n                display = composite_on_color(icon_img, (255, 255, 255))\n',
             "                # White background for explorer\n                from ui.preview_utils import composite_on_color\n                display = composite_on_color(icon_img, OS_SIM_GROUNDS_RGB['explorer_bg'])\n")
    tree.sub('ui/context_preview.py',
             '                display = composite_on_color(icon_img, (245, 245, 245))\n',
             "                display = composite_on_color(icon_img, OS_SIM_GROUNDS_RGB['finder_bg'])\n")
    tree.sub('ui/context_preview.py',
             '            icon_label = QLabel()\n            from ui.preview_utils import composite_on_color\n            display = composite_on_color(icon_img, (255, 255, 255))\n',
             "            icon_label = QLabel()\n            from ui.preview_utils import composite_on_color\n            display = composite_on_color(icon_img, OS_SIM_GROUNDS_RGB['chrome_active_tab_bg'])\n")
    tree.sub('ui/context_preview.py',
             '            display = composite_on_color(icon_img, (248, 249, 250))\n',
             "            display = composite_on_color(icon_img, OS_SIM_GROUNDS_RGB['bookmarks_bg'])\n")
    tree.sub('RNV_Icon_Builder.py',
             '    DARK_THEME_COLORS, LIGHT_THEME_COLORS, IMAGE_MODE_COLORS,\n    get_theme_colors,\n)\n',
             '    DARK_THEME_COLORS, LIGHT_THEME_COLORS, IMAGE_MODE_COLORS,\n    get_theme_colors, PREVIEW_MISSING_FILL,\n)\n')
    tree.sub('RNV_Icon_Builder.py',
             '                img = Image.new("RGBA", (size, size), (200, 200, 200, 255))\n',
             '                # RNV-NAMED-AND-USED (2026-10-04): was (200, 200, 200, 255).\n                img = Image.new("RGBA", (size, size), PREVIEW_MISSING_FILL)\n')
    tree.sub('test_rnv_icon_builder.py',
             '    BRAND_GOLD, BRAND_DARK_GOLD, BRAND_GOLD_RGB, BRAND_DARK_GOLD_RGB,\n    DARK_THEME_COLORS, LIGHT_THEME_COLORS, IMAGE_MODE_COLORS,\n    get_theme_colors,\n    DEFAULT_CUSTOM_BG_COLOR, STATUS_ACTIVE_COLOR,\n',
             '    BRAND_GOLD, BRAND_DARK_GOLD, _to_rgb,\n    DARK_THEME_COLORS, LIGHT_THEME_COLORS, IMAGE_MODE_COLORS,\n    get_theme_colors,\n    DEFAULT_CUSTOM_BG_COLOR,\n')
    tree.sub('test_rnv_icon_builder.py',
             '    def test_brand_gold_rgb_tuple(self):\n        self.assertEqual(BRAND_GOLD_RGB, (210, 188, 147))\n\n    def test_brand_gold_dark_rgb_tuple(self):\n        self.assertEqual(BRAND_DARK_GOLD_RGB, (140, 115, 55))\n\n    def test_rgb_matches_hex_gold(self):\n        r, g, b = BRAND_GOLD_RGB\n        expected = f"#{r:02x}{g:02x}{b:02x}"\n        self.assertEqual(BRAND_GOLD.lower(), expected)\n\n    def test_rgb_matches_hex_gold_dark(self):\n        r, g, b = BRAND_DARK_GOLD_RGB\n',
             '    # LOCK EXCEPTION, ruled 2026-10-04 (RNV-NAMED-AND-USED). The two golds\n    # as integer triples were constants nothing in the application read,\n    # held by these four tests alone, and they went. The tests stay and\n    # take the triple from the hex, as the constants did.\n    def test_brand_gold_rgb_tuple(self):\n        self.assertEqual(_to_rgb(BRAND_GOLD), (210, 188, 147))\n\n    def test_brand_gold_dark_rgb_tuple(self):\n        self.assertEqual(_to_rgb(BRAND_DARK_GOLD), (140, 115, 55))\n\n    def test_rgb_matches_hex_gold(self):\n        r, g, b = _to_rgb(BRAND_GOLD)\n        expected = f"#{r:02x}{g:02x}{b:02x}"\n        self.assertEqual(BRAND_GOLD.lower(), expected)\n\n    def test_rgb_matches_hex_gold_dark(self):\n        r, g, b = _to_rgb(BRAND_DARK_GOLD)\n')
    tree.sub('test_rnv_icon_builder.py',
             '    def test_status_active_color_nonempty(self):\n        self.assertGreater(len(STATUS_ACTIVE_COLOR), 3)\n',
             "    def test_status_active_color_nonempty(self):\n        # LOCK EXCEPTION, ruled 2026-10-04 (RNV-NAMED-AND-USED). This read\n        # STATUS_ACTIVE_COLOR, an alias nothing painted from. The watcher's\n        # label reads status_active from the palette in force, so each\n        # palette's entry is what is held.\n        for theme in (DARK_THEME_COLORS, LIGHT_THEME_COLORS, IMAGE_MODE_COLORS):\n            self.assertGreater(len(theme['status_active']), 3)\n")
    tree.sub('test_rnv_icon_builder.py',
             '    # ── Required keys present in all theme dicts ───────────────────────────────\n    _REQUIRED_KEYS = [\n',
             '    # ── Required keys present in all theme dicts ───────────────────────────────\n    # LOCK EXCEPTION, ruled 2026-10-04 (RNV-NAMED-AND-USED): "for the locked\n    # key test if we don\'t use these values we can fix the test and remove\n    # unused values". Two status fills nothing read went from every palette,\n    # and the drop zone\'s ground and edge are in the image palette alone,\n    # the one palette they are read from.\n    _REQUIRED_KEYS = [\n')
    tree.sub('test_rnv_icon_builder.py',
             "        'dropzone_bg', 'dropzone_border', 'dropzone_active_bg',\n        'success', 'warning',\n    ]\n",
             "        'dropzone_active_bg',\n    ]\n")
    tree.sub('tests/test_brand_contrast.py',
             'DERIVED_CONSTANTS = {\n    "BRAND_DARK_GOLD_DEEP",\n    "BRAND_GOLD_RGB",\n    "BRAND_DARK_GOLD_RGB",\n}\n',
             '# RNV-NAMED-AND-USED, 2026-10-04: the two golds as triples went -- nothing\n# read them -- and the tuples the application does read took their place\n# here: the grounds a preview is composited onto, each made from the colour\n# it is.\nDERIVED_CONSTANTS = {\n    "BRAND_DARK_GOLD_DEEP",\n    "PREVIEW_CHECKER_LIGHT",\n    "PREVIEW_CHECKER_DARK",\n    "PREVIEW_GROUND_WHITE",\n    "PREVIEW_GROUND_BLACK",\n    "DEFAULT_CUSTOM_BG_RGB",\n}\n')
    tree.sub('tests/test_brand_contrast.py',
             '@pytest.mark.parametrize("const,rgb", [\n    ("BRAND_GOLD", "BRAND_GOLD_RGB"),\n    ("BRAND_DARK_GOLD", "BRAND_DARK_GOLD_RGB"),\n])\n',
             '@pytest.mark.parametrize("const,rgb", [\n    ("WHITE", "PREVIEW_CHECKER_LIGHT"),\n    ("GREY_CC", "PREVIEW_CHECKER_DARK"),\n    ("WHITE", "PREVIEW_GROUND_WHITE"),\n    ("TRUE_BLACK", "PREVIEW_GROUND_BLACK"),\n    ("DEFAULT_CUSTOM_BG_COLOR", "DEFAULT_CUSTOM_BG_RGB"),\n])\n')
    tree.sub('tests/test_brand_contrast.py',
             'NOT_BRAND_GOLD = {\n    "#a2703c": "STATUS warning -- the semantic warning colour, not brand gold. "\n               "RNV-STATUS-FAMILY (2026-09-03): it reads as gold to the r > g > b "\n               "shape test because it half IS one -- the register derives it 50% "\n               "toward BRAND_DARK_GOLD in OKLab. CIEDE2000 9.1 from that gold, "\n               "clearing the register\'s own 8.40 threshold by 0.7. Replaced "\n               "#ffc107, which sat 17.7 away and tripped only the shape test.",\n}\n\n\n',
             "# RNV-NAMED-AND-USED, 2026-10-04: empty. Its one entry was the status\n# warning, which reads as gold to the shape test below. Nothing read the\n# palettes' warning key, so the key and its colour went, and no palette\n# holds a gold-adjacent value that is not brand gold.\nNOT_BRAND_GOLD: dict[str, str] = {}\n\n\n")
    tree.sub('tests/test_derived_values.py',
             '#: Found when this was written; below the floor, the sweep has gone blind.\nLOWER8_FLOOR = 21\n',
             "#: Found when this was written; below the floor, the sweep has gone blind.\n#: 19 since RNV-NAMED-AND-USED, 2026-10-04: image mode's card_bg override,\n#: which nothing read, went, and it was counted in two modules.\nLOWER8_FLOOR = 19\n")
    tree.sub('tests/test_ladder_and_plate.py',
             "    'DARK_THEME_COLORS': ('hover_bg', 'dialog_btn_hover_bg',\n                          'list_hover_bg'),\n    'LIGHT_THEME_COLORS': ('hover_bg', 'dialog_btn_hover_bg',\n",
             "    # RNV-NAMED-AND-USED, 2026-10-04: hover_bg headed both lists. Nothing\n    # read it but two copies in the main window's palettes that nothing\n    # read either, and it went with them.\n    'DARK_THEME_COLORS': ('dialog_btn_hover_bg',\n                          'list_hover_bg'),\n    'LIGHT_THEME_COLORS': ('dialog_btn_hover_bg',\n")
    tree.sub('tests/test_light_rewalk.py',
             "REWALKED = {'STATUS_SUCCESS_TEXT_LIGHT': '#825d79', 'STATUS_WARNING_TEXT_LIGHT': '#8e5e2b'}\n",
             "# RNV-NAMED-AND-USED, 2026-10-04: the warning's light text stood beside this.\n# This application draws no warning, nothing read the value, and it went.\nREWALKED = {'STATUS_SUCCESS_TEXT_LIGHT': '#825d79'}\n")
    tree.sub('tests/snapshots.json',
             '  "dark_theme_keys": [\n    "accent_hover",\n    "border_accent",\n    "border_default",\n    "border_focus",\n    "border_hover",\n    "card_bg",\n    "checkbox_bg",\n    "checkbox_border",\n    "checkbox_checked_bg",\n    "checkbox_checked_border",\n    "checkbox_hover_border",\n    "clear_btn_bg",\n    "dialog_bg",\n    "dialog_border",\n    "dialog_btn_accent_bg",\n    "dialog_btn_accent_border",\n    "dialog_btn_accent_hover_bg",\n    "dialog_btn_accent_pressed_bg",\n    "dialog_btn_accent_pressed_text",\n    "dialog_btn_accent_text",\n    "dialog_btn_bg",\n    "dialog_btn_border",\n    "dialog_btn_hover_bg",\n    "dialog_btn_hover_border",\n    "dialog_btn_hover_text",\n    "dialog_btn_pressed_bg",\n    "dialog_btn_pressed_text",\n    "dialog_btn_text",\n    "dropzone_active_bg",\n    "dropzone_bg",\n    "dropzone_border",\n    "hover_bg",\n    "input_bg",\n    "input_border",\n    "list_alt_bg",\n    "list_bg",\n    "list_grid",\n    "list_header_bg",\n    "list_hover_bg",\n    "list_selected_bg",\n    "main_btn_bg",\n    "main_btn_border",\n    "main_btn_hover_bg",\n    "main_btn_hover_text",\n    "main_btn_pressed_bg",\n    "main_btn_pressed_text",\n    "main_btn_text",\n    "panel_bg",\n    "platform_btn_bg",\n    "platform_btn_hover_bg",\n    "pressed_bg",\n    "scrollbar_bg",\n    "scrollbar_border",\n    "scrollbar_handle",\n    "scrollbar_handle_hover",\n    "selected_bg",\n    "status_active",\n    "statusbar_bg",\n    "statusbar_border",\n    "success",\n    "tab_bg",\n    "tab_border",\n    "tab_hover_bg",\n    "tab_indicator",\n    "tab_selected_bg",\n    "text_accent",\n    "text_disabled",\n    "text_muted",\n    "text_on_accent",\n    "text_primary",\n    "text_secondary",\n    "tooltip_bg",\n    "tooltip_border",\n    "tooltip_text",\n    "warning",\n    "window_bg"\n  ],\n',
             '  "dark_theme_keys": [\n    "accent_hover",\n    "border_accent",\n    "border_default",\n    "border_focus",\n    "border_hover",\n    "card_bg",\n    "checkbox_bg",\n    "checkbox_border",\n    "checkbox_checked_bg",\n    "checkbox_checked_border",\n    "checkbox_hover_border",\n    "clear_btn_bg",\n    "dialog_bg",\n    "dialog_btn_accent_bg",\n    "dialog_btn_accent_border",\n    "dialog_btn_accent_hover_bg",\n    "dialog_btn_accent_pressed_bg",\n    "dialog_btn_accent_pressed_text",\n    "dialog_btn_accent_text",\n    "dialog_btn_bg",\n    "dialog_btn_border",\n    "dialog_btn_hover_bg",\n    "dialog_btn_hover_border",\n    "dialog_btn_hover_text",\n    "dialog_btn_pressed_bg",\n    "dialog_btn_pressed_text",\n    "dialog_btn_text",\n    "dropzone_active_bg",\n    "input_bg",\n    "input_border",\n    "list_alt_bg",\n    "list_bg",\n    "list_grid",\n    "list_header_bg",\n    "list_hover_bg",\n    "list_selected_bg",\n    "main_btn_bg",\n    "main_btn_border",\n    "main_btn_hover_bg",\n    "main_btn_hover_text",\n    "main_btn_pressed_bg",\n    "main_btn_pressed_text",\n    "main_btn_text",\n    "panel_bg",\n    "platform_btn_bg",\n    "platform_btn_hover_bg",\n    "pressed_bg",\n    "scrollbar_bg",\n    "scrollbar_border",\n    "scrollbar_handle",\n    "scrollbar_handle_hover",\n    "selected_bg",\n    "status_active",\n    "tab_bg",\n    "tab_hover_bg",\n    "tab_indicator",\n    "tab_selected_bg",\n    "text_accent",\n    "text_disabled",\n    "text_muted",\n    "text_on_accent",\n    "text_primary",\n    "text_secondary",\n    "tooltip_bg",\n    "tooltip_border",\n    "tooltip_text",\n    "window_bg"\n  ],\n')
    tree.sub('tests/snapshots.json',
             '  "light_theme_keys": [\n    "accent_hover",\n    "border_accent",\n    "border_default",\n    "border_focus",\n    "border_hover",\n    "card_bg",\n    "checkbox_bg",\n    "checkbox_border",\n    "checkbox_checked_bg",\n    "checkbox_checked_border",\n    "checkbox_hover_border",\n    "clear_btn_bg",\n    "dialog_bg",\n    "dialog_border",\n    "dialog_btn_accent_bg",\n    "dialog_btn_accent_border",\n    "dialog_btn_accent_hover_bg",\n    "dialog_btn_accent_pressed_bg",\n    "dialog_btn_accent_pressed_text",\n    "dialog_btn_accent_text",\n    "dialog_btn_bg",\n    "dialog_btn_border",\n    "dialog_btn_hover_bg",\n    "dialog_btn_hover_border",\n    "dialog_btn_hover_text",\n    "dialog_btn_pressed_bg",\n    "dialog_btn_pressed_text",\n    "dialog_btn_text",\n    "dropzone_active_bg",\n    "dropzone_bg",\n    "dropzone_border",\n    "hover_bg",\n    "input_bg",\n    "input_border",\n    "list_alt_bg",\n    "list_bg",\n    "list_grid",\n    "list_header_bg",\n    "list_hover_bg",\n    "list_selected_bg",\n    "main_btn_bg",\n    "main_btn_border",\n    "main_btn_hover_bg",\n    "main_btn_hover_text",\n    "main_btn_pressed_bg",\n    "main_btn_pressed_text",\n    "main_btn_text",\n    "panel_bg",\n    "platform_btn_bg",\n    "platform_btn_hover_bg",\n    "pressed_bg",\n    "scrollbar_bg",\n    "scrollbar_border",\n    "scrollbar_handle",\n    "scrollbar_handle_hover",\n    "selected_bg",\n    "status_active",\n    "statusbar_bg",\n    "statusbar_border",\n    "success",\n    "tab_bg",\n    "tab_border",\n    "tab_hover_bg",\n    "tab_indicator",\n    "tab_selected_bg",\n    "text_accent",\n    "text_disabled",\n    "text_muted",\n    "text_on_accent",\n    "text_primary",\n    "text_secondary",\n    "tooltip_bg",\n    "tooltip_border",\n    "tooltip_text",\n    "warning",\n    "window_bg"\n  ],\n',
             '  "light_theme_keys": [\n    "accent_hover",\n    "border_accent",\n    "border_default",\n    "border_focus",\n    "border_hover",\n    "card_bg",\n    "checkbox_bg",\n    "checkbox_border",\n    "checkbox_checked_bg",\n    "checkbox_checked_border",\n    "checkbox_hover_border",\n    "clear_btn_bg",\n    "dialog_bg",\n    "dialog_btn_accent_bg",\n    "dialog_btn_accent_border",\n    "dialog_btn_accent_hover_bg",\n    "dialog_btn_accent_pressed_bg",\n    "dialog_btn_accent_pressed_text",\n    "dialog_btn_accent_text",\n    "dialog_btn_bg",\n    "dialog_btn_border",\n    "dialog_btn_hover_bg",\n    "dialog_btn_hover_border",\n    "dialog_btn_hover_text",\n    "dialog_btn_pressed_bg",\n    "dialog_btn_pressed_text",\n    "dialog_btn_text",\n    "dropzone_active_bg",\n    "input_bg",\n    "input_border",\n    "list_alt_bg",\n    "list_bg",\n    "list_grid",\n    "list_header_bg",\n    "list_hover_bg",\n    "list_selected_bg",\n    "main_btn_bg",\n    "main_btn_border",\n    "main_btn_hover_bg",\n    "main_btn_hover_text",\n    "main_btn_pressed_bg",\n    "main_btn_pressed_text",\n    "main_btn_text",\n    "panel_bg",\n    "platform_btn_bg",\n    "platform_btn_hover_bg",\n    "pressed_bg",\n    "scrollbar_bg",\n    "scrollbar_border",\n    "scrollbar_handle",\n    "scrollbar_handle_hover",\n    "selected_bg",\n    "status_active",\n    "tab_bg",\n    "tab_hover_bg",\n    "tab_indicator",\n    "tab_selected_bg",\n    "text_accent",\n    "text_disabled",\n    "text_muted",\n    "text_on_accent",\n    "text_primary",\n    "text_secondary",\n    "tooltip_bg",\n    "tooltip_border",\n    "tooltip_text",\n    "window_bg"\n  ],\n')
    tree.sub('tests/snapshots.json',
             '  "image_mode_keys": [\n    "accent_hover",\n    "border_accent",\n    "border_default",\n    "border_focus",\n    "border_hover",\n    "card_bg",\n    "checkbox_bg",\n    "checkbox_border",\n    "checkbox_checked_bg",\n    "checkbox_checked_border",\n    "checkbox_hover_border",\n    "clear_btn_bg",\n    "dialog_bg",\n    "dialog_border",\n    "dialog_btn_accent_bg",\n    "dialog_btn_accent_border",\n    "dialog_btn_accent_hover_bg",\n    "dialog_btn_accent_pressed_bg",\n    "dialog_btn_accent_pressed_text",\n    "dialog_btn_accent_text",\n    "dialog_btn_bg",\n    "dialog_btn_border",\n    "dialog_btn_hover_bg",\n    "dialog_btn_hover_border",\n    "dialog_btn_hover_text",\n    "dialog_btn_pressed_bg",\n    "dialog_btn_pressed_text",\n    "dialog_btn_text",\n    "dropzone_active_bg",\n    "dropzone_bg",\n    "dropzone_border",\n    "hover_bg",\n    "input_bg",\n    "input_border",\n    "list_alt_bg",\n    "list_bg",\n    "list_grid",\n    "list_header_bg",\n    "list_hover_bg",\n    "list_selected_bg",\n    "main_btn_bg",\n    "main_btn_border",\n    "main_btn_hover_bg",\n    "main_btn_hover_text",\n    "main_btn_pressed_bg",\n    "main_btn_pressed_text",\n    "main_btn_text",\n    "panel_bg",\n    "platform_btn_bg",\n    "platform_btn_hover_bg",\n    "pressed_bg",\n    "scrollbar_bg",\n    "scrollbar_border",\n    "scrollbar_handle",\n    "scrollbar_handle_hover",\n    "selected_bg",\n    "status_active",\n    "statusbar_bg",\n    "statusbar_border",\n    "success",\n    "tab_bg",\n    "tab_border",\n    "tab_hover_bg",\n    "tab_indicator",\n    "tab_selected_bg",\n    "text_accent",\n    "text_disabled",\n    "text_muted",\n    "text_on_accent",\n    "text_primary",\n    "text_secondary",\n    "tooltip_bg",\n    "tooltip_border",\n    "tooltip_text",\n    "warning",\n    "window_bg"\n  ],\n',
             '  "image_mode_keys": [\n    "accent_hover",\n    "border_accent",\n    "border_default",\n    "border_focus",\n    "border_hover",\n    "card_bg",\n    "checkbox_bg",\n    "checkbox_border",\n    "checkbox_checked_bg",\n    "checkbox_checked_border",\n    "checkbox_hover_border",\n    "clear_btn_bg",\n    "dialog_bg",\n    "dialog_btn_accent_bg",\n    "dialog_btn_accent_border",\n    "dialog_btn_accent_hover_bg",\n    "dialog_btn_accent_pressed_bg",\n    "dialog_btn_accent_pressed_text",\n    "dialog_btn_accent_text",\n    "dialog_btn_bg",\n    "dialog_btn_border",\n    "dialog_btn_hover_bg",\n    "dialog_btn_hover_border",\n    "dialog_btn_hover_text",\n    "dialog_btn_pressed_bg",\n    "dialog_btn_pressed_text",\n    "dialog_btn_text",\n    "dropzone_active_bg",\n    "dropzone_bg",\n    "dropzone_border",\n    "input_bg",\n    "input_border",\n    "list_alt_bg",\n    "list_bg",\n    "list_grid",\n    "list_header_bg",\n    "list_hover_bg",\n    "list_selected_bg",\n    "main_btn_bg",\n    "main_btn_border",\n    "main_btn_hover_bg",\n    "main_btn_hover_text",\n    "main_btn_pressed_bg",\n    "main_btn_pressed_text",\n    "main_btn_text",\n    "panel_bg",\n    "platform_btn_bg",\n    "platform_btn_hover_bg",\n    "pressed_bg",\n    "scrollbar_bg",\n    "scrollbar_border",\n    "scrollbar_handle",\n    "scrollbar_handle_hover",\n    "selected_bg",\n    "status_active",\n    "statusbar_bg",\n    "statusbar_border",\n    "tab_bg",\n    "tab_hover_bg",\n    "tab_indicator",\n    "tab_selected_bg",\n    "text_accent",\n    "text_disabled",\n    "text_muted",\n    "text_on_accent",\n    "text_primary",\n    "text_secondary",\n    "tooltip_bg",\n    "tooltip_border",\n    "tooltip_text",\n    "window_bg"\n  ],\n')
    tree.sub('tests/test_snapshots.py',
             '    """Locks the *names* of color slots in each theme dict. If anyone adds,\n    removes, or renames a slot, every theme that defines colors must do the\n    same — these snapshots make that mismatch visible."""\n',
             '    """Locks the *names* of color slots in each theme dict. If anyone adds,\n    removes, or renames a slot, every theme that defines colors must do the\n    same — these snapshots make that mismatch visible.\n\n    RNV-NAMED-AND-USED, 2026-10-04: dark and light hold the same slots.\n    Image holds those and four more -- the drop zone\'s and the status bar\'s\n    ground and edge -- which image mode alone reads, from its own palette\n    by name."""\n')
    tree.sub('tests/test_status_register.py',
             'REGISTERED = {\n    "STATUS_SUCCESS": "#926c89",\n    "STATUS_WARNING": "#a2703c",\n    "STATUS_SUCCESS_TEXT": "#ad85a3",\n    "STATUS_WARNING_TEXT": "#bc8752",\n    "STATUS_SUCCESS_TEXT_LIGHT": "#825d79",\n    "STATUS_WARNING_TEXT_LIGHT": "#8e5e2b",\n}\n',
             '# RNV-NAMED-AND-USED, 2026-10-04: the two this application draws. It draws\n# one status colour, the folder watcher\'s label, as text in dark and in\n# light. The family\'s two fills and the warning\'s two text values were held\n# here too; nothing in the application read them, and they went. The\n# register holds the family.\nREGISTERED = {\n    "STATUS_SUCCESS_TEXT": "#ad85a3",\n    "STATUS_SUCCESS_TEXT_LIGHT": "#825d79",\n}\n')
    tree.sub('tests/test_status_register.py',
             '    job. Pinned by value: a test asserting only that these differ from each\n    other would pass on six wrong colours."""\n',
             '    job. Pinned by value: a test asserting only that these differ from each\n    other would pass on two wrong colours."""\n')
    tree.sub('tests/test_status_register.py',
             'def test_a_fill_cannot_carry_text_and_that_is_the_point():\n    """Why there are six values and not two.\n\n    STATUS_SUCCESS and STATUS_WARNING are fills. Every fill in this family\n    sits at L* 48-59, which is exactly what lets ONE value clear 3:1 on a dark\n    AND a light ground -- and a mid-tone reaches 4.5:1 on neither. If either\n    ever clears the text floor, the register has moved it out of the band and\n    somebody needs to know rather than quietly benefiting.\n    """\n    for name in ("STATUS_SUCCESS", "STATUS_WARNING"):\n        value = getattr(colors, name)\n        for ground in ("#1a1a1a", "#2a2a2a", "#f5f5f5", "#ffffff"):\n            assert _contrast(value, ground) >= FILL_FLOOR, f"{name} {ground}"\n            assert _contrast(value, ground) < TEXT_FLOOR, (\n                f"{name} now clears the text floor on {ground}. Do not relax "\n                f"this -- find out whether the register moved it.")\n\n\n',
             "# RNV-NAMED-AND-USED, 2026-10-04: a test stood here on the arithmetic of the\n# two fills -- that each clears 3:1 on both grounds and 4.5:1 on neither.\n# This application draws no fill and no longer carries them; the\n# arithmetic is the register's, where the fills are.\n\n\n")
    tree.sub('tests/test_status_register.py',
             '    for name in ("STATUS_SUCCESS_TEXT", "STATUS_WARNING_TEXT"):\n        for ground in ("#1a1a1a", "#2a2a2a"):\n',
             '    for name in ("STATUS_SUCCESS_TEXT",):\n        for ground in ("#1a1a1a", "#2a2a2a"):\n')
    tree.sub('tests/test_status_register.py',
             '    for name in ("STATUS_SUCCESS_TEXT_LIGHT", "STATUS_WARNING_TEXT_LIGHT"):\n        # Restored at rev 31: the re-walked pair reaches all four rungs.\n',
             '    for name in ("STATUS_SUCCESS_TEXT_LIGHT",):\n        # Restored at rev 31: the re-walked pair reaches all four rungs.\n')
    tree.sub('tests/test_status_register.py',
             'def test_the_watcher_green_is_an_alias_not_a_copy():\n    """"Running" is not "succeeded", and the register has no name for the\n    first. Holding it as an alias keeps the borrowing visible: if status-active\n    is ever registered, one line moves. A copied literal would hide that this\n    app is borrowing at all.\n\n    Unchanged in intent since 2026-09-02. What changed is that the alias is no\n    longer what gets PAINTED -- see the next test.\n    """\n    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")\n    assert "STATUS_ACTIVE_COLOR: Final[str] = STATUS_SUCCESS_TEXT" in src\n    assert colors.STATUS_ACTIVE_COLOR == colors.STATUS_SUCCESS_TEXT\n    assert colors.STATUS_ACTIVE_COLOR != colors.STATUS_SUCCESS, (\n        "the alias points at the FILL again. It is painted with `color:` and "\n        "the fill reads 3.91 on BRAND_BLACK against a 4.5 text floor -- it was "\n        "safe under Bootstrap only because that green happened to be light "\n        "enough to double as text.")\n\n\n',
             '# RNV-NAMED-AND-USED, 2026-10-04: a test stood here holding\n# STATUS_ACTIVE_COLOR as an alias of the success text. Nothing painted from\n# the alias after 2026-09-03 -- the label reads status_active, per mode, as\n# the next three tests hold -- and it went.\n\n\n')
    tree.sub('tests/test_status_register.py',
             'def test_the_palettes_are_wired_through_the_constants_not_rewritten():\n    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")\n    for key, const in (("success", "STATUS_SUCCESS"),\n                       ("warning", "STATUS_WARNING")):\n        found = len(re.findall(r"\'%s\':\\s+%s\\b" % (key, const), src))\n        assert found == 2, (\n            f"{key} is wired through {const} in {found} palettes, not 2")\n\n\n',
             "# RNV-NAMED-AND-USED, 2026-10-04: a test stood here holding the palettes'\n# success and warning keys to their constants. Nothing read the keys, so\n# they went, and the constants with them.\n\n\n")
    tree.sub('tests/test_status_register.py',
             '    assert colors.STATUS_SUCCESS == "#926c89"\n    assert colors.STATUS_WARNING == "#a2703c"\n    assert colors.STATUS_SUCCESS_TEXT == "#ad85a3"\n',
             '    assert colors.STATUS_SUCCESS_TEXT == "#ad85a3"\n    assert colors.STATUS_SUCCESS_TEXT_LIGHT == "#825d79"\n')
    tree.sub('tests/test_status_register.py',
             'LIVE_VALUE = "#926c89"\n',
             '# the success text: a value ui/colors.py holds. It was the success fill\'s\n# until RNV-NAMED-AND-USED, 2026-10-04, when the fill went.\nLIVE_VALUE = "#ad85a3"\n')
    if (tree.root / 'tests/test_named_and_used.py').exists():
        raise Stop('tests/test_named_and_used.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_named_and_used.py', '"""\ntests/test_named_and_used.py\n============================\nRNV-NAMED-AND-USED, 2026-10-04. Every colour in the application is named,\nand every name is used.\n\nRuled 2026-10-04: "As long as a color exist in the app it should be named\nand used no hardcoded or pointless literals should exist, only literals with\na purpose, like data or comparison are allowed. Colors are name for swap\nability and alignment."\n\nIn this application that removed five palette keys no mode read; kept the\ndrop zone\'s and the status bar\'s four keys in the image palette alone, the\none palette they are read from; removed an image-mode card ground nothing\nread, six copies in the main window\'s palettes that nothing looked up, and\nseven constants nothing read; and it named the grounds a preview is\ncomposited onto and the fill of a missing size.\n\nThree sweeps hold it, each over the application\'s own source:\n\n1. NAMED. No colour is written out in the code. Every spelling is read: hex,\n   rgb() and rgba(), a CSS colour name, QColor built from numbers, a Qt\n   global colour, a tuple or a list of channels, an alpha set as a number.\n   A colour is written once, in the colour module, under a name; everything\n   else reads the name. What stays written is DATA, each entry with its\n   reason, and the sweep fails for an entry that no longer matches anything.\n2. USED, the palettes. Every colour a palette holds is looked up by key\n   somewhere in the application.\n3. USED, the constants. Every colour the colour module names is read\n   somewhere in the application: by the palettes, by another constant, or by\n   the code.\n\nClear is not a colour: \'transparent\', alpha 0 and Qt\'s transparent are how a\nwidget is told to paint nothing, and are left as written.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport importlib\nimport pathlib\nimport re\n\nimport pytest\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\n\n#: Where this application writes its colours: the one place a literal belongs.\nCOLOUR_MODULES = ("ui/colors.py",)\n#: Where its palettes are written: their own keys are not lookups.\nPALETTE_MODULES = ("ui/colors.py", "ui/theme_manager.py")\nSKIP_DIRS = {"tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__"}\n\nfrom ui.colors import DARK_THEME_COLORS, IMAGE_MODE_COLORS, LIGHT_THEME_COLORS, OS_SIM_COLORS  # noqa: E402\nfrom ui.theme_manager import ThemeManager  # noqa: E402\n\nPALETTES = {"DARK_THEME_COLORS": DARK_THEME_COLORS, "LIGHT_THEME_COLORS": LIGHT_THEME_COLORS,\n            "IMAGE_MODE_COLORS": IMAGE_MODE_COLORS, "OS_SIM_COLORS": OS_SIM_COLORS}\n\n#: Below these a sweep has gone blind.\nMIN_FILES = 30\nMIN_ENTRIES = 200\nMIN_CONSTANTS = 30\n\n#: What stays written, and why: (file, literal) -> the reason. What goes into\n#: a generated file, what a generated icon starts with and what a choice is\n#: called are not the application\'s look, and a brand move should not change them.\nDATA = {\n    ("cli.py", "#ffffff"):\n        "the theme and background colour a generated web manifest declares: a file\'s content",\n    ("core/icon_builder_core.py", "#ffffff"):\n        "the same two colours, in the manifest the application itself writes: a file\'s content",\n    ("core/icon_builder_core.py", "#da532c"):\n        "the tile colour a generated browserconfig.xml declares: a file\'s content",\n    ("ui/settings_dialog.py", "(255, 255, 255, 255)"):\n        "the fill a generated icon starts with: image content, and the person\'s to change",\n    ("ui/settings_dialog.py", "(0, 0, 0, 255)"):\n        "the border a generated icon starts with: image content, and the person\'s to change",\n    ("ui/preview_utils.py", "White"):\n        "the label of a preview background choice: text shown to the person",\n    ("ui/preview_utils.py", "Black"):\n        "the label of a preview background choice: text shown to the person",\n    ("utils/config.py", "white"):\n        "the name a preview background choice is stored under: an option, not a colour",\n    ("utils/config.py", "black"):\n        "the name a preview background choice is stored under: an option, not a colour",\n    ("ui/ico_analyzer.py", "Qt.GlobalColor.darkGreen"):\n        "HELD, and not data. Set on a PNG row\'s cell and never drawn: the table\'s stylesheet "\n        "colours every cell, and the sheet wins. Proven 2026-10-04 with a magenta control, in "\n        "all three modes. A ruling is asked: draw the mark, or drop the line",\n}\n\nCSS_NAMES = frozenset("""aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue\nblueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue\ndarkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid\ndarkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink\ndeepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold\ngoldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush\nlawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey\nlightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime\nlimegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen\nmediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin\nnavajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise\npalevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue\nsaddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow\nspringgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow\nyellowgreen""".split())\nQT_GLOBAL = frozenset({"white", "black", "red", "darkRed", "green", "darkGreen", "blue", "darkBlue", "cyan",\n                       "darkCyan", "magenta", "darkMagenta", "yellow", "darkYellow", "gray", "darkGray",\n                       "lightGray"})\nHEX = re.compile(r"(?<![\\w&])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_])")\nFUNC = re.compile(r"\\b(?:rgba?|hsla?|hsva?)\\(\\s*[0-9.]+%?\\s*,[^)]*\\)", re.I)\nPROP = re.compile(r"(?:^|[;{\\s\\"\'])((?:[a-z-]*color|background(?:-color)?|border(?:-[a-z]+)*|outline(?:-[a-z]+)*|"\n                  r"fill|stroke))\\s*[:=]\\s*([^;{}<>]*)", re.I)\nWORD = re.compile(r"(?<![\\w#.-])([a-z]+)(?![\\w(-])", re.I)\nNOT_A_COLOUR = re.compile(r"margin|padding|spacing|size|offset|geometry|rect|pos|range|version|ratio|weight", re.I)\nA_COLOUR = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})|rgba?\\([^)]*\\)")\n\n\ndef _sources():\n    """(repo-relative path, text) of every file of the application: not the\n    tests, not a delivery script, not what a build leaves behind."""\n    for path in sorted(ROOT.rglob("*.py")):\n        rel = path.relative_to(ROOT).as_posix()\n        parts = rel.split("/")\n        if any(p in SKIP_DIRS or p.startswith(".") for p in parts[:-1]):\n            continue\n        if len(parts) == 1 and (parts[0].startswith(("test_", "up", "conftest", "run_tests"))):\n            continue\n        text = path.read_text(encoding="utf-8-sig", errors="replace")\n        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:\n            continue\n        yield rel, text\n\n\ndef _prose(tree) -> set:\n    """ids of the strings that are prose: docstrings and bare string statements."""\n    return {id(n.value) for n in ast.walk(tree)\n            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}\n\n\ndef _clear(literal: str) -> bool:\n    """rgba(..., 0) and QColor(..., 0): clear, not a colour."""\n    nums = re.findall(r"[0-9.]+", literal)\n    return len(nums) == 4 and float(nums[3]) == 0\n\n\ndef _written(rel: str, text: str) -> list:\n    """(line, kind, literal) for every colour this file writes out."""\n    tree = ast.parse(text)\n    prose, out = _prose(tree), []\n    parent = {}\n    for node in ast.walk(tree):\n        for child in ast.iter_child_nodes(node):\n            parent[id(child)] = node\n\n    def named_like(node) -> str:\n        """The name a value is given: its assignment target, keyword or parameter."""\n        up = parent.get(id(node))\n        while isinstance(up, (ast.IfExp, ast.BoolOp, ast.Tuple, ast.List)):\n            node, up = up, parent.get(id(up))\n        if isinstance(up, ast.keyword):\n            return up.arg or ""\n        if isinstance(up, (ast.Assign, ast.AnnAssign)):\n            target = up.targets[0] if isinstance(up, ast.Assign) else up.target\n            return ast.unparse(target)\n        if isinstance(up, ast.arguments):\n            both = up.posonlyargs + up.args\n            if node in up.defaults:\n                return both[len(both) - len(up.defaults) + up.defaults.index(node)].arg\n            if node in up.kw_defaults:\n                return up.kwonlyargs[up.kw_defaults.index(node)].arg\n        return ""\n\n    def a_name_on_its_own(node, up) -> bool:\n        """A CSS colour name that is the whole string, where a colour is given:\n        handed to a call, chosen by an if, assigned, returned, a default or a\n        value in a table. A key, an index and a comparison are not a colour\n        given to anything."""\n        s = node.value\n        if isinstance(up, (ast.Call, ast.keyword, ast.IfExp)):\n            return s.lower() in CSS_NAMES              # Qt and PIL read a name in any case\n        if s not in CSS_NAMES:\n            return False\n        if isinstance(up, ast.Dict):\n            return any(v is node for v in up.values)\n        if isinstance(up, ast.arguments):\n            return node in up.defaults or node in up.kw_defaults\n        return isinstance(up, (ast.Assign, ast.AnnAssign, ast.Return)) and up.value is node\n\n    for node in ast.walk(tree):\n        up = parent.get(id(node))\n        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in prose:\n            s = node.value\n            for m in HEX.finditer(s):\n                out.append((node.lineno, "hex", m.group(0)))\n            for m in FUNC.finditer(s):\n                if not _clear(m.group(0)):\n                    out.append((node.lineno, "func", " ".join(m.group(0).split())))\n            for m in PROP.finditer(s):\n                for w in WORD.finditer(m.group(2)):\n                    if w.group(1).lower() in CSS_NAMES:\n                        out.append((node.lineno, "name", f"{m.group(1).lower()}: {w.group(1)}"))\n            # a colour name on its own: QColor("yellow"), fill="white", ink = "black"\n            if a_name_on_its_own(node, up):\n                out.append((node.lineno, "name", s))\n        elif isinstance(node, ast.Call):\n            name = getattr(node.func, "id", getattr(node.func, "attr", None))\n            if name in ("QColor", "fromRgb", "fromRgbF", "qRgb", "qRgba") and node.args \\\n                    and all(isinstance(a, ast.Constant) and not isinstance(a.value, str) for a in node.args):\n                literal = ast.unparse(node)\n                if not _clear(literal):\n                    out.append((node.lineno, "qcolor", literal))\n            # an alpha set as a number: colour.setAlpha(171). Clear and solid are not a choice of alpha.\n            elif name in ("setAlpha", "setAlphaF") and len(node.args) == 1 and isinstance(node.args[0], ast.Constant) \\\n                    and type(node.args[0].value) in (int, float) \\\n                    and node.args[0].value not in ((0, 255) if name == "setAlpha" else (0, 1)):\n                out.append((node.lineno, "alpha", f"{name}({node.args[0].value!r})"))\n        elif isinstance(node, ast.Attribute) and node.attr in QT_GLOBAL \\\n                and ast.unparse(node.value) in ("Qt.GlobalColor", "Qt", "QtCore.Qt.GlobalColor", "QtCore.Qt"):\n            out.append((node.lineno, "global", ast.unparse(node)))\n        elif isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in (3, 4) and all(\n                isinstance(e, ast.Constant) and type(e.value) is int and 0 <= e.value <= 255 for e in node.elts):\n            if (isinstance(up, (ast.comprehension, ast.For)) and up.iter is node) \\\n                    or isinstance(up, (ast.Compare, ast.Subscript)):\n                continue                                   # an index, a membership or a comparison\n            if isinstance(up, ast.Call) and getattr(up.func, "id", getattr(up.func, "attr", "")) in QCOLOR_CALLS:\n                continue                                   # counted with its QColor(...)\n            if len(node.elts) == 4 and node.elts[3].value == 0:\n                continue                                   # clear\n            if NOT_A_COLOUR.search(named_like(node)):\n                continue\n            out.append((node.lineno, "list" if isinstance(node, ast.List) else "tuple", ast.unparse(node)))\n    return out\n\n\nQCOLOR_CALLS = ("QColor", "fromRgb", "fromRgbF", "qRgb", "qRgba")\n\n\ndef _all_written() -> list:\n    """(rel, line, kind, literal) outside the colour module."""\n    out = []\n    for rel, text in _sources():\n        if rel in COLOUR_MODULES:\n            continue\n        out += [(rel, line, kind, literal) for line, kind, literal in _written(rel, text)]\n    return out\n\n\ndef _data(rel: str, literal: str):\n    """The DATA entry that covers this literal, or None."""\n    for (where, what) in DATA:\n        if where == rel and what in ("*", literal):\n            return (where, what)\n    return None\n\n\n# ------------------------------------------------------------ guard the guard\n\ndef test_the_sweep_reads_the_application():\n    files = [rel for rel, _text in _sources()]\n    assert len(files) >= MIN_FILES, f"only {len(files)} files swept: the sweep has gone blind"\n    for rel in COLOUR_MODULES:\n        assert rel in files, f"{rel} is not among the files swept"\n    assert not [f for f in files if f.startswith("tests/")], "the sweep reads the tests"\n\n\ndef test_the_sweep_reads_every_spelling():\n    """Each spelling of a colour, in a line of the kind the application\n    writes, is seen; clear, an index and a margin are not."""\n    seen = {(kind, literal) for _line, kind, literal in _written("probe.py", (\n        "from PyQt6.QtGui import QColor\\n"\n        "from PyQt6.QtCore import Qt\\n"\n        "a = \'background-color: #ffcccc; border: 2px solid red;\'\\n"\n        "b = f\'color: rgba(255, 255, 255, 230); padding: {4}px\'\\n"\n        "c = QColor(128, 128, 128)\\n"\n        "d = Qt.GlobalColor.darkGreen\\n"\n        "e = QColor(\'yellow\')\\n"\n        "text_color = (0, 0, 0) if a else (255, 255, 255)\\n"\n        "f = saved.get(\'color\', [200, 200, 200])\\n"\n        "ink = \'white\'\\n"\n        "g = {\'ground\': \'black\'}\\n"\n        "h = Image.new(\'RGB\', (8, 8), \'Gray\')\\n"\n        "c.setAlpha(171)\\n"))}\n    assert seen == {("hex", "#ffcccc"), ("name", "border: red"), ("func", "rgba(255, 255, 255, 230)"),\n                    ("qcolor", "QColor(128, 128, 128)"), ("global", "Qt.GlobalColor.darkGreen"),\n                    ("name", "yellow"), ("tuple", "(0, 0, 0)"), ("tuple", "(255, 255, 255)"),\n                    ("list", "[200, 200, 200]"), ("name", "white"), ("name", "black"), ("name", "Gray"),\n                    ("alpha", "setAlpha(171)")}, seen\n    quiet = _written("probe.py", (\n        "from PyQt6.QtGui import QColor\\n"\n        "from PyQt6.QtCore import Qt\\n"\n        "a = \'background: transparent; border: none; color: rgba(0, 0, 0, 0);\'\\n"\n        "b = QColor(0, 0, 0, 0)\\n"\n        "b.setAlpha(0)\\n"\n        "b.setAlpha(255)\\n"\n        "c = Qt.GlobalColor.transparent\\n"\n        "d = [int(h[i:i + 2], 16) for i in (0, 2, 4)]\\n"\n        "margins = (10, 10, 10, 10)\\n"\n        "sizes = [16, 32, 48]\\n"\n        "\'\'\'a bare string is prose: color: red, #ffcccc\'\'\'\\n"\n        "if d in (5, 10, 20) or d == (0, 0, 0) or a == \'red\':\\n"\n        "    pass\\n"\n        "for size in [16, 32, 48]:\\n"\n        "    e = {\'red\': 1}[\'red\']\\n"))\n    assert quiet == [], quiet\n\n\n# ----------------------------------------------------------------- 1. named\n\ndef test_no_colour_is_written_out_in_the_code():\n    stray = [f"{rel}:{line}  {literal}" for rel, line, _kind, literal in _all_written()\n             if _data(rel, literal) is None]\n    assert not stray, (\n        "a colour is written out where a name belongs. Name it in "\n        f"{COLOUR_MODULES[0]} and read the name; or, if it is data, add it to DATA "\n        "with its reason:\\n  " + "\\n  ".join(stray))\n\n\ndef test_every_data_entry_still_covers_something():\n    """An exemption that outlives what it excused is a licence for the next\n    literal written in that file."""\n    used = {_data(rel, literal) for rel, _line, _kind, literal in _all_written()}\n    stale = [f"{where}: {what}" for (where, what) in DATA if (where, what) not in used]\n    assert not stale, "DATA entries that match nothing now:\\n  " + "\\n  ".join(stale)\n    assert all(reason.strip() for reason in DATA.values()), "a DATA entry has no reason"\n\n\n# ---------------------------------------------------- 2. used: the palettes\n\ndef _strings_the_application_reads() -> set:\n    """Every string the code holds outside the palettes\' own keys: what a\n    lookup by key, or a table of keys, is written with. A module\'s __all__\n    is a list of the names it exports, not of keys, and is left out: a\n    function called warning() does not look up a palette\'s \'warning\'."""\n    out = set()\n    for rel, text in _sources():\n        tree = ast.parse(text)\n        not_keys = _prose(tree)\n        if rel in PALETTE_MODULES:\n            for node in ast.walk(tree):\n                if isinstance(node, ast.Dict):\n                    not_keys |= {id(k) for k in node.keys if k is not None}\n        for node in tree.body:\n            target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else\n                      node.target if isinstance(node, ast.AnnAssign) else None)\n            if getattr(target, "id", None) == "__all__" and node.value is not None:\n                not_keys |= {id(n) for n in ast.walk(node.value)}\n        for node in ast.walk(tree):\n            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in not_keys:\n                if (rel, node.value) in NOT_LOOKUPS:        # spelled like a key, and not a lookup of one\n                    _NOT_A_READ_SEEN.add((rel, node.value))\n                    continue\n                out.add(node.value)\n    return out\n\n\ndef test_every_colour_a_palette_holds_is_looked_up():\n    read = _strings_the_application_reads()\n    unread = sorted({f"{name}[{key!r}]" for name, palette in PALETTES.items() for key, value in palette.items()\n                     if isinstance(value, str) and (A_COLOUR.fullmatch(value) or value == "transparent")\n                     and key not in read})\n    assert not unread, (\n        "palette entries nothing in the application looks up. A colour is kept "\n        "for what uses it:\\n  " + "\\n  ".join(unread))\n    assert sum(len(p) for p in PALETTES.values()) >= MIN_ENTRIES, "the palettes have gone missing"\n\n\n# --------------------------------------------------- 3. used: the constants\n\ndef _colour_constants() -> dict:\n    """NAME -> where it is defined, for every module-level constant of the\n    colour module whose value is a colour: a hex string, an rgb() string, or\n    channels under a name that says so."""\n    out = {}\n    for rel in COLOUR_MODULES:\n        module = importlib.import_module(rel[:-3].replace("/", "."))\n        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8-sig"))\n        for node in tree.body:\n            target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else\n                      node.target if isinstance(node, ast.AnnAssign) else None)\n            if not isinstance(target, ast.Name) or not target.id.isupper():\n                continue\n            value = getattr(module, target.id, None)\n            if isinstance(value, str) and A_COLOUR.fullmatch(value):\n                out[target.id] = rel\n            elif isinstance(value, tuple) and len(value) in (3, 4) and all(type(v) is int for v in value) \\\n                    and re.search(r"RGB|COLOR|COLOUR|OVERLAY|GROUND|CHECKER", target.id):\n                out[target.id] = rel\n    return out\n\n\ndef _names_the_application_reads() -> dict:\n    """NAME -> how many times the code reads it: as a name or as an attribute."""\n    counts: dict[str, int] = {}\n    for rel, text in _sources():\n        for node in ast.walk(ast.parse(text)):\n            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):\n                counts[node.id] = counts.get(node.id, 0) + 1\n            elif isinstance(node, ast.Attribute):\n                if (rel, node.attr) in NOT_READS:           # spelled like a constant, and not a read of one\n                    _NOT_A_READ_SEEN.add((rel, node.attr))\n                    continue\n                counts[node.attr] = counts.get(node.attr, 0) + 1\n    return counts\n\n\ndef test_every_colour_constant_is_read():\n    constants = _colour_constants()\n    assert len(constants) >= MIN_CONSTANTS, f"only {len(constants)} colour constants found"\n    reads = _names_the_application_reads()\n    unread = sorted(name for name in constants if not reads.get(name))\n    assert not unread, (\n        "colour constants nothing in the application reads. A name is kept for "\n        "what uses it:\\n  " + "\\n  ".join(f"{name}  ({constants[name]})" for name in unread))\n\n\ndef test_every_exported_name_exists():\n    """__all__ names what the colour module offers. A name it lists and does\n    not define makes `from module import *` fail."""\n    for rel in COLOUR_MODULES:\n        module = importlib.import_module(rel[:-3].replace("/", "."))\n        missing = [n for n in getattr(module, "__all__", []) if not hasattr(module, n)]\n        assert not missing, f"{rel} exports names it does not define: {missing}"\n\n\n# ------------------------------------------- the keys one mode alone holds\n\n#: A key one mode alone reads is in that mode\'s palette alone, and is read\n#: from that palette BY NAME: key -> (the palette that holds it, how the code\n#: spells that palette). Read through "the palette in force" it would be a\n#: KeyError in the mode that does not hold it.\nMODE_ONLY = {\n    \'dropzone_bg\': (\'IMAGE_MODE_COLORS\', \'IMAGE_MODE_COLORS\'),\n    \'dropzone_border\': (\'IMAGE_MODE_COLORS\', \'IMAGE_MODE_COLORS\'),\n    \'statusbar_bg\': (\'IMAGE_MODE_COLORS\', \'IMAGE_MODE_COLORS\'),\n    \'statusbar_border\': (\'IMAGE_MODE_COLORS\', \'IMAGE_MODE_COLORS\'),\n}\n\n\ndef _lookups_of(key: str) -> list:\n    """(rel, line, what the receiver is) for every lookup of key outside the\n    palettes\' own modules. A receiver that is a name stands for everything\n    that name is assigned in the function the lookup is in."""\n    out = []\n    for rel, text in _sources():\n        if rel in PALETTE_MODULES:\n            continue\n        tree = ast.parse(text)\n        owner = {}\n        for fn in ast.walk(tree):                  # outer functions first, so the innermost is kept\n            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):\n                for node in ast.walk(fn):\n                    owner[id(node)] = fn\n        for node in ast.walk(tree):\n            receiver = None\n            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and node.slice.value == key:\n                receiver = node.value\n            elif isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "get" and node.args \\\n                    and isinstance(node.args[0], ast.Constant) and node.args[0].value == key:\n                receiver = node.func.value\n            if receiver is None:\n                continue\n            if isinstance(receiver, ast.Name):\n                is_a = {ast.unparse(n.value) for n in ast.walk(owner.get(id(node), tree))\n                        if isinstance(n, ast.Assign) and len(n.targets) == 1\n                        and isinstance(n.targets[0], ast.Name) and n.targets[0].id == receiver.id}\n            else:\n                is_a = {ast.unparse(receiver)}\n            out.append((rel, node.lineno, is_a))\n    return out\n\n\n@pytest.mark.parametrize("key", sorted(MODE_ONLY))\ndef test_a_key_one_mode_holds_is_read_from_that_palette_by_name(key):\n    palette, spelled = MODE_ONLY[key]\n    assert key in PALETTES[palette], f"{palette} does not hold {key!r}"\n    lookups = _lookups_of(key)\n    assert lookups, f"nothing looks up {key!r}"\n    astray = [f"{rel}:{line}  read from {sorted(is_a) or \'a receiver this test cannot follow\'}"\n              for rel, line, is_a in lookups if is_a != {spelled}]\n    assert not astray, (\n        f"{key!r} is in {palette} alone. Read from anything but {spelled} it is a "\n        "KeyError in the mode that does not hold it:\\n  " + "\\n  ".join(astray))\n\n\n# ------------------------------------------------ what each palette holds\n\ndef test_dark_and_light_hold_the_same_keys_and_image_holds_four_more():\n    """A lookup through the palette a dialog was handed cannot miss in dark\n    or light, and image mode holds everything dark does."""\n    dark, light, image = (PALETTES[n] for n in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS"))\n    assert set(dark) == set(light), sorted(set(dark) ^ set(light))\n    assert set(image) - set(dark) == set(MODE_ONLY) and set(dark) <= set(image), sorted(set(image) ^ set(dark))\n\n\n# ------------------------------------------ the main window\'s two palettes\n\ndef test_every_key_the_main_window_palettes_hold_is_looked_up_there():\n    """ThemeManager.DARK_THEME and LIGHT_THEME are what get_current_theme()\n    hands the main window, and nothing else is handed them. Each key they\n    hold is looked up on that palette in the main window."""\n    callers = sorted(rel for rel, text in _sources() if "get_current_theme()" in text)\n    assert callers == ["RNV_Icon_Builder.py", "ui/theme_manager.py"], (\n        f"get_current_theme() is called in {callers}: this test reads the main window alone")\n    tree = ast.parse((ROOT / "RNV_Icon_Builder.py").read_text(encoding="utf-8-sig"))\n    read = {node.slice.value for node in ast.walk(tree)\n            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant)\n            and ast.unparse(node.value) == "theme"}\n    assert len(read) >= 8, f"only {sorted(read)} looked up on the main window\'s palette: the sweep has gone blind"\n    for name in ("DARK_THEME", "LIGHT_THEME"):\n        unread = sorted(set(getattr(ThemeManager, name)) - read)\n        assert not unread, (\n            f"ThemeManager.{name} holds {unread}, which the main window never looks up. "\n            "A copy is kept for what reads it.")\n\n\n# ---------------------------------------------- image mode\'s own palette\n\n#: Image mode is the dark palette under its own name and, after the spread,\n#: the entries image mode reads and draws for itself. A new one is a\n#: decision: it is added here with the entry.\nIMAGE_OWN = (\'window_bg\', \'panel_bg\', \'input_bg\', \'scrollbar_bg\', \'scrollbar_handle\', \'scrollbar_handle_hover\', \'scrollbar_border\', \'dropzone_bg\', \'dropzone_border\', \'statusbar_bg\', \'statusbar_border\')\n\n\ndef _palette_display(name: str) -> ast.Dict:\n    """The dict display NAME is assigned, at module level or in a class body."""\n    for rel in PALETTE_MODULES:\n        for node in ast.walk(ast.parse((ROOT / rel).read_text(encoding="utf-8-sig"))):\n            target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else\n                      node.target if isinstance(node, ast.AnnAssign) else None)\n            if getattr(target, "id", None) == name and isinstance(node.value, ast.Dict):\n                return node.value\n    raise AssertionError(f"{name} is not written as a dict display")\n\n\ndef test_image_mode_is_the_dark_palette_and_its_own_entries():\n    node = _palette_display("IMAGE_MODE_COLORS")\n    spreads = [ast.unparse(v) for k, v in zip(node.keys, node.values) if k is None]\n    assert spreads == ["DARK_THEME_COLORS"] and node.keys[0] is None, (\n        f"IMAGE_MODE_COLORS spreads {spreads}: it is the dark palette first, and no other")\n    written = sorted(k.value for k in node.keys if k is not None and k.value != "name")\n    assert written == sorted(IMAGE_OWN), (\n        "the entries image mode writes for itself are not the ones listed. An entry "\n        f"image mode never reads is a value nothing shows:\\n  written {written}\\n  listed  {sorted(IMAGE_OWN)}")\n\n\n# ------------------------------------------- what only looks like a read\n\n#: A string the code holds that is spelled like a palette key and is not a\n#: lookup of one: (file, string) -> what it is. Left uncounted, so a key\n#: this round removed cannot come back and be taken for read by a line\n#: that never read it.\nNOT_LOOKUPS = {\n    (\'RNV_Icon_Builder.py\', \'success\'):\n        \'a word in a log line, written when a batch job has finished: it looks up no palette\',\n    (\'core/export_history.py\', \'success\'):\n        "a field of a stored export record, data.get(\'success\', True): the record\'s, not a "\n        "palette\'s",\n}\n\n#: An attribute the code reads that is spelled like a colour constant and is\n#: not one: (file, name) -> what it is. Left uncounted for the same reason.\nNOT_READS = dict()\n\n_NOT_A_READ_SEEN: set = set()\n\n\ndef test_what_only_looks_like_a_read_is_still_in_the_code():\n    """An entry that matches no line excuses nothing, and is taken out."""\n    _strings_the_application_reads()\n    _names_the_application_reads()\n    listed = set(NOT_LOOKUPS) | set(NOT_READS)\n    stale = sorted(listed - _NOT_A_READ_SEEN)\n    assert not stale, f"listed as only looking like a read, and no longer in the code: {stale}"\n    assert all(reason.strip() for reason in list(NOT_LOOKUPS.values()) + list(NOT_READS.values())), (\n        "an entry has no reason")\n')


def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _function(src: str, name: str, cls: str | None = None):
    """The named function, at module level or inside the named class."""
    body = ast.parse(src).body
    if cls is not None:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == cls).body
    return next(n for n in body if isinstance(n, ast.FunctionDef) and n.name == name)


def _top(src: str) -> dict:
    """Module-level NAME -> ast.dump of the value it is assigned."""
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(t, ast.Name):
                out[t.id] = ast.dump(node.value)
    return out


def _entries(node) -> dict:
    """A dict display's literal keys -> ast.dump of each value; ** spreads
    under their own ast.dump, so a moved spread is seen too."""
    return {(k.value if k is not None else "**" + ast.dump(v)): ast.dump(v)
             for k, v in zip(node.keys, node.values)}


def _sheet_parts(call) -> list:
    """The literal text of a setStyleSheet(f"...") call, the parts between
    its placeholders, in order."""
    arg = call.args[0]
    assert isinstance(arg, ast.JoinedStr), ast.unparse(arg)[:80]
    return [v.value for v in arg.values if isinstance(v, ast.Constant)]


def _calls(fn, attr: str) -> list:
    return [c for c in ast.walk(fn) if isinstance(c, ast.Call)
            and getattr(c.func, "attr", getattr(c.func, "id", None)) == attr]


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    import json
    CFG, MANAGER, MAIN = "ui/colors.py", "ui/theme_manager.py", "RNV_Icon_Builder.py"
    ROOT_SUITE, SNAPSHOTS = "test_rnv_icon_builder.py", "tests/snapshots.json"
    KEYS_GONE = ('dialog_border', 'hover_bg', 'success', 'tab_border', 'warning')
    IMAGE_ONLY = ('dropzone_bg', 'dropzone_border', 'statusbar_bg', 'statusbar_border')
    IMAGE_UNREAD = 'card_bg'
    COPIES_GONE = ('text_primary', 'border_default', 'hover_bg', 'checkbox_bg', 'checkbox_border', 'hover_color')
    NAMES_GONE = ('BRAND_GOLD_RGB', 'BRAND_DARK_GOLD_RGB', 'STATUS_SUCCESS', 'STATUS_WARNING', 'STATUS_WARNING_TEXT', 'STATUS_WARNING_TEXT_LIGHT', 'STATUS_ACTIVE_COLOR')
    NEW_VALUES = {'OS_SIM_GROUNDS_RGB': "{key: _to_rgb(OS_SIM_COLORS[key]) for key in ('taskbar_dark_bg', 'taskbar_light_bg', 'explorer_bg', 'finder_bg', 'chrome_active_tab_bg', 'bookmarks_bg')}", 'PREVIEW_CHECKER_LIGHT': '_to_rgb(WHITE)', 'PREVIEW_CHECKER_DARK': '_to_rgb(GREY_CC)', 'PREVIEW_GROUND_WHITE': '_to_rgb(WHITE)', 'PREVIEW_GROUND_BLACK': '_to_rgb(TRUE_BLACK)', 'DEFAULT_CUSTOM_BG_RGB': '_to_rgb(DEFAULT_CUSTOM_BG_COLOR)', 'PREVIEW_MISSING_FILL': "'#c8c8c8'"}
    LINKED = {'WHITE': '#ffffff', 'GREY_CC': '#cccccc', 'TRUE_BLACK': '#000000', 'DEFAULT_CUSTOM_BG_COLOR': '#808080'}
    SIM_GROUNDS = {'taskbar_dark_bg': (32, 32, 32), 'taskbar_light_bg': (240, 240, 240), 'explorer_bg': (255, 255, 255), 'finder_bg': (245, 245, 245), 'chrome_active_tab_bg': (255, 255, 255), 'bookmarks_bg': (248, 249, 250)}
    NAMED = {'ui/preview_utils.py': [('get_theme_colors, contrast_ink, DARK_THEME_COLORS, DEFAULT_CUSTOM_BG_COLOR\n', 'get_theme_colors, contrast_ink, DARK_THEME_COLORS, DEFAULT_CUSTOM_BG_RGB, PREVIEW_CHECKER_DARK, PREVIEW_CHECKER_LIGHT, PREVIEW_GROUND_BLACK, PREVIEW_GROUND_WHITE\n', 1), ('color1: tuple[int, int, int]=(255, 255, 255), color2: tuple[int, int, int]=(204, 204, 204)', 'color1: tuple[int, int, int]=PREVIEW_CHECKER_LIGHT, color2: tuple[int, int, int]=PREVIEW_CHECKER_DARK', 2), ('color: tuple[int, int, int]=(255, 255, 255)', 'color: tuple[int, int, int]=PREVIEW_GROUND_WHITE', 1), ('composite_on_color(image, (255, 255, 255))', 'composite_on_color(image, PREVIEW_GROUND_WHITE)', 1), ('composite_on_color(image, (0, 0, 0))', 'composite_on_color(image, PREVIEW_GROUND_BLACK)', 1), ('self.custom_color: tuple[int, int, int] = (128, 128, 128)', 'self.custom_color: tuple[int, int, int] = DEFAULT_CUSTOM_BG_RGB', 1)], 'ui/context_preview.py': [('import BRAND_GOLD, BRAND_DARK_GOLD, OS_SIM_COLORS, get_theme_colors\n', 'import BRAND_GOLD, BRAND_DARK_GOLD, OS_SIM_COLORS, OS_SIM_GROUNDS_RGB, get_theme_colors\n', 1), ('bg = (32, 32, 32) if dark else (240, 240, 240)', "bg = OS_SIM_GROUNDS_RGB['taskbar_dark_bg'] if dark else OS_SIM_GROUNDS_RGB['taskbar_light_bg']", 1), ('                display = composite_on_color(icon_img, (255, 255, 255))', "                display = composite_on_color(icon_img, OS_SIM_GROUNDS_RGB['explorer_bg'])", 1), ('composite_on_color(icon_img, (245, 245, 245))', "composite_on_color(icon_img, OS_SIM_GROUNDS_RGB['finder_bg'])", 1), ('composite_on_color(icon_img, (255, 255, 255))', "composite_on_color(icon_img, OS_SIM_GROUNDS_RGB['chrome_active_tab_bg'])", 1), ('composite_on_color(icon_img, (248, 249, 250))', "composite_on_color(icon_img, OS_SIM_GROUNDS_RGB['bookmarks_bg'])", 1)], 'RNV_Icon_Builder.py': [('LIGHT_THEME_COLORS, IMAGE_MODE_COLORS, get_theme_colors\n', 'LIGHT_THEME_COLORS, IMAGE_MODE_COLORS, get_theme_colors, PREVIEW_MISSING_FILL\n', 1), ("Image.new('RGBA', (size, size), (200, 200, 200, 255))", "Image.new('RGBA', (size, size), PREVIEW_MISSING_FILL)", 1)], 'ui/__init__.py': [('import BRAND_GOLD, BRAND_DARK_GOLD, BRAND_GOLD_RGB, BRAND_DARK_GOLD_RGB, DARK_THEME_COLORS,', 'import BRAND_GOLD, BRAND_DARK_GOLD, DARK_THEME_COLORS,', 1), ("'BRAND_GOLD', 'BRAND_DARK_GOLD', 'BRAND_GOLD_RGB', 'BRAND_DARK_GOLD_RGB', 'DARK_THEME_COLORS',", "'BRAND_GOLD', 'BRAND_DARK_GOLD', 'DARK_THEME_COLORS',", 1)], 'test_rnv_icon_builder.py': [('import BRAND_GOLD, BRAND_DARK_GOLD, BRAND_GOLD_RGB, BRAND_DARK_GOLD_RGB, DARK_THEME_COLORS,', 'import BRAND_GOLD, BRAND_DARK_GOLD, _to_rgb, DARK_THEME_COLORS,', 1), ('DEFAULT_CUSTOM_BG_COLOR, STATUS_ACTIVE_COLOR, TRUE_BLACK,', 'DEFAULT_CUSTOM_BG_COLOR, TRUE_BLACK,', 1), ('self.assertEqual(BRAND_GOLD_RGB, (210, 188, 147))', 'self.assertEqual(_to_rgb(BRAND_GOLD), (210, 188, 147))', 1), ('self.assertEqual(BRAND_DARK_GOLD_RGB, (140, 115, 55))', 'self.assertEqual(_to_rgb(BRAND_DARK_GOLD), (140, 115, 55))', 1), ('r, g, b = BRAND_GOLD_RGB\n', 'r, g, b = _to_rgb(BRAND_GOLD)\n', 1), ('r, g, b = BRAND_DARK_GOLD_RGB\n', 'r, g, b = _to_rgb(BRAND_DARK_GOLD)\n', 1), ('        self.assertGreater(len(STATUS_ACTIVE_COLOR), 3)\n', "        for theme in (DARK_THEME_COLORS, LIGHT_THEME_COLORS, IMAGE_MODE_COLORS):\n            self.assertGreater(len(theme['status_active']), 3)\n", 1), ("'dropzone_bg', 'dropzone_border', 'dropzone_active_bg', 'success', 'warning']", "'dropzone_active_bg']", 1)]}
    LOST = {'tests/test_status_register.py': ['test_a_fill_cannot_carry_text_and_that_is_the_point', 'test_the_palettes_are_wired_through_the_constants_not_rewritten', 'test_the_watcher_green_is_an_alias_not_a_copy']}
    old_cfg, new_cfg = _original(tree, CFG), tree.read(CFG)

    def value(expr):
        return ast.dump(ast.parse(expr, mode="eval").body)

    def assigned(src, name):
        for node in ast.parse(src).body:
            t = (node.targets[0] if isinstance(node, ast.Assign) else
                 node.target if isinstance(node, ast.AnnAssign) else None)
            if getattr(t, "id", None) == name:
                return node.value
        raise AssertionError(f"no {name}")

    def palette(src, name):
        return _entries(assigned(src, name))

    def app_sources():
        for p in sorted(tree.root.rglob("*.py")):
            rel = p.relative_to(tree.root).as_posix()
            parts = rel.split("/")
            if any(q in ("tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__")
                   or q.startswith(".") for q in parts[:-1]):
                continue
            if len(parts) == 1 and parts[0].startswith(("test_", "up", "conftest", "run_tests")):
                continue
            text = tree.read(rel) if rel in tree.files else p.read_text(encoding="utf-8-sig", errors="replace")
            if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
                continue
            yield rel, text

    def lookups(mod):
        """(key, line, what the receiver is) for each lookup by a written key.
        A receiver that is a name stands for everything that name is assigned
        in the function the lookup is in, and for itself where it is assigned
        nothing there."""
        owner = dict()
        for fn in ast.walk(mod):                   # outer functions first, so the innermost is kept
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for node in ast.walk(fn):
                    owner[id(node)] = fn
        for node in ast.walk(mod):
            key = receiver = None
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                key, receiver = node.slice.value, node.value
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", None) in ("get", "pop", "setdefault") \
                    and node.args and isinstance(node.args[0], ast.Constant):
                key, receiver = node.args[0].value, node.func.value
            if not isinstance(key, str):
                continue
            is_a = {ast.unparse(receiver)}
            if isinstance(receiver, ast.Name):
                is_a = {ast.unparse(n.value) for n in ast.walk(owner.get(id(node), mod))
                        if isinstance(n, ast.Assign) and len(n.targets) == 1
                        and isinstance(n.targets[0], ast.Name) and n.targets[0].id == receiver.id} or is_a
            yield key, node.lineno, is_a

    # ---- dark and light: nine keys out of each, and nothing else moves
    d_b, l_b, i_b = (palette(old_cfg, n) for n in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS"))
    d_a, l_a, i_a = (palette(new_cfg, n) for n in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS"))
    gone = set(KEYS_GONE) | set(IMAGE_ONLY)
    for name, before, after in (("DARK_THEME_COLORS", d_b, d_a), ("LIGHT_THEME_COLORS", l_b, l_a)):
        assert set(before) - set(after) == gone, f"{name} lost {sorted(set(before) - set(after))}"
        assert after == {k: v for k, v in before.items() if k not in gone}, f"{name} moved beyond the keys removed"

    # ---- image: the spread first; the card override out; the four it alone reads written, at the values they had
    spread = "**" + value("DARK_THEME_COLORS")
    assert list(i_b)[0] == spread and list(i_a)[0] == spread, "image mode does not spread the dark palette first"
    own_b = {k: v for k, v in i_b.items() if k != spread}
    own_a = {k: v for k, v in i_a.items() if k != spread}
    assert set(own_b) - set(own_a) == {IMAGE_UNREAD}, \
        f"IMAGE_MODE_COLORS lost {sorted(set(own_b) - set(own_a))}, not its {IMAGE_UNREAD} override alone"
    assert set(own_a) - set(own_b) == set(IMAGE_ONLY) - set(own_b) and set(IMAGE_ONLY) <= set(own_a), \
        f"IMAGE_MODE_COLORS does not write the four keys image mode alone reads: {sorted(set(own_a) - set(own_b))}"
    assert all(own_a[k] == own_b[k] for k in own_b if k != IMAGE_UNREAD), "an entry image mode draws differently moved"
    resolved_b, resolved_a = {**d_b, **own_b}, {**d_a, **own_a}
    assert resolved_a == {**{k: v for k, v in resolved_b.items() if k not in KEYS_GONE}, IMAGE_UNREAD: d_b[IMAGE_UNREAD]}, \
        "image mode no longer resolves every key it kept to the value it had"

    # ---- the module: seven names go, seven come at the values the code had, and nothing else moves
    old_top, new_top = _top(old_cfg), _top(new_cfg)
    assert set(old_top) - set(new_top) == set(NAMES_GONE), sorted(set(old_top) - set(new_top))
    assert set(new_top) - set(old_top) == set(NEW_VALUES), sorted(set(new_top) - set(old_top))
    for name, expr in NEW_VALUES.items():
        assert new_top[name] == value(expr), f"{name} is not {expr}"
    for name, written in LINKED.items():
        assert old_top.get(name) == value(repr(written)), f"{name} is not {written}: a colour linked to it would move"
    sim = ast.literal_eval(assigned(old_cfg, "OS_SIM_COLORS"))
    for key, written in SIM_GROUNDS.items():
        assert sim.get(key, "").lower() == "#%02x%02x%02x" % written, \
            f"OS_SIM_COLORS[{key!r}] is not {written}, the ground the code wrote out beside it: an icon's ground would move"
    moved = sorted(n for n in new_top if n in old_top and old_top[n] != new_top[n])
    assert moved == ["DARK_THEME_COLORS", "IMAGE_MODE_COLORS", "LIGHT_THEME_COLORS", "__all__"], \
        f"ui/colors.py: these names moved: {moved}"
    was, now = ast.literal_eval(assigned(old_cfg, "__all__")), ast.literal_eval(assigned(new_cfg, "__all__"))
    assert [n for n in now if n not in NEW_VALUES] == [n for n in was if n not in NAMES_GONE] \
        and sorted(set(now) - set(was)) == sorted(NEW_VALUES), "__all__ moved beyond the names removed and the seven added"

    def defined(src):
        return {n.name: ast.dump(n) for n in ast.parse(src).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert defined(old_cfg) == defined(new_cfg), "ui/colors.py: a function moved"
    missing = [n for n in now if n not in set(new_top) | set(defined(new_cfg))]
    assert not missing, f"__all__ names what is not defined: {missing}"

    # ---- the main window's two palettes: six copies out of each, and they hold what the main window looks up
    def manager(src):
        """ThemeManager's two palettes -> (the keys copied across, the entries written), and the class without them."""
        mod = ast.parse(src)
        cls = next(n for n in mod.body if isinstance(n, ast.ClassDef) and n.name == "ThemeManager")
        out = dict()
        for node in cls.body:
            name = getattr(getattr(node, "target", None), "id", None)
            if name in ("DARK_THEME", "LIGHT_THEME"):
                copied, written = [], dict()
                for k, v in zip(node.value.keys, node.value.values):
                    if k is None:
                        assert isinstance(v, ast.DictComp) and not copied, f"ThemeManager.{name} is not as this round found it"
                        copied = [ast.dump(v.key), ast.dump(v.value)] + [e.value for e in v.generators[0].iter.elts]
                    else:
                        written[k.value] = ast.dump(v)
                out[name] = (copied, written)
        cls.body = [n for n in cls.body if getattr(getattr(n, "target", None), "id", None) not in out]
        return out, ast.dump(mod)
    (before, rest_b), (after, rest_a) = manager(_original(tree, MANAGER)), manager(tree.read(MANAGER))
    assert sorted(before) == sorted(after) == ["DARK_THEME", "LIGHT_THEME"], sorted(after)
    assert rest_b == rest_a, f"{MANAGER} moved beyond its two palettes"
    copies = [k for k in COPIES_GONE if k != "hover_color"]
    the_palette = {"theme", "self.theme_manager.get_current_theme()"}       # as the main window spells what it is handed
    main_reads = set(key for key, _line, is_a in lookups(ast.parse(tree.read(MAIN))) if is_a & the_palette)
    for name in ("DARK_THEME", "LIGHT_THEME"):
        (copied_b, written_b), (copied_a, written_a) = before[name], after[name]
        assert copied_a == [k for k in copied_b if k not in copies] and set(copied_b) - set(copied_a) == set(copies), \
            f"ThemeManager.{name}: the keys copied across moved beyond the five removed"
        assert written_a == {k: v for k, v in written_b.items() if k != "hover_color"} and "hover_color" in written_b, \
            f"ThemeManager.{name}: its written entries moved beyond hover_color"
        held = set(copied_a[2:]) | set(written_a)
        assert main_reads == held, (
            f"ThemeManager.{name} would hold {sorted(held - main_reads)} that the main window never looks up, and "
            f"lack {sorted(main_reads - held)} that it does")

    # ---- derived, over the whole application
    handed_out, by_name = [], []
    for rel, text in app_sources():
        mod = ast.parse(text)
        for node in ast.walk(mod):
            names = []
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                names = [node.id]
            elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[-1] in ("colors", "ui"):
                names = [a.name for a in node.names]
            for n in names:
                assert n not in NAMES_GONE, f"{rel}:{node.lineno} still names {n}, which this round removes"
            # the main window's palettes reach the main window alone, through get_current_theme()
            if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "get_current_theme":
                assert rel == MAIN, f"{rel}:{node.lineno} calls get_current_theme(): its palette is no longer the main window's alone"
            if isinstance(node, ast.Attribute) and node.attr in ("DARK_THEME", "LIGHT_THEME"):
                assert rel == MANAGER, f"{rel}:{node.lineno} reads ThemeManager.{node.attr} itself"
            # nothing asks for the image palette whole: it is read key by key, by its name
            if isinstance(node, ast.Call) and getattr(node.func, "attr", getattr(node.func, "id", None)) == "get_theme_colors":
                assert len(node.args) + len(node.keywords) <= 1 and all(k.arg == "is_dark" for k in node.keywords), \
                    f"{rel}:{node.lineno} asks get_theme_colors() for image mode: its {IMAGE_UNREAD} may be read"
        for key, line, is_a in lookups(mod):
            # the one lookup that shares a spelling with a key that goes: a history record's own field
            if (rel, key, is_a) == ("core/export_history.py", "success", {"data"}):
                continue
            assert key not in KEYS_GONE, f"{rel}:{line} looks up {key!r}, a key this round removes"
            if rel == CFG:
                continue
            if key in IMAGE_ONLY:
                by_name.append(key)
                assert is_a == {"IMAGE_MODE_COLORS"}, \
                    f"{rel}:{line} reads {key!r} from {sorted(is_a)}: it is in IMAGE_MODE_COLORS alone"
            if key == IMAGE_UNREAD:
                handed_out.append(rel)
                for source in is_a:
                    call = ast.parse(source, mode="eval").body
                    assert source == "DARK_THEME_COLORS" or (
                        isinstance(call, ast.Call)
                        and getattr(call.func, "attr", getattr(call.func, "id", None)) == "get_theme_colors"), \
                        f"{rel}:{line} reads {key!r} from {source}: image mode's entry may be read"
    assert sorted(set(by_name)) == sorted(IMAGE_ONLY), f"image mode no longer reads {sorted(set(IMAGE_ONLY) - set(by_name))}"
    assert len(handed_out) >= 5, f"only {len(handed_out)} lookups of {IMAGE_UNREAD!r} found: this check has gone blind"

    # ---- the code, the package and the root suite: each moves by what is named, and by nothing else
    for rel, pairs in NAMED.items():
        want, now_u = ast.unparse(ast.parse(_original(tree, rel))), ast.unparse(ast.parse(tree.read(rel)))
        for old, new, times in pairs:
            assert want.count(old) == times, f"{rel}: {old.strip()!r} is written {want.count(old)} times, not {times}"
            want = want.replace(old, new)
        assert now_u == want, f"{rel}: moved beyond naming what it wrote out"

    # ---- the tests: the root suite keeps every test; the snapshot lists lose the keys; each guard loses what named what went
    def tests_in(src):
        return [n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert tests_in(_original(tree, ROOT_SUITE)) == tests_in(tree.read(ROOT_SUITE)), "the root suite gained or lost a test"
    snap_b, snap_a = json.loads(_original(tree, SNAPSHOTS)), json.loads(tree.read(SNAPSHOTS))
    lists = {"dark_theme_keys": gone, "light_theme_keys": gone, "image_mode_keys": set(KEYS_GONE)}
    for name, value_b in snap_b.items():
        want = [k for k in value_b if k not in lists[name]] if name in lists else value_b
        assert snap_a.get(name) == want, f"{SNAPSHOTS}: {name} moved beyond the keys removed"
        assert name not in lists or set(value_b) - set(want) == lists[name], f"{SNAPSHOTS}: {name} did not hold what goes"
    assert sorted(snap_a) == sorted(snap_b), f"{SNAPSHOTS}: a snapshot came or went"
    assert tests_in(tree.read(GUARD)) == ['test_the_sweep_reads_the_application', 'test_the_sweep_reads_every_spelling', 'test_no_colour_is_written_out_in_the_code', 'test_every_data_entry_still_covers_something', 'test_every_colour_a_palette_holds_is_looked_up', 'test_every_colour_constant_is_read', 'test_every_exported_name_exists', 'test_a_key_one_mode_holds_is_read_from_that_palette_by_name', 'test_dark_and_light_hold_the_same_keys_and_image_holds_four_more', 'test_every_key_the_main_window_palettes_hold_is_looked_up_there', 'test_image_mode_is_the_dark_palette_and_its_own_entries', 'test_what_only_looks_like_a_read_is_still_in_the_code'], f"{GUARD}: its tests are {tests_in(tree.read(GUARD))}"
    for rel in GUARD_FILES[1:]:
        lost = sorted(set(tests_in(_original(tree, rel))) - set(tests_in(tree.read(rel))))
        assert lost == LOST.get(rel, []), f"{rel} lost {lost}"
    assert SENTINEL in new_cfg and SENTINEL in tree.read(GUARD), "the sentinel is not in the palette and its guard"
# ------------------------------------------------------------------ plumbing
#
# EXIT CODES ARE A TAXONOMY, NOT A BOOLEAN. Rev 6 §3.0.1. A harness that
# returns non-zero for everything tells the operator something is wrong and
# nothing about what, and the three non-zero cases want three different
# actions: read the diff, install something, re-run.
EXIT_CLEAN = 0       # everything agreed
EXIT_DISAGREES = 1   # something ran and disagreed -- read it
EXIT_CANNOT_RUN = 2  # the environment is not ready -- nothing was asked
EXIT_INCOMPLETE = 3  # it ran and did not finish -- re-run before believing it


class Stop(SystemExit):
    """A refusal this script chose, as opposed to a crash.

    Carries an exit code from the taxonomy. Bare SystemExit('message') exits 1,
    which says A TEST DISAGREED -- so every refusal used to arrive wearing the
    one verdict it was not.
    """

    def __init__(self, message: str, code: int = EXIT_CANNOT_RUN) -> None:
        super().__init__(message)
        self.code = code


#: Two files per repository that exist there and in none of the others.
#: Verified against the live fleet by _fingerprint_check.py at build time,
#: because a fingerprint that has been renamed away identifies nothing and
#: would refuse every correct checkout.
FINGERPRINTS = {
    "rnv-color-mixer": ("core/image_handler.py", "ui/canvas_view.py"),
    "rnv-color-palette-manager": ("core/color_extractor.py",
                                  "ui/batch_export_dialog.py"),
    "rnv-color-picker": ("core/hilbert_curve.py", "ui/color_swatch_widget.py"),
    "rnv-icon-builder": ("core/icon_builder_core.py", "core/project_manager.py"),
    "rnv-text-transformer": ("core/diff_engine.py", "core/text_cleaner.py"),
}


def refuse_wrong_repository(root) -> None:
    """Refuse a checkout that is not the repository this script was built for.

    CALLED FIRST IN apply(), BEFORE THE SENTINEL AND BEFORE ANY ANCHOR, and the
    order is the whole point. The five applications share file names -- four of
    them have a utils/config.py or a ui/colors.py, and several share a
    tests/conftest.py. Run in the wrong sibling, a sentinel check says "already
    applied" or "not a checkout" and an anchor check says "the file moved",
    and BOTH of those are the script guessing at the wrong question.

    A fingerprint is a file only the right repository has. Two, because one
    that gets renamed takes the check with it.
    """
    want = FINGERPRINTS.get(REPO)
    if not want:
        return
    missing = [f for f in want if not (root / f).exists()]
    if missing:
        raise Stop(
            f"this is not a {REPO} checkout.\n"
            f"  expected to find: {', '.join(want)}\n"
            f"  missing here:     {', '.join(missing)}\n"
            f"Run it from the root of {REPO}. Nothing was read or written.",
            EXIT_CANNOT_RUN)


def _left_alone() -> None:
    """Print what this round deliberately did not touch.

    LEFT_ALONE is optional and is prose, not a guard. It exists because a
    reader of a diff can see what changed and cannot see what was considered
    and declined, and the second is where a round's scope actually lives.
    """
    items = globals().get("LEFT_ALONE")
    if not items:
        return
    print("\nleft alone, deliberately:")
    for line in items:
        print(f"  - {line}")


def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        raise Stop(f"refusing to run as {name} -- it would shadow a module on "
                   f"sys.path. Rename to up.py and run again.", EXIT_CANNOT_RUN)


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}
        self.deleted: set[str] = set()
        #: rel -> (had a BOM, line endings were CRLF throughout). What a file
        #: was on disk, so flush() can put back exactly that around the edit.
        self.form: dict[str, tuple[bool, bool]] = {}

    def read(self, rel: str) -> str:
        """The file as text with LF line endings, whatever it is on disk.

        A FILE IS ITS BYTES, AND AN EDIT MUST NOT CHANGE THE ONES IT DID NOT
        MEAN TO. This used to read with read_text('utf-8-sig') and flush with
        encode('utf-8'). The first strips a byte-order mark and folds CRLF to
        LF; the second puts neither back. So a one-line edit to a CRLF file
        rewrote every line ending in it, and any edit to a file with a BOM
        deleted its first three bytes. rnv-color-picker's utils/config.py --
        the picker's palette -- carries a BOM, so its next round would have.

        Anchors are written with \\n, so a CRLF file is held as LF in memory
        and its endings are restored on write. A file that MIXES endings is
        held exactly as it is: anchors then match only its LF lines, and
        everything else round-trips untouched.
        """
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise Stop(f"missing file: {rel}", EXIT_CANNOT_RUN)
            raw = p.read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            text = (raw[3:] if bom else raw).decode("utf-8")
            crlf = text.count("\r\n")
            all_crlf = crlf > 0 and crlf == text.count("\n")
            if all_crlf:
                text = text.replace("\r\n", "\n")
            self.files[rel] = text
            self.form[rel] = (bom, all_crlf)
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def delete(self, rel: str) -> None:
        """Mark a file for removal. Nothing leaves disk until flush()."""
        if not (self.root / rel).exists() and rel not in self.files:
            raise Stop(f"cannot delete {rel}: it is not in this checkout",
                       EXIT_CANNOT_RUN)
        self.files.pop(rel, None)
        self.deleted.add(rel)

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise Stop(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.", EXIT_CANNOT_RUN)
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel in sorted(self.deleted):
            p = self.root / rel
            if p.exists():
                p.unlink()
                touched.append(f"{rel} (deleted)")
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = self.encode(rel, text)
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched

    def encode(self, rel: str, text: str) -> bytes:
        """Text back to bytes in the form the file had when it was read.

        A file never read -- one this script creates -- has no form to keep
        and is written as plain UTF-8 with LF, which is what every file in
        this fleet is unless it says otherwise.
        """
        bom, all_crlf = self.form.get(rel, (False, False))
        if all_crlf:
            text = text.replace("\n", "\r\n")
        return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort", "killed" or "env" -- only exit code 1 means a
    test failed.

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
        # EXIT 1 IS NOT ALWAYS A TEST DISAGREEING, and this used to assume it
        # was. A missing pytest PLUGIN or a missing pinned package does not
        # stop collection -- the tests are found, then fail at setup -- so
        # pytest exits 1, the same code a real regression gives.
        #
        # It shipped that way. A fresh Codespace with the app requirements and
        # none of tests/requirements-dev.txt ran a round that had landed
        # cleanly and got 85 errors ("fixture 'qtbot' not found": pytest-qt)
        # and 3 failures ("No module named 'engine'": the rnv-brand pin), and
        # the verdict was "FAILED -- the suite is not green". Not one of the 88
        # was the change disagreeing with anything.
        #
        # The discriminator is the assertion. A regression raises
        # AssertionError; a missing dependency raises nothing of the kind. If
        # the run carries environment signatures and NO assertion failure, it
        # is the environment. If it carries both, it is a failure -- the
        # conservative direction, because under-reporting a real regression is
        # the one way this verdict must never be wrong.
        if _missing_dependency(out) and not _ASSERTION.search(out):
            return "env"
        return "fail"
    return "env"


#: A dependency that is not installed, as pytest reports it. Each of these
#: arrived in a real run of this fleet's suites.
_ENV_SIGNS = (
    re.compile(r"fixture '\w+' not found"),                 # a pytest plugin
    re.compile(r"ModuleNotFoundError: No module named"),    # a package
    re.compile(r"\bis not importable\b"),                   # the register pin
    re.compile(r"ImportError: lib[\w.+-]+\.so"),            # a system library
)
#: A real regression. pytest prints the failing line under `E   ` and the
#: exception class in the summary.
_ASSERTION = re.compile(r"^E\s+assert\b|\bAssertionError\b", re.M)


def _missing_dependency(out: str) -> bool:
    return any(sign.search(out) for sign in _ENV_SIGNS)


#: verdict -> taxonomy. "abort" and "killed" are EXIT_INCOMPLETE rather than
#: EXIT_CANNOT_RUN: the environment WAS ready and the run started, which is a
#: different instruction to the operator -- re-run, do not go installing things.
_VERDICT_CODE = {
    "pass": EXIT_CLEAN,
    "fail": EXIT_DISAGREES,
    "env": EXIT_CANNOT_RUN,
    "abort": EXIT_INCOMPLETE,
    "killed": EXIT_INCOMPLETE,
}


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
    return _VERDICT_CODE[verdict]


def verify() -> int:
    # A script that changes the ENVIRONMENT its suites run in does it here,
    # not in checks(): checks() runs against the in-memory tree before
    # anything is on disk. The register pin is the case that needed it -- it
    # writes a dependency line and then runs tests that import what the line
    # declares, and DECLARING IS NOT INSTALLING.
    #
    # In verify() rather than apply() so that `--verify` gets it too; that is
    # the entry point someone uses to re-check a repository, and it has to
    # prepare the same environment.
    hook = globals().get("post_write")
    if hook is not None:
        hook()
        print()

    # GUARD_CMD is OPTIONAL and exists for a repository with no pytest. Every
    # round until 2026-09-12 ran inside one of the five applications, where a
    # guard is a test file; rnv-brand has no tests directory, no pytest
    # dependency, and a deliberate ZERO-IMPORT policy in engine/brand.py --
    # its own idiom is a function that runs AT IMPORT and raises. Installing
    # pytest there to satisfy this harness would change the shape of someone
    # else's repository to suit a tool, which is backwards. GUARD still names
    # the file that holds the check; GUARD_CMD says how to run it.
    guard_cmd = globals().get("GUARD_CMD") or [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", GUARD]
    code = _step("guard", guard_cmd)
    if code != EXIT_CLEAN:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != EXIT_CLEAN:
            return code
    print("\nGreen.")
    return EXIT_CLEAN


def apply(check_only: bool) -> int:
    root = Path.cwd()

    # FIRST. Before the sentinel, before any anchor. See the docstring.
    refuse_wrong_repository(root)

    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise Stop(globals().get("MISSING_HELP") or
                   f"run this from the root of a {REPO} checkout "
                   f"(no {SENTINEL_FILE} here)", EXIT_CANNOT_RUN)

    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8-sig"):
        # ALREADY APPLIED IS NOT AN ERROR, AND USED TO EXIT 1.
        #
        # The operator runs this from a phone and the honest question behind a
        # second run is "did this land?". Exiting 1 answered "something
        # disagreed", which is the one thing that had not happened. Re-running
        # the suites answers the question that was actually asked, and a
        # repository that has the change and passes its tests is CLEAN.
        print(f"already applied -- {SENTINEL!r} is present in "
              f"{SENTINEL_FILE}.\nNothing to write. Re-running the suites so "
              f"the answer is measured rather than assumed.\n")
        return verify()

    tree = Tree(root)
    edits(tree)

    # THE SCRIPT MUST WRITE ITS OWN SENTINEL WHERE apply() LOOKS FOR IT.
    #
    # Checked here, against the in-memory tree, before anything reaches disk.
    #
    # WHY THIS IS NOT A BUILD-TIME CHECK. The build's `sentinel-written` guard
    # asserts the marker appears at least twice in the composed script -- its
    # own declaration plus somewhere it gets written. That is a PROXY. A round
    # can carry the marker in a new guard file and never put it in
    # SENTINEL_FILE, and the build passes while the already-applied branch can
    # never fire. That shipped once, on 2026-09-24: the operator ran a landed
    # script a second time and got "expected 1 occurrence of the anchor, found
    # 0. The file moved" -- about a file that had not moved, from a script
    # that could not tell it had already run.
    #
    # Here the question is exact rather than approximated: after every edit,
    # is the marker in the file apply() reads? It fires on the FIRST run, in
    # the author's verification, rather than on the operator's second.
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise Stop(
            f"this script never writes {SENTINEL!r} into {SENTINEL_FILE}, "
            f"which is the file it reads to tell whether it has already run.\n"
            f"Applied once it would work; run again it would re-attempt "
            f"anchors that are already replaced and report them as missing.\n"
            f"Add an edit that marks {SENTINEL_FILE}. Nothing was written.",
            EXIT_CANNOT_RUN)
    # GUARD_SOURCE is OPTIONAL. Every round until 2026-09-12 installed a new
    # guard file, so the harness assumed one; the ramp-condense round adopts
    # three that already exist -- the mixer's SPLITS table and two RETIRED
    # tuples -- and adding a fourth rule for what they already watch is how a
    # suite grows checks that disagree. GUARD still names the file verify()
    # runs first; it just does not have to be a file this script wrote.
    source = globals().get("GUARD_SOURCE")
    if source is not None:
        tree.write(GUARD, source)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        _left_alone()
        return EXIT_CLEAN

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    code = verify()
    if code == EXIT_CLEAN:
        _left_alone()
    return code


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    try:
        refuse_to_shadow()
        if args.finish:
            finish()
            return EXIT_CLEAN
        if args.verify:
            return verify()
        return apply(args.check)
    except Stop as stop:
        # Print it ourselves and return the taxonomy code. Letting SystemExit
        # propagate would print the message and exit 1 regardless of .code.
        print(stop.args[0] if stop.args else "", file=sys.stderr)
        return stop.code


if __name__ == "__main__":
    raise SystemExit(main())
