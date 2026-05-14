"""
RNV Icon Builder - Base Dialog Module
Provides a base class for application dialogs with common functionality.

Features:
- Signal manager integration (SignalMixin)
- Windows compositor glitch prevention (WindowMoveMixin)
- Automatic cleanup on close
- Theme-aware styling helpers
- Consistent initialization pattern

Usage:
    from ui.base_dialog import BaseDialog
    
    class MyDialog(BaseDialog):
        def __init__(self, parent=None):
            super().__init__(
                parent=parent,
                title="My Dialog",
                modal=True,
                fixed_size=(500, 400)  # Optional
            )
            self._setup_ui()
            self._apply_theme()
        
        def _setup_ui(self):
            # Build your UI here
            pass
        
        def _apply_theme(self):
            # Apply theme styling here
            is_dark = self._is_dark_theme()
            ...
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QDialog, QWidget
from PyQt6.QtGui import QMoveEvent

from utils.signal_manager import SignalMixin, WindowMoveMixin
from utils.logger import Logger, get_logger_instance
from utils.dialog_helper import DialogHelper
from ui.colors import get_theme_colors, BRAND_GOLD, BRAND_GOLD_DARK

if TYPE_CHECKING:
    pass

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)


class BaseDialog(QDialog, SignalMixin, WindowMoveMixin):
    """
    Base class for application dialogs with common functionality.
    
    Provides:
    - Signal manager integration for tracking connections
    - Windows compositor glitch prevention during window drag
    - Automatic cleanup on close
    - Theme detection helpers
    - Consistent initialization pattern
    
    Subclasses should:
    1. Call super().__init__() with appropriate parameters
    2. Implement _setup_ui() to build the dialog UI
    3. Implement _apply_theme() to apply theme styling
    4. Override closeEvent() if additional cleanup is needed (call super!)
    
    Example:
        class MyCustomDialog(BaseDialog):
            def __init__(self, parent=None):
                super().__init__(
                    parent=parent,
                    title="Custom Dialog",
                    modal=True,
                    min_size=(400, 300)
                )
                self._setup_ui()
                self._apply_theme()
            
            def _setup_ui(self):
                layout = QVBoxLayout(self)
                # ... build UI
            
            def _apply_theme(self):
                is_dark = self._is_dark_theme()
                # ... apply theme styles
    """
    
    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "Dialog",
        modal: bool = True,
        fixed_size: tuple[int, int] | None = None,
        min_size: tuple[int, int] | None = None,
        max_size: tuple[int, int] | None = None,
        enable_move_handler: bool = True
    ) -> None:
        """
        Initialize the base dialog.
        
        Args:
            parent: Parent widget
            title: Window title
            modal: Whether dialog is modal (blocks parent interaction)
            fixed_size: Optional (width, height) for fixed size dialog
            min_size: Optional (width, height) minimum size
            max_size: Optional (width, height) maximum size
            enable_move_handler: Whether to enable Windows compositor fix
        """
        super().__init__(parent)
        
        # Initialize signal manager for tracking connections
        self.init_signal_manager()
        
        # Initialize move handler if enabled
        self._move_handler_enabled = enable_move_handler
        if enable_move_handler:
            self.init_move_handler()
        
        # Set window properties
        self.setWindowTitle(title)
        self.setModal(modal)
        
        # Set size constraints (use min/max instead of setFixedSize to
        # avoid Windows compositor glitches during window dragging)
        if fixed_size is not None:
            self.setMinimumSize(fixed_size[0], fixed_size[1])
            self.setMaximumSize(fixed_size[0], fixed_size[1])
        else:
            if min_size is not None:
                self.setMinimumSize(min_size[0], min_size[1])
            if max_size is not None:
                self.setMaximumSize(max_size[0], max_size[1])
        
        logger.debug(f"BaseDialog initialized: {title}")
    
    def moveEvent(self, event: QMoveEvent) -> None:
        """Handle window move events to prevent rendering glitches."""
        if self._move_handler_enabled:
            self._handle_move_event(event)
        super().moveEvent(event)
    
    def closeEvent(self, event) -> None:
        """
        Handle dialog close event for proper resource cleanup.
        
        Subclasses that override this MUST call super().closeEvent(event).
        """
        # Clean up move handler
        if self._move_handler_enabled:
            self.cleanup_move_handler()
        
        # Disconnect all tracked signals
        disconnected = self.disconnect_all_signals()
        if disconnected > 0:
            logger.debug(f"Disconnected {disconnected} tracked signals")
        
        logger.debug(f"Dialog closed: {self.windowTitle()}")
        super().closeEvent(event)
    
    def _is_dark_theme(self) -> bool:
        """
        Detect if the application is using a dark theme.
        
        Returns:
            True if dark theme, False if light theme
        """
        return DialogHelper._is_dark_theme(self.parent())
    
    def _get_dialog_style(self) -> str:
        """
        Get theme-appropriate stylesheet for the dialog.
        
        Returns:
            CSS stylesheet string
        """
        return DialogHelper._get_style(self.parent())
    
    def _setup_ui(self) -> None:
        """
        Setup the dialog UI. Override in subclass.
        
        This method is called by subclasses after super().__init__().
        """
        pass
    
    def _apply_theme(self) -> None:
        """
        Apply theme styling to the dialog. Override in subclass.
        
        This method is called by subclasses after _setup_ui().
        """
        pass


class ThemedDialog(BaseDialog):
    """
    BaseDialog with automatic theme application.
    
    Extends BaseDialog to automatically apply consistent theming
    based on the parent widget's theme. Useful for simple dialogs
    that don't need custom styling.
    
    Example:
        class SimpleInfoDialog(ThemedDialog):
            def __init__(self, parent=None, message=""):
                super().__init__(parent, title="Info")
                self.message = message
                self._setup_ui()
                # Theme is applied automatically
            
            def _setup_ui(self):
                layout = QVBoxLayout(self)
                layout.addWidget(QLabel(self.message))
    """
    
    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "Dialog",
        modal: bool = True,
        fixed_size: tuple[int, int] | None = None,
        min_size: tuple[int, int] | None = None,
        max_size: tuple[int, int] | None = None,
        enable_move_handler: bool = True
    ) -> None:
        """Initialize themed dialog with automatic theme application."""
        super().__init__(
            parent=parent,
            title=title,
            modal=modal,
            fixed_size=fixed_size,
            min_size=min_size,
            max_size=max_size,
            enable_move_handler=enable_move_handler
        )
    
    def showEvent(self, event) -> None:
        """Apply theme when dialog is shown."""
        self._apply_default_theme()
        super().showEvent(event)
    
    def _apply_default_theme(self) -> None:
        """Apply default theme styling based on parent's theme."""
        is_dark = self._is_dark_theme()
        theme = get_theme_colors(is_dark)

        # Use BRAND_GOLD for dark theme, BRAND_GOLD_DARK for light
        accent = BRAND_GOLD if is_dark else BRAND_GOLD_DARK

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme['dialog_bg']};
                color: {theme['text_primary']};
            }}
            QLabel {{
                color: {theme['text_primary']};
            }}
            QPushButton {{
                background-color: {theme['button_bg']};
                color: {theme['button_text']};
                border: 1px solid {theme['border_default']};
                padding: 6px 16px;
                border-radius: 4px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover_bg']};
                color: {theme['button_hover_text']};
                border-color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {accent};
                color: {theme['button_pressed_text']};
            }}
            QGroupBox {{
                color: {theme['text_primary']};
                border: 1px solid {theme['border_default']};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)


# ==================== Module Exports ====================

__all__: list[str] = [
    'BaseDialog',
    'ThemedDialog',
]