"""
RNV Icon Builder - Settings Dialog Module
Tabbed settings dialog for application configuration.

Features:
- Tabbed interface for organized settings
- Size selection with presets
- Export options
- Quick image adjustments
- Recent files and folders history
- Visual settings
- Brightness/Contrast/Saturation adjustments
- Grayscale conversion
- macOS .icns export
- Estimated file size preview
- Output filename templates
- Favicon Package export
- Android Adaptive Icons export
- iOS App Icon Set export
- Batch processing controls
- Watch folder mode
- Custom preset management
- Project files support
- Session restore options
- Preview background options
- Zoom controls
- Color palette display
- Icon in context preview
- Image metadata panel
- Compression statistics display
- Export history tracking
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QCheckBox, QPushButton, QLabel, QGridLayout,
    QFrame, QSizePolicy, QSpacerItem, QScrollArea, QSpinBox, QComboBox,
    QListWidget, QListWidgetItem, QColorDialog, QSlider, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QColor

from utils.config import ICON_SIZES
from ui.colors import (
    BRAND_GOLD, BRAND_GOLD_DARK, get_theme_colors,
    SWATCH_BORDER_ON_LIGHT, SWATCH_BORDER_ON_DARK, STATUS_ACTIVE_COLOR,
)
from utils.logger import Logger, get_logger_instance
from utils.dialog_helper import DialogHelper
from ui.base_dialog import BaseDialog

if TYPE_CHECKING:
    from RNV_Icon_Builder import IconBuilderApp

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)


class SettingsDialog(BaseDialog):
    """
    Tabbed settings dialog for RNV Icon Builder.
    
    Tabs:
    - Sizes: Icon size selection and presets
    - Export: Export format options
    - Adjust: Quick image adjustments
    - Preview: Preview background and zoom options
    - Info: Export history and compression statistics
    - Auto: Batch processing and folder watching
    - Recent: Recently opened files and folders
    
    Signals:
        settings_changed: Emitted when settings are modified
        export_png_requested: Emitted when PNG Set export is requested
        analyze_ico_requested: Emitted when ICO analysis is requested
        auto_crop_requested: Emitted when auto-crop is requested
        add_padding_requested: Emitted with padding value
        center_resize_requested: Emitted with (size, maintain_aspect)
        open_recent_file_requested: Emitted with file path when recent file clicked
        open_recent_folder_requested: Emitted with folder path when recent folder clicked
        undo_requested: Emitted when undo is requested
        redo_requested: Emitted when redo is requested
        color_adjustment_requested: Emitted with (brightness, contrast, saturation)
        grayscale_requested: Emitted when grayscale conversion is requested
    """
    
    # Signals
    settings_changed = pyqtSignal()
    export_png_requested = pyqtSignal()
    analyze_ico_requested = pyqtSignal()
    auto_crop_requested = pyqtSignal()
    add_padding_requested = pyqtSignal(int)
    center_resize_requested = pyqtSignal(int, bool)
    open_recent_file_requested = pyqtSignal(str)
    open_recent_folder_requested = pyqtSignal(str)
    # Transform signals
    rotate_requested = pyqtSignal(int)  # degrees
    flip_horizontal_requested = pyqtSignal()
    flip_vertical_requested = pyqtSignal()
    # Color signals
    fill_transparency_requested = pyqtSignal(tuple)  # color tuple
    add_border_requested = pyqtSignal(int, tuple)  # width, color tuple
    # Undo/Redo signals
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    # Color Adjustment signals
    color_adjustment_requested = pyqtSignal(int, int, int)  # brightness, contrast, saturation
    grayscale_requested = pyqtSignal()
    # Export Format signals
    export_icns_requested = pyqtSignal()
    filename_template_changed = pyqtSignal(str)  # template string
    # Platform Export signals
    export_favicon_requested = pyqtSignal()
    export_android_requested = pyqtSignal()
    export_ios_requested = pyqtSignal()
    # Workflow Automation signals
    # Batch Processing
    batch_add_files_requested = pyqtSignal()
    batch_add_folder_requested = pyqtSignal()
    batch_clear_requested = pyqtSignal()
    batch_process_requested = pyqtSignal()
    batch_cancel_requested = pyqtSignal()
    # Watch Folder
    watch_start_requested = pyqtSignal(str, str)  # input_folder, output_folder
    watch_stop_requested = pyqtSignal()
    # Presets
    preset_selected = pyqtSignal(str)  # preset_name
    preset_save_requested = pyqtSignal(str)  # new_preset_name
    preset_delete_requested = pyqtSignal(str)  # preset_name
    # Project Files
    project_save_requested = pyqtSignal()
    project_save_as_requested = pyqtSignal()
    project_load_requested = pyqtSignal()
    project_new_requested = pyqtSignal()
    # Session
    session_restore_requested = pyqtSignal()
    session_settings_changed = pyqtSignal(bool, bool)  # restore_session, auto_save
    
    # Preview Enhancement signals
    background_changed = pyqtSignal(str, object)  # background_type, custom_color
    zoom_changed = pyqtSignal(int)  # zoom_percentage
    context_preview_requested = pyqtSignal()  # open context preview dialog
    
    # Information & Metadata signals
    clear_export_history_requested = pyqtSignal()  # clear export history
    reveal_in_explorer_requested = pyqtSignal(str)  # path to reveal
    
    def __init__(self, parent: QWidget | None = None, recent_files_manager = None,
                 preset_manager = None, batch_processor = None, folder_watcher = None,
                 project_manager = None, export_history = None) -> None:
        """Initialize the settings dialog."""
        super().__init__(
            parent=parent,
            title="Icon Builder - Settings",
            modal=False,
            min_size=(690, 720),
            max_size=(690, 720)
        )
        
        # Size checkboxes storage
        self.size_checkboxes: dict[int, QCheckBox] = {}
        
        # Manager references
        self.recent_files_manager = recent_files_manager
        self.preset_manager = preset_manager
        self.batch_processor = batch_processor
        self.folder_watcher = folder_watcher
        self.project_manager = project_manager
        self.export_history = export_history
        
        # Compression statistics from last build
        self._last_compression_stats: dict | None = None
        
        # Watch folder state
        self._is_watching: bool = False
        
        # Store selected colors for fill and border
        self._fill_color: tuple = (255, 255, 255, 255)  # Default white
        self._border_color: tuple = (0, 0, 0, 255)  # Default black
        
        # Track current theme to avoid unnecessary reapplication
        self._current_theme_is_dark: bool = True
        
        self._build_ui()
        self._apply_theme(is_dark=self._is_dark_theme())
        
        logger.debug("Settings dialog initialized")
    
    def _build_ui(self) -> None:
        """Build the control panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setAutoFillBackground(True)
        
        # Create tabs
        self.sizes_tab = self._create_sizes_tab()
        self.export_tab = self._create_export_tab()
        self.adjust_tab = self._create_adjust_tab()
        self.preview_tab = self._create_preview_tab()
        self.info_tab = self._create_info_tab()
        self.automation_tab = self._create_automation_tab()
        self.recent_tab = self._create_recent_tab()
        
        # Set auto fill background on all tabs
        for tab in [self.sizes_tab, self.export_tab, self.adjust_tab, self.preview_tab,
                    self.info_tab, self.automation_tab, self.recent_tab]:
            tab.setAutoFillBackground(True)
        
        # Add tabs with emoji icons
        self.tabs.addTab(self.sizes_tab, "\U0001F4D0 Sizes")
        self.tabs.addTab(self.export_tab, "\U0001F4E4 Export")
        self.tabs.addTab(self.adjust_tab, "\u2699\ufe0f Adjust")
        self.tabs.addTab(self.preview_tab, "\U0001F50D Preview")
        self.tabs.addTab(self.info_tab, "\U0001F4CA Info")
        self.tabs.addTab(self.automation_tab, "\U0001F504 Auto")
        self.tabs.addTab(self.recent_tab, "\U0001F4C2 Recent")
        
        layout.addWidget(self.tabs)
        
    
    def _create_sizes_tab(self) -> QWidget:
        """Create the Sizes tab with size selection and presets."""
        sizes_tab = QWidget()
        layout = QVBoxLayout(sizes_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Size selection group
        size_group = QGroupBox("Include Sizes in Output")
        size_layout = QGridLayout(size_group)
        size_layout.setSpacing(15)
        size_layout.setContentsMargins(15, 20, 15, 15)
        
        # Create checkboxes in a 2-column grid
        for i, size in enumerate(ICON_SIZES):
            cb = QCheckBox(f"{size} x {size}")
            cb.setChecked(True)
            cb.setToolTip(f"Include {size}x{size} in ICO output")
            cb.stateChanged.connect(self._on_size_changed)
            self.size_checkboxes[size] = cb
            
            row = i // 2
            col = i % 2
            size_layout.addWidget(cb, row, col)
        
        layout.addWidget(size_group)
        
        # Presets group
        preset_group = QGroupBox("Quick Presets")
        preset_layout = QGridLayout(preset_group)
        preset_layout.setSpacing(10)
        preset_layout.setContentsMargins(15, 20, 15, 15)
        
        # Row 1: All, Favicon
        all_btn = QPushButton("All Sizes")
        all_btn.setToolTip("Select all 6 standard sizes")
        all_btn.clicked.connect(self._select_all_sizes)
        preset_layout.addWidget(all_btn, 0, 0)
        
        favicon_btn = QPushButton("Favicon")
        favicon_btn.setToolTip("Web favicon: 16, 32, 48")
        favicon_btn.clicked.connect(self._select_favicon_preset)
        preset_layout.addWidget(favicon_btn, 0, 1)
        
        # Row 2: Windows, macOS
        win_btn = QPushButton("Windows")
        win_btn.setToolTip("Windows icons: 16, 32, 48, 256")
        win_btn.clicked.connect(self._select_windows_preset)
        preset_layout.addWidget(win_btn, 1, 0)
        
        mac_btn = QPushButton("macOS")
        mac_btn.setToolTip("macOS icons: 16, 32, 128, 256")
        mac_btn.clicked.connect(self._select_macos_preset)
        preset_layout.addWidget(mac_btn, 1, 1)
        
        # Row 3: None
        none_btn = QPushButton("Clear All")
        none_btn.setToolTip("Deselect all sizes")
        none_btn.clicked.connect(self._select_none)
        preset_layout.addWidget(none_btn, 2, 0, 1, 2)
        
        layout.addWidget(preset_group)
        
        # Info label
        info_label = QLabel(
            "Selected sizes will be included when building ICO files.\n"
            "Unselected sizes will be skipped even if images are loaded."
        )
        info_label.setObjectName("desc_label")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        return sizes_tab
    
    def _create_export_tab(self) -> QWidget:
        """Create the Export tab with export options."""
        export_tab = QWidget()
        layout = QVBoxLayout(export_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Use a scroll area to fit all groups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 5, 0)
        scroll_layout.setSpacing(10)
        
        # PNG Set export group
        png_group = QGroupBox("Export as PNG Set")
        png_layout = QVBoxLayout(png_group)
        png_layout.setContentsMargins(15, 20, 15, 15)
        png_layout.setSpacing(8)
        
        png_desc = QLabel(
            "Save each selected size as a separate PNG file."
        )
        png_desc.setObjectName("desc_label")
        png_desc.setWordWrap(True)
        png_layout.addWidget(png_desc)
        
        png_btn = QPushButton("Export PNG Set...")
        png_btn.setObjectName("export_png_btn")
        png_btn.setToolTip("Export individual PNG files at selected sizes")
        png_btn.clicked.connect(self._on_export_png)
        png_layout.addWidget(png_btn)
        
        scroll_layout.addWidget(png_group)
        
        # macOS .icns export group 
        icns_group = QGroupBox("Export as macOS Icon")
        icns_layout = QVBoxLayout(icns_group)
        icns_layout.setContentsMargins(15, 20, 15, 15)
        icns_layout.setSpacing(8)
        
        icns_desc = QLabel(
            "Export as macOS .icns format for Mac applications."
        )
        icns_desc.setObjectName("desc_label")
        icns_desc.setWordWrap(True)
        icns_layout.addWidget(icns_desc)
        
        icns_btn = QPushButton("Export .icns File...")
        icns_btn.setObjectName("export_icns_btn")
        icns_btn.setToolTip("Export as macOS .icns icon file")
        icns_btn.clicked.connect(self._on_export_icns)
        icns_layout.addWidget(icns_btn)
        
        scroll_layout.addWidget(icns_group)
        
        # Platform Exports group 
        platform_group = QGroupBox("Platform-Specific Exports")
        platform_layout = QVBoxLayout(platform_group)
        platform_layout.setContentsMargins(15, 20, 15, 15)
        platform_layout.setSpacing(8)
        
        platform_desc = QLabel(
            "Export icon sets optimized for specific platforms."
        )
        platform_desc.setObjectName("desc_label")
        platform_desc.setWordWrap(True)
        platform_layout.addWidget(platform_desc)
        
        # Favicon Package button
        favicon_btn = QPushButton("\U0001F310 Favicon Package...")
        favicon_btn.setObjectName("platform_btn")
        favicon_btn.setToolTip(
            "Export complete favicon package:\n"
            "• favicon.ico (16, 32, 48)\n"
            "• PNG favicons\n"
            "• apple-touch-icon.png\n"
            "• Android Chrome icons\n"
            "• site.webmanifest\n"
            "• browserconfig.xml"
        )
        favicon_btn.clicked.connect(self._on_export_favicon)
        platform_layout.addWidget(favicon_btn)
        
        # Android Icons button
        android_btn = QPushButton("\U0001F4F1 Android Icons...")
        android_btn.setObjectName("platform_btn")
        android_btn.setToolTip(
            "Export Android adaptive icons:\n"
            "• mipmap-mdpi (48x48)\n"
            "• mipmap-hdpi (72x72)\n"
            "• mipmap-xhdpi (96x96)\n"
            "• mipmap-xxhdpi (144x144)\n"
            "• mipmap-xxxhdpi (192x192)"
        )
        android_btn.clicked.connect(self._on_export_android)
        platform_layout.addWidget(android_btn)
        
        # iOS Icons button
        ios_btn = QPushButton("\U0001F34E iOS App Icons...")
        ios_btn.setObjectName("platform_btn")
        ios_btn.setToolTip(
            "Export iOS App Icon Set:\n"
            "• All required sizes with @2x/@3x\n"
            "• Contents.json manifest\n"
            "• Ready for Xcode"
        )
        ios_btn.clicked.connect(self._on_export_ios)
        platform_layout.addWidget(ios_btn)
        
        scroll_layout.addWidget(platform_group)
        
        # ICO Analyzer group
        analyzer_group = QGroupBox("ICO Analyzer")
        analyzer_layout = QVBoxLayout(analyzer_group)
        analyzer_layout.setContentsMargins(15, 20, 15, 15)
        analyzer_layout.setSpacing(8)
        
        analyzer_desc = QLabel(
            "Analyze ICO files to see structure, compression, and sizes."
        )
        analyzer_desc.setObjectName("desc_label")
        analyzer_desc.setWordWrap(True)
        analyzer_layout.addWidget(analyzer_desc)
        
        analyzer_btn = QPushButton("Analyze ICO File...")
        analyzer_btn.setObjectName("analyzer_btn")
        analyzer_btn.setToolTip("Inspect the internal structure of an existing ICO file")
        analyzer_btn.clicked.connect(self._on_analyze_ico)
        analyzer_layout.addWidget(analyzer_btn)
        
        scroll_layout.addWidget(analyzer_group)
        
        # Estimated File Size group 
        size_group = QGroupBox("Estimated File Size")
        size_layout = QVBoxLayout(size_group)
        size_layout.setContentsMargins(15, 20, 15, 15)
        size_layout.setSpacing(8)
        
        self.file_size_label = QLabel("Load images to see estimate")
        self.file_size_label.setObjectName("size_label")
        size_layout.addWidget(self.file_size_label)
        
        self.file_size_details = QLabel("")
        self.file_size_details.setObjectName("desc_label")
        self.file_size_details.setWordWrap(True)
        size_layout.addWidget(self.file_size_details)
        
        scroll_layout.addWidget(size_group)
        
        # Filename Template group 
        template_group = QGroupBox("Output Filename Template")
        template_layout = QVBoxLayout(template_group)
        template_layout.setContentsMargins(15, 20, 15, 15)
        template_layout.setSpacing(8)
        
        template_desc = QLabel(
            "Customize output filenames using placeholders:\n"
            "{name} = base name, {size} = dimensions, {date} = date"
        )
        template_desc.setObjectName("desc_label")
        template_desc.setWordWrap(True)
        template_layout.addWidget(template_desc)
        
        template_row = QHBoxLayout()
        template_row.addWidget(QLabel("Template:"))
        self.template_input = QLineEdit()
        self.template_input.setToolTip("Output filename pattern — {name} is replaced with original filename")
        self.template_input.setPlaceholderText("icon_{size}")
        self.template_input.setText("icon_{size}")
        self.template_input.textChanged.connect(self._on_template_changed)
        template_row.addWidget(self.template_input)
        template_layout.addLayout(template_row)
        
        self.template_preview = QLabel("Preview: icon_256.png")
        self.template_preview.setObjectName("desc_label")
        template_layout.addWidget(self.template_preview)
        
        scroll_layout.addWidget(template_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return export_tab
    
    def _create_adjust_tab(self) -> QWidget:
        """Create the Adjust tab with image adjustment tools."""
        adjust_tab = QWidget()
        
        # Use a scroll area for the adjust tab since it has many controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # ==================== Undo/Redo Group ====================
        undo_group = QGroupBox("History")
        undo_layout = QHBoxLayout(undo_group)
        undo_layout.setContentsMargins(15, 20, 15, 15)
        undo_layout.setSpacing(10)
        
        self.undo_btn = QPushButton("\u21b6 Undo")
        self.undo_btn.setObjectName("action_btn")
        self.undo_btn.setToolTip("Undo last adjustment (Ctrl+Z)")
        self.undo_btn.clicked.connect(self._on_undo)
        undo_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("Redo \u21b7")
        self.redo_btn.setObjectName("action_btn")
        self.redo_btn.setToolTip("Redo last undone adjustment (Ctrl+Y)")
        self.redo_btn.clicked.connect(self._on_redo)
        undo_layout.addWidget(self.redo_btn)
        
        undo_layout.addStretch()
        
        layout.addWidget(undo_group)
        
        # Info label
        info_label = QLabel(
            "Apply adjustments to all currently loaded images."
        )
        info_label.setObjectName("info_label")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # ==================== Transform Group ====================
        transform_group = QGroupBox("Transform")
        transform_layout = QVBoxLayout(transform_group)
        transform_layout.setContentsMargins(15, 20, 15, 15)
        transform_layout.setSpacing(8)
        
        # Rotate buttons row
        rotate_row = QHBoxLayout()
        rotate_row.addWidget(QLabel("Rotate:"))
        
        self.rotate_ccw_btn = QPushButton("\u21ba 90 CCW")
        self.rotate_ccw_btn.setObjectName("small_btn")
        self.rotate_ccw_btn.setToolTip("Rotate 90 degrees counter-clockwise")
        self.rotate_ccw_btn.clicked.connect(lambda: self._on_rotate(270))
        rotate_row.addWidget(self.rotate_ccw_btn)
        
        self.rotate_180_btn = QPushButton("180")
        self.rotate_180_btn.setObjectName("small_btn")
        self.rotate_180_btn.setToolTip("Rotate 180 degrees")
        self.rotate_180_btn.clicked.connect(lambda: self._on_rotate(180))
        rotate_row.addWidget(self.rotate_180_btn)
        
        self.rotate_cw_btn = QPushButton("\u21bb 90 CW")
        self.rotate_cw_btn.setObjectName("small_btn")
        self.rotate_cw_btn.setToolTip("Rotate 90 degrees clockwise")
        self.rotate_cw_btn.clicked.connect(lambda: self._on_rotate(90))
        rotate_row.addWidget(self.rotate_cw_btn)
        
        rotate_row.addStretch()
        transform_layout.addLayout(rotate_row)
        
        # Flip buttons row
        flip_row = QHBoxLayout()
        flip_row.addWidget(QLabel("Flip:"))
        
        self.flip_h_btn = QPushButton("↔ Horizontal")
        self.flip_h_btn.setObjectName("small_btn")
        self.flip_h_btn.setToolTip("Flip horizontally (mirror)")
        self.flip_h_btn.clicked.connect(self._on_flip_horizontal)
        flip_row.addWidget(self.flip_h_btn)
        
        self.flip_v_btn = QPushButton("↕ Vertical")
        self.flip_v_btn.setObjectName("small_btn")
        self.flip_v_btn.setToolTip("Flip vertically")
        self.flip_v_btn.clicked.connect(self._on_flip_vertical)
        flip_row.addWidget(self.flip_v_btn)
        
        flip_row.addStretch()
        transform_layout.addLayout(flip_row)
        
        layout.addWidget(transform_group)
        
        # ==================== Color Group ====================
        color_group = QGroupBox("Color")
        color_layout = QVBoxLayout(color_group)
        color_layout.setContentsMargins(15, 20, 15, 15)
        color_layout.setSpacing(8)
        
        # Fill transparency row
        fill_row = QHBoxLayout()
        fill_row.addWidget(QLabel("Fill transparency:"))
        
        self.fill_color_btn = QPushButton()
        self.fill_color_btn.setObjectName("color_swatch")
        self.fill_color_btn.setFixedSize(28, 28)
        self.fill_color_btn.setToolTip("Click to choose fill color")
        self.fill_color_btn.clicked.connect(self._on_choose_fill_color)
        self._update_color_button(self.fill_color_btn, self._fill_color)
        fill_row.addWidget(self.fill_color_btn)
        
        self.fill_btn = QPushButton("Fill")
        self.fill_btn.setObjectName("small_btn")
        self.fill_btn.setToolTip("Replace transparent areas with selected color")
        self.fill_btn.clicked.connect(self._on_fill_transparency)
        fill_row.addWidget(self.fill_btn)
        
        fill_row.addStretch()
        color_layout.addLayout(fill_row)
        
        # Add border row
        border_row = QHBoxLayout()
        border_row.addWidget(QLabel("Add border:"))
        
        self.border_color_btn = QPushButton()
        self.border_color_btn.setObjectName("color_swatch")
        self.border_color_btn.setFixedSize(28, 28)
        self.border_color_btn.setToolTip("Click to choose border color")
        self.border_color_btn.clicked.connect(self._on_choose_border_color)
        self._update_color_button(self.border_color_btn, self._border_color)
        border_row.addWidget(self.border_color_btn)
        
        self.border_width_spin = QSpinBox()
        self.border_width_spin.setRange(1, 32)
        self.border_width_spin.setValue(2)
        self.border_width_spin.setSuffix(" px")
        self.border_width_spin.setToolTip("Border width in pixels")
        border_row.addWidget(self.border_width_spin)
        
        self.border_btn = QPushButton("Add Border")
        self.border_btn.setObjectName("small_btn")
        self.border_btn.setToolTip("Add colored border around image content")
        self.border_btn.clicked.connect(self._on_add_border)
        border_row.addWidget(self.border_btn)
        
        border_row.addStretch()
        color_layout.addLayout(border_row)
        
        layout.addWidget(color_group)
        
        # ==================== Color Adjustments Group  ====================
        color_adj_group = QGroupBox("Color Adjustments")
        color_adj_layout = QVBoxLayout(color_adj_group)
        color_adj_layout.setContentsMargins(15, 20, 15, 15)
        color_adj_layout.setSpacing(8)
        
        # Brightness slider row
        brightness_row = QHBoxLayout()
        brightness_label = QLabel("Brightness:")
        brightness_label.setMinimumWidth(70)
        brightness_row.addWidget(brightness_label)
        
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setToolTip("Adjust image brightness (-100 to +100)")
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.brightness_slider.setTickInterval(25)
        self.brightness_slider.valueChanged.connect(self._on_brightness_changed)
        brightness_row.addWidget(self.brightness_slider, 1)
        
        self.brightness_value_label = QLabel("0")
        self.brightness_value_label.setMinimumWidth(35)
        self.brightness_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        brightness_row.addWidget(self.brightness_value_label)
        
        color_adj_layout.addLayout(brightness_row)
        
        # Contrast slider row
        contrast_row = QHBoxLayout()
        contrast_label = QLabel("Contrast:")
        contrast_label.setMinimumWidth(70)
        contrast_row.addWidget(contrast_label)
        
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setToolTip("Adjust image contrast (-100 to +100)")
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.contrast_slider.setTickInterval(25)
        self.contrast_slider.valueChanged.connect(self._on_contrast_changed)
        contrast_row.addWidget(self.contrast_slider, 1)
        
        self.contrast_value_label = QLabel("0")
        self.contrast_value_label.setMinimumWidth(35)
        self.contrast_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        contrast_row.addWidget(self.contrast_value_label)
        
        color_adj_layout.addLayout(contrast_row)
        
        # Saturation slider row
        saturation_row = QHBoxLayout()
        saturation_label = QLabel("Saturation:")
        saturation_label.setMinimumWidth(70)
        saturation_row.addWidget(saturation_label)
        
        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setToolTip("Adjust image color saturation (-100 to +100)")
        self.saturation_slider.setRange(-100, 100)
        self.saturation_slider.setValue(0)
        self.saturation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.saturation_slider.setTickInterval(25)
        self.saturation_slider.valueChanged.connect(self._on_saturation_changed)
        saturation_row.addWidget(self.saturation_slider, 1)
        
        self.saturation_value_label = QLabel("0")
        self.saturation_value_label.setMinimumWidth(35)
        self.saturation_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        saturation_row.addWidget(self.saturation_value_label)
        
        color_adj_layout.addLayout(saturation_row)
        
        # Buttons row for Apply and Reset
        color_adj_btn_row = QHBoxLayout()
        
        self.apply_color_btn = QPushButton("Apply Adjustments")
        self.apply_color_btn.setObjectName("small_btn")
        self.apply_color_btn.setToolTip("Apply brightness, contrast, and saturation changes")
        self.apply_color_btn.clicked.connect(self._on_apply_color_adjustments)
        color_adj_btn_row.addWidget(self.apply_color_btn)
        
        self.reset_sliders_btn = QPushButton("Reset")
        self.reset_sliders_btn.setObjectName("small_btn")
        self.reset_sliders_btn.setToolTip("Reset all sliders to 0")
        self.reset_sliders_btn.clicked.connect(self._on_reset_color_sliders)
        color_adj_btn_row.addWidget(self.reset_sliders_btn)
        
        self.grayscale_btn = QPushButton("Grayscale")
        self.grayscale_btn.setObjectName("small_btn")
        self.grayscale_btn.setToolTip("Convert to grayscale (preserves transparency)")
        self.grayscale_btn.clicked.connect(self._on_grayscale)
        color_adj_btn_row.addWidget(self.grayscale_btn)
        
        color_adj_btn_row.addStretch()
        color_adj_layout.addLayout(color_adj_btn_row)
        
        layout.addWidget(color_adj_group)
        
        # ==================== Crop & Padding Group ====================
        crop_pad_group = QGroupBox("Crop && Padding")
        crop_pad_layout = QVBoxLayout(crop_pad_group)
        crop_pad_layout.setContentsMargins(15, 20, 15, 15)
        crop_pad_layout.setSpacing(8)
        
        # Auto-crop row
        crop_row = QHBoxLayout()
        crop_row.addWidget(QLabel("Auto-crop:"))
        self.crop_btn = QPushButton("Remove Transparent Borders")
        self.crop_btn.setObjectName("small_btn")
        self.crop_btn.setToolTip("Trim fully transparent pixels from image edges")
        self.crop_btn.clicked.connect(self._on_auto_crop)
        crop_row.addWidget(self.crop_btn)
        crop_row.addStretch()
        crop_pad_layout.addLayout(crop_row)
        
        # Padding row
        padding_row = QHBoxLayout()
        padding_row.addWidget(QLabel("Add padding:"))
        self.padding_spin = QSpinBox()
        self.padding_spin.setToolTip("Number of transparent pixels to add around image")
        self.padding_spin.setRange(1, 128)
        self.padding_spin.setValue(8)
        self.padding_spin.setSuffix(" px")
        padding_row.addWidget(self.padding_spin)
        
        self.padding_btn = QPushButton("Add Padding")
        self.padding_btn.setObjectName("small_btn")
        self.padding_btn.setToolTip("Add transparent padding around the image")
        self.padding_btn.clicked.connect(self._on_add_padding)
        padding_row.addWidget(self.padding_btn)
        padding_row.addStretch()
        crop_pad_layout.addLayout(padding_row)
        
        layout.addWidget(crop_pad_group)
        
        # ==================== Resize Group ====================
        resize_group = QGroupBox("Center && Resize")
        resize_layout = QVBoxLayout(resize_group)
        resize_layout.setContentsMargins(15, 20, 15, 15)
        resize_layout.setSpacing(8)
        
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Target size:"))
        self.resize_combo = QComboBox()
        self.resize_combo.setToolTip("Select target resolution for resize")
        for size in ICON_SIZES:
            self.resize_combo.addItem(f"{size}x{size}", size)
        size_row.addWidget(self.resize_combo)
        
        self.maintain_aspect_cb = QCheckBox("Maintain aspect")
        self.maintain_aspect_cb.setToolTip("Preserve original width-to-height ratio when resizing")
        self.maintain_aspect_cb.setChecked(True)
        size_row.addWidget(self.maintain_aspect_cb)
        
        self.resize_btn = QPushButton("Apply")
        self.resize_btn.setObjectName("small_btn")
        self.resize_btn.setToolTip("Resize image to selected dimensions")
        self.resize_btn.clicked.connect(self._on_center_resize)
        size_row.addWidget(self.resize_btn)
        size_row.addStretch()
        resize_layout.addLayout(size_row)
        
        layout.addWidget(resize_group)
        
        layout.addStretch()
        
        scroll.setWidget(scroll_content)
        
        # Main layout for adjust tab
        main_layout = QVBoxLayout(adjust_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        return adjust_tab
    
    def _update_color_button(self, button: QPushButton, color: tuple) -> None:
        """Update a color swatch button's background color."""
        r, g, b = color[:3]
        # Use contrasting border for visibility
        border_color = SWATCH_BORDER_ON_LIGHT if (r + g + b) / 3 > 128 else SWATCH_BORDER_ON_DARK
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({r}, {g}, {b});
                border: 2px solid {border_color};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: {BRAND_GOLD};
            }}
        """)
    
    def _on_choose_fill_color(self) -> None:
        """Open color dialog for fill color selection."""
        current = QColor(*self._fill_color[:3])
        color = QColorDialog.getColor(current, self, "Choose Fill Color")
        if color.isValid():
            self._fill_color = (color.red(), color.green(), color.blue(), 255)
            self._update_color_button(self.fill_color_btn, self._fill_color)
            logger.debug(f"Fill color changed to {self._fill_color[:3]}")
    
    def _on_choose_border_color(self) -> None:
        """Open color dialog for border color selection."""
        current = QColor(*self._border_color[:3])
        color = QColorDialog.getColor(current, self, "Choose Border Color")
        if color.isValid():
            self._border_color = (color.red(), color.green(), color.blue(), 255)
            self._update_color_button(self.border_color_btn, self._border_color)
            logger.debug(f"Border color changed to {self._border_color[:3]}")
    
    def _on_undo(self) -> None:
        """Handle undo button click."""
        logger.info("Undo requested from settings")
        self.undo_requested.emit()
    
    def _on_redo(self) -> None:
        """Handle redo button click."""
        logger.info("Redo requested from settings")
        self.redo_requested.emit()
    
    def _on_rotate(self, degrees: int) -> None:
        """Handle rotation button click."""
        logger.info(f"Rotate {degrees} degrees requested from settings")
        self.rotate_requested.emit(degrees)
    
    def _on_flip_horizontal(self) -> None:
        """Handle horizontal flip button click."""
        logger.info("Flip horizontal requested from settings")
        self.flip_horizontal_requested.emit()
    
    def _on_flip_vertical(self) -> None:
        """Handle vertical flip button click."""
        logger.info("Flip vertical requested from settings")
        self.flip_vertical_requested.emit()
    
    def _on_fill_transparency(self) -> None:
        """Handle fill transparency button click."""
        logger.info(f"Fill transparency requested with color {self._fill_color[:3]}")
        self.fill_transparency_requested.emit(self._fill_color)
    
    def _on_add_border(self) -> None:
        """Handle add border button click."""
        width = self.border_width_spin.value()
        logger.info(f"Add border requested: {width}px, color {self._border_color[:3]}")
        self.add_border_requested.emit(width, self._border_color)
    
    def _on_auto_crop(self) -> None:
        """Handle auto-crop button click."""
        logger.info("Auto-crop requested from settings")
        self.auto_crop_requested.emit()
    
    def _on_add_padding(self) -> None:
        """Handle add padding button click."""
        padding = self.padding_spin.value()
        logger.info(f"Add padding requested: {padding}px")
        self.add_padding_requested.emit(padding)
    
    def _on_center_resize(self) -> None:
        """Handle center & resize button click."""
        size = self.resize_combo.currentData()
        maintain = self.maintain_aspect_cb.isChecked()
        logger.info(f"Center & resize requested: {size}x{size}, maintain_aspect={maintain}")
        self.center_resize_requested.emit(size, maintain)
    
    # ==================== Color Adjustment Handlers ====================
    
    def _on_brightness_changed(self, value: int) -> None:
        """Update brightness value label when slider changes."""
        self.brightness_value_label.setText(f"{value:+d}" if value != 0 else "0")
    
    def _on_contrast_changed(self, value: int) -> None:
        """Update contrast value label when slider changes."""
        self.contrast_value_label.setText(f"{value:+d}" if value != 0 else "0")
    
    def _on_saturation_changed(self, value: int) -> None:
        """Update saturation value label when slider changes."""
        self.saturation_value_label.setText(f"{value:+d}" if value != 0 else "0")
    
    def _on_apply_color_adjustments(self) -> None:
        """Handle apply color adjustments button click."""
        brightness = self.brightness_slider.value()
        contrast = self.contrast_slider.value()
        saturation = self.saturation_slider.value()
        
        if brightness == 0 and contrast == 0 and saturation == 0:
            logger.debug("No color adjustments to apply (all values are 0)")
            return
        
        logger.info(f"Color adjustment requested: B:{brightness:+d}, C:{contrast:+d}, S:{saturation:+d}")
        self.color_adjustment_requested.emit(brightness, contrast, saturation)
        
        # Reset sliders after applying
        self._on_reset_color_sliders()
    
    def _on_reset_color_sliders(self) -> None:
        """Reset all color adjustment sliders to 0."""
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)
        self.saturation_slider.setValue(0)
        logger.debug("Color adjustment sliders reset to 0")
    
    def _on_grayscale(self) -> None:
        """Handle grayscale conversion button click."""
        logger.info("Grayscale conversion requested from settings")
        self.grayscale_requested.emit()
    
    def _create_recent_tab(self) -> QWidget:
        """Create the Recent tab with recently opened files and folders."""
        recent_tab = QWidget()
        layout = QVBoxLayout(recent_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Recent Files group
        files_group = QGroupBox("Recent Files")
        files_layout = QVBoxLayout(files_group)
        files_layout.setContentsMargins(15, 20, 15, 15)
        files_layout.setSpacing(10)
        
        self.recent_files_list = QListWidget()
        self.recent_files_list.setObjectName("recent_list")
        self.recent_files_list.setMaximumHeight(120)
        self.recent_files_list.itemDoubleClicked.connect(self._on_recent_file_clicked)
        self.recent_files_list.setToolTip("Double-click to open file")
        files_layout.addWidget(self.recent_files_list)
        
        files_btn_layout = QHBoxLayout()
        self.clear_files_btn = QPushButton("Clear Files History")
        self.clear_files_btn.setObjectName("clear_btn")
        self.clear_files_btn.setToolTip("Remove all entries from recent files list")
        self.clear_files_btn.clicked.connect(self._on_clear_recent_files)
        files_btn_layout.addWidget(self.clear_files_btn)
        files_btn_layout.addStretch()
        files_layout.addLayout(files_btn_layout)
        
        layout.addWidget(files_group)
        
        # Recent Folders group
        folders_group = QGroupBox("Recent Folders")
        folders_layout = QVBoxLayout(folders_group)
        folders_layout.setContentsMargins(15, 20, 15, 15)
        folders_layout.setSpacing(10)
        
        self.recent_folders_list = QListWidget()
        self.recent_folders_list.setObjectName("recent_list")
        self.recent_folders_list.setMaximumHeight(120)
        self.recent_folders_list.itemDoubleClicked.connect(self._on_recent_folder_clicked)
        self.recent_folders_list.setToolTip("Double-click to scan folder")
        folders_layout.addWidget(self.recent_folders_list)
        
        folders_btn_layout = QHBoxLayout()
        self.clear_folders_btn = QPushButton("Clear Folders History")
        self.clear_folders_btn.setObjectName("clear_btn")
        self.clear_folders_btn.setToolTip("Remove all entries from recent folders list")
        self.clear_folders_btn.clicked.connect(self._on_clear_recent_folders)
        folders_btn_layout.addWidget(self.clear_folders_btn)
        folders_btn_layout.addStretch()
        folders_layout.addLayout(folders_btn_layout)
        
        layout.addWidget(folders_group)
        
        # Clear All button
        clear_all_btn = QPushButton("Clear All History")
        clear_all_btn.setObjectName("action_btn")
        clear_all_btn.setToolTip("Clear both files and folders history")
        clear_all_btn.clicked.connect(self._on_clear_all_history)
        layout.addWidget(clear_all_btn)
        
        # Info label
        info_label = QLabel(
            "Double-click an item to open it.\n"
            "Recent history is saved automatically."
        )
        info_label.setObjectName("desc_label")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        # Populate lists
        self._refresh_recent_lists()
        
        return recent_tab
    
    def _refresh_recent_lists(self) -> None:
        """Refresh the recent files and folders lists."""
        self.recent_files_list.clear()
        self.recent_folders_list.clear()
        
        if self.recent_files_manager is None:
            return
        
        # Populate recent files
        recent_files = self.recent_files_manager.get_recent_files()
        for item in recent_files:
            list_item = QListWidgetItem(f"\U0001F4C4 {item['name']}")  # File icon
            list_item.setData(Qt.ItemDataRole.UserRole, item['path'])
            list_item.setToolTip(item['path'])
            self.recent_files_list.addItem(list_item)
        
        # Populate recent folders
        recent_folders = self.recent_files_manager.get_recent_folders()
        for item in recent_folders:
            list_item = QListWidgetItem(f"\U0001F4C1 {item['name']}")  # Folder icon
            list_item.setData(Qt.ItemDataRole.UserRole, item['path'])
            list_item.setToolTip(item['path'])
            self.recent_folders_list.addItem(list_item)
        
        logger.debug(f"Refreshed recent lists: {len(recent_files)} files, {len(recent_folders)} folders")
    
    def _on_recent_file_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on recent file."""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            logger.info(f"Opening recent file: {file_path}")
            self.open_recent_file_requested.emit(file_path)
    
    def _on_recent_folder_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on recent folder."""
        folder_path = item.data(Qt.ItemDataRole.UserRole)
        if folder_path:
            logger.info(f"Opening recent folder: {folder_path}")
            self.open_recent_folder_requested.emit(folder_path)
    
    def _on_clear_recent_files(self) -> None:
        """Clear recent files history."""
        if self.recent_files_manager:
            self.recent_files_manager.clear_files()
            self._refresh_recent_lists()
            logger.info("Recent files history cleared")
    
    def _on_clear_recent_folders(self) -> None:
        """Clear recent folders history."""
        if self.recent_files_manager:
            self.recent_files_manager.clear_folders()
            self._refresh_recent_lists()
            logger.info("Recent folders history cleared")
    
    def _on_clear_all_history(self) -> None:
        """Clear all recent history."""
        if self.recent_files_manager:
            self.recent_files_manager.clear_history()
            self._refresh_recent_lists()
            logger.info("All recent history cleared")
    
    def update_recent_lists(self) -> None:
        """Public method to refresh recent lists from main app."""
        self._refresh_recent_lists()
    
    def refresh_display(self) -> None:
        """
        Force refresh of the dialog display.
        
        Fixes blank/white screen issue on Windows when dialog is
        closed and reopened.
        """
        # Force style recomputation
        self.style().unpolish(self)
        self.style().polish(self)
        
        # Force update of all child widgets
        self.tabs.update()
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if widget:
                widget.update()
        
        # Repaint the dialog
        self.repaint()
        
        # Process events to ensure immediate display
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
    
    def showEvent(self, event) -> None:
        """Handle show event to ensure proper rendering."""
        super().showEvent(event)
        # Schedule a refresh after the dialog is shown
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(10, self.refresh_display)
    
    def _create_preview_tab(self) -> QWidget:
        """Create the Preview tab with preview enhancements."""
        preview_tab = QWidget()
        layout = QVBoxLayout(preview_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # ==================== Background Options ====================
        bg_group = QGroupBox("Preview Background")
        bg_layout = QVBoxLayout(bg_group)
        bg_layout.setContentsMargins(15, 20, 15, 15)
        bg_layout.setSpacing(10)
        
        bg_desc = QLabel(
            "Choose how transparency is displayed in previews:"
        )
        bg_desc.setWordWrap(True)
        bg_desc.setObjectName("desc_label")
        bg_layout.addWidget(bg_desc)
        
        # Background selector widget
        from ui.preview_utils import BackgroundSelectorWidget
        self.bg_selector = BackgroundSelectorWidget()
        self.bg_selector.background_changed.connect(self._on_background_changed)
        bg_layout.addWidget(self.bg_selector)
        
        layout.addWidget(bg_group)
        
        # ==================== Zoom Controls ====================
        zoom_group = QGroupBox("Zoom Controls")
        zoom_layout = QVBoxLayout(zoom_group)
        zoom_layout.setContentsMargins(15, 20, 15, 15)
        zoom_layout.setSpacing(10)
        
        zoom_desc = QLabel(
            "Adjust preview zoom level (50% - 400%):"
        )
        zoom_desc.setWordWrap(True)
        zoom_desc.setObjectName("desc_label")
        zoom_layout.addWidget(zoom_desc)
        
        # Zoom controls widget
        from ui.preview_utils import ZoomControlsWidget
        self.zoom_controls = ZoomControlsWidget()
        self.zoom_controls.zoom_changed.connect(self._on_zoom_changed)
        zoom_layout.addWidget(self.zoom_controls)
        
        layout.addWidget(zoom_group)
        
        # ==================== Color Palette ====================
        palette_group = QGroupBox("Color Palette")
        palette_layout = QVBoxLayout(palette_group)
        palette_layout.setContentsMargins(15, 20, 15, 15)
        palette_layout.setSpacing(10)
        
        palette_desc = QLabel(
            "Dominant colors from the loaded image (click to copy hex):"
        )
        palette_desc.setWordWrap(True)
        palette_desc.setObjectName("desc_label")
        palette_layout.addWidget(palette_desc)
        
        # Color palette widget
        from ui.preview_utils import ColorPaletteWidget
        self.color_palette = ColorPaletteWidget()
        self.color_palette.color_clicked.connect(self._on_palette_color_clicked)
        palette_layout.addWidget(self.color_palette)
        
        layout.addWidget(palette_group)
        
        # ==================== Context Preview ====================
        context_group = QGroupBox("Icon in Context")
        context_layout = QVBoxLayout(context_group)
        context_layout.setContentsMargins(15, 20, 15, 15)
        context_layout.setSpacing(10)
        
        context_desc = QLabel(
            "Preview how your icon will appear in different contexts:"
        )
        context_desc.setWordWrap(True)
        context_desc.setObjectName("desc_label")
        context_layout.addWidget(context_desc)
        
        # Context preview button
        context_btn = QPushButton("Open Context Preview...")
        context_btn.setToolTip("See icon in taskbar, folder, browser tab, etc.")
        context_btn.clicked.connect(self._on_context_preview)
        context_layout.addWidget(context_btn)
        
        layout.addWidget(context_group)
        
        layout.addStretch()
        
        return preview_tab
    
    def _on_background_changed(self, bg_type: str, color: object) -> None:
        """Handle background type change from preview tab."""
        logger.debug(f"Background changed to: {bg_type}, color: {color}")
        self.background_changed.emit(bg_type, color)
    
    def _on_zoom_changed(self, zoom: int) -> None:
        """Handle zoom level change from preview tab."""
        logger.debug(f"Zoom changed to: {zoom}%")
        self.zoom_changed.emit(zoom)
    
    def _on_palette_color_clicked(self, hex_color: str) -> None:
        """Handle color palette swatch click."""
        logger.debug(f"Palette color clicked: {hex_color}")
        # Color is already copied to clipboard by the widget
    
    def _on_context_preview(self) -> None:
        """Handle context preview button click."""
        logger.debug("Context preview requested")
        self.context_preview_requested.emit()
    
    def update_color_palette(self, image) -> None:
        """
        Update the color palette widget with a new image.
        
        Args:
            image: PIL Image or None to clear
        """
        if hasattr(self, 'color_palette'):
            self.color_palette.set_image(image)
    
    def get_preview_background(self) -> tuple[str, tuple[int, int, int] | None]:
        """
        Get current preview background settings.
        
        Returns:
            Tuple of (background_type, custom_color or None)
        """
        if hasattr(self, 'bg_selector'):
            return self.bg_selector.get_background_settings()
        return ('checkerboard', None)
    
    def get_zoom_level(self) -> int:
        """
        Get current zoom level percentage.
        
        Returns:
            Zoom percentage (50-400)
        """
        if hasattr(self, 'zoom_controls'):
            return self.zoom_controls.get_zoom()
        return 100
    
    # ==================== Info Tab ====================
    
    def _create_info_tab(self) -> QWidget:
        """Create the Info tab with metadata, compression stats, and export history."""
        info_tab = QWidget()
        layout = QVBoxLayout(info_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Use scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 5, 0)
        scroll_layout.setSpacing(10)
        
        # ==================== Compression Statistics ====================
        compression_group = QGroupBox("Last Build Statistics")
        compression_layout = QVBoxLayout(compression_group)
        compression_layout.setContentsMargins(15, 20, 15, 15)
        compression_layout.setSpacing(8)
        
        # Stats labels
        self.compression_file_label = QLabel("File: No recent build")
        self.compression_file_label.setObjectName("desc_label")
        compression_layout.addWidget(self.compression_file_label)
        
        self.compression_size_label = QLabel("Size: --")
        self.compression_size_label.setObjectName("desc_label")
        compression_layout.addWidget(self.compression_size_label)
        
        self.compression_ratio_label = QLabel("Compression: --")
        self.compression_ratio_label.setObjectName("desc_label")
        compression_layout.addWidget(self.compression_ratio_label)
        
        self.compression_savings_label = QLabel("Savings: --")
        self.compression_savings_label.setObjectName("desc_label")
        compression_layout.addWidget(self.compression_savings_label)
        
        # Per-size breakdown
        self.compression_details_label = QLabel("")
        self.compression_details_label.setObjectName("desc_label")
        self.compression_details_label.setWordWrap(True)
        compression_layout.addWidget(self.compression_details_label)
        
        scroll_layout.addWidget(compression_group)
        
        # ==================== Export History ====================
        history_group = QGroupBox("Export History")
        history_layout = QVBoxLayout(history_group)
        history_layout.setContentsMargins(15, 20, 15, 15)
        history_layout.setSpacing(8)
        
        history_desc = QLabel("Recent export operations:")
        history_desc.setObjectName("desc_label")
        history_layout.addWidget(history_desc)
        
        # Export history list
        self.export_history_list = QListWidget()
        self.export_history_list.setObjectName("export_history_list")
        self.export_history_list.setMaximumHeight(180)
        self.export_history_list.setToolTip("Double-click to reveal file in explorer")
        self.export_history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        history_layout.addWidget(self.export_history_list)
        
        # History stats
        self.history_stats_label = QLabel("No exports recorded")
        self.history_stats_label.setObjectName("desc_label")
        history_layout.addWidget(self.history_stats_label)
        
        # History buttons
        history_btn_layout = QHBoxLayout()
        
        refresh_history_btn = QPushButton("Refresh")
        refresh_history_btn.setToolTip("Refresh export history")
        refresh_history_btn.clicked.connect(self._refresh_export_history)
        history_btn_layout.addWidget(refresh_history_btn)
        
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.setToolTip("Clear all export history")
        clear_history_btn.clicked.connect(self._on_clear_history)
        history_btn_layout.addWidget(clear_history_btn)
        
        history_btn_layout.addStretch()
        history_layout.addLayout(history_btn_layout)
        
        scroll_layout.addWidget(history_group)
        
        # ==================== Statistics Summary ====================
        stats_group = QGroupBox("Overall Statistics")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setContentsMargins(15, 20, 15, 15)
        stats_layout.setSpacing(8)
        
        self.total_exports_label = QLabel("Total exports: 0")
        self.total_exports_label.setObjectName("desc_label")
        stats_layout.addWidget(self.total_exports_label)
        
        self.success_rate_label = QLabel("Success rate: --")
        self.success_rate_label.setObjectName("desc_label")
        stats_layout.addWidget(self.success_rate_label)
        
        self.total_bytes_label = QLabel("Total data exported: --")
        self.total_bytes_label.setObjectName("desc_label")
        stats_layout.addWidget(self.total_bytes_label)
        
        scroll_layout.addWidget(stats_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Initial refresh
        self._refresh_export_history()
        
        return info_tab
    
    def _refresh_export_history(self) -> None:
        """Refresh the export history display."""
        self.export_history_list.clear()
        
        if not self.export_history:
            self.history_stats_label.setText("Export history not available")
            return
        
        # Get recent history
        history = self.export_history.get_history(limit=20)
        
        if not history:
            self.history_stats_label.setText("No exports recorded")
            return
        
        # Populate list
        for entry in history:
            status_icon = "✓" if entry.success else "✗"
            item_text = f"{status_icon} {entry.formatted_time} - {entry.filename} ({entry.export_type.upper()})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, entry.output_path)
            item.setToolTip(f"Path: {entry.output_path}\nSize: {entry.formatted_size}\nSizes: {entry.sizes}")
            
            self.export_history_list.addItem(item)
        
        # Update stats
        stats = self.export_history.get_statistics()
        self.history_stats_label.setText(f"Showing {len(history)} of {stats['total_exports']} exports")
        
        self.total_exports_label.setText(f"Total exports: {stats['total_exports']}")
        self.success_rate_label.setText(f"Success rate: {stats['success_rate']:.1f}%")
        
        total_bytes = stats['total_bytes_exported']
        if total_bytes > 0:
            size_str = self._format_bytes(total_bytes)
            self.total_bytes_label.setText(f"Total data exported: {size_str}")
        else:
            self.total_bytes_label.setText("Total data exported: --")
    
    def _on_history_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on history item to reveal in explorer."""
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.reveal_in_explorer_requested.emit(path)
    
    def _on_clear_history(self) -> None:
        """Handle clear history button click."""
        self.clear_export_history_requested.emit()
        self._refresh_export_history()
    
    def update_compression_stats(self, stats: dict | None, output_path: str = "") -> None:
        """
        Update the compression statistics display.
        
        Args:
            stats: Compression statistics dictionary from IconBuilderCore
            output_path: Path to the output file
        """
        self._last_compression_stats = stats
        
        if not stats:
            self.compression_file_label.setText("File: No recent build")
            self.compression_size_label.setText("Size: --")
            self.compression_ratio_label.setText("Compression: --")
            self.compression_savings_label.setText("Savings: --")
            self.compression_details_label.setText("")
            return
        
        # File info
        if output_path:
            from pathlib import Path
            filename = Path(output_path).name
            self.compression_file_label.setText(f"File: {filename}")
        
        # Actual file size
        if 'actual_file_size' in stats:
            size_str = self._format_bytes(stats['actual_file_size'])
            self.compression_size_label.setText(f"Size: {size_str}")
        
        # Compression ratio
        ratio = stats.get('compression_ratio', 0)
        if ratio > 0:
            percent = (1 - ratio) * 100
            self.compression_ratio_label.setText(f"Compression: {percent:.1f}% reduction")
        
        # Savings
        savings = stats.get('savings_bytes', 0)
        if savings > 0:
            savings_str = self._format_bytes(savings)
            self.compression_savings_label.setText(f"Savings: {savings_str}")
        else:
            self.compression_savings_label.setText("Savings: 0 bytes (no PNG compression)")
        
        # Per-size breakdown
        per_size = stats.get('per_size', {})
        if per_size:
            details = []
            for size in sorted(per_size.keys(), reverse=True):
                info = per_size[size]
                comp_type = "PNG" if info['is_png'] else "BMP"
                size_str = self._format_bytes(info['compressed'])
                details.append(f"{size}×{size}: {size_str} ({comp_type})")
            self.compression_details_label.setText("  |  ".join(details))
    
    def _format_bytes(self, size_bytes: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                if unit == 'B':
                    return f"{size_bytes} {unit}"
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _create_automation_tab(self) -> QWidget:
        """Create the Automation tab with batch processing and watch folder controls."""
        automation_tab = QWidget()
        layout = QVBoxLayout(automation_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Use scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 5, 0)
        scroll_layout.setSpacing(10)
        
        # ==================== Batch Processing ====================
        batch_group = QGroupBox("Batch Processing")
        batch_layout = QVBoxLayout(batch_group)
        batch_layout.setContentsMargins(15, 20, 15, 15)
        batch_layout.setSpacing(8)
        
        batch_desc = QLabel(
            "Process multiple images to ICO in one batch.\n"
            "Each source file becomes a separate ICO file."
        )
        batch_desc.setObjectName("desc_label")
        batch_desc.setWordWrap(True)
        batch_layout.addWidget(batch_desc)
        
        # Batch job list
        self.batch_list = QListWidget()
        self.batch_list.setObjectName("batch_list")
        self.batch_list.setMaximumHeight(100)
        self.batch_list.setToolTip("Queue of files to process")
        batch_layout.addWidget(self.batch_list)
        
        # Batch stats label
        self.batch_stats_label = QLabel("0 files in queue")
        self.batch_stats_label.setObjectName("desc_label")
        batch_layout.addWidget(self.batch_stats_label)
        
        # Batch buttons row 1
        batch_btn_row1 = QHBoxLayout()
        
        self.batch_add_files_btn = QPushButton("Add Files")
        self.batch_add_files_btn.setToolTip("Add files to batch queue")
        self.batch_add_files_btn.clicked.connect(self._on_batch_add_files)
        batch_btn_row1.addWidget(self.batch_add_files_btn)
        
        self.batch_add_folder_btn = QPushButton("Add Folder")
        self.batch_add_folder_btn.setToolTip("Add all images from a folder")
        self.batch_add_folder_btn.clicked.connect(self._on_batch_add_folder)
        batch_btn_row1.addWidget(self.batch_add_folder_btn)
        
        self.batch_clear_btn = QPushButton("Clear Queue")
        self.batch_clear_btn.setToolTip("Remove all pending jobs")
        self.batch_clear_btn.clicked.connect(self._on_batch_clear)
        batch_btn_row1.addWidget(self.batch_clear_btn)
        
        batch_layout.addLayout(batch_btn_row1)
        
        # Batch buttons row 2
        batch_btn_row2 = QHBoxLayout()
        
        self.batch_process_btn = QPushButton("Process All")
        self.batch_process_btn.setObjectName("action_btn")
        self.batch_process_btn.setToolTip("Start processing all queued files")
        self.batch_process_btn.clicked.connect(self._on_batch_process)
        batch_btn_row2.addWidget(self.batch_process_btn)
        
        self.batch_cancel_btn = QPushButton("Cancel")
        self.batch_cancel_btn.setEnabled(False)
        self.batch_cancel_btn.setToolTip("Cancel batch processing")
        self.batch_cancel_btn.clicked.connect(self._on_batch_cancel)
        batch_btn_row2.addWidget(self.batch_cancel_btn)
        
        batch_layout.addLayout(batch_btn_row2)
        
        scroll_layout.addWidget(batch_group)
        
        # ==================== Watch Folder ====================
        watch_group = QGroupBox("Watch Folder Mode")
        watch_layout = QVBoxLayout(watch_group)
        watch_layout.setContentsMargins(15, 20, 15, 15)
        watch_layout.setSpacing(8)
        
        watch_desc = QLabel(
            "Automatically process new images added to a folder.\n"
            "Icons are created in the output folder."
        )
        watch_desc.setObjectName("desc_label")
        watch_desc.setWordWrap(True)
        watch_layout.addWidget(watch_desc)
        
        # Input folder
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Input:"))
        self.watch_input_edit = QLineEdit()
        self.watch_input_edit.setToolTip("Folder to monitor for new image files")
        self.watch_input_edit.setPlaceholderText("Folder to watch for new images...")
        self.watch_input_edit.setObjectName("folder_edit")
        input_row.addWidget(self.watch_input_edit)
        self.watch_input_btn = QPushButton("...")
        self.watch_input_btn.setToolTip("Browse for input folder")
        self.watch_input_btn.setMaximumWidth(30)
        self.watch_input_btn.clicked.connect(self._on_select_watch_input)
        input_row.addWidget(self.watch_input_btn)
        watch_layout.addLayout(input_row)
        
        # Output folder
        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Output:"))
        self.watch_output_edit = QLineEdit()
        self.watch_output_edit.setToolTip("Destination folder for generated ICO files")
        self.watch_output_edit.setPlaceholderText("Folder for generated ICO files...")
        self.watch_output_edit.setObjectName("folder_edit")
        output_row.addWidget(self.watch_output_edit)
        self.watch_output_btn = QPushButton("...")
        self.watch_output_btn.setToolTip("Browse for output folder")
        self.watch_output_btn.setMaximumWidth(30)
        self.watch_output_btn.clicked.connect(self._on_select_watch_output)
        output_row.addWidget(self.watch_output_btn)
        watch_layout.addLayout(output_row)
        
        # Watch status
        self.watch_status_label = QLabel("\u23F9 Not watching")
        self.watch_status_label.setObjectName("status_label")
        watch_layout.addWidget(self.watch_status_label)
        
        # Watch buttons
        watch_btn_row = QHBoxLayout()
        
        self.watch_start_btn = QPushButton("Start Watching")
        self.watch_start_btn.setObjectName("action_btn")
        self.watch_start_btn.setToolTip("Start watching the input folder")
        self.watch_start_btn.clicked.connect(self._on_watch_start)
        watch_btn_row.addWidget(self.watch_start_btn)
        
        self.watch_stop_btn = QPushButton("Stop Watching")
        self.watch_stop_btn.setEnabled(False)
        self.watch_stop_btn.setToolTip("Stop watching")
        self.watch_stop_btn.clicked.connect(self._on_watch_stop)
        watch_btn_row.addWidget(self.watch_stop_btn)
        
        watch_layout.addLayout(watch_btn_row)
        
        scroll_layout.addWidget(watch_group)
        
        # ==================== Custom Presets ====================
        preset_group = QGroupBox("Custom Presets")
        preset_layout = QVBoxLayout(preset_group)
        preset_layout.setContentsMargins(15, 20, 15, 15)
        preset_layout.setSpacing(8)
        
        preset_desc = QLabel(
            "Save your frequently used size configurations as presets."
        )
        preset_desc.setObjectName("desc_label")
        preset_desc.setWordWrap(True)
        preset_layout.addWidget(preset_desc)
        
        # Preset dropdown
        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Load Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.setToolTip("Select a saved preset to load")
        self.preset_combo.setObjectName("preset_combo")
        self.preset_combo.setMinimumWidth(150)
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        preset_row.addWidget(self.preset_combo)
        preset_row.addStretch()
        preset_layout.addLayout(preset_row)
        
        # Save new preset
        save_row = QHBoxLayout()
        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setToolTip("Enter a name to save current size selections as a preset")
        self.preset_name_edit.setPlaceholderText("New preset name...")
        self.preset_name_edit.setObjectName("preset_name_edit")
        save_row.addWidget(self.preset_name_edit)
        
        self.preset_save_btn = QPushButton("Save Current")
        self.preset_save_btn.setToolTip("Save current size selection as preset")
        self.preset_save_btn.clicked.connect(self._on_preset_save)
        save_row.addWidget(self.preset_save_btn)
        
        self.preset_delete_btn = QPushButton("Delete")
        self.preset_delete_btn.setToolTip("Delete selected preset")
        self.preset_delete_btn.clicked.connect(self._on_preset_delete)
        save_row.addWidget(self.preset_delete_btn)
        
        preset_layout.addLayout(save_row)
        
        scroll_layout.addWidget(preset_group)
        
        # ==================== Project Files ====================
        project_group = QGroupBox("Project Files")
        project_layout = QVBoxLayout(project_group)
        project_layout.setContentsMargins(15, 20, 15, 15)
        project_layout.setSpacing(8)
        
        project_desc = QLabel(
            "Save and load complete project state (.rnvicon files).\n"
            "Includes loaded images and all settings."
        )
        project_desc.setObjectName("desc_label")
        project_desc.setWordWrap(True)
        project_layout.addWidget(project_desc)
        
        # Project buttons
        project_btn_row = QHBoxLayout()
        
        self.project_new_btn = QPushButton("New Project")
        self.project_new_btn.setToolTip("Clear and start a new project")
        self.project_new_btn.clicked.connect(self._on_project_new)
        project_btn_row.addWidget(self.project_new_btn)
        
        self.project_save_btn = QPushButton("Save Project")
        self.project_save_btn.setToolTip("Save current project (Ctrl+S)")
        self.project_save_btn.clicked.connect(self._on_project_save)
        project_btn_row.addWidget(self.project_save_btn)
        
        self.project_load_btn = QPushButton("Load Project")
        self.project_load_btn.setToolTip("Load a saved project")
        self.project_load_btn.clicked.connect(self._on_project_load)
        project_btn_row.addWidget(self.project_load_btn)
        
        project_layout.addLayout(project_btn_row)
        
        scroll_layout.addWidget(project_group)
        
        # ==================== Session Restore ====================
        session_group = QGroupBox("Session Settings")
        session_layout = QVBoxLayout(session_group)
        session_layout.setContentsMargins(15, 20, 15, 15)
        session_layout.setSpacing(8)
        
        self.restore_session_cb = QCheckBox("Restore last session on startup")
        self.restore_session_cb.setToolTip("Automatically reload your last working state when the app starts")
        self.restore_session_cb.setChecked(True)
        self.restore_session_cb.stateChanged.connect(self._on_session_settings_changed)
        session_layout.addWidget(self.restore_session_cb)
        
        self.auto_save_cb = QCheckBox("Auto-save project periodically")
        self.auto_save_cb.setToolTip("Automatically save a backup of your project")
        self.auto_save_cb.setChecked(True)
        self.auto_save_cb.stateChanged.connect(self._on_session_settings_changed)
        session_layout.addWidget(self.auto_save_cb)
        
        scroll_layout.addWidget(session_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Populate preset combo
        self._refresh_preset_combo()
        
        return automation_tab
    
    def _on_session_settings_changed(self) -> None:
        """Emit session settings changed signal."""
        self.session_settings_changed.emit(
            self.restore_session_cb.isChecked(),
            self.auto_save_cb.isChecked()
        )
    
    # ==================== Automation Tab Handlers ====================
    
    def _on_batch_add_files(self) -> None:
        """Handle batch add files button."""
        logger.debug("Batch add files requested")
        self.batch_add_files_requested.emit()
    
    def _on_batch_add_folder(self) -> None:
        """Handle batch add folder button."""
        logger.debug("Batch add folder requested")
        self.batch_add_folder_requested.emit()
    
    def _on_batch_clear(self) -> None:
        """Handle batch clear button."""
        logger.debug("Batch clear requested")
        self.batch_clear_requested.emit()
    
    def _on_batch_process(self) -> None:
        """Handle batch process button."""
        logger.debug("Batch process requested")
        self.batch_process_requested.emit()
    
    def _on_batch_cancel(self) -> None:
        """Handle batch cancel button."""
        logger.debug("Batch cancel requested")
        self.batch_cancel_requested.emit()
    
    def _on_select_watch_input(self) -> None:
        """Select input folder for watch mode."""
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder to Watch")
        if folder:
            self.watch_input_edit.setText(folder)
    
    def _on_select_watch_output(self) -> None:
        """Select output folder for watch mode."""
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.watch_output_edit.setText(folder)
    
    def _on_watch_start(self) -> None:
        """Handle watch start button."""
        input_folder = self.watch_input_edit.text().strip()
        output_folder = self.watch_output_edit.text().strip()
        
        if not input_folder or not output_folder:
            DialogHelper.show_warning(
                self,
                "Please select both input and output folders.",
                "Missing Folders"
            )
            return
        
        logger.debug(f"Watch start requested: {input_folder} -> {output_folder}")
        self.watch_start_requested.emit(input_folder, output_folder)
    
    def _on_watch_stop(self) -> None:
        """Handle watch stop button."""
        logger.debug("Watch stop requested")
        self.watch_stop_requested.emit()
    
    def update_watch_status(self, is_watching: bool, folder: str = "") -> None:
        """Update watch status display."""
        self._is_watching = is_watching
        if is_watching:
            self.watch_status_label.setText(f"\u25B6 Watching: {folder}")
            self.watch_status_label.setStyleSheet(f"color: {STATUS_ACTIVE_COLOR};")
            self.watch_start_btn.setEnabled(False)
            self.watch_stop_btn.setEnabled(True)
            self.watch_input_edit.setEnabled(False)
            self.watch_output_edit.setEnabled(False)
            self.watch_input_btn.setEnabled(False)
            self.watch_output_btn.setEnabled(False)
        else:
            self.watch_status_label.setText("\u23F9 Not watching")
            self.watch_status_label.setStyleSheet("")
            self.watch_start_btn.setEnabled(True)
            self.watch_stop_btn.setEnabled(False)
            self.watch_input_edit.setEnabled(True)
            self.watch_output_edit.setEnabled(True)
            self.watch_input_btn.setEnabled(True)
            self.watch_output_btn.setEnabled(True)
    
    def _on_preset_selected(self, preset_name: str) -> None:
        """Handle preset selection from dropdown."""
        if preset_name and preset_name != "-- Select Preset --":
            logger.debug(f"Preset selected: {preset_name}")
            self.preset_selected.emit(preset_name)
    
    def _on_preset_save(self) -> None:
        """Handle save preset button."""
        name = self.preset_name_edit.text().strip()
        if not name:
            DialogHelper.show_warning(
                self,
                "Please enter a name for the preset.",
                "Name Required"
            )
            return
        logger.debug(f"Preset save requested: {name}")
        self.preset_save_requested.emit(name)
        self.preset_name_edit.clear()
    
    def _on_preset_delete(self) -> None:
        """Handle delete preset button."""
        name = self.preset_combo.currentText()
        if name and name != "-- Select Preset --":
            logger.debug(f"Preset delete requested: {name}")
            self.preset_delete_requested.emit(name)
    
    def _refresh_preset_combo(self) -> None:
        """Refresh the preset dropdown with current presets."""
        self.preset_combo.clear()
        self.preset_combo.addItem("-- Select Preset --")
        
        if self.preset_manager:
            presets = self.preset_manager.list_presets()
            for preset in presets:
                self.preset_combo.addItem(preset.name)
    
    def update_preset_list(self) -> None:
        """Public method to refresh preset list."""
        self._refresh_preset_combo()
    
    def _on_project_new(self) -> None:
        """Handle new project button."""
        logger.debug("Project new requested")
        self.project_new_requested.emit()
    
    def _on_project_save(self) -> None:
        """Handle save project button."""
        logger.debug("Project save requested")
        self.project_save_requested.emit()
    
    def _on_project_load(self) -> None:
        """Handle load project button."""
        logger.debug("Project load requested")
        self.project_load_requested.emit()
    
    def update_batch_list(self, jobs: list) -> None:
        """
        Update the batch job list display.
        
        Args:
            jobs: List of BatchJob objects
        """
        self.batch_list.clear()
        for job in jobs:
            from pathlib import Path
            name = Path(job.source_path).name
            status = job.status.value
            item = QListWidgetItem(f"{name} [{status}]")
            self.batch_list.addItem(item)
        
        pending = len([j for j in jobs if j.status.value == 'pending'])
        completed = len([j for j in jobs if j.status.value == 'completed'])
        failed = len([j for j in jobs if j.status.value == 'failed'])
        
        self.batch_stats_label.setText(
            f"{len(jobs)} total | {pending} pending | {completed} done | {failed} failed"
        )
    
    def set_batch_processing(self, is_processing: bool) -> None:
        """Update UI for batch processing state."""
        self.batch_add_files_btn.setEnabled(not is_processing)
        self.batch_add_folder_btn.setEnabled(not is_processing)
        self.batch_clear_btn.setEnabled(not is_processing)
        self.batch_process_btn.setEnabled(not is_processing)
        self.batch_cancel_btn.setEnabled(is_processing)
    
    def get_session_settings(self) -> dict:
        """Get session settings."""
        return {
            'restore_session': self.restore_session_cb.isChecked(),
            'auto_save': self.auto_save_cb.isChecked()
        }
    
    def set_session_settings(self, settings: dict) -> None:
        """Set session settings."""
        self.restore_session_cb.setChecked(settings.get('restore_session', True))
        self.auto_save_cb.setChecked(settings.get('auto_save', True))
    
    def _build_stylesheet(self, c: dict) -> str:
        """
        Build the settings dialog stylesheet from a theme colors dictionary.
        
        Args:
            c: Color dictionary from get_theme_colors()
            
        Returns:
            Complete CSS stylesheet string for the dialog
        """
        return f"""
            /* ========================================
               GOLD BRAND COLOR THEME
               ======================================== */
            
            QDialog {{
                background-color: {c['dialog_bg']};
                color: {c['text_primary']};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {c['border_default']};
                background-color: {c['panel_bg']};
                border-radius: 4px;
            }}
            
            QTabBar::tab {{
                background-color: {c['tab_bg']};
                color: {c['text_primary']};
                padding: 8px 0px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid {c['border_default']};
                border-bottom: none;
                min-width: 92px;
                max-width: 92px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {c['tab_selected_bg']};
                color: {c['text_accent']};
                border-bottom: 2px solid {c['tab_indicator']};
            }}
            
            QTabBar::tab:hover {{
                background-color: {c['tab_hover_bg']};
                color: {c['text_accent']};
            }}
            
            QTabBar::scroller {{
                width: 0px;
            }}
            
            QTabBar QToolButton {{
                width: 0px;
                height: 0px;
            }}
            
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {c['border_default']};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: {c['panel_bg']};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {c['text_accent']};
            }}
            
            /* Checkboxes - Gold theme */
            QCheckBox {{
                color: {c['text_primary']};
                spacing: 8px;
            }}
            
            QCheckBox:hover {{
                color: {c['text_accent']};
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {c['checkbox_border']};
                border-radius: 3px;
                background-color: {c['checkbox_bg']};
            }}
            
            QCheckBox::indicator:unchecked:hover {{
                border-color: {c['checkbox_hover_border']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {c['checkbox_checked_bg']};
                border-color: {c['checkbox_checked_border']};
            }}
            
            QCheckBox::indicator:checked:hover {{
                background-color: {BRAND_GOLD_DARK};
                border-color: {BRAND_GOLD_DARK};
            }}
            
            /* Buttons - Gold hover */
            QPushButton {{
                background-color: {c['button_bg']};
                color: {c['button_text']};
                border: 1px solid {c['button_border']};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: normal;
            }}
            
            QPushButton:hover {{
                background-color: {c['button_hover_bg']};
                border-color: {c['button_hover_border']};
                color: {c['button_hover_text']};
            }}
            
            QPushButton:pressed {{
                background-color: {c['button_pressed_bg']};
                border-color: {BRAND_GOLD_DARK};
                color: {c['button_pressed_text']};
            }}
            
            /* Accent buttons (Export PNG, Analyzer, ICNS Export) */
            QPushButton[objectName="export_png_btn"],
            QPushButton[objectName="analyzer_btn"],
            QPushButton[objectName="export_icns_btn"] {{
                background-color: {c['accent_button_bg']};
                color: {c['accent_button_text']};
                border: 1px solid {c['accent_button_border']};
                padding: 10px 20px;
                font-weight: bold;
            }}
            
            QPushButton[objectName="export_png_btn"]:hover,
            QPushButton[objectName="analyzer_btn"]:hover,
            QPushButton[objectName="export_icns_btn"]:hover {{
                background-color: {c['accent_button_hover_bg']};
                color: {c['accent_button_text']};
                border-color: {c['accent_button_border']};
            }}
            
            QPushButton[objectName="export_png_btn"]:pressed,
            QPushButton[objectName="analyzer_btn"]:pressed,
            QPushButton[objectName="export_icns_btn"]:pressed {{
                background-color: {c['accent_button_pressed_bg']};
                color: {c['accent_button_pressed_text']};
            }}
            
            /* Platform Export buttons */
            QPushButton[objectName="platform_btn"] {{
                background-color: {c['platform_btn_bg']};
                color: {c['accent_button_text']};
                border: 1px solid {c['button_border']};
                padding: 8px 16px;
                font-weight: bold;
                text-align: left;
            }}
            
            QPushButton[objectName="platform_btn"]:hover {{
                background-color: {c['platform_btn_hover_bg']};
                color: {c['accent_button_text']};
                border-color: {c['button_hover_border']};
            }}
            
            QPushButton[objectName="platform_btn"]:pressed {{
                background-color: {c['button_pressed_bg']};
                color: {c['accent_button_pressed_text']};
            }}
            
            /* File size estimate label */
            QLabel[objectName="size_label"] {{
                color: {c['text_accent']};
                font-size: 13px;
                font-weight: bold;
            }}
            
            QLabel {{
                color: {c['text_primary']};
            }}
            
            /* Description/info labels */
            QLabel[objectName="desc_label"] {{
                color: {c['text_secondary']};
                font-size: 11px;
            }}
            
            /* Monospace labels (shortcuts) */
            QLabel[objectName="mono_label"] {{
                color: {c['text_secondary']};
                font-size: 10px;
                font-family: monospace;
            }}
            
            /* Title label */
            QLabel[objectName="title_label"] {{
                color: {c['text_accent']};
                font-size: 20px;
                font-weight: bold;
            }}
            
            /* Version label */
            QLabel[objectName="version_label"] {{
                color: {c['text_muted']};
                font-size: 12px;
            }}
            
            /* Author label */
            QLabel[objectName="author_label"] {{
                color: {BRAND_GOLD_DARK};
                font-size: 10px;
            }}
            
            /* SpinBox styling */
            QSpinBox {{
                background-color: {c['input_bg']};
                color: {c['text_primary']};
                border: 1px solid {c['input_border']};
                padding: 5px 10px;
                border-radius: 3px;
                min-width: 60px;
                selection-background-color: {c['selected_bg']};
                selection-color: {c['text_on_accent']};
            }}
            
            QSpinBox:focus {{
                border-color: {c['border_focus']};
            }}
            
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {c['pressed_bg']};
                border: none;
                width: 16px;
            }}
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {c['selected_bg']};
            }}
            
            /* ComboBox styling */
            QComboBox {{
                background-color: {c['input_bg']};
                color: {c['text_primary']};
                border: 1px solid {c['input_border']};
                padding: 5px 10px;
                border-radius: 3px;
                min-width: 100px;
                selection-background-color: {c['selected_bg']};
                selection-color: {c['text_on_accent']};
            }}
            
            QComboBox:focus {{
                border-color: {c['border_focus']};
            }}
            
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {c['input_bg']};
                color: {c['text_primary']};
                selection-background-color: {c['selected_bg']};
                selection-color: {c['text_on_accent']};
                border: 1px solid {c['input_border']};
                outline: none;
            }}
            
            QComboBox QAbstractItemView::item {{
                padding: 4px 8px;
                min-height: 20px;
            }}
            
            QComboBox QAbstractItemView::item:hover {{
                background-color: {c['list_hover_bg']};
                color: {c['text_accent']};
            }}
            
            QComboBox QAbstractItemView::item:selected {{
                background-color: {c['list_selected_bg']};
                color: {c['text_on_accent']};
            }}
            
            /* Generic QListWidget styling */
            QListWidget {{
                background-color: {c['input_bg']};
                color: {c['text_primary']};
                border: 1px solid {c['input_border']};
                border-radius: 4px;
            }}
            
            QListWidget::item {{
                padding: 4px 8px;
            }}
            
            QListWidget::item:hover {{
                background-color: {c['list_hover_bg']};
                color: {c['text_accent']};
            }}
            
            QListWidget::item:selected {{
                background-color: {c['list_selected_bg']};
                color: {c['text_on_accent']};
            }}
            
            /* QLineEdit styling */
            QLineEdit {{
                background-color: {c['input_bg']};
                color: {c['text_primary']};
                border: 1px solid {c['input_border']};
                padding: 6px 10px;
                border-radius: 3px;
                selection-background-color: {c['selected_bg']};
                selection-color: {c['text_on_accent']};
            }}
            
            QLineEdit:focus {{
                border-color: {c['border_focus']};
            }}
            
            QLineEdit::placeholder {{
                color: {c['text_disabled']};
            }}
            
            /* Slider styling for Adjust tab */
            QSlider::groove:horizontal {{
                border: 1px solid {c['button_border']};
                height: 6px;
                background: {c['button_bg']};
                border-radius: 3px;
            }}
            
            QSlider::handle:horizontal {{
                background: {c['text_accent']};
                border: 1px solid {c['border_focus']};
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            
            QSlider::handle:horizontal:hover {{
                background: {c['accent_button_border']};
            }}
            
            QSlider::sub-page:horizontal {{
                background: {c['text_accent']};
                border-radius: 3px;
            }}
            
            /* Action buttons in Adjust tab */
            QPushButton[objectName="action_btn"] {{
                background-color: {c['accent_button_bg']};
                color: {c['accent_button_text']};
                border: 1px solid {c['accent_button_border']};
                padding: 10px 20px;
                font-weight: bold;
            }}
            
            QPushButton[objectName="action_btn"]:hover {{
                background-color: {c['accent_button_hover_bg']};
                color: {c['accent_button_text']};
                border-color: {c['accent_button_border']};
            }}
            
            QPushButton[objectName="action_btn"]:pressed {{
                background-color: {c['accent_button_pressed_bg']};
                color: {c['accent_button_pressed_text']};
            }}
            
            /* Small buttons in Adjust tab */
            QPushButton[objectName="small_btn"] {{
                background-color: {c['button_bg']};
                color: {c['button_text']};
                border: 1px solid {c['button_border']};
                padding: 5px 12px;
                border-radius: 3px;
                font-size: 11px;
            }}
            
            QPushButton[objectName="small_btn"]:hover {{
                background-color: {c['button_hover_bg']};
                border-color: {c['border_focus']};
                color: {c['button_hover_text']};
            }}
            
            QPushButton[objectName="small_btn"]:pressed {{
                background-color: {c['button_pressed_bg']};
                color: {c['text_on_accent']};
            }}
            
            /* Info label styling */
            QLabel[objectName="info_label"] {{
                color: {c['text_secondary']};
                font-size: 11px;
            }}
            
            /* Recent files list styling */
            QListWidget[objectName="recent_list"] {{
                background-color: {c['input_bg']};
                color: {c['text_primary']};
                border: 1px solid {c['input_border']};
                border-radius: 4px;
                padding: 5px;
            }}
            
            QListWidget[objectName="recent_list"]::item {{
                padding: 5px 8px;
                border-radius: 3px;
            }}
            
            QListWidget[objectName="recent_list"]::item:hover {{
                background-color: {c['list_hover_bg']};
                color: {c['text_accent']};
            }}
            
            QListWidget[objectName="recent_list"]::item:selected {{
                background-color: {c['list_selected_bg']};
                color: {c['text_on_accent']};
            }}
            
            /* Clear history buttons */
            QPushButton[objectName="clear_btn"] {{
                background-color: {c['clear_btn_bg']};
                color: {c['button_text']};
                border: 1px solid {c['input_border']};
                padding: 6px 12px;
                font-size: 11px;
            }}
            
            QPushButton[objectName="clear_btn"]:hover {{
                background-color: {c['button_hover_bg']};
                color: {c['button_hover_text']};
                border-color: {c['border_focus']};
            }}
            
            QPushButton[objectName="clear_btn"]:pressed {{
                background-color: {c['button_pressed_bg']};
                color: {c['text_on_accent']};
                border-color: {BRAND_GOLD_DARK};
            }}
        """

    def _apply_theme(self, is_dark: bool = True) -> None:
        """Apply theme styling to dialog using centralized color definitions."""
        colors = get_theme_colors(is_dark=is_dark)
        self.setStyleSheet(self._build_stylesheet(colors))
        
        # Propagate theme to child widgets with their own stylesheets
        if hasattr(self, 'color_palette'):
            self.color_palette.apply_theme(is_dark=is_dark)
        if hasattr(self, 'zoom_controls'):
            self.zoom_controls.apply_theme(is_dark=is_dark)
        if hasattr(self, 'bg_selector'):
            self.bg_selector.apply_theme(is_dark=is_dark)
    
    def apply_theme_from_manager(self, theme_name: str) -> None:
        """
        Apply theme based on theme manager state.
        
        Args:
            theme_name: 'dark', 'light', or 'image'
        """
        is_dark = theme_name in ('dark', 'image')
        
        # Only reapply if theme actually changed
        if hasattr(self, '_current_theme_is_dark') and self._current_theme_is_dark == is_dark:
            return
        
        logger.debug(f"Settings dialog applying theme: {theme_name} (is_dark={is_dark})")
        self._current_theme_is_dark = is_dark
        self._apply_theme(is_dark)
        
        # Simple update - no need for expensive unpolish/polish loop
        # The setStyleSheet call in _apply_theme already handles this
        self.update()
    
    # ==================== Size Selection Methods ====================
    
    def _on_size_changed(self) -> None:
        """Handle size checkbox state change."""
        self.settings_changed.emit()
    
    def get_selected_sizes(self) -> list[int]:
        """
        Get list of currently selected sizes.
        
        Returns:
            List of selected sizes in descending order
        """
        selected = [size for size, cb in self.size_checkboxes.items() if cb.isChecked()]
        return sorted(selected, reverse=True)
    
    def set_selected_sizes(self, sizes: list[int]) -> None:
        """
        Set which sizes are selected.
        
        Args:
            sizes: List of sizes to select
        """
        for size, cb in self.size_checkboxes.items():
            cb.setChecked(size in sizes)
    
    def _select_all_sizes(self) -> None:
        """Select all size checkboxes."""
        logger.debug("Preset: All sizes")
        for cb in self.size_checkboxes.values():
            cb.setChecked(True)
    
    def _select_none(self) -> None:
        """Deselect all size checkboxes."""
        logger.debug("Preset: None")
        for cb in self.size_checkboxes.values():
            cb.setChecked(False)
    
    def _select_favicon_preset(self) -> None:
        """Select favicon sizes only (16, 32, 48)."""
        logger.debug("Preset: Favicon")
        favicon_sizes = {16, 32, 48}
        for size, cb in self.size_checkboxes.items():
            cb.setChecked(size in favicon_sizes)
    
    def _select_windows_preset(self) -> None:
        """Select Windows icon sizes (16, 32, 48, 256)."""
        logger.debug("Preset: Windows")
        windows_sizes = {16, 32, 48, 256}
        for size, cb in self.size_checkboxes.items():
            cb.setChecked(size in windows_sizes)
    
    def _select_macos_preset(self) -> None:
        """Select macOS icon sizes (16, 32, 128, 256)."""
        logger.debug("Preset: macOS")
        macos_sizes = {16, 32, 128, 256}
        for size, cb in self.size_checkboxes.items():
            cb.setChecked(size in macos_sizes)
    
    # ==================== Export Methods ====================
    
    def _on_export_png(self) -> None:
        """Handle PNG Set export request."""
        logger.debug("Export PNG Set requested from settings")
        self.export_png_requested.emit()
    
    def _on_analyze_ico(self) -> None:
        """Handle ICO analysis request."""
        logger.debug("ICO analysis requested from settings")
        self.analyze_ico_requested.emit()
    
    def _on_export_icns(self) -> None:
        """Handle macOS .icns export request."""
        logger.debug("Export .icns requested from settings")
        self.export_icns_requested.emit()
    
    # ==================== Platform Export Methods ====================
    
    def _on_export_favicon(self) -> None:
        """Handle Favicon Package export request."""
        logger.debug("Export Favicon Package requested from settings")
        self.export_favicon_requested.emit()
    
    def _on_export_android(self) -> None:
        """Handle Android Icons export request."""
        logger.debug("Export Android Icons requested from settings")
        self.export_android_requested.emit()
    
    def _on_export_ios(self) -> None:
        """Handle iOS App Icons export request."""
        logger.debug("Export iOS App Icons requested from settings")
        self.export_ios_requested.emit()
    
    def _on_template_changed(self, text: str) -> None:
        """Handle filename template input changes."""
        # Update preview
        preview = self._generate_template_preview(text, 256)
        self.template_preview.setText(f"Preview: {preview}.png")
        # Emit signal
        self.filename_template_changed.emit(text)
        logger.debug(f"Filename template changed: {text}")
    
    def _generate_template_preview(self, template: str, size: int) -> str:
        """
        Generate a preview filename from template.
        
        Args:
            template: Template string with placeholders
            size: Example size for preview
            
        Returns:
            Preview filename (without extension)
        """
        from datetime import datetime
        
        if not template:
            template = "icon_{size}"
        
        now = datetime.now()
        result = template
        result = result.replace("{name}", "myicon")
        result = result.replace("{size}", str(size))
        result = result.replace("{date}", now.strftime("%Y%m%d"))
        result = result.replace("{time}", now.strftime("%H%M%S"))
        
        # Sanitize filename (remove invalid chars)
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            result = result.replace(char, '_')
        
        return result
    
    def get_filename_template(self) -> str:
        """
        Get the current filename template string.
        
        Returns:
            Template string with placeholders
        """
        if hasattr(self, 'template_input'):
            return self.template_input.text() or "icon_{size}"
        return "icon_{size}"
    
    def update_file_size_estimate(self, estimate_info: dict | None) -> None:
        """
        Update the file size estimate display.
        
        Args:
            estimate_info: Dictionary from IconBuilderCore.estimate_ico_size() or None
        """
        if not hasattr(self, 'file_size_label'):
            return
        
        if estimate_info is None:
            self.file_size_label.setText("Load images to see estimate")
            self.file_size_details.setText("")
            return
        
        total = estimate_info.get('total_kb', '0 KB')
        count = estimate_info.get('image_count', 0)
        
        self.file_size_label.setText(f"Estimated ICO size: {total}")
        
        # Build details string
        # breakdown is dict[int, int] mapping size -> bytes
        breakdown = estimate_info.get('breakdown', {})
        if breakdown:
            details_parts = []
            # Sort by size descending and take first 4
            sorted_sizes = sorted(breakdown.keys(), reverse=True)[:4]
            for size in sorted_sizes:
                size_bytes = breakdown[size]
                size_kb = size_bytes / 1024
                if size_kb < 1:
                    kb_str = f"{size_bytes} B"
                else:
                    kb_str = f"{size_kb:.1f} KB"
                details_parts.append(f"{size}x{size}: {kb_str}")
            if len(breakdown) > 4:
                details_parts.append(f"...+{len(breakdown) - 4} more")
            self.file_size_details.setText(" | ".join(details_parts))
        else:
            self.file_size_details.setText(f"{count} images included")


# ==================== Settings Button Widget ====================

class SettingsButton(QPushButton):
    """
    Settings gear button with three-state images (base, hover, pressed).
    
    Designed to be placed on the right side of the options row.
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize settings button."""
        super().__init__(parent)
        
        # Image paths
        from utils.config import BUTTON_IMAGES_DIR
        self.base_image = BUTTON_IMAGES_DIR / "settings_gear_base.png"
        self.hover_image = BUTTON_IMAGES_DIR / "settings_gear_hover.png"
        self.pressed_image = BUTTON_IMAGES_DIR / "settings_gear_pressed.png"
        
        # Store pixmaps
        self.base_pixmap: QPixmap | None = None
        self.hover_pixmap: QPixmap | None = None
        self.pressed_pixmap: QPixmap | None = None
        
        # State tracking
        self._is_hovered = False
        self._is_pressed = False
        
        self.setToolTip("Settings (Sizes, Export, Adjust, Preview)")
        self.setFixedSize(48, 48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Load images
        self._load_images()
        
        # Set initial icon
        if self.base_pixmap:
            self.setIcon(QIcon(self.base_pixmap))
            self.setIconSize(QSize(44, 44))
            self.setText("")
        else:
            # Fallback to text gear symbol
            self.setText("\u2699")  # Gear symbol ⚙
        
        self._apply_styling()
    
    def _load_images(self) -> None:
        """Load the three-state button images."""
        import os
        
        if self.base_image.exists():
            self.base_pixmap = QPixmap(str(self.base_image))
            logger.debug(f"Loaded settings base image: {self.base_image}")
        else:
            logger.warning(f"Settings base image not found: {self.base_image}")
        
        if self.hover_image.exists():
            self.hover_pixmap = QPixmap(str(self.hover_image))
        else:
            self.hover_pixmap = self.base_pixmap
        
        if self.pressed_image.exists():
            self.pressed_pixmap = QPixmap(str(self.pressed_image))
        else:
            self.pressed_pixmap = self.base_pixmap
    
    def enterEvent(self, event) -> None:
        """Handle mouse enter - show hover state."""
        super().enterEvent(event)
        self._is_hovered = True
        if self.hover_pixmap:
            self.setIcon(QIcon(self.hover_pixmap))
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave - show base state."""
        super().leaveEvent(event)
        self._is_hovered = False
        self._is_pressed = False
        if self.base_pixmap:
            self.setIcon(QIcon(self.base_pixmap))
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press - show pressed state."""
        super().mousePressEvent(event)
        self._is_pressed = True
        if self.pressed_pixmap:
            self.setIcon(QIcon(self.pressed_pixmap))
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release - return to hover or base state."""
        super().mouseReleaseEvent(event)
        self._is_pressed = False
        if self._is_hovered and self.hover_pixmap:
            self.setIcon(QIcon(self.hover_pixmap))
        elif self.base_pixmap:
            self.setIcon(QIcon(self.base_pixmap))
    
    def _apply_styling(self) -> None:
        """Apply styling to the button."""
        # Transparent background to show only the icon
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 0px;
            }}
        """)


# ==================== Module Exports ====================

__all__: list[str] = [
    'SettingsDialog',
    'SettingsButton',
]