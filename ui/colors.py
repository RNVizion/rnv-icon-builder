"""
RNV Icon Builder - Color Definitions
Centralized color palette for consistent branding.
"""

from __future__ import annotations
from typing import Final

# ==================== Brand Colors ====================
# Registered values are sourced from RNVizion/rnv-brand (engine/brand.py).
# Derived values are COMPUTED from their source below, never written down,
# so a derivative cannot drift away from the colour it was derived from.


def _to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Split a 6-digit hex colour into an (r, g, b) tuple."""
    h = hex_color.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def lighten(hex_color: str, step: int) -> str:
    """Shift every channel by the same number of 8-bit steps.

    A uniform per-channel shift preserves the hue exactly, which is what
    keeps a derived gold recognisably the same gold. Negative darkens.
    """
    r, g, b = _to_rgb(hex_color)
    return '#%02x%02x%02x' % tuple(
        max(0, min(255, c + step)) for c in (r, g, b)
    )


BRAND_GOLD: Final[str] = "#d2bc93"
"""Primary brand gold - use for hover states, highlights, tooltips, accents.

Registered brand value.
"""

BRAND_DARK_GOLD: Final[str] = "#8c7337"
"""Brand dark gold - light-mode FILLS, borders and pressed states.

Registered brand value. Carries white text at 4.5429:1. It is a fill
colour: as text it clears 4.5:1 only against pure white, which is why
BRAND_DARK_GOLD_DEEP exists.
"""

BRAND_DARK_GOLD_DEEP: Final[str] = lighten(BRAND_DARK_GOLD, -14)  # -> #7e6529
"""Derived from BRAND_DARK_GOLD - light-mode gold TEXT on grey surfaces.

Every light surface in this app below #ffffff leaves BRAND_DARK_GOLD short
as text (#fafafa 4.35, #f0f0f0 3.99, #eeeeee 3.92). This derivative clears
the whole band (#eeeeee 4.79). It is a TEXT colour only - it carries white
text at just 5.55:1 against black-on-gold's 3.78:1, so it must not become
a fill.
"""

BRAND_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_GOLD)
"""Brand gold as an RGB tuple, derived from the hex above.

Derived rather than written down: a hardcoded tuple is invisible to every
hex-based search, so it survives sweeps that catch every other reference.
"""

BRAND_DARK_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_DARK_GOLD)
"""Brand dark gold as an RGB tuple, derived from the hex above."""


# ==================== APP Neutrals ====================
#
# MIRRORED FROM RNVizion/rnv-brand engine/brand.py APP. Until 2026-08-28 these
# were bare hex literals in the palettes below -- no constant, no provenance --
# and every one of them is a REGISTERED brand value. A registered value could
# move upstream and this app would keep the old one silently, which is the
# failure #c4a458 had, one level down. It nearly happened: APP["text"] moved
# from #e0e0e0 to #dddddd in rnv-brand@68d195e.
#
# THE INK GRID, published in the brand beside that move:
#
#     grey(n) = n * 0x11, n in 0..15.   TRUE_BLACK -> WHITE in fifteen steps.
#
# IT GOVERNS INKS AND EDGES AND DELIBERATELY DOES NOT GOVERN SURFACES.
# BRAND_BLACK sits at n = 1.53 and APP_CARD at n = 2.47; BRAND_BLACK is a
# permanent and will not move to fit a ladder. The scope is part of the rule.
#
# THIS PASS WIRES THE INK ONLY. The other five constants are defined and
# mirrored here so drift is caught, but the palettes below still spell them as
# literals; rewiring those is the grey-ramp derivation pass, and doing it here
# would have mixed a mechanical substitution into a value change.

TRUE_BLACK: Final[str] = "#000000"
"""engine/brand.py TRUE_BLACK, and APP["window"]. Primary text in light mode,
and the label on a pressed control in dark. grey(0)."""

WHITE: Final[str] = "#ffffff"
"""engine/brand.py WHITE. Control surface in light mode. grey(15)."""

BRAND_BLACK: Final[str] = "#1a1a1a"
"""engine/brand.py BRAND_BLACK, and APP["panel"]. Charcoal; a permanent.
Not on the ink grid (n = 1.53) and not required to be -- it is a surface."""

APP_CARD: Final[str] = "#2a2a2a"
"""engine/brand.py APP["card"]. A surface, not on the grid (n = 2.47)."""

STATUS_SUCCESS: Final[str] = "#926c89"
"""MIRRORS the register's STATUS["success"]. A FILL.

RNV-STATUS-FAMILY (2026-09-03): was #28a745, Bootstrap's green. Retired
because it and Bootstrap's red collapsed to one olive under deuteranopia at
about 4 apart -- success and error are the two most consequential colours in
an interface, and roughly 8% of men could not tell them apart.

It is a FILL and cannot carry text: 3.92 on #1a1a1a, 3.23 on #2a2a2a, above
the 3:1 fill floor and below the 4.5:1 text floor. That is not a shortcoming,
it is the fill band -- a value that works on a dark AND a light ground sits at
L* 48-59 by arithmetic, and a mid-tone reaches 4.5 on neither side.

RNV-STATUS-REGISTER (2026-09-02): both palettes already held this value,
written out rather than named. Named here so it has one home. Defined above
the palettes because they consume it.
"""

STATUS_WARNING: Final[str] = "#a2703c"
"""MIRRORS the register's STATUS["warning"]. A FILL.

RNV-STATUS-FAMILY (2026-09-03): was #ffc107, retired on arithmetic rather
than taste -- it read 1.63 on #ffffff and 1.49 on #f5f5f5 against a 3:1 fill
floor, so it could not legally carry a boundary on a light ground at all.
"""

STATUS_SUCCESS_TEXT: Final[str] = "#ad85a3"
STATUS_WARNING_TEXT: Final[str] = "#bc8752"
"""MIRROR the register's STATUS["success-text"] and ["warning-text"].
TEXT on a dark ground: 4.55 and 4.60 on APP card #2a2a2a.

REGISTERED, not derived. The register's rule -- hold hue and chroma, move
lightness only, take the first step that clears 4.5 on the worst ground -- is
published as PROVENANCE so the choice is auditable. It is not re-run here. A
rule held live becomes an edit anyone can make, and retuning it would silently
change what a warning looks like in five applications.
"""

STATUS_SUCCESS_TEXT_LIGHT: Final[str] = "#825d79"
STATUS_WARNING_TEXT_LIGHT: Final[str] = "#8e5e2b"
"""MIRROR the register's STATUS["*-text-light"]. TEXT on a light ground:
4.52 on #f5f5f5, this application's light dialog background.

RNV-STATUS-LIGHT-FLOOR, CLOSED 2026-09-05 at register rev 31.

These were first walked against #f5f5f5 as "the worst light ground". It was
not the worst: rev 27 had put APP hover-light #eeeeee, GOLD_TEXT_GROUND_FLOOR
#e8e8e8 and pressed-light #e0e0e0 below it, and because the rule takes the
FIRST step that clears, each value stopped at 4.52 with no margin and they
failed one rung down together.

Re-walked against #e8e8e8. THE DECIDING REASON IS NOT THE SIZE OF THE MOVE --
#e0e0e0 was affordable on identical grounds, so cost does not pick between
them. It is that #e8e8e8 is where BRAND_DARK_GOLD_DEEP already stops:

    on #e8e8e8   gold-deep 4.53   these 4.52 / 4.53 / 4.52   pass
    on #e0e0e0   gold-deep 4.21   these 4.20 / 4.20 / 4.20   fail

ONE boundary for every brand text family instead of two. Walking to #e0e0e0
would have covered the pressed plate and left an author having to remember
which family they were in to know where text stops. Below #e8e8e8, no brand
text of any family.

WHY THIS APPLICATION HAS THEM AT ALL. Both palettes previously held the same
#28a745 and #ffc107. As text on #f5f5f5 that is 2.87 and 1.50 -- illegal, and
invisible only because the two keys are unused. Light now carries its own
siblings, so the keys are legal on arrival if they are ever wired up.
"""

APP_BORDER: Final[str] = "#333333"
"""engine/brand.py APP["border"]. grey(3). An edge, so the grid governs it."""

APP_TEXT: Final[str] = "#dddddd"
"""engine/brand.py APP["text"]. grey(13). Primary ink in dark and image mode.

MOVED FROM #e0e0e0 ON 2026-08-28, with the brand rather than after it.
#e0e0e0 was one hex doing two unrelated jobs -- ink in dark mode, and a light
SURFACE in the light palette below. It refused to sit on the grid because the
grid governs inks and half its uses were not ink. Only the ink half moved.
Contrast falls 0.21 to 0.45 and the floor afterwards is 7.17:1 on the pressed
plate #444444, the darkest ground it is ever drawn on.
"""

APP_TEXT_DIM: Final[str] = "#aaaaaa"
"""engine/brand.py APP["text-dim"]. grey(10)."""

APP_PANEL_HOVER: Final[str] = "#3a3a3a"
"""engine/brand.py APP["panel-hover"]. The dark interaction plate.

REGISTERED 2026-08-29 in rnv-brand rev 22, and app-owned here until then. The
register had called the dark ladder "two-thirds specified" because APP_BORDER
#333333 is not #3a3a3a and so looked like a missing rung. It is not a rung at
all: #333333 is grey(3) on the INK grid, which governs inks and EDGES, and a
border is an edge. The ladder was complete when the question was first asked.

    BRAND_BLACK + n * 0x10,  n in -1..+2
    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover

This app holds three of the four; it has no canvas surface.
"""

APP_HOVER_LIGHT: Final[str] = "#eeeeee"
"""engine/brand.py APP["hover-light"]. grey(14). The light interaction plate.

REGISTERED 2026-08-29 as #e8e8e8 and MOVED to #eeeeee on 2026-08-30 in rev 23,
before any app had been wired to it. Nothing here changes value -- the five
entries below already held #eeeeee.

#e8e8e8 is the ground BRAND_DARK_GOLD_DEEP is calibrated against: -14 per
channel is the smallest uniform step that clears it, and -13 gives 4.4675 and
fails. Registering it as the hover would have put every hover in the app on the
one value the gold cannot afford to lose, clearing the 4.5 floor by 0.0334. A
boundary is not a plate. This value is a grid step inside it and reads 4.7875.

#e8e8e8 keeps everything else -- registered, the published gold-as-text
boundary, the binding ground. It is simply not the hover.
"""

# RNV-LIGHT-WIRING (2026-09-06): the constants below name values the
# palettes already carried as literals. Nothing here is a new colour.
# Registered values take the register's key; ramp greys take their byte.

APP_SURFACE_LIGHT_3: Final[str] = "#f5f5f5"
"""engine/brand.py APP["surface-light-3"]. The light window and panel
ground -- what a dialog sits on in light mode.

RNV-LIGHT-WIRING (2026-09-06): this value was written out as a literal
in every palette that used it, so nothing could move it. Registered by
rev 27 as the third rung of the light surface ladder; named here under
the register's key, the way APP_PANEL_HOVER and APP_HOVER_LIGHT are.
Every key that carries it is a surface, so it is not split."""

APP_SURFACE_LIGHT_2: Final[str] = "#fbfbfb"
"""engine/brand.py APP["surface-light-2"]. One rung above the panel ground.

RNV-LIGHT-WIRING (2026-09-06): new to this application. It arrives
because two strays collapse onto it -- #f8f8f8 and #fafafa, which sat
0.60 and 0.20 CIEDE2000 from this rung and on no ladder at all. Same
ruling as #252525 onto the card: a value a fraction of a step from a
registered one is that one, misspelled."""

APP_PRESSED_LIGHT: Final[str] = "#e0e0e0"
"""engine/brand.py APP["pressed-light"]. The light PRESSED plate -- an
interaction state, which is why this name goes only on `pressed_bg`.

RNV-LIGHT-WIRING (2026-09-06): SPLIT, NOT RENAMED. Other keys hold
#e0e0e0 as a static surface (a tab, a scrollbar track) and keep the
ramp-step name GREY_E0 below. Wiring a resting ground to a pressed
state would claim a role for it on the strength of a shared hex --
the same ruling rnv-text-transformer made for GREY_EE / APP_HOVER_LIGHT."""

GREY_E0: Final[str] = "#e0e0e0"
"""grey(14) on the ramp, #e0e0e0. Static surfaces that share a hex with
APP_PRESSED_LIGHT without being a pressed state. See the split note
there. Named by its byte, like every other ramp step."""

GREY_EE: Final[str] = "#eeeeee"
"""grey(14) on the ramp, #eeeeee. Static surfaces that share a hex with
APP_HOVER_LIGHT without being a hover: a list header, a scroll ground.
Same split rnv-text-transformer ruled for its diff headers."""

GREY_DD: Final[str] = "#dddddd"
"""grey(13) on the ramp, #dddddd. Edges and grid lines that share a hex
with APP_TEXT without being text. The register's APP["text"] is ink;
a gridline is not, and moving the ink should not move the grid."""

GREY_66: Final[str] = "#666666"
"""grey(6) on the ramp, #666666. Secondary and muted text on light."""

GREY_88: Final[str] = "#888888"
"""grey(8) on the ramp, #888888. Muted text on dark, a scrollbar handle
hover on light."""

GREY_55: Final[str] = "#555555"
"""grey(5) on the ramp, #555555. Disabled text and a checkbox edge on dark."""

GREY_44: Final[str] = "#444444"
"""grey(4) on the ramp, #444444. The pressed plate and the scrollbar
handle on dark."""

# RNV-LIGHT-WIRING (2026-09-06): moved up from below the
# palettes, unchanged. It now has palette callers, and a
# name defined after its use is a NameError at import.
GREY_CC: Final[str] = "#cccccc"
"""Grey cc. The light edge swatch_edge() reaches for on a dark ground.

RNV-INK-RULE (2026-09-02). It used to be three digits under a role name,
which is why a census that reads six-digit hexes never saw it.
"""


APP_PROVENANCE: Final[dict[str, str]] = {
    "TRUE_BLACK": "register",
    "WHITE": "register",
    "BRAND_BLACK": "register",
    "APP_CARD": "register",
    "APP_BORDER": "register",
    "APP_TEXT": "register",
    "APP_TEXT_DIM": "register",
    "APP_PANEL_HOVER": "register",
    "APP_HOVER_LIGHT": "register",
    "APP_SURFACE_LIGHT_3": "register",
    "APP_SURFACE_LIGHT_2": "register",
    "APP_PRESSED_LIGHT": "register",
    "GREY_E0": "app-ramp",
    "GREY_EE": "app-ramp",
    "GREY_DD": "app-ramp",
    "GREY_66": "app-ramp",
    "GREY_88": "app-ramp",
    "GREY_55": "app-ramp",
    "GREY_44": "app-ramp",
}
"""Declarative, and read by tests/test_app_mirror.py. A classification that
lives only in a test drifts from the thing it classifies."""

# ==================== Dark Theme Colors ====================

# DERIVED. The dark-mode hover gold, published in rnv-brand engine/brand.py.
# Hover moves AWAY from the ground in both modes: lighter on dark, deeper on
# light. Stated as "a lighter tint for hover" it is wrong half the time.
BRAND_GOLD_HOVER: Final[str] = lighten(BRAND_GOLD, 13)   # -> #dfc9a0

DARK_THEME_COLORS: Final[dict[str, str]] = {
    # Base colors
    'window_bg': TRUE_BLACK,
    'panel_bg': BRAND_BLACK,
    'card_bg': APP_CARD,
    'input_bg': BRAND_BLACK,
    'hover_bg': APP_PANEL_HOVER,
    'pressed_bg': APP_BORDER,
    'selected_bg': BRAND_GOLD,
    
    # Text colors
    'text_primary': APP_TEXT,
    'text_secondary': GREY_88,
    'text_muted': GREY_88,
    'text_disabled': GREY_55,
    'accent_hover': BRAND_GOLD_HOVER,
    'text_accent': BRAND_GOLD,
    'text_on_accent': TRUE_BLACK,
    
    # Border colors
    'border_default': APP_BORDER,
    'border_focus': BRAND_GOLD,
    'border_hover': GREY_44,
    'border_accent': BRAND_GOLD,
    'input_border': APP_BORDER,
    
    # Button colors (dialog buttons - gold accent system)
    'dialog_btn_bg': APP_CARD,
    'dialog_btn_hover_bg': APP_PANEL_HOVER,
    'dialog_btn_pressed_bg': BRAND_GOLD,
    'dialog_btn_text': APP_TEXT,
    'dialog_btn_hover_text': BRAND_GOLD,
    'dialog_btn_pressed_text': TRUE_BLACK,
    'dialog_btn_border': APP_BORDER,
    'dialog_btn_hover_border': BRAND_GOLD,

    # Main window buttons - color inverse system (no brand gold)
    # Dark: rest=#1a1a1a bg / hover=#333333 bg / pressed=#444444 bg
    'main_btn_bg': BRAND_BLACK,
    'main_btn_text': APP_TEXT,
    'main_btn_border': APP_BORDER,
    'main_btn_hover_bg': APP_BORDER,
    'main_btn_hover_text': APP_TEXT,
    'main_btn_pressed_bg': GREY_44,
    'main_btn_pressed_text': TRUE_BLACK,

    # Accent button (gold border)
    'dialog_btn_accent_bg': APP_CARD,
    'dialog_btn_accent_text': BRAND_GOLD,
    'dialog_btn_accent_border': BRAND_GOLD,
    'dialog_btn_accent_hover_bg': APP_BORDER,
    'dialog_btn_accent_pressed_bg': BRAND_GOLD,
    'dialog_btn_accent_pressed_text': TRUE_BLACK,
    
    # Platform button
    # RNV-COLLAPSE-252525 (2026-09-02): was #252525, a value a third of
    # the way from panel to card and on neither ladder nor grid. Ruled
    # onto the card rung. Image mode inherits this through the splat.
    'platform_btn_bg': APP_CARD,
    'platform_btn_hover_bg': APP_BORDER,
    
    # Clear/subtle button
    'clear_btn_bg': APP_CARD,
    
    # Checkbox
    'checkbox_bg': APP_CARD,
    'checkbox_border': GREY_55,
    'checkbox_checked_bg': BRAND_GOLD,
    'checkbox_checked_border': BRAND_GOLD,
    'checkbox_hover_border': BRAND_GOLD,
    
    # Tab widget
    'tab_bg': APP_CARD,
    'tab_selected_bg': APP_BORDER,
    'tab_hover_bg': APP_BORDER,
    'tab_border': APP_BORDER,
    'tab_indicator': BRAND_GOLD,
    
    # Scrollbar
    'scrollbar_bg': APP_CARD,   # was #252525, see platform_btn_bg
    'scrollbar_handle': GREY_44,
    'scrollbar_handle_hover': BRAND_GOLD,
    'scrollbar_border': APP_BORDER,
    
    # List/Table
    'list_bg': BRAND_BLACK,
    'list_alt_bg': APP_CARD,   # was #252525, see platform_btn_bg
    'list_selected_bg': BRAND_GOLD,
    'list_hover_bg': APP_PANEL_HOVER,
    'list_header_bg': APP_CARD,
    'list_grid': APP_BORDER,
    
    # Dialog
    'dialog_bg': BRAND_BLACK,
    'dialog_border': APP_BORDER,
    
    # Status bar
    'statusbar_bg': BRAND_BLACK,
    'statusbar_border': APP_BORDER,
    
    # Drop zone
    'dropzone_bg': BRAND_BLACK,
    'dropzone_border': APP_BORDER,
    'dropzone_active_bg': 'rgba(210, 188, 147, 0.2)',
    
    # Tooltip
    'tooltip_bg': APP_CARD,
    'tooltip_border': BRAND_GOLD,
    'tooltip_text': APP_TEXT,
    
    # Success/Warning/Error
    # RNV-STATUS-FAMILY: the fills, unwired. Both keys are looked
    # up nowhere in this application and are on the dead-key list;
    # whether they should exist is a separate question. If either
    # is ever painted as TEXT it must take the _TEXT variant
    # instead -- a fill sits at L* 48-59 and cannot reach 4.5:1.
    'success': STATUS_SUCCESS,
    'warning': STATUS_WARNING,
    # RNV-STATUS-FAMILY: the watcher's label is TEXT, and a module
    # constant cannot know which mode it is being painted in.
    'status_active': STATUS_SUCCESS_TEXT,
}


# ==================== Light Theme Colors ====================
LIGHT_THEME_COLORS: Final[dict[str, str]] = {
    # Base colors
    'window_bg': APP_SURFACE_LIGHT_3,
    'panel_bg': APP_SURFACE_LIGHT_3,
    'card_bg': WHITE,
    'input_bg': WHITE,
    'hover_bg': APP_HOVER_LIGHT,
    'pressed_bg': APP_PRESSED_LIGHT,
    'selected_bg': BRAND_DARK_GOLD,
    
    # Text colors
    'text_primary': TRUE_BLACK,
    'text_secondary': GREY_66,
    'text_muted': GREY_66,
    'text_disabled': APP_TEXT_DIM,
    'accent_hover': BRAND_DARK_GOLD_DEEP,
    'text_accent': BRAND_DARK_GOLD_DEEP,
    'text_on_accent': WHITE,
    
    # Border colors
    'border_default': GREY_CC,
    'border_focus': BRAND_DARK_GOLD,
    'border_hover': APP_TEXT_DIM,
    'border_accent': BRAND_DARK_GOLD,
    'input_border': GREY_CC,
    
    # Button colors (dialog buttons - gold accent system)
    'dialog_btn_bg': WHITE,
    'dialog_btn_hover_bg': APP_HOVER_LIGHT,
    'dialog_btn_pressed_bg': BRAND_DARK_GOLD,
    'dialog_btn_text': TRUE_BLACK,
    'dialog_btn_hover_text': BRAND_DARK_GOLD_DEEP,
    'dialog_btn_pressed_text': WHITE,
    'dialog_btn_border': GREY_CC,
    'dialog_btn_hover_border': BRAND_DARK_GOLD,

    # Main window buttons - color inverse system (no brand gold)
    # Light: rest=#ffffff bg / hover=#333333 bg / pressed=#444444 bg
    'main_btn_bg': WHITE,
    'main_btn_text': TRUE_BLACK,
    'main_btn_border': GREY_CC,
    'main_btn_hover_bg': APP_BORDER,
    'main_btn_hover_text': TRUE_BLACK,
    'main_btn_pressed_bg': GREY_44,
    'main_btn_pressed_text': WHITE,

    # Accent button (gold border)
    'dialog_btn_accent_bg': WHITE,
    'dialog_btn_accent_text': BRAND_DARK_GOLD_DEEP,
    'dialog_btn_accent_border': BRAND_DARK_GOLD,
    'dialog_btn_accent_hover_bg': APP_HOVER_LIGHT,
    'dialog_btn_accent_pressed_bg': BRAND_DARK_GOLD,
    'dialog_btn_accent_pressed_text': WHITE,
    
    # Platform button
    'platform_btn_bg': APP_SURFACE_LIGHT_2,   # was #fafafa, collapsed onto #fbfbfb
    'platform_btn_hover_bg': APP_HOVER_LIGHT,   # was #f0f0f0, collapsed onto #eeeeee
    
    # Clear/subtle button
    'clear_btn_bg': APP_SURFACE_LIGHT_3,
    
    # Checkbox
    'checkbox_bg': WHITE,
    'checkbox_border': APP_TEXT_DIM,
    'checkbox_checked_bg': BRAND_DARK_GOLD,
    'checkbox_checked_border': BRAND_DARK_GOLD,
    'checkbox_hover_border': BRAND_DARK_GOLD,
    
    # Tab widget
    'tab_bg': GREY_E0,
    'tab_selected_bg': WHITE,
    'tab_hover_bg': APP_HOVER_LIGHT,
    'tab_border': GREY_CC,
    'tab_indicator': BRAND_DARK_GOLD,
    
    # Scrollbar
    'scrollbar_bg': GREY_E0,
    'scrollbar_handle': APP_TEXT_DIM,
    'scrollbar_handle_hover': BRAND_DARK_GOLD,
    'scrollbar_border': GREY_CC,
    
    # List/Table
    'list_bg': WHITE,
    'list_alt_bg': APP_SURFACE_LIGHT_2,   # was #f8f8f8, collapsed onto #fbfbfb
    'list_selected_bg': BRAND_DARK_GOLD,
    'list_hover_bg': APP_HOVER_LIGHT,
    'list_header_bg': GREY_EE,   # was #f0f0f0, collapsed onto #eeeeee
    'list_grid': GREY_DD,
    
    # Dialog
    'dialog_bg': APP_SURFACE_LIGHT_3,
    'dialog_border': GREY_CC,
    
    # Status bar
    'statusbar_bg': APP_SURFACE_LIGHT_3,
    'statusbar_border': GREY_CC,
    
    # Drop zone
    'dropzone_bg': WHITE,
    'dropzone_border': GREY_CC,
    'dropzone_active_bg': 'rgba(210, 188, 147, 0.3)',
    
    # Tooltip
    'tooltip_bg': WHITE,
    'tooltip_border': BRAND_DARK_GOLD,
    'tooltip_text': TRUE_BLACK,
    
    # Success/Warning/Error
    # RNV-STATUS-FAMILY: light's own siblings. This palette held
    # the dark values, which as text on #f5f5f5 read 2.87 and 1.50.
    'success': STATUS_SUCCESS,
    'warning': STATUS_WARNING,
    'status_active': STATUS_SUCCESS_TEXT_LIGHT,
}


# ==================== Image Mode Colors (Dark with transparency) ====================
IMAGE_MODE_COLORS: Final[dict[str, str]] = {
    **DARK_THEME_COLORS,
    # Override with transparent backgrounds
    'window_bg': 'rgba(26, 26, 26, 0.93)',
    'panel_bg': 'rgba(26, 26, 26, 0.93)',
    'card_bg': 'rgba(42, 42, 42, 0.93)',
    'input_bg': 'rgba(42, 42, 42, 0.93)',
    'dropzone_bg': 'rgba(26, 26, 26, 0.93)',
    'scrollbar_bg': 'transparent',
    'scrollbar_handle': 'rgba(80, 80, 80, 150)',
    'scrollbar_handle_hover': BRAND_GOLD,
    'scrollbar_border': 'rgba(51, 51, 51, 100)',
}


def get_theme_colors(is_dark: bool = True, is_image_mode: bool = False) -> dict[str, str]:
    """
    Get the color palette for the specified theme.
    
    Args:
        is_dark: True for dark theme, False for light theme
        is_image_mode: True for image mode (transparent overlays)
        
    Returns:
        Dictionary of color definitions
    """
    if is_image_mode:
        return IMAGE_MODE_COLORS.copy()
    elif is_dark:
        return DARK_THEME_COLORS.copy()
    else:
        return LIGHT_THEME_COLORS.copy()


# ==================== OS Simulation Colors ====================
# Used exclusively by context_preview.py to simulate real OS chrome.
# These are fixed platform UI values — they must NOT follow the app theme.
OS_SIM_COLORS: Final[dict[str, str]] = {
    # Windows Taskbar
    'taskbar_dark_bg':           '#202020',
    'taskbar_light_bg':          '#f0f0f0',
    'taskbar_border':            APP_BORDER,
    'taskbar_text_dark':         '#ffffff',
    'taskbar_text_light':        TRUE_BLACK,
    'taskbar_text_muted_dark':   '#aaaaaa',
    'taskbar_text_muted_light':  '#666666',

    # Windows Explorer
    'explorer_bg':               '#ffffff',
    'explorer_border':           '#dddddd',
    'explorer_text':             TRUE_BLACK,

    # macOS Dock
    'dock_gradient_start':       'rgba(255,255,255,0.3)',
    'dock_gradient_end':         'rgba(255,255,255,0.1)',
    'dock_border':               'rgba(255,255,255,0.2)',

    # macOS Finder
    'finder_bg':                 '#f5f5f5',
    'finder_border':             '#dddddd',
    'finder_text':               APP_BORDER,

    # Chrome Browser Tab Bar
    'chrome_tabbar_bg':          '#dee1e6',
    'chrome_active_tab_bg':      '#ffffff',
    'chrome_inactive_tab_bg':    '#cccfd4',
    'chrome_tab_title':          APP_BORDER,
    'chrome_tab_close':          '#666666',
    'chrome_inactive_tab_text':  '#555555',

    # Browser Bookmarks Bar
    'bookmarks_bg':              '#f8f9fa',
    'bookmarks_border':          '#dddddd',
    'bookmarks_text':            APP_BORDER,

    # Windows Desktop
    'desktop_gradient_start':    '#1e90ff',
    'desktop_gradient_end':      '#104e8b',
    'desktop_icon_text':         '#ffffff',
    'desktop_icon_label_bg':     'rgba(0,0,0,0.3)',
}


# ==================== Standalone Color Constants ====================

DEFAULT_CUSTOM_BG_COLOR: Final[str] = "#808080"
"""Default custom preview background color (neutral gray starting value)"""

# ── Which ink goes on this ground ──
#
# RNV-INK-RULE (2026-09-02, ruled by Chris). This application asked the
# question in two places and answered it two different ways:
#
#     ui/settings_dialog.py     (r + g + b) / 3 > 128
#     ui/preview_utils.py       ITU-R 601 luma > 128
#
# Neither is a contrast measurement, and they part company on saturated
# colour, because 601 weights green 587/1000 where the mean weights it 333.
# On pure green the mean calls it dark and puts WHITE on it at 1.37:1, where
# the right answer is black at 15.30:1.
#
# One rule now, stated as a real comparison rather than a threshold --
# whichever candidate has the higher contrast ratio against the ground wins.
# A threshold would have to be re-derived for every pair of candidates; a
# ratio does not, which is what lets swatch_edge() share the rule with
# contrast_ink().
#
# The same maths as the surface ladder and the 4.5 floor. rnv-color-picker
# carries the identical block.


def _channel(value: float) -> float:
    """One sRGB channel, 0-255, linearised."""
    c = value / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _rgb(color: "str | tuple[int, int, int]") -> tuple[int, int, int]:
    """Accept either shape. Callers hold hex strings and RGB triples both."""
    if isinstance(color, str):
        h = color.lstrip("#")
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return (int(color[0]), int(color[1]), int(color[2]))


def relative_luminance(color: "str | tuple[int, int, int]") -> float:
    """WCAG 2.x relative luminance, 0.0 (black) to 1.0 (white)."""
    r, g, b = _rgb(color)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(a: "str | tuple[int, int, int]",
                   b: "str | tuple[int, int, int]") -> float:
    """WCAG contrast ratio between two colours, 1.0 to 21.0."""
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = (la, lb) if la >= lb else (lb, la)
    return (hi + 0.05) / (lo + 0.05)


def better_on(background: "str | tuple[int, int, int]", *candidates: str) -> str:
    """Whichever candidate reads best on this ground. Ties go to the first."""
    return max(candidates, key=lambda c: contrast_ratio(background, c))


def contrast_ink(background: "str | tuple[int, int, int]") -> str:
    """Text colour for an arbitrary ground: WHITE or TRUE_BLACK.

    For a colour the USER chose -- a swatch, a preview background. Not for
    brand surfaces: what sits on a brand gold is a ruling, not a measurement,
    and the two are only 0.08 apart on BRAND_DARK_GOLD.
    """
    return better_on(background, TRUE_BLACK, WHITE)


def prefers_dark_ink(background: "str | tuple[int, int, int]") -> bool:
    """True when TRUE_BLACK reads better on this ground than WHITE does."""
    return contrast_ink(background) == TRUE_BLACK


def swatch_edge(background: "str | tuple[int, int, int]") -> str:
    """Outline for a swatch of an arbitrary colour: GREY_CC or APP_BORDER."""
    return better_on(background, APP_BORDER, GREY_CC)

STATUS_ACTIVE_COLOR: Final[str] = STATUS_SUCCESS_TEXT
"""The folder watcher, running. RNV-STATUS-REGISTER (2026-09-02): was
#4caf50, Material's green, where the register publishes #28a745 and where
rnv-color-picker's identically-named constant already used the register's.
Two applications, one role, two greens; ruled onto one.

RNV-STATUS-FAMILY (2026-09-03): this constant is no longer what
gets painted. ui/settings_dialog.py wrote `color: {STATUS_ACTIVE_COLOR}`
on the watch label -- TEXT, in a dialog that runs in three modes --
and a module-level constant does not know which mode it is in. One
value cannot be legal on all three grounds: the dark text variant
reads 5.52 on #1a1a1a and 3.15 on #ffffff. The palettes now carry a
`status_active` key resolved per mode, and the call site reads the
theme it was already holding. This constant remains as the
REGISTER-FACING alias below, which is what it was always for.

AND IT NOW ALIASES success-text RATHER THAN success, ruled by the
register 2026-09-04. It pointed at the FILL, which was safe only by
accident: Bootstrap's green read 5.55 on BRAND_BLACK and doubled as
text. The RNV fills are mid-tones by design and #926c89 reads 3.91
there, so the alias would have failed the 4.5 text floor on the day
the family landed. An alias onto a fill is a fill used as text.

It is an ALIAS rather than a copy because "running" is not "succeeded" and
the register has no name for the first. If status-active is ever
registered, this line is the only one that moves.
"""


__all__: list[str] = [
    'BRAND_GOLD',
    'BRAND_DARK_GOLD',
    'BRAND_DARK_GOLD_DEEP',
    'BRAND_GOLD_RGB',
    'BRAND_DARK_GOLD_RGB',
    'lighten',
    'DARK_THEME_COLORS',
    'LIGHT_THEME_COLORS',
    'IMAGE_MODE_COLORS',
    'OS_SIM_COLORS',
    'get_theme_colors',
    'DEFAULT_CUSTOM_BG_COLOR',
    'TRUE_BLACK',
    'WHITE',
    'APP_BORDER',
    'GREY_CC',
    'relative_luminance',
    'contrast_ratio',
    'better_on',
    'contrast_ink',
    'prefers_dark_ink',
    'swatch_edge',
    'STATUS_SUCCESS',
    'STATUS_WARNING',
    'STATUS_SUCCESS_TEXT',
    'STATUS_WARNING_TEXT',
    'STATUS_SUCCESS_TEXT_LIGHT',
    'STATUS_WARNING_TEXT_LIGHT',
    'STATUS_ACTIVE_COLOR',
]