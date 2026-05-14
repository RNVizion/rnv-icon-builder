"""
RNV Icon Builder - Context Preview Module
Provides icon-in-context preview functionality showing how icons
will appear in various UI contexts.

Features:
- Windows taskbar preview (light and dark)
- Windows Explorer folder view
- macOS Dock preview
- Browser favicon in tab
- Desktop shortcut preview
"""

from __future__ import annotations

import io
from typing import Any

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QWidget, QSizePolicy, QPushButton, QTabWidget, QGridLayout
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QPen, QBrush

from PIL import Image

from utils.config import (
    CONTEXT_PREVIEW_TASKBAR_SIZE, CONTEXT_PREVIEW_FOLDER_SIZE,
    CONTEXT_PREVIEW_DESKTOP_SIZE, CONTEXT_PREVIEW_DOCK_SIZE,
    CONTEXT_PREVIEW_FAVICON_SIZE
)
from utils.logger import Logger, get_logger_instance
from ui.base_dialog import BaseDialog
from ui.colors import BRAND_GOLD, BRAND_GOLD_DARK, OS_SIM_COLORS, get_theme_colors
from ui.preview_utils import pil_to_qpixmap, composite_on_checkerboard

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)


class ContextPreviewDialog(BaseDialog):
    """
    Dialog showing icon previews in various context environments.
    
    Provides visual representation of how the icon will look in:
    - Windows taskbar (dark and light themes)
    - Windows Explorer folder view
    - macOS Dock
    - Browser tab as favicon
    - Desktop shortcut
    
    Example:
        >>> dialog = ContextPreviewDialog(icon_images, parent)
        >>> dialog.exec()
    """
    
    def __init__(
        self,
        images: dict[int, Image.Image],
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize the context preview dialog.
        
        Args:
            images: Dictionary mapping sizes to PIL Images
            parent: Parent widget
        """
        super().__init__(
            parent=parent,
            title="Icon in Context Preview",
            modal=True,
            fixed_size=(600, 500)
        )
        
        # Ensure Qt deletes the C++ object when dialog is closed
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self.images = images
        
        self._setup_ui()
        self._apply_theme(is_dark=self._is_dark_theme())
        
        logger.debug(f"Context preview dialog opened with {len(images)} images")
    
    def closeEvent(self, event) -> None:
        """Handle dialog close with image reference cleanup."""
        # Release image references
        self.images = None
        
        logger.debug("Context Preview dialog closed")
        super().closeEvent(event)
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Tab widget for different contexts
        self.tabs = QTabWidget()
        
        # Create context tabs
        self.tabs.addTab(self._create_windows_tab(), "Windows")
        self.tabs.addTab(self._create_macos_tab(), "macOS")
        self.tabs.addTab(self._create_browser_tab(), "Browser")
        self.tabs.addTab(self._create_desktop_tab(), "Desktop")
        
        layout.addWidget(self.tabs)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setToolTip("Close this dialog (Esc)")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
    
    def _get_icon_at_size(self, size: int) -> Image.Image | None:
        """Get icon image at specified size, or closest available."""
        if size in self.images:
            return self.images[size]
        
        # Find closest size
        available = sorted(self.images.keys(), reverse=True)
        for s in available:
            if s >= size:
                img = self.images[s]
                return img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Use smallest available and scale up
        if available:
            img = self.images[available[-1]]
            return img.resize((size, size), Image.Resampling.LANCZOS)
        
        return None
    
    def _create_windows_tab(self) -> QWidget:
        """Create Windows context preview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Taskbar preview
        taskbar_group = QFrame()
        taskbar_group.setObjectName("context_group")
        taskbar_layout = QVBoxLayout(taskbar_group)
        
        # Dark taskbar
        taskbar_layout.addWidget(QLabel("Taskbar (Dark):"))
        dark_taskbar = self._create_taskbar_preview(dark=True)
        taskbar_layout.addWidget(dark_taskbar)
        
        # Light taskbar
        taskbar_layout.addWidget(QLabel("Taskbar (Light):"))
        light_taskbar = self._create_taskbar_preview(dark=False)
        taskbar_layout.addWidget(light_taskbar)
        
        layout.addWidget(taskbar_group)
        
        # Explorer preview
        explorer_group = QFrame()
        explorer_group.setObjectName("context_group")
        explorer_layout = QVBoxLayout(explorer_group)
        explorer_layout.addWidget(QLabel("File Explorer:"))
        explorer = self._create_explorer_preview()
        explorer_layout.addWidget(explorer)
        
        layout.addWidget(explorer_group)
        layout.addStretch()
        
        return widget
    
    def _create_taskbar_preview(self, dark: bool = True) -> QFrame:
        """Create a Windows taskbar mockup.

        NOTE: Colors in this method and all other _create_*_preview methods
        are intentional OS simulation values — they replicate real operating
        system chrome (Windows taskbar, macOS Dock/Finder, Chrome browser UI)
        and must NOT follow the application theme. All values are sourced
        from OS_SIM_COLORS in colors.py.
        """
        frame = QFrame()
        frame.setFixedHeight(48)
        
        bg_color = OS_SIM_COLORS['taskbar_dark_bg'] if dark else OS_SIM_COLORS['taskbar_light_bg']
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {OS_SIM_COLORS['taskbar_border']};
                border-radius: 0px;
            }}
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        
        # Start button placeholder
        start = QLabel("⊞")
        start.setStyleSheet(f"color: {OS_SIM_COLORS['taskbar_text_dark'] if dark else OS_SIM_COLORS['taskbar_text_light']}; font-size: 20px;")
        layout.addWidget(start)
        
        # Add icon
        icon_img = self._get_icon_at_size(CONTEXT_PREVIEW_TASKBAR_SIZE)
        if icon_img:
            icon_label = QLabel()
            # Composite on appropriate background
            bg = (32, 32, 32) if dark else (240, 240, 240)
            from ui.preview_utils import composite_on_color
            display = composite_on_color(icon_img, bg)
            pixmap = pil_to_qpixmap(display)
            icon_label.setPixmap(pixmap.scaled(
                CONTEXT_PREVIEW_TASKBAR_SIZE, CONTEXT_PREVIEW_TASKBAR_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            layout.addWidget(icon_label)
        
        # Other taskbar icons (placeholders)
        for _ in range(3):
            placeholder = QLabel("📁")
            placeholder.setStyleSheet(f"color: {OS_SIM_COLORS['taskbar_text_muted_dark'] if dark else OS_SIM_COLORS['taskbar_text_muted_light']}; font-size: 16px;")
            layout.addWidget(placeholder)
        
        layout.addStretch()
        
        # System tray area
        time_label = QLabel("12:34 PM")
        time_label.setStyleSheet(f"color: {OS_SIM_COLORS['taskbar_text_dark'] if dark else OS_SIM_COLORS['taskbar_text_light']}; font-size: 11px;")
        layout.addWidget(time_label)
        
        return frame
    
    def _create_explorer_preview(self) -> QFrame:
        """Create a Windows Explorer folder view mockup.

        NOTE: Colors here are intentional OS simulation values replicating
        Windows Explorer chrome. Do not migrate to colors.py or get_theme_colors().
        All values are sourced from OS_SIM_COLORS in colors.py.
        """
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {OS_SIM_COLORS['explorer_bg']};
                border: 1px solid {OS_SIM_COLORS['explorer_border']};
            }}
        """)
        frame.setFixedHeight(100)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(30)
        
        # Add icons in folder view style
        sizes = [48, 48, 48]  # Three folder-style icons
        for i, size in enumerate(sizes):
            item_frame = QVBoxLayout()
            item_frame.setSpacing(5)
            
            icon_img = self._get_icon_at_size(size)
            if icon_img:
                icon_label = QLabel()
                # White background for explorer
                from ui.preview_utils import composite_on_color
                display = composite_on_color(icon_img, (255, 255, 255))
                pixmap = pil_to_qpixmap(display)
                icon_label.setPixmap(pixmap)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                item_frame.addWidget(icon_label)
            
            # Filename
            name = QLabel(f"MyApp_{i+1}.exe" if i == 0 else f"file{i+1}.txt")
            name.setStyleSheet(f"color: {OS_SIM_COLORS['explorer_text']}; font-size: 10px;")
            name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            item_frame.addWidget(name)
            
            container = QWidget()
            container.setLayout(item_frame)
            layout.addWidget(container)
        
        layout.addStretch()
        return frame
    
    def _create_macos_tab(self) -> QWidget:
        """Create macOS context preview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Dock preview
        dock_group = QFrame()
        dock_group.setObjectName("context_group")
        dock_layout = QVBoxLayout(dock_group)
        dock_layout.addWidget(QLabel("Dock:"))
        dock = self._create_dock_preview()
        dock_layout.addWidget(dock)
        
        layout.addWidget(dock_group)
        
        # Finder preview
        finder_group = QFrame()
        finder_group.setObjectName("context_group")
        finder_layout = QVBoxLayout(finder_group)
        finder_layout.addWidget(QLabel("Finder:"))
        finder = self._create_finder_preview()
        finder_layout.addWidget(finder)
        
        layout.addWidget(finder_group)
        layout.addStretch()
        
        return widget
    
    def _create_dock_preview(self) -> QFrame:
        """Create a macOS Dock mockup.

        NOTE: Colors here are intentional OS simulation values replicating
        the macOS Dock glass appearance. Do not migrate to colors.py or get_theme_colors().
        All values are sourced from OS_SIM_COLORS in colors.py.
        """
        frame = QFrame()
        frame.setFixedHeight(80)
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {OS_SIM_COLORS['dock_gradient_start']}, stop:1 {OS_SIM_COLORS['dock_gradient_end']});
                border: 1px solid {OS_SIM_COLORS['dock_border']};
                border-radius: 15px;
            }}
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)
        
        layout.addStretch()
        
        # Placeholder app icons
        placeholders = ["🎵", "📧", "🌐"]
        for emoji in placeholders:
            lbl = QLabel(emoji)
            lbl.setStyleSheet("font-size: 32px;")
            layout.addWidget(lbl)
        
        # Our icon
        icon_img = self._get_icon_at_size(CONTEXT_PREVIEW_DOCK_SIZE)
        if icon_img:
            icon_label = QLabel()
            display = composite_on_checkerboard(icon_img)
            pixmap = pil_to_qpixmap(display)
            icon_label.setPixmap(pixmap.scaled(
                CONTEXT_PREVIEW_DOCK_SIZE, CONTEXT_PREVIEW_DOCK_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            layout.addWidget(icon_label)
        
        # More placeholders
        for emoji in ["📁", "⚙️"]:
            lbl = QLabel(emoji)
            lbl.setStyleSheet("font-size: 32px;")
            layout.addWidget(lbl)
        
        layout.addStretch()
        
        return frame
    
    def _create_finder_preview(self) -> QFrame:
        """Create a macOS Finder window mockup.

        NOTE: Colors here are intentional OS simulation values replicating
        macOS Finder chrome. Do not migrate to colors.py or get_theme_colors().
        All values are sourced from OS_SIM_COLORS in colors.py.
        """
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {OS_SIM_COLORS['finder_bg']};
                border: 1px solid {OS_SIM_COLORS['finder_border']};
                border-radius: 6px;
            }}
        """)
        frame.setFixedHeight(100)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(25)
        
        # Icons in grid view
        icon_img = self._get_icon_at_size(48)
        if icon_img:
            for i in range(3):
                item_layout = QVBoxLayout()
                item_layout.setSpacing(3)
                
                icon_label = QLabel()
                from ui.preview_utils import composite_on_color
                display = composite_on_color(icon_img, (245, 245, 245))
                pixmap = pil_to_qpixmap(display)
                icon_label.setPixmap(pixmap)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                item_layout.addWidget(icon_label)
                
                name = QLabel(f"App{i+1}" if i == 0 else f"Document{i}")
                name.setStyleSheet(f"color: {OS_SIM_COLORS['finder_text']}; font-size: 10px;")
                name.setAlignment(Qt.AlignmentFlag.AlignCenter)
                item_layout.addWidget(name)
                
                container = QWidget()
                container.setLayout(item_layout)
                layout.addWidget(container)
        
        layout.addStretch()
        return frame
    
    def _create_browser_tab(self) -> QWidget:
        """Create browser context preview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Chrome-style tab bar
        chrome_group = QFrame()
        chrome_group.setObjectName("context_group")
        chrome_layout = QVBoxLayout(chrome_group)
        chrome_layout.addWidget(QLabel("Browser Tab (Chrome-style):"))
        chrome = self._create_browser_tabs_preview(style="chrome")
        chrome_layout.addWidget(chrome)
        
        layout.addWidget(chrome_group)
        
        # Firefox-style bookmark bar
        bookmark_group = QFrame()
        bookmark_group.setObjectName("context_group")
        bookmark_layout = QVBoxLayout(bookmark_group)
        bookmark_layout.addWidget(QLabel("Bookmarks Bar:"))
        bookmarks = self._create_bookmarks_preview()
        bookmark_layout.addWidget(bookmarks)
        
        layout.addWidget(bookmark_group)
        layout.addStretch()
        
        return widget
    
    def _create_browser_tabs_preview(self, style: str = "chrome") -> QFrame:
        """Create browser tabs mockup.

        NOTE: Colors here are intentional OS simulation values replicating
        Chrome browser UI chrome. Do not migrate to colors.py or get_theme_colors().
        All values are sourced from OS_SIM_COLORS in colors.py.
        """
        frame = QFrame()
        frame.setFixedHeight(40)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {OS_SIM_COLORS['chrome_tabbar_bg']};
                border: none;
                border-radius: 0px;
            }}
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 0)
        layout.setSpacing(2)
        
        # Tab with our favicon
        tab1 = QFrame()
        tab1.setStyleSheet(f"""
            QFrame {{
                background-color: {OS_SIM_COLORS['chrome_active_tab_bg']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)
        tab1.setFixedSize(200, 30)
        
        tab1_layout = QHBoxLayout(tab1)
        tab1_layout.setContentsMargins(8, 3, 8, 3)
        tab1_layout.setSpacing(6)
        
        icon_img = self._get_icon_at_size(CONTEXT_PREVIEW_FAVICON_SIZE)
        if icon_img:
            icon_label = QLabel()
            from ui.preview_utils import composite_on_color
            display = composite_on_color(icon_img, (255, 255, 255))
            pixmap = pil_to_qpixmap(display)
            icon_label.setPixmap(pixmap)
            tab1_layout.addWidget(icon_label)
        
        title = QLabel("My Application")
        title.setStyleSheet(f"color: {OS_SIM_COLORS['chrome_tab_title']}; font-size: 11px;")
        tab1_layout.addWidget(title)
        tab1_layout.addStretch()
        
        close = QLabel("×")
        close.setStyleSheet(f"color: {OS_SIM_COLORS['chrome_tab_close']}; font-size: 14px;")
        tab1_layout.addWidget(close)
        
        layout.addWidget(tab1)
        
        # Inactive tab
        tab2 = QFrame()
        tab2.setStyleSheet(f"""
            QFrame {{
                background-color: {OS_SIM_COLORS['chrome_inactive_tab_bg']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)
        tab2.setFixedSize(150, 30)
        
        tab2_layout = QHBoxLayout(tab2)
        tab2_layout.setContentsMargins(8, 3, 8, 3)
        
        globe = QLabel("🌐")
        globe.setStyleSheet("font-size: 12px;")
        tab2_layout.addWidget(globe)
        
        title2 = QLabel("New Tab")
        title2.setStyleSheet(f"color: {OS_SIM_COLORS['chrome_inactive_tab_text']}; font-size: 11px;")
        tab2_layout.addWidget(title2)
        tab2_layout.addStretch()
        
        layout.addWidget(tab2)
        layout.addStretch()
        
        return frame
    
    def _create_bookmarks_preview(self) -> QFrame:
        """Create bookmarks bar mockup.

        NOTE: Colors here are intentional OS simulation values replicating
        the browser bookmarks bar. Do not migrate to colors.py or get_theme_colors().
        All values are sourced from OS_SIM_COLORS in colors.py.
        """
        frame = QFrame()
        frame.setFixedHeight(32)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {OS_SIM_COLORS['bookmarks_bg']};
                border: 1px solid {OS_SIM_COLORS['bookmarks_border']};
            }}
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 3, 10, 3)
        layout.setSpacing(15)
        
        # Bookmark with our icon
        icon_img = self._get_icon_at_size(CONTEXT_PREVIEW_FAVICON_SIZE)
        if icon_img:
            item = QHBoxLayout()
            item.setSpacing(5)
            
            icon_label = QLabel()
            from ui.preview_utils import composite_on_color
            display = composite_on_color(icon_img, (248, 249, 250))
            pixmap = pil_to_qpixmap(display)
            icon_label.setPixmap(pixmap)
            item.addWidget(icon_label)
            
            name = QLabel("My App")
            name.setStyleSheet(f"color: {OS_SIM_COLORS['bookmarks_text']}; font-size: 11px;")
            item.addWidget(name)
            
            container = QWidget()
            container.setLayout(item)
            layout.addWidget(container)
        
        # Other bookmarks
        for text in ["📧 Gmail", "📺 YouTube", "📰 News"]:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {OS_SIM_COLORS['bookmarks_text']}; font-size: 11px;")
            layout.addWidget(lbl)
        
        layout.addStretch()
        return frame
    
    def _create_desktop_tab(self) -> QWidget:
        """Create desktop context preview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Desktop shortcut preview
        shortcut_group = QFrame()
        shortcut_group.setObjectName("context_group")
        shortcut_layout = QVBoxLayout(shortcut_group)
        shortcut_layout.addWidget(QLabel("Desktop Shortcut:"))
        shortcut = self._create_desktop_shortcut_preview()
        shortcut_layout.addWidget(shortcut)
        
        layout.addWidget(shortcut_group)
        
        # All sizes preview
        sizes_group = QFrame()
        sizes_group.setObjectName("context_group")
        sizes_layout = QVBoxLayout(sizes_group)
        sizes_layout.addWidget(QLabel("All Available Sizes:"))
        sizes = self._create_all_sizes_preview()
        sizes_layout.addWidget(sizes)
        
        layout.addWidget(sizes_group)
        layout.addStretch()
        
        return widget
    
    def _create_desktop_shortcut_preview(self) -> QFrame:
        """Create desktop shortcut mockup.

        NOTE: Colors here are intentional OS simulation values replicating
        a Windows desktop background and icon labels. Do not migrate to
        colors.py or get_theme_colors(). All values are sourced from
        OS_SIM_COLORS in colors.py.
        """
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {OS_SIM_COLORS['desktop_gradient_start']}, stop:1 {OS_SIM_COLORS['desktop_gradient_end']});
                border: none;
                border-radius: 4px;
            }}
        """)
        frame.setFixedHeight(120)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(40)
        
        # Desktop icons
        icon_img = self._get_icon_at_size(CONTEXT_PREVIEW_DESKTOP_SIZE)
        if icon_img:
            for i, name in enumerate(["My App", "Recycle Bin", "Documents"]):
                item_layout = QVBoxLayout()
                item_layout.setSpacing(5)
                
                icon_label = QLabel()
                if i == 0 and icon_img:
                    display = composite_on_checkerboard(icon_img)
                    pixmap = pil_to_qpixmap(display)
                    icon_label.setPixmap(pixmap.scaled(
                        CONTEXT_PREVIEW_DESKTOP_SIZE, CONTEXT_PREVIEW_DESKTOP_SIZE,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
                else:
                    icon_label.setText("📁" if i == 2 else "🗑️")
                    icon_label.setStyleSheet("font-size: 40px;")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                item_layout.addWidget(icon_label)
                
                name_label = QLabel(name)
                name_label.setStyleSheet(f"""
                    color: {OS_SIM_COLORS['desktop_icon_text']};
                    font-size: 11px;
                    background-color: {OS_SIM_COLORS['desktop_icon_label_bg']};
                    padding: 2px 5px;
                    border-radius: 2px;
                """)
                name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                item_layout.addWidget(name_label)
                
                container = QWidget()
                container.setLayout(item_layout)
                layout.addWidget(container)
        
        layout.addStretch()
        return frame
    
    def _create_all_sizes_preview(self) -> QFrame:
        """Create preview showing all available icon sizes."""
        frame = QFrame()
        frame.setObjectName("sizes_frame")
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Sort sizes descending
        sizes = sorted(self.images.keys(), reverse=True)
        
        for size in sizes:
            item_layout = QVBoxLayout()
            item_layout.setSpacing(5)
            
            icon_img = self.images[size]
            display = composite_on_checkerboard(icon_img)
            pixmap = pil_to_qpixmap(display)
            
            icon_label = QLabel()
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("background-color: transparent;")
            item_layout.addWidget(icon_label)
            
            size_label = QLabel(f"{size}×{size}")
            size_label.setObjectName("size_info_label")
            size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            item_layout.addWidget(size_label)
            
            container = QWidget()
            container.setLayout(item_layout)
            layout.addWidget(container)
        
        layout.addStretch()
        return frame
    
    def _apply_theme(self, is_dark: bool = True) -> None:
        """Apply theme styling to dialog.
        
        Args:
            is_dark: Whether to apply dark theme (True) or light theme (False)
        """
        colors = get_theme_colors(is_dark=is_dark)
        accent = BRAND_GOLD if is_dark else BRAND_GOLD_DARK
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['dialog_bg']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
            QPushButton {{
                background-color: {colors['button_bg']};
                color: {colors['button_text']};
                border: 1px solid {colors['button_border']};
                border-radius: 4px;
                padding: 6px 15px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover_bg']};
                color: {colors['button_hover_text']};
                border-color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {accent};
                color: {colors['button_pressed_text']};
            }}
            QTabWidget::pane {{
                border: 1px solid {colors['border_default']};
                background-color: {colors['dialog_bg']};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: {colors['tab_bg']};
                color: {colors['text_secondary']};
                padding: 8px 15px;
                border: 1px solid {colors['border_default']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {colors['dialog_bg']};
                color: {accent};
                border-bottom: 2px solid {accent};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {colors['tab_hover_bg']};
            }}
            QFrame[objectName="context_group"] {{
                background-color: {colors['tab_bg']};
                border: 1px solid {colors['border_hover']};
                border-radius: 4px;
            }}
            QFrame[objectName="sizes_frame"] {{
                background-color: {colors['dialog_bg']};
                border: 1px solid {colors['border_hover']};
                border-radius: 4px;
            }}
            QLabel[objectName="size_info_label"] {{
                color: {colors['text_muted']};
                font-size: 10px;
            }}
        """)
    
    def apply_theme_from_manager(self, theme_name: str) -> None:
        """
        Apply theme from theme manager.
        
        Args:
            theme_name: 'dark', 'light', or 'image'
        """
        is_dark = theme_name != 'light'
        self._apply_theme(is_dark=is_dark)


# ==================== Module Exports ====================

__all__: list[str] = [
    'ContextPreviewDialog',
]