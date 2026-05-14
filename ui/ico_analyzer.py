"""
RNV Icon Builder - ICO Analyzer Module
Dialog for analyzing ICO file structure and contents.

Features:
- Display all sizes in ICO file
- Show compression type (PNG vs BMP) per image
- Show file size breakdown
- Display bit depth and color info
- Extract ICO to PNG files
"""

from __future__ import annotations

import os
from typing import Any

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QFileDialog, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from utils.config import ICO_FILE_FILTER
from utils.dialog_helper import DialogHelper
from ui.base_dialog import BaseDialog
from ui.colors import BRAND_GOLD, BRAND_GOLD_DARK, get_theme_colors
from core.icon_builder_core import IconBuilderCore
from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)


class IcoAnalyzerDialog(BaseDialog):
    """
    Dialog for analyzing ICO file structure and contents.
    
    Shows detailed information about each image in an ICO file including:
    - Dimensions
    - Compression type (PNG vs BMP)
    - File size
    - Bit depth
    
    Example:
        >>> dialog = IcoAnalyzerDialog(parent)
        >>> dialog.analyze_file("app.ico")
        >>> dialog.exec()
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the analyzer dialog."""
        super().__init__(
            parent=parent,
            title="ICO Analyzer",
            modal=True,
            min_size=(600, 450)
        )
        
        # Ensure Qt deletes the C++ object when dialog is closed
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self._current_info: dict[str, Any] | None = None
        
        self._setup_ui()
        self._apply_theme(dark_mode=self._is_dark_theme())
        
        logger.debug("IcoAnalyzerDialog initialized")
    
    def closeEvent(self, event) -> None:
        """Handle dialog close with data reference cleanup."""
        # Release data references
        self._current_info = None
        
        logger.debug("ICO Analyzer dialog closed")
        super().closeEvent(event)
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # File selection section
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("file_label")
        file_layout.addWidget(self.file_label, 1)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setToolTip("Browse for an ICO file to analyze")
        self.browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_btn)
        
        layout.addLayout(file_layout)
        
        # File info group
        self.info_group = QGroupBox("File Information")
        info_layout = QVBoxLayout(self.info_group)
        info_layout.setContentsMargins(15, 20, 15, 15)
        info_layout.setSpacing(8)
        
        # Info labels
        self.file_size_label = QLabel("File Size: --")
        self.image_count_label = QLabel("Images: --")
        self.compression_label = QLabel("Compression: --")
        self.sizes_label = QLabel("Sizes: --")
        self.sizes_label.setWordWrap(True)
        
        info_layout.addWidget(self.file_size_label)
        info_layout.addWidget(self.image_count_label)
        info_layout.addWidget(self.compression_label)
        info_layout.addWidget(self.sizes_label)
        
        layout.addWidget(self.info_group)
        
        # Images table
        self.table_group = QGroupBox("Image Details")
        table_layout = QVBoxLayout(self.table_group)
        table_layout.setContentsMargins(15, 20, 15, 15)
        
        self.images_table = QTableWidget()
        self.images_table.setColumnCount(5)
        self.images_table.setHorizontalHeaderLabels([
            "Size", "Compression", "Bit Depth", "Bytes", "%"
        ])
        
        # Configure table
        header = self.images_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Bytes stretches
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        # Set minimum widths to ensure visibility
        self.images_table.setColumnWidth(4, 80)  # % of Total minimum width
        header.setMinimumSectionSize(60)
        
        self.images_table.setAlternatingRowColors(True)
        self.images_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.images_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.images_table.setAutoFillBackground(True)
        
        # Ensure viewport background is styled
        self.images_table.viewport().setAutoFillBackground(True)
        
        table_layout.addWidget(self.images_table)
        
        layout.addWidget(self.table_group, 1)
        
        # Button row: Extract and Close
        btn_layout = QHBoxLayout()
        
        # Extract to PNGs button 
        self.extract_btn = QPushButton("📤 Extract to PNGs...")
        self.extract_btn.setObjectName("extract_btn")
        self.extract_btn.setToolTip("Extract all images from ICO as separate PNG files")
        self.extract_btn.clicked.connect(self._extract_to_pngs)
        self.extract_btn.setEnabled(False)  # Disabled until file is loaded
        btn_layout.addWidget(self.extract_btn)
        
        btn_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setToolTip("Close this dialog (Esc)")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
    
    def _browse_file(self) -> None:
        """Open file browser to select an ICO file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ICO File to Analyze",
            "",
            ICO_FILE_FILTER
        )
        
        if file_path:
            self.analyze_file(file_path)
    
    def analyze_file(self, file_path: str) -> bool:
        """
        Analyze an ICO file and display results.
        
        Args:
            file_path: Path to ICO file
            
        Returns:
            True if analysis successful
        """
        logger.info(f"Analyzing ICO file: {file_path}")
        
        # Get ICO info
        info = IconBuilderCore.get_ico_info(file_path)
        
        if not info:
            logger.warning(f"Failed to analyze: {file_path}")
            self._show_error("Could not read file")
            self.extract_btn.setEnabled(False)
            return False
        
        if not info.get('valid', False):
            error_msg = info.get('error', 'Unknown error')
            logger.warning(f"Invalid ICO file: {error_msg}")
            self._show_error(f"Invalid ICO file: {error_msg}")
            self.extract_btn.setEnabled(False)
            return False
        
        self._current_info = info
        self._display_info(info)
        self.extract_btn.setEnabled(True)  # Enable extraction button
        logger.success(f"Analyzed ICO: {info.get('image_count', 0)} images")
        return True
    
    def _display_info(self, info: dict[str, Any]) -> None:
        """Display the analyzed ICO information."""
        # Update file label
        file_name = info.get('file_name', 'Unknown')
        self.file_label.setText(f"\U0001F4C4 {file_name}")
        
        # Update file info
        file_size = info.get('file_size', 0)
        self.file_size_label.setText(f"File Size: {self._format_bytes(file_size)}")
        
        image_count = info.get('image_count', 0)
        self.image_count_label.setText(f"Images: {image_count}")
        
        # Compression summary
        has_png = info.get('has_png', False)
        has_bmp = info.get('has_bmp', False)
        if has_png and has_bmp:
            comp_text = "Mixed (PNG + BMP)"
        elif has_png:
            comp_text = "PNG (compressed)"
        else:
            comp_text = "BMP (uncompressed)"
        self.compression_label.setText(f"Compression: {comp_text}")
        
        # Sizes summary
        sizes = info.get('sizes', [])
        self.sizes_label.setText(f"Sizes: {', '.join(sizes)}")
        
        # Populate table
        self._populate_table(info)
    
    def _populate_table(self, info: dict[str, Any]) -> None:
        """Populate the images table with data."""
        images = info.get('images', [])
        total_size = info.get('file_size', 1)  # Avoid div by zero
        
        self.images_table.setRowCount(len(images))
        
        for row, img in enumerate(images):
            # Size
            size_item = QTableWidgetItem(f"{img['width']}x{img['height']}")
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.images_table.setItem(row, 0, size_item)
            
            # Compression
            compression = img.get('compression', 'BMP')
            comp_item = QTableWidgetItem(compression)
            comp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Color code: green for PNG, default for BMP
            if compression == 'PNG':
                comp_item.setForeground(Qt.GlobalColor.darkGreen)
            self.images_table.setItem(row, 1, comp_item)
            
            # Bit depth
            bpp = img.get('bits_per_pixel', 0)
            bpp_text = f"{bpp}-bit" if bpp > 0 else "N/A"
            bpp_item = QTableWidgetItem(bpp_text)
            bpp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.images_table.setItem(row, 2, bpp_item)
            
            # Bytes
            img_bytes = img.get('bytes', 0)
            bytes_item = QTableWidgetItem(self._format_bytes(img_bytes))
            bytes_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.images_table.setItem(row, 3, bytes_item)
            
            # Percentage
            percentage = (img_bytes / total_size * 100) if total_size > 0 else 0
            pct_item = QTableWidgetItem(f"{percentage:.1f}%")
            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.images_table.setItem(row, 4, pct_item)
    
    def _format_bytes(self, size: int) -> str:
        """Format byte size to human readable string."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"
    
    def _show_error(self, message: str) -> None:
        """Show error state in the dialog."""
        self.file_label.setText(f"\u274C Error: {message}")
        self.file_size_label.setText("File Size: --")
        self.image_count_label.setText("Images: --")
        self.compression_label.setText("Compression: --")
        self.sizes_label.setText("Sizes: --")
        self.images_table.setRowCount(0)
    
    def _extract_to_pngs(self) -> None:
        """Extract all images from the loaded ICO file as PNGs."""
        if not self._current_info or not self._current_info.get('valid'):
            DialogHelper.show_warning(
                self,
                "Please load an ICO file first.",
                "No File Loaded"
            )
            return
        
        ico_path = self._current_info.get('file_path')
        if not ico_path or not os.path.exists(ico_path):
            DialogHelper.show_warning(
                self,
                "The ICO file could not be found.",
                "File Not Found"
            )
            return
        
        # Ask user for output folder
        output_folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder for PNG Files"
        )
        
        if not output_folder:
            return  # User cancelled
        
        # Get base name from ICO filename
        ico_name = os.path.splitext(self._current_info.get('file_name', 'icon'))[0]
        
        # Extract images
        logger.info(f"Extracting ICO to PNGs: {ico_path} -> {output_folder}")
        
        success, message, extracted_files = IconBuilderCore.extract_ico_to_pngs(
            ico_path,
            output_folder,
            ico_name
        )
        
        if success:
            logger.success(f"Extracted {len(extracted_files)} PNG files")
            
            # Show success message
            file_list = "\n".join([os.path.basename(f) for f in extracted_files[:5]])
            if len(extracted_files) > 5:
                file_list += f"\n... and {len(extracted_files) - 5} more"
            
            DialogHelper.show_info(
                self,
                f"Successfully extracted {len(extracted_files)} PNG file(s) to:\n\n"
                f"{output_folder}\n\n"
                f"Files:\n{file_list}",
                "Extraction Complete"
            )
        else:
            logger.warning(f"Extraction failed: {message}")
            DialogHelper.show_warning(
                self,
                f"Failed to extract images:\n\n{message}",
                "Extraction Failed"
            )
    
    def _apply_theme(self, dark_mode: bool = True) -> None:
        """Apply theme styling to the dialog."""
        c = get_theme_colors(is_dark=dark_mode)
        accent = BRAND_GOLD if dark_mode else BRAND_GOLD_DARK

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c['window_bg']};
                color: {c['text_primary']};
            }}

            QGroupBox {{
                font-weight: bold;
                border: 1px solid {c['border_default']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {accent};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}

            QLabel {{
                color: {c['text_primary']};
            }}

            QLabel[objectName="file_label"] {{
                font-size: 12px;
                font-weight: bold;
                color: {accent};
            }}

            QPushButton {{
                background-color: {c['button_bg']};
                color: {c['button_text']};
                border: 1px solid {c['button_border']};
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
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

            QPushButton:disabled {{
                background-color: {c['panel_bg']};
                color: {c['text_disabled']};
                border-color: {c['border_default']};
            }}

            QPushButton[objectName="extract_btn"] {{
                background-color: {c['accent_button_bg']};
                color: {c['accent_button_text']};
                border: 1px solid {c['accent_button_border']};
            }}

            QPushButton[objectName="extract_btn"]:hover {{
                background-color: {c['accent_button_hover_bg']};
                color: {c['accent_button_text']};
                border-color: {c['accent_button_border']};
            }}

            QPushButton[objectName="extract_btn"]:pressed {{
                background-color: {c['accent_button_pressed_bg']};
                color: {c['accent_button_pressed_text']};
            }}

            QPushButton[objectName="extract_btn"]:disabled {{
                background-color: {c['panel_bg']};
                color: {c['text_disabled']};
                border-color: {c['border_hover']};
            }}

            QTableWidget {{
                background-color: {c['list_bg']};
                alternate-background-color: {c['list_alt_bg']};
                color: {c['text_primary']};
                border: 1px solid {c['border_default']};
                gridline-color: {c['list_grid']};
                selection-background-color: {c['list_selected_bg']};
                selection-color: {c['text_on_accent']};
            }}

            QTableWidget::item {{
                padding: 5px;
                background-color: {c['list_bg']};
                color: {c['text_primary']};
            }}

            QTableWidget::item:alternate {{
                background-color: {c['list_alt_bg']};
            }}

            QTableWidget::item:selected {{
                background-color: {c['list_selected_bg']};
                color: {c['text_on_accent']};
            }}

            QTableWidget::item:selected:active {{
                background-color: {accent};
                color: {c['text_on_accent']};
            }}

            QTableWidget::item:focus {{
                background-color: {accent};
                color: {c['text_on_accent']};
                outline: none;
                border: none;
            }}

            QHeaderView::section {{
                background-color: {c['list_header_bg']};
                color: {accent};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {c['border_default']};
                font-weight: bold;
            }}

            QHeaderView::section:vertical {{
                background-color: {c['list_header_bg']};
                color: {c['text_primary']};
                border-right: 1px solid {c['border_default']};
                border-bottom: 1px solid {c['border_default']};
            }}

            QTableCornerButton::section {{
                background-color: {c['list_header_bg']};
                border: none;
                border-right: 1px solid {c['border_default']};
                border-bottom: 1px solid {c['border_default']};
            }}

            QScrollBar:vertical {{
                background: {c['scrollbar_bg']};
                width: 12px;
                border: 1px solid {c['scrollbar_border']};
                border-radius: 6px;
            }}

            QScrollBar::handle:vertical {{
                background: {c['scrollbar_handle']};
                min-height: 20px;
                border-radius: 5px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {c['scrollbar_handle_hover']};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
    
    def apply_theme_from_manager(self, theme_name: str) -> None:
        """
        Apply theme based on theme manager state.
        
        Args:
            theme_name: Current theme ('dark', 'light', 'image')
        """
        dark_mode = theme_name != 'light'
        self._apply_theme(dark_mode)
        
        # Simple update - no need for expensive unpolish/polish
        self.update()


# ==================== Module Exports ====================

__all__: list[str] = [
    'IcoAnalyzerDialog',
]