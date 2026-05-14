"""
RNV Icon Builder - Utils Package
Contains utility modules for configuration, logging, error handling, and helpers.

Modules:
    config: All configuration constants, paths, window dimensions
    logger: Colored logging, Logger class wrapper
    error_handler: ErrorHandler, safe_method decorator, exception_handler
    font_loader: Load embedded fonts with fallback support
    dialog_helper: DialogHelper for consistent themed dialogs
    pixmap_cache: QPixmapCache, ThumbnailCache with LRU eviction
    file_utils: FileUtils static methods for file operations
    signal_manager: SignalConnectionManager, SignalMixin, WindowMoveMixin
    async_file_ops: AsyncFileManager, threaded non-blocking I/O
"""

from .logger import Logger, setup_logger, get_logger_instance, get_logger
from .error_handler import ErrorHandler, ErrorCategory, safe_method, exception_handler
from .dialog_helper import DialogHelper, DialogResult
from .file_utils import FileUtils
from .font_loader import load_embedded_font, get_bold_font, get_regular_font, get_monospace_font
from .signal_manager import SignalConnectionManager, SignalMixin, WindowMoveMixin
from .pixmap_cache import QPixmapCache, ImagePixmapCache, ThumbnailCache
from .async_file_ops import AsyncFileManager, get_async_file_manager

__all__: list[str] = [
    # Logger
    'Logger', 'setup_logger', 'get_logger_instance', 'get_logger',
    # Error handling
    'ErrorHandler', 'ErrorCategory', 'safe_method', 'exception_handler',
    # Dialogs
    'DialogHelper', 'DialogResult',
    # File utilities
    'FileUtils',
    # Fonts
    'load_embedded_font', 'get_bold_font', 'get_regular_font', 'get_monospace_font',
    # Signals
    'SignalConnectionManager', 'SignalMixin', 'WindowMoveMixin',
    # Caching
    'QPixmapCache', 'ImagePixmapCache', 'ThumbnailCache',
    # Async
    'AsyncFileManager', 'get_async_file_manager',
]
