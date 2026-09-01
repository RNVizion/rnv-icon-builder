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
    'text_secondary': '#888888',
    'text_muted': '#888888',
    'text_disabled': '#555555',
    'accent_hover': BRAND_GOLD_HOVER,
    'text_accent': BRAND_GOLD,
    'text_on_accent': TRUE_BLACK,
    
    # Border colors
    'border_default': APP_BORDER,
    'border_focus': BRAND_GOLD,
    'border_hover': '#444444',
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
    'main_btn_pressed_bg': '#444444',
    'main_btn_pressed_text': TRUE_BLACK,

    # Accent button (gold border)
    'dialog_btn_accent_bg': APP_CARD,
    'dialog_btn_accent_text': BRAND_GOLD,
    'dialog_btn_accent_border': BRAND_GOLD,
    'dialog_btn_accent_hover_bg': APP_BORDER,
    'dialog_btn_accent_pressed_bg': BRAND_GOLD,
    'dialog_btn_accent_pressed_text': TRUE_BLACK,
    
    # Platform button
    'platform_btn_bg': '#252525',
    'platform_btn_hover_bg': APP_BORDER,
    
    # Clear/subtle button
    'clear_btn_bg': APP_CARD,
    
    # Checkbox
    'checkbox_bg': APP_CARD,
    'checkbox_border': '#555555',
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
    'scrollbar_bg': '#252525',
    'scrollbar_handle': '#444444',
    'scrollbar_handle_hover': BRAND_GOLD,
    'scrollbar_border': APP_BORDER,
    
    # List/Table
    'list_bg': BRAND_BLACK,
    'list_alt_bg': '#252525',
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
    'success': '#28a745',
    'warning': '#ffc107',
}


# ==================== Light Theme Colors ====================
LIGHT_THEME_COLORS: Final[dict[str, str]] = {
    # Base colors
    'window_bg': '#f5f5f5',
    'panel_bg': '#f5f5f5',
    'card_bg': '#ffffff',
    'input_bg': '#ffffff',
    'hover_bg': APP_HOVER_LIGHT,
    'pressed_bg': '#e0e0e0',
    'selected_bg': BRAND_DARK_GOLD,
    
    # Text colors
    'text_primary': '#000000',
    'text_secondary': '#666666',
    'text_muted': '#666666',
    'text_disabled': '#aaaaaa',
    'accent_hover': BRAND_DARK_GOLD_DEEP,
    'text_accent': BRAND_DARK_GOLD_DEEP,
    'text_on_accent': '#ffffff',
    
    # Border colors
    'border_default': '#cccccc',
    'border_focus': BRAND_DARK_GOLD,
    'border_hover': '#aaaaaa',
    'border_accent': BRAND_DARK_GOLD,
    'input_border': '#cccccc',
    
    # Button colors (dialog buttons - gold accent system)
    'dialog_btn_bg': '#ffffff',
    'dialog_btn_hover_bg': APP_HOVER_LIGHT,
    'dialog_btn_pressed_bg': BRAND_DARK_GOLD,
    'dialog_btn_text': '#000000',
    'dialog_btn_hover_text': BRAND_DARK_GOLD_DEEP,
    'dialog_btn_pressed_text': '#ffffff',
    'dialog_btn_border': '#cccccc',
    'dialog_btn_hover_border': BRAND_DARK_GOLD,

    # Main window buttons - color inverse system (no brand gold)
    # Light: rest=#ffffff bg / hover=#333333 bg / pressed=#444444 bg
    'main_btn_bg': '#ffffff',
    'main_btn_text': '#000000',
    'main_btn_border': '#cccccc',
    'main_btn_hover_bg': '#333333',
    'main_btn_hover_text': '#000000',
    'main_btn_pressed_bg': '#444444',
    'main_btn_pressed_text': '#ffffff',

    # Accent button (gold border)
    'dialog_btn_accent_bg': '#ffffff',
    'dialog_btn_accent_text': BRAND_DARK_GOLD_DEEP,
    'dialog_btn_accent_border': BRAND_DARK_GOLD,
    'dialog_btn_accent_hover_bg': APP_HOVER_LIGHT,
    'dialog_btn_accent_pressed_bg': BRAND_DARK_GOLD,
    'dialog_btn_accent_pressed_text': '#ffffff',
    
    # Platform button
    'platform_btn_bg': '#fafafa',
    'platform_btn_hover_bg': '#f0f0f0',
    
    # Clear/subtle button
    'clear_btn_bg': '#f5f5f5',
    
    # Checkbox
    'checkbox_bg': '#ffffff',
    'checkbox_border': '#aaaaaa',
    'checkbox_checked_bg': BRAND_DARK_GOLD,
    'checkbox_checked_border': BRAND_DARK_GOLD,
    'checkbox_hover_border': BRAND_DARK_GOLD,
    
    # Tab widget
    'tab_bg': '#e0e0e0',
    'tab_selected_bg': '#ffffff',
    'tab_hover_bg': APP_HOVER_LIGHT,
    'tab_border': '#cccccc',
    'tab_indicator': BRAND_DARK_GOLD,
    
    # Scrollbar
    'scrollbar_bg': '#e0e0e0',
    'scrollbar_handle': '#aaaaaa',
    'scrollbar_handle_hover': BRAND_DARK_GOLD,
    'scrollbar_border': '#cccccc',
    
    # List/Table
    'list_bg': '#ffffff',
    'list_alt_bg': '#f8f8f8',
    'list_selected_bg': BRAND_DARK_GOLD,
    'list_hover_bg': APP_HOVER_LIGHT,
    'list_header_bg': '#f0f0f0',
    'list_grid': '#dddddd',
    
    # Dialog
    'dialog_bg': '#f5f5f5',
    'dialog_border': '#cccccc',
    
    # Status bar
    'statusbar_bg': '#f5f5f5',
    'statusbar_border': '#cccccc',
    
    # Drop zone
    'dropzone_bg': '#ffffff',
    'dropzone_border': '#cccccc',
    'dropzone_active_bg': 'rgba(210, 188, 147, 0.3)',
    
    # Tooltip
    'tooltip_bg': '#ffffff',
    'tooltip_border': BRAND_DARK_GOLD,
    'tooltip_text': '#000000',
    
    # Success/Warning/Error
    'success': '#28a745',
    'warning': '#ffc107',
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

CONTRAST_ON_LIGHT: Final[str] = "#000000"
"""Black — used as contrast text on light/bright backgrounds (e.g. color swatches)"""

CONTRAST_ON_DARK: Final[str] = "#ffffff"
"""White — used as contrast text on dark/dim backgrounds (e.g. color swatches)"""

SWATCH_BORDER_ON_LIGHT: Final[str] = "#333"
"""Dark border for color swatch buttons on light-colored swatches"""

SWATCH_BORDER_ON_DARK: Final[str] = "#ccc"
"""Light border for color swatch buttons on dark-colored swatches"""

STATUS_ACTIVE_COLOR: Final[str] = "#4caf50"
"""Green — used for active/running status indicators (e.g. folder watcher)"""


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
    'CONTRAST_ON_LIGHT',
    'CONTRAST_ON_DARK',
    'SWATCH_BORDER_ON_LIGHT',
    'SWATCH_BORDER_ON_DARK',
    'STATUS_ACTIVE_COLOR',
]