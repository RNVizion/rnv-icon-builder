"""
RNV Icon Builder - Theme Manager Module
Manages application themes: Dark Mode, Light Mode, and Image Mode.

Features:
- Three theme modes (Dark, Light, Image)
- Background image loading and scaling
- Theme cycling
- Scrollbar style generation
"""

from __future__ import annotations

import io
from typing import Any, Final

from PyQt6.QtGui import QPixmap
from PIL import Image

from utils.config import BACKGROUND_IMAGE_PATH, MAX_IMAGE_DIMENSION, MAX_IMAGE_PIXELS
from utils.logger import Logger, get_logger_instance
from ui.colors import (
    DARK_THEME_COLORS,
    LIGHT_THEME_COLORS,
    IMAGE_MODE_COLORS,
)

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)


# Type alias for theme dictionary
type ThemeDict = dict[str, str]


class ThemeManager:
    """
    Manages application themes with Dark Mode, Light Mode, and Image Mode.
    
    Handles background image loading, theme cycling, and provides theme data.
    
    Attributes:
        current_theme: Current theme name ('dark', 'light', 'image')
        image_mode_available: Whether Image Mode resources exist
        image_mode_active: Whether Image Mode is currently active
        background_pixmap: Loaded background image for Image Mode
        
    Example:
        >>> manager = ThemeManager()
        >>> manager.detect_image_resources()
        >>> manager.cycle_theme()
        >>> theme = manager.get_current_theme()
    """
    
    # ==================== Theme Definitions ====================
    # Color values sourced from utils/colors.py — do not hardcode here.

    DARK_THEME: Final[ThemeDict] = {
        'name': 'Dark',
        **{k: DARK_THEME_COLORS[k] for k in (
            'window_bg', 'text_primary', 'border_default', 'hover_bg',
            'checkbox_bg', 'checkbox_border',
        )},
        # Main window buttons use inverse system — see colors.py main_btn_* keys
        'button_bg': DARK_THEME_COLORS['main_btn_bg'],
        'button_text': DARK_THEME_COLORS['main_btn_text'],
        'button_hover_bg': DARK_THEME_COLORS['main_btn_hover_bg'],
        'button_hover_text': DARK_THEME_COLORS['main_btn_hover_text'],
        'button_pressed_bg': DARK_THEME_COLORS['main_btn_pressed_bg'],
        'button_pressed_text': DARK_THEME_COLORS['main_btn_pressed_text'],
        # Legacy key aliases kept for backward-compatibility
        'text_color': DARK_THEME_COLORS['text_primary'],
        'border_color': DARK_THEME_COLORS['main_btn_border'],
        'hover_color': DARK_THEME_COLORS['hover_bg'],
    }

    LIGHT_THEME: Final[ThemeDict] = {
        'name': 'Light',
        **{k: LIGHT_THEME_COLORS[k] for k in (
            'window_bg', 'text_primary', 'border_default', 'hover_bg',
            'checkbox_bg', 'checkbox_border',
        )},
        # Main window buttons use inverse system — see colors.py main_btn_* keys
        'button_bg': LIGHT_THEME_COLORS['main_btn_bg'],
        'button_text': LIGHT_THEME_COLORS['main_btn_text'],
        'button_hover_bg': LIGHT_THEME_COLORS['main_btn_hover_bg'],
        'button_hover_text': LIGHT_THEME_COLORS['main_btn_hover_text'],
        'button_pressed_bg': LIGHT_THEME_COLORS['main_btn_pressed_bg'],
        'button_pressed_text': LIGHT_THEME_COLORS['main_btn_pressed_text'],
        # Legacy key aliases kept for backward-compatibility
        'text_color': LIGHT_THEME_COLORS['text_primary'],
        'border_color': LIGHT_THEME_COLORS['main_btn_border'],
        'hover_color': LIGHT_THEME_COLORS['hover_bg'],
    }
    
    # ==================== Scrollbar Styles ====================
    # Built dynamically from colors.py so all values stay in one place.

    @staticmethod
    def _build_scrollbar_style(
        bg: str,
        handle: str,
        handle_hover: str,
        border: str,
    ) -> str:
        """Generate a scrollbar stylesheet from the given color values."""
        return f"""
        QScrollBar:vertical {{
            background: {bg};
            width: 12px;
            margin: 0px;
            border: 1px solid {border};
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background: {handle};
            min-height: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {handle_hover};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollBar:horizontal {{
            background: {bg};
            height: 12px;
            margin: 0px;
            border: 1px solid {border};
            border-radius: 6px;
        }}
        QScrollBar::handle:horizontal {{
            background: {handle};
            min-width: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {handle_hover};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
    """

    # Pre-built scrollbar stylesheets (lazily referenced via get_scrollbar_style)
    SCROLLBAR_DARK: Final[str] = _build_scrollbar_style.__func__(  # type: ignore[attr-defined]
        bg=DARK_THEME_COLORS['scrollbar_bg'],
        handle=DARK_THEME_COLORS['scrollbar_handle'],
        handle_hover=DARK_THEME_COLORS['scrollbar_handle_hover'],
        border=DARK_THEME_COLORS['scrollbar_border'],
    )

    SCROLLBAR_LIGHT: Final[str] = _build_scrollbar_style.__func__(  # type: ignore[attr-defined]
        bg=LIGHT_THEME_COLORS['scrollbar_bg'],
        handle=LIGHT_THEME_COLORS['scrollbar_handle'],
        handle_hover=LIGHT_THEME_COLORS['scrollbar_handle_hover'],
        border=LIGHT_THEME_COLORS['scrollbar_border'],
    )

    SCROLLBAR_IMAGE: Final[str] = _build_scrollbar_style.__func__(  # type: ignore[attr-defined]
        bg=IMAGE_MODE_COLORS['scrollbar_bg'],
        handle=IMAGE_MODE_COLORS['scrollbar_handle'],
        handle_hover=IMAGE_MODE_COLORS['scrollbar_handle_hover'],
        border=IMAGE_MODE_COLORS['scrollbar_border'],
    )
    
    # ==================== Initialization ====================
    
    def __init__(self) -> None:
        """Initialize theme manager with default settings."""
        self.current_theme: str = 'dark'
        self.image_mode_available: bool = False
        self.image_mode_active: bool = False
        self.background_pixmap: QPixmap | None = None
        
        logger.info("ThemeManager initialized")
        logger.debug(f"Initial theme: {self.current_theme}")
    
    # ==================== Resource Detection ====================
    
    def detect_image_resources(self) -> bool:
        """
        Check if custom background image exists and preload it.
        
        Automatically resizes large images to improve performance.
        
        Returns:
            True if Image Mode resources are available
            
        Example:
            >>> manager = ThemeManager()
            >>> if manager.detect_image_resources():
            ...     print("Image Mode available!")
        """
        has_background: bool = BACKGROUND_IMAGE_PATH.exists()
        
        if has_background:
            try:
                # Temporarily raise PIL pixel limit for background images
                # (we control the source, and resize to MAX_IMAGE_DIMENSION anyway)
                _original_max_pixels = Image.MAX_IMAGE_PIXELS
                Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
                
                # Load with PIL using context manager to ensure file handle is closed
                with Image.open(str(BACKGROUND_IMAGE_PATH)) as img:
                    # Load image data into memory before context manager closes file
                    img.load()
                    original_size: tuple[int, int] = (img.width, img.height)
                    
                    # Resize if image is too large (over 4K resolution)
                    if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
                        # Calculate new size maintaining aspect ratio
                        ratio: float = min(
                            MAX_IMAGE_DIMENSION / img.width,
                            MAX_IMAGE_DIMENSION / img.height
                        )
                        new_size: tuple[int, int] = (
                            int(img.width * ratio),
                            int(img.height * ratio)
                        )
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                        logger.info(f"Resized background image  ({new_size[0]}x{new_size[1]})")
                    
                    # Convert to QPixmap
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    buffer.seek(0)
                    
                    self.background_pixmap = QPixmap()
                    if self.background_pixmap.loadFromData(buffer.getvalue()):
                        has_background = True
                        logger.success(f"Loaded background image  ({img.width}x{img.height})")
                    else:
                        has_background = False
                        self.background_pixmap = None
                        logger.error("Failed to load background image into QPixmap")
                    
            except Exception as e:
                logger.error(f"Error loading background image: {e}")
                has_background = False
                self.background_pixmap = None
            finally:
                # Restore PIL pixel limit to default safety value
                Image.MAX_IMAGE_PIXELS = _original_max_pixels
        else:
            logger.debug(f"Background image not found at: {BACKGROUND_IMAGE_PATH}")
        
        self.image_mode_available = has_background
        
        # Auto-activate Image Mode if available
        if self.image_mode_available:
            self.image_mode_active = True
            self.current_theme = 'image'
            logger.success("Image Mode available  (background: True)")
        else:
            logger.debug("Image Mode not available, using Dark Mode")
        
        return self.image_mode_available
    
    # ==================== Theme Management ====================
    
    def cycle_theme(self) -> str:
        """
        Cycle through available themes.
        
        Returns:
            New current theme name
            
        Example:
            >>> manager.cycle_theme()  # 'dark' -> 'light'
            >>> manager.cycle_theme()  # 'light' -> 'image' (if available)
        """
        old_theme: str = self.current_theme
        
        if self.image_mode_available:
            # Cycle: Image → Dark → Light → Image
            if self.current_theme == 'image':
                self.current_theme = 'dark'
                self.image_mode_active = False
            elif self.current_theme == 'dark':
                self.current_theme = 'light'
            else:
                self.current_theme = 'image'
                self.image_mode_active = True
        else:
            # Cycle: Dark → Light → Dark
            self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        
        logger.info(f"Theme cycled: {old_theme} → {self.current_theme}")
        return self.current_theme
    
    def set_theme(self, theme_name: str) -> bool:
        """
        Set a specific theme by name.
        
        Args:
            theme_name: Theme to set ('dark', 'light', 'image')
            
        Returns:
            True if theme was set successfully
            
        Example:
            >>> manager.set_theme('light')
        """
        theme_name = theme_name.lower()
        
        if theme_name == 'image' and not self.image_mode_available:
            logger.warning("Image Mode not available")
            return False
        
        if theme_name not in ('dark', 'light', 'image'):
            logger.warning(f"Unknown theme: {theme_name}")
            return False
        
        self.current_theme = theme_name
        self.image_mode_active = (theme_name == 'image')
        logger.info(f"Theme set to: {theme_name}")
        return True
    
    def get_current_theme(self) -> ThemeDict | None:
        """
        Return current theme dictionary.
        
        Returns:
            Theme dictionary or None for Image Mode
            
        Example:
            >>> theme = manager.get_current_theme()
            >>> if theme:
            ...     bg_color = theme['window_bg']
        """
        if self.current_theme == 'dark':
            return self.DARK_THEME
        elif self.current_theme == 'light':
            return self.LIGHT_THEME
        else:
            return None  # Image Mode has no theme dict
    
    def get_theme_display_name(self) -> str:
        """
        Get human-readable theme name.
        
        Returns:
            Display name of current theme
            
        Example:
            >>> name = manager.get_theme_display_name()
            >>> print(name)  # "Dark Mode"
        """
        if self.current_theme == 'image':
            return "Image Mode"
        elif self.current_theme == 'dark':
            return "Dark Mode"
        else:
            return "Light Mode"
    
    def is_image_mode(self) -> bool:
        """
        Check if Image Mode is currently active.
        
        Returns:
            True if Image Mode active
            
        Example:
            >>> if manager.is_image_mode():
            ...     show_background_image()
        """
        return self.image_mode_active
    
    def is_dark_mode(self) -> bool:
        """
        Check if Dark Mode is currently active.
        
        Returns:
            True if Dark Mode active
        """
        return self.current_theme == 'dark'
    
    def is_light_mode(self) -> bool:
        """
        Check if Light Mode is currently active.
        
        Returns:
            True if Light Mode active
        """
        return self.current_theme == 'light'
    
    def get_scrollbar_style(self) -> str:
        """
        Get scrollbar stylesheet for current theme.
        
        Returns:
            Scrollbar CSS stylesheet
            
        Example:
            >>> style = manager.get_scrollbar_style()
            >>> widget.setStyleSheet(style)
        """
        if self.current_theme == 'image':
            return self.SCROLLBAR_IMAGE
        elif self.current_theme == 'dark':
            return self.SCROLLBAR_DARK
        else:
            return self.SCROLLBAR_LIGHT
    
    # ==================== Background Management ====================
    
    def get_background_pixmap(self) -> QPixmap | None:
        """
        Get background pixmap for Image Mode.
        
        Returns:
            Background QPixmap or None
            
        Example:
            >>> pixmap = manager.get_background_pixmap()
            >>> if pixmap:
            ...     label.setPixmap(pixmap)
        """
        return self.background_pixmap
    
    def has_background(self) -> bool:
        """
        Check if background image is loaded.
        
        Returns:
            True if background exists
            
        Example:
            >>> if manager.has_background():
            ...     setup_background_label()
        """
        return self.background_pixmap is not None
    
    # ==================== Theme Information ====================
    
    def get_available_themes(self) -> list[str]:
        """
        Get list of available theme names.
        
        Returns:
            List of theme names
            
        Example:
            >>> themes = manager.get_available_themes()
            >>> print(themes)  # ['dark', 'light', 'image']
        """
        themes: list[str] = ['dark', 'light']
        if self.image_mode_available:
            themes.append('image')
        return themes
    
    def get_theme_info(self) -> dict[str, Any]:
        """
        Get information about current theme state.
        
        Returns:
            Dictionary with theme information
            
        Example:
            >>> info = manager.get_theme_info()
            >>> print(f"Current: {info['current']}")
        """
        return {
            'current': self.current_theme,
            'display_name': self.get_theme_display_name(),
            'is_image_mode': self.image_mode_active,
            'image_mode_available': self.image_mode_available,
            'has_background': self.has_background(),
            'available_themes': self.get_available_themes(),
        }


# ==================== Module Exports ====================

__all__: list[str] = [
    'ThemeManager',
    'ThemeDict',
]