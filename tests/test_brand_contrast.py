"""
RNV Icon Builder — Brand contrast and derivation guards
========================================================
RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN

That marker tells any value-sweeping tool to skip this file. Its whole
purpose is to name retired colours -- #b19145, (177, 145, 69) -- and
assert they never come back. A sweep that rewrites those mentions turns
the guard into "#8c7337 must never equal #8c7337", which passes forever
and protects nothing. Use and mention are different things, and the file
that states a rule about a value must never be searched for that value.

These tests do not check that colours have particular values. They check
two things that a value test cannot:

  1. Every constant labelled "derived" is genuinely computed from its
     source, checked by parsing the source rather than by comparing at
     runtime. A written-down literal that happens to equal
     lighten(BRAND_DARK_GOLD, -14) is indistinguishable from the real
     thing once the module is imported -- and it is exactly what breaks
     the next time the source colour moves. Only the AST can tell them
     apart.

  2. Every foreground/background pair the app actually renders clears the
     WCAG floor, resolved against the real background in scope rather
     than against an assumed one. A census of values cannot find these:
     in almost every defect of this kind both colours are individually
     correct and it is the pairing that fails.

The exemption list is asserted in BOTH directions. An unexpected failure
fails the suite, and so does an exemption that no longer matches anything.
Exemption lists always go stale in the direction that reports clean, so
the second half is the half that matters.
"""

from __future__ import annotations

import ast
import functools
import re
import subprocess
from pathlib import Path

import pytest

from ui import colors as C


PROJECT_ROOT = Path(__file__).resolve().parent.parent
COLORS_PY = PROJECT_ROOT / "ui" / "colors.py"

TEXT_FLOOR = 4.5          # WCAG 1.4.3, normal-size text
COMPONENT_FLOOR = 3.0     # WCAG 1.4.11, UI components and graphics


# ══════════════════════════════════════════════════════════════════════════
# CONTRAST
# ══════════════════════════════════════════════════════════════════════════

def relative_luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
          for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast_ratio(fg: str, bg: str) -> float:
    l1, l2 = sorted([relative_luminance(fg), relative_luminance(bg)],
                    reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


# ══════════════════════════════════════════════════════════════════════════
# DERIVATION GUARD
# ══════════════════════════════════════════════════════════════════════════

# Constants whose docstring claims they are derived. Each must be a call
# expression in the source, not a literal.
DERIVED_CONSTANTS = {
    "BRAND_DARK_GOLD_DEEP",
    "BRAND_GOLD_RGB",
    "BRAND_DARK_GOLD_RGB",
}

# Constants that are registered brand values and must therefore be literals.
# Deriving one of these would invert the relationship: the register is the
# source, so a registered colour cannot be computed from something else.
REGISTERED_CONSTANTS = {
    "BRAND_GOLD",
    "BRAND_DARK_GOLD",
}


def _module_level_assignments() -> dict[str, ast.expr]:
    tree = ast.parse(COLORS_PY.read_text(encoding="utf-8"))
    out: dict[str, ast.expr] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                out[node.target.id] = node.value
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and node.value is not None:
                    out[t.id] = node.value
    return out


@pytest.mark.parametrize("name", sorted(DERIVED_CONSTANTS))
def test_derived_constant_is_actually_computed(name: str) -> None:
    """A derived constant must be a call, not a literal that looks right."""
    assigns = _module_level_assignments()
    assert name in assigns, (
        f"{name} is expected to exist in ui/colors.py and does not. "
        f"If it was deliberately removed, remove it from DERIVED_CONSTANTS "
        f"in this test too.")
    node = assigns[name]
    assert isinstance(node, ast.Call), (
        f"{name} is documented as derived but is assigned a literal "
        f"({ast.dump(node)[:80]}). Once it is written down it stops "
        f"tracking the colour it came from, and the next time that colour "
        f"moves this one silently does not.")


@pytest.mark.parametrize("name", sorted(REGISTERED_CONSTANTS))
def test_registered_constant_is_a_literal(name: str) -> None:
    """A registered brand value must be written down, not computed."""
    assigns = _module_level_assignments()
    assert name in assigns, f"{name} missing from ui/colors.py"
    node = assigns[name]
    assert isinstance(node, ast.Constant) and isinstance(node.value, str), (
        f"{name} is a registered brand colour and must be a literal. "
        f"Deriving it would make the register depend on the app instead "
        f"of the other way round.")


def test_deep_gold_tracks_its_source() -> None:
    """Changing BRAND_DARK_GOLD must move the derivative with it."""
    assert C.BRAND_DARK_GOLD_DEEP == C.lighten(C.BRAND_DARK_GOLD, -14)
    assert C.BRAND_DARK_GOLD_DEEP != C.BRAND_DARK_GOLD


@pytest.mark.parametrize("const,rgb", [
    ("BRAND_GOLD", "BRAND_GOLD_RGB"),
    ("BRAND_DARK_GOLD", "BRAND_DARK_GOLD_RGB"),
])
def test_rgb_tuple_matches_its_hex(const: str, rgb: str) -> None:
    """The RGB-tuple blind spot.

    A hardcoded (177, 145, 69) is invisible to every hex-based search, so
    it survives sweeps that catch every other reference to the colour.
    Deriving it removes the hiding place; this test keeps it removed.
    """
    r, g, b = getattr(C, rgb)
    assert getattr(C, const).lower() == f"#{r:02x}{g:02x}{b:02x}"


def test_lighten_preserves_hue_by_shifting_channels_uniformly() -> None:
    base = "#8c7337"
    out = C.lighten(base, -14)
    br, bg_, bb = C._to_rgb(base)
    orr, og, ob = C._to_rgb(out)
    assert (br - orr, bg_ - og, bb - ob) == (14, 14, 14)


def test_lighten_clamps_instead_of_wrapping() -> None:
    assert C.lighten("#ffffff", 40) == "#ffffff"
    assert C.lighten("#000000", -40) == "#000000"


# ══════════════════════════════════════════════════════════════════════════
# PAIRING AUDIT
# ══════════════════════════════════════════════════════════════════════════

# Pairs that render below the floor on purpose, each with the reason.
# Both halves of this dict are asserted -- see the module docstring.
ACCEPTED: dict[tuple[str, str], str] = {
    ("#000000", "#333333"):
        "main-window button hover. The main window uses a white/near-black "
        "inverse scheme in which the text stays black while the background "
        "darkens; this is the app's deliberate design, not an oversight, "
        "and it is separate from the gold dialog-button scheme.",
    ("#000000", "#444444"):
        "main-window button pressed, same inverse scheme.",
    ("#ffffff", "#d2bc93"):
        "BRAND_GOLD as a list-item fill with white text. BRAND_GOLD is a "
        "registered value and is not in scope for the dark-gold alignment. "
        "Recorded here so it stays visible rather than forgotten.",
    ("#aaaaaa", "#f5f5f5"):
        "disabled control text. WCAG 1.4.3 exempts disabled controls. Re-keyed "
        "from #ffffff on 2026-08-27 when the light panel moved to #f5f5f5 to "
        "match the other four apps -- the same text on the same control, one "
        "step of ground away.",
    ("#555555", "#1a1a1a"):
        "disabled control text, dark theme. Same exemption.",
    ("#666666", "#e0e0e0"):
        "OS-simulation chrome in context_preview.py, which reproduces "
        "platform UI so users can preview an icon in situ. It must match "
        "the platform, not the brand.",
    ("#888888", "#2a2a2a"):
        "OS-simulation chrome, dark. Same reason.",
}

_HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")

# The QSS lives inside f-strings, so its braces are doubled. Matching single
# braces here finds nothing at all -- and finding nothing reads exactly like
# finding no defects, which is why test_the_audit_finds_something_to_audit
# exists below.
#

def _rules(src: str) -> list[tuple[str, str]]:
    """Yield (selector, body) for each QSS rule in one source file.

    Deliberately a scan rather than a regex. The obvious pattern,
    ``([^{}]+?)\\{\\{(.*?)\\}\\}``, backtracks quadratically on files this
    size -- it took forty seconds per pass. The obvious fix, tightening the
    body to ``[^{}]*``, is wrong for a different reason: QSS bodies are full
    of f-string placeholders like ``{c['tab_bg']}``, so a brace-free body
    class stops dead at the first one and finds a fraction of the rules.
    Finding a fraction of the rules reads exactly like finding no defects,
    which is what test_the_audit_finds_something_to_audit is there to catch.

    The selector is the last line of text between the end of the previous
    block and the start of this one, which is where Qt's selector sits.
    """
    out = []
    cursor = 0
    while True:
        start = src.find("{{", cursor)
        if start == -1:
            break
        end = src.find("}}", start + 2)
        if end == -1:
            break
        lead = src[cursor:start].strip()
        selector = lead.splitlines()[-1].strip() if lead else ""
        out.append((selector, src[start + 2:end]))
        cursor = end + 2
    return out


def _normalise(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.lower()


def _resolve(token: str, palette: dict[str, str]) -> str | None:
    """Turn one QSS value into a concrete hex, or None if it is not one."""
    token = token.strip().rstrip(";").strip()
    if _HEX.fullmatch(token):
        return _normalise(token)
    # {c['key']} / {colors['key']} / {theme['key']}
    m = re.fullmatch(r"\{\s*\w+\[['\"]([\w\-]+)['\"]\]\s*\}", token)
    if m:
        v = palette.get(m.group(1))
        return _normalise(v) if isinstance(v, str) and _HEX.fullmatch(v) else None
    # bare {CONSTANT}
    m = re.fullmatch(r"\{\s*([A-Z_][A-Z0-9_]*)\s*\}", token)
    if m:
        v = getattr(C, m.group(1), None)
        return _normalise(v) if isinstance(v, str) and _HEX.fullmatch(v) else None
    return None


def _tracked_python_files() -> list[Path]:
    """Enumerate from git rather than from a list written down here.

    A hardcoded file list goes stale the moment a module is added, and it
    goes stale in the direction that reports clean.
    """
    r = subprocess.run(["git", "ls-files", "-z", "*.py"],
                       cwd=PROJECT_ROOT, capture_output=True, text=True)
    if r.returncode != 0:                       # not a git checkout
        return sorted(p for p in PROJECT_ROOT.rglob("*.py")
                      if "__pycache__" not in p.parts)
    return sorted((PROJECT_ROOT / n) for n in r.stdout.split("\0")
                  if n and (PROJECT_ROOT / n).exists())


@functools.lru_cache(maxsize=1)
def _sources() -> tuple[tuple[str, str], ...]:
    """(relative path, text) for every tracked Python file, read once."""
    return tuple((str(p.relative_to(PROJECT_ROOT)),
                  p.read_text(encoding="utf-8", errors="ignore"))
                 for p in _tracked_python_files())


def audit_palette(palette: dict[str, str]) -> list[tuple[str, str, float, str]]:
    findings = []
    for rel, src in _sources():
        for selector, body in _rules(src):
            fg = bg = None
            for decl in body.split(";"):
                if ":" not in decl:
                    continue
                prop, _, value = decl.partition(":")
                prop = prop.strip()
                if prop == "color":
                    fg = _resolve(value, palette)
                elif prop in ("background-color", "background"):
                    bg = _resolve(value, palette)
            if fg and bg:
                ratio = contrast_ratio(fg, bg)
                if ratio < TEXT_FLOOR:
                    findings.append((fg, bg, round(ratio, 4),
                                     f"{rel} :: {selector}"))
    return findings


def test_the_audit_finds_something_to_audit() -> None:
    """Guard the guard.

    If the QSS format changes and the rule regex stops matching, every
    contrast test below passes vacuously. This asserts the walker is still
    reaching real rules.
    """
    total = sum(len(_rules(src)) for _rel, src in _sources())
    assert total > 100, (
        f"the QSS walker matched only {total} rules across the repository, "
        f"which means it has stopped parsing the stylesheets rather than "
        f"that the stylesheets got smaller")


@pytest.mark.parametrize("theme_name", ["LIGHT", "DARK"])
def test_no_unaccepted_contrast_failures(theme_name: str) -> None:
    palette = (C.LIGHT_THEME_COLORS if theme_name == "LIGHT"
               else C.DARK_THEME_COLORS)
    bad = [f for f in audit_palette(palette) if (f[0], f[1]) not in ACCEPTED]
    assert not bad, "\n".join(
        f"  {r:>7}:1  {fg} on {bg}  <- {where}" for fg, bg, r, where in bad)


def test_every_exemption_still_applies() -> None:
    """The half that matters.

    An exemption for a pairing that no longer exists is an exemption that
    will silently cover a future defect. Removing dead entries keeps the
    list honest.
    """
    seen = set()
    for palette in (C.LIGHT_THEME_COLORS, C.DARK_THEME_COLORS):
        for fg, bg, _r, _w in audit_palette(palette):
            seen.add((fg, bg))
    dead = sorted(k for k in ACCEPTED if k not in seen)
    assert not dead, (
        "these exemptions no longer match anything the app renders and "
        f"should be deleted: {dead}")


# ══════════════════════════════════════════════════════════════════════════
# THE TWO GOLD ROLES
# ══════════════════════════════════════════════════════════════════════════
#
# Light mode uses exactly two golds, because one cannot do both jobs: a
# gold light enough to carry white text at 4.5:1 is too light to BE text
# on anything but pure white. The luminance bands do not overlap.

LIGHT_SURFACES = ["#ffffff", "#fafafa", "#f5f5f5", "#f0f0f0", "#eeeeee"]


def test_fill_gold_carries_white_text() -> None:
    assert contrast_ratio("#ffffff", C.BRAND_DARK_GOLD) >= TEXT_FLOOR


def test_text_gold_clears_every_light_surface() -> None:
    failures = [(s, round(contrast_ratio(C.BRAND_DARK_GOLD_DEEP, s), 4))
                for s in LIGHT_SURFACES
                if contrast_ratio(C.BRAND_DARK_GOLD_DEEP, s) < TEXT_FLOOR]
    assert not failures, (
        f"the text gold no longer clears every light surface: {failures}")


@pytest.mark.parametrize("key", [
    "text_accent", "button_hover_text", "accent_button_text",
])
def test_gold_text_keys_use_the_text_gold(key: str) -> None:
    assert C.LIGHT_THEME_COLORS[key] == C.BRAND_DARK_GOLD_DEEP


@pytest.mark.parametrize("key", [
    "selected_bg", "button_pressed_bg", "accent_button_pressed_bg",
    "checkbox_checked_bg", "list_selected_bg",
])
def test_gold_fill_keys_use_the_fill_gold(key: str) -> None:
    """Fills must not take the text gold: it does not carry white text."""
    assert C.LIGHT_THEME_COLORS[key] == C.BRAND_DARK_GOLD


def test_tab_hover_ground_is_light_enough_for_gold_text() -> None:
    """The hover tab reads as hover because the ground LIGHTENS toward the
    selected tab's white, and the gold text stays legible on it."""
    ground = C.LIGHT_THEME_COLORS["tab_hover_bg"]
    rest = C.LIGHT_THEME_COLORS["tab_bg"]
    assert relative_luminance(ground) > relative_luminance(rest)
    assert contrast_ratio(C.LIGHT_THEME_COLORS["text_accent"],
                          ground) >= TEXT_FLOOR


def test_tab_indicator_clears_the_component_floor() -> None:
    assert contrast_ratio(C.LIGHT_THEME_COLORS["tab_indicator"],
                          C.LIGHT_THEME_COLORS["tab_selected_bg"]
                          ) >= COMPONENT_FLOOR


# ══════════════════════════════════════════════════════════════════════════
# SCHEME SEPARATION
# ══════════════════════════════════════════════════════════════════════════
#
# The app runs two button schemes side by side. Conflating them is the
# easiest way to "fix" one by breaking the other.

@pytest.mark.parametrize("palette_name", ["LIGHT", "DARK"])
def test_main_button_scheme_holds_no_gold(palette_name: str) -> None:
    """Main-window buttons are the white/near-black inverse system. No
    brand gold belongs anywhere in them."""
    palette = (C.LIGHT_THEME_COLORS if palette_name == "LIGHT"
               else C.DARK_THEME_COLORS)
    golds = {C.BRAND_GOLD.lower(), C.BRAND_DARK_GOLD.lower(),
             C.BRAND_DARK_GOLD_DEEP.lower()}
    offenders = {k: v for k, v in palette.items()
                 if k.startswith("main_btn_") and v.lower() in golds}
    assert not offenders, (
        f"gold leaked into the main-window button scheme: {offenders}")


def test_retired_app_gold_is_gone() -> None:
    """#b19145 was an app-local approximation of the brand dark gold. It
    carried white text at 2.9976:1. Nothing should reintroduce it."""
    for palette in (C.LIGHT_THEME_COLORS, C.DARK_THEME_COLORS,
                    C.IMAGE_MODE_COLORS):
        assert not [k for k, v in palette.items()
                    if isinstance(v, str) and v.lower() == "#b19145"]


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

_BYPASS = re.compile(r"\{BRAND_[A-Z_]+\}")


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
    "RNV_Icon_Builder.py :: background-color: {BRAND_GOLD};":
        "correct: image-mode stylesheet block, and image mode is dark-based",
    "ui/preview_utils.py :: border: 2px solid {BRAND_GOLD};":
        "correct: a hover border drawn over an arbitrary user colour swatch, "
        "so the ground is the swatch and not a themed surface -- the same "
        "reason as the settings_dialog entry below. NOTE the reason here used "
        "to read 'mode-guarded by the caller', which was not true of this site "
        "and was copied to three entries. One of the three, metadata_panel, "
        "had no caller at all.",
    "ui/preview_utils.py :: border-color: {BRAND_GOLD};":
        "correct: the same swatch case, on the colour button rather than the "
        "swatch frame",
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


#: Bypasses that are correct and PERMANENT: a hover border drawn over a colour
#: the user chose can never read the palette, because the ground is the user's
#: colour. They are the anchor for the scan, since a bare count goes stale the
#: moment a real bypass is fixed -- which is what happened on 2026-08-30, when
#: three were fixed and the count fell below the threshold that was supposed to
#: prove the scan still worked.
PERMANENT_BYPASSES = (
    "ui/settings_dialog.py :: border-color: {BRAND_GOLD};",
    "ui/preview_utils.py :: border-color: {BRAND_GOLD};",
    "ui/preview_utils.py :: border: 2px solid {BRAND_GOLD};",
)


def test_the_bypass_scan_is_still_looking():
    """A scan that finds nothing reports no unreviewed sites and passes, which
    is indistinguishable from a clean repo. Anchored on sites that cannot stop
    being bypasses rather than on how many there happen to be."""
    sites = set(_bypass_sites())
    missing = [s for s in PERMANENT_BYPASSES if s not in sites]
    assert not missing, (
        "the bypass scan no longer finds sites that cannot have been fixed: "
        + "; ".join(missing) + " -- the scan has stopped looking, or the "
        "declaration text moved and every REVIEWED key with it.")


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
        assert lum(pal["accent_hover"]) > lum(pal["text_accent"]),             f"{name} hover must go lighter, away from a dark ground"
    light = _PALETTES["LIGHT"]
    assert lum(light["accent_hover"]) < lum(C.BRAND_DARK_GOLD),         "light hover must go deeper, away from a light ground"
