"""
RNV Icon Builder - Configuration Module
Contains all application constants, paths, and configuration settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Final

# ==================== Application Info ====================
APP_NAME: Final[str] = "RNV Icon Builder"
APP_VERSION: Final[str] = "3.0.0"
APP_AUTHOR: Final[str] = "RNV"

# ==================== Icon Sizes ====================
ICON_SIZES: Final[list[int]] = [256, 128, 64, 48, 32, 16]
"""Standard ICO file resolutions in descending order"""

# Largest standard icon size
MAX_ICON_SIZE: Final[int] = 256

# Smallest standard icon size
MIN_ICON_SIZE: Final[int] = 16

# ==================== Paths ====================
# Get the project root directory (parent of utils folder)
BASE_DIR: Final[Path] = Path(os.path.dirname(os.path.abspath(__file__))).parent
RESOURCES_DIR: Final[Path] = BASE_DIR / "resources"
BUTTON_IMAGES_DIR: Final[Path] = RESOURCES_DIR / "button_images"
BACKGROUND_IMAGES_DIR: Final[Path] = RESOURCES_DIR / "background_images"
FONTS_DIR: Final[Path] = RESOURCES_DIR / "fonts"
ICONS_DIR: Final[Path] = RESOURCES_DIR / "icons"

# User data directory
USER_DATA_DIR: Final[Path] = Path.home() / ".rnv_icon_builder"
LOGS_DIR: Final[Path] = USER_DATA_DIR / "logs"
SESSIONS_DIR: Final[Path] = USER_DATA_DIR / "sessions"
CACHE_DIR: Final[Path] = USER_DATA_DIR / "cache"

# Recent files
RECENT_FILES_PATH: Final[Path] = USER_DATA_DIR / "recent_files.json"
"""Path to recent files history JSON file"""

MAX_RECENT_FILES: Final[int] = 15
"""Maximum number of recent files/folders to track"""

# ==================== Workflow Automation Paths ====================
# Presets
PRESETS_DIR: Final[Path] = USER_DATA_DIR / "presets"
"""Directory for custom preset files"""

PRESETS_FILE_PATH: Final[Path] = USER_DATA_DIR / "presets.json"
"""Path to presets JSON file"""

# Projects
PROJECTS_DIR: Final[Path] = USER_DATA_DIR / "projects"
"""Directory for project files"""

PROJECT_FILE_EXTENSION: Final[str] = ".rnvicon"
"""File extension for project files"""

# Auto-save and session
AUTO_SAVE_PATH: Final[Path] = USER_DATA_DIR / "autosave.rnvicon"
"""Path to auto-save project file"""

LAST_SESSION_PATH: Final[Path] = USER_DATA_DIR / "last_session.rnvicon"
"""Path to last session project file"""

# Watch folder
WATCH_CONFIG_PATH: Final[Path] = USER_DATA_DIR / "watch_config.json"
"""Path to watch folder configuration"""

# Application settings
SETTINGS_PATH: Final[Path] = USER_DATA_DIR / "settings.json"
"""Path to user settings JSON file"""

# ==================== File Paths ====================
BACKGROUND_IMAGE_PATH: Final[Path] = BACKGROUND_IMAGES_DIR / "background.png"
APP_ICON_PATH: Final[Path] = ICONS_DIR / "icon.png"
FONT_PATH: Final[Path] = FONTS_DIR / "Montserrat-Black.ttf"

# ==================== Window Configuration ====================
# Window dimensions
MIN_WINDOW_WIDTH: Final[int] = 900
MIN_WINDOW_HEIGHT: Final[int] = 700
DEFAULT_WINDOW_WIDTH: Final[int] = 1000
DEFAULT_WINDOW_HEIGHT: Final[int] = 800

# Window position
WINDOW_X: Final[int] = 100
WINDOW_Y: Final[int] = 100

# ==================== Button Configuration ====================
# Action button dimensions
MIN_BUTTON_WIDTH: Final[int] = 72
MIN_BUTTON_HEIGHT: Final[int] = 40
DEFAULT_BUTTON_WIDTH: Final[int] = 110
DEFAULT_BUTTON_HEIGHT: Final[int] = 40

# Remove button dimensions
REMOVE_BUTTON_WIDTH: Final[int] = 80
REMOVE_BUTTON_HEIGHT: Final[int] = 50

# Theme button
THEME_BUTTON_MARGIN: Final[int] = 20

# ==================== UI Element Sizes ====================
# Thumbnail preview
THUMBNAIL_SIZE: Final[int] = 48
"""Size in pixels for thumbnail previews in the preview area"""

# Drop zone
DROP_ZONE_MIN_HEIGHT: Final[int] = 80
"""Minimum height for drag-and-drop zone"""

# File list
FILE_LIST_MAX_HEIGHT: Final[int] = 120
"""Maximum height for file list widget"""

# Color swatch (for future color-related features)
COLOR_SWATCH_WIDTH: Final[int] = 60
COLOR_SWATCH_HEIGHT: Final[int] = 40

# ==================== Image Processing Limits ====================
# Maximum image dimensions
MAX_IMAGE_DIMENSION: Final[int] = 3840
"""Maximum width/height for images (4K resolution)"""

# File size limits
MAX_FILE_SIZE_MB: Final[int] = 200
"""Maximum file size in megabytes"""

MAX_FILE_SIZE_BYTES: Final[int] = MAX_FILE_SIZE_MB * 1024 * 1024
"""Maximum file size in bytes"""

# Image pixel limits
MAX_IMAGE_PIXELS: Final[int] = 100_000_000
"""Maximum total pixels (100 million) - prevents memory bombs"""

# ==================== ICO Building Constants ====================
# BMP header size
BMP_HEADER_SIZE: Final[int] = 40
"""Size of BITMAPINFOHEADER in bytes"""

# ICO file header
ICO_HEADER_SIZE: Final[int] = 6
"""Size of ICO file header in bytes"""

ICO_DIR_ENTRY_SIZE: Final[int] = 16
"""Size of each ICO directory entry in bytes"""

# Bits per pixel
BITS_PER_PIXEL: Final[int] = 32
"""Bits per pixel for ICO images (RGBA)"""

# Bytes per pixel
BYTES_PER_PIXEL: Final[int] = 4
"""Bytes per pixel (BGRA format)"""

# Color planes
COLOR_PLANES: Final[int] = 1
"""Number of color planes (always 1 for ICO)"""

# Alpha threshold for AND mask
ALPHA_THRESHOLD: Final[int] = 128
"""Alpha value threshold - below this is transparent (0-255)"""

# ==================== Timing Constants ====================
# Drag tracking
DRAG_TRACK_FPS: Final[int] = 60
"""Frames per second for drag tracking"""

DRAG_TRACK_INTERVAL: Final[int] = 1000 // DRAG_TRACK_FPS  # 16ms
"""Timer interval in milliseconds for drag tracking (16ms = ~60fps)"""

# Auto-save interval (in seconds)
AUTO_SAVE_INTERVAL: Final[int] = 60
"""Auto-save interval in seconds"""

# Status message timeout (in milliseconds)
STATUS_MESSAGE_TIMEOUT: Final[int] = 3000
"""How long to show status messages (2 seconds)"""

# ==================== Logging Configuration ====================
# Log file settings
LOG_FILE_MAX_SIZE: Final[int] = 5 * 1024 * 1024  # 5MB
"""Maximum log file size before rotation"""

LOG_FILE_BACKUP_COUNT: Final[int] = 3
"""Number of backup log files to keep"""

# Default log level
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
"""Default logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"""

# ==================== Validation Constants ====================
# Image validation
REQUIRE_SQUARE_IMAGES: Final[bool] = True
"""Whether to require square images (width == height)"""

# File name validation
MAX_FILENAME_LENGTH: Final[int] = 255
"""Maximum length for filenames"""

# Path validation
MAX_PATH_LENGTH: Final[int] = 260
"""Maximum path length (Windows limitation)"""

# ==================== Preview Constants ====================
# Transparency checkerboard
TRANSPARENCY_CHECKERBOARD_SIZE: Final[int] = 8
"""Size of checkerboard pattern squares for transparency visualization"""

# Thumbnail frame
THUMBNAIL_FRAME_PADDING: Final[int] = 5
"""Padding around thumbnails in pixels"""

THUMBNAIL_BORDER_RADIUS: Final[int] = 3
"""Border radius for thumbnail frames"""

# Preview layout
PREVIEW_FRAME_MARGINS: Final[tuple[int, int, int, int]] = (10, 10, 10, 10)
"""Margins for preview frame (left, top, right, bottom)"""

PREVIEW_FRAME_SPACING: Final[int] = 5
"""Spacing between preview items"""

# ==================== Preview Enhancement Constants ====================
# Preview background options
PREVIEW_BG_CHECKERBOARD: Final[str] = "checkerboard"
"""Transparency checkerboard background"""

PREVIEW_BG_WHITE: Final[str] = "white"
"""White background"""

PREVIEW_BG_BLACK: Final[str] = "black"
"""Black background"""

PREVIEW_BG_CUSTOM: Final[str] = "custom"
"""Custom color background"""

PREVIEW_BACKGROUND_OPTIONS: Final[list[str]] = [
    PREVIEW_BG_CHECKERBOARD,
    PREVIEW_BG_WHITE,
    PREVIEW_BG_BLACK,
    PREVIEW_BG_CUSTOM,
]
"""Available background preview options"""

DEFAULT_PREVIEW_BACKGROUND: Final[str] = PREVIEW_BG_CHECKERBOARD
"""Default background for previews"""

# Zoom controls
ZOOM_MIN: Final[int] = 50
"""Minimum zoom percentage"""

ZOOM_MAX: Final[int] = 400
"""Maximum zoom percentage"""

ZOOM_DEFAULT: Final[int] = 100
"""Default zoom percentage"""

ZOOM_STEP: Final[int] = 25
"""Zoom step increment"""

# Color palette extraction
COLOR_PALETTE_SIZE: Final[int] = 5
"""Number of dominant colors to extract"""

COLOR_SWATCH_SIZE: Final[int] = 24
"""Size of color swatches in pixels"""

# Context preview sizes
CONTEXT_PREVIEW_TASKBAR_SIZE: Final[int] = 24
"""Size for taskbar icon context preview"""

CONTEXT_PREVIEW_FOLDER_SIZE: Final[int] = 48
"""Size for folder icon context preview"""

CONTEXT_PREVIEW_DESKTOP_SIZE: Final[int] = 64
"""Size for desktop shortcut context preview"""

CONTEXT_PREVIEW_DOCK_SIZE: Final[int] = 64
"""Size for macOS dock context preview"""

CONTEXT_PREVIEW_FAVICON_SIZE: Final[int] = 16
"""Size for browser favicon context preview"""

# ==================== File Type Filters ====================
IMAGE_FILE_FILTER: Final[str] = "Image Files (*.png *.ico *.svg)"
ICO_FILE_FILTER: Final[str] = "ICO Files (*.ico)"
PNG_FILE_FILTER: Final[str] = "PNG Files (*.png)"
SVG_FILE_FILTER: Final[str] = "SVG Files (*.svg)"
ALL_FILES_FILTER: Final[str] = "All Files (*.*)"

SUPPORTED_EXTENSIONS: Final[list[str]] = ['.png', '.ico', '.svg']
"""List of supported file extensions"""

SUPPORTED_IMAGE_FORMATS: Final[list[str]] = ['PNG', 'ICO', 'SVG']
"""List of supported image format names"""

# ==================== Error Messages ====================
# Common error messages as constants
ERROR_NO_FILES_LOADED: Final[str] = "Please load some PNG/ICO files first."
ERROR_FILE_NOT_FOUND: Final[str] = "File not found: {path}"
ERROR_PERMISSION_DENIED: Final[str] = "Permission denied: {path}"
ERROR_INVALID_IMAGE: Final[str] = "Invalid or corrupted image: {path}"
ERROR_WRONG_SIZE: Final[str] = "Image size {size}x{size} is not a standard icon size."
ERROR_NOT_SQUARE: Final[str] = "Image must be square (width must equal height)."

# Success messages
SUCCESS_ICO_CREATED: Final[str] = "Multi-resolution ICO created successfully!"
SUCCESS_FILES_LOADED: Final[str] = "Loaded {count} file(s) successfully."
SUCCESS_FILES_CLEARED: Final[str] = "All files cleared successfully."

# ==================== Dialog Text ====================
# Confirmation dialog
CONFIRM_CLEAR_TITLE: Final[str] = "Confirm Clear"
CONFIRM_CLEAR_MESSAGE: Final[str] = "Clear all loaded files?"
CONFIRM_CLEAR_DETAILS: Final[str] = "{count} file(s) will be removed."

# File dialogs
DIALOG_SELECT_FILES: Final[str] = "Select Image Files"
DIALOG_SELECT_FOLDER: Final[str] = "Select Folder"
DIALOG_SAVE_ICO: Final[str] = "Save Multi-Resolution Icon"

# ==================== Performance Settings ====================
# Cache settings
ENABLE_PIXMAP_CACHE: Final[bool] = True
"""Whether to cache pixmaps for performance"""

MAX_CACHE_SIZE_MB: Final[int] = 100
"""Maximum cache size in megabytes"""

THUMBNAIL_CACHE_MAX_SIZE: Final[int] = 50
"""Maximum number of cached thumbnails.
Typical usage: 6 icon sizes x ~4 variants (default, checker, hover, etc.) = 24.
Set to 50 for comfortable headroom without excessive memory use.
Each thumbnail is small (48x48 or similar), so memory impact is minimal."""

# Threading
ENABLE_ASYNC_FILE_OPS: Final[bool] = False
"""Whether to use async file operations (future feature)"""

# ==================== Debug Settings ====================
# Debug mode
DEBUG_MODE: Final[bool] = False
"""Enable debug mode (shows additional logging and overlays)"""

# Show debug overlay
SHOW_DEBUG_OVERLAY: Final[bool] = False
"""Show debug overlay on panels (F12 key toggles)"""

# Show tooltips
SHOW_TOOLTIPS: Final[bool] = True
"""Show tooltips on UI elements"""

# Verbose logging
VERBOSE_LOGGING: Final[bool] = False
"""Enable verbose logging (DEBUG level)"""

# ==================== Feature Flags ====================
# Optional features that can be enabled/disabled
ENABLE_AUTO_SAVE: Final[bool] = True
"""Enable auto-save functionality"""

ENABLE_CRASH_RECOVERY: Final[bool] = True
"""Enable crash recovery on startup"""

ENABLE_THEME_CYCLING: Final[bool] = True
"""Enable theme cycling (Dark/Light/Image)"""

ENABLE_IMAGE_MODE: Final[bool] = True
"""Enable Image Mode theme (requires background image)"""

ENABLE_CONTEXT_MENUS: Final[bool] = True
"""Enable right-click context menus"""

ENABLE_KEYBOARD_SHORTCUTS: Final[bool] = True
"""Enable keyboard shortcuts"""

# ==================== Startup Options ====================
# Session restoration settings (can be modified by user)
DEFAULT_RESTORE_LAST_SESSION: Final[bool] = False
"""Default setting for restoring last session on startup"""

AUTO_SAVE_INTERVAL_SECONDS: Final[int] = 300
"""Auto-save interval in seconds (5 minutes)"""

ENABLE_SESSION_RESTORE: Final[bool] = True
"""Enable session restore feature (user can toggle in settings)"""

MAX_AUTO_SAVE_AGE_HOURS: Final[int] = 24
"""Maximum age of auto-save file to consider valid (hours)"""

# ==================== Keyboard Shortcuts ====================
# Default keyboard shortcuts (can be customized)
SHORTCUT_OPEN_FILES: Final[str] = "Ctrl+O"
SHORTCUT_OPEN_FOLDER: Final[str] = "Ctrl+Shift+O"
SHORTCUT_CLEAR_FILES: Final[str] = "Ctrl+N"
SHORTCUT_BUILD_ICO: Final[str] = "Ctrl+B"
SHORTCUT_SETTINGS: Final[str] = "Ctrl+,"
SHORTCUT_REFRESH_PREVIEW: Final[str] = "F5"
SHORTCUT_TOGGLE_TOOLTIPS: Final[str] = "F11"
SHORTCUT_TOGGLE_DEBUG: Final[str] = "F12"
SHORTCUT_QUIT: Final[str] = "Ctrl+Q"

# ==================== Batch Operation Limits ====================
# Maximum number of files to process in one batch
MAX_BATCH_SIZE: Final[int] = 1000
"""Maximum files to process at once"""

# Progress dialog threshold
SHOW_PROGRESS_THRESHOLD: Final[int] = 10
"""Show progress dialog if processing more than this many files"""


# ==================== Helper Functions ====================

def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    Args:
        relative_path: Relative path from resources directory
        
    Returns:
        Absolute path to resource
    """
    return RESOURCES_DIR / relative_path


def resource_exists(relative_path: str) -> bool:
    """
    Check if a resource file exists.
    
    Args:
        relative_path: Relative path from resources directory
        
    Returns:
        True if resource exists
    """
    return (RESOURCES_DIR / relative_path).exists()


def get_button_image_paths(button_name: str) -> dict[str, Path]:
    """
    Get paths for button images (base, hover, pressed).
    
    Args:
        button_name: Name of button (e.g., "Select Files")
        
    Returns:
        Dictionary with 'base', 'hover', 'pressed' keys mapping to Path objects
    """
    btn_name: str = button_name.lower().replace(' ', '-')
    return {
        'base': BUTTON_IMAGES_DIR / f"{btn_name}_base.png",
        'hover': BUTTON_IMAGES_DIR / f"{btn_name}_hover.png",
        'pressed': BUTTON_IMAGES_DIR / f"{btn_name}_pressed.png"
    }


def ensure_directories() -> None:
    """
    Ensure all required directories exist.
    Creates user data directories if they don't exist.
    """
    directories: list[Path] = [
        USER_DATA_DIR,
        LOGS_DIR,
        SESSIONS_DIR,
        CACHE_DIR,
        PRESETS_DIR,
        PROJECTS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_config_summary() -> dict[str, Any]:
    """
    Get a summary of current configuration.
    Useful for debugging and logging.
    
    Returns:
        Configuration summary dictionary
    """
    return {
        'app_name': APP_NAME,
        'app_version': APP_VERSION,
        'debug_mode': DEBUG_MODE,
        'icon_sizes': ICON_SIZES,
        'max_file_size_mb': MAX_FILE_SIZE_MB,
        'auto_save_enabled': ENABLE_AUTO_SAVE,
        'image_mode_enabled': ENABLE_IMAGE_MODE,
        'window_size': f"{MIN_WINDOW_WIDTH}x{MIN_WINDOW_HEIGHT}",
        'resources_dir': str(RESOURCES_DIR),
        'user_data_dir': str(USER_DATA_DIR),
    }


# ==================== Module Initialization ====================
# Ensure directories exist when module is imported
ensure_directories()


# ==================== Exports ====================
__all__: list[str] = [
    # App info
    'APP_NAME', 'APP_VERSION', 'APP_AUTHOR',
    
    # Icon sizes
    'ICON_SIZES', 'MAX_ICON_SIZE', 'MIN_ICON_SIZE',
    
    # Paths
    'BASE_DIR', 'RESOURCES_DIR', 'USER_DATA_DIR', 'LOGS_DIR',
    'BUTTON_IMAGES_DIR', 'BACKGROUND_IMAGES_DIR', 'FONTS_DIR', 'ICONS_DIR',
    'BACKGROUND_IMAGE_PATH', 'APP_ICON_PATH', 'FONT_PATH',
    'RECENT_FILES_PATH', 'MAX_RECENT_FILES',
    
    # Workflow automation paths
    'PRESETS_DIR', 'PRESETS_FILE_PATH', 'PROJECTS_DIR', 'PROJECT_FILE_EXTENSION',
    'AUTO_SAVE_PATH', 'LAST_SESSION_PATH', 'WATCH_CONFIG_PATH', 'SETTINGS_PATH',
    
    # Window config
    'MIN_WINDOW_WIDTH', 'MIN_WINDOW_HEIGHT', 'DEFAULT_WINDOW_WIDTH', 'DEFAULT_WINDOW_HEIGHT',
    'WINDOW_X', 'WINDOW_Y',
    
    # Button config
    'MIN_BUTTON_WIDTH', 'MIN_BUTTON_HEIGHT', 'DEFAULT_BUTTON_WIDTH', 'DEFAULT_BUTTON_HEIGHT',
    'THEME_BUTTON_MARGIN',
    
    # UI sizes
    'THUMBNAIL_SIZE', 'DROP_ZONE_MIN_HEIGHT', 'FILE_LIST_MAX_HEIGHT',
    
    # Image limits
    'MAX_IMAGE_DIMENSION', 'MAX_FILE_SIZE_MB', 'MAX_IMAGE_PIXELS',
    
    # ICO constants
    'BMP_HEADER_SIZE', 'ICO_HEADER_SIZE', 'ICO_DIR_ENTRY_SIZE',
    'BITS_PER_PIXEL', 'BYTES_PER_PIXEL', 'COLOR_PLANES', 'ALPHA_THRESHOLD',
    
    # Timing
    'DRAG_TRACK_FPS', 'DRAG_TRACK_INTERVAL', 'AUTO_SAVE_INTERVAL',
    'STATUS_MESSAGE_TIMEOUT',
    
    # Logging
    'LOG_FILE_MAX_SIZE', 'LOG_FILE_BACKUP_COUNT', 'DEFAULT_LOG_LEVEL',
    
    # File filters
    'IMAGE_FILE_FILTER', 'ICO_FILE_FILTER', 'PNG_FILE_FILTER', 'SVG_FILE_FILTER',
    'SUPPORTED_EXTENSIONS', 'SUPPORTED_IMAGE_FORMATS',
    
    # Error messages
    'ERROR_NO_FILES_LOADED', 'ERROR_FILE_NOT_FOUND', 'ERROR_PERMISSION_DENIED',
    'SUCCESS_ICO_CREATED', 'SUCCESS_FILES_LOADED',
    
    # Feature flags
    'ENABLE_AUTO_SAVE', 'ENABLE_CRASH_RECOVERY', 'ENABLE_IMAGE_MODE',
    'DEBUG_MODE', 'SHOW_TOOLTIPS',
    
    # Performance
    'THUMBNAIL_CACHE_MAX_SIZE',
    
    # Startup options
    'DEFAULT_RESTORE_LAST_SESSION', 'AUTO_SAVE_INTERVAL_SECONDS',
    'ENABLE_SESSION_RESTORE', 'MAX_AUTO_SAVE_AGE_HOURS',

    # Keyboard shortcuts
    'SHORTCUT_OPEN_FILES', 'SHORTCUT_BUILD_ICO', 'SHORTCUT_CLEAR_FILES',

    # Preview Enhancement constants
    'PREVIEW_BG_CHECKERBOARD', 'PREVIEW_BG_WHITE', 'PREVIEW_BG_BLACK', 'PREVIEW_BG_CUSTOM',
    'PREVIEW_BACKGROUND_OPTIONS', 'DEFAULT_PREVIEW_BACKGROUND',
    'ZOOM_MIN', 'ZOOM_MAX', 'ZOOM_DEFAULT', 'ZOOM_STEP',
    'COLOR_PALETTE_SIZE', 'COLOR_SWATCH_SIZE',
    'CONTEXT_PREVIEW_TASKBAR_SIZE', 'CONTEXT_PREVIEW_FOLDER_SIZE',
    'CONTEXT_PREVIEW_DESKTOP_SIZE', 'CONTEXT_PREVIEW_DOCK_SIZE', 'CONTEXT_PREVIEW_FAVICON_SIZE',

    # Helper functions
    'get_resource_path', 'resource_exists', 'get_button_image_paths',
    'ensure_directories', 'get_config_summary',
]