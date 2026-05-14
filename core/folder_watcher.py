"""
RNV Icon Builder - Folder Watcher Module
Monitors a folder for new images and auto-processes them.

Features:
- Watch folder for new image files
- Auto-process with configurable settings
- Debounce rapid file changes
- Background thread monitoring
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
from dataclasses import dataclass
import threading

from PyQt6.QtCore import QObject, pyqtSignal, QFileSystemWatcher, QTimer

from utils.config import ICON_SIZES, SUPPORTED_EXTENSIONS
from utils.logger import Logger, get_logger_instance
from utils.file_utils import FileUtils

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)


@dataclass
class WatchSettings:
    """
    Settings for folder watching.
    
    Attributes:
        input_folder: Folder to watch for new files
        output_folder: Folder to output ICO files
        sizes: List of sizes to include in ICO
        autofill: Whether to autofill missing sizes
        png_compression: Whether to use PNG compression
        recursive: Watch subfolders
        delete_source: Delete source after processing
        overwrite_existing: Overwrite existing ICO files
    """
    input_folder: str = ""
    output_folder: str = ""
    sizes: list[int] | None = None
    autofill: bool = True
    png_compression: bool = True
    recursive: bool = False
    delete_source: bool = False
    overwrite_existing: bool = True
    
    def __post_init__(self):
        if self.sizes is None:
            self.sizes = ICON_SIZES.copy()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'input_folder': self.input_folder,
            'output_folder': self.output_folder,
            'sizes': self.sizes,
            'autofill': self.autofill,
            'png_compression': self.png_compression,
            'recursive': self.recursive,
            'delete_source': self.delete_source,
            'overwrite_existing': self.overwrite_existing
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WatchSettings:
        """Create from dictionary."""
        return cls(
            input_folder=data.get('input_folder', ''),
            output_folder=data.get('output_folder', ''),
            sizes=data.get('sizes'),
            autofill=data.get('autofill', True),
            png_compression=data.get('png_compression', True),
            recursive=data.get('recursive', False),
            delete_source=data.get('delete_source', False),
            overwrite_existing=data.get('overwrite_existing', True)
        )


class FolderWatcher(QObject):
    """
    Monitors a folder for new images and auto-processes them to ICO.
    
    Uses QFileSystemWatcher for file system monitoring with debouncing
    to handle rapid successive file changes.
    
    Signals:
        file_detected: Emitted when a new file is detected (file_path)
        file_processed: Emitted when a file is processed (file_path, output_path, success)
        watch_started: Emitted when watching starts (folder_path)
        watch_stopped: Emitted when watching stops
        error_occurred: Emitted on errors (error_message)
        
    Example:
        >>> watcher = FolderWatcher()
        >>> settings = WatchSettings(
        ...     input_folder="/path/to/watch",
        ...     output_folder="/path/to/output"
        ... )
        >>> watcher.start_watching(settings)
        >>> # ... later ...
        >>> watcher.stop_watching()
    """
    
    # Signals
    file_detected = pyqtSignal(str)          # file_path
    file_processed = pyqtSignal(str, str, bool)  # file_path, output_path, success
    watch_started = pyqtSignal(str)          # folder_path
    watch_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)         # error_message
    
    # Debounce delay in milliseconds
    DEBOUNCE_DELAY = 500
    
    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the folder watcher."""
        super().__init__(parent)
        
        self._watcher: QFileSystemWatcher | None = None
        self._settings: WatchSettings | None = None
        self._is_watching: bool = False
        self._processed_files: set[str] = set()
        
        # Debounce timer
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._process_pending_files)
        
        # Pending files queue
        self._pending_files: list[str] = []
        self._pending_lock = threading.Lock()
        
        # Processing lock to prevent concurrent processing
        self._processing_lock = threading.Lock()
        
        logger.debug("FolderWatcher initialized")
    
    def start_watching(self, settings: WatchSettings) -> bool:
        """
        Start watching a folder for new images.
        
        Args:
            settings: Watch settings including input/output folders
            
        Returns:
            True if watching started successfully
        """
        if self._is_watching:
            logger.warning("Already watching a folder")
            return False
        
        # Validate settings
        if not settings.input_folder:
            self.error_occurred.emit("Input folder not specified")
            return False
        
        if not os.path.isdir(settings.input_folder):
            self.error_occurred.emit(f"Input folder does not exist: {settings.input_folder}")
            return False
        
        if not settings.output_folder:
            self.error_occurred.emit("Output folder not specified")
            return False
        
        # Create output folder if needed
        if not FileUtils.create_directory_if_not_exists(settings.output_folder):
            self.error_occurred.emit(f"Cannot create output folder: {settings.output_folder}")
            return False
        
        self._settings = settings
        self._processed_files.clear()
        self._pending_files.clear()
        
        # Setup file system watcher
        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_directory_changed)
        self._watcher.fileChanged.connect(self._on_file_changed)
        
        # Add input folder to watch
        if not self._watcher.addPath(settings.input_folder):
            self.error_occurred.emit(f"Failed to watch folder: {settings.input_folder}")
            return False
        
        # If recursive, add subfolders
        if settings.recursive:
            for root, dirs, _ in os.walk(settings.input_folder):
                for d in dirs:
                    subdir = os.path.join(root, d)
                    self._watcher.addPath(subdir)
        
        self._is_watching = True
        logger.info(f"Started watching folder: {settings.input_folder}")
        self.watch_started.emit(settings.input_folder)
        
        # Process any existing files
        self._scan_existing_files()
        
        return True
    
    def stop_watching(self) -> None:
        """Stop watching the folder."""
        if not self._is_watching:
            return
        
        self._is_watching = False
        
        if self._watcher:
            # Stop timers
            self._debounce_timer.stop()
            
            # Remove all watched paths
            dirs = self._watcher.directories()
            files = self._watcher.files()
            if dirs:
                self._watcher.removePaths(dirs)
            if files:
                self._watcher.removePaths(files)
            
            self._watcher.deleteLater()
            self._watcher = None
        
        logger.info("Stopped watching folder")
        self.watch_stopped.emit()
    
    def is_watching(self) -> bool:
        """Check if currently watching."""
        return self._is_watching
    
    def get_settings(self) -> WatchSettings | None:
        """Get current watch settings."""
        return self._settings
    
    def get_processed_count(self) -> int:
        """Get number of files processed in this session."""
        return len(self._processed_files)
    
    def _scan_existing_files(self) -> None:
        """Scan for existing files in watched folder."""
        if not self._settings:
            return
        
        folder = Path(self._settings.input_folder)
        
        if self._settings.recursive:
            files = folder.rglob('*')
        else:
            files = folder.glob('*')
        
        for file_path in files:
            if file_path.is_file() and self._is_valid_image(str(file_path)):
                self._queue_file(str(file_path))
        
        # Start debounce timer if files were queued
        if self._pending_files:
            self._debounce_timer.start(self.DEBOUNCE_DELAY)
    
    def _on_directory_changed(self, path: str) -> None:
        """Handle directory change event."""
        if not self._is_watching or not self._settings:
            return
        
        logger.debug(f"Directory changed: {path}")
        
        # Scan for new files
        folder = Path(path)
        for file_path in folder.iterdir():
            if file_path.is_file() and self._is_valid_image(str(file_path)):
                self._queue_file(str(file_path))
        
        # Restart debounce timer
        self._debounce_timer.start(self.DEBOUNCE_DELAY)
    
    def _on_file_changed(self, path: str) -> None:
        """Handle file change event."""
        if not self._is_watching:
            return
        
        logger.debug(f"File changed: {path}")
        
        if self._is_valid_image(path):
            self._queue_file(path)
            self._debounce_timer.start(self.DEBOUNCE_DELAY)
    
    def _queue_file(self, file_path: str) -> None:
        """Add file to pending queue if not already processed."""
        file_path = os.path.abspath(file_path)
        
        with self._pending_lock:
            if file_path not in self._processed_files and file_path not in self._pending_files:
                self._pending_files.append(file_path)
                logger.debug(f"Queued file: {file_path}")
    
    def _is_valid_image(self, file_path: str) -> bool:
        """Check if file is a valid image for processing."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in SUPPORTED_EXTENSIONS
    
    def _process_pending_files(self) -> None:
        """Process all pending files."""
        if not self._is_watching or not self._settings:
            return
        
        # Get and clear pending files
        with self._pending_lock:
            files_to_process = self._pending_files.copy()
            self._pending_files.clear()
        
        if not files_to_process:
            return
        
        logger.info(f"Processing {len(files_to_process)} file(s)")
        
        # Process each file
        for file_path in files_to_process:
            if not self._is_watching:
                break
            
            self._process_file(file_path)
    
    def _process_file(self, file_path: str) -> bool:
        """
        Process a single file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if processing succeeded
        """
        from core.image_processor import ImageProcessor
        from core.icon_builder_core import IconBuilderCore
        
        if not self._settings:
            return False
        
        file_path = os.path.abspath(file_path)
        
        # Check if already processed
        if file_path in self._processed_files:
            return True
        
        # Check if file still exists
        if not FileUtils.validate_file_path(file_path, must_exist=True):
            logger.warning(f"File no longer exists: {file_path}")
            return False
        
        # Wait briefly for file to be fully written
        time.sleep(0.1)
        
        self.file_detected.emit(file_path)
        
        # Generate output path
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        output_path = os.path.join(self._settings.output_folder, f"{name_without_ext}.ico")
        
        # Check if output exists and we shouldn't overwrite
        if FileUtils.validate_file_path(output_path, must_exist=True) and not self._settings.overwrite_existing:
            logger.warning(f"Output exists, skipping: {output_path}")
            self._processed_files.add(file_path)
            return True
        
        # Load image
        processor = ImageProcessor()
        ext = FileUtils.get_file_extension(file_path)
        
        try:
            with self._processing_lock:
                if ext == '.png':
                    processor.load_png(file_path)
                elif ext == '.ico':
                    processor.load_ico(file_path)
                elif ext == '.svg':
                    processor.load_svg(file_path)
                else:
                    return False
                
                images = processor.get_detected_images()
                if not images:
                    logger.warning(f"No valid images from: {file_path}")
                    self.file_processed.emit(file_path, "", False)
                    return False
                
                # Build ICO
                success, message, info = IconBuilderCore.build_ico_file(
                    images_dict=images,
                    output_path=output_path,
                    autofill=self._settings.autofill,
                    selected_sizes=self._settings.sizes,
                    use_png_compression=self._settings.png_compression
                )
                
                if success:
                    self._processed_files.add(file_path)
                    logger.success(f"Auto-processed: {filename} -> {output_path}")
                    self.file_processed.emit(file_path, output_path, True)
                    
                    # Delete source if configured
                    if self._settings.delete_source:
                        try:
                            os.remove(file_path)
                            logger.debug(f"Deleted source: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete source: {e}")
                    
                    return True
                else:
                    logger.error(f"Failed to process: {message}")
                    self.file_processed.emit(file_path, output_path, False)
                    return False
                    
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.file_processed.emit(file_path, "", False)
            return False
    
    def process_file_manually(self, file_path: str) -> bool:
        """
        Manually trigger processing of a specific file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if processing succeeded
        """
        if not self._settings:
            logger.warning("No watch settings configured")
            return False
        
        return self._process_file(file_path)


# ==================== Module Exports ====================

__all__: list[str] = [
    'WatchSettings',
    'FolderWatcher',
]