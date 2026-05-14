"""
RNV Icon Builder - UI Package
Contains user interface components and dialogs.

Modules:
    theme_manager: Dark/light theme management, stylesheets
    settings_dialog: Tabbed settings dialog (Sizes, Export, Adjust, Recent, Preview)
    about_dialog: About dialog with Features, Shortcuts, Credits
    preview_utils: Checkerboard patterns, zoom, color palette, preview dialogs
    context_preview: Taskbar/folder/dock mockup previews
    ico_analyzer: Analyze existing ICO files
    metadata_panel: Display image file metadata
    image_adjustments: Brightness, contrast, saturation controls
    debug_button: Developer debug information button
    colors: Color constants, theme color dictionaries
    base_dialog: Base dialog class with SignalMixin + WindowMoveMixin
"""

from .theme_manager import ThemeManager
from .colors import (
    BRAND_GOLD, BRAND_GOLD_DARK,
    BRAND_GOLD_RGB, BRAND_GOLD_DARK_RGB,
    DARK_THEME_COLORS, LIGHT_THEME_COLORS, IMAGE_MODE_COLORS,
    get_theme_colors,
)
from .base_dialog import BaseDialog
from .settings_dialog import SettingsDialog, SettingsButton
from .about_dialog import AboutDialog
from .preview_utils import (
    composite_on_checkerboard,
    composite_with_background,
    pil_to_qpixmap,
    ImagePreviewDialog,
    ComparisonDialog,
    ColorPaletteWidget,
    ZoomControlsWidget,
    BackgroundSelectorWidget,
)
from .context_preview import ContextPreviewDialog
from .ico_analyzer import IcoAnalyzerDialog
from .metadata_panel import MetadataPanel
from .debug_button import DebugButton

__all__: list[str] = [
    # Theme
    'ThemeManager',
    # Colors
    'BRAND_GOLD', 'BRAND_GOLD_DARK',
    'BRAND_GOLD_RGB', 'BRAND_GOLD_DARK_RGB',
    'DARK_THEME_COLORS', 'LIGHT_THEME_COLORS', 'IMAGE_MODE_COLORS',
    'get_theme_colors',
    # Base
    'BaseDialog',
    # Dialogs
    'SettingsDialog', 'SettingsButton',
    'AboutDialog',
    'ContextPreviewDialog',
    'IcoAnalyzerDialog',
    # Preview
    'composite_on_checkerboard',
    'composite_with_background',
    'pil_to_qpixmap',
    'ImagePreviewDialog',
    'ComparisonDialog',
    'ColorPaletteWidget',
    'ZoomControlsWidget',
    'BackgroundSelectorWidget',
    # Panels
    'MetadataPanel',
    'DebugButton',
]
