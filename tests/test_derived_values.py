"""Derived values: a palette entry that is a register value AT AN ALPHA.

A palette entry used to be one of two things here -- a name, or a literal --
and this file adds the third the application always had and never declared.
rgba(26, 26, 26, 0.93) is not a second colour beside BRAND_BLACK; it IS
BRAND_BLACK, at 93%, and nothing related the two.

WHY THAT MATTERED. RNV-COLLAPSE-505050 ruled #505050 onto GREY_44 on
2026-09-02. It went on painting here, and in three other applications, because
the alpha form was written out as rgba() and every sweep in the fleet compares
six-digit hex. A written-down derivative is orphaned the moment its source
moves, and nothing says so.

AND OS_SIM_COLORS IS THE OPPOSITE RULE. It depicts Windows, macOS and Chrome.
Its own comment says these values "must NOT follow the app theme", and six of
them were bound to RNV constants -- so APP_BORDER moved Chrome's tab title
with it. For that dict the check is an EXCLUSION: no RNV constant may appear.
"""
from __future__ import annotations

import ast
import pathlib
import re

from ui import colors
from ui.colors import (DARK_THEME_COLORS as DARK,
                       LIGHT_THEME_COLORS as LIGHT,
                       IMAGE_MODE_COLORS as IMAGE,
                       OS_SIM_COLORS as OS_SIM,
                       translucent)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "ui" / "colors.py"

MODE_DICTS = ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS")
PALETTES = {"DARK_THEME_COLORS": DARK, "LIGHT_THEME_COLORS": LIGHT,
            "IMAGE_MODE_COLORS": IMAGE}

#: constant -> the byte, and the float spelling it replaced. MEASURED through
#: Qt's own stylesheet parser on three grounds: Qt truncates, so 0.3 is 76.
ALPHAS = {
    "SCRIM_ALPHA": (0xED, "0.93"),
    "DROPZONE_ALPHA_DARK": (0x33, "0.2"),
    "DROPZONE_ALPHA_LIGHT": (0x4C, "0.3"),
    "SCROLLBAR_HANDLE_ALPHA": (0x96, "150"),
    "SCROLLBAR_BORDER_ALPHA": (0x64, "100"),
}

#: every notation a colour can wear here, longest first so that #ED1A1A1A is
#: not also read as 1A1A1A and #333333 is not also read as #333.
COMPOSED = re.compile(r"rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}"
                      r"\s*(?:,\s*[0-9.]+\s*)?\)")
HEX8 = re.compile(r"#[0-9a-fA-F]{8}\b")


def _dicts(names):
    tree = ast.parse(SRC.read_text(encoding="utf-8-sig"))
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = (node.targets[0] if isinstance(node, ast.Assign)
                      else node.target)
            if (getattr(target, "id", None) in names
                    and isinstance(node.value, ast.Dict)):
                out[target.id] = node.value
    missing = set(names) - set(out)
    assert not missing, f"palettes that are no longer dict literals: {missing}"
    return out


# ------------------------------------------------------------ guard the guard

def test_translucent_composes_alpha_first():
    """#AARRGGBB, not #RRGGBBAA. Taking the wrong end gives a real colour and
    the wrong one, which is the failure that does not look like a failure."""
    assert translucent("#1a1a1a", 0xED) == "#ed1a1a1a"
    assert translucent("1a1a1a", 0xED) == "#ed1a1a1a"
    assert translucent("#D2BC93", 0x33) == "#33d2bc93"


def test_translucent_refuses_what_it_cannot_compose():
    for bad in (-1, 256, 999):
        try:
            translucent("#1a1a1a", bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"alpha {bad} was accepted")
    for bad in ("#1a1a1", "#1a1a1a1a", "nonsense"):
        try:
            translucent(bad, 0xED)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{bad!r} was accepted as a base")


def test_the_alphas_are_the_measured_bytes():
    """Each constant holds the byte Qt produces for the spelling it replaced.
    Qt TRUNCATES: 0.3 * 255 is 76.5 and Qt gives 76. Rounding here would move
    a pixel in a round that says it moves one, and names which."""
    for name, (byte, _was) in ALPHAS.items():
        assert hasattr(colors, name), f"ui.colors has no {name}"
        assert getattr(colors, name) == byte, (
            f"{name} is {getattr(colors, name):#x}, measured {byte:#x}")


# ----------------------------------------------------------- the derivations

def test_every_derived_entry_names_a_constant_that_exists():
    """A derived entry is translucent(BASE, ALPHA) where both are names. A
    literal in either position is the thing this round removed."""
    bad = []
    for dict_name, node in _dicts(MODE_DICTS).items():
        for key, value in zip(node.keys, node.values):
            if not (isinstance(value, ast.Call)
                    and getattr(value.func, "id", None) == "translucent"):
                continue
            where = f"{dict_name}[{key.value!r}]"
            if len(value.args) != 2:
                bad.append(f"{where} takes {len(value.args)} arguments")
                continue
            base, alpha = value.args
            for pos, arg in (("base", base), ("alpha", alpha)):
                if not isinstance(arg, ast.Name):
                    bad.append(f"{where} {pos} is a literal, not a name")
                elif not hasattr(colors, arg.id):
                    bad.append(f"{where} {pos} names {arg.id}, which does not "
                               f"exist in ui.colors")
            if isinstance(alpha, ast.Name) and alpha.id not in ALPHAS:
                bad.append(f"{where} uses alpha {alpha.id}, which is not one "
                           f"of the declared composite alphas")
    assert not bad, "derived entries that do not derive:\n  " + "\n  ".join(bad)


def test_every_derived_entry_decomposes_to_its_base_and_its_alpha():
    """The relationship, checked by TAKING THE VALUE APART rather than by
    building it again.

    The first version of this recomputed the entry with translucent() and
    compared -- which is very nearly vacuous, because the dict entry IS
    translucent(BASE, ALPHA) evaluated at import. The two sides came from the
    same call, so the assertion held whatever translucent() did, and the only
    things it could ever have caught were a palette mutated after definition
    or a duplicate dict where the AST and the runtime disagree.

    Decomposition is independent of the composing function: the last six
    digits must BE the base and the first two must BE the alpha. A bug in
    translucent() now fails here, which was the point."""
    wrong = []
    for dict_name, node in _dicts(MODE_DICTS).items():
        for key, value in zip(node.keys, node.values):
            if not (isinstance(value, ast.Call)
                    and getattr(value.func, "id", None) == "translucent"):
                continue
            base, alpha = value.args
            got = PALETTES[dict_name][key.value]
            where = f"{dict_name}[{key.value!r}]"
            want_base = getattr(colors, base.id).lstrip("#").lower()
            want_alpha = getattr(colors, alpha.id)
            if len(got) != 9 or not got.startswith("#"):
                wrong.append(f"{where} is {got}, not #AARRGGBB")
                continue
            if got[3:].lower() != want_base:
                wrong.append(f"{where} is {got}, whose colour half is not "
                             f"{base.id} #{want_base}")
            if int(got[1:3], 16) != want_alpha:
                wrong.append(f"{where} composites at {got[1:3]}, not "
                             f"{alpha.id} {want_alpha:#04x}")
    assert not wrong, "derived entries that do not match:\n  " + "\n  ".join(wrong)


def test_no_composed_literal_is_left_in_a_mode_palette():
    """The completeness half. A composed literal cannot follow its base, so
    there must not be one left in a palette this application themes."""
    strays = []
    for dict_name, node in _dicts(MODE_DICTS).items():
        for key, value in zip(node.keys, node.values):
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                if COMPOSED.search(value.value) or HEX8.search(value.value):
                    strays.append(f"{dict_name}[{key.value!r}] = "
                                  f"{value.value}")
    assert not strays, (
        "composed values still written out rather than derived:\n  "
        + "\n  ".join(strays))


# -------------------------------------------------------- the exclusion rule

def test_os_sim_holds_no_rnv_constant():
    """OS_SIM_COLORS depicts Windows, macOS and Chrome. Its own comment says
    these "must NOT follow the app theme", and six of them named RNV constants
    -- so APP_BORDER moved Chrome's tab title with it. Two identical numbers
    doing unrelated jobs must stay separate; binding them couples things that
    should move independently.

    #333333 being a plausible tab title is a coincidence, not a wiring."""
    bound = []
    for _name, node in _dicts(("OS_SIM_COLORS",)).items():
        for key, value in zip(node.keys, node.values):
            if isinstance(value, ast.Name):
                bound.append(f"OS_SIM_COLORS[{key.value!r}] -> {value.id}")
            elif isinstance(value, ast.Call):
                bound.append(f"OS_SIM_COLORS[{key.value!r}] is computed from "
                             f"the application's own values")
    assert not bound, (
        "a depiction of another system's chrome, bound to this brand's "
        "register:\n  " + "\n  ".join(bound))


def test_os_sim_still_paints_what_it_did():
    """Unbinding must not have moved a colour. These are the six that were
    named, with the values those names held."""
    assert OS_SIM["taskbar_border"] == "#333333"
    assert OS_SIM["taskbar_text_light"] == "#000000"
    assert OS_SIM["explorer_text"] == "#000000"
    assert OS_SIM["finder_text"] == "#333333"
    assert OS_SIM["chrome_tab_title"] == "#333333"
    assert OS_SIM["bookmarks_text"] == "#333333"


# ------------------------------------------------- the bug deriving fixed

def test_the_image_palette_values_are_readable_by_qcolor():
    """_apply_image_mode_palette() calls QColor() on these. QColor cannot
    parse rgba() -- it is a stylesheet notation -- and returns an INVALID
    colour, which Qt renders as opaque black. Every input field in image mode
    was black rather than the card at 93%.

    This is why the derived form is #AARRGGBB: it is the only spelling that
    works in both a stylesheet and a QColor."""
    from PyQt6.QtGui import QColor
    for key in ("window_bg", "input_bg"):
        value = IMAGE[key]
        colour = QColor(value)
        assert colour.isValid(), (
            f"QColor({value!r}) is invalid, so QPalette gets opaque black")
        assert colour.alpha() == 0xED, (
            f"{key} composites at {colour.alpha()}, not SCRIM_ALPHA")


def test_the_scrollbar_handle_is_grey_44_and_not_the_collapsed_value():
    """RNV-COLLAPSE-505050, closed here on 2026-09-24. Ruled 2026-09-02,
    survived in four applications because the alpha form was written out."""
    handle = IMAGE["scrollbar_handle"]
    assert handle == translucent(colors.GREY_44, colors.SCROLLBAR_HANDLE_ALPHA)
    assert "505050" not in handle.lower(), f"{handle} is still #505050"
    assert handle[3:].lower() == colors.GREY_44.lstrip("#").lower()

# RNV-DERIVE-ALPHA


# ------------------------------------------------ eight-digit hex, lower case
# RNV-LOWER-EIGHT-GUARD, 2026-09-29: the test the transformer, the picker and
# the palette manager gained on 2026-09-25, added here by ruling ("Add the
# same test"). This application already wrote lower case, so nothing else
# moves; the register's Notation section (rev 42) says each app's guard holds
# its eight-digit values to lower case, and until now this one did not.

LOWER8_MODULES = ('ui.colors', 'ui.preview_utils', 'ui.theme_manager')
#: Found when this was written; below the floor, the sweep has gone blind.
LOWER8_FLOOR = 21
LOWER8_FILES = 38


def _bare_strings(tree: ast.AST) -> set[int]:
    """The ids of string constants that stand alone as statements --
    docstrings and bare strings -- which are prose, not values."""
    bare = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list):
            for st in body:
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant):
                    bare.add(id(st.value))
    return bare


def _lower8_values():
    """(where, value) for every eight-digit hex string the colour modules
    build -- their constants, the dicts they hold, and their classes' dicts
    -- as they EVALUATE, which is what a derived value is."""
    import importlib

    def walk(where, value):
        if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{8}", value):
            yield where, value
        elif isinstance(value, dict):
            for key, item in value.items():
                yield from walk(f"{where}[{key!r}]", item)

    for name in LOWER8_MODULES:
        module = importlib.import_module(name)
        for attr, value in vars(module).items():
            if attr.startswith("__"):
                continue
            if isinstance(value, type) and value.__module__ == name:
                for cattr, cvalue in vars(value).items():
                    if not cattr.startswith("__"):
                        yield from walk(f"{name}.{attr}.{cattr}", cvalue)
            else:
                yield from walk(f"{name}.{attr}", value)


def _lower8_trees():
    """Application source: not tests, not a root test suite, not a delivery
    script. BOM-aware."""
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if any(p in {".git", "tests", "snapshots", "build", "dist", ".venv",
                     "venv", "__pycache__"} for p in rel.parts):
            continue
        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):
            continue
        text = path.read_bytes().decode("utf-8-sig", errors="replace")
        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
            continue
        yield rel, ast.parse(text)


def test_eight_digit_hex_is_lower_case():
    """RNV-LOWER-EIGHT, 2026-09-25. The register writes hex in lower case --
    Notation, ruled 2026-08-15, Brand Book decision #19 -- and on 2026-09-25
    Chris ruled that eight digits are hex too: #ed1a1a1a, never #ED1A1A1A.
    Qt reads either case. This application's helper wrote lower case from
    the start; this holds it there.

    Both halves: every eight-digit value the application BUILDS, as its
    colour modules evaluate, and every eight-digit literal it WRITES in code.
    Docstrings are prose, and a sentence that names an upper-case value as
    history keeps its case."""
    built = list(_lower8_values())
    assert len(built) >= LOWER8_FLOOR, (
        f"only {len(built)} eight-digit values found; the sweep has gone blind")
    upper = [f"{where} = {value}" for where, value in built
             if value != value.lower()]
    written, files = [], 0
    for rel, tree in _lower8_trees():
        files += 1
        bare = _bare_strings(tree)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and id(node) not in bare):
                for hex8 in re.findall(r"#[0-9a-fA-F]{8}\b", node.value):
                    if hex8 != hex8.lower():
                        written.append(f"{rel}:{node.lineno}  {hex8}")
    assert files >= LOWER8_FILES, f"only {files} files swept"
    assert not upper, "built in upper case:\n  " + "\n  ".join(upper)
    assert not written, "written in upper case:\n  " + "\n  ".join(written)
