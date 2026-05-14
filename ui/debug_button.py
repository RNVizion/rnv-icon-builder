"""
RNV Icon Builder - Debug Button Module
Custom QPushButton with image mode support and drag-off detection.

Features:
- Three-state button images (base, hover, pressed)
- Automatic image switching on mouse events
- Drag-off detection to revert state
- Theme manager integration
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QTimer, QSize, QPoint
from PyQt6.QtGui import QPixmap, QIcon, QCursor, QPainter, QEnterEvent

from utils.config import DRAG_TRACK_INTERVAL
from utils.logger import Logger, get_logger_instance

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)

if TYPE_CHECKING:
    from ui.theme_manager import ThemeManager


class DebugButton(QPushButton):
    """
    Custom QPushButton that supports image mode with three states.
    
    States:
        - Base: Normal appearance
        - Hover: Mouse over button
        - Pressed: Button is being pressed
    
    Also includes drag-off detection to revert to base state if
    user drags mouse off button while pressed.
    
    Attributes:
        image_mode_active: Class variable set by theme manager
        button_name: Name/identifier for this button
        base_pixmap: Image for normal state
        hover_pixmap: Image for hover state
        pressed_pixmap: Image for pressed state
        
    Example:
        >>> btn = DebugButton("Click Me")
        >>> btn.set_button_images("base.png", "hover.png", "pressed.png")
        >>> btn.set_theme_manager(theme_manager)
    """
    
    # Class variable set by theme manager
    image_mode_active: bool = False
    
    def __init__(self, text: str = "", parent: QPushButton | None = None) -> None:
        """
        Initialize the debug button.
        
        Args:
            text: Button text
            parent: Parent widget
        """
        super().__init__(text, parent)
        
        # Icon storage
        self._icon: QIcon | None = None
        
        # Button identification
        self.button_name: str = text
        
        # Image state tracking
        self.base_pixmap: QPixmap | None = None
        self.hover_pixmap: QPixmap | None = None
        self.pressed_pixmap: QPixmap | None = None
        
        # Theme manager reference
        self.theme_manager: ThemeManager | None = None
        
        # State tracking
        self.is_pressed_state: bool = False
        self.is_hover_state: bool = False
        
        # Setup
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pressed.connect(self._on_press)
        self.released.connect(self._on_release)
        self.setMouseTracking(True)
        
        # Drag tracking timer (~60fps)
        self.drag_track_timer: QTimer = QTimer(self)
        self.drag_track_timer.timeout.connect(self._check_mouse_position)
        self.drag_track_timer.setInterval(DRAG_TRACK_INTERVAL)
    
    def setIcon(self, icon: QIcon) -> None:
        """
        Store icon and repaint.
        
        Args:
            icon: Icon to set
        """
        self._icon = icon
        super().setIcon(icon)
        self.update()
    
    def set_button_images(
        self,
        base_path: str,
        hover_path: str,
        pressed_path: str
    ) -> None:
        """
        Set the three button state images.
        
        Args:
            base_path: Path to base state image
            hover_path: Path to hover state image
            pressed_path: Path to pressed state image
            
        Example:
            >>> btn.set_button_images(
            ...     "images/btn_base.png",
            ...     "images/btn_hover.png",
            ...     "images/btn_pressed.png"
            ... )
        """
        self.base_pixmap = QPixmap(base_path) if os.path.exists(base_path) else None
        self.hover_pixmap = QPixmap(hover_path) if os.path.exists(hover_path) else self.base_pixmap
        self.pressed_pixmap = QPixmap(pressed_path) if os.path.exists(pressed_path) else self.base_pixmap
        
        if self.base_pixmap:
            logger.debug(f"Button '{self.button_name}': loaded images "
                         f"(base={'ok' if os.path.exists(base_path) else 'missing'}, "
                         f"hover={'ok' if os.path.exists(hover_path) else 'fallback'}, "
                         f"pressed={'ok' if os.path.exists(pressed_path) else 'fallback'})")
            self.setIcon(QIcon(self.base_pixmap))
        else:
            logger.warning(f"Button '{self.button_name}': base image not found: {base_path}")
    
    def set_theme_manager(self, theme_manager: ThemeManager) -> None:
        """
        Set theme manager reference.
        
        Args:
            theme_manager: ThemeManager instance
            
        Example:
            >>> btn.set_theme_manager(app.theme_manager)
        """
        self.theme_manager = theme_manager
    
    def has_images(self) -> bool:
        """
        Check if button has image resources loaded.
        
        Returns:
            True if at least base image is loaded
        """
        return self.base_pixmap is not None
    
    def _check_mouse_position(self) -> None:
        """
        Check if mouse is over button while pressed (for drag tracking).
        
        Called by timer at ~60fps during press state to detect
        when user drags mouse off the button.
        """
        if not self.is_pressed_state:
            return
        
        # Get global cursor position
        global_pos: QPoint = QCursor.pos()
        
        # Convert to button's local coordinates
        local_pos: QPoint = self.mapFromGlobal(global_pos)
        
        # Check if inside button
        is_inside: bool = self.rect().contains(local_pos)
        
        if not is_inside:
            if self.is_hover_state:  # Only update if state changed
                self.is_hover_state = False
                self._update_button_state('base')
        else:
            if not self.is_hover_state:  # Only update if state changed
                self.is_hover_state = True
                self._update_button_state('pressed')
    
    def enterEvent(self, event: QEnterEvent) -> None:
        """
        Handle mouse enter (hover).
        
        Args:
            event: Mouse enter event
        """
        super().enterEvent(event)
        if self.theme_manager and self.theme_manager.is_image_mode():
            if not self.is_pressed_state:
                self.is_hover_state = True
                self._update_button_state('hover')
    
    def leaveEvent(self, event) -> None:
        """
        Handle mouse leave.
        
        Args:
            event: Mouse leave event
        """
        super().leaveEvent(event)
        if self.theme_manager and self.theme_manager.is_image_mode():
            if not self.is_pressed_state:
                self.is_hover_state = False
                self._update_button_state('base')
    
    def _on_press(self) -> None:
        """Handle press event - start drag tracking."""
        self.is_pressed_state = True
        if self.theme_manager and self.theme_manager.is_image_mode():
            self.drag_track_timer.start()
            self._update_button_state('pressed')
    
    def _on_release(self) -> None:
        """Handle release event - stop drag tracking and update state."""
        self.is_pressed_state = False
        if self.theme_manager and self.theme_manager.is_image_mode():
            self.drag_track_timer.stop()
            
            # Check final position
            global_pos: QPoint = QCursor.pos()
            local_pos: QPoint = self.mapFromGlobal(global_pos)
            is_inside: bool = self.rect().contains(local_pos)
            
            if is_inside:
                self.is_hover_state = True
                self._update_button_state('hover')
            else:
                self.is_hover_state = False
                self._update_button_state('base')
    
    def _update_button_state(self, state: str) -> None:
        """
        Update button to show specified state.
        
        Args:
            state: State to show ('base', 'hover', 'pressed')
        """
        if not self.theme_manager or not self.theme_manager.is_image_mode():
            return
        
        # Select the appropriate pixmap
        pixmap: QPixmap | None = None
        
        if state == 'base':
            pixmap = self.base_pixmap
        elif state == 'hover':
            pixmap = self.hover_pixmap if self.hover_pixmap else self.base_pixmap
        elif state == 'pressed':
            pixmap = self.pressed_pixmap if self.pressed_pixmap else self.base_pixmap
        
        if pixmap and not pixmap.isNull():
            self.setIcon(QIcon(pixmap))
    
    def paintEvent(self, event) -> None:
        """
        Custom paint event to fill button area with icon in image mode.
        
        Args:
            event: Paint event
        """
        if self.image_mode_active and self._icon:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            rect = self.rect()
            # Get pixmap and scale it to full rect
            pixmap: QPixmap = self._icon.pixmap(QSize(rect.width(), rect.height()))
            painter.drawPixmap(rect, pixmap)
        else:
            super().paintEvent(event)
    
    def reset_to_text_mode(self) -> None:
        """
        Reset button to text mode (non-image mode).
        
        Restores text label and removes icon.
        
        Example:
            >>> btn.reset_to_text_mode()
        """
        self.image_mode_active = False
        if self.button_name:
            self.setText(self.button_name)
        self.setIcon(QIcon())
        logger.debug(f"Button '{self.button_name}': reset to text mode")
    
    def switch_to_image_mode(self) -> None:
        """
        Switch button to image mode.
        
        Hides text and shows image icon.
        
        Example:
            >>> btn.switch_to_image_mode()
        """
        self.image_mode_active = True
        if self.text():
            self.button_name = self.text()
            self.setText("")
        if self.base_pixmap:
            self.setIcon(QIcon(self.base_pixmap))
        logger.debug(f"Button '{self.button_name}': switched to image mode")
    
    def get_state(self) -> str:
        """
        Get current button state.
        
        Returns:
            Current state ('base', 'hover', or 'pressed')
        """
        if self.is_pressed_state:
            return 'pressed'
        elif self.is_hover_state:
            return 'hover'
        else:
            return 'base'


# ==================== Module Exports ====================

__all__: list[str] = [
    'DebugButton',
]
