"""
RNV Icon Builder — Brand contrast and derivation guards
========================================================

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
    ("#aaaaaa", "#ffffff"):
        "disabled control text. WCAG 1.4.3 exempts disabled controls.",
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
