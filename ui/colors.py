"""
RNV Icon Builder - Color Definitions
Centralized color palette for consistent branding.
"""

from __future__ import annotations
from typing import Final

# ==================== Brand Colors ====================
BRAND_GOLD: Final[str] = "#d2bc93"
"""Primary brand gold - use for hover states, highlights, tooltips, accents"""

BRAND_GOLD_DARK: Final[str] = "#b19145"
"""Darker gold - use for borders, pressed states, and contrast"""

BRAND_GOLD_RGB: Final[tuple[int, int, int]] = (210, 188, 147)
"""Brand gold as RGB tuple (d2=210, bc=188, 93=147)"""

BRAND_GOLD_DARK_RGB: Final[tuple[int, int, int]] = (177, 145, 69)
"""Dark brand gold as RGB tuple"""


# ==================== Dark Theme Colors ====================
DARK_THEME_COLORS: Final[dict[str, str]] = {
    # Base colors
    'window_bg': '#000000',
    'panel_bg': '#1A1A1A',
    'card_bg': '#2A2A2A',
    'input_bg': '#2A2A2A',
    'hover_bg': '#3A3A3A',
    'pressed_bg': '#333333',
    'selected_bg': BRAND_GOLD,
    
    # Text colors
    'text_primary': '#E0E0E0',
    'text_secondary': '#888888',
    'text_muted': '#888888',
    'text_disabled': '#555555',
    'text_accent': BRAND_GOLD,
    'text_on_accent': '#000000',
    
    # Border colors
    'border_default': '#333333',
    'border_focus': BRAND_GOLD,
    'border_hover': '#444444',
    'border_accent': BRAND_GOLD,
    'input_border': '#333333',
    
    # Button colors (dialog buttons - gold accent system)
    'button_bg': '#2A2A2A',
    'button_hover_bg': '#3A3A3A',
    'button_pressed_bg': BRAND_GOLD,
    'button_text': '#E0E0E0',
    'button_hover_text': BRAND_GOLD,
    'button_pressed_text': '#000000',
    'button_border': '#333333',
    'button_hover_border': BRAND_GOLD,

    # Main window buttons - color inverse system (no brand gold)
    # Dark: rest=#1A1A1A bg / hover=#333333 bg / pressed=#444444 bg
    'main_btn_bg': '#1A1A1A',
    'main_btn_text': '#E0E0E0',
    'main_btn_border': '#333333',
    'main_btn_hover_bg': '#333333',
    'main_btn_hover_text': '#E0E0E0',
    'main_btn_pressed_bg': '#444444',
    'main_btn_pressed_text': '#000000',

    # Accent button (gold border)
    'accent_button_bg': '#2A2A2A',
    'accent_button_text': BRAND_GOLD,
    'accent_button_border': BRAND_GOLD,
    'accent_button_hover_bg': '#333333',
    'accent_button_pressed_bg': BRAND_GOLD,
    'accent_button_pressed_text': '#000000',
    
    # Platform button
    'platform_btn_bg': '#252525',
    'platform_btn_hover_bg': '#333333',
    
    # Clear/subtle button
    'clear_btn_bg': '#2A2A2A',
    
    # Checkbox
    'checkbox_bg': '#2A2A2A',
    'checkbox_border': '#555555',
    'checkbox_checked_bg': BRAND_GOLD,
    'checkbox_checked_border': BRAND_GOLD,
    'checkbox_hover_border': BRAND_GOLD,
    
    # Tab widget
    'tab_bg': '#2A2A2A',
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
    'list_bg': '#1A1A1A',
    'list_alt_bg': '#252525',
    'list_selected_bg': BRAND_GOLD,
    'list_hover_bg': '#3A3A3A',
    'list_header_bg': '#2A2A2A',
    'list_grid': '#333333',
    
    # Dialog
    'dialog_bg': '#1A1A1A',
    'dialog_border': '#333333',
    
    # Status bar
    'statusbar_bg': '#1A1A1A',
    'statusbar_border': '#333333',
    
    # Drop zone
    'dropzone_bg': '#1A1A1A',
    'dropzone_border': '#333333',
    'dropzone_active_border': BRAND_GOLD_DARK,
    'dropzone_active_bg': 'rgba(210, 188, 147, 0.2)',
    
    # Tooltip
    'tooltip_bg': '#2A2A2A',
    'tooltip_border': BRAND_GOLD,
    'tooltip_text': '#E0E0E0',
    
    # Success/Warning/Error
    'success': '#28a745',
    'warning': '#FFC107',
    'error': '#dc3545',
}


# ==================== Light Theme Colors ====================
LIGHT_THEME_COLORS: Final[dict[str, str]] = {
    # Base colors
    'window_bg': '#F5F5F5',
    'panel_bg': '#FFFFFF',
    'card_bg': '#FFFFFF',
    'input_bg': '#FFFFFF',
    'hover_bg': '#EEEEEE',
    'pressed_bg': '#E0E0E0',
    'selected_bg': BRAND_GOLD_DARK,
    
    # Text colors
    'text_primary': '#000000',
    'text_secondary': '#666666',
    'text_muted': '#666666',
    'text_disabled': '#AAAAAA',
    'text_accent': BRAND_GOLD_DARK,
    'text_on_accent': '#FFFFFF',
    
    # Border colors
    'border_default': '#CCCCCC',
    'border_focus': BRAND_GOLD_DARK,
    'border_hover': '#AAAAAA',
    'border_accent': BRAND_GOLD_DARK,
    'input_border': '#CCCCCC',
    
    # Button colors (dialog buttons - gold accent system)
    'button_bg': '#FFFFFF',
    'button_hover_bg': '#EEEEEE',
    'button_pressed_bg': BRAND_GOLD_DARK,
    'button_text': '#000000',
    'button_hover_text': BRAND_GOLD_DARK,
    'button_pressed_text': '#FFFFFF',
    'button_border': '#CCCCCC',
    'button_hover_border': BRAND_GOLD_DARK,

    # Main window buttons - color inverse system (no brand gold)
    # Light: rest=#FFFFFF bg / hover=#333333 bg / pressed=#444444 bg
    'main_btn_bg': '#FFFFFF',
    'main_btn_text': '#000000',
    'main_btn_border': '#CCCCCC',
    'main_btn_hover_bg': '#333333',
    'main_btn_hover_text': '#000000',
    'main_btn_pressed_bg': '#444444',
    'main_btn_pressed_text': '#FFFFFF',

    # Accent button (gold border)
    'accent_button_bg': '#FFFFFF',
    'accent_button_text': BRAND_GOLD_DARK,
    'accent_button_border': BRAND_GOLD_DARK,
    'accent_button_hover_bg': '#EEEEEE',
    'accent_button_pressed_bg': BRAND_GOLD_DARK,
    'accent_button_pressed_text': '#FFFFFF',
    
    # Platform button
    'platform_btn_bg': '#FAFAFA',
    'platform_btn_hover_bg': '#F0F0F0',
    
    # Clear/subtle button
    'clear_btn_bg': '#F5F5F5',
    
    # Checkbox
    'checkbox_bg': '#FFFFFF',
    'checkbox_border': '#AAAAAA',
    'checkbox_checked_bg': BRAND_GOLD_DARK,
    'checkbox_checked_border': BRAND_GOLD_DARK,
    'checkbox_hover_border': BRAND_GOLD_DARK,
    
    # Tab widget
    'tab_bg': '#E0E0E0',
    'tab_selected_bg': '#FFFFFF',
    'tab_hover_bg': '#D0D0D0',
    'tab_border': '#CCCCCC',
    'tab_indicator': BRAND_GOLD_DARK,
    
    # Scrollbar
    'scrollbar_bg': '#E0E0E0',
    'scrollbar_handle': '#AAAAAA',
    'scrollbar_handle_hover': BRAND_GOLD_DARK,
    'scrollbar_border': '#CCCCCC',
    
    # List/Table
    'list_bg': '#FFFFFF',
    'list_alt_bg': '#F8F8F8',
    'list_selected_bg': BRAND_GOLD_DARK,
    'list_hover_bg': '#EEEEEE',
    'list_header_bg': '#F0F0F0',
    'list_grid': '#DDDDDD',
    
    # Dialog
    'dialog_bg': '#F5F5F5',
    'dialog_border': '#CCCCCC',
    
    # Status bar
    'statusbar_bg': '#F5F5F5',
    'statusbar_border': '#CCCCCC',
    
    # Drop zone
    'dropzone_bg': '#FFFFFF',
    'dropzone_border': '#CCCCCC',
    'dropzone_active_border': BRAND_GOLD_DARK,
    'dropzone_active_bg': 'rgba(210, 188, 147, 0.3)',
    
    # Tooltip
    'tooltip_bg': '#FFFFFF',
    'tooltip_border': BRAND_GOLD_DARK,
    'tooltip_text': '#000000',
    
    # Success/Warning/Error
    'success': '#28a745',
    'warning': '#FFC107',
    'error': '#dc3545',
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

CONTRAST_ON_DARK: Final[str] = "#FFFFFF"
"""White — used as contrast text on dark/dim backgrounds (e.g. color swatches)"""

SWATCH_BORDER_ON_LIGHT: Final[str] = "#333"
"""Dark border for color swatch buttons on light-colored swatches"""

SWATCH_BORDER_ON_DARK: Final[str] = "#CCC"
"""Light border for color swatch buttons on dark-colored swatches"""

STATUS_ACTIVE_COLOR: Final[str] = "#4CAF50"
"""Green — used for active/running status indicators (e.g. folder watcher)"""


__all__: list[str] = [
    'BRAND_GOLD',
    'BRAND_GOLD_DARK',
    'BRAND_GOLD_RGB',
    'BRAND_GOLD_DARK_RGB',
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