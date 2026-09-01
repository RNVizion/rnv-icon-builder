"""The dark ladder's top rung and the light plate, both now registered.

WHAT THIS PASS DID. rnv-brand rev 22 registered the two ends of the dark
surface ladder -- APP["canvas"] #0a0a0a and APP["panel-hover"] #3a3a3a -- and
rev 23 registered APP["hover-light"] #eeeeee. Both were app-owned here. This
app holds panel-hover and hover-light; it has no canvas surface. Neither value
changed: the pass changes provenance and spelling, not pixels.

WHY THE LADDER WAS NOT "TWO-THIRDS SPECIFIED". The register originally said it
was, because APP["border"] #333333 is not #3a3a3a and so looked like a missing
rung. It is not a rung at all -- #333333 is grey(3) on the INK grid, which
governs inks and EDGES, and a border is an edge. The ladder was complete when
the question was first asked; it was measured against the wrong family.

    BRAND_BLACK + n * 0x10,  n in -1..+2
    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover

WHY THE PLATE IS #eeeeee AND NOT #e8e8e8. #e8e8e8 is the ground
BRAND_DARK_GOLD_DEEP is calibrated against: the smallest uniform step that
clears it is -14, and -13 gives 4.4675 and fails. Registering it as the hover
would have put every hover in the app on the one value the gold cannot afford
to lose, with 0.0334 of margin. A boundary is not a plate. #eeeeee is grey(14),
one step inside, and gold reads 4.7875 on it. The margin is asserted below
rather than described, because a comment cannot fail.

#e8e8e8 keeps everything else it had -- registered, the published gold-as-text
boundary, the binding ground. It is simply not the hover.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from ui import colors
from ui.colors import (DARK_THEME_COLORS as DARK,
                       IMAGE_MODE_COLORS as IMAGE,
                       LIGHT_THEME_COLORS as LIGHT)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'ui/colors.py'

GRID_STEP = 0x11
LADDER_STEP = 0x10
TEXT_FLOOR = 4.5

#: Constant name -> the register key it mirrors, and the value both hold.
NEW = {'APP_PANEL_HOVER': ('panel-hover', '#3a3a3a'),
       'APP_HOVER_LIGHT': ('hover-light', '#eeeeee')}

#: palette dict name -> the keys in it that must now name the constant.
WIRED = {
    'DARK_THEME_COLORS': ('hover_bg', 'dialog_btn_hover_bg',
                          'list_hover_bg'),
    'LIGHT_THEME_COLORS': ('hover_bg', 'dialog_btn_hover_bg',
                           'dialog_btn_accent_hover_bg',
                           'tab_hover_bg', 'list_hover_bg'),
}

#: dict NAME -> the live dict. Looking a key up in the wrong palette is how a
#: per-mode difference gets checked against the other mode's value and passes.
PALETTES = {'DARK_THEME_COLORS': DARK, 'IMAGE_MODE_COLORS': IMAGE,
             'LIGHT_THEME_COLORS': LIGHT}

#: The value the plate is NOT, and the reason the distinction is worth a test.
BOUNDARY = '#e8e8e8'


def grey(n: int) -> str:
    v = n * GRID_STEP
    return '#%02x%02x%02x' % (v, v, v)


def _luminance(value: str) -> float:
    channels = [int(value.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _dict_node(name: str) -> ast.Dict:
    tree = ast.parse(SRC.read_text(encoding='utf-8-sig'))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(target, 'id', None) == name and isinstance(node.value, ast.Dict):
                return node.value
    raise AssertionError(f'{name} is not a dict literal in ui/colors.py')


def _entry(node: ast.Dict, key: str):
    for k, v in zip(node.keys, node.values):
        if isinstance(k, ast.Constant) and k.value == key:
            return v
    return None


# ------------------------------------------------------------- guard the guard

def test_everything_this_file_reads_still_exists():
    """Every assertion below reads these. Renaming a key must fail loudly here
    rather than let the rest pass quietly over nothing."""
    for name in NEW:
        assert hasattr(colors, name), f'colors has no {name}'
    for dict_name, keys in WIRED.items():
        assert dict_name in PALETTES, f'{dict_name} is not in PALETTES'
        for key in keys:
            assert key in PALETTES[dict_name], f'{dict_name} has no {key!r}'


def test_the_wiring_map_is_not_empty():
    """Every sweep below iterates WIRED. An empty map passes all of them."""
    assert WIRED and all(WIRED.values()), 'WIRED lists nothing to check'
    assert sum(len(v) for v in WIRED.values()) >= 3


# ------------------------------------------------------------------- the values

def test_the_new_constants_hold_the_registered_values():
    """The local half of the mirror. Runs everywhere, including where
    engine.brand is not importable -- which is exactly why it is not optional."""
    drift = {n: getattr(colors, n) for n, (_, v) in NEW.items()
             if getattr(colors, n) != v}
    assert not drift, (
        f'these constants no longer hold their registered values: {drift}\n'
        f'If the brand moved, update this file in the same commit that updates '
        f'ui/colors.py -- never one without the other.')


def test_the_new_constants_match_rnv_brand():
    """The upstream half. Skips where rnv-brand is not importable."""
    brand = pytest.importorskip(
        'engine.brand',
        reason='rnv-brand not importable here; the local pin is doing the work')
    drift = []
    for name, (key, _) in NEW.items():
        theirs, mine = brand.APP[key], getattr(colors, name)
        if mine.lower() != theirs.lower():
            drift.append(f'{name}: ours {mine}, theirs APP[{key!r}] {theirs}')
    assert not drift, 'drift from rnv-brand:\n  ' + '\n  '.join(drift)


def test_both_are_declared_register_owned():
    """A classification that lives only in a test drifts from the thing it
    classifies, so it lives in the module and is read from there."""
    for name in NEW:
        assert colors.APP_PROVENANCE.get(name) == 'register', (
            f'{name} is not declared register-owned in APP_PROVENANCE. It was '
            f'app-owned until rnv-brand registered it; the provenance is the '
            f'whole change.')


# ------------------------------------------------------------------ the ladder

def test_the_dark_rungs_are_exact_steps_on_the_ladder():
    """BRAND_BLACK + n * 0x10. Two of these were app-owned on the argument that
    the ladder might not be real. It is, and this is what says so."""
    base = int(colors.BRAND_BLACK.lstrip('#'), 16)
    for n, name in ((0, 'BRAND_BLACK'), (1, 'APP_CARD'), (2, 'APP_PANEL_HOVER')):
        want = base + n * (LADDER_STEP * 0x010101)
        assert int(getattr(colors, name).lstrip('#'), 16) == want, (
            f'{name} is {getattr(colors, name)}, not rung n={n} of '
            f'BRAND_BLACK + n*0x10')


def test_the_border_is_an_edge_and_not_a_rung():
    """The distinction that made the ladder look incomplete. #333333 is grey(3)
    on the ink grid, which governs inks and edges; it was never a surface."""
    assert colors.APP_BORDER == grey(3)
    base = int(colors.BRAND_BLACK.lstrip('#'), 16)
    rungs = {base + n * (LADDER_STEP * 0x010101) for n in range(-1, 3)}
    assert int(colors.APP_BORDER.lstrip('#'), 16) not in rungs


# ------------------------------------------------------------------- the plate

def test_the_plate_is_a_step_on_the_ink_grid():
    assert colors.APP_HOVER_LIGHT == grey(14) == '#eeeeee'


def test_the_plate_carries_gold_with_room_to_spare():
    """The reason the register moved the value. Both plates clear the floor;
    only one clears it by enough to survive the gold moving."""
    gold = colors.BRAND_DARK_GOLD_DEEP
    here = _contrast(gold, colors.APP_HOVER_LIGHT)
    edge = _contrast(gold, BOUNDARY)
    assert here >= TEXT_FLOOR, f'gold reads {here:.4f} on the plate'
    assert here - TEXT_FLOOR >= 0.2, (
        f'the plate clears the floor by only {here - TEXT_FLOOR:.4f}. The '
        f'register moved APP["hover-light"] here to get margin, not to get a '
        f'pass.')
    assert edge - TEXT_FLOOR < 0.05, (
        f'{BOUNDARY} now clears the floor by {edge - TEXT_FLOOR:.4f}, so it is '
        f'no longer the knife-edge this ruling was about. Either the gold moved '
        f'or the floor did; re-derive before trusting the value above.')


def test_the_boundary_is_not_used_as_a_hover_anywhere():
    """A negative check needs a companion proving it is still looking, or it
    passes by finding nothing for the wrong reason."""
    looked = 0
    found = []
    for dict_name, live in PALETTES.items():
        for key, value in live.items():
            if 'hover' not in key:
                continue
            looked += 1
            if value.lower() == BOUNDARY:
                found.append(f'{dict_name}[{key!r}]')
    assert looked >= 3, f'only {looked} hover keys seen -- the sweep is blind'
    assert not found, (
        f'{BOUNDARY} is being used as a hover plate: {found}. It is the ground '
        f'BRAND_DARK_GOLD_DEEP is calibrated against, not an interaction state.')


# ------------------------------------------------- the spelling, not the value

def test_every_wired_entry_names_the_constant_not_a_literal():
    """A literal cannot follow its base. This is the point of the pass: if the
    register moves either value again, these move with it or this fails."""
    literals = []
    for dict_name, keys in WIRED.items():
        node = _dict_node(dict_name)
        for key in keys:
            value = _entry(node, key)
            if not isinstance(value, ast.Name) or value.id not in NEW:
                literals.append(
                    f'{dict_name}[{key!r}] = '
                    f'{ast.unparse(value) if value else "missing"}')
    assert not literals, (
        'entries still written as literals:\n  ' + '\n  '.join(literals))


def test_the_resolved_values_are_the_constants():
    """The AST check above proves the spelling; this proves the value. Both,
    because a name can be spelled correctly and resolve to something else."""
    for dict_name, keys in WIRED.items():
        node = _dict_node(dict_name)
        for key in keys:
            name = _entry(node, key).id
            assert PALETTES[dict_name][key] == getattr(colors, name), (
                f'{dict_name}[{key!r}] resolves to '
                f'{PALETTES[dict_name][key]}, not {name}')


def test_no_literal_of_either_value_survives_in_any_palette():
    """Completeness. The two checks above prove the keys we listed are wired;
    this proves we did not miss one."""
    values = {v for _, v in NEW.values()}
    survivors = []
    for dict_name in PALETTES:
        node = _dict_node(dict_name)
        for k, v in zip(node.keys, node.values):
            if (isinstance(v, ast.Constant) and isinstance(v.value, str)
                    and v.value.lower() in values):
                survivors.append(f'{dict_name}[{k.value!r}] = {v.value}')
    assert not survivors, (
        'registered values still spelled as literals:\n  '
        + '\n  '.join(survivors))
