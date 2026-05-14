"""
RNV Icon Builder - Dialog Helper
Centralized dialog interface for consistent UX across the application.

Features:
- Consistent styling across all dialogs
- Theme-aware dialogs (dark/light)
- Less code duplication
- Simple API for common dialog patterns

Usage Examples:
    # Show error
    DialogHelper.show_error(self, "Failed to load file!")
    
    # Show warning
    DialogHelper.show_warning(self, "Image size out of range")
    
    # Show info
    DialogHelper.show_info(self, "ICO file built successfully!")
    
    # Confirm action
    if DialogHelper.confirm(self, "Delete this file?"):
        delete_file()
    
    # Ask yes/no/cancel
    result = DialogHelper.ask_yes_no_cancel(self, "Save changes?")
    if result == DialogResult.YES:
        save()
"""

from __future__ import annotations

from enum import Enum

from PyQt6.QtWidgets import QMessageBox, QWidget

# Import logger
from utils.logger import Logger, get_logger_instance

# NOTE: ui.colors is NOT imported at the top level here.
# utils.dialog_helper is imported early in the startup chain (via utils/__init__.py
# and utils.error_handler), before ui is fully initialized. A top-level
# 'from ui.colors import ...' would create a circular import: utils -> ui -> utils.
# Instead, get_theme_colors() is imported lazily inside each method that needs it.

logger: Logger = get_logger_instance(__name__)


class DialogResult(Enum):
    """Dialog result options for multi-choice dialogs."""
    YES = 1
    NO = 2
    CANCEL = 3
    OK = 4


class DialogHelper:
    """
    Centralized dialog management for consistent UX.
    
    Benefits:
    - Consistent styling across all dialogs
    - Theme-aware dialogs
    - Less code duplication
    - Single point to customize all dialogs
    
    All methods are static for easy access without instantiation.
    """
    
    # Default window titles
    DEFAULT_ERROR_TITLE = "Error"
    DEFAULT_WARNING_TITLE = "Warning"
    DEFAULT_INFO_TITLE = "Information"
    DEFAULT_CONFIRM_TITLE = "Confirm"
    DEFAULT_SUCCESS_TITLE = "Success"
    
    @staticmethod
    def _get_style(parent: QWidget | None) -> str:
        """
        Get the appropriate dialog style based on current theme.
        
        Args:
            parent: Parent widget to detect theme from
            
        Returns:
            CSS stylesheet string
        """
        is_dark = DialogHelper._is_dark_theme(parent)
        
        if is_dark:
            return DialogHelper._get_style_dark()
        else:
            return DialogHelper._get_style_light()
    
    @staticmethod
    def _get_style_dark() -> str:
        """
        Get dark theme dialog stylesheet.
        
        Returns:
            CSS stylesheet string for dark theme
        """
        from ui.colors import get_theme_colors  # lazy import - avoids circular dependency
        c = get_theme_colors(is_dark=True)
        return f"""
            QMessageBox {{
                background-color: {c['card_bg']};
                color: {c['text_primary']};
            }}
            QMessageBox QLabel {{
                color: {c['text_primary']};
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {c['button_bg']};
                color: {c['button_text']};
                border: 1px solid {c['button_border']};
                padding: 6px 16px;
                border-radius: 4px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background-color: {c['button_hover_bg']};
                color: {c['button_hover_text']};
                border-color: {c['border_focus']};
            }}
            QPushButton:pressed {{
                background-color: {c['button_pressed_bg']};
                color: {c['button_pressed_text']};
            }}
            QPushButton:default {{
                border: 2px solid {c['border_focus']};
            }}
            QTextEdit {{
                background-color: {c['panel_bg']};
                color: {c['text_primary']};
                border: 1px solid {c['border_hover']};
            }}
        """
    
    @staticmethod
    def _get_style_light() -> str:
        """
        Get light theme dialog stylesheet.
        
        Returns:
            CSS stylesheet string for light theme
        """
        from ui.colors import get_theme_colors  # lazy import - avoids circular dependency
        c = get_theme_colors(is_dark=False)
        return f"""
            QMessageBox {{
                background-color: {c['dialog_bg']};
                color: {c['text_primary']};
            }}
            QMessageBox QLabel {{
                color: {c['text_primary']};
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {c['button_bg']};
                color: {c['button_text']};
                border: 1px solid {c['button_border']};
                padding: 6px 16px;
                border-radius: 4px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background-color: {c['button_hover_bg']};
                color: {c['button_hover_text']};
                border-color: {c['border_focus']};
            }}
            QPushButton:pressed {{
                background-color: {c['button_pressed_bg']};
                color: {c['button_pressed_text']};
            }}
            QPushButton:default {{
                border: 2px solid {c['border_focus']};
            }}
            QTextEdit {{
                background-color: {c['input_bg']};
                color: {c['text_primary']};
                border: 1px solid {c['input_border']};
            }}
        """
    
    @staticmethod
    def _is_dark_theme(parent: QWidget | None) -> bool:
        """
        Detect if the parent widget is using a dark theme.
        
        Args:
            parent: Parent widget to check
            
        Returns:
            True if dark theme, False if light theme
        """
        if parent is None:
            return True  # Default to dark
        
        # Try to get theme from parent's theme_manager attribute
        # Walk up the parent chain to find the main window
        widget = parent
        while widget is not None:
            if hasattr(widget, 'theme_manager'):
                theme_manager = widget.theme_manager
                if hasattr(theme_manager, 'current_theme'):
                    return theme_manager.current_theme != 'light'
                if hasattr(theme_manager, 'is_dark_mode'):
                    return theme_manager.is_dark_mode()
            # Try parent widget
            widget = widget.parent() if hasattr(widget, 'parent') else None
        
        # Fallback: check the window's background color
        try:
            palette = parent.palette()
            bg_color = palette.color(palette.ColorRole.Window)
            # If background is dark (luminance < 128), it's dark theme
            luminance = (bg_color.red() * 0.299 + bg_color.green() * 0.587 + bg_color.blue() * 0.114)
            return luminance < 128
        except Exception:
            return True  # Default to dark on error
    
    @staticmethod
    def show_error(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        detailed_text: str | None = None
    ) -> None:
        """
        Show error dialog.
        
        Args:
            parent: Parent widget
            message: Error message to display
            title: Optional custom title (default: "Error")
            detailed_text: Optional detailed error info
        
        Example:
            DialogHelper.show_error(self, "Failed to load image!")
            DialogHelper.show_error(self, "File not found", detailed_text=str(exception))
        """
        title = title or DialogHelper.DEFAULT_ERROR_TITLE
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))
        
        if detailed_text:
            msg_box.setDetailedText(detailed_text)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    @staticmethod
    def show_warning(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        detailed_text: str | None = None
    ) -> None:
        """
        Show warning dialog.
        
        Args:
            parent: Parent widget
            message: Warning message to display
            title: Optional custom title (default: "Warning")
            detailed_text: Optional detailed warning info
        
        Example:
            DialogHelper.show_warning(self, "Image will be scaled down to fit")
        """
        title = title or DialogHelper.DEFAULT_WARNING_TITLE
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))
        
        if detailed_text:
            msg_box.setDetailedText(detailed_text)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    @staticmethod
    def show_info(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        detailed_text: str | None = None
    ) -> None:
        """
        Show information dialog.
        
        Args:
            parent: Parent widget
            message: Information message to display
            title: Optional custom title (default: "Information")
            detailed_text: Optional detailed info
        
        Example:
            DialogHelper.show_info(self, "ICO file created successfully!")
        """
        title = title or DialogHelper.DEFAULT_INFO_TITLE
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))
        
        if detailed_text:
            msg_box.setDetailedText(detailed_text)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    @staticmethod
    def show_success(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        detailed_text: str | None = None
    ) -> None:
        """
        Show success dialog (information with success title).
        
        Args:
            parent: Parent widget
            message: Success message to display
            title: Optional custom title (default: "Success")
            detailed_text: Optional detailed info
        
        Example:
            DialogHelper.show_success(self, "Export completed!")
        """
        title = title or DialogHelper.DEFAULT_SUCCESS_TITLE
        DialogHelper.show_info(parent, message, title, detailed_text)
    
    @staticmethod
    def confirm(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        default_yes: bool = False
    ) -> bool:
        """
        Show yes/no confirmation dialog.
        
        Args:
            parent: Parent widget
            message: Question to ask
            title: Optional custom title (default: "Confirm")
            default_yes: If True, Yes is default button
        
        Returns:
            True if user clicked Yes, False if No
        
        Example:
            if DialogHelper.confirm(self, "Delete all files?"):
                delete_all()
        """
        title = title or DialogHelper.DEFAULT_CONFIRM_TITLE
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if default_yes:
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        else:
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        result = msg_box.exec()
        return result == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def ask_yes_no_cancel(
        parent: QWidget | None,
        message: str,
        title: str | None = None
    ) -> DialogResult:
        """
        Show yes/no/cancel dialog.
        
        Args:
            parent: Parent widget
            message: Question to ask
            title: Optional custom title (default: "Confirm")
        
        Returns:
            DialogResult.YES, DialogResult.NO, or DialogResult.CANCEL
        
        Example:
            result = DialogHelper.ask_yes_no_cancel(self, "Save changes before closing?")
            if result == DialogResult.YES:
                save_and_close()
            elif result == DialogResult.NO:
                close_without_saving()
            # CANCEL = do nothing
        """
        title = title or DialogHelper.DEFAULT_CONFIRM_TITLE
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No | 
            QMessageBox.StandardButton.Cancel
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        
        result = msg_box.exec()
        
        if result == QMessageBox.StandardButton.Yes:
            return DialogResult.YES
        elif result == QMessageBox.StandardButton.No:
            return DialogResult.NO
        else:
            return DialogResult.CANCEL
    
    @staticmethod
    def show_custom(
        parent: QWidget | None,
        title: str,
        message: str,
        icon: QMessageBox.Icon = QMessageBox.Icon.Information,
        buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
        default_button: QMessageBox.StandardButton | None = None,
        detailed_text: str | None = None
    ) -> QMessageBox.StandardButton:
        """
        Show custom dialog with full control.
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Message to display
            icon: Icon type
            buttons: Button combination
            default_button: Default button
            detailed_text: Optional detailed info
        
        Returns:
            The button that was clicked
        
        Example:
            result = DialogHelper.show_custom(
                self,
                "Custom Dialog",
                "Choose an option",
                icon=QMessageBox.Icon.Question,
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        """
        msg_box = QMessageBox(parent)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))
        msg_box.setStandardButtons(buttons)
        
        if default_button:
            msg_box.setDefaultButton(default_button)
        
        if detailed_text:
            msg_box.setDetailedText(detailed_text)
        
        return msg_box.exec()


# ==================== Convenience Functions ====================
# These provide shorthand access for common operations

def error(parent: QWidget | None, message: str, title: str | None = None) -> None:
    """Shorthand for DialogHelper.show_error()"""
    DialogHelper.show_error(parent, message, title)


def warning(parent: QWidget | None, message: str, title: str | None = None) -> None:
    """Shorthand for DialogHelper.show_warning()"""
    DialogHelper.show_warning(parent, message, title)


def info(parent: QWidget | None, message: str, title: str | None = None) -> None:
    """Shorthand for DialogHelper.show_info()"""
    DialogHelper.show_info(parent, message, title)


def success(parent: QWidget | None, message: str, title: str | None = None) -> None:
    """Shorthand for DialogHelper.show_success()"""
    DialogHelper.show_success(parent, message, title)


def confirm(parent: QWidget | None, message: str, title: str | None = None) -> bool:
    """Shorthand for DialogHelper.confirm()"""
    return DialogHelper.confirm(parent, message, title)


# ==================== Module Exports ====================

__all__: list[str] = [
    'DialogResult',
    'DialogHelper',
    # Convenience functions
    'error',
    'warning', 
    'info',
    'success',
    'confirm',
]