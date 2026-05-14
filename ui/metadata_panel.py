"""
RNV Icon Builder - Metadata Panel Module
Displays detailed metadata about loaded images.

Features:
- File path and name
- Dimensions and aspect ratio
- Color mode and bit depth
- File size
- Format-specific details
- DPI information (if available)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QGroupBox, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from PIL import Image

from ui.colors import BRAND_GOLD, get_theme_colors
from utils.logger import Logger, get_logger_instance

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)


class MetadataPanel(QFrame):
    """
    Panel displaying image metadata information.
    
    Shows detailed information about the currently selected image
    including file details, dimensions, color mode, and format-specific
    metadata.
    
    Signals:
        metadata_updated: Emitted when metadata is updated
        
    Example:
        >>> panel = MetadataPanel()
        >>> panel.set_image(pil_image, "/path/to/image.png")
    """
    
    metadata_updated = pyqtSignal()
    
    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the metadata panel."""
        super().__init__(parent)
        
        self._current_image: Image.Image | None = None
        self._current_path: str | None = None
        
        self._setup_ui()
        self._apply_theme()
        
        logger.debug("Metadata panel initialized")
    
    def _setup_ui(self) -> None:
        """Setup the panel UI."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Image Metadata")
        title.setObjectName("panel_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Scroll area for metadata content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        self.metadata_layout = QVBoxLayout(scroll_content)
        self.metadata_layout.setContentsMargins(0, 0, 0, 0)
        self.metadata_layout.setSpacing(10)
        
        # File Information Group
        self.file_group = self._create_group("File Information")
        self.file_grid = QGridLayout()
        self.file_grid.setSpacing(5)
        self.file_group.layout().addLayout(self.file_grid)
        self.metadata_layout.addWidget(self.file_group)
        
        # Image Properties Group
        self.image_group = self._create_group("Image Properties")
        self.image_grid = QGridLayout()
        self.image_grid.setSpacing(5)
        self.image_group.layout().addLayout(self.image_grid)
        self.metadata_layout.addWidget(self.image_group)
        
        # Format Details Group
        self.format_group = self._create_group("Format Details")
        self.format_grid = QGridLayout()
        self.format_grid.setSpacing(5)
        self.format_group.layout().addLayout(self.format_grid)
        self.metadata_layout.addWidget(self.format_group)
        
        self.metadata_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Initialize with empty state
        self._show_empty_state()
    
    def _create_group(self, title: str) -> QGroupBox:
        """Create a styled group box."""
        group = QGroupBox(title)
        group.setObjectName("metadata_group")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(5)
        return group
    
    def _add_metadata_row(
        self,
        grid: QGridLayout,
        row: int,
        label: str,
        value: str
    ) -> tuple[QLabel, QLabel]:
        """Add a label-value pair to a grid layout."""
        label_widget = QLabel(f"{label}:")
        label_widget.setObjectName("metadata_label")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        value_widget = QLabel(value)
        value_widget.setObjectName("metadata_value")
        value_widget.setWordWrap(True)
        value_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        grid.addWidget(label_widget, row, 0)
        grid.addWidget(value_widget, row, 1)
        
        return label_widget, value_widget
    
    def _clear_grid(self, grid: QGridLayout) -> None:
        """Remove all items from a grid layout."""
        while grid.count():
            item = grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _show_empty_state(self) -> None:
        """Show empty state when no image is loaded."""
        self._clear_grid(self.file_grid)
        self._clear_grid(self.image_grid)
        self._clear_grid(self.format_grid)
        
        self._add_metadata_row(self.file_grid, 0, "Status", "No image selected")
        
        self.image_group.hide()
        self.format_group.hide()
    
    def set_image(
        self,
        image: Image.Image | None,
        file_path: str | None = None,
        size_label: int | None = None
    ) -> None:
        """
        Set the image to display metadata for.
        
        Args:
            image: PIL Image object or None to clear
            file_path: Original file path (optional)
            size_label: Size label for this image (e.g., 256, 128)
        """
        self._current_image = image
        self._current_path = file_path
        
        if image is None:
            self._show_empty_state()
            return
        
        self._update_metadata(image, file_path, size_label)
        self.metadata_updated.emit()
    
    def _update_metadata(
        self,
        image: Image.Image,
        file_path: str | None,
        size_label: int | None
    ) -> None:
        """Update metadata display with image information."""
        # Clear existing content
        self._clear_grid(self.file_grid)
        self._clear_grid(self.image_grid)
        self._clear_grid(self.format_grid)
        
        row = 0
        
        # === File Information ===
        if file_path:
            path = Path(file_path)
            
            # Filename
            self._add_metadata_row(self.file_grid, row, "Name", path.name)
            row += 1
            
            # Directory (truncated if too long)
            dir_str = str(path.parent)
            if len(dir_str) > 40:
                dir_str = "..." + dir_str[-37:]
            self._add_metadata_row(self.file_grid, row, "Directory", dir_str)
            row += 1
            
            # File size
            if path.exists():
                size_bytes = path.stat().st_size
                size_str = self._format_size(size_bytes)
                self._add_metadata_row(self.file_grid, row, "File Size", size_str)
                row += 1
            
            # Format
            self._add_metadata_row(self.file_grid, row, "Format", path.suffix.upper().lstrip('.'))
            row += 1
        else:
            self._add_metadata_row(self.file_grid, row, "Source", "In-memory image")
            row += 1
        
        if size_label:
            self._add_metadata_row(self.file_grid, row, "Size Slot", f"{size_label}x{size_label}")
        
        # === Image Properties ===
        self.image_group.show()
        row = 0
        
        # Dimensions
        self._add_metadata_row(
            self.image_grid, row, "Dimensions",
            f"{image.width} × {image.height} px"
        )
        row += 1
        
        # Aspect ratio
        gcd = self._gcd(image.width, image.height)
        aspect_w = image.width // gcd
        aspect_h = image.height // gcd
        aspect_str = f"{aspect_w}:{aspect_h}"
        if image.width == image.height:
            aspect_str += " (Square)"
        self._add_metadata_row(self.image_grid, row, "Aspect Ratio", aspect_str)
        row += 1
        
        # Color mode
        mode_desc = self._get_mode_description(image.mode)
        self._add_metadata_row(self.image_grid, row, "Color Mode", mode_desc)
        row += 1
        
        # Bit depth
        bit_depth = self._get_bit_depth(image)
        self._add_metadata_row(self.image_grid, row, "Bit Depth", bit_depth)
        row += 1
        
        # Has transparency
        has_alpha = image.mode in ('RGBA', 'LA', 'PA') or 'transparency' in image.info
        self._add_metadata_row(
            self.image_grid, row, "Transparency",
            "Yes" if has_alpha else "No"
        )
        row += 1
        
        # Pixel count
        pixel_count = image.width * image.height
        self._add_metadata_row(
            self.image_grid, row, "Pixels",
            f"{pixel_count:,}"
        )
        row += 1
        
        # === Format Details ===
        format_details = self._get_format_details(image)
        
        if format_details:
            self.format_group.show()
            row = 0
            for key, value in format_details.items():
                self._add_metadata_row(self.format_grid, row, key, str(value))
                row += 1
        else:
            self.format_group.hide()
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable form."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                if unit == 'B':
                    return f"{size_bytes} {unit}"
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _gcd(self, a: int, b: int) -> int:
        """Calculate greatest common divisor."""
        while b:
            a, b = b, a % b
        return a
    
    def _get_mode_description(self, mode: str) -> str:
        """Get human-readable description of image mode."""
        mode_descriptions = {
            '1': "1-bit (Black & White)",
            'L': "8-bit Grayscale",
            'LA': "Grayscale + Alpha",
            'P': "8-bit Palette",
            'PA': "Palette + Alpha",
            'RGB': "24-bit RGB",
            'RGBA': "32-bit RGBA",
            'RGBX': "32-bit RGB (padded)",
            'CMYK': "32-bit CMYK",
            'YCbCr': "YCbCr",
            'LAB': "L*a*b*",
            'HSV': "HSV",
            'I': "32-bit Integer",
            'F': "32-bit Float",
        }
        return mode_descriptions.get(mode, mode)
    
    def _get_bit_depth(self, image: Image.Image) -> str:
        """Get bit depth description."""
        mode_bits = {
            '1': "1 bit",
            'L': "8 bits",
            'LA': "16 bits (8+8)",
            'P': "8 bits",
            'PA': "16 bits (8+8)",
            'RGB': "24 bits (8×3)",
            'RGBA': "32 bits (8×4)",
            'RGBX': "32 bits",
            'CMYK': "32 bits (8×4)",
            'I': "32 bits",
            'F': "32 bits",
        }
        return mode_bits.get(image.mode, "Unknown")
    
    def _get_format_details(self, image: Image.Image) -> dict[str, Any]:
        """Extract format-specific details from image."""
        details = {}
        
        # DPI
        if 'dpi' in image.info:
            dpi = image.info['dpi']
            if isinstance(dpi, tuple):
                details['DPI'] = f"{dpi[0]} × {dpi[1]}"
            else:
                details['DPI'] = str(dpi)
        
        # ICC Profile
        if 'icc_profile' in image.info:
            details['Color Profile'] = "Embedded"
        
        # PNG specific
        if image.format == 'PNG':
            if 'gamma' in image.info:
                details['Gamma'] = f"{image.info['gamma']:.4f}"
        
        # ICO specific
        if image.format == 'ICO':
            details['ICO Format'] = "Windows Icon"
        
        # EXIF data presence
        if hasattr(image, '_getexif') and image._getexif():
            details['EXIF'] = "Present"
        
        return details
    
    def _apply_theme(self, is_dark: bool = True) -> None:
        """Apply theme styling to the panel."""
        c = get_theme_colors(is_dark=is_dark)

        self.setStyleSheet(f"""
            MetadataPanel {{
                background-color: {c['panel_bg']};
                border: 1px solid {c['border_default']};
                border-radius: 4px;
            }}
            
            QLabel#panel_title {{
                color: {BRAND_GOLD};
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
            }}
            
            QGroupBox#metadata_group {{
                background-color: {c['card_bg']};
                border: 1px solid {c['border_default']};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: {c['text_primary']};
            }}
            
            QGroupBox#metadata_group::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            
            QLabel#metadata_label {{
                color: {c['text_secondary']};
                font-size: 11px;
                padding-right: 5px;
            }}
            
            QLabel#metadata_value {{
                color: {c['text_primary']};
                font-size: 11px;
            }}
            
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
        """)
    
    def apply_theme(self, is_dark: bool) -> None:
        """
        Apply theme from external source.
        
        Args:
            is_dark: True for dark theme, False for light
        """
        self._apply_theme(is_dark)
    
    def clear(self) -> None:
        """Clear the metadata display."""
        self._current_image = None
        self._current_path = None
        self._show_empty_state()


# Module exports
__all__: list[str] = [
    'MetadataPanel',
]