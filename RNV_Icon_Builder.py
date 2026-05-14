"""
RNV Icon Builder - Main Application
Multi-resolution ICO file builder with theme support.

Author: RNV
Version: 3.0 (Phase 8 - Quality of Life & Polish)

Changes in v3.0:
- Auto-save session with crash recovery
- Quick actions toolbar (customizable)
- Tooltips toggle (F11)
- Session recovery on startup

Changes in v2.13:
- Image metadata panel showing file info, dimensions, color mode
- Compression statistics display after ICO build
- Export history tracking with persistent log
- Reveal exported files in explorer

Changes in v2.12:
- Preview background options (checkerboard/white/black/custom)
- Zoom controls for preview (50%-400%)
- Color palette extraction and display
- Icon in context preview (taskbar/folder/browser mockups)
- Enhanced comparison view

Changes in v2.11:
- Batch processing multiple files to ICO
- Watch folder mode (auto-process new images)
- Command-line interface (cli.py)
- Custom preset management (save/load size presets)
- Project files (.rnvicon format) save/load
- Session restore option on startup

Changes in v2.10:
- Favicon Package export (ICO, PNG, manifest files for web)
- Android Adaptive Icons export (all density buckets)
- iOS App Icon Set export (with Contents.json manifest)

Changes in v2.9:
- ICO to PNG extraction (extract all sizes from ICO)
- macOS .icns export format
- Estimated file size preview before building
- Output filename templates with placeholders

Changes in v2.8:
- Brightness/Contrast/Saturation sliders with -100 to +100 range
- Grayscale conversion preserving alpha channel
- Color adjustments integrated into Adjust tab

Changes in v2.7:
- Undo/Redo stack (up to 20 states) for all adjustments
- Rotation (90, 180, 270 degrees clockwise/counter-clockwise)
- Horizontal and vertical flip
- Fill transparency with color picker
- Border with color picker and width control
- Reorganized Adjust tab with scrollable content

Changes in v2.6:
- Recent files and folders history tab in Settings
- Automatically tracks opened files and scanned folders
- Double-click to reopen recent items
- Persistent history saved to disk

Changes in v2.3:
- Custom size selection (checkboxes to include/exclude sizes)
- PNG compression option for 256x256 (modern ICO, smaller files)
- Export as PNG set (individual files)
- Favicon preset (16, 32, 48 quick selection)
- Export menu with multiple options

Changes in v2.2:
- Transparency checkerboard pattern for alpha visualization
- Hover-to-zoom on thumbnails (300ms delay)
- Double-click for full-size preview popup
- Side-by-side original vs resized comparison
- Enhanced context menu with preview options

Changes in v2.1:
- Updated to modern Python 3.10+ syntax
- Replaced Optional[X] with X | None
- Replaced Dict/List/Tuple with dict/list/tuple
- Cleaned up typing imports

Changes in v2.0:
- Added type hints throughout
- Broke up long apply_theme() method into smaller functions
- Added status bar with file count and status messages
- Added keyboard shortcuts (Ctrl+O, Ctrl+B, Ctrl+N, etc.)
- Improved drag & drop feedback
- Standardized docstrings
"""

from __future__ import annotations

import sys
import os
import io
import logging
from typing import Any, TYPE_CHECKING

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QCheckBox,
    QFileDialog, QScrollArea, QFrame, QMenu, QStatusBar
)
from PyQt6.QtCore import Qt, QSize, QTimer, QEvent, QPoint
from PyQt6.QtGui import (
    QPixmap, QIcon, QColor, QPalette, QKeySequence, QShortcut,
    QDragEnterEvent, QDragLeaveEvent, QDropEvent, QResizeEvent,
    QCursor, QPainter, QPen, QPainterPath
)
from PIL import Image

# Import project modules
from utils.config import (
    APP_NAME, APP_VERSION,
    ICON_SIZES, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, WINDOW_X, WINDOW_Y,
    MIN_BUTTON_WIDTH, MIN_BUTTON_HEIGHT, THUMBNAIL_SIZE, DROP_ZONE_MIN_HEIGHT,
    FILE_LIST_MAX_HEIGHT, THEME_BUTTON_MARGIN, APP_ICON_PATH,
    get_button_image_paths, IMAGE_FILE_FILTER, ICO_FILE_FILTER, SUPPORTED_EXTENSIONS,
    DEFAULT_PREVIEW_BACKGROUND,
    STATUS_MESSAGE_TIMEOUT
)
from ui.colors import (
    BRAND_GOLD, BRAND_GOLD_DARK,
    DARK_THEME_COLORS, LIGHT_THEME_COLORS, IMAGE_MODE_COLORS,
    get_theme_colors,
)
from utils.font_loader import load_embedded_font
from utils.logger import setup_logger, Logger, get_logger_instance
from utils.error_handler import ErrorHandler, ErrorCategory, exception_handler
from utils.dialog_helper import DialogHelper, DialogResult
from utils.file_utils import FileUtils
from core.image_processor import ImageProcessor
from core.icon_builder_core import IconBuilderCore
from core.recent_files import RecentFilesManager
# Phase 5: Workflow Automation modules
from core.batch_processor import BatchProcessor, BatchJob, JobStatus
from core.folder_watcher import FolderWatcher, WatchSettings
from core.preset_manager import PresetManager, SizePreset
from core.project_manager import ProjectManager, Project
# Phase 7: Information & Metadata
from core.export_history import ExportHistory, ExportEntry
# Phase 8: Quality of Life
from core.session_manager import SessionManager, SessionState

from ui.theme_manager import ThemeManager
from ui.debug_button import DebugButton
from ui.preview_utils import (
    composite_on_checkerboard,
    composite_with_background,
    pil_to_qpixmap,
    ImagePreviewDialog,
    ComparisonDialog,
    get_cached_thumbnail,
    clear_thumbnail_cache,
    get_thumbnail_cache_stats
)
from ui.settings_dialog import SettingsDialog, SettingsButton
from ui.ico_analyzer import IcoAnalyzerDialog
# Phase 6: Preview Enhancements
from ui.context_preview import ContextPreviewDialog
# Phase 8: About Dialog
from ui.about_dialog import AboutDialog

# Setup logger for main application
logger: Logger = get_logger_instance(__name__)


# ==================== Custom Tooltip System ====================

class _ThemedToolTip(QLabel):
    """
    Custom tooltip that bypasses native Windows tooltip rendering.

    Native QToolTip on Windows creates an OS-level popup window with its own
    frame that cannot be styled via CSS. This class creates a frameless Qt
    widget with WA_TranslucentBackground and paints its own rounded-rect
    background, giving pixel-perfect themed tooltips in all modes.
    """

    _instance: '_ThemedToolTip | None' = None
    _OFFSET_X: int = 16
    _OFFSET_Y: int = 20
    _HIDE_DELAY_MS: int = 5000
    _MAX_WIDTH: int = 400
    _BORDER_RADIUS: int = 4

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWordWrap(True)
        self.setMaximumWidth(self._MAX_WIDTH)
        self.hide()

        # Colors for paintEvent (updated on each show)
        self._bg_color = QColor(DARK_THEME_COLORS['card_bg'])
        self._border_color = QColor(BRAND_GOLD)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    @classmethod
    def instance(cls) -> '_ThemedToolTip':
        """Get or create the singleton tooltip instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def paintEvent(self, event) -> None:
        """Paint rounded-rect background and border manually."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw filled rounded rectangle
        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        path.addRoundedRect(float(rect.x()), float(rect.y()),
                           float(rect.width()), float(rect.height()),
                           self._BORDER_RADIUS, self._BORDER_RADIUS)
        painter.fillPath(path, self._bg_color)

        # Draw border
        painter.setPen(QPen(self._border_color, 1.0))
        painter.drawPath(path)
        painter.end()

        # Let QLabel paint the text on top
        super().paintEvent(event)

    def show_tip(self, global_pos: QPoint, text: str,
                 colors: dict, font_family: str) -> None:
        """Show themed tooltip at the given global position."""
        # Store colors for paintEvent
        self._bg_color = QColor(colors['bg_secondary'])
        self._border_color = QColor(colors['tooltip_border'])

        # Title case the tooltip text
        self.setText(text.title())

        # Stylesheet for text only (background/border painted in paintEvent)
        self.setStyleSheet(
            f"color: {colors['text']};"
            f"padding: 4px 8px;"
            f"font-family: '{font_family}';"
            f"background: transparent;"
        )
        self.adjustSize()

        # Position below-right of cursor
        x = global_pos.x() + self._OFFSET_X
        y = global_pos.y() + self._OFFSET_Y

        # Keep tooltip on screen
        screen = QApplication.screenAt(global_pos)
        if screen:
            rect = screen.availableGeometry()
            if x + self.width() > rect.right():
                x = global_pos.x() - self.width() - 4
            if y + self.height() > rect.bottom():
                y = global_pos.y() - self.height() - 4

        self.move(x, y)
        self.show()
        self._hide_timer.start(self._HIDE_DELAY_MS)

    def hide_tip(self) -> None:
        """Hide the tooltip and cancel auto-hide timer."""
        self._hide_timer.stop()
        self.hide()


class IconBuilderApp(QMainWindow):
    """
    Main application window for RNV Icon Builder.
    
    Handles UI, user interactions, and orchestrates core functionality.
    
    Attributes:
        image_processor: Handles image loading and validation
        theme_manager: Manages application themes
        buttons: List of action buttons
        thumbnail_widgets: Dictionary of preview thumbnails by size
        
    Keyboard Shortcuts:
        Ctrl+O: Select files
        Ctrl+Shift+O: Select folder
        Ctrl+N: Clear files
        Ctrl+B: Build ICO
        Ctrl+T: Toggle theme
        F5: Refresh preview
        Escape: Clear selection
    """
    
    def __init__(self) -> None:
        """Initialize the application window and all components."""
        super().__init__()
        
        # Initialize core components
        logger.debug("Initializing core components")
        self.image_processor: ImageProcessor = ImageProcessor()
        self.theme_manager: ThemeManager = ThemeManager()
        self.theme_manager.detect_image_resources()
        self.recent_files_manager: RecentFilesManager = RecentFilesManager()
        
        # Phase 5: Workflow Automation managers
        self.batch_processor: BatchProcessor = BatchProcessor(self)
        self.folder_watcher: FolderWatcher = FolderWatcher(self)
        self.preset_manager: PresetManager = PresetManager()
        self.project_manager: ProjectManager = ProjectManager()
        
        # Phase 7: Export history
        self.export_history: ExportHistory = ExportHistory()
        
        # Phase 8: Session manager and tooltips
        self.session_manager: SessionManager = SessionManager(self)
        self._tooltips_enabled: bool = True
        
        # Phase 5: Current project tracking
        self._current_project: Project | None = None
        self._current_project_path: str | None = None
        self._project_modified: bool = False
        
        # UI components
        self.background_label: QLabel | None = None
        self.thumbnail_widgets: dict[int, QFrame] = {}
        self.buttons: list[DebugButton] = []
        self.button_images: dict[str, dict] = {}
        self.selected_size: int | None = None
        
        # Phase 2: Settings dialog for size selection and export options
        self.settings_dialog: SettingsDialog | None = None
        """Settings dialog instance (created on first use)"""
        
        # Preview enhancement: store full-size images for preview/comparison
        self.preview_images: dict[int, tuple[Image.Image, str]] = {}
        """Stores (image, tag) tuples for each size for preview functionality"""
        
        # Phase 3: Filename template
        self._filename_template: str = "icon_{size}"
        """Template for output filenames with placeholders"""
        
        # Phase 6: Preview Enhancement settings
        self._preview_background: str = DEFAULT_PREVIEW_BACKGROUND
        """Current preview background type"""
        self._preview_custom_color: tuple[int, int, int] | None = None
        """Custom background color (if using custom background)"""
        self._preview_zoom: int = 100
        """Current preview zoom percentage"""
        
        # Status bar timer for clearing messages
        self._status_timer: QTimer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._clear_status_message)
        
        # Setup window
        logger.debug(f"Setting up main window: {MIN_WINDOW_WIDTH}x{MIN_WINDOW_HEIGHT}")
        self.setWindowTitle("Multi-Resolution ICO Builder")
        self.setGeometry(WINDOW_X, WINDOW_Y, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)  # Tighter spacing between sections
        
        # Setup UI components
        logger.debug("Building UI components")
        self._setup_drop_zone(main_layout)
        self._setup_buttons(main_layout)
        self._setup_checkboxes(main_layout)
        self._setup_file_list(main_layout)
        self._setup_preview_area(main_layout)
        self._setup_status_bar()
        self._setup_theme_button()
        self._setup_keyboard_shortcuts()
        
        # Apply initial theme
        logger.debug("Applying initial theme")
        self.apply_theme()
        
        # Show initial status
        self._update_status_bar()
        
        # Phase 8: Start auto-save and check for session recovery
        self._setup_auto_save()
        QTimer.singleShot(500, self._check_session_recovery)
        
        # Install application-level event filter for custom themed tooltips
        # (bypasses native Windows tooltip rendering that ignores CSS border-radius)
        QApplication.instance().installEventFilter(self)
        
        logger.success("Application initialized successfully")
    
    # ==================== Setup Methods ====================
    
    def _setup_drop_zone(self, layout: QVBoxLayout) -> None:
        """
        Setup drag & drop zone.
        
        Args:
            layout: Parent layout to add drop zone to
        """
        logger.debug("Setting up drop zone")
        self.drop_label = QLabel("Drag & drop PNG/ICO/SVG files here\n(or use Ctrl+O to select files)")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setMinimumHeight(DROP_ZONE_MIN_HEIGHT)
        self.setAcceptDrops(True)
        layout.addWidget(self.drop_label)
    
    def _setup_buttons(self, layout: QVBoxLayout) -> None:
        """
        Setup main action buttons.
        
        Args:
            layout: Parent layout to add buttons to
        """
        logger.debug("Setting up action buttons")
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        
        button_configs: list[tuple] = [
            ("Select Files", self.select_files, "Choose individual image files to load (Ctrl+O)"),
            ("Select Folder", self.select_folder, "Load all images from a folder (Ctrl+Shift+O)"),
            ("Clear Files", self.clear_files, "Remove all loaded images"),
            ("Build ICO", self.build_ico, "Generate ICO file from loaded images (Ctrl+B)")
        ]
        
        for name, callback, tooltip in button_configs:
            btn = DebugButton(name)
            btn.set_theme_manager(self.theme_manager)
            btn.clicked.connect(callback)
            btn.setToolTip(tooltip)
            btn.setProperty("button_name", name)
            btn.setMinimumSize(MIN_BUTTON_WIDTH, MIN_BUTTON_HEIGHT)
            
            # Load button images if they exist
            img_paths = get_button_image_paths(name)
            if img_paths['base'].exists():
                btn.set_button_images(
                    str(img_paths['base']),
                    str(img_paths['hover']),
                    str(img_paths['pressed'])
                )
                self.button_images[name] = img_paths
                logger.debug(f"Loaded images for button: {name}")
            
            btn_layout.addWidget(btn)
            self.buttons.append(btn)
        
        layout.addLayout(btn_layout)
        logger.debug(f"Created {len(self.buttons)} action buttons")
    
    def _setup_checkboxes(self, layout: QVBoxLayout) -> None:
        """
        Setup option checkboxes with settings button on the right.
        
        Args:
            layout: Parent layout to add checkboxes to
        """
        logger.debug("Setting up checkboxes and settings button")
        
        # Single row with checkboxes on left, settings button on right
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 0)  # Remove extra padding
        options_layout.setSpacing(15)
        
        # Autofill checkbox
        self.autofill_checkbox = QCheckBox("Autofill missing smaller sizes")
        self.autofill_checkbox.setChecked(True)
        self.autofill_checkbox.stateChanged.connect(self.update_preview)
        self.autofill_checkbox.setToolTip("Automatically generate smaller sizes from the largest loaded image")
        options_layout.addWidget(self.autofill_checkbox)
        
        # Recursive scan checkbox
        self.recursive_checkbox = QCheckBox("Scan subfolders when selecting folder")
        self.recursive_checkbox.setChecked(True)
        self.recursive_checkbox.setToolTip("Include images from subfolders when using Select Folder")
        options_layout.addWidget(self.recursive_checkbox)
        
        # PNG compression option
        self.png_compression_checkbox = QCheckBox("Use PNG compression (smaller file)")
        self.png_compression_checkbox.setChecked(True)
        self.png_compression_checkbox.setToolTip(
            "Uses PNG compression for 256x256 and 128x128 sizes.\n"
            "Results in smaller ICO files. Supported by modern systems."
        )
        options_layout.addWidget(self.png_compression_checkbox)
        
        # Stretch to push settings button to the right
        options_layout.addStretch()
        
        # Settings button (gear icon) - locked to right side
        self.settings_button = SettingsButton(self)
        self.settings_button.clicked.connect(self._open_settings)
        options_layout.addWidget(self.settings_button)
        
        layout.addLayout(options_layout)
    
    def _open_settings(self) -> None:
        """Open the settings dialog."""
        logger.debug("Opening settings dialog")
        
        # Create dialog if it doesn't exist
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(
                self,
                recent_files_manager=self.recent_files_manager,
                preset_manager=self.preset_manager,
                batch_processor=self.batch_processor,
                folder_watcher=self.folder_watcher,
                project_manager=self.project_manager,
                export_history=self.export_history
            )
            # Connect all settings dialog signals
            self._connect_settings_dialog_signals()
            logger.debug("Settings dialog created")
            
            # Connect backend signals to UI updates
            self._connect_phase5_backend_signals()
        
        # Refresh recent lists in case they've changed
        self.settings_dialog.update_recent_lists()
        
        # Update file size estimate (Phase 3)
        self._update_file_size_estimate()
        
        # Update theme to match current app theme
        self.settings_dialog.apply_theme_from_manager(self.theme_manager.current_theme)
        
        # Show or raise the dialog
        if self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
        else:
            self.settings_dialog.show()
            # Force refresh after showing to fix blank screen issue
            self.settings_dialog.refresh_display()
    
    def _connect_settings_dialog_signals(self) -> None:
        """
        Connect all settings dialog signals to their handlers.
        
        Organized by feature category for easier maintenance.
        """
        dialog = self.settings_dialog
        
        # Core signals
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.export_png_requested.connect(self.export_png_set)
        dialog.analyze_ico_requested.connect(self._open_ico_analyzer)
        
        # Image adjustment signals
        dialog.auto_crop_requested.connect(self._on_auto_crop)
        dialog.add_padding_requested.connect(self._on_add_padding)
        dialog.center_resize_requested.connect(self._on_center_resize)
        
        # Transform signals
        dialog.rotate_requested.connect(self._on_rotate)
        dialog.flip_horizontal_requested.connect(self._on_flip_horizontal)
        dialog.flip_vertical_requested.connect(self._on_flip_vertical)
        dialog.fill_transparency_requested.connect(self._on_fill_transparency)
        dialog.add_border_requested.connect(self._on_add_border)
        
        # Undo/Redo signals
        dialog.undo_requested.connect(self._on_undo)
        dialog.redo_requested.connect(self._on_redo)
        
        # Color adjustment signals
        dialog.color_adjustment_requested.connect(self._on_color_adjustment)
        dialog.grayscale_requested.connect(self._on_grayscale)
        
        # Recent files signals
        dialog.open_recent_file_requested.connect(self._on_open_recent_file)
        dialog.open_recent_folder_requested.connect(self._on_open_recent_folder)
        
        # Export format signals
        dialog.export_icns_requested.connect(self.export_icns)
        dialog.filename_template_changed.connect(self._on_filename_template_changed)
        
        # Platform export signals
        dialog.export_favicon_requested.connect(self.export_favicon_package)
        dialog.export_android_requested.connect(self.export_android_icons)
        dialog.export_ios_requested.connect(self.export_ios_icons)
        
        # Batch processing signals
        dialog.batch_add_files_requested.connect(self._on_batch_add_files)
        dialog.batch_add_folder_requested.connect(self._on_batch_add_folder)
        dialog.batch_clear_requested.connect(self._on_batch_clear)
        dialog.batch_process_requested.connect(self._on_batch_process)
        dialog.batch_cancel_requested.connect(self._on_batch_cancel)
        
        # Watch folder signals
        dialog.watch_start_requested.connect(self._on_watch_start)
        dialog.watch_stop_requested.connect(self._on_watch_stop)
        
        # Preset signals
        dialog.preset_selected.connect(self._on_preset_selected)
        dialog.preset_save_requested.connect(self._on_preset_save)
        dialog.preset_delete_requested.connect(self._on_preset_delete)
        
        # Project signals
        dialog.project_new_requested.connect(self._on_project_new)
        dialog.project_save_requested.connect(self._on_project_save)
        dialog.project_load_requested.connect(self._on_project_load)
        
        # Session signals
        dialog.session_settings_changed.connect(self._on_session_settings_changed)
        
        # Preview enhancement signals
        dialog.background_changed.connect(self._on_preview_background_changed)
        dialog.zoom_changed.connect(self._on_preview_zoom_changed)
        dialog.context_preview_requested.connect(self._on_context_preview_requested)
        
        # Info & Metadata signals
        dialog.clear_export_history_requested.connect(self._on_clear_export_history)
        dialog.reveal_in_explorer_requested.connect(self._on_reveal_in_explorer)
    
    def _on_settings_changed(self) -> None:
        """Handle settings changes from the settings dialog."""
        if self.settings_dialog:
            selected = self.settings_dialog.get_selected_sizes()
            logger.debug(f"Settings changed, selected sizes: {selected}")
            self._show_status_message(f"{len(selected)} sizes selected")
            # Update file size estimate when sizes change
            self._update_file_size_estimate()
    
    def get_selected_sizes(self) -> list[int]:
        """
        Get list of currently selected sizes from settings dialog.
        
        Returns:
            List of selected sizes in descending order, or all ICON_SIZES if dialog not opened
        """
        if self.settings_dialog:
            return self.settings_dialog.get_selected_sizes()
        else:
            # Return all sizes if settings dialog hasn't been opened yet
            return sorted(ICON_SIZES, reverse=True)
    
    def _open_ico_analyzer(self) -> None:
        """Open the ICO Analyzer dialog."""
        logger.info("Opening ICO Analyzer")
        
        # Create and show analyzer dialog
        analyzer = IcoAnalyzerDialog(self)
        
        # Apply current theme
        analyzer.apply_theme_from_manager(self.theme_manager.current_theme)
        
        # Show as modal dialog
        analyzer.exec()
    
    def _on_auto_crop(self) -> None:
        """Handle auto-crop signal from settings dialog."""
        if not self.image_processor.detected_images:
            self._show_status_message("No images loaded to crop")
            return
        
        count = self.image_processor.apply_auto_crop()
        self._show_status_message(f"Auto-cropped {count} image(s)")
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
    
    def _on_add_padding(self, padding: int) -> None:
        """Handle add padding signal from settings dialog."""
        if not self.image_processor.detected_images:
            self._show_status_message("No images loaded")
            return
        
        count = self.image_processor.apply_padding(padding)
        self._show_status_message(f"Added {padding}px padding to {count} image(s)")
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
    
    def _on_center_resize(self, target_size: int, maintain_aspect: bool) -> None:
        """Handle center & resize signal from settings dialog."""
        if not self.image_processor.detected_images:
            self._show_status_message("No images loaded")
            return
        
        count = self.image_processor.apply_center_resize(target_size, maintain_aspect)
        self._show_status_message(f"Resized to {target_size}x{target_size}")
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
    
    def _on_undo(self) -> None:
        """Handle undo signal from settings dialog."""
        if not self.image_processor.can_undo():
            self._show_status_message("Nothing to undo")
            return
        
        if self.image_processor.undo():
            self._show_status_message(f"Undone ({self.image_processor.get_undo_count()} remaining)")
            self.update_file_listbox()
            self.update_preview()
            self._update_status_bar()
    
    def _on_redo(self) -> None:
        """Handle redo signal from settings dialog."""
        if not self.image_processor.can_redo():
            self._show_status_message("Nothing to redo")
            return
        
        if self.image_processor.redo():
            self._show_status_message(f"Redone ({self.image_processor.get_redo_count()} remaining)")
            self.update_file_listbox()
            self.update_preview()
            self._update_status_bar()
    
    def _on_rotate(self, degrees: int) -> None:
        """Handle rotate signal from settings dialog."""
        if not self.image_processor.detected_images:
            self._show_status_message("No images loaded")
            return
        
        count = self.image_processor.apply_rotate(degrees)
        self._show_status_message(f"Rotated {count} image(s) by {degrees} degrees")
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
    
    def _on_flip_horizontal(self) -> None:
        """Handle flip horizontal signal from settings dialog."""
        if not self.image_processor.detected_images:
            self._show_status_message("No images loaded")
            return
        
        count = self.image_processor.apply_flip_horizontal()
        self._show_status_message(f"Flipped {count} image(s) horizontally")
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
    
    def _on_flip_vertical(self) -> None:
        """Handle flip vertical signal from settings dialog."""
        if not self.image_processor.detected_images:
            self._show_status_message("No images loaded")
            return
        
        count = self.image_processor.apply_flip_vertical()
        self._show_status_message(f"Flipped {count} image(s) vertically")
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
    
    def _on_fill_transparency(self, color: tuple) -> None:
        """Handle fill transparency signal from settings dialog."""
        if not self.image_processor.detected_images:
            self._show_status_message("No images loaded")
            return
        
        count = self.image_processor.apply_fill_transparency(color)
        self._show_status_message(f"Filled transparency in {count} image(s)")
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
    
    def _on_add_border(self, width: int, color: tuple) -> None:
        """Handle add border signal from settings dialog."""
        if not self.image_processor.detected_images:
            self._show_status_message("No images loaded")
            return
        
        count = self.image_processor.apply_add_border(width, color)
        self._show_status_message(f"Added {width}px border to {count} image(s)")
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
    
    def _on_color_adjustment(self, brightness: int, contrast: int, saturation: int) -> None:
        """
        Handle color adjustment signal from settings dialog.
        
        Args:
            brightness: Brightness value (-100 to +100)
            contrast: Contrast value (-100 to +100)
            saturation: Saturation value (-100 to +100)
        """
        if not self.image_processor.detected_images:
            self._show_status_message("No images loaded")
            return
        
        count = self.image_processor.apply_color_adjustments(brightness, contrast, saturation)
        adjustments = []
        if brightness != 0:
            adjustments.append(f"B:{brightness:+d}")
        if contrast != 0:
            adjustments.append(f"C:{contrast:+d}")
        if saturation != 0:
            adjustments.append(f"S:{saturation:+d}")
        adj_str = ", ".join(adjustments)
        self._show_status_message(f"Applied {adj_str} to {count} image(s)")
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
    
    def _on_grayscale(self) -> None:
        """Handle grayscale conversion signal from settings dialog."""
        if not self.image_processor.detected_images:
            self._show_status_message("No images loaded")
            return
        
        count = self.image_processor.apply_grayscale()
        self._show_status_message(f"Converted {count} image(s) to grayscale")
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
    
    def _on_open_recent_file(self, file_path: str) -> None:
        """
        Handle opening a recent file from the settings dialog.
        
        Args:
            file_path: Path to the file to open
        """
        logger.info(f"Opening recent file: {file_path}")
        
        if not os.path.exists(file_path):
            logger.warning(f"Recent file no longer exists: {file_path}")
            self._show_status_message("File no longer exists")
            DialogHelper.show_warning(
                self,
                f"The file no longer exists:\n{file_path}",
                "File Not Found"
            )
            # Refresh the recent lists to remove the invalid entry
            if self.settings_dialog:
                self.settings_dialog.update_recent_lists()
            return
        
        # Load the file
        self.handle_files([file_path])
        self._show_status_message(f"Opened: {os.path.basename(file_path)}")
    
    def _on_open_recent_folder(self, folder_path: str) -> None:
        """
        Handle opening a recent folder from the settings dialog.
        
        Args:
            folder_path: Path to the folder to scan
        """
        logger.info(f"Opening recent folder: {folder_path}")
        
        if not os.path.exists(folder_path):
            logger.warning(f"Recent folder no longer exists: {folder_path}")
            self._show_status_message("Folder no longer exists")
            DialogHelper.show_warning(
                self,
                f"The folder no longer exists:\n{folder_path}",
                "Folder Not Found"
            )
            # Refresh the recent lists to remove the invalid entry
            if self.settings_dialog:
                self.settings_dialog.update_recent_lists()
            return
        
        # Scan the folder for files
        recursive = self.recursive_checkbox.isChecked()
        logger.debug(f"Scanning folder (recursive={recursive}): {folder_path}")
        self._show_status_message(f"Scanning folder...")
        
        files: list[str] = []
        for root_dir, _, fnames in os.walk(folder_path):
            for f in fnames:
                if any(f.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    files.append(os.path.join(root_dir, f))
            
            if not recursive:
                break
        
        if files:
            logger.info(f"Found {len(files)} image file(s) in folder")
            self.handle_files(files)
            self._show_status_message(f"Loaded {len(files)} file(s) from folder")
        else:
            logger.warning("No image files found in folder")
            self._show_status_message("No valid files found in folder")
            DialogHelper.show_warning(
                self,
                "No PNG, ICO, or SVG files found in folder.",
                "No Files"
            )
    
    # ==================== Phase 5: Batch Processing Handlers ====================
    
    def _connect_phase5_backend_signals(self) -> None:
        """Connect Phase 5 backend signals to UI updates."""
        # Batch processor signals
        if self.batch_processor:
            self.batch_processor.job_started.connect(self._on_batch_job_started)
            self.batch_processor.job_completed.connect(self._on_batch_job_completed)
            self.batch_processor.batch_started.connect(self._on_batch_started)
            self.batch_processor.batch_completed.connect(self._on_batch_completed)
            self.batch_processor.batch_progress.connect(self._on_batch_progress)
        
        # Folder watcher signals
        if self.folder_watcher:
            self.folder_watcher.file_detected.connect(self._on_watch_file_detected)
            self.folder_watcher.file_processed.connect(self._on_watch_file_processed)
            self.folder_watcher.watch_started.connect(self._on_watch_started)
            self.folder_watcher.watch_stopped.connect(self._on_watch_stopped)
            self.folder_watcher.error_occurred.connect(self._on_watch_error)
        
        logger.debug("Phase 5 backend signals connected")
    
    def _on_batch_add_files(self) -> None:
        """Handle batch add files request."""
        logger.info("Batch: Add files requested")
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files for Batch Processing",
            "",
            IMAGE_FILE_FILTER
        )
        
        if not file_paths:
            return
        
        # Get the folder of the first selected file as default output
        import os
        default_output = os.path.dirname(file_paths[0])
        
        # Ask if user wants a different output folder
        result = DialogHelper.ask_yes_no_cancel(
            self,
            f"Save ICO files to the same folder as source files?\n\n"
            f"Default: {default_output}\n\n"
            "Click 'Yes' to save alongside source files\n"
            "Click 'No' to choose a different output folder",
            "Output Location"
        )
        
        if result == DialogResult.CANCEL:
            return
        elif result == DialogResult.NO:
            output_folder = QFileDialog.getExistingDirectory(
                self,
                "Select Output Folder for ICO Files"
            )
            if not output_folder:
                return
        else:
            output_folder = default_output
        
        # Get current settings
        settings = self._get_batch_settings()
        
        # Add jobs
        added = 0
        for file_path in file_paths:
            job = self.batch_processor.add_job(file_path, output_folder, settings)
            if job:
                added += 1
        
        self._show_status_message(f"Added {added} file(s) to batch queue")
        
        # Update UI
        if self.settings_dialog:
            self.settings_dialog.update_batch_list(self.batch_processor.get_jobs())
    
    def _on_batch_add_folder(self) -> None:
        """Handle batch add folder request."""
        logger.info("Batch: Add folder requested")
        
        input_folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Images to Process"
        )
        
        if not input_folder:
            return
        
        # Ask if user wants a different output folder
        result = DialogHelper.ask_yes_no_cancel(
            self,
            f"Save ICO files to the same folder?\n\n"
            f"Images will be processed from:\n{input_folder}\n\n"
            "Click 'Yes' to save in same folder\n"
            "Click 'No' to choose a different output folder",
            "Output Location"
        )
        
        if result == DialogResult.CANCEL:
            return
        elif result == DialogResult.NO:
            output_folder = QFileDialog.getExistingDirectory(
                self,
                "Select Output Folder for ICO Files"
            )
            if not output_folder:
                return
        else:
            output_folder = input_folder
        
        # Get current settings
        settings = self._get_batch_settings()
        recursive = self.recursive_checkbox.isChecked()
        
        # Add jobs from folder
        added = self.batch_processor.add_jobs_from_folder(
            input_folder, output_folder, settings, recursive
        )
        
        self._show_status_message(f"Added {added} file(s) from folder to batch queue")
        
        # Update UI
        if self.settings_dialog:
            self.settings_dialog.update_batch_list(self.batch_processor.get_jobs())
    
    def _on_batch_clear(self) -> None:
        """Handle batch clear request."""
        logger.info("Batch: Clear requested")
        self.batch_processor.clear_jobs()
        self._show_status_message("Batch queue cleared")
        
        if self.settings_dialog:
            self.settings_dialog.update_batch_list([])
    
    def _on_batch_process(self) -> None:
        """Handle batch process request."""
        jobs = self.batch_processor.get_jobs()
        if not jobs:
            self._show_status_message("No jobs in batch queue")
            return
        
        logger.info(f"Batch: Processing {len(jobs)} job(s)")
        self._show_status_message(f"Processing {len(jobs)} batch job(s)...")
        
        if self.settings_dialog:
            self.settings_dialog.set_batch_processing(True)
        
        self.batch_processor.process_all()
    
    def _on_batch_cancel(self) -> None:
        """Handle batch cancel request."""
        logger.info("Batch: Cancel requested")
        self.batch_processor.cancel()
        self._show_status_message("Batch processing cancelled")
        
        if self.settings_dialog:
            self.settings_dialog.set_batch_processing(False)
    
    def _on_batch_job_started(self, job_id: int) -> None:
        """Handle batch job started signal."""
        logger.debug(f"Batch job {job_id} started")
        if self.settings_dialog:
            self.settings_dialog.update_batch_list(self.batch_processor.get_jobs())
    
    def _on_batch_job_completed(self, job_id: int, success: bool) -> None:
        """Handle batch job completed signal."""
        logger.debug(f"Batch job {job_id} completed: {'success' if success else 'failed'}")
        if self.settings_dialog:
            self.settings_dialog.update_batch_list(self.batch_processor.get_jobs())
    
    def _on_batch_started(self, total: int) -> None:
        """Handle batch processing started signal."""
        logger.info(f"Batch processing started: {total} jobs")
        self._show_status_message(f"Batch processing: 0/{total}")
    
    def _on_batch_completed(self, total: int, succeeded: int, failed: int) -> None:
        """Handle batch processing completed signal."""
        logger.info(f"Batch completed: {succeeded}/{total} succeeded, {failed} failed")
        self._show_status_message(f"Batch complete: {succeeded} succeeded, {failed} failed")
        
        if self.settings_dialog:
            self.settings_dialog.set_batch_processing(False)
            self.settings_dialog.update_batch_list(self.batch_processor.get_jobs())
        
        # Show completion dialog
        DialogHelper.show_info(
            self,
            f"Processed {total} file(s)\n\n"
            f"✓ Succeeded: {succeeded}\n"
            f"✗ Failed: {failed}",
            "Batch Processing Complete"
        )
    
    def _on_batch_progress(self, current: int, total: int) -> None:
        """Handle batch progress signal."""
        self._show_status_message(f"Batch processing: {current}/{total}", 0)
    
    def _get_batch_settings(self) -> dict:
        """Get current settings for batch processing."""
        return {
            'sizes': self.get_selected_sizes(),
            'autofill': self.autofill_checkbox.isChecked(),
            'png_compression': self.png_compression_checkbox.isChecked(),
        }
    
    # ==================== Phase 5: Watch Folder Handlers ====================
    
    def _on_watch_start(self, input_folder: str, output_folder: str) -> None:
        """Handle watch folder start request."""
        logger.info(f"Watch: Start requested - {input_folder} -> {output_folder}")
        
        if not input_folder or not output_folder:
            self._show_status_message("Please select input and output folders")
            return
        
        if not os.path.exists(input_folder):
            self._show_status_message("Input folder does not exist")
            return
        
        if not os.path.exists(output_folder):
            if not FileUtils.create_directory_if_not_exists(output_folder):
                self._show_status_message("Cannot create output folder")
                return
        
        # Create watch settings
        from core.folder_watcher import WatchSettings
        settings = WatchSettings(
            input_folder=input_folder,
            output_folder=output_folder,
            sizes=self.get_selected_sizes(),
            autofill=self.autofill_checkbox.isChecked(),
            png_compression=self.png_compression_checkbox.isChecked(),
            recursive=self.recursive_checkbox.isChecked(),
        )
        
        # Start watching
        if self.folder_watcher.start_watching(settings):
            self._show_status_message(f"Watching folder: {input_folder}")
        else:
            self._show_status_message("Failed to start folder watch")
    
    def _on_watch_stop(self) -> None:
        """Handle watch folder stop request."""
        logger.info("Watch: Stop requested")
        self.folder_watcher.stop_watching()
        self._show_status_message("Stopped watching folder")
    
    def _on_watch_started(self, folder: str) -> None:
        """Handle watch started signal from backend."""
        logger.info(f"Watch started: {folder}")
        if self.settings_dialog:
            self.settings_dialog.update_watch_status(True, folder)
    
    def _on_watch_stopped(self) -> None:
        """Handle watch stopped signal from backend."""
        logger.info("Watch stopped")
        if self.settings_dialog:
            self.settings_dialog.update_watch_status(False)
    
    def _on_watch_file_detected(self, file_path: str) -> None:
        """Handle file detected in watch folder."""
        logger.debug(f"Watch: File detected - {file_path}")
        self._show_status_message(f"Processing: {os.path.basename(file_path)}")
    
    def _on_watch_file_processed(self, source: str, output: str, success: bool) -> None:
        """Handle file processed from watch folder."""
        if success:
            logger.info(f"Watch: Processed {os.path.basename(source)}")
            self._show_status_message(f"Created: {os.path.basename(output)}")
        else:
            logger.warning(f"Watch: Failed to process {source}")
            self._show_status_message(f"Failed: {os.path.basename(source)}")
    
    def _on_watch_error(self, error: str) -> None:
        """Handle watch folder error."""
        logger.error(f"Watch error: {error}")
        self._show_status_message(f"Watch error: {error}")
    
    # ==================== Phase 5: Preset Handlers ====================
    
    def _on_preset_selected(self, preset_name: str) -> None:
        """Handle preset selection."""
        logger.info(f"Preset selected: {preset_name}")
        
        preset = self.preset_manager.get_preset(preset_name)
        if not preset:
            logger.warning(f"Preset not found: {preset_name}")
            return
        
        # Apply preset to size checkboxes
        if self.settings_dialog:
            self.settings_dialog.set_selected_sizes(preset.sizes)
        
        # Apply autofill setting
        self.autofill_checkbox.setChecked(preset.autofill)
        
        # Apply PNG compression setting
        self.png_compression_checkbox.setChecked(preset.png_compression)
        
        self._show_status_message(f"Applied preset: {preset_name}")
        self.update_preview()
    
    def _on_preset_save(self, preset_name: str) -> None:
        """Handle preset save request."""
        logger.info(f"Preset save requested: {preset_name}")
        
        if not preset_name:
            self._show_status_message("Please enter a preset name")
            return
        
        # Get current settings
        sizes = self.get_selected_sizes()
        autofill = self.autofill_checkbox.isChecked()
        png_compression = self.png_compression_checkbox.isChecked()
        
        # Save preset
        if self.preset_manager.save_preset(preset_name, sizes, autofill, png_compression):
            self._show_status_message(f"Saved preset: {preset_name}")
            
            # Refresh preset list in dialog
            if self.settings_dialog:
                self.settings_dialog.update_preset_list(
                    self.preset_manager.list_preset_names()
                )
        else:
            self._show_status_message(f"Failed to save preset: {preset_name}")
    
    def _on_preset_delete(self, preset_name: str) -> None:
        """Handle preset delete request."""
        logger.info(f"Preset delete requested: {preset_name}")
        
        if not preset_name:
            return
        
        # Confirm deletion
        if not ErrorHandler.confirm_action(
            parent=self,
            title="Delete Preset",
            message=f"Delete preset '{preset_name}'?",
            default_yes=False
        ):
            return
        
        if self.preset_manager.delete_preset(preset_name):
            self._show_status_message(f"Deleted preset: {preset_name}")
            
            # Refresh preset list in dialog
            if self.settings_dialog:
                self.settings_dialog.update_preset_list(
                    self.preset_manager.list_preset_names()
                )
        else:
            self._show_status_message(f"Cannot delete preset: {preset_name}")
    
    # ==================== Phase 5: Project Handlers ====================
    
    def _on_project_new(self) -> None:
        """Handle new project request."""
        logger.info("Project: New requested")
        
        # Check for unsaved changes
        if self._project_modified:
            if not ErrorHandler.confirm_action(
                parent=self,
                title="Unsaved Changes",
                message="Create new project without saving current changes?",
                default_yes=False
            ):
                return
        
        # Clear current state
        self.image_processor.clear_images()
        self.update_file_listbox()
        self.clear_preview()
        self._update_status_bar()
        
        # Reset project tracking
        self._current_project = self.project_manager.create_new_project("Untitled")
        self._current_project_path = None
        self._project_modified = False
        
        self._show_status_message("New project created")
    
    def _on_project_save(self) -> None:
        """Handle project save request."""
        logger.info("Project: Save requested")
        
        # Use existing path or prompt for new one
        if self._current_project_path:
            self._save_project_to_path(self._current_project_path)
        else:
            self._on_project_save_as()
    
    def _on_project_save_as(self) -> None:
        """Handle project save as request."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project",
            "",
            "RNV Icon Project (*.rnvicon)"
        )
        
        if file_path:
            if not file_path.endswith('.rnvicon'):
                file_path += '.rnvicon'
            self._save_project_to_path(file_path)
    
    def _save_project_to_path(self, file_path: str) -> None:
        """Save project to specified path."""
        # Update project with current state
        project = self._create_project_from_current_state()
        
        # Save project
        if self.project_manager.save_project(project, file_path, embed_images=True):
            self._current_project_path = file_path
            self._current_project = project
            self._project_modified = False
            self._show_status_message(f"Project saved: {os.path.basename(file_path)}")
            logger.success(f"Project saved to {file_path}")
        else:
            self._show_status_message("Failed to save project")
            logger.error(f"Failed to save project to {file_path}")
    
    def _on_project_load(self) -> None:
        """Handle project load request."""
        logger.info("Project: Load requested")
        
        # Check for unsaved changes
        if self._project_modified:
            if not ErrorHandler.confirm_action(
                parent=self,
                title="Unsaved Changes",
                message="Load project without saving current changes?",
                default_yes=False
            ):
                return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Project",
            "",
            "RNV Icon Project (*.rnvicon)"
        )
        
        if not file_path:
            return
        
        self._load_project_from_path(file_path)
    
    def _load_project_from_path(self, file_path: str) -> None:
        """Load project from specified path."""
        project = self.project_manager.load_project(file_path)
        
        if not project:
            self._show_status_message("Failed to load project")
            DialogHelper.show_warning(
                self,
                f"Could not load project from:\n{file_path}",
                "Load Failed"
            )
            return
        
        # Clear current state
        self.image_processor.clear_images()
        
        # Restore images. project.images is dict[int, ProjectImage]; each
        # ProjectImage knows how to materialize itself into a PIL.Image via
        # to_pil_image() (which handles both embedded base64 data and
        # external source paths).
        if project.images:
            for size, project_image in project.images.items():
                try:
                    img = project_image.to_pil_image()
                    if img is not None:
                        self.image_processor.detected_images[size] = img
                    else:
                        logger.warning(
                            f"Failed to restore image {size}: "
                            "to_pil_image() returned None"
                        )
                except Exception as e:
                    logger.warning(f"Failed to restore image {size}: {e}")
        
        # Restore settings. project.settings is a ProjectSettings dataclass
        # (attribute access), not a dict.
        if project.settings:
            settings = project.settings

            if settings.selected_sizes and self.settings_dialog:
                self.settings_dialog.set_selected_sizes(settings.selected_sizes)

            self.autofill_checkbox.setChecked(settings.autofill)
            self.png_compression_checkbox.setChecked(settings.png_compression)
        
        # Update tracking
        self._current_project = project
        self._current_project_path = file_path
        self._project_modified = False
        
        # Update UI
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
        
        self._show_status_message(f"Loaded project: {project.name}")
        logger.success(f"Project loaded from {file_path}")
    
    def _create_project_from_current_state(self):
        """Create a Project object from current application state."""
        import base64
        import io
        from core.project_manager import Project, ProjectSettings, ProjectImage

        # Get project name
        name = "Untitled"
        if self._current_project:
            name = self._current_project.name
        elif self._current_project_path:
            name = os.path.splitext(os.path.basename(self._current_project_path))[0]

        # Serialize images as ProjectImage objects.
        # ProjectImage.embedded_data is a base64-encoded PNG string; to_pil_image()
        # base64.b64decode()s it when loading back.
        images: dict[int, ProjectImage] = {}
        for size, img in self.image_processor.detected_images.items():
            try:
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
                images[size] = ProjectImage(
                    size=size,
                    embedded_data=encoded,
                    is_embedded=True,
                    is_autofilled=False,
                )
            except Exception as e:
                logger.warning(f"Failed to serialize image {size}: {e}")

        # Build a typed ProjectSettings (not a plain dict — Project.to_dict()
        # calls .to_dict() on this attribute).
        settings = ProjectSettings(
            selected_sizes=self.get_selected_sizes(),
            autofill=self.autofill_checkbox.isChecked(),
            png_compression=self.png_compression_checkbox.isChecked(),
        )

        return Project(name=name, settings=settings, images=images)
    
    def _on_session_settings_changed(self, restore_session: bool, auto_save: bool) -> None:
        """Handle session settings change from settings dialog."""
        logger.debug(f"Session settings: restore={restore_session}, auto_save={auto_save}")
        # Settings are stored in the dialog and will be applied on next startup
    
    # ==================== Phase 5: Startup Session Restore ====================
    
    def _check_session_restore(self) -> None:
        """Check for session to restore on startup."""
        # Check if auto-save exists
        if not self.project_manager.load_auto_save():
            return
        
        # Check if restore is enabled (from settings)
        # For now, just show a dialog asking if user wants to restore
        result = DialogHelper.confirm(
            self,
            "A previous session was found. Would you like to restore it?",
            "Restore Session",
            default_yes=True
        )
        
        if result:
            self._restore_last_session()
    
    def _restore_last_session(self) -> None:
        """Restore the last auto-saved session."""
        project = self.project_manager.load_auto_save()
        if not project:
            return
        
        # Restore images
        if project.images:
            for size, img_data in project.images.items():
                try:
                    import io
                    from PIL import Image
                    img = Image.open(io.BytesIO(img_data))
                    self.image_processor.detected_images[size] = img
                except Exception as e:
                    logger.warning(f"Failed to restore image {size}: {e}")
        
        # Restore settings
        if project.settings:
            if 'autofill' in project.settings:
                self.autofill_checkbox.setChecked(project.settings['autofill'])
            if 'png_compression' in project.settings:
                self.png_compression_checkbox.setChecked(project.settings['png_compression'])
        
        # Update UI
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
        
        self._show_status_message("Previous session restored")
        logger.success("Session restored from auto-save")

    # ==================== Phase 6: Preview Enhancement Handlers ====================
    
    def _on_preview_background_changed(self, bg_type: str, color: object) -> None:
        """
        Handle preview background change from settings dialog.
        
        Args:
            bg_type: Background type ('checkerboard', 'white', 'black', 'custom')
            color: Custom color tuple or None
        """
        self._preview_background = bg_type
        self._preview_custom_color = color if color else None
        logger.debug(f"Preview background changed to: {bg_type}")
        
        # Refresh preview to use new background
        self.update_preview()
        self._show_status_message(f"Preview background: {bg_type}")
    
    def _on_preview_zoom_changed(self, zoom: int) -> None:
        """
        Handle preview zoom change from settings dialog.
        
        Args:
            zoom: Zoom percentage (50-400)
        """
        self._preview_zoom = zoom
        logger.debug(f"Preview zoom changed to: {zoom}%")
        
        # Refresh preview with new zoom level
        self.update_preview()
        self._show_status_message(f"Zoom: {zoom}%")
    
    def _on_context_preview_requested(self) -> None:
        """Handle context preview request from settings dialog."""
        logger.info("Opening context preview dialog")
        
        # Collect available images
        images = {}
        for size, (img, tag) in self.preview_images.items():
            images[size] = img.copy()
        
        if not images:
            self._show_status_message("No images loaded for context preview")
            return
        
        # Create and show context preview dialog
        dialog = ContextPreviewDialog(images, self)
        dialog.apply_theme_from_manager(self.theme_manager.current_theme)
        dialog.exec()
    
    def _update_color_palette(self) -> None:
        """Update color palette in settings dialog with current largest image."""
        if not self.settings_dialog:
            return
        
        # Get largest available image for color analysis
        largest_img = None
        if self.preview_images:
            largest_size = max(self.preview_images.keys())
            largest_img = self.preview_images[largest_size][0]
        
        self.settings_dialog.update_color_palette(largest_img)
    
    def get_preview_background_settings(self) -> tuple[str, tuple[int, int, int] | None]:
        """
        Get current preview background settings.
        
        Returns:
            Tuple of (background_type, custom_color or None)
        """
        return (self._preview_background, self._preview_custom_color)
    
    def get_preview_zoom(self) -> int:
        """
        Get current preview zoom level.
        
        Returns:
            Zoom percentage (50-400)
        """
        return self._preview_zoom

    # ==================== Phase 7: Information & Metadata Handlers ====================
    
    def _on_clear_export_history(self) -> None:
        """Handle clear export history request from settings dialog."""
        logger.info("Clearing export history")
        self.export_history.clear_history()
        self._show_status_message("Export history cleared")
    
    def _on_reveal_in_explorer(self, path: str) -> None:
        """
        Reveal a file in the system file explorer.
        
        Args:
            path: Path to the file to reveal
        """
        import subprocess
        import platform
        from pathlib import Path
        
        file_path = Path(path)
        
        if not file_path.exists():
            self._show_status_message(f"File not found: {file_path.name}")
            return
        
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows: use explorer with /select to highlight the file
                subprocess.run(['explorer', '/select,', str(file_path)], check=False)
            elif system == "Darwin":
                # macOS: use open -R to reveal in Finder
                subprocess.run(['open', '-R', str(file_path)], check=False)
            else:
                # Linux: try xdg-open on parent directory
                subprocess.run(['xdg-open', str(file_path.parent)], check=False)
            
            self._show_status_message(f"Revealed: {file_path.name}")
            logger.info(f"Revealed file in explorer: {file_path}")
            
        except Exception as e:
            logger.warning(f"Failed to reveal file: {e}")
            self._show_status_message("Could not open file explorer")
    
    def _log_export(
        self,
        output_path: str,
        export_type: str,
        sizes: list[int],
        success: bool,
        file_info: dict | None = None,
        error_message: str = ""
    ) -> None:
        """
        Log an export operation to the export history.
        
        Args:
            output_path: Path where file was exported
            export_type: Type of export ('ico', 'png_set', 'icns', etc.)
            sizes: List of sizes included
            success: Whether export succeeded
            file_info: File info dict from build operation
            error_message: Error message if failed
        """
        file_size = 0
        compression_ratio = 0.0
        
        if file_info:
            file_size = file_info.get('file_size', 0)
            compression_stats = file_info.get('compression_stats', {})
            compression_ratio = compression_stats.get('compression_ratio', 0.0)
        
        source_count = len(self.image_processor.images) if hasattr(self.image_processor, 'images') else 0
        
        self.export_history.log_export(
            output_path=output_path,
            export_type=export_type,
            sizes=sizes,
            success=success,
            source_count=source_count,
            file_size=file_size,
            compression_ratio=compression_ratio,
            error_message=error_message
        )
        
        # Update settings dialog if open
        if self.settings_dialog:
            self.settings_dialog._refresh_export_history()

    # ==================== Phase 8: Quality of Life Handlers ====================
    
    def _setup_auto_save(self) -> None:
        """Setup automatic session saving."""
        # Set the state getter function
        self.session_manager.set_state_getter(self._get_session_state)
        
        # Start auto-save (every 5 minutes)
        from utils.config import AUTO_SAVE_INTERVAL_SECONDS
        interval_ms = AUTO_SAVE_INTERVAL_SECONDS * 1000
        self.session_manager.start_auto_save(interval_ms)
        
        logger.debug("Auto-save enabled")
    
    def _get_session_state(self) -> SessionState:
        """
        Get current session state for auto-save.
        
        Returns:
            SessionState object with current app state
        """
        # Get list of loaded file paths
        loaded_files = []
        if hasattr(self, 'file_listbox'):
            for i in range(self.file_listbox.count()):
                item = self.file_listbox.item(i)
                if item:
                    loaded_files.append(item.text())
        
        # Get selected sizes
        selected_sizes = self.get_selected_sizes() if hasattr(self, 'get_selected_sizes') else []
        
        # Get autofill and compression settings
        autofill = self.autofill_checkbox.isChecked() if hasattr(self, 'autofill_checkbox') else True
        png_compression = self.png_compression_checkbox.isChecked() if hasattr(self, 'png_compression_checkbox') else True
        
        # Get window geometry
        geometry = {
            'x': self.x(),
            'y': self.y(),
            'width': self.width(),
            'height': self.height()
        }
        
        return SessionState(
            loaded_files=loaded_files,
            selected_sizes=selected_sizes,
            autofill_enabled=autofill,
            png_compression=png_compression,
            current_project_path=self._current_project_path or '',
            window_geometry=geometry
        )
    
    def _check_session_recovery(self) -> None:
        """Check for crash recovery on startup."""
        if not self.session_manager.has_recovery():
            return
        
        state = self.session_manager.get_recovery_state()
        if not state:
            return
        
        # Show recovery dialog
        result = DialogHelper.confirm(
            self,
            f"A previous session was found from {state.formatted_time}.\n\n"
            f"Files: {len(state.loaded_files)}\n"
            f"Sizes: {len(state.selected_sizes)}\n\n"
            "Would you like to recover this session?",
            "Recover Session"
        )
        
        if result:
            self._restore_session_state(state)
            logger.success("Session recovered successfully")
        else:
            self.session_manager.clear_recovery()
            logger.info("Session recovery declined")
    
    def _restore_session_state(self, state: SessionState) -> None:
        """
        Restore a session state.
        
        Args:
            state: SessionState to restore
        """
        from pathlib import Path
        
        # Restore window geometry
        if state.window_geometry:
            geo = state.window_geometry
            if geo.get('x') and geo.get('y'):
                self.move(geo['x'], geo['y'])
            if geo.get('width') and geo.get('height'):
                self.resize(geo['width'], geo['height'])
        
        # Load files
        if state.loaded_files:
            existing_files = [f for f in state.loaded_files if Path(f).exists()]
            if existing_files:
                self._load_files(existing_files)
        
        # Restore settings
        if hasattr(self, 'autofill_checkbox'):
            self.autofill_checkbox.setChecked(state.autofill_enabled)
        if hasattr(self, 'png_compression_checkbox'):
            self.png_compression_checkbox.setChecked(state.png_compression)
        
        # Clear recovery flag
        self.session_manager.clear_recovery()
        
        self._show_status_message("Session recovered")
    
    def _toggle_tooltips(self) -> None:
        """Toggle tooltips visibility globally."""
        self._tooltips_enabled = not self._tooltips_enabled
        
        # Hide any currently visible custom tooltip
        _ThemedToolTip.instance().hide_tip()
        
        status = "enabled" if self._tooltips_enabled else "disabled"
        self._show_status_message(f"Tooltips {status} (F11 to toggle)")
        logger.info(f"Tooltips toggled: {status}")
    
    def _open_about_dialog(self) -> None:
        """Open the About dialog (Ctrl+/)."""
        # Use dark styling for both Dark Mode and Image Mode
        is_dark = self.theme_manager.is_dark_mode() or self.theme_manager.is_image_mode()
        dialog = AboutDialog(self, is_dark=is_dark)
        dialog.exec()
    
    def closeEvent(self, event) -> None:
        """Handle application close with full resource cleanup."""
        logger.info("Application closing - cleaning up resources")
        
        # Remove app-level event filter and hide custom tooltip
        QApplication.instance().removeEventFilter(self)
        _ThemedToolTip.instance().hide_tip()
        
        # Stop timers
        if hasattr(self, '_status_timer') and self._status_timer.isActive():
            self._status_timer.stop()
            logger.debug("Stopped status timer")
        
        if hasattr(self, '_hover_timer') and self._hover_timer.isActive():
            self._hover_timer.stop()
            logger.debug("Stopped hover timer")
        
        # Cancel any active batch processing
        if hasattr(self, 'batch_processor') and self.batch_processor:
            self.batch_processor.cancel()
            logger.debug("Cancelled batch processor")
        
        # Clear preview images (PIL Image objects)
        if hasattr(self, 'preview_images') and self.preview_images:
            self.preview_images.clear()
            logger.debug("Cleared preview images")
        
        # Clear thumbnail cache
        try:
            clear_thumbnail_cache()
            logger.debug("Cleared thumbnail cache")
        except Exception:
            pass
        
        # Clean shutdown for session manager
        self.session_manager.on_clean_shutdown()
        
        # Stop folder watcher if running
        if hasattr(self, 'folder_watcher') and self.folder_watcher:
            self.folder_watcher.stop_watching()
        
        logger.info("Application cleanup complete")
        super().closeEvent(event)

    def _setup_file_list(self, layout: QVBoxLayout) -> None:
        """
        Setup file list display.
        
        Args:
            layout: Parent layout to add file list to
        """
        logger.debug("Setting up file list widget")
        self.file_listbox = QListWidget()
        self.file_listbox.setMaximumHeight(FILE_LIST_MAX_HEIGHT)
        layout.addWidget(self.file_listbox)
    
    def _setup_preview_area(self, layout: QVBoxLayout) -> None:
        """
        Setup preview area with scroll support.
        
        Args:
            layout: Parent layout to add preview area to
        """
        logger.debug("Setting up preview area")
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.scroll_area = scroll_area
        
        self.preview_frame = QFrame()
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.setSpacing(5)
        self.preview_frame.setLayout(preview_layout)
        
        scroll_area.setWidget(self.preview_frame)
        layout.addWidget(scroll_area, 1)
        
        # Context menu for thumbnails
        self.preview_frame.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.preview_frame.customContextMenuRequested.connect(self.show_context_menu)
    
    def _setup_status_bar(self) -> None:
        """Setup status bar at the bottom of the window."""
        logger.debug("Setting up status bar")
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create permanent widgets for status bar
        self.status_file_count = QLabel("No files loaded")
        self.status_bar.addPermanentWidget(self.status_file_count)
    
    def _setup_theme_button(self) -> None:
        """Setup floating theme toggle button."""
        logger.debug("Setting up theme toggle button")
        self.theme_button = QPushButton(self.theme_manager.get_theme_display_name(), self)
        self.theme_button.setToolTip("Cycle theme: Dark → Light → Image (T)")
        self.theme_button.clicked.connect(self.cycle_theme)
        self.theme_button.raise_()
    
    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for common actions."""
        logger.debug("Setting up keyboard shortcuts")
        
        shortcuts = [
            ("Ctrl+O", self.select_files, "Select files"),
            ("Ctrl+Shift+O", self.select_folder, "Select folder"),
            ("Ctrl+N", self.clear_files, "Clear files"),
            ("Ctrl+B", self.build_ico, "Build ICO"),
            ("Ctrl+T", self.cycle_theme, "Toggle theme"),
            ("F5", self.refresh_preview, "Refresh preview"),
            ("Escape", self._clear_selection, "Clear selection"),
            # Phase 5: Project shortcuts
            ("Ctrl+S", self._on_project_save, "Save project"),
            ("Ctrl+Shift+S", self._on_project_save_as, "Save project as"),
            ("Ctrl+Shift+N", self._on_project_new, "New project"),
            # Phase 8: Settings, tooltips toggle and About dialog
            ("Ctrl+,", self._open_settings, "Open Settings"),
            ("F11", self._toggle_tooltips, "Toggle tooltips"),
            ("Ctrl+/", self._open_about_dialog, "Open About dialog"),
        ]
        
        for key_sequence, callback, description in shortcuts:
            shortcut = QShortcut(QKeySequence(key_sequence), self)
            shortcut.activated.connect(callback)
            logger.debug(f"Registered shortcut: {key_sequence} -> {description}")
    
    # ==================== Status Bar Methods ====================
    
    def _update_status_bar(self) -> None:
        """Update the permanent status bar information."""
        count = len(self.image_processor.get_detected_images())
        if count == 0:
            self.status_file_count.setText("No files loaded")
        elif count == 1:
            self.status_file_count.setText("1 size loaded")
        else:
            self.status_file_count.setText(f"{count} sizes loaded")
    
    def _show_status_message(self, message: str, timeout: int = STATUS_MESSAGE_TIMEOUT) -> None:
        """
        Show a temporary message in the status bar.
        
        Args:
            message: Message to display
            timeout: How long to show message (ms), 0 for permanent
        """
        self.status_bar.showMessage(message, timeout)
        logger.debug(f"Status: {message}")
    
    def _clear_status_message(self) -> None:
        """Clear the temporary status message."""
        self.status_bar.clearMessage()
    
    # ==================== Event Handlers ====================
    
    def resizeEvent(self, event: QResizeEvent | None) -> None:
        """
        Handle window resize.
        
        Args:
            event: Resize event
        """
        if event:
            super().resizeEvent(event)
        
        # Resize background label if it exists
        if self.background_label and self.theme_manager.is_image_mode():
            self.background_label.setGeometry(0, 0, self.width(), self.height())
        
        # Position theme button in bottom-right corner
        self.theme_button.move(
            self.width() - self.theme_button.width() - THEME_BUTTON_MARGIN,
            self.height() - self.theme_button.height() - THEME_BUTTON_MARGIN
        )
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        Handle drag enter with visual feedback.
        
        Args:
            event: Drag event
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            logger.debug("Drag enter accepted")
            self._show_drag_highlight(True)
            
            # Count valid files
            valid_count = sum(
                1 for url in event.mimeData().urls()
                if any(url.toLocalFile().lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)
            )
            self._show_status_message(f"Drop to add {valid_count} file(s)", 0)
    
    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """
        Handle drag leave.
        
        Args:
            event: Drag event
        """
        logger.debug("Drag leave")
        self._show_drag_highlight(False)
        self._clear_status_message()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handle drop event.
        
        Args:
            event: Drop event
        """
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            logger.info(f"Files dropped: {len(files)} file(s)")
            self.handle_files(files)
            event.acceptProposedAction()
        
        self._show_drag_highlight(False)
        self._clear_status_message()
    
    def _show_drag_highlight(self, show: bool) -> None:
        """
        Show or hide drag-and-drop highlight.
        
        Args:
            show: Whether to show highlight
        """
        if show:
            self.drop_label.setStyleSheet(f"""
                QLabel {{
                    border: 3px dashed {BRAND_GOLD_DARK};
                    border-radius: 8px;
                    padding: 40px;
                    background-color: {DARK_THEME_COLORS['dropzone_active_bg']};
                    color: {DARK_THEME_COLORS['text_on_accent']};
                    font-size: 14px;
                    font-weight: bold;
                }}
            """)
        else:
            self.apply_theme()
    
    # ==================== File Handling ====================
    
    def select_files(self) -> None:
        """Open file dialog to select image files."""
        logger.info("Opening file selection dialog")
        self._show_status_message("Selecting files...")
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            "",
            IMAGE_FILE_FILTER
        )
        
        if file_paths:
            logger.info(f"User selected {len(file_paths)} file(s)")
            # Add files to recent history
            for file_path in file_paths:
                self.recent_files_manager.add_file(file_path)
            self.handle_files(file_paths)
        else:
            logger.debug("File selection cancelled")
            self._show_status_message("Selection cancelled")
    
    def select_folder(self) -> None:
        """Open folder dialog and scan for image files."""
        logger.info("Opening folder selection dialog")
        self._show_status_message("Selecting folder...")
        
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            logger.debug("Folder selection cancelled")
            self._show_status_message("Selection cancelled")
            return
        
        logger.info(f"Scanning folder: {folder}")
        self._show_status_message(f"Scanning folder...")
        
        # Add folder to recent history
        self.recent_files_manager.add_folder(folder)
        
        recursive = self.recursive_checkbox.isChecked()
        logger.debug(f"Recursive scan: {recursive}")
        
        files: list[str] = []
        for root_dir, _, fnames in os.walk(folder):
            for f in fnames:
                if any(f.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    files.append(os.path.join(root_dir, f))
            
            if not recursive:
                break
        
        if files:
            logger.info(f"Found {len(files)} image file(s) in folder")
            self.handle_files(files)
        else:
            logger.warning("No PNG or ICO files found in folder")
            self._show_status_message("No valid files found in folder")
            DialogHelper.show_warning(
                self,
                "No PNG or ICO files found.",
                "No Files"
            )
    
    def handle_files(self, files: list[str]) -> None:
        """
        Process and load image files (PNG, ICO, SVG).
        
        Args:
            files: List of file paths to process
        """
        logger.info(f"Processing {len(files)} file(s)")
        self._show_status_message(f"Loading {len(files)} file(s)...")
        
        success_count = 0
        
        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            
            # Wrap in exception handler - errors are logged automatically
            with exception_handler(f"Loading {os.path.basename(file_path)}", show_error=False):
                if ext == ".png":
                    if self.image_processor.load_png(file_path):
                        success_count += 1
                elif ext == ".ico":
                    loaded = self.image_processor.load_ico(file_path)
                    if loaded > 0:
                        success_count += loaded
                elif ext == ".svg":
                    # SVG renders at all sizes, so count all successful renders
                    loaded = self.image_processor.load_svg(file_path)
                    if loaded > 0:
                        success_count += loaded
        
        self.update_file_listbox()
        self.update_preview()
        self._update_status_bar()
        self._update_file_size_estimate()
        
        logger.info(f"Loaded {success_count} file(s)")
        self._show_status_message(f"Loaded {success_count} size(s) successfully")
    
    def clear_files(self) -> None:
        """Clear all loaded files with confirmation."""
        if not self.image_processor.detected_images:
            self._show_status_message("No files to clear")
            return
        
        # Ask for confirmation
        if ErrorHandler.confirm_action(
            parent=self,
            title="Confirm Clear",
            message="Clear all loaded files?",
            details=f"{len(self.image_processor.detected_images)} file(s) will be removed.",
            default_yes=False
        ):
            logger.info("Clearing all files")
            self.image_processor.clear_images()
            self.file_listbox.clear()
            self.clear_preview()
            self._update_status_bar()
            self._update_file_size_estimate()
            self._show_status_message("All files cleared")
    
    def refresh_preview(self) -> None:
        """Refresh the preview area (F5 shortcut)."""
        logger.debug("Refreshing preview")
        self.update_preview()
        self._show_status_message("Preview refreshed")
    
    def _clear_selection(self) -> None:
        """Clear current selection (Escape key)."""
        self.selected_size = None
        self.file_listbox.clearSelection()
        logger.debug("Selection cleared")
    
    # ==================== UI Updates ====================
    
    def update_file_listbox(self) -> None:
        """Update file list display with current images."""
        logger.debug("Updating file listbox")
        self.file_listbox.clear()
        detected_images = self.image_processor.get_detected_images()
        
        for size in ICON_SIZES:
            if size in detected_images:
                item = QListWidgetItem(f"{size}x{size} \u2713")  # checkmark
                item.setForeground(QColor(BRAND_GOLD))
            else:
                item = QListWidgetItem(f"{size}x{size} \u2717")  # X mark
                item.setForeground(QColor(BRAND_GOLD_DARK))
            self.file_listbox.addItem(item)
    
    def clear_preview(self) -> None:
        """Clear preview thumbnails and cache."""
        logger.debug("Clearing preview thumbnails")
        count = 0
        while self.preview_frame.layout().count():
            item = self.preview_frame.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                count += 1
        self.thumbnail_widgets.clear()
        self.preview_images.clear()  # Phase 1: Clear stored preview images
        
        # Clear thumbnail cache for performance
        cache_cleared = clear_thumbnail_cache()
        logger.debug(f"Cleared {count} thumbnail(s), {cache_cleared} cached")
    
    def update_preview(self) -> None:
        """Update preview thumbnails with current images."""
        logger.debug("Updating preview")
        self.clear_preview()
        
        detected_images = self.image_processor.get_detected_images()
        if not detected_images:
            logger.debug("No images to preview")
            return
        
        base_size = self.image_processor.get_largest_size()
        autofill = self.autofill_checkbox.isChecked()
        logger.debug(f"Generating preview: base_size={base_size}, autofill={autofill}")
        
        # Clear stored preview images
        self.preview_images.clear()
        
        thumbnail_count = 0
        for size in ICON_SIZES:
            # Determine which image to show
            if size in detected_images:
                img = detected_images[size]
                tag = "(provided)"
            elif autofill and base_size and size < base_size:
                img = detected_images[base_size].resize(
                    (size, size),
                    Image.Resampling.LANCZOS
                )
                tag = "(autofill)"
            else:
                img = Image.new("RGBA", (size, size), (200, 200, 200, 255))
                tag = "(missing)"
            
            # Store full-size image for preview (Phase 1 enhancement)
            self.preview_images[size] = (img.copy(), tag)
            
            # Create thumbnail widget with full image reference
            thumb_widget = self._create_thumbnail_widget(size, img, tag)
            self.thumbnail_widgets[size] = thumb_widget
            self.preview_frame.layout().addWidget(thumb_widget)
            thumbnail_count += 1
        
        self.preview_frame.layout().addStretch()
        logger.debug(f"Created {thumbnail_count} thumbnail(s)")
        
        # Phase 6: Update color palette in settings dialog
        self._update_color_palette()
    
    def _create_thumbnail_widget(self, size: int, full_image: Image.Image, tag: str) -> QFrame:
        """
        Create a thumbnail widget for preview with enhanced features.
        
        Phase 1 Enhancements:
        - Transparency checkerboard background
        - Hover-to-zoom preview on ICON (300ms delay)
        - Text tooltip on row/text area
        - Double-click for full-size popup
        
        Args:
            size: Icon size
            full_image: Full-size image (not thumbnail)
            tag: Status tag (provided/autofill/missing)
            
        Returns:
            Configured thumbnail frame widget
        """
        thumb_widget = QFrame()
        thumb_widget.setProperty("icon_size", size)
        thumb_widget.setProperty("tag", tag)
        
        # Set background based on current theme
        theme = self.theme_manager.get_current_theme()
        if theme and theme['name'] == 'Light':
            thumb_widget.setStyleSheet(
                f"QFrame {{ background-color: {LIGHT_THEME_COLORS['panel_bg']}; border-radius: 3px; }}"
            )
        else:
            thumb_widget.setStyleSheet(
                f"QFrame {{ background-color: {DARK_THEME_COLORS['panel_bg']}; border-radius: 3px; }}"
            )
        
        thumb_layout = QHBoxLayout(thumb_widget)
        thumb_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create thumbnail with background based on Phase 6 settings
        thumb = full_image.resize((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
        
        # Apply zoom if not 100%
        display_size = int(THUMBNAIL_SIZE * self._preview_zoom / 100)
        if display_size != THUMBNAIL_SIZE:
            thumb = full_image.resize((display_size, display_size), Image.Resampling.LANCZOS)
        
        # Apply background based on Phase 6 settings
        thumb_with_bg = composite_with_background(
            thumb,
            self._preview_background,
            self._preview_custom_color
        )
        pixmap = pil_to_qpixmap(thumb_with_bg)
        
        # Icon label - hover here shows ZOOM preview
        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(display_size, display_size)
        icon_label.setProperty("icon_size", size)
        icon_label.setProperty("is_icon", True)  # Mark as icon for event filter
        icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
        icon_label.setMouseTracking(True)
        icon_label.installEventFilter(self)  # Zoom on icon hover
        thumb_layout.addWidget(icon_label)
        
        # Text label - simple tooltip, hover highlights in brand gold
        text_label = QLabel(f"{size}x{size}\n{tag}")
        text_label.setToolTip(f"{size}x{size} {tag}\nDouble-click for full preview")
        if theme and theme['name'] == 'Light':
            text_label.setStyleSheet(f"""
                QLabel {{ color: {LIGHT_THEME_COLORS['text_secondary']}; font-size: 11px; }}
                QLabel:hover {{ color: {BRAND_GOLD_DARK}; }}
            """)
        else:
            text_label.setStyleSheet(f"""
                QLabel {{ color: {DARK_THEME_COLORS['text_primary']}; font-size: 11px; }}
                QLabel:hover {{ color: {BRAND_GOLD}; }}
            """)
        thumb_layout.addWidget(text_label)
        
        # Frame-level double-click handling (works on entire row)
        thumb_widget.installEventFilter(self)
        
        # Add context menu
        thumb_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        thumb_widget.customContextMenuRequested.connect(
            lambda pos, s=size: self.show_context_menu_for_size(pos, s)
        )
        
        return thumb_widget
    
    def eventFilter(self, obj, event) -> bool:
        """
        Application-level event filter for custom themed tooltips
        and thumbnail hover/double-click handling.
        
        Custom tooltips:
        - QEvent.ToolTip → show _ThemedToolTip, consume native event
        - Leave/Click/Deactivate/Wheel → hide _ThemedToolTip
        
        Thumbnail interaction:
        - QLabel (icon): Hover shows zoom preview
        - QFrame (row): Double-click shows full preview
        """
        event_type = event.type()
        
        # ---- Custom themed tooltip system ----
        if event_type == QEvent.Type.ToolTip:
            if isinstance(obj, QWidget) and obj.toolTip():
                tooltip = _ThemedToolTip.instance()
                if self._tooltips_enabled:
                    tooltip.show_tip(
                        QCursor.pos(),
                        obj.toolTip(),
                        self._get_tooltip_colors(),
                        QApplication.instance().font().family()
                    )
                return True  # Always consume — prevent native tooltip
        
        elif event_type in (QEvent.Type.Leave, QEvent.Type.MouseButtonPress,
                            QEvent.Type.WindowDeactivate, QEvent.Type.Wheel):
            _ThemedToolTip.instance().hide_tip()
        
        # ---- Thumbnail hover-to-zoom and double-click ----
        # Icon label: hover-to-zoom behavior
        if isinstance(obj, QLabel) and obj.property("is_icon"):
            size = obj.property("icon_size")
            
            if event_type == QEvent.Type.Enter:
                # Start hover timer for zoom preview
                if not hasattr(self, '_hover_timer'):
                    self._hover_timer = QTimer(self)
                    self._hover_timer.setSingleShot(True)
                    self._hover_timer.timeout.connect(self._show_hover_zoom)
                self._hover_size = size
                self._hover_widget = obj
                self._hover_timer.start(300)  # 300ms delay
                
            elif event_type == QEvent.Type.Leave:
                # Cancel hover timer and hide zoom tooltip
                if hasattr(self, '_hover_timer'):
                    self._hover_timer.stop()
                from PyQt6.QtWidgets import QToolTip
                QToolTip.hideText()
                
            elif event_type == QEvent.Type.MouseButtonDblClick:
                # Double-click on icon shows full preview
                self._show_full_preview(size)
                return True
        
        # Frame: double-click anywhere on row shows full preview
        elif isinstance(obj, QFrame) and obj.property("icon_size") is not None:
            if event_type == QEvent.Type.MouseButtonDblClick:
                size = obj.property("icon_size")
                self._show_full_preview(size)
                return True
        
        return super().eventFilter(obj, event)
    
    def _show_hover_zoom(self) -> None:
        """Show zoomed preview as tooltip on hover."""
        if not hasattr(self, '_hover_size') or self._hover_size not in self.preview_images:
            return
        
        size = self._hover_size
        img, tag = self.preview_images[size]
        
        # Create zoomed preview (2x or max 256px)
        zoom_size = min(size * 2, 256)
        zoomed = img.resize((zoom_size, zoom_size), Image.Resampling.LANCZOS)
        zoomed_with_bg = composite_on_checkerboard(zoomed)
        
        # Convert to base64 for HTML tooltip
        import base64
        buffer = io.BytesIO()
        zoomed_with_bg.save(buffer, format='PNG')
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Theme-aware tooltip colors
        is_dark = self.theme_manager.current_theme != 'light'
        c = get_theme_colors(is_dark=is_dark)
        tt_bg = c['tooltip_bg']
        tt_text = c['tooltip_text']
        
        tooltip_html = f'''
        <div style="padding: 5px; background: {tt_bg}; border-radius: 4px;">
            <img src="data:image/png;base64,{img_data}" width="{zoom_size}" height="{zoom_size}">
            <br>
            <center style="color: {tt_text}; font-size: 11px;">
                <b>{size}x{size}</b> {tag}<br>
                <i>Double-click for full view</i>
            </center>
        </div>
        '''
        
        from PyQt6.QtWidgets import QToolTip
        from PyQt6.QtGui import QCursor
        QToolTip.showText(QCursor.pos(), tooltip_html, self._hover_widget)
    
    def _show_full_preview(self, size: int) -> None:
        """
        Show full-size preview dialog for a specific size.
        
        Args:
            size: Icon size to preview
        """
        if size not in self.preview_images:
            return
        
        img, tag = self.preview_images[size]
        
        # Get source image for comparison (if this is autofill)
        comparison_image = None
        if tag == "(autofill)":
            base_size = self.image_processor.get_largest_size()
            if base_size and base_size in self.preview_images:
                comparison_image = self.preview_images[base_size][0]
        
        dialog = ImagePreviewDialog(
            image=img,
            size=size,
            tag=tag,
            show_checkerboard=True,
            comparison_image=comparison_image,
            parent=self
        )
        dialog.exec()
        logger.debug(f"Showed full preview for {size}x{size}")
    
    # ==================== Context Menu ====================
    
    def show_context_menu(self, pos) -> None:
        """Show context menu (placeholder)."""
        logger.debug("Context menu requested (not implemented)")
        pass
    
    def show_context_menu_for_size(self, pos, size: int) -> None:
        """
        Show context menu for specific size.
        
        Args:
            pos: Menu position
            size: Icon size
        """
        logger.debug(f"Showing context menu for size {size}x{size}")
        self.selected_size = size
        menu = QMenu(self)
        
        # Preview options (Phase 1)
        menu.addAction("Preview Full Size", lambda: self._show_full_preview(size))
        if size in self.preview_images and self.preview_images[size][1] == "(autofill)":
            menu.addAction("Compare with Original", lambda: self._show_comparison(size))
        menu.addSeparator()
        
        # Original options
        menu.addAction("Replace this size", lambda: self.replace_size(size))
        menu.addAction("Remove this size", lambda: self.remove_size(size))
        menu.exec(self.thumbnail_widgets[size].mapToGlobal(pos))
    
    def _show_comparison(self, size: int) -> None:
        """
        Show side-by-side comparison of original vs resized.
        
        Args:
            size: Target size being compared
        """
        if size not in self.preview_images:
            return
        
        resized_img, tag = self.preview_images[size]
        
        # Get source (original) image
        base_size = self.image_processor.get_largest_size()
        if not base_size or base_size not in self.preview_images:
            return
        
        original_img = self.preview_images[base_size][0]
        
        dialog = ComparisonDialog(
            original_image=original_img,
            resized_image=resized_img,
            target_size=size,
            parent=self
        )
        dialog.exec()
        logger.debug(f"Showed comparison for {size}x{size}")
    
    def replace_size(self, size: int) -> None:
        """
        Replace a specific size.
        
        Args:
            size: Size to replace
        """
        logger.info(f"Replacing size {size}x{size}")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Replace {size}x{size}",
            "",
            IMAGE_FILE_FILTER
        )
        if not file_path:
            logger.debug("Replace cancelled")
            return
        
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == ".png":
                self.image_processor.load_png(file_path)
            elif ext == ".ico":
                self.image_processor.load_ico(file_path)
        except Exception as e:
            logger.error(f"Failed to load replacement file: {str(e)}")
            DialogHelper.show_error(
                self,
                f"Failed to load file:\n{str(e)}",
                "Error"
            )
        
        if not self.image_processor.has_size(size):
            logger.warning(f"Replacement file did not provide {size}x{size}")
            DialogHelper.show_warning(
                self,
                f"Replacement file did not provide {size}x{size}.",
                "Warning"
            )
        
        self.update_preview()
        self.update_file_listbox()
        self._update_status_bar()
    
    def remove_size(self, size: int) -> None:
        """
        Remove a specific size.
        
        Args:
            size: Size to remove
        """
        logger.info(f"Removing size {size}x{size}")
        if self.image_processor.remove_size(size):
            self.update_preview()
            self.update_file_listbox()
            self._update_status_bar()
            self._show_status_message(f"Removed {size}x{size}")
    
    # ==================== ICO Building ====================
    
    def build_ico(self) -> None:
        """Build multi-resolution ICO file with selected sizes and options."""
        logger.info("Starting ICO build process")
        
        detected_images = self.image_processor.get_detected_images()
        if not detected_images:
            logger.warning("No files loaded for ICO building")
            self._show_status_message("No files loaded - cannot build ICO")
            DialogHelper.show_warning(
                self,
                "Please load some PNG/ICO files first.",
                "No Files"
            )
            return
        
        # Phase 2: Get selected sizes
        selected_sizes = self.get_selected_sizes()
        if not selected_sizes:
            logger.warning("No sizes selected for ICO building")
            self._show_status_message("No sizes selected")
            DialogHelper.show_warning(
                self,
                "Please select at least one size to include in the ICO file.",
                "No Sizes Selected"
            )
            return
        
        # Filter images to only include selected sizes
        filtered_images = {
            size: img for size, img in detected_images.items() 
            if size in selected_sizes
        }
        
        # Check if we have any images for selected sizes
        if not filtered_images and not self.autofill_checkbox.isChecked():
            logger.warning("No images available for selected sizes")
            self._show_status_message("No images for selected sizes")
            DialogHelper.show_warning(
                self,
                "No images available for the selected sizes.\n"
                "Either load images for those sizes or enable 'Autofill missing smaller sizes'.",
                "No Images"
            )
            return
        
        self._show_status_message("Selecting output location...")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Multi-Resolution Icon",
            "",
            ICO_FILE_FILTER
        )
        if not file_path:
            logger.debug("ICO save cancelled")
            self._show_status_message("Build cancelled")
            return
        
        logger.info(f"Building ICO to: {file_path}")
        logger.info(f"Selected sizes: {selected_sizes}")
        logger.info(f"PNG compression: {self.png_compression_checkbox.isChecked()}")
        self._show_status_message("Building ICO file...")
        
        # Build ICO file with error handler
        # Pass selected sizes and compression option
        success, result = ErrorHandler.safe_execute(
            func=IconBuilderCore.build_ico_file,
            operation_name="Building ICO file",
            args=(
                detected_images,  # All images (for autofill source)
                file_path, 
                self.autofill_checkbox.isChecked(),
            ),
            kwargs={
                'selected_sizes': selected_sizes,
                'use_png_compression': self.png_compression_checkbox.isChecked(),
            },
            show_error_dialog=True,
            parent_widget=self,
            error_category=ErrorCategory.FILE_IO,
            critical=False
        )
        
        if success and result:
            success_flag, message, file_info = result
            
            if success_flag:
                sizes_str = ", ".join(file_info.get('sizes', []))
                file_size = file_info.get('file_size', 0)
                
                logger.success(f"ICO built successfully: {file_size:,} bytes")
                self._show_status_message(f"ICO created: {file_size:,} bytes")
                
                DialogHelper.show_info(
                    self,
                    f"Multi-resolution ICO created!\n\n"
                    f"File: {file_path}\n"
                    f"File size: {file_size:,} bytes\n\n"
                    f"Resolutions: {sizes_str}",
                    "Success"
                )
                
                # Phase 7: Log export and update compression stats
                self._log_export(
                    output_path=file_path,
                    export_type='ico',
                    sizes=selected_sizes,
                    success=True,
                    file_info=file_info
                )
                
                # Update compression stats in settings dialog
                if self.settings_dialog:
                    compression_stats = file_info.get('compression_stats', {})
                    self.settings_dialog.update_compression_stats(compression_stats, file_path)
            else:
                # Build function returned False (not an exception)
                self._show_status_message("Build failed - see error dialog")
                ErrorHandler.show_error_dialog(
                    parent=self,
                    title="Build Failed",
                    message="Failed to create ICO file",
                    details=message,
                    critical=False
                )
                
                # Phase 7: Log failed export
                self._log_export(
                    output_path=file_path,
                    export_type='ico',
                    sizes=selected_sizes,
                    success=False,
                    error_message=message
                )
        else:
            self._show_status_message("Build failed")
            
            # Phase 7: Log failed export
            self._log_export(
                output_path=file_path,
                export_type='ico',
                sizes=selected_sizes,
                success=False,
                error_message="Exception during build"
            )
    
    def export_png_set(self) -> None:
        """Export each selected size as a separate PNG file."""
        logger.info("Starting PNG set export")
        
        detected_images = self.image_processor.get_detected_images()
        if not detected_images:
            logger.warning("No files loaded for PNG export")
            self._show_status_message("No files loaded")
            DialogHelper.show_warning(
                self,
                "Please load some PNG/ICO files first.",
                "No Files"
            )
            return
        
        # Get selected sizes
        selected_sizes = self.get_selected_sizes()
        if not selected_sizes:
            logger.warning("No sizes selected for PNG export")
            self._show_status_message("No sizes selected")
            DialogHelper.show_warning(
                self,
                "Please select at least one size to export.",
                "No Sizes Selected"
            )
            return
        
        # Select output folder
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Folder for PNG Files"
        )
        if not folder:
            logger.debug("PNG export cancelled")
            self._show_status_message("Export cancelled")
            return
        
        logger.info(f"Exporting PNG set to: {folder}")
        self._show_status_message("Exporting PNG files...")
        
        base_size = self.image_processor.get_largest_size()
        autofill = self.autofill_checkbox.isChecked()
        exported_count = 0
        
        for size in selected_sizes:
            # Get or generate image for this size
            if size in detected_images:
                img = detected_images[size]
            elif autofill and base_size and size < base_size:
                img = detected_images[base_size].resize(
                    (size, size),
                    Image.Resampling.LANCZOS
                )
            else:
                logger.debug(f"Skipping {size}x{size} - no image available")
                continue
            
            # Save PNG file
            output_path = os.path.join(folder, f"icon_{size}.png")
            try:
                img.save(output_path, format='PNG', optimize=True)
                exported_count += 1
                logger.debug(f"Exported: {output_path}")
            except Exception as e:
                logger.error(f"Failed to export {size}x{size}: {e}")
        
        if exported_count > 0:
            logger.success(f"Exported {exported_count} PNG files")
            self._show_status_message(f"Exported {exported_count} PNG files")
            DialogHelper.show_info(
                self,
                f"Successfully exported {exported_count} PNG file(s) to:\n\n{folder}",
                "Export Complete"
            )
        else:
            logger.warning("No PNG files exported")
            self._show_status_message("No files exported")
            DialogHelper.show_warning(
                self,
                "No PNG files were exported.\n"
                "Make sure you have images loaded for the selected sizes.",
                "Export Failed"
            )
    
    def export_icns(self) -> None:
        """Export as macOS .icns file."""
        logger.info("Starting macOS .icns export")
        
        detected_images = self.image_processor.get_detected_images()
        if not detected_images:
            logger.warning("No files loaded for .icns export")
            self._show_status_message("No files loaded")
            DialogHelper.show_warning(
                self,
                "Please load some PNG/ICO files first.",
                "No Files"
            )
            return
        
        # Get selected sizes
        selected_sizes = self.get_selected_sizes()
        if not selected_sizes:
            logger.warning("No sizes selected for .icns export")
            self._show_status_message("No sizes selected")
            DialogHelper.show_warning(
                self,
                "Please select at least one size to export.",
                "No Sizes Selected"
            )
            return
        
        self._show_status_message("Selecting output location...")
        
        # Select output file
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save macOS Icon",
            "",
            "macOS Icon Files (*.icns)"
        )
        if not file_path:
            logger.debug(".icns export cancelled")
            self._show_status_message("Export cancelled")
            return
        
        # Ensure .icns extension
        if not file_path.lower().endswith('.icns'):
            file_path += '.icns'
        
        logger.info(f"Exporting .icns to: {file_path}")
        self._show_status_message("Building .icns file...")
        
        # Build .icns file
        success, result = ErrorHandler.safe_execute(
            func=IconBuilderCore.build_icns_file,
            operation_name="Building .icns file",
            args=(
                detected_images,
                file_path,
                self.autofill_checkbox.isChecked(),
            ),
            kwargs={
                'selected_sizes': selected_sizes,
            },
            show_error_dialog=True,
            parent_widget=self,
            error_category=ErrorCategory.FILE_IO,
            critical=False
        )
        
        if success and result:
            success_flag, message, file_info = result
            
            if success_flag:
                sizes_str = ", ".join(file_info.get('sizes', []))
                file_size = file_info.get('file_size', 0)
                
                logger.success(f".icns built successfully: {file_size:,} bytes")
                self._show_status_message(f".icns created: {file_size:,} bytes")
                
                DialogHelper.show_info(
                    self,
                    f"macOS .icns file created!\n\n"
                    f"File: {file_path}\n"
                    f"File size: {file_size:,} bytes\n\n"
                    f"Sizes: {sizes_str}",
                    "Success"
                )
            else:
                self._show_status_message("Export failed - see error dialog")
                ErrorHandler.show_error_dialog(
                    parent=self,
                    title="Export Failed",
                    message="Failed to create .icns file",
                    details=message,
                    critical=False
                )
        else:
            self._show_status_message("Export failed")
    
    def export_favicon_package(self) -> None:
        """Export complete favicon package for web use."""
        logger.info("Starting favicon package export")
        
        detected_images = self.image_processor.get_detected_images()
        if not detected_images:
            logger.warning("No files loaded for favicon export")
            self._show_status_message("No files loaded")
            DialogHelper.show_warning(
                self,
                "Please load some PNG/ICO files first.",
                "No Files"
            )
            return
        
        self._show_status_message("Selecting output folder...")
        
        # Select output folder
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder for Favicon Package"
        )
        if not folder:
            logger.debug("Favicon export cancelled")
            self._show_status_message("Export cancelled")
            return
        
        logger.info(f"Exporting favicon package to: {folder}")
        self._show_status_message("Building favicon package...")
        
        # Build favicon package
        success, result = ErrorHandler.safe_execute(
            func=IconBuilderCore.export_favicon_package,
            operation_name="Building favicon package",
            args=(
                detected_images,
                folder,
                self.autofill_checkbox.isChecked(),
            ),
            show_error_dialog=True,
            parent_widget=self,
            error_category=ErrorCategory.FILE_IO,
            critical=False
        )
        
        if success and result:
            success_flag, message, file_info = result
            
            if success_flag:
                file_count = file_info.get('file_count', 0)
                files = file_info.get('files', [])
                
                logger.success(f"Favicon package exported: {file_count} files")
                self._show_status_message(f"Favicon package created: {file_count} files")
                
                # Show file list in details
                file_list = "\n".join(f"  • {f}" for f in files[:10])
                if len(files) > 10:
                    file_list += f"\n  ... and {len(files) - 10} more"
                
                DialogHelper.show_info(
                    self,
                    f"Favicon package created!\n\n"
                    f"Folder: {folder}\n"
                    f"Files: {file_count}\n\n"
                    f"Generated files:\n{file_list}",
                    "Success"
                )
            else:
                self._show_status_message("Export failed - see error dialog")
                ErrorHandler.show_error_dialog(
                    parent=self,
                    title="Export Failed",
                    message="Failed to create favicon package",
                    details=message,
                    critical=False
                )
        else:
            self._show_status_message("Export failed")
    
    def export_android_icons(self) -> None:
        """Export Android adaptive icons for all density buckets."""
        logger.info("Starting Android icons export")
        
        detected_images = self.image_processor.get_detected_images()
        if not detected_images:
            logger.warning("No files loaded for Android export")
            self._show_status_message("No files loaded")
            DialogHelper.show_warning(
                self,
                "Please load some PNG/ICO files first.",
                "No Files"
            )
            return
        
        self._show_status_message("Selecting output folder...")
        
        # Select output folder
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder for Android Icons"
        )
        if not folder:
            logger.debug("Android export cancelled")
            self._show_status_message("Export cancelled")
            return
        
        logger.info(f"Exporting Android icons to: {folder}")
        self._show_status_message("Building Android icons...")
        
        # Build Android icons
        success, result = ErrorHandler.safe_execute(
            func=IconBuilderCore.export_android_icons,
            operation_name="Building Android icons",
            args=(
                detected_images,
                folder,
                self.autofill_checkbox.isChecked(),
            ),
            show_error_dialog=True,
            parent_widget=self,
            error_category=ErrorCategory.FILE_IO,
            critical=False
        )
        
        if success and result:
            success_flag, message, file_info = result
            
            if success_flag:
                file_count = file_info.get('file_count', 0)
                output_folder = file_info.get('output_folder', folder)
                
                logger.success(f"Android icons exported: {file_count} files")
                self._show_status_message(f"Android icons created: {file_count} files")
                
                DialogHelper.show_info(
                    self,
                    f"Android icons created!\n\n"
                    f"Folder: {output_folder}\n"
                    f"Files: {file_count}\n\n"
                    f"Generated density buckets:\n"
                    f"  • mipmap-mdpi (48×48)\n"
                    f"  • mipmap-hdpi (72×72)\n"
                    f"  • mipmap-xhdpi (96×96)\n"
                    f"  • mipmap-xxhdpi (144×144)\n"
                    f"  • mipmap-xxxhdpi (192×192)\n\n"
                    f"Copy the 'res' folder to your Android project.",
                    "Success"
                )
            else:
                self._show_status_message("Export failed - see error dialog")
                ErrorHandler.show_error_dialog(
                    parent=self,
                    title="Export Failed",
                    message="Failed to create Android icons",
                    details=message,
                    critical=False
                )
        else:
            self._show_status_message("Export failed")
    
    def export_ios_icons(self) -> None:
        """Export iOS App Icon set with Contents.json manifest."""
        logger.info("Starting iOS icons export")
        
        detected_images = self.image_processor.get_detected_images()
        if not detected_images:
            logger.warning("No files loaded for iOS export")
            self._show_status_message("No files loaded")
            DialogHelper.show_warning(
                self,
                "Please load some PNG/ICO files first.",
                "No Files"
            )
            return
        
        self._show_status_message("Selecting output folder...")
        
        # Select output folder
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder for iOS App Icons"
        )
        if not folder:
            logger.debug("iOS export cancelled")
            self._show_status_message("Export cancelled")
            return
        
        logger.info(f"Exporting iOS icons to: {folder}")
        self._show_status_message("Building iOS App Icon set...")
        
        # Build iOS icons
        success, result = ErrorHandler.safe_execute(
            func=IconBuilderCore.export_ios_icons,
            operation_name="Building iOS App Icon set",
            args=(
                detected_images,
                folder,
                self.autofill_checkbox.isChecked(),
            ),
            show_error_dialog=True,
            parent_widget=self,
            error_category=ErrorCategory.FILE_IO,
            critical=False
        )
        
        if success and result:
            success_flag, message, file_info = result
            
            if success_flag:
                file_count = file_info.get('file_count', 0)
                output_folder = file_info.get('output_folder', folder)
                
                logger.success(f"iOS App Icon set exported: {file_count} files")
                self._show_status_message(f"iOS icons created: {file_count} files")
                
                DialogHelper.show_info(
                    self,
                    f"iOS App Icon set created!\n\n"
                    f"Folder: {output_folder}\n"
                    f"Files: {file_count} (including Contents.json)\n\n"
                    f"Generated for:\n"
                    f"  • iPhone (all sizes)\n"
                    f"  • iPad (all sizes)\n"
                    f"  • App Store (1024×1024)\n\n"
                    f"Drag the 'AppIcon.appiconset' folder\n"
                    f"into your Xcode Assets.xcassets.",
                    "Success"
                )
            else:
                self._show_status_message("Export failed - see error dialog")
                ErrorHandler.show_error_dialog(
                    parent=self,
                    title="Export Failed",
                    message="Failed to create iOS App Icon set",
                    details=message,
                    critical=False
                )
        else:
            self._show_status_message("Export failed")
    
    def _on_filename_template_changed(self, template: str) -> None:
        """Handle filename template changes from settings dialog."""
        self._filename_template = template
        logger.debug(f"Filename template updated: {template}")
    
    def _update_file_size_estimate(self) -> None:
        """Update the file size estimate in the settings dialog."""
        if not self.settings_dialog:
            return
        
        detected_images = self.image_processor.get_detected_images()
        if not detected_images:
            self.settings_dialog.update_file_size_estimate(None)
            return
        
        selected_sizes = self.get_selected_sizes()
        use_png = self.png_compression_checkbox.isChecked()
        autofill = self.autofill_checkbox.isChecked()
        
        # Calculate estimate
        estimate = IconBuilderCore.estimate_ico_size(
            detected_images,
            selected_sizes=selected_sizes,
            use_png_compression=use_png,
            autofill=autofill
        )
        
        self.settings_dialog.update_file_size_estimate(estimate)
    
    # ==================== Theme Management ====================
    
    def _get_tooltip_colors(self) -> dict[str, str]:
        """
        Get tooltip color dict for the current theme mode.
        
        Returns dict with keys expected by _ThemedToolTip.show_tip():
            bg_secondary, text, tooltip_border
        
        Image Mode uses dark tooltip colors since the background is dark.
        """
        theme = self.theme_manager.current_theme
        if theme == 'light':
            return {
                'bg_secondary': LIGHT_THEME_COLORS['panel_bg'],
                'text': LIGHT_THEME_COLORS['text_primary'],
                'tooltip_border': BRAND_GOLD_DARK,
            }
        else:
            # Dark and Image modes both use dark tooltip colors
            return {
                'bg_secondary': DARK_THEME_COLORS['card_bg'],
                'text': DARK_THEME_COLORS['text_primary'],
                'tooltip_border': BRAND_GOLD,
            }
    
    def cycle_theme(self) -> None:
        """Cycle through available themes."""
        logger.info("Cycling theme")
        self.theme_manager.cycle_theme()
        self.theme_button.setText(self.theme_manager.get_theme_display_name())
        self.apply_theme()
        self.update_preview()
        self.update()
        QApplication.processEvents()
        self._show_status_message(f"Theme: {self.theme_manager.get_theme_display_name()}")
        
        # Update settings dialog theme if it exists
        if self.settings_dialog is not None:
            self.settings_dialog.apply_theme_from_manager(self.theme_manager.current_theme)
    
    def apply_theme(self) -> None:
        """Apply current theme to all UI components."""
        logger.debug(f"Applying theme: {self.theme_manager.get_theme_display_name()}")
        theme = self.theme_manager.get_current_theme()
        
        if theme:
            self._apply_standard_theme(theme)
        else:
            self._apply_image_mode_theme()
        
        # Update theme button text
        self.theme_button.setText(self.theme_manager.get_theme_display_name())
        self.theme_button.repaint()
        
        logger.debug("Theme applied successfully")
    
    def _apply_standard_theme(self, theme: dict[str, str]) -> None:
        """
        Apply Dark or Light theme.
        
        Args:
            theme: Theme dictionary with color values
        """
        # Remove Image Mode background if exists
        if self.background_label:
            self.background_label.deleteLater()
            self.background_label = None
        
        # Reset buttons to text mode
        self._reset_buttons_to_text_mode()
        
        # Set palette
        self._apply_palette(theme)
        
        # Apply stylesheets
        self._apply_main_stylesheet(theme)
        self._apply_drop_zone_stylesheet(theme)
        self._apply_preview_stylesheet(theme)
        self._apply_theme_button_stylesheet(theme)
        self._apply_status_bar_stylesheet(theme)
    
    def _apply_image_mode_theme(self) -> None:
        """Apply Image Mode theme with background image."""
        # Clean up any existing background
        if self.background_label is not None:
            self.background_label.setParent(None)
            self.background_label.deleteLater()
            self.background_label = None
            QApplication.processEvents()
        
        # Set dark palette for image mode
        self._apply_image_mode_palette()
        
        # Set buttons to image mode
        self._set_buttons_to_image_mode()
        
        # Force layout update
        self.centralWidget().layout().update()
        self.centralWidget().layout().activate()
        QApplication.processEvents()
        
        # Setup background image
        self._setup_background_image()
        
        # Apply transparent stylesheets
        self._apply_image_mode_stylesheets()
    
    def _reset_buttons_to_text_mode(self) -> None:
        """Reset all buttons to text mode."""
        for btn in self.buttons:
            btn.image_mode_active = False
            btn_name = btn.property("button_name")
            if btn.text() == "" and btn_name:
                btn.setText(btn_name)
            btn.setIcon(QIcon())
            btn.setMaximumSize(16777215, 16777215)
            btn.setMinimumSize(MIN_BUTTON_WIDTH, MIN_BUTTON_HEIGHT)
    
    def _set_buttons_to_image_mode(self) -> None:
        """Set all buttons to image mode."""
        for btn in self.buttons:
            btn.image_mode_active = True
            if btn.text() != "":
                btn.setProperty("button_name", btn.text())
                btn.setText("")
            
            btn_name = btn.property("button_name")
            if btn_name and btn_name in self.button_images:
                btn.setIcon(QIcon(str(self.button_images[btn_name]['base'])))
    
    def _apply_palette(self, theme: dict[str, str]) -> None:
        """
        Apply color palette from theme.
        
        Sets palette roles needed by Fusion style for proper checkbox,
        selection, and input rendering across all theme modes.
        
        Args:
            theme: Theme dictionary with color values
        """
        is_light = theme['name'] == 'Light'
        palette = QPalette()
        c = LIGHT_THEME_COLORS if is_light else DARK_THEME_COLORS

        window_color = QColor(theme['window_bg'])
        text_color = QColor(theme['text_color'])
        highlight = QColor(BRAND_GOLD_DARK if is_light else BRAND_GOLD)
        highlight_text = QColor(c['text_on_accent'])
        base = QColor(c['input_bg'])
        
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            palette.setColor(group, QPalette.ColorRole.Window, window_color)
            palette.setColor(group, QPalette.ColorRole.WindowText, text_color)
            palette.setColor(group, QPalette.ColorRole.Base, base)
            palette.setColor(group, QPalette.ColorRole.Text, text_color)
            palette.setColor(group, QPalette.ColorRole.Highlight, highlight)
            palette.setColor(group, QPalette.ColorRole.HighlightedText, highlight_text)
        
        QApplication.instance().setPalette(palette)
    
    def _apply_image_mode_palette(self) -> None:
        """Apply dark palette for image mode."""
        palette = QPalette()

        window_color = QColor(IMAGE_MODE_COLORS['window_bg'])
        text_color = QColor(IMAGE_MODE_COLORS['text_primary'])
        highlight = QColor(BRAND_GOLD)
        highlight_text = QColor(IMAGE_MODE_COLORS['text_on_accent'])
        base = QColor(IMAGE_MODE_COLORS['input_bg'])
        
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            palette.setColor(group, QPalette.ColorRole.Window, window_color)
            palette.setColor(group, QPalette.ColorRole.WindowText, text_color)
            palette.setColor(group, QPalette.ColorRole.Base, base)
            palette.setColor(group, QPalette.ColorRole.Text, text_color)
            palette.setColor(group, QPalette.ColorRole.Highlight, highlight)
            palette.setColor(group, QPalette.ColorRole.HighlightedText, highlight_text)
        
        QApplication.instance().setPalette(palette)
    
    def _apply_main_stylesheet(self, theme: dict[str, str]) -> None:
        """
        Apply main window stylesheet.
        
        Args:
            theme: Theme dictionary with color values
        """
        scrollbar_style = self.theme_manager.get_scrollbar_style()
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['window_bg']};
            }}
            QLabel {{
                color: {theme['text_color']};
            }}
            QPushButton {{
                background-color: {theme['button_bg']};
                color: {theme['button_text']};
                border: 1px solid {theme['border_color']};
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover_bg']};
                color: {theme['button_hover_text']};
            }}
            QPushButton:pressed {{
                background-color: {theme['button_pressed_bg']};
                color: {theme['button_pressed_text']};
            }}
            QCheckBox {{
                color: {theme['text_color']};
            }}
            QListWidget {{
                background-color: {theme['window_bg']};
                color: {theme['text_color']};
                border: 1px solid {theme['border_color']};
            }}
            QListWidget::item {{
                padding: 3px 6px;
            }}
            QListWidget::item:hover {{
                background-color: {BRAND_GOLD_DARK if theme['name'] == 'Light' else BRAND_GOLD};
                color: {LIGHT_THEME_COLORS['text_on_accent'] if theme['name'] == 'Light' else DARK_THEME_COLORS['text_on_accent']};
            }}
            QListWidget::item:selected {{
                background-color: {BRAND_GOLD_DARK if theme['name'] == 'Light' else BRAND_GOLD};
                color: {LIGHT_THEME_COLORS['text_on_accent'] if theme['name'] == 'Light' else DARK_THEME_COLORS['text_on_accent']};
            }}
            QScrollArea {{
                background-color: {theme['window_bg']};
            }}
            {scrollbar_style}
        """)
    
    def _apply_drop_zone_stylesheet(self, theme: dict[str, str]) -> None:
        """
        Apply drop zone stylesheet.
        
        Args:
            theme: Theme dictionary with color values
        """
        self.drop_label.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {theme['border_color']};
                border-radius: 5px;
                padding: 40px;
                background-color: {theme['window_bg']};
                color: {theme['text_color']};
                font-size: 14px;
                font-weight: bold;
            }}
        """)
    
    def _apply_preview_stylesheet(self, theme: dict[str, str]) -> None:
        """
        Apply preview area stylesheet.
        
        Args:
            theme: Theme dictionary with color values
        """
        self.preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme['window_bg']};
            }}
        """)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {theme['window_bg']};
                border: 1px solid {theme['border_color']};
            }}
        """)
    
    def _apply_theme_button_stylesheet(self, theme: dict[str, str]) -> None:
        """
        Apply theme button stylesheet.
        
        Args:
            theme: Theme dictionary with color values
        """
        self.theme_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['button_bg']};
                color: {theme['button_text']};
                border: 1px solid {theme['border_color']};
                padding: 6px 10px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover_bg']};
                color: {theme['button_hover_text']};
            }}
            QPushButton:pressed {{
                background-color: {theme['button_pressed_bg']};
                color: {theme['button_pressed_text']};
            }}
        """)
    
    def _apply_status_bar_stylesheet(self, theme: dict[str, str]) -> None:
        """
        Apply status bar stylesheet.
        
        Args:
            theme: Theme dictionary with color values
        """
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {theme['window_bg']};
                color: {theme['text_color']};
                border-top: 1px solid {theme['border_color']};
            }}
            QStatusBar QLabel {{
                color: {theme['text_color']};
                padding: 2px 8px;
            }}
        """)
    
    def _setup_background_image(self) -> None:
        """Setup background image for Image Mode."""
        if self.theme_manager.has_background():
            self.background_label = QLabel(self)
            self.background_label.setScaledContents(True)
            self.background_label.setPixmap(self.theme_manager.get_background_pixmap())
            self.background_label.setGeometry(0, 0, self.width(), self.height())
            self.background_label.lower()
            self.background_label.setVisible(True)
            self.background_label.update()
    
    def _apply_image_mode_stylesheets(self) -> None:
        """Apply all stylesheets for Image Mode."""
        im = IMAGE_MODE_COLORS
        scrollbar_style = self.theme_manager.get_scrollbar_style()

        # Main window
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {im['window_bg']}; }}
            QPushButton {{
                background-color: {im['panel_bg']};
                border: none;
                padding: 0px;
                margin: 0px;
            }}
            QCheckBox {{
                color: {im['text_primary']};
            }}
            QListWidget {{
                background-color: {im['panel_bg']};
                color: {im['text_primary']};
                border: none;
            }}
            QListWidget::item {{
                padding: 3px 6px;
            }}
            QListWidget::item:hover {{
                background-color: {BRAND_GOLD};
                color: {im['text_on_accent']};
            }}
            QListWidget::item:selected {{
                background-color: {BRAND_GOLD};
                color: {im['text_on_accent']};
            }}
            {scrollbar_style}
        """)

        # Drop zone
        self.drop_label.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {im['dropzone_border']};
                border-radius: 5px;
                padding: 40px;
                background-color: {im['dropzone_bg']};
                color: {im['text_primary']};
                font-size: 14px;
                font-weight: bold;
            }}
        """)

        # Preview frame
        self.preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {im['panel_bg']};
                border: none;
            }}
        """)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {im['scrollbar_bg']};
                border: none;
            }}
        """)

        # Theme button — follows dark mode inverse styling
        self.theme_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {im['main_btn_bg']};
                color: {im['main_btn_text']};
                padding: 6px 5px;
                border: 1px solid {im['main_btn_border']};
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {im['main_btn_hover_bg']};
                color: {im['main_btn_hover_text']};
            }}
            QPushButton:pressed {{
                background-color: {im['main_btn_pressed_bg']};
                color: {im['main_btn_pressed_text']};
            }}
        """)

        # Status bar
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {im['statusbar_bg']};
                color: {im['text_primary']};
                border-top: 1px solid {im['statusbar_border']};
            }}
            QStatusBar QLabel {{
                color: {im['text_primary']};
                padding: 2px 8px;
            }}
        """)


# ==================== Main Entry Point ====================

def main() -> None:
    """Main entry point for the application."""
    # Setup logging FIRST
    setup_logger(
        name='RNV_Icon_Builder',
        level=logging.INFO,  # Change to logging.DEBUG for verbose output
        log_to_file=True
    )
    
    # Get Logger instance for main()
    main_logger: Logger = get_logger_instance(__name__)
    main_logger.header(f"{APP_NAME} v{APP_VERSION}")
    main_logger.info("Starting application...")
    
    app = QApplication(sys.argv)
    
    # Use Fusion style for consistent cross-platform rendering
    app.setStyle("Fusion")
    
    # Load and set global font
    main_logger.info("Loading custom font...")
    font = load_embedded_font()
    app.setFont(font)
    main_logger.success("Font applied to application")
    
    # Set application icon
    if APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        main_logger.success("Loaded application icon")
    else:
        main_logger.warning(f"Icon not found: {APP_ICON_PATH.name}")
    
    # Create and show main window
    main_logger.info("Creating main window...")
    window = IconBuilderApp()
    window.show()
    
    main_logger.separator()
    main_logger.success("Application ready!")
    main_logger.separator()
    
    # Run application
    exit_code = app.exec()
    
    main_logger.separator()
    main_logger.info(f"Application exiting with code: {exit_code}")
    main_logger.separator()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()