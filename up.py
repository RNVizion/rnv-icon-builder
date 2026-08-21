#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

rnv-icon-builder: delete the dead `dropzone_active_border` key.

    python ib.py            # apply, then verify
    python ib.py --verify   # verify only
    python ib.py --finish   # delete this file

WHY

`dropzone_active_border` holds BRAND_DARK_GOLD -- the LIGHT-mode gold -- in the
DARK and IMAGE palettes. Nothing reads it: the only occurrences in the whole
repository are its two definitions in ui/colors.py and its name listed in the
three key-set snapshots. Its sibling `dropzone_active_bg` IS consumed, at
RNV_Icon_Builder.py:2037; the border key is not.

So it renders nothing today, and the palettes still count two golds on screen.
What it is, is a dormant wrong value: the day someone styles that dropzone
border in dark mode, it draws the light gold. Deleting it is the fix -- there is
no correct value for a key nobody reads.

The guard that certified this repo counted a fixed list of CONSTANTS rather
than walking the palette, so a third value sitting on an unlisted key was
invisible to it. This adds the palette-walking count that closes that gap.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TOOL_MARKER = "RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP"
ROOT = Path.cwd()
COLORS = "ui/colors.py"
SETTINGS = "ui/settings_dialog.py"
ABOUT = "ui/about_dialog.py"
MAIN = "RNV_Icon_Builder.py"
SNAPSHOTS = "tests/snapshots.json"
GUARD = "tests/test_brand_contrast.py"
DEAD_KEY = "dropzone_active_border"

OUR_FILES = (COLORS, SETTINGS, ABOUT, MAIN, SNAPSHOTS, GUARD)


def read_any(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "bom"
    try:
        return raw.decode("utf-8"), "plain"
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="surrogateescape"), "surrogate"


def write_any(path: Path, text: str, kind: str) -> None:
    if kind == "bom":
        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    elif kind == "surrogate":
        path.write_bytes(text.encode("utf-8", errors="surrogateescape"))
    else:
        path.write_text(text, encoding="utf-8")


def sub_once(src: str, old: str, new: str, where: str) -> str:
    """Replace exactly one occurrence, or stop.

    A count of 0 means the file moved on; a count of 2 means the anchor is not
    specific enough and a blind replace would hit a site nobody looked at.
    """
    n = src.count(old)
    if n != 1:
        raise SystemExit(
            f"ABORT: expected exactly 1 occurrence of this anchor in {where}, "
            f"found {n}. Stopping rather than guessing.\n---\n{old}\n---")
    return src.replace(old, new)


def prove_it_is_dead() -> None:
    """Refuse to delete a key that something reads.

    Checked here rather than trusted from the write-up, because the write-up
    was made against a clone and this runs against the real tree.
    """
    out = subprocess.run(["git", "ls-files"], cwd=ROOT,
                         capture_output=True, text=True).stdout.split()
    readers = []
    for rel in out:
        path = ROOT / rel
        if path.suffix.lower() not in (".py", ".qss", ".css", ".json", ".md"):
            continue
        if rel in (COLORS, SNAPSHOTS) or Path(rel).name == Path(__file__).name:
            continue
        try:
            text, _ = read_any(path)
        except Exception:
            continue
        if TOOL_MARKER in text:
            continue
        if DEAD_KEY in text:
            readers.append(rel)
    if readers:
        raise SystemExit(
            f"ABORT: {DEAD_KEY} is referenced by {readers}. It is not dead; "
            f"deleting it would break them. Nothing was changed.")
    print(f"  confirmed dead: no file outside {COLORS} and {SNAPSHOTS} "
          f"mentions {DEAD_KEY}")


def step_colors(src: str) -> str:
    """Remove the key from every palette, by AST line span, not by regex."""
    tree = ast.parse(src)
    drop: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value == DEAD_KEY:
                if value.lineno != key.lineno:
                    raise SystemExit(
                        f"ABORT: {DEAD_KEY} at line {key.lineno} spans lines; "
                        f"refusing to guess its extent.")
                drop.append(key.lineno)
    if len(drop) != 2:
        raise SystemExit(
            f"ABORT: expected 2 definitions of {DEAD_KEY}, found {len(drop)} "
            f"at {drop}. The file has moved on; stopping.")
    lines = src.splitlines(keepends=True)
    for lineno in sorted(drop, reverse=True):
        text = lines[lineno - 1]
        if DEAD_KEY not in text:
            raise SystemExit(f"ABORT: line {lineno} is not the key: {text!r}")
        del lines[lineno - 1]
    return "".join(lines)


def step_snapshots() -> bool:
    """Re-baseline the key-set snapshots: one key leaves, one arrives.

    Deleting only the dead key leaves the snapshots one short of the palettes
    once accent_hover is added, which fails as three snapshot tests rather than
    anything meaningful. Both edits belong in the same step.
    """
    path = ROOT / SNAPSHOTS
    data = json.loads(path.read_text(encoding="utf-8"))
    removed = added = 0
    for name, value in data.items():
        # Only the three THEME key sets. Nine lists end with _keys here --
        # batchjob, project, watchsettings and the rest are unrelated schemas.
        if name not in ("dark_theme_keys", "light_theme_keys", "image_mode_keys"):
            continue
        if not isinstance(value, list):
            continue
        keys = list(value)
        if DEAD_KEY in keys:
            keys = [k for k in keys if k != DEAD_KEY]
            removed += 1
        if "accent_hover" not in keys:
            keys.append("accent_hover")
            added += 1
        data[name] = sorted(keys) if value == sorted(value) else keys
    if removed != 3 or added != 3:
        raise SystemExit(
            f"ABORT: expected to drop {DEAD_KEY} from 3 key sets and add "
            f"accent_hover to 3; got {removed} and {added}. Stopping rather "
            f"than half-updating them.")
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


# --------------------------------------------- the dark hover derivative

HOVER_CONST = """

# DERIVED. The dark-mode hover gold, published in rnv-brand engine/brand.py.
# Hover moves AWAY from the ground in both modes: lighter on dark, deeper on
# light. Stated as "a lighter tint for hover" it is wrong half the time.
BRAND_GOLD_HOVER: Final[str] = lighten(BRAND_GOLD, 13)   # -> #dfc9a0
"""


def step_hover_constant(src: str) -> str:
    if "BRAND_GOLD_HOVER" in src:
        return src
    anchor = "\nDARK_THEME_COLORS"
    if anchor not in src:
        raise SystemExit("ABORT: no DARK_THEME_COLORS anchor in ui/colors.py")
    if "def lighten" not in src:
        raise SystemExit("ABORT: ui/colors.py has no lighten(); this repo was "
                         "expected to already carry the derivation helper.")
    return src.replace(anchor, HOVER_CONST + anchor, 1)


def step_accent_hover_key(src: str) -> str:
    """Give every palette the hover role the other three apps already have.

    Dark and image spend the derivative on hover; light spends its own
    derivative, which it already holds as BRAND_DARK_GOLD_DEEP.
    """
    if "'accent_hover'" in src:
        return src
    tree = ast.parse(src)
    inserts = []
    for node in ast.walk(tree):
        # These palettes are annotated -- DARK_THEME_COLORS: Final[dict] = {...}
        # which is an AnnAssign, not an Assign. Handling only one finds nothing
        # and reports it, which is why this aborts rather than half-applying.
        if isinstance(node, ast.Assign):
            targets = [t for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if target.id not in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS"):
                continue
            if not isinstance(node.value, ast.Dict):
                continue
            for key, value in zip(node.value.keys, node.value.values):
                if isinstance(key, ast.Constant) and key.value == "text_accent":
                    inserts.append((key.lineno, target.id))
                    break
    # IMAGE_MODE_COLORS spreads **DARK_THEME_COLORS and overrides only the
    # transparent backgrounds, so it inherits the new key rather than declaring
    # one. Two literal inserts, three palettes -- asserted by the guard.
    if len(inserts) != 2:
        raise SystemExit(
            f"ABORT: expected a text_accent anchor in the 2 literal palettes, "
            f"found {len(inserts)}. Stopping rather than half-adding the key.")
    lines = src.splitlines(keepends=True)
    for lineno, name in sorted(inserts, reverse=True):
        value = ("BRAND_DARK_GOLD_DEEP" if name == "LIGHT_THEME_COLORS"
                 else "BRAND_GOLD_HOVER")
        indent = lines[lineno - 1][:len(lines[lineno - 1])
                                   - len(lines[lineno - 1].lstrip())]
        lines.insert(lineno - 1, f"{indent}'accent_hover': {value},\n")
    return "".join(lines)


def step_checkbox_hover(src: str) -> str:
    """The one site that renders a wrong-mode gold today.

    QCheckBox::indicator:checked:hover hardcodes BRAND_DARK_GOLD -- the LIGHT
    gold -- so in dark mode the checked box hovers to #8c7337. It also means
    light has no visible hover at all, because #8c7337 is already its accent.
    This is the exact role the other three apps fill with accent_hover.
    """
    old = ("            QCheckBox::indicator:checked:hover {{\n"
           "                background-color: {BRAND_DARK_GOLD};\n"
           "                border-color: {BRAND_DARK_GOLD};\n"
           "            }}")
    new = ("            QCheckBox::indicator:checked:hover {{\n"
           "                background-color: {c['accent_hover']};\n"
           "                border-color: {c['accent_hover']};\n"
           "            }}")
    if old not in src:
        raise SystemExit("ABORT: the checkbox hover rule has moved; not editing "
                         "a block I cannot identify.")
    return src.replace(old, new, 1)


# ------------------------------- the remaining palette bypasses

def step_settings_bypasses(src: str) -> str:
    """Three stylesheets in settings_dialog write the LIGHT gold directly.

    Each renders the same value in both modes, so dark mode gets #8c7337 where
    it should have #d2bc93. `c` is the palette already passed into
    _build_stylesheet, so each one has the right value in scope already.
    """
    edits = [
        # pressed border, drawn around a fill that already follows the mode
        ("            QPushButton:pressed {{\n"
         "                background-color: {c['button_pressed_bg']};\n"
         "                border-color: {BRAND_DARK_GOLD};\n",
         "            QPushButton:pressed {{\n"
         "                background-color: {c['button_pressed_bg']};\n"
         "                border-color: {c['button_pressed_bg']};\n"),
        # author label -- gold as TEXT, so it takes the text role
        ('            QLabel[objectName="author_label"] {{\n'
         "                color: {BRAND_DARK_GOLD};\n",
         '            QLabel[objectName="author_label"] {{\n'
         "                color: {c['text_accent']};\n"),
        # clear button pressed border, same as the first
        ("                color: {c['text_on_accent']};\n"
         "                border-color: {BRAND_DARK_GOLD};\n",
         "                color: {c['text_on_accent']};\n"
         "                border-color: {c['button_pressed_bg']};\n"),
    ]
    for old, new in edits:
        src = sub_once(src, old, new, SETTINGS)
    # BRAND_DARK_GOLD was only reachable through those three sites and the
    # checkbox hover. Leaving the import is a loaded gun: the next stylesheet
    # that wants a gold finds a name already in scope and bypasses the palette
    # again, which is how all four of these got here.
    if "BRAND_DARK_GOLD" in src.split("\n", 1)[1].split("def ", 1)[0] or True:
        rest = src.split("BRAND_GOLD, BRAND_DARK_GOLD, get_theme_colors,", 1)
        if len(rest) == 2 and "BRAND_DARK_GOLD" not in rest[1]:
            src = "BRAND_GOLD, get_theme_colors,".join(rest)
    return src


def step_about_bypasses(src: str) -> str:
    """The version label and the credits footer paint BRAND_GOLD in both modes.

    In light mode that is #d2bc93 on a light panel -- the same defect as the
    mixer's Settings headers. about_dialog already imports get_theme_colors and
    already holds self._is_dark.
    """
    src = sub_once(
        src,
        'version_label.setStyleSheet(f"font-size: 14px; color: {BRAND_GOLD}; '
        'border: none; background: transparent;")',
        'version_label.setStyleSheet(\n'
        '            f"font-size: 14px; '
        'color: {get_theme_colors(is_dark=self._is_dark)[\'text_accent\']}; "\n'
        '            f"border: none; background: transparent;")',
        ABOUT)
    src = sub_once(src, "        credits_text = f\"\"\"",
                   "        _c = get_theme_colors(is_dark=self._is_dark)\n"
                   "        credits_text = f\"\"\"", ABOUT)
    src = sub_once(src,
                   '<p style="text-align: center; color: {BRAND_GOLD};">',
                   '<p style="text-align: center; color: {_c[\'text_accent\']};">',
                   ABOUT)
    return src


def step_dropzone(src: str) -> str:
    """The active dropzone highlight is locked to the dark palette entirely.

    Border, fill and label all read BRAND_DARK_GOLD or DARK_THEME_COLORS, so in
    light mode the whole highlight is the wrong palette -- and the border is the
    LIGHT gold in dark mode, which is the reverse. This is also why
    dropzone_active_border was dead: the value was inlined at the point of use
    instead of read from the key.
    """
    old = ("            self.drop_label.setStyleSheet(f\"\"\"\n"
           "                QLabel {{\n"
           "                    border: 3px dashed {BRAND_DARK_GOLD};\n"
           "                    border-radius: 8px;\n"
           "                    padding: 40px;\n"
           "                    background-color: {DARK_THEME_COLORS['dropzone_active_bg']};\n"
           "                    color: {DARK_THEME_COLORS['text_on_accent']};\n")
    new = ("            _c = get_theme_colors(\n"
           "                is_dark=self.theme_manager.current_theme != 'light')\n"
           "            self.drop_label.setStyleSheet(f\"\"\"\n"
           "                QLabel {{\n"
           "                    border: 3px dashed {_c['border_accent']};\n"
           "                    border-radius: 8px;\n"
           "                    padding: 40px;\n"
           "                    background-color: {_c['dropzone_active_bg']};\n"
           "                    color: {_c['text_on_accent']};\n")
    return sub_once(src, old, new, MAIN)


GUARD_ADDITION = '''

# ---------------------------------------------------------------------------
# Palette-walking gold count.   Added 2026-08-21.
#
# The counts above read a fixed list of CONSTANTS. That cannot see a third gold
# sitting on a palette key the list does not name -- which is exactly what
# `dropzone_active_border` was: BRAND_DARK_GOLD, the light-mode gold, parked in
# the DARK and IMAGE palettes on a key nothing read.
#
# Walk the palette instead of naming keys, so the next one cannot hide.

import pathlib
import re

_PALETTES = {
    "DARK": C.DARK_THEME_COLORS,
    "LIGHT": C.LIGHT_THEME_COLORS,
    "IMAGE": C.IMAGE_MODE_COLORS,
}

# Values that are gold-adjacent but are not brand gold, with the reason.
NOT_BRAND_GOLD = {
    "#ffc107": "Material amber -- the semantic warning colour, not brand gold",
}


def _is_goldish(value: object) -> bool:
    if not (isinstance(value, str) and len(value) == 7 and value.startswith("#")):
        return False
    try:
        r, g, b = (int(value[i:i + 2], 16) for i in (1, 3, 5))
    except ValueError:
        return False
    return r > g > b and (r - b) >= 30


def _brand_golds(palette: dict) -> dict:
    out = {}
    for key, value in palette.items():
        if _is_goldish(value) and value.lower() not in NOT_BRAND_GOLD:
            out.setdefault(value.lower(), []).append(key)
    return out


# The four values the system holds: two registered, two derived.
KNOWN_GOLDS = {
    C.BRAND_GOLD.lower(): "registered",
    C.BRAND_DARK_GOLD.lower(): "registered",
    C.BRAND_DARK_GOLD_DEEP.lower(): "derived, lighten(BRAND_DARK_GOLD, -14)",
    C.BRAND_GOLD_HOVER.lower(): "derived, lighten(BRAND_GOLD, 13)",
}


@pytest.mark.parametrize("name", sorted(_PALETTES))
def test_at_most_two_brand_golds_per_palette(name):
    """At most the registered gold and one derivative.

    AT MOST, not exactly. This repo's dark palettes need only #d2bc93 -- hover
    text and the pressed fill both take the accent, so there is no role for a
    dark derivative and none is minted. Spending a derivative you do not need
    is how an orphan gets created; requiring one would force that.
    """
    golds = _brand_golds(_PALETTES[name])
    assert len(golds) <= 2, (
        f"{name} holds {len(golds)} brand golds -- "
        + "; ".join(f"{v} on {sorted(ks)}" for v, ks in sorted(golds.items())))


@pytest.mark.parametrize("name", sorted(_PALETTES))
def test_every_gold_is_a_known_value(name):
    """A gold outside the register is an orphan, and an orphan can be perfectly
    legible -- no contrast check would ever object to it."""
    unknown = {v: sorted(ks) for v, ks in _brand_golds(_PALETTES[name]).items()
               if v not in KNOWN_GOLDS}
    assert not unknown, f"{name} holds golds outside the register: {unknown}"


@pytest.mark.parametrize("name", sorted(_PALETTES))
def test_the_palette_walk_is_still_looking(name):
    """Guard the guard: if the goldish test or the exclusion ever matched
    nothing, the count above would pass by measuring an empty set."""
    assert _brand_golds(_PALETTES[name]), f"{name}: the walk found no golds at all"


def test_the_not_brand_gold_list_has_no_dead_entries():
    """A dead exemption is a licence waiting for a future defect."""
    seen = {str(v).lower() for p in _PALETTES.values() for v in p.values()}
    stale = [v for v in NOT_BRAND_GOLD if v not in seen]
    assert not stale, f"NOT_BRAND_GOLD names nothing in any palette: {stale}"


def test_the_light_gold_stays_out_of_the_dark_palettes():
    """The specific defect this pass removed, pinned so it cannot return."""
    for name in ("DARK", "IMAGE"):
        offenders = [k for k, v in _PALETTES[name].items()
                     if isinstance(v, str) and v.lower() == C.BRAND_DARK_GOLD.lower()]
        assert not offenders, (
            f"{name} carries the light-mode gold {C.BRAND_DARK_GOLD} on "
            f"{offenders}")


def test_the_dead_key_stays_dead():
    """Deleted because nothing read it. Give it a consumer or leave it out."""
    for name, palette in _PALETTES.items():
        assert "dropzone_active_border" not in palette, (
            f"{name} re-grew dropzone_active_border")


# ---------------------------------------------------------------------------
# Palette bypass review.
#
# A stylesheet that writes {BRAND_GOLD} directly, instead of reading a palette
# key, renders the SAME gold in every mode. Sometimes that is right; usually it
# is the light gold appearing in dark mode, or the reverse. The palette walk
# above cannot see any of them, because the value never enters a palette.
#
# Every bypass must be REVIEWED. An entry does not make a site correct -- it
# records that someone looked, and says which. Outstanding entries are visible
# rather than silently permitted.

_BYPASS = re.compile(r"\\{BRAND_[A-Z_]+\\}")


def _bypass_sites():
    import subprocess
    root = pathlib.Path(C.__file__).resolve().parent.parent
    files = subprocess.run(["git", "ls-files", "*.py"], cwd=root,
                           capture_output=True, text=True).stdout.split()
    for rel in files:
        if rel == "ui/colors.py" or rel.startswith("tests/") or rel.startswith("test_"):
            continue
        text = (root / rel).read_text(encoding="utf-8", errors="surrogateescape")
        if "RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP" in text:
            continue
        for line in text.splitlines():
            if _BYPASS.search(line):
                # Keyed by TEXT, not line number. Any edit above a site shifts
                # its line and would silently un-review it; the declaration
                # itself is stable.
                yield rel + " :: " + " ".join(line.split())


REVIEWED = {
    # Each of these was read. A bypass renders the same gold in BOTH modes, so
    # it is only correct where the mode has already been chosen, or where the
    # ground is not a themed surface at all.
    "RNV_Icon_Builder.py :: QLabel:hover {{ color: {BRAND_DARK_GOLD}; }}":
        "correct: inside the light branch of an explicit theme check",
    "RNV_Icon_Builder.py :: QLabel:hover {{ color: {BRAND_GOLD}; }}":
        "correct: the dark branch of that same check",
    "RNV_Icon_Builder.py :: background-color: {BRAND_GOLD};":
        "correct: image-mode stylesheet block, and image mode is dark-based",
    "ui/metadata_panel.py :: color: {BRAND_GOLD};":
        "correct: mode-guarded by the caller",
    "ui/preview_utils.py :: border: 2px solid {BRAND_GOLD};":
        "correct: mode-guarded by the caller",
    "ui/preview_utils.py :: border-color: {BRAND_GOLD};":
        "correct: mode-guarded by the caller",
    "ui/settings_dialog.py :: border-color: {BRAND_GOLD};":
        "correct: hover border drawn over an arbitrary user colour swatch, so "
        "it is deliberately mode-independent -- the ground is the swatch, not "
        "a themed surface",

}


def test_every_palette_bypass_has_been_reviewed():
    """A new bypass must be looked at, not inherited silently."""
    unreviewed = [s for s in _bypass_sites() if s not in REVIEWED]
    assert not unreviewed, (
        "stylesheets write a brand constant directly, with no review "
        "entry: " + ", ".join(unreviewed)
        + " -- read the palette instead, or add an entry saying why not.")


def test_no_reviewed_entry_is_stale():
    """Line numbers move. A stale entry silently un-reviews a real site."""
    live = set(_bypass_sites())
    stale = [k for k in REVIEWED if k not in live]
    assert not stale, (
        "REVIEWED names sites that no longer bypass the palette: "
        + "; ".join(stale) + " -- delete them.")


def test_the_bypass_scan_is_still_looking():
    sites = list(_bypass_sites())
    assert len(sites) >= 5, f"the bypass scan found only {len(sites)} sites"


def test_the_checkbox_hover_reads_the_palette():
    """The one bypass this pass fixed, pinned so it cannot come back."""
    src = (pathlib.Path(C.__file__).resolve().parent / "settings_dialog.py"
           ).read_text(encoding="utf-8")
    block = src.split("QCheckBox::indicator:checked:hover", 1)
    assert len(block) == 2, "the checked-hover rule is gone"
    body = block[1][:220]
    assert "accent_hover" in body, "checked-hover no longer reads accent_hover"
    assert "BRAND_DARK_GOLD" not in body, (
        "checked-hover is hardcoding the light gold again")


def test_dark_hover_is_the_published_derivative():
    assert C.BRAND_GOLD_HOVER == C.lighten(C.BRAND_GOLD, 13)
    assert C.DARK_THEME_COLORS["accent_hover"] == C.BRAND_GOLD_HOVER
    assert C.IMAGE_MODE_COLORS["accent_hover"] == C.BRAND_GOLD_HOVER
    assert C.LIGHT_THEME_COLORS["accent_hover"] == C.BRAND_DARK_GOLD_DEEP


def test_hover_moves_away_from_the_ground():
    def lum(v):
        v = v.lstrip("#")
        ch = [int(v[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]
    for name in ("DARK", "IMAGE"):
        pal = _PALETTES[name]
        assert lum(pal["accent_hover"]) > lum(pal["text_accent"]), \
            f"{name} hover must go lighter, away from a dark ground"
    light = _PALETTES["LIGHT"]
    assert lum(light["accent_hover"]) < lum(C.BRAND_DARK_GOLD), \
        "light hover must go deeper, away from a light ground"
'''


def step_guard(src: str) -> str:
    if "test_two_brand_golds_per_palette" in src:
        return src
    if "import pytest" not in src:
        raise SystemExit("ABORT: the guard file does not import pytest")
    return src.rstrip("\n") + "\n" + GUARD_ADDITION


def edit(rel: str, fn) -> bool:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"ABORT: {rel} not found. Run from the repository root.")
    src, kind = read_any(path)
    out = fn(src)
    if out == src:
        return False
    if rel.endswith(".py"):
        try:
            ast.parse(out)
        except SyntaxError as exc:
            raise SystemExit(f"ABORT: {rel} would not parse: {exc}")
    write_any(path, out, kind)
    return True


APT_PACKAGES = (
    "libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 "
    "libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 "
    "libxcb-randr0 libxcb-render-util0 libxcb-shape0 "
    "libxcb-sync1 libxcb-xfixes0 libxcb-xkb1"
)


def probe() -> None:
    """Run the real import in a subprocess rather than asking if it is findable.

    A missing SYSTEM library is not something pip can fix. Reporting
    'pip install -r ...' when the failure is libGL.so.1 sends the reader in a
    circle -- they have already installed the requirements.
    """
    code = ("import PyQt6.QtWidgets, pytest; "
            "from PyQt6.QtWidgets import QApplication; print('ok')")
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    proc = subprocess.run([sys.executable, "-c", code],
                          capture_output=True, text=True, env=env)
    if proc.returncode == 0:
        return
    err = (proc.stderr or "").strip()
    last = err.splitlines()[-1] if err else "(no error text)"
    print("\nThis environment cannot run the suite yet.\n")
    print(last)
    if any(tok in err for tok in ("libGL", "libEGL", "libxkb", "xcb", "libdbus")):
        print("\nThat is a SYSTEM library, not a Python package -- pip cannot")
        print("install it, and re-running the requirements files will not help.")
        print("This repo's own workflow installs these. Run, in the terminal:\n")
        print("  sudo apt-get update && sudo apt-get install -y " + APT_PACKAGES)
        print("\nThen: python ib.py")
    else:
        print("\nInstall the Python dependencies:\n")
        print("  pip install -r requirements.txt -r requirements-test.txt")
    print("\nThat is a SHELL command. Run it in the terminal, not with python.")
    print("Nothing has been changed.\n")
    raise SystemExit(2)


def run(label: str, args: list[str]) -> tuple[int, str]:
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    print(f"\n--- {label} ---")
    proc = subprocess.run([sys.executable, "-m", "pytest", *args],
                          capture_output=True, text=True, env=env)
    out = proc.stdout + proc.stderr
    tail = [l for l in out.splitlines()
            if l.startswith(("FAILED", "ERROR")) or " passed" in l or " failed" in l]
    print("\n".join(tail[-12:]) or (out.splitlines() or ["(no output)"])[-1])
    if proc.returncode < 0:
        names = {6: "SIGABRT", 9: "SIGKILL (out of memory)",
                 15: "SIGTERM (session reclaimed)"}
        sig = -proc.returncode
        print(f"\nKILLED by signal {sig} -- {names.get(sig, sig)}. "
              f"Killed is not failed; nothing is concluded from this run.")
    return proc.returncode, out


def split_failures(output: str) -> tuple[list[str], list[str]]:
    ours, other = [], []
    pattern = re.compile(r"^(FAILED|ERROR) (\S+\.py)(::\S+)?")
    for line in output.splitlines():
        match = pattern.match(line.strip())
        if match:
            (ours if match.group(2) in OUR_FILES else other).append(line.strip())
    return ours, other


def apply() -> None:
    print("rnv-icon-builder: removing the dead dropzone_active_border key\n")
    prove_it_is_dead()
    edit(COLORS, step_colors)
    print(f"  1  {DEAD_KEY} deleted from both palettes in {COLORS}")
    step_snapshots()
    print("  2  key-set snapshots re-baselined: -1 dead key, +accent_hover")
    edit(COLORS, step_hover_constant)
    print("  3  BRAND_GOLD_HOVER derived, lighten(BRAND_GOLD, 13) -> #dfc9a0")
    edit(COLORS, step_accent_hover_key)
    print("  4  accent_hover added to all three palettes")
    edit(SETTINGS, step_checkbox_hover)
    print("  5  checked-checkbox hover reads the palette instead of the light gold")
    edit(SETTINGS, step_settings_bypasses)
    print("  6  settings_dialog: 3 hardcoded golds routed to the palette")
    edit(ABOUT, step_about_bypasses)
    print("  7  about_dialog: version label and credits footer follow the mode")
    edit(MAIN, step_dropzone)
    print("  8  dropzone highlight reads the current palette, not the dark one")
    edit(GUARD, step_guard)
    print(f"  9  palette walk + bypass review added to {GUARD}")


def verify() -> int:
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    proc = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'.'); from ui import colors as C\n"
         "def g(v):\n"
         "    if not (isinstance(v,str) and len(v)==7 and v.startswith('#')): return False\n"
         "    r,gg,b=(int(v[i:i+2],16) for i in (1,3,5))\n"
         "    return r>gg>b and (r-b)>=30 and v.lower()!='#ffc107'\n"
         "for n in ('DARK_THEME_COLORS','LIGHT_THEME_COLORS','IMAGE_MODE_COLORS'):\n"
         "    d=getattr(C,n); print(' ', n, sorted({v.lower() for v in d.values() if g(v)}))"],
        capture_output=True, text=True, env=env)
    print("\n  brand golds per palette:")
    print(proc.stdout.rstrip() or proc.stderr.strip())

    rc_guard, out_guard = run("brand guard (the gate)",
                              [GUARD, "-q", "-p", "no:cacheprovider"])
    rc_all, out_all = run("full suite", ["-q", "-p", "no:cacheprovider"])
    ours, other = split_failures(out_guard + out_all)
    if other:
        print("\n  pre-existing failures, not from this pass:")
        for line in other:
            print("   ", line)
    if ours:
        print("\n  FAILURES IN FILES THIS PASS TOUCHED:")
        for line in ours:
            print("   ", line)
    ok = rc_guard == 0 and not ours
    print("\n" + ("PASS -- the gate is green and nothing this pass touched failed."
                  if ok else "NOT CLEAN -- see above. Nothing was reverted."))
    return 0 if ok else 1


def finish() -> None:
    me = Path(__file__).resolve()
    me.unlink()
    cache = me.parent / "__pycache__"
    if cache.is_dir():
        shutil.rmtree(cache, ignore_errors=True)
    print("removed", me.name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--finish", action="store_true")
    args = parser.parse_args()
    if args.finish:
        finish()
        return 0
    if not (ROOT / COLORS).exists():
        raise SystemExit("ABORT: run this from the repository root.")
    probe()
    if not args.verify:
        apply()
    return verify()


if __name__ == "__main__":
    raise SystemExit(main())
