"""
RNV Icon Builder - About Dialog
Application Information and Help accessible via Ctrl+/ keyboard shortcut

Displays:
- Application name, version, description
- Feature list
- Keyboard shortcuts reference
- System information
- Credits
"""

from __future__ import annotations

import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ui.base_dialog import BaseDialog

# Import logger
from utils.logger import Logger, get_logger_instance
from ui.colors import BRAND_GOLD, get_theme_colors
logger: Logger = get_logger_instance("AboutDialog")

# Import config for app info
try:
    from utils import config
except ImportError:
    config = None  # type: ignore[assignment]


class AboutDialog(BaseDialog):
    """
    About dialog with application information, features, and keyboard shortcuts.
    
    Displays application metadata, feature overview, keyboard shortcuts reference,
    and credits in a tabbed interface. Accessible via Ctrl+/ shortcut.
    
    Attributes:
        tabs: QTabWidget containing About, Features, Shortcuts, and Credits tabs
        
    Example:
        >>> dialog = AboutDialog(parent=main_window, is_dark=True)
        >>> dialog.exec()
    """
    
    def __init__(self, parent: QWidget | None = None, is_dark: bool = True) -> None:
        """
        Initialize the About dialog.
        
        Args:
            parent: Parent widget (not used to avoid stylesheet inheritance)
            is_dark: Whether to use dark theme
        """
        # Don't pass parent to avoid stylesheet inheritance issues
        super().__init__(
            parent=None,
            title="About RNV Icon Builder",
            modal=True,
            fixed_size=(520, 700)
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self._is_dark: bool = is_dark
        
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.MSWindowsFixedSizeDialogHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._build_ui()
        self._apply_theme()
        
        logger.info("About dialog initialized")
    
    def _build_ui(self) -> None:
        """
        Build the about dialog UI.
        
        Creates the dialog layout with header section and tabbed content area
        containing About, Features, Shortcuts, and Credits tabs.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header section with app name and version
        header = self._create_header()
        layout.addWidget(header)
        
        # Tab widget for organized content
        self.tabs = QTabWidget()
        
        # Create tabs
        about_tab = self._create_about_tab()
        features_tab = self._create_features_tab()
        shortcuts_tab = self._create_shortcuts_tab()
        credits_tab = self._create_credits_tab()
        
        self.tabs.addTab(about_tab, "About")
        self.tabs.addTab(features_tab, "Features")
        self.tabs.addTab(shortcuts_tab, "Shortcuts")
        self.tabs.addTab(credits_tab, "Credits")
        
        layout.addWidget(self.tabs, 1)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setToolTip("Close this dialog (Esc)")
        close_btn.setFixedSize(100, 35)
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_header(self) -> QWidget:
        """
        Create the header section with app name and logo.
        
        Returns:
            QFrame containing app icon, name, version, and description
        """
        header = QFrame()
        header.setObjectName("header_frame")
        header.setFrameShape(QFrame.Shape.NoFrame)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        # App icon (if available)
        icon_label = QLabel()
        icon_label.setStyleSheet("border: none; background: transparent;")
        if config:
            icon_path = os.path.join(config.BASE_DIR, "resources", "icons", "icon.png")
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        64, 64, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    icon_label.setPixmap(scaled_pixmap)
        icon_label.setFixedSize(70, 70)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # App name and version
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        app_info = self._get_app_info()
        
        name_label = QLabel(app_info['name'])
        name_label.setStyleSheet("font-size: 24px; font-weight: bold; border: none; background: transparent;")
        text_layout.addWidget(name_label)
        
        version_label = QLabel(f"Version {app_info['version']}")
        version_label.setStyleSheet(f"font-size: 14px; color: {BRAND_GOLD}; border: none; background: transparent;")
        text_layout.addWidget(version_label)
        
        desc_label = QLabel(app_info['description'])
        desc_label.setStyleSheet("font-size: 12px; border: none; background: transparent;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)
        
        text_layout.addStretch()
        header_layout.addLayout(text_layout, 1)
        
        return header
    
    def _create_about_tab(self) -> QWidget:
        """
        Create the About tab with application description.
        
        Returns:
            QWidget containing application overview and system information
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Description
        desc_text = """
<h3>Professional Multi-Resolution ICO Builder</h3>

<p>RNV Icon Builder is a desktop application for creating professional multi-resolution 
ICO files from PNG, ICO, and SVG source images. It provides comprehensive tools for 
image manipulation, multiple export formats, and workflow automation.</p>

<h4>Core Capabilities:</h4>
<ul>
<li><b>Multi-Resolution ICO</b> - Create ICO files with all standard sizes (16-256px)</li>
<li><b>PNG Compression</b> - Optimized compression for smaller file sizes</li>
<li><b>Multiple Source Formats</b> - Support for PNG, ICO, and SVG inputs</li>
<li><b>Platform Export</b> - Export for Windows, macOS, iOS, Android, and Web</li>
<li><b>Batch Processing</b> - Process multiple files in a queue</li>
<li><b>Image Adjustments</b> - Rotate, flip, crop, resize, and color corrections</li>
<li><b>Session Management</b> - Auto-save and crash recovery</li>
</ul>

<h4>System Information:</h4>
"""
        
        # Add system info
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        try:
            from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
            qt_version = QT_VERSION_STR
            pyqt_version = PYQT_VERSION_STR
        except ImportError:
            qt_version = "Unknown"
            pyqt_version = "Unknown"
        
        desc_text += f"""
<table>
<tr><td><b>Python:</b></td><td>{python_version}</td></tr>
<tr><td><b>PyQt6:</b></td><td>{pyqt_version}</td></tr>
<tr><td><b>Qt:</b></td><td>{qt_version}</td></tr>
<tr><td><b>Platform:</b></td><td>{sys.platform}</td></tr>
</table>
"""
        
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setTextFormat(Qt.TextFormat.RichText)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(desc_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _create_features_tab(self) -> QWidget:
        """
        Create the Features tab with feature list.
        
        Returns:
            QWidget containing categorized feature overview
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        features_text = """
<h3>Feature Overview</h3>

<h4>🖼️ ICO File Creation</h4>
<ul>
<li><b>Multi-Resolution Support</b> - Standard sizes: 256, 128, 64, 48, 32, 16px</li>
<li><b>PNG Compression</b> - Smaller files with PNG for large sizes</li>
<li><b>Autofill Sizes</b> - Automatically generate missing smaller sizes</li>
<li><b>Smart Detection</b> - Auto-detect image sizes from filenames</li>
</ul>

<h4>🖌️ Image Adjustments</h4>
<ul>
<li><b>Transform</b> - Rotate 90°, flip horizontal/vertical</li>
<li><b>Crop & Resize</b> - Auto-crop, add padding, center resize</li>
<li><b>Borders</b> - Add colored borders with custom width</li>
<li><b>Color Adjustments</b> - Brightness, contrast, saturation, grayscale</li>
<li><b>Undo/Redo</b> - Full history for each size slot</li>
</ul>

<h4>📤 Export Formats</h4>
<ul>
<li><b>Windows ICO</b> - Multi-resolution icon files</li>
<li><b>macOS ICNS</b> - Apple icon format with Retina support</li>
<li><b>PNG Set</b> - Individual PNG files for each size</li>
<li><b>Favicon Package</b> - Complete web favicon set with manifest</li>
<li><b>Android Icons</b> - mipmap folders (mdpi to xxxhdpi)</li>
<li><b>iOS App Icons</b> - Complete Assets.xcassets structure</li>
</ul>

<h4>⚙️ Workflow Automation</h4>
<ul>
<li><b>Batch Processing</b> - Queue multiple files for processing</li>
<li><b>Folder Watching</b> - Auto-process new files in a folder</li>
<li><b>Size Presets</b> - Save and load size configurations</li>
<li><b>Project Files</b> - Save complete application state</li>
</ul>

<h4>🔍 Preview & Analysis</h4>
<ul>
<li><b>Live Preview</b> - See all sizes with zoom and backgrounds</li>
<li><b>Context Preview</b> - View icons in OS context mockups</li>
<li><b>ICO Analyzer</b> - Examine existing ICO file structure</li>
<li><b>Color Palette</b> - Extract dominant colors from images</li>
</ul>

<h4>💾 Session & History</h4>
<ul>
<li><b>Auto-Save</b> - Periodic session backup every 5 minutes</li>
<li><b>Crash Recovery</b> - Restore sessions after unexpected close</li>
<li><b>Export History</b> - Track all export operations</li>
<li><b>Compression Stats</b> - View file size savings</li>
</ul>
"""
        
        features_label = QLabel(features_text)
        features_label.setWordWrap(True)
        features_label.setTextFormat(Qt.TextFormat.RichText)
        features_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(features_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _create_shortcuts_tab(self) -> QWidget:
        """
        Create the Shortcuts tab with keyboard shortcuts.
        
        Returns:
            QWidget containing keyboard shortcuts reference tables
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        shortcuts_text = """
<h3>Keyboard Shortcuts</h3>

<h4>File Operations</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+O</b></td><td>Open/Upload Images</td></tr>
<tr><td><b>Ctrl+Shift+O</b></td><td>Open Folder</td></tr>
<tr><td><b>Ctrl+N</b></td><td>Clear All Files</td></tr>
<tr><td><b>Ctrl+B</b></td><td>Build ICO File</td></tr>
</table>

<h4>Project Management</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+S</b></td><td>Save Project</td></tr>
<tr><td><b>Ctrl+Shift+S</b></td><td>Save Project As</td></tr>
<tr><td><b>Ctrl+Shift+N</b></td><td>New Project</td></tr>
</table>

<h4>Application</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+,</b></td><td>Open Settings Panel</td></tr>
<tr><td><b>Ctrl+/</b></td><td>Open About Dialog (This Window)</td></tr>
<tr><td><b>Ctrl+T</b></td><td>Cycle Theme (Dark → Light → Image)</td></tr>
</table>

<h4>Display & Debug</h4>
<table width="100%">
<tr><td width="40%"><b>F5</b></td><td>Refresh Preview</td></tr>
<tr><td><b>F11</b></td><td>Toggle Tooltips On/Off</td></tr>
<tr><td><b>Escape</b></td><td>Clear Selection</td></tr>
</table>

<h4>Preview Navigation</h4>
<table width="100%">
<tr><td width="40%"><b>Single Click</b></td><td>Select Size for Adjustments</td></tr>
<tr><td><b>Double Click</b></td><td>Open Full Preview Dialog</td></tr>
<tr><td><b>Hover</b></td><td>Show Enlarged Thumbnail</td></tr>
</table>

<h4>Drag & Drop</h4>
<table width="100%">
<tr><td width="40%"><b>Drop Files</b></td><td>Load PNG/ICO/SVG Images</td></tr>
<tr><td><b>Drop Folder</b></td><td>Scan Folder for Images</td></tr>
</table>
"""
        
        shortcuts_label = QLabel(shortcuts_text)
        shortcuts_label.setWordWrap(True)
        shortcuts_label.setTextFormat(Qt.TextFormat.RichText)
        shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(shortcuts_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _create_credits_tab(self) -> QWidget:
        """
        Create the Credits tab with acknowledgments.
        
        Returns:
            QWidget containing credits and acknowledgments
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        credits_text = f"""
<h3>Credits & Acknowledgments</h3>

<h4>Development</h4>
<p>RNV Icon Builder was created with passion for helping developers and designers 
create professional icon assets efficiently.</p>

<h4>Technologies</h4>
<table width="100%">
<tr><td width="40%"><b>Framework:</b></td><td>PyQt6</td></tr>
<tr><td><b>Language:</b></td><td>Python 3</td></tr>
<tr><td><b>Image Processing:</b></td><td>Pillow (PIL)</td></tr>
<tr><td><b>ICO Format:</b></td><td>Custom Implementation</td></tr>
</table>

<h4>ICO Format Reference</h4>
<ul>
<li>Microsoft ICO file format specification</li>
<li>PNG compression within ICO (Vista+)</li>
<li>BMP format for legacy compatibility</li>
</ul>

<h4>Platform Icon Guidelines</h4>
<ul>
<li>Microsoft Windows Icon Guidelines</li>
<li>Apple Human Interface Guidelines (macOS, iOS)</li>
<li>Google Material Design (Android)</li>
<li>Favicon Best Practices (Web)</li>
</ul>

<h4>Special Thanks</h4>
<ul>
<li>The PyQt community for excellent documentation</li>
<li>Pillow maintainers for image processing support</li>
<li>Beta testers and early adopters</li>
<li>Everyone who provided feedback and suggestions</li>
</ul>

<hr>

<p style="text-align: center; color: {BRAND_GOLD};">
<b>RNV Icon Builder</b><br>
Crafted pixel by pixel for developers and designers<br>
<small>© 2026 RNV · MIT Licensed · Part of the RNVizion toolkit</small>
</p>
"""
        
        credits_label = QLabel(credits_text)
        credits_label.setWordWrap(True)
        credits_label.setTextFormat(Qt.TextFormat.RichText)
        credits_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(credits_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _get_app_info(self) -> dict[str, str]:
        """
        Get application information from config or defaults.
        
        Returns:
            Dictionary containing name, version, description, author, and framework
        """
        version = getattr(config, 'APP_VERSION', '?') if config else '?'
        app_name = getattr(config, 'APP_NAME', 'RNV Icon Builder') if config else 'RNV Icon Builder'
        
        return {
            "name": app_name,
            "version": version,
            "description": "Professional Multi-Resolution ICO Builder",
            "author": "RNV",
            "framework": "PyQt6"
        }
    
    def set_theme(self, is_dark: bool) -> None:
        """
        Set the dialog theme (dark or light).
        
        Args:
            is_dark: Whether to use dark theme
        """
        self._is_dark = is_dark
        self._apply_theme()
    
    def _apply_theme(self) -> None:
        """Apply the current theme to the dialog."""
        c = get_theme_colors(is_dark=self._is_dark)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c['window_bg']};
                color: {c['text_primary']};
            }}
            QFrame {{
                background-color: {c['card_bg']};
                border: 1px solid {c['border_default']};
                border-radius: 8px;
            }}
            QFrame#header_frame {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }}
            QTabWidget::pane {{
                background-color: {c['panel_bg']};
                border: 1px solid {c['border_default']};
                border-radius: 4px;
                padding: 5px;
            }}
            QTabBar::tab {{
                background-color: {c['tab_bg']};
                color: {c['text_primary']};
                padding: 8px 16px;
                border: 1px solid {c['border_default']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {c['tab_selected_bg']};
                color: {c['text_accent']};
                border-bottom: 2px solid {c['tab_indicator']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {c['tab_hover_bg']};
                color: {c['text_accent']};
            }}
            QLabel {{
                color: {c['text_primary']};
                background-color: transparent;
                border: none;
            }}
            QScrollArea {{
                background-color: {c['panel_bg']};
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {c['panel_bg']};
            }}
            QScrollBar:vertical {{
                background-color: {c['scrollbar_bg']};
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {c['scrollbar_handle']};
                border-radius: 5px;
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {c['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background-color: transparent;
            }}
            QPushButton {{
                background-color: {c['button_bg']};
                color: {c['button_text']};
                border: 1px solid {c['button_border']};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c['button_hover_bg']};
                border-color: {c['border_focus']};
                color: {c['button_hover_text']};
            }}
            QPushButton:pressed {{
                background-color: {c['button_pressed_bg']};
                color: {c['button_pressed_text']};
            }}
        """)
    
    def cleanup(self) -> None:
        """Clean up resources before deletion."""
        try:
            # Clear any pixmaps to free memory
            for child in self.findChildren(QLabel):
                if child.pixmap() and not child.pixmap().isNull():
                    child.clear()
            
            logger.debug("AboutDialog cleanup complete")
                
        except Exception as e:
            logger.error(f"Error during AboutDialog cleanup: {e}")
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle dialog close - ensure cleanup runs.
        
        Args:
            event: Close event from Qt
        """
        self.cleanup()
        # BaseDialog.closeEvent handles signal disconnection and move handler cleanup
        super().closeEvent(event)


# Module exports
__all__: list[str] = ['AboutDialog']