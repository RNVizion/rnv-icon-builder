"""derive the composed palette values from their bases

RULED 2026-09-24. Nine composed palette entries become translucent(BASE, ALPHA)\nso that changing a base ripples. One pixel moves, by ruling: the image-mode\nscrollbar handle leaves #505050 for GREY_44, closing RNV-COLLAPSE-505050.\n\nSix OS_SIM_COLORS entries are unbound from RNV constants -- same value,\nno coupling -- because that dict depicts other systems and its own comment\nsays it must not follow this theme.\n\nThe alphas were MEASURED through Qt's stylesheet parser on three grounds.\nQt truncates: rgba(..., 0.3) is alpha 76, not 77.
"""
from __future__ import annotations

import argparse
import ast
import os
import pathlib
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = 'rnv-icon-builder'
SENTINEL = 'RNV-DERIVE-ALPHA'
SENTINEL_FILE = "tests/conftest.py"
GUARD = "tests/test_derived_values.py"
DESCRIPTION = 'derive the composed palette values from their bases'
SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p",
            "no:cacheprovider"])]
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

LEFT_ALONE = [
    "the four composed values in OS_SIM_COLORS -- rgba(255,255,255,0.3) and "
    "its siblings are the macOS dock's white, not WHITE. Deriving them would "
    "bind a depiction of another system to this register, which is the defect "
    "the exclusion guard now forbids.",
    "every alpha except the scrollbar handle's, which was ruled. The palette "
    "manager uses 100 on the same widget where three applications use 150, "
    "and nothing records why -- a fleet question, not this round's.",
    "the other four applications. #505050 is alive in all of them; this round "
    "closes one.",
    "the element column of the chart. Its resolver needs rebuilding and a "
    "derived entry is a Call rather than a Constant, which it must learn.",
]

LIGHTEN_TAIL = "    r, g, b = _to_rgb(hex_color)\n    return '#%02x%02x%02x' % tuple(\n        max(0, min(255, c + step)) for c in (r, g, b)\n    )\n"
DARK_DECL = 'DARK_THEME_COLORS: Final[dict[str, str]] = {'
HELPER = '\n\ndef translucent(hex_color: str, alpha: int) -> str:\n    """Compose a colour and an alpha into Qt\'s eight-digit #AARRGGBB.\n\n    WHY A FUNCTION RATHER THAN A WRITTEN-OUT VALUE. A value computed from\n    another value must be computed in code; a written-down derivative is\n    orphaned the moment its source moves, silently. RNV-COLLAPSE-505050 is\n    what that costs: #505050 was collapsed onto GREY_44 on 2026-09-02 and went\n    on painting in four applications, because the alpha forms were written out\n    as rgba() and nothing followed them. Derived, the collapse would have\n    carried in the same edit.\n\n    WHY #AARRGGBB AND NOT rgba(). Both are valid in a Qt stylesheet and only\n    one is valid in QColor(). QColor(\'rgba(42, 42, 42, 0.93)\') is INVALID and\n    Qt substitutes opaque black -- which is what _apply_image_mode_palette()\n    has been setting QPalette.Window and QPalette.Base to. The eight-digit\n    form works in both places.\n\n    ALPHA IS THE 0-255 BYTE, not a fraction. Qt TRUNCATES a float alpha in a\n    stylesheet: rgba(..., 0.3) is alpha 76, not 77, because 0.3 * 255 is 76.5.\n    The constants below carry the measured byte so the spelling change moves\n    nothing.\n    """\n    if not 0 <= alpha <= 255:\n        raise ValueError(f\'alpha {alpha} is outside 0-255\')\n    h = hex_color.lstrip(\'#\').lower()\n    if len(h) != 6:\n        raise ValueError(f\'{hex_color!r} is not a six-digit hex colour\')\n    return \'#%02x%s\' % (alpha, h)\n\n'
ALPHAS = '# ==================== Composite alphas ====================\n# Each is the integer byte Qt produces for the float spelling it replaces,\n# MEASURED through Qt\'s own stylesheet parser over three grounds rather than\n# computed -- Qt truncates, so 0.3 is 76 and not 77, and 0.1 is 25 and not 26.\n# Named so a chart row can carry its variants: change the base constant and\n# every alpha form of it follows.\nSCRIM_ALPHA: Final[int] = 0xED\n"""237. The image-mode chrome scrim, from rgba(..., 0.93).\n\nThe colour picker derived the same byte by hand for its IMAGE_OVERLAY_ALPHA\nand spelled it "ED". Two derivations, one value."""\n\nDROPZONE_ALPHA_DARK: Final[int] = 0x33\n"""51, from rgba(..., 0.2). The active drop zone on a dark ground."""\n\nDROPZONE_ALPHA_LIGHT: Final[int] = 0x4C\n"""76, from rgba(..., 0.3). Heavier on light, because the tint has less\nground to work against."""\n\nSCROLLBAR_HANDLE_ALPHA: Final[int] = 0x96\n"""150. Three of the four applications with an image scrollbar use this; the\npalette manager uses 100 and nothing records why."""\n\nSCROLLBAR_BORDER_ALPHA: Final[int] = 0x64\n"""100, from rgba(51, 51, 51, 100)."""\n\n'
DERIVE = [("    'dropzone_active_bg': 'rgba(210, 188, 147, 0.2)',", "    'dropzone_active_bg': translucent(BRAND_GOLD, DROPZONE_ALPHA_DARK),"), ("    'dropzone_active_bg': 'rgba(210, 188, 147, 0.3)',", "    'dropzone_active_bg': translucent(BRAND_GOLD, DROPZONE_ALPHA_LIGHT),"), ("    'window_bg': 'rgba(26, 26, 26, 0.93)',", "    'window_bg': translucent(BRAND_BLACK, SCRIM_ALPHA),"), ("    'panel_bg': 'rgba(26, 26, 26, 0.93)',", "    'panel_bg': translucent(BRAND_BLACK, SCRIM_ALPHA),"), ("    'card_bg': 'rgba(42, 42, 42, 0.93)',", "    'card_bg': translucent(APP_CARD, SCRIM_ALPHA),"), ("    'input_bg': 'rgba(42, 42, 42, 0.93)',", "    'input_bg': translucent(APP_CARD, SCRIM_ALPHA),"), ("    'dropzone_bg': 'rgba(26, 26, 26, 0.93)',", "    'dropzone_bg': translucent(BRAND_BLACK, SCRIM_ALPHA),"), ("    'scrollbar_handle': 'rgba(80, 80, 80, 150)',", "    # RNV-COLLAPSE-505050 closed here, 2026-09-24. This read\n    # rgba(80, 80, 80, 150) -- #505050 at 150 -- which the 2026-09-02\n    # ruling collapsed onto GREY_44 and which survived because the alpha\n    # form was written out and no sweep in the fleet decodes rgba().\n    # Composites to #333333 on the image ground, where #505050 gave\n    # #3a3a3a: a 2.26 CIEDE2000 step, rendered before it was ruled.\n    'scrollbar_handle': translucent(GREY_44, SCROLLBAR_HANDLE_ALPHA),"), ("    'scrollbar_border': 'rgba(51, 51, 51, 100)',", "    'scrollbar_border': translucent(APP_BORDER, SCROLLBAR_BORDER_ALPHA),")]
UNBIND = [("    'taskbar_border':            APP_BORDER,", "    'taskbar_border':            '#333333',   # Windows taskbar edge"), ("    'taskbar_text_light':        TRUE_BLACK,", "    'taskbar_text_light':        '#000000',   # Windows light taskbar"), ("    'explorer_text':             TRUE_BLACK,", "    'explorer_text':             '#000000',   # Windows Explorer"), ("    'finder_text':               APP_BORDER,", "    'finder_text':               '#333333',   # macOS Finder"), ("    'chrome_tab_title':          APP_BORDER,", "    'chrome_tab_title':          '#333333',   # Chrome tab title"), ("    'bookmarks_text':            APP_BORDER,", "    'bookmarks_text':            '#333333',   # Chrome bookmarks bar")]
SNAPSHOT = [('rgba(51, 51, 51, 100)', '#64333333', 2), ('rgba(80, 80, 80, 150)', '#96444444', 2)]

GUARD_SOURCE = '"""Derived values: a palette entry that is a register value AT AN ALPHA.\n\nA palette entry used to be one of two things here -- a name, or a literal --\nand this file adds the third the application always had and never declared.\nrgba(26, 26, 26, 0.93) is not a second colour beside BRAND_BLACK; it IS\nBRAND_BLACK, at 93%, and nothing related the two.\n\nWHY THAT MATTERED. RNV-COLLAPSE-505050 ruled #505050 onto GREY_44 on\n2026-09-02. It went on painting here, and in three other applications, because\nthe alpha form was written out as rgba() and every sweep in the fleet compares\nsix-digit hex. A written-down derivative is orphaned the moment its source\nmoves, and nothing says so.\n\nAND OS_SIM_COLORS IS THE OPPOSITE RULE. It depicts Windows, macOS and Chrome.\nIts own comment says these values "must NOT follow the app theme", and six of\nthem were bound to RNV constants -- so APP_BORDER moved Chrome\'s tab title\nwith it. For that dict the check is an EXCLUSION: no RNV constant may appear.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       LIGHT_THEME_COLORS as LIGHT,\n                       IMAGE_MODE_COLORS as IMAGE,\n                       OS_SIM_COLORS as OS_SIM,\n                       translucent)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / "ui" / "colors.py"\n\nMODE_DICTS = ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS")\nPALETTES = {"DARK_THEME_COLORS": DARK, "LIGHT_THEME_COLORS": LIGHT,\n            "IMAGE_MODE_COLORS": IMAGE}\n\n#: constant -> the byte, and the float spelling it replaced. MEASURED through\n#: Qt\'s own stylesheet parser on three grounds: Qt truncates, so 0.3 is 76.\nALPHAS = {\n    "SCRIM_ALPHA": (0xED, "0.93"),\n    "DROPZONE_ALPHA_DARK": (0x33, "0.2"),\n    "DROPZONE_ALPHA_LIGHT": (0x4C, "0.3"),\n    "SCROLLBAR_HANDLE_ALPHA": (0x96, "150"),\n    "SCROLLBAR_BORDER_ALPHA": (0x64, "100"),\n}\n\n#: every notation a colour can wear here, longest first so that #ED1A1A1A is\n#: not also read as 1A1A1A and #333333 is not also read as #333.\nCOMPOSED = re.compile(r"rgba?\\(\\s*\\d{1,3}\\s*,\\s*\\d{1,3}\\s*,\\s*\\d{1,3}"\n                      r"\\s*(?:,\\s*[0-9.]+\\s*)?\\)")\nHEX8 = re.compile(r"#[0-9a-fA-F]{8}\\b")\n\n\ndef _dicts(names):\n    tree = ast.parse(SRC.read_text(encoding="utf-8-sig"))\n    out = {}\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            target = (node.targets[0] if isinstance(node, ast.Assign)\n                      else node.target)\n            if (getattr(target, "id", None) in names\n                    and isinstance(node.value, ast.Dict)):\n                out[target.id] = node.value\n    missing = set(names) - set(out)\n    assert not missing, f"palettes that are no longer dict literals: {missing}"\n    return out\n\n\n# ------------------------------------------------------------ guard the guard\n\ndef test_translucent_composes_alpha_first():\n    """#AARRGGBB, not #RRGGBBAA. Taking the wrong end gives a real colour and\n    the wrong one, which is the failure that does not look like a failure."""\n    assert translucent("#1a1a1a", 0xED) == "#ed1a1a1a"\n    assert translucent("1a1a1a", 0xED) == "#ed1a1a1a"\n    assert translucent("#D2BC93", 0x33) == "#33d2bc93"\n\n\ndef test_translucent_refuses_what_it_cannot_compose():\n    for bad in (-1, 256, 999):\n        try:\n            translucent("#1a1a1a", bad)\n        except ValueError:\n            pass\n        else:\n            raise AssertionError(f"alpha {bad} was accepted")\n    for bad in ("#1a1a1", "#1a1a1a1a", "nonsense"):\n        try:\n            translucent(bad, 0xED)\n        except ValueError:\n            pass\n        else:\n            raise AssertionError(f"{bad!r} was accepted as a base")\n\n\ndef test_the_alphas_are_the_measured_bytes():\n    """Each constant holds the byte Qt produces for the spelling it replaced.\n    Qt TRUNCATES: 0.3 * 255 is 76.5 and Qt gives 76. Rounding here would move\n    a pixel in a round that says it moves one, and names which."""\n    for name, (byte, _was) in ALPHAS.items():\n        assert hasattr(colors, name), f"ui.colors has no {name}"\n        assert getattr(colors, name) == byte, (\n            f"{name} is {getattr(colors, name):#x}, measured {byte:#x}")\n\n\n# ----------------------------------------------------------- the derivations\n\ndef test_every_derived_entry_names_a_constant_that_exists():\n    """A derived entry is translucent(BASE, ALPHA) where both are names. A\n    literal in either position is the thing this round removed."""\n    bad = []\n    for dict_name, node in _dicts(MODE_DICTS).items():\n        for key, value in zip(node.keys, node.values):\n            if not (isinstance(value, ast.Call)\n                    and getattr(value.func, "id", None) == "translucent"):\n                continue\n            where = f"{dict_name}[{key.value!r}]"\n            if len(value.args) != 2:\n                bad.append(f"{where} takes {len(value.args)} arguments")\n                continue\n            base, alpha = value.args\n            for pos, arg in (("base", base), ("alpha", alpha)):\n                if not isinstance(arg, ast.Name):\n                    bad.append(f"{where} {pos} is a literal, not a name")\n                elif not hasattr(colors, arg.id):\n                    bad.append(f"{where} {pos} names {arg.id}, which does not "\n                               f"exist in ui.colors")\n            if isinstance(alpha, ast.Name) and alpha.id not in ALPHAS:\n                bad.append(f"{where} uses alpha {alpha.id}, which is not one "\n                           f"of the declared composite alphas")\n    assert not bad, "derived entries that do not derive:\\n  " + "\\n  ".join(bad)\n\n\ndef test_every_derived_entry_decomposes_to_its_base_and_its_alpha():\n    """The relationship, checked by TAKING THE VALUE APART rather than by\n    building it again.\n\n    The first version of this recomputed the entry with translucent() and\n    compared -- which is very nearly vacuous, because the dict entry IS\n    translucent(BASE, ALPHA) evaluated at import. The two sides came from the\n    same call, so the assertion held whatever translucent() did, and the only\n    things it could ever have caught were a palette mutated after definition\n    or a duplicate dict where the AST and the runtime disagree.\n\n    Decomposition is independent of the composing function: the last six\n    digits must BE the base and the first two must BE the alpha. A bug in\n    translucent() now fails here, which was the point."""\n    wrong = []\n    for dict_name, node in _dicts(MODE_DICTS).items():\n        for key, value in zip(node.keys, node.values):\n            if not (isinstance(value, ast.Call)\n                    and getattr(value.func, "id", None) == "translucent"):\n                continue\n            base, alpha = value.args\n            got = PALETTES[dict_name][key.value]\n            where = f"{dict_name}[{key.value!r}]"\n            want_base = getattr(colors, base.id).lstrip("#").lower()\n            want_alpha = getattr(colors, alpha.id)\n            if len(got) != 9 or not got.startswith("#"):\n                wrong.append(f"{where} is {got}, not #AARRGGBB")\n                continue\n            if got[3:].lower() != want_base:\n                wrong.append(f"{where} is {got}, whose colour half is not "\n                             f"{base.id} #{want_base}")\n            if int(got[1:3], 16) != want_alpha:\n                wrong.append(f"{where} composites at {got[1:3]}, not "\n                             f"{alpha.id} {want_alpha:#04x}")\n    assert not wrong, "derived entries that do not match:\\n  " + "\\n  ".join(wrong)\n\n\ndef test_no_composed_literal_is_left_in_a_mode_palette():\n    """The completeness half. A composed literal cannot follow its base, so\n    there must not be one left in a palette this application themes."""\n    strays = []\n    for dict_name, node in _dicts(MODE_DICTS).items():\n        for key, value in zip(node.keys, node.values):\n            if isinstance(value, ast.Constant) and isinstance(value.value, str):\n                if COMPOSED.search(value.value) or HEX8.search(value.value):\n                    strays.append(f"{dict_name}[{key.value!r}] = "\n                                  f"{value.value}")\n    assert not strays, (\n        "composed values still written out rather than derived:\\n  "\n        + "\\n  ".join(strays))\n\n\n# -------------------------------------------------------- the exclusion rule\n\ndef test_os_sim_holds_no_rnv_constant():\n    """OS_SIM_COLORS depicts Windows, macOS and Chrome. Its own comment says\n    these "must NOT follow the app theme", and six of them named RNV constants\n    -- so APP_BORDER moved Chrome\'s tab title with it. Two identical numbers\n    doing unrelated jobs must stay separate; binding them couples things that\n    should move independently.\n\n    #333333 being a plausible tab title is a coincidence, not a wiring."""\n    bound = []\n    for _name, node in _dicts(("OS_SIM_COLORS",)).items():\n        for key, value in zip(node.keys, node.values):\n            if isinstance(value, ast.Name):\n                bound.append(f"OS_SIM_COLORS[{key.value!r}] -> {value.id}")\n            elif isinstance(value, ast.Call):\n                bound.append(f"OS_SIM_COLORS[{key.value!r}] is computed from "\n                             f"the application\'s own values")\n    assert not bound, (\n        "a depiction of another system\'s chrome, bound to this brand\'s "\n        "register:\\n  " + "\\n  ".join(bound))\n\n\ndef test_os_sim_still_paints_what_it_did():\n    """Unbinding must not have moved a colour. These are the six that were\n    named, with the values those names held."""\n    assert OS_SIM["taskbar_border"] == "#333333"\n    assert OS_SIM["taskbar_text_light"] == "#000000"\n    assert OS_SIM["explorer_text"] == "#000000"\n    assert OS_SIM["finder_text"] == "#333333"\n    assert OS_SIM["chrome_tab_title"] == "#333333"\n    assert OS_SIM["bookmarks_text"] == "#333333"\n\n\n# ------------------------------------------------- the bug deriving fixed\n\ndef test_the_image_palette_values_are_readable_by_qcolor():\n    """_apply_image_mode_palette() calls QColor() on these. QColor cannot\n    parse rgba() -- it is a stylesheet notation -- and returns an INVALID\n    colour, which Qt renders as opaque black. Every input field in image mode\n    was black rather than the card at 93%.\n\n    This is why the derived form is #AARRGGBB: it is the only spelling that\n    works in both a stylesheet and a QColor."""\n    from PyQt6.QtGui import QColor\n    for key in ("window_bg", "input_bg"):\n        value = IMAGE[key]\n        colour = QColor(value)\n        assert colour.isValid(), (\n            f"QColor({value!r}) is invalid, so QPalette gets opaque black")\n        assert colour.alpha() == 0xED, (\n            f"{key} composites at {colour.alpha()}, not SCRIM_ALPHA")\n\n\ndef test_the_scrollbar_handle_is_grey_44_and_not_the_collapsed_value():\n    """RNV-COLLAPSE-505050, closed here on 2026-09-24. Ruled 2026-09-02,\n    survived in four applications because the alpha form was written out."""\n    handle = IMAGE["scrollbar_handle"]\n    assert handle == translucent(colors.GREY_44, colors.SCROLLBAR_HANDLE_ALPHA)\n    assert "505050" not in handle.lower(), f"{handle} is still #505050"\n    assert handle[3:].lower() == colors.GREY_44.lstrip("#").lower()\n\n# RNV-DERIVE-ALPHA\n'


def edits(tree) -> None:
    """Every substitution, against the in-memory tree."""
    rel = 'ui/colors.py'
    tree.sub(rel, LIGHTEN_TAIL, LIGHTEN_TAIL + HELPER)
    tree.sub(rel, DARK_DECL, ALPHAS + DARK_DECL)
    for old, new in DERIVE + UNBIND:
        tree.sub(rel, old, new)
    tree.sub(rel, "    'lighten',",
             "    'lighten',\n    'translucent',")
    for old, new, n in SNAPSHOT:
        tree.sub('tests/snapshots.json', old, new, n)


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    src = tree.read('ui/colors.py')

    # the helper and every alpha landed
    assert 'def translucent(' in src, 'the helper did not land'
    for name in ('SCRIM_ALPHA', 'DROPZONE_ALPHA_DARK', 'DROPZONE_ALPHA_LIGHT',
                 'SCROLLBAR_HANDLE_ALPHA', 'SCROLLBAR_BORDER_ALPHA'):
        assert f'{name}: Final[int]' in src, f'{name} did not land'

    # it still parses, and the palettes are still dict literals
    tree_ast = ast.parse(src)
    dicts = {}
    for node in ast.walk(tree_ast):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(getattr(t, 'id', None), str) and isinstance(node.value, ast.Dict):
                dicts[t.id] = node.value
    for name in ('DARK_THEME_COLORS', 'LIGHT_THEME_COLORS',
                 'IMAGE_MODE_COLORS', 'OS_SIM_COLORS'):
        assert name in dicts, f'{name} is no longer a dict literal'

    # nine derived entries, and no composed literal left in a mode palette
    derived = 0
    strays = []
    for name in ('DARK_THEME_COLORS', 'LIGHT_THEME_COLORS', 'IMAGE_MODE_COLORS'):
        for k, v in zip(dicts[name].keys, dicts[name].values):
            if isinstance(v, ast.Call) and getattr(v.func, 'id', None) == 'translucent':
                derived += 1
            elif isinstance(v, ast.Constant) and isinstance(v.value, str):
                if 'rgba(' in v.value or 'rgb(' in v.value:
                    strays.append(f'{name}[{k.value!r}] = {v.value}')
    assert derived == 9, f'expected 9 derived entries, found {derived}'
    assert not strays, 'composed literals left behind: ' + '; '.join(strays)

    # OS_SIM carries no name at all any more
    bound = [k.value for k, v in zip(dicts['OS_SIM_COLORS'].keys,
                                     dicts['OS_SIM_COLORS'].values)
             if isinstance(v, (ast.Name, ast.Call))]
    assert not bound, f'OS_SIM_COLORS still names RNV constants: {bound}'

    # the snapshot no longer records either old spelling
    snap = tree.read('tests/snapshots.json')
    for old, _new, _n in SNAPSHOT:
        assert old not in snap, f'snapshots.json still records {old}'
    assert '#96444444' in snap, 'the ruled handle did not reach the snapshot'

    # and the sentinel is in the guard this script writes
    assert SENTINEL in GUARD_SOURCE or SENTINEL in src, \
        'nothing this script writes carries the sentinel'
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

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise Stop(f"missing file: {rel}", EXIT_CANNOT_RUN)
            # utf-8-sig, not utf-8: six files across two repositories carry a
            # BOM, and read_text('utf-8') leaves U+FEFF at the front where
            # ast.parse rejects it.
            self.files[rel] = p.read_text(encoding="utf-8-sig")
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
        return "fail"
    return "env"


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
