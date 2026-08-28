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


# ==================== Dark Theme Colors ====================

# DERIVED. The dark-mode hover gold, published in rnv-brand engine/brand.py.
# Hover moves AWAY from the ground in both modes: lighter on dark, deeper on
# light. Stated as "a lighter tint for hover" it is wrong half the time.
BRAND_GOLD_HOVER: Final[str] = lighten(BRAND_GOLD, 13)   # -> #dfc9a0

DARK_THEME_COLORS: Final[dict[str, str]] = {
    # Base colors
    'window_bg': '#000000',
    'panel_bg': '#1a1a1a',
    'card_bg': '#2a2a2a',
    'input_bg': '#1a1a1a',
    'hover_bg': '#3a3a3a',
    'pressed_bg': '#333333',
    'selected_bg': BRAND_GOLD,
    
    # Text colors
    'text_primary': '#e0e0e0',
    'text_secondary': '#888888',
    'text_muted': '#888888',
    'text_disabled': '#555555',
    'accent_hover': BRAND_GOLD_HOVER,
    'text_accent': BRAND_GOLD,
    'text_on_accent': '#000000',
    
    # Border colors
    'border_default': '#333333',
    'border_focus': BRAND_GOLD,
    'border_hover': '#444444',
    'border_accent': BRAND_GOLD,
    'input_border': '#333333',
    
    # Button colors (dialog buttons - gold accent system)
    'button_bg': '#2a2a2a',
    'button_hover_bg': '#3a3a3a',
    'button_pressed_bg': BRAND_GOLD,
    'button_text': '#e0e0e0',
    'button_hover_text': BRAND_GOLD,
    'button_pressed_text': '#000000',
    'button_border': '#333333',
    'button_hover_border': BRAND_GOLD,

    # Main window buttons - color inverse system (no brand gold)
    # Dark: rest=#1a1a1a bg / hover=#333333 bg / pressed=#444444 bg
    'main_btn_bg': '#1a1a1a',
    'main_btn_text': '#e0e0e0',
    'main_btn_border': '#333333',
    'main_btn_hover_bg': '#333333',
    'main_btn_hover_text': '#e0e0e0',
    'main_btn_pressed_bg': '#444444',
    'main_btn_pressed_text': '#000000',

    # Accent button (gold border)
    'accent_button_bg': '#2a2a2a',
    'accent_button_text': BRAND_GOLD,
    'accent_button_border': BRAND_GOLD,
    'accent_button_hover_bg': '#333333',
    'accent_button_pressed_bg': BRAND_GOLD,
    'accent_button_pressed_text': '#000000',
    
    # Platform button
    'platform_btn_bg': '#252525',
    'platform_btn_hover_bg': '#333333',
    
    # Clear/subtle button
    'clear_btn_bg': '#2a2a2a',
    
    # Checkbox
    'checkbox_bg': '#2a2a2a',
    'checkbox_border': '#555555',
    'checkbox_checked_bg': BRAND_GOLD,
    'checkbox_checked_border': BRAND_GOLD,
    'checkbox_hover_border': BRAND_GOLD,
    
    # Tab widget
    'tab_bg': '#2a2a2a',
    'tab_selected_bg': '#333333',
    'tab_hover_bg': '#333333',
    'tab_border': '#333333',
    'tab_indicator': BRAND_GOLD,
    
    # Scrollbar
    'scrollbar_bg': '#252525',
    'scrollbar_handle': '#444444',
    'scrollbar_handle_hover': BRAND_GOLD,
    'scrollbar_border': '#333333',
    
    # List/Table
    'list_bg': '#1a1a1a',
    'list_alt_bg': '#252525',
    'list_selected_bg': BRAND_GOLD,
    'list_hover_bg': '#3a3a3a',
    'list_header_bg': '#2a2a2a',
    'list_grid': '#333333',
    
    # Dialog
    'dialog_bg': '#1a1a1a',
    'dialog_border': '#333333',
    
    # Status bar
    'statusbar_bg': '#1a1a1a',
    'statusbar_border': '#333333',
    
    # Drop zone
    'dropzone_bg': '#1a1a1a',
    'dropzone_border': '#333333',
    'dropzone_active_bg': 'rgba(210, 188, 147, 0.2)',
    
    # Tooltip
    'tooltip_bg': '#2a2a2a',
    'tooltip_border': BRAND_GOLD,
    'tooltip_text': '#e0e0e0',
    
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
    'hover_bg': '#eeeeee',
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
    'button_bg': '#ffffff',
    'button_hover_bg': '#eeeeee',
    'button_pressed_bg': BRAND_DARK_GOLD,
    'button_text': '#000000',
    'button_hover_text': BRAND_DARK_GOLD_DEEP,
    'button_pressed_text': '#ffffff',
    'button_border': '#cccccc',
    'button_hover_border': BRAND_DARK_GOLD,

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
    'accent_button_bg': '#ffffff',
    'accent_button_text': BRAND_DARK_GOLD_DEEP,
    'accent_button_border': BRAND_DARK_GOLD,
    'accent_button_hover_bg': '#eeeeee',
    'accent_button_pressed_bg': BRAND_DARK_GOLD,
    'accent_button_pressed_text': '#ffffff',
    
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
    'tab_hover_bg': '#eeeeee',
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
    'list_hover_bg': '#eeeeee',
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
    'taskbar_border':            '#333333',
    'taskbar_text_dark':         '#ffffff',
    'taskbar_text_light':        '#000000',
    'taskbar_text_muted_dark':   '#aaaaaa',
    'taskbar_text_muted_light':  '#666666',

    # Windows Explorer
    'explorer_bg':               '#ffffff',
    'explorer_border':           '#dddddd',
    'explorer_text':             '#000000',

    # macOS Dock
    'dock_gradient_start':       'rgba(255,255,255,0.3)',
    'dock_gradient_end':         'rgba(255,255,255,0.1)',
    'dock_border':               'rgba(255,255,255,0.2)',

    # macOS Finder
    'finder_bg':                 '#f5f5f5',
    'finder_border':             '#dddddd',
    'finder_text':               '#333333',

    # Chrome Browser Tab Bar
    'chrome_tabbar_bg':          '#dee1e6',
    'chrome_active_tab_bg':      '#ffffff',
    'chrome_inactive_tab_bg':    '#cccfd4',
    'chrome_tab_title':          '#333333',
    'chrome_tab_close':          '#666666',
    'chrome_inactive_tab_text':  '#555555',

    # Browser Bookmarks Bar
    'bookmarks_bg':              '#f8f9fa',
    'bookmarks_border':          '#dddddd',
    'bookmarks_text':            '#333333',

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