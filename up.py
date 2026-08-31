#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Adopt APP["panel-hover"] and APP["hover-light"] in rnv-icon-builder.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHAT MOVES: NOTHING. Not one rendered pixel.

#3a3a3a and #eeeeee were already the values in these eight entries. rnv-brand
registered them -- #3a3a3a as APP["panel-hover"] in rev 22, #eeeeee as
APP["hover-light"] in rev 23 -- so what changes is provenance and spelling:
each becomes a named constant this app mirrors and pins.

    dark   hover_bg, button_hover_bg, list_hover_bg          -> APP_PANEL_HOVER
    light  hover_bg, button_hover_bg, accent_button_hover_bg,
           tab_hover_bg, list_hover_bg                       -> APP_HOVER_LIGHT

The script proves nothing moved rather than asserting it: checks() resolves
every entry of every palette from the ORIGINAL file and the EDITED one and
refuses to write unless all four palettes are equal entry for entry.

THIS PASS WIRES A LIGHT VALUE, WHICH THE LAST ONE PROMISED NOT TO

tests/test_register_wiring.py carries test_the_light_palettes_were_left_alone,
written so that widening scope into light would have to be a deliberate act.
This is that deliberate act, and the test is rewritten here in the open.

It is worth knowing that the old test WOULD NOT HAVE FIRED. It flagged light
entries naming something in its REGISTERED map, and that map was a four-value
snapshot -- TRUE_BLACK, BRAND_BLACK, APP_CARD, APP_BORDER -- which never
contained APP_HOVER_LIGHT. Light could have been wired underneath it silently.
A guard whose reach is narrower than the change it guards against reports clean
because it cannot see, which is the third time that shape has appeared in this
programme. REGISTERED is widened here in the same edit, and the rewritten test
is an allowlist with a companion that requires the allowed value to actually be
used, so an entry cannot outlive its reason.

WHY #eeeeee AND NOT #e8e8e8

The register first ruled #e8e8e8, on the argument that within the passing band
it keeps the most separation from the white base. It withdrew that on
2026-08-30. #e8e8e8 is the ground BRAND_DARK_GOLD_DEEP is calibrated against --
the smallest uniform step that clears it is -14, and -13 gives 4.4675 and fails
-- so registering it as the hover would have pinned every hover in every app to
the one value the gold cannot afford to lose, with 0.0334 of margin. #eeeeee is
grey(14), one step inside, and gold reads 4.7875 on it.

Eleven hover keys across four apps already held #eeeeee. Zero held #e8e8e8.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-icon-builder"
DESCRIPTION = "adopt APP[panel-hover] and APP[hover-light]"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "APP_HOVER_LIGHT,"
MIRROR = "tests/test_app_mirror.py"
WIRING = "tests/test_register_wiring.py"
GUARD = "tests/test_ladder_and_plate.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('pytest tests/ (about 5 minutes)',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ('unittest suite',
     [sys.executable, "-m", "unittest", "test_rnv_icon_builder"]),
]

#: value -> constant name. An ALLOWLIST, not a sweep: a value-keyed
#: substitution with no allowlist can install a name whose meaning is wrong for
#: the palette it lands in, which has happened once in this programme.
SUBSTITUTE = {
    "DARK_THEME_COLORS": {"#3a3a3a": "APP_PANEL_HOVER"},
    "LIGHT_THEME_COLORS": {"#eeeeee": "APP_HOVER_LIGHT"},
}

ALL_DICTS = ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS",
             "OS_SIM_COLORS")

CONSTANTS = '\nAPP_PANEL_HOVER: Final[str] = "#3a3a3a"\n"""engine/brand.py APP["panel-hover"]. The dark interaction plate.\n\nREGISTERED 2026-08-29 in rnv-brand rev 22, and app-owned here until then. The\nregister had called the dark ladder "two-thirds specified" because APP_BORDER\n#333333 is not #3a3a3a and so looked like a missing rung. It is not a rung at\nall: #333333 is grey(3) on the INK grid, which governs inks and EDGES, and a\nborder is an edge. The ladder was complete when the question was first asked.\n\n    BRAND_BLACK + n * 0x10,  n in -1..+2\n    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover\n\nThis app holds three of the four; it has no canvas surface.\n"""\n\nAPP_HOVER_LIGHT: Final[str] = "#eeeeee"\n"""engine/brand.py APP["hover-light"]. grey(14). The light interaction plate.\n\nREGISTERED 2026-08-29 as #e8e8e8 and MOVED to #eeeeee on 2026-08-30 in rev 23,\nbefore any app had been wired to it. Nothing here changes value -- the five\nentries below already held #eeeeee.\n\n#e8e8e8 is the ground BRAND_DARK_GOLD_DEEP is calibrated against: -14 per\nchannel is the smallest uniform step that clears it, and -13 gives 4.4675 and\nfails. Registering it as the hover would have put every hover in the app on the\none value the gold cannot afford to lose, clearing the 4.5 floor by 0.0334. A\nboundary is not a plate. This value is a grid step inside it and reads 4.7875.\n\n#e8e8e8 keeps everything else -- registered, the published gold-as-text\nboundary, the binding ground. It is simply not the hover.\n"""\n'
PROVENANCE = '    "APP_PANEL_HOVER": "register",\n    "APP_HOVER_LIGHT": "register",\n'
PINNED = "    'APP_PANEL_HOVER': '#3a3a3a',\n    'APP_HOVER_LIGHT': '#eeeeee',\n"
OLD_LIGHT_TEST = 'def test_the_light_palettes_were_left_alone():\n    """This pass is the DARK half, on the register\'s stated order. The light\n    ladder is unruled -- nine surfaces inside three grid steps, and which of\n    them are real distinctions is a judgement the register has not made. If a\n    later pass wires light, this test is the thing that has to be deleted on\n    purpose."""\n    named = []\n    for dict_name, node in _dicts(LIGHT_DICTS).items():\n        for key, value in zip(node.keys, node.values):\n            if isinstance(value, ast.Name) and value.id in REGISTERED:\n                named.append(f\'{dict_name}[{key.value!r}] -> {value.id}\')\n    assert not named, (\n        \'the light palettes now reference the register:\\n  \' + \'\\n  \'.join(named)\n        + \'\\n\\nThat is the light half, and it is not ruled yet.\')'
NEW_LIGHT_TEST = '#: The light half is ruled one value at a time. This is the allowlist, and it\n#: is what a later pass has to extend ON PURPOSE.\nLIGHT_RULED = (\'APP_HOVER_LIGHT\',)\n\n\ndef test_the_light_palettes_reference_only_what_the_register_has_ruled():\n    """This began life as "the light palettes were left alone", which was true\n    while the light half was entirely unruled. rnv-brand rev 23 ruled one value\n    of it -- APP["hover-light"] -- so the test becomes an allowlist rather than\n    a prohibition. The light LADDER is still unruled: nine surfaces inside three\n    grid steps, and which of them are real distinctions is a judgement the\n    register has not made.\n\n    THE EARLIER FORM COULD NOT HAVE CAUGHT THIS PASS. It flagged names found in\n    REGISTERED, and REGISTERED was a four-value snapshot that did not contain\n    the value being wired -- so light could have been wired underneath it and it\n    would have reported clean. That is the opposite of what a delete-on-purpose\n    guard is for. REGISTERED is widened in the same commit as the wiring."""\n    named = []\n    for dict_name, node in _dicts(LIGHT_DICTS).items():\n        for key, value in zip(node.keys, node.values):\n            if (isinstance(value, ast.Name) and value.id in REGISTERED\n                    and value.id not in LIGHT_RULED):\n                named.append(f\'{dict_name}[{key.value!r}] -> {value.id}\')\n    assert not named, (\n        \'the light palettes reference register values that are not ruled \'\n        \'yet:\\n  \' + \'\\n  \'.join(named)\n        + \'\\n\\nAdd the name to LIGHT_RULED in the same commit that wires it, \'\n          \'or do not wire it.\')\n\n\ndef test_the_ruled_light_value_is_actually_wired():\n    """The allowlist permits; this requires. An allowlist entry nothing uses is\n    a licence with no subject -- the same shape as a dead exemption."""\n    used = set()\n    for node in _dicts(LIGHT_DICTS).values():\n        for value in node.values:\n            if isinstance(value, ast.Name) and value.id in LIGHT_RULED:\n                used.add(value.id)\n    assert used == set(LIGHT_RULED), (\n        f\'LIGHT_RULED lists {sorted(LIGHT_RULED)} but the light palettes use \'\n        f\'{sorted(used)}\')'
OLD_REG = "REGISTERED = {'TRUE_BLACK': '#000000', 'BRAND_BLACK': '#1a1a1a', 'APP_CARD': '#2a2a2a', 'APP_BORDER': '#333333'}"
NEW_REG = "REGISTERED = {'TRUE_BLACK': '#000000', 'BRAND_BLACK': '#1a1a1a', 'APP_CARD': '#2a2a2a', 'APP_BORDER': '#333333',\n              'APP_PANEL_HOVER': '#3a3a3a', 'APP_HOVER_LIGHT': '#eeeeee'}"

#: Every line this pass adds, counted from the text that adds it. checks()
#: compares the real delta against this: a substitution that eats or adds a
#: line ending leaves every value identical and every test green while the file
#: is quietly reflowed, and only a shape check sees it.
EXPECTED_ADDED = {
    # CONSTANTS supplies its own leading newline and the anchor it replaces
    # gave one up, hence the -1.
    SENTINEL_FILE: CONSTANTS.count("\n") - 1 + PROVENANCE.count("\n"),
    MIRROR: PINNED.count("\n"),
    WIRING: (NEW_LIGHT_TEST.count("\n") - OLD_LIGHT_TEST.count("\n")
             + NEW_REG.count("\n") - OLD_REG.count("\n")),
}


def _resolve(source: str) -> dict:
    """Every palette, resolved to plain values, whether an entry is written as
    a literal or as a name. This is what makes "nothing moved" checkable rather
    than asserted."""
    tree = ast.parse(source.lstrip("\ufeff"))
    consts = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                consts[target.id] = node.value.value
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            name = getattr(target, "id", None)
            if name in ALL_DICTS and isinstance(node.value, ast.Dict):
                palette = {}
                for key, value in zip(node.value.keys, node.value.values):
                    if not isinstance(key, ast.Constant):
                        continue
                    if isinstance(value, ast.Constant):
                        palette[key.value] = value.value
                    elif isinstance(value, ast.Name):
                        palette[key.value] = consts.get(value.id, f"<{value.id}>")
                    else:
                        palette[key.value] = ast.unparse(value)
                out[name] = palette
    return out


def _bounds(lines):
    """The palettes carry identically-spelled key lines, so a plain string
    replace cannot tell dark from light. Every edit is scoped to its own."""
    starts = {}
    pattern = re.compile(r"^(" + "|".join(ALL_DICTS) + r")\s*[:=]")
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            starts[m.group(1)] = i
    if len(starts) != len(ALL_DICTS):
        raise SystemExit(f"expected {len(ALL_DICTS)} palettes, found {sorted(starts)}")
    order = sorted(starts.items(), key=lambda kv: kv[1])
    return {n: (st, order[i + 1][1] if i + 1 < len(order) else len(lines))
            for i, (n, st) in enumerate(order)}


def edits(tree) -> None:
    # 1. the two constants, with their provenance in prose beside the value
    tree.sub(SENTINEL_FILE,
             '\nAPP_PROVENANCE: Final[dict[str, str]] = {',
             CONSTANTS + 'APP_PROVENANCE: Final[dict[str, str]] = {')

    # 2. the declarative classification the tests read
    tree.sub(SENTINEL_FILE, '    "APP_TEXT_DIM": "register",\n',
             '    "APP_TEXT_DIM": "register",\n' + PROVENANCE)

    # 3. the substitutions, scoped per palette
    source = tree.read(SENTINEL_FILE)
    lines = source.splitlines(keepends=True)
    bounds = _bounds(lines)
    swapped = 0
    for dict_name, table in SUBSTITUTE.items():
        start, end = bounds[dict_name]
        for i in range(start, end):
            line = lines[i]
            # Match the line WITHOUT its ending and put the ending back
            # verbatim. Python's `$` also matches just before a trailing
            # newline, so a pattern ending in `(,.*)$` silently drops it -- and
            # the result is still valid Python, so every test passes while the
            # palette is reflowed onto one line.
            body = line.rstrip("\r\n")
            ending = line[len(body):]
            # Only a whole quoted value with a key in front of it, so a hex
            # inside a comment or an rgba string is never touched.
            m = re.match(r"^(\s*'[a-z_0-9]+':\s*)'(#[0-9a-fA-F]{6})'(,.*)$", body)
            if not m:
                continue
            const = table.get(m.group(2).lower())
            if const:
                lines[i] = f"{m.group(1)}{const}{m.group(3)}{ending}"
                swapped += 1
    if swapped != 8:
        raise SystemExit(f"expected 8 substitutions, made {swapped}. The "
                         f"palettes have already been wired, or their shape "
                         f"changed -- re-derive before trusting this script.")
    tree.write(SENTINEL_FILE, "".join(lines))
    print(f"  substituted {swapped} literals for their register names")

    # 4. pin both locally, so drift is caught where rnv-brand is not importable
    tree.sub(MIRROR, "    'APP_TEXT_DIM': '#aaaaaa',\n",
             "    'APP_TEXT_DIM': '#aaaaaa',\n" + PINNED)

    # 5. widen the wiring guard's register map, then rewrite the light test it
    #    is the reach of. Both, in one edit: widening alone turns the light test
    #    red, and rewriting alone leaves it unable to see.
    tree.sub(WIRING, OLD_REG, NEW_REG)
    tree.sub(WIRING, OLD_LIGHT_TEST, NEW_LIGHT_TEST)


def checks(tree) -> None:
    # SHAPE FIRST, on every file this pass touches.
    for rel, added in EXPECTED_ADDED.items():
        before = (Path.cwd() / rel).read_text(encoding="utf-8-sig")
        after = tree.read(rel)
        delta = after.count("\n") - before.count("\n")
        if delta != added:
            raise SystemExit(
                f"{rel} changed shape by {delta} lines; this pass adds exactly "
                f"{added}. A substitution that eats or adds a line ending "
                f"leaves every value identical and every test green.")

    original = (Path.cwd() / SENTINEL_FILE).read_text(encoding="utf-8-sig")
    edited = tree.read(SENTINEL_FILE)

    before, after = _resolve(original), _resolve(edited)
    if set(before) != set(after):
        raise SystemExit(f"a palette appeared or vanished: {set(before) ^ set(after)}")
    moved = []
    for name in before:
        for key in set(before[name]) | set(after[name]):
            was, now = before[name].get(key), after[name].get(key)
            if was != now:
                moved.append(f"{name}[{key!r}]: {was} -> {now}")
    if moved:
        raise SystemExit("THIS PASS MUST NOT MOVE A VALUE, and it moved these:\n  "
                         + "\n  ".join(moved))

    # Completeness: neither value may survive as a literal in ANY palette,
    # including the two this pass does not substitute in.
    values = {v for table in SUBSTITUTE.values() for v in table}
    lines = edited.splitlines()
    bounds = _bounds([l + "\n" for l in lines])
    survivors = []
    for name in ALL_DICTS:
        start, end = bounds[name]
        for i in range(start, end):
            m = re.match(r"^\s*'([a-z_0-9]+)':\s*'(#[0-9a-fA-F]{6})',", lines[i])
            if m and m.group(2).lower() in values:
                survivors.append(f"{name}[{m.group(1)!r}] = {m.group(2)}")
    if survivors:
        raise SystemExit("a registered value is still spelled as a literal:\n  "
                         + "\n  ".join(survivors))

    # The value the plate is NOT. If #e8e8e8 ever lands on a hover key here,
    # the reason this pass exists has been undone.
    for name, palette in after.items():
        for key, value in palette.items():
            if "hover" in key and isinstance(value, str) and value.lower() == "#e8e8e8":
                raise SystemExit(
                    f"{name}[{key!r}] is #e8e8e8 -- that is the ground the gold "
                    f"is calibrated against, not an interaction plate.")

    if SENTINEL not in edited:
        raise SystemExit(f"expected {SENTINEL!r} in the edited palette")


GUARD_SOURCE = '"""The dark ladder\'s top rung and the light plate, both now registered.\n\nWHAT THIS PASS DID. rnv-brand rev 22 registered the two ends of the dark\nsurface ladder -- APP["canvas"] #0a0a0a and APP["panel-hover"] #3a3a3a -- and\nrev 23 registered APP["hover-light"] #eeeeee. Both were app-owned here. This\napp holds panel-hover and hover-light; it has no canvas surface. Neither value\nchanged: the pass changes provenance and spelling, not pixels.\n\nWHY THE LADDER WAS NOT "TWO-THIRDS SPECIFIED". The register originally said it\nwas, because APP["border"] #333333 is not #3a3a3a and so looked like a missing\nrung. It is not a rung at all -- #333333 is grey(3) on the INK grid, which\ngoverns inks and EDGES, and a border is an edge. The ladder was complete when\nthe question was first asked; it was measured against the wrong family.\n\n    BRAND_BLACK + n * 0x10,  n in -1..+2\n    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover\n\nWHY THE PLATE IS #eeeeee AND NOT #e8e8e8. #e8e8e8 is the ground\nBRAND_DARK_GOLD_DEEP is calibrated against: the smallest uniform step that\nclears it is -14, and -13 gives 4.4675 and fails. Registering it as the hover\nwould have put every hover in the app on the one value the gold cannot afford\nto lose, with 0.0334 of margin. A boundary is not a plate. #eeeeee is grey(14),\none step inside, and gold reads 4.7875 on it. The margin is asserted below\nrather than described, because a comment cannot fail.\n\n#e8e8e8 keeps everything else it had -- registered, the published gold-as-text\nboundary, the binding ground. It is simply not the hover.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\n\nimport pytest\n\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       IMAGE_MODE_COLORS as IMAGE,\n                       LIGHT_THEME_COLORS as LIGHT)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / \'ui/colors.py\'\n\nGRID_STEP = 0x11\nLADDER_STEP = 0x10\nTEXT_FLOOR = 4.5\n\n#: Constant name -> the register key it mirrors, and the value both hold.\nNEW = {\'APP_PANEL_HOVER\': (\'panel-hover\', \'#3a3a3a\'),\n       \'APP_HOVER_LIGHT\': (\'hover-light\', \'#eeeeee\')}\n\n#: palette dict name -> the keys in it that must now name the constant.\nWIRED = {\n    \'DARK_THEME_COLORS\': (\'hover_bg\', \'button_hover_bg\',\n                          \'list_hover_bg\'),\n    \'LIGHT_THEME_COLORS\': (\'hover_bg\', \'button_hover_bg\',\n                           \'accent_button_hover_bg\',\n                           \'tab_hover_bg\', \'list_hover_bg\'),\n}\n\n#: dict NAME -> the live dict. Looking a key up in the wrong palette is how a\n#: per-mode difference gets checked against the other mode\'s value and passes.\nPALETTES = {\'DARK_THEME_COLORS\': DARK, \'IMAGE_MODE_COLORS\': IMAGE,\n             \'LIGHT_THEME_COLORS\': LIGHT}\n\n#: The value the plate is NOT, and the reason the distinction is worth a test.\nBOUNDARY = \'#e8e8e8\'\n\n\ndef grey(n: int) -> str:\n    v = n * GRID_STEP\n    return \'#%02x%02x%02x\' % (v, v, v)\n\n\ndef _luminance(value: str) -> float:\n    channels = [int(value.lstrip(\'#\')[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4\n                for c in channels]\n    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]\n\n\ndef _contrast(a: str, b: str) -> float:\n    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)\n    return (high + 0.05) / (low + 0.05)\n\n\ndef _dict_node(name: str) -> ast.Dict:\n    tree = ast.parse(SRC.read_text(encoding=\'utf-8-sig\'))\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            if getattr(target, \'id\', None) == name and isinstance(node.value, ast.Dict):\n                return node.value\n    raise AssertionError(f\'{name} is not a dict literal in ui/colors.py\')\n\n\ndef _entry(node: ast.Dict, key: str):\n    for k, v in zip(node.keys, node.values):\n        if isinstance(k, ast.Constant) and k.value == key:\n            return v\n    return None\n\n\n# ------------------------------------------------------------- guard the guard\n\ndef test_everything_this_file_reads_still_exists():\n    """Every assertion below reads these. Renaming a key must fail loudly here\n    rather than let the rest pass quietly over nothing."""\n    for name in NEW:\n        assert hasattr(colors, name), f\'colors has no {name}\'\n    for dict_name, keys in WIRED.items():\n        assert dict_name in PALETTES, f\'{dict_name} is not in PALETTES\'\n        for key in keys:\n            assert key in PALETTES[dict_name], f\'{dict_name} has no {key!r}\'\n\n\ndef test_the_wiring_map_is_not_empty():\n    """Every sweep below iterates WIRED. An empty map passes all of them."""\n    assert WIRED and all(WIRED.values()), \'WIRED lists nothing to check\'\n    assert sum(len(v) for v in WIRED.values()) >= 3\n\n\n# ------------------------------------------------------------------- the values\n\ndef test_the_new_constants_hold_the_registered_values():\n    """The local half of the mirror. Runs everywhere, including where\n    engine.brand is not importable -- which is exactly why it is not optional."""\n    drift = {n: getattr(colors, n) for n, (_, v) in NEW.items()\n             if getattr(colors, n) != v}\n    assert not drift, (\n        f\'these constants no longer hold their registered values: {drift}\\n\'\n        f\'If the brand moved, update this file in the same commit that updates \'\n        f\'ui/colors.py -- never one without the other.\')\n\n\ndef test_the_new_constants_match_rnv_brand():\n    """The upstream half. Skips where rnv-brand is not importable."""\n    brand = pytest.importorskip(\n        \'engine.brand\',\n        reason=\'rnv-brand not importable here; the local pin is doing the work\')\n    drift = []\n    for name, (key, _) in NEW.items():\n        theirs, mine = brand.APP[key], getattr(colors, name)\n        if mine.lower() != theirs.lower():\n            drift.append(f\'{name}: ours {mine}, theirs APP[{key!r}] {theirs}\')\n    assert not drift, \'drift from rnv-brand:\\n  \' + \'\\n  \'.join(drift)\n\n\ndef test_both_are_declared_register_owned():\n    """A classification that lives only in a test drifts from the thing it\n    classifies, so it lives in the module and is read from there."""\n    for name in NEW:\n        assert colors.APP_PROVENANCE.get(name) == \'register\', (\n            f\'{name} is not declared register-owned in APP_PROVENANCE. It was \'\n            f\'app-owned until rnv-brand registered it; the provenance is the \'\n            f\'whole change.\')\n\n\n# ------------------------------------------------------------------ the ladder\n\ndef test_the_dark_rungs_are_exact_steps_on_the_ladder():\n    """BRAND_BLACK + n * 0x10. Two of these were app-owned on the argument that\n    the ladder might not be real. It is, and this is what says so."""\n    base = int(colors.BRAND_BLACK.lstrip(\'#\'), 16)\n    for n, name in ((0, \'BRAND_BLACK\'), (1, \'APP_CARD\'), (2, \'APP_PANEL_HOVER\')):\n        want = base + n * (LADDER_STEP * 0x010101)\n        assert int(getattr(colors, name).lstrip(\'#\'), 16) == want, (\n            f\'{name} is {getattr(colors, name)}, not rung n={n} of \'\n            f\'BRAND_BLACK + n*0x10\')\n\n\ndef test_the_border_is_an_edge_and_not_a_rung():\n    """The distinction that made the ladder look incomplete. #333333 is grey(3)\n    on the ink grid, which governs inks and edges; it was never a surface."""\n    assert colors.APP_BORDER == grey(3)\n    base = int(colors.BRAND_BLACK.lstrip(\'#\'), 16)\n    rungs = {base + n * (LADDER_STEP * 0x010101) for n in range(-1, 3)}\n    assert int(colors.APP_BORDER.lstrip(\'#\'), 16) not in rungs\n\n\n# ------------------------------------------------------------------- the plate\n\ndef test_the_plate_is_a_step_on_the_ink_grid():\n    assert colors.APP_HOVER_LIGHT == grey(14) == \'#eeeeee\'\n\n\ndef test_the_plate_carries_gold_with_room_to_spare():\n    """The reason the register moved the value. Both plates clear the floor;\n    only one clears it by enough to survive the gold moving."""\n    gold = colors.BRAND_DARK_GOLD_DEEP\n    here = _contrast(gold, colors.APP_HOVER_LIGHT)\n    edge = _contrast(gold, BOUNDARY)\n    assert here >= TEXT_FLOOR, f\'gold reads {here:.4f} on the plate\'\n    assert here - TEXT_FLOOR >= 0.2, (\n        f\'the plate clears the floor by only {here - TEXT_FLOOR:.4f}. The \'\n        f\'register moved APP["hover-light"] here to get margin, not to get a \'\n        f\'pass.\')\n    assert edge - TEXT_FLOOR < 0.05, (\n        f\'{BOUNDARY} now clears the floor by {edge - TEXT_FLOOR:.4f}, so it is \'\n        f\'no longer the knife-edge this ruling was about. Either the gold moved \'\n        f\'or the floor did; re-derive before trusting the value above.\')\n\n\ndef test_the_boundary_is_not_used_as_a_hover_anywhere():\n    """A negative check needs a companion proving it is still looking, or it\n    passes by finding nothing for the wrong reason."""\n    looked = 0\n    found = []\n    for dict_name, live in PALETTES.items():\n        for key, value in live.items():\n            if \'hover\' not in key:\n                continue\n            looked += 1\n            if value.lower() == BOUNDARY:\n                found.append(f\'{dict_name}[{key!r}]\')\n    assert looked >= 3, f\'only {looked} hover keys seen -- the sweep is blind\'\n    assert not found, (\n        f\'{BOUNDARY} is being used as a hover plate: {found}. It is the ground \'\n        f\'BRAND_DARK_GOLD_DEEP is calibrated against, not an interaction state.\')\n\n\n# ------------------------------------------------- the spelling, not the value\n\ndef test_every_wired_entry_names_the_constant_not_a_literal():\n    """A literal cannot follow its base. This is the point of the pass: if the\n    register moves either value again, these move with it or this fails."""\n    literals = []\n    for dict_name, keys in WIRED.items():\n        node = _dict_node(dict_name)\n        for key in keys:\n            value = _entry(node, key)\n            if not isinstance(value, ast.Name) or value.id not in NEW:\n                literals.append(\n                    f\'{dict_name}[{key!r}] = \'\n                    f\'{ast.unparse(value) if value else "missing"}\')\n    assert not literals, (\n        \'entries still written as literals:\\n  \' + \'\\n  \'.join(literals))\n\n\ndef test_the_resolved_values_are_the_constants():\n    """The AST check above proves the spelling; this proves the value. Both,\n    because a name can be spelled correctly and resolve to something else."""\n    for dict_name, keys in WIRED.items():\n        node = _dict_node(dict_name)\n        for key in keys:\n            name = _entry(node, key).id\n            assert PALETTES[dict_name][key] == getattr(colors, name), (\n                f\'{dict_name}[{key!r}] resolves to \'\n                f\'{PALETTES[dict_name][key]}, not {name}\')\n\n\ndef test_no_literal_of_either_value_survives_in_any_palette():\n    """Completeness. The two checks above prove the keys we listed are wired;\n    this proves we did not miss one."""\n    values = {v for _, v in NEW.values()}\n    survivors = []\n    for dict_name in PALETTES:\n        node = _dict_node(dict_name)\n        for k, v in zip(node.keys, node.values):\n            if (isinstance(v, ast.Constant) and isinstance(v.value, str)\n                    and v.value.lower() in values):\n                survivors.append(f\'{dict_name}[{k.value!r}] = {v.value}\')\n    assert not survivors, (\n        \'registered values still spelled as literals:\\n  \'\n        + \'\\n  \'.join(survivors))\n'


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
