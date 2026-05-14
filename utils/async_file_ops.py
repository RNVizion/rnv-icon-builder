"""
RNV Icon Builder - Async File Operations Module
Non-blocking file I/O operations using Qt threads.

Features:
- Async file reading (JSON, text, binary)
- Async file writing with progress callbacks
- Thread-safe file operations
- Automatic format detection
- Error handling with callbacks

Usage Examples:
    # Async write
    manager = AsyncFileManager()
    manager.write_file_async(
        filepath="output.json",
        data={"key": "value"},
        on_complete=lambda path: print(f"Saved: {path}"),
        on_error=lambda e: print(f"Error: {e}"),
        format="json"
    )
    
    # Async read
    manager.read_file_async(
        filepath="input.json",
        on_complete=lambda data: process(data),
        on_error=lambda e: print(f"Error: {e}"),
        format="json"
    )
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable
from enum import Enum

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from utils.logger import Logger, get_logger_instance
from utils.file_utils import FileUtils

# Setup logger
logger: Logger = get_logger_instance(__name__)


class FileFormat(Enum):
    """Supported file formats for async operations."""
    JSON = "json"
    TEXT = "text"
    BINARY = "binary"
    AUTO = "auto"  # Auto-detect from extension


class FileWriterThread(QThread):
    """
    Thread for non-blocking file write operations.
    
    Emits signals on completion or error, allowing the main
    thread to remain responsive during file I/O.
    
    Signals:
        finished: Emitted when write completes (str filepath)
        error: Emitted on error (str error_message)
        progress: Emitted for progress updates (int percent)
    """
    
    finished = pyqtSignal(str)  # filepath
    error = pyqtSignal(str)     # error message
    progress = pyqtSignal(int)  # percent complete
    
    def __init__(
        self,
        filepath: str,
        data: Any,
        file_format: FileFormat = FileFormat.AUTO,
        encoding: str = "utf-8",
        parent: QObject | None = None
    ) -> None:
        """
        Initialize file writer thread.
        
        Args:
            filepath: Path to write to
            data: Data to write
            file_format: Format to use (json, text, binary, auto)
            encoding: Text encoding for non-binary files
            parent: Parent QObject
        """
        super().__init__(parent)
        self.filepath = filepath
        self.data = data
        self.file_format = file_format
        self.encoding = encoding
    
    def run(self) -> None:
        """Execute the file write operation."""
        try:
            self.progress.emit(0)
            
            # Determine format
            fmt = self._resolve_format()
            
            # Create directory if needed
            directory = os.path.dirname(self.filepath)
            if directory and not os.path.exists(directory):
                FileUtils.create_directory_if_not_exists(directory)
            
            self.progress.emit(25)
            
            # Write based on format
            if fmt == FileFormat.JSON:
                self._write_json()
            elif fmt == FileFormat.TEXT:
                self._write_text()
            elif fmt == FileFormat.BINARY:
                self._write_binary()
            
            self.progress.emit(100)
            self.finished.emit(self.filepath)
            logger.debug(f"Async write completed: {self.filepath}")
            
        except Exception as e:
            error_msg = f"Error writing file: {e}"
            logger.error(error_msg)
            self.error.emit(error_msg)
    
    def _resolve_format(self) -> FileFormat:
        """Resolve file format from extension if AUTO."""
        if self.file_format != FileFormat.AUTO:
            return self.file_format
        
        ext = os.path.splitext(self.filepath)[1].lower()
        
        if ext == '.json':
            return FileFormat.JSON
        elif ext in ('.txt', '.log', '.md', '.csv', '.xml', '.html'):
            return FileFormat.TEXT
        else:
            return FileFormat.BINARY
    
    def _write_json(self) -> None:
        """Write data as JSON."""
        with open(self.filepath, 'w', encoding=self.encoding) as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def _write_text(self) -> None:
        """Write data as text."""
        with open(self.filepath, 'w', encoding=self.encoding) as f:
            f.write(str(self.data))
    
    def _write_binary(self) -> None:
        """Write data as binary."""
        with open(self.filepath, 'wb') as f:
            if isinstance(self.data, bytes):
                f.write(self.data)
            elif isinstance(self.data, str):
                f.write(self.data.encode(self.encoding))
            else:
                raise ValueError(f"Cannot write {type(self.data)} as binary")


class FileReaderThread(QThread):
    """
    Thread for non-blocking file read operations.
    
    Emits signals on completion or error.
    
    Signals:
        finished: Emitted when read completes (object data)
        error: Emitted on error (str error_message)
        progress: Emitted for progress updates (int percent)
    """
    
    finished = pyqtSignal(object)  # data
    error = pyqtSignal(str)        # error message
    progress = pyqtSignal(int)     # percent complete
    
    def __init__(
        self,
        filepath: str,
        file_format: FileFormat = FileFormat.AUTO,
        encoding: str = "utf-8",
        parent: QObject | None = None
    ) -> None:
        """
        Initialize file reader thread.
        
        Args:
            filepath: Path to read from
            file_format: Format to use (json, text, binary, auto)
            encoding: Text encoding for non-binary files
            parent: Parent QObject
        """
        super().__init__(parent)
        self.filepath = filepath
        self.file_format = file_format
        self.encoding = encoding
    
    def run(self) -> None:
        """Execute the file read operation."""
        try:
            self.progress.emit(0)
            
            if not os.path.exists(self.filepath):
                raise FileNotFoundError(f"File not found: {self.filepath}")
            
            # Determine format
            fmt = self._resolve_format()
            
            self.progress.emit(25)
            
            # Read based on format
            if fmt == FileFormat.JSON:
                data = self._read_json()
            elif fmt == FileFormat.TEXT:
                data = self._read_text()
            elif fmt == FileFormat.BINARY:
                data = self._read_binary()
            
            self.progress.emit(100)
            self.finished.emit(data)
            logger.debug(f"Async read completed: {self.filepath}")
            
        except Exception as e:
            error_msg = f"Error reading file: {e}"
            logger.error(error_msg)
            self.error.emit(error_msg)
    
    def _resolve_format(self) -> FileFormat:
        """Resolve file format from extension if AUTO."""
        if self.file_format != FileFormat.AUTO:
            return self.file_format
        
        ext = os.path.splitext(self.filepath)[1].lower()
        
        if ext == '.json':
            return FileFormat.JSON
        elif ext in ('.txt', '.log', '.md', '.csv', '.xml', '.html'):
            return FileFormat.TEXT
        else:
            return FileFormat.BINARY
    
    def _read_json(self) -> Any:
        """Read data as JSON."""
        with open(self.filepath, 'r', encoding=self.encoding) as f:
            return json.load(f)
    
    def _read_text(self) -> str:
        """Read data as text."""
        with open(self.filepath, 'r', encoding=self.encoding) as f:
            return f.read()
    
    def _read_binary(self) -> bytes:
        """Read data as binary."""
        with open(self.filepath, 'rb') as f:
            return f.read()


class AsyncFileManager(QObject):
    """
    Manager for async file operations.
    
    Provides a high-level API for non-blocking file I/O with
    callbacks for completion and error handling.
    
    Example:
        manager = AsyncFileManager()
        
        # Write file asynchronously
        manager.write_file_async(
            filepath="data.json",
            data={"key": "value"},
            on_complete=lambda path: print(f"Saved to {path}"),
            on_error=lambda e: print(f"Error: {e}")
        )
        
        # Read file asynchronously
        manager.read_file_async(
            filepath="data.json",
            on_complete=lambda data: print(f"Loaded: {data}"),
            on_error=lambda e: print(f"Error: {e}")
        )
    
    Note:
        The manager keeps references to active threads to prevent
        premature garbage collection.
    """
    
    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the async file manager."""
        super().__init__(parent)
        
        # Keep references to active threads
        self._active_threads: list[QThread] = []
    
    def write_file_async(
        self,
        filepath: str,
        data: Any,
        on_complete: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_progress: Callable[[int], None] | None = None,
        file_format: str | FileFormat = "auto",
        encoding: str = "utf-8"
    ) -> FileWriterThread:
        """
        Write a file asynchronously.
        
        Args:
            filepath: Path to write to
            data: Data to write
            on_complete: Callback when write completes (receives filepath)
            on_error: Callback on error (receives error message)
            on_progress: Callback for progress (receives percent 0-100)
            file_format: Format to use ("json", "text", "binary", "auto")
            encoding: Text encoding for non-binary files
            
        Returns:
            The FileWriterThread instance
        
        Example:
            manager.write_file_async(
                "output.json",
                {"data": [1, 2, 3]},
                on_complete=lambda p: print(f"Saved: {p}")
            )
        """
        # Convert string format to enum
        if isinstance(file_format, str):
            file_format = FileFormat(file_format.lower())
        
        # Create thread
        thread = FileWriterThread(
            filepath=filepath,
            data=data,
            file_format=file_format,
            encoding=encoding,
            parent=self
        )
        
        # Connect signals
        if on_complete:
            thread.finished.connect(on_complete)
        if on_error:
            thread.error.connect(on_error)
        if on_progress:
            thread.progress.connect(on_progress)
        
        # Cleanup when done
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.error.connect(lambda: self._cleanup_thread(thread))
        
        # Track and start
        self._active_threads.append(thread)
        thread.start()
        
        logger.debug(f"Started async write: {filepath}")
        return thread
    
    def read_file_async(
        self,
        filepath: str,
        on_complete: Callable[[Any], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_progress: Callable[[int], None] | None = None,
        file_format: str | FileFormat = "auto",
        encoding: str = "utf-8"
    ) -> FileReaderThread:
        """
        Read a file asynchronously.
        
        Args:
            filepath: Path to read from
            on_complete: Callback when read completes (receives data)
            on_error: Callback on error (receives error message)
            on_progress: Callback for progress (receives percent 0-100)
            file_format: Format to use ("json", "text", "binary", "auto")
            encoding: Text encoding for non-binary files
            
        Returns:
            The FileReaderThread instance
        
        Example:
            manager.read_file_async(
                "input.json",
                on_complete=lambda data: print(f"Loaded: {data}")
            )
        """
        # Convert string format to enum
        if isinstance(file_format, str):
            file_format = FileFormat(file_format.lower())
        
        # Create thread
        thread = FileReaderThread(
            filepath=filepath,
            file_format=file_format,
            encoding=encoding,
            parent=self
        )
        
        # Connect signals
        if on_complete:
            thread.finished.connect(on_complete)
        if on_error:
            thread.error.connect(on_error)
        if on_progress:
            thread.progress.connect(on_progress)
        
        # Cleanup when done
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.error.connect(lambda: self._cleanup_thread(thread))
        
        # Track and start
        self._active_threads.append(thread)
        thread.start()
        
        logger.debug(f"Started async read: {filepath}")
        return thread
    
    def _cleanup_thread(self, thread: QThread) -> None:
        """Remove a completed thread from tracking."""
        if thread in self._active_threads:
            self._active_threads.remove(thread)
    
    def get_active_count(self) -> int:
        """Get number of active file operations."""
        return len(self._active_threads)
    
    def wait_all(self, timeout_ms: int = 30000) -> bool:
        """
        Wait for all active operations to complete.
        
        Args:
            timeout_ms: Maximum time to wait in milliseconds
            
        Returns:
            True if all operations completed, False if timeout
        """
        for thread in self._active_threads[:]:  # Copy list as it may be modified
            if not thread.wait(timeout_ms):
                return False
        return True
    
    def cancel_all(self) -> int:
        """
        Request cancellation of all active operations.
        
        Note: This requests termination but threads may not
        stop immediately if they're in the middle of I/O.
        
        Returns:
            Number of threads that were requested to terminate
        """
        count = 0
        for thread in self._active_threads[:]:
            if thread.isRunning():
                thread.requestInterruption()
                count += 1
        return count


class FileCopyThread(QThread):
    """
    Thread for non-blocking file copy operations.
    
    Signals:
        finished: Emitted when copy completes (str destination)
        error: Emitted on error (str error_message)
        progress: Emitted for progress updates (int percent)
    """
    
    finished = pyqtSignal(str)  # destination path
    error = pyqtSignal(str)     # error message
    progress = pyqtSignal(int)  # percent complete
    
    def __init__(
        self,
        source: str,
        destination: str,
        chunk_size: int = 1024 * 1024,  # 1MB chunks
        parent: QObject | None = None
    ) -> None:
        """
        Initialize file copy thread.
        
        Args:
            source: Source file path
            destination: Destination file path
            chunk_size: Size of chunks for progress reporting
            parent: Parent QObject
        """
        super().__init__(parent)
        self.source = source
        self.destination = destination
        self.chunk_size = chunk_size
    
    def run(self) -> None:
        """Execute the file copy operation."""
        try:
            if not os.path.exists(self.source):
                raise FileNotFoundError(f"Source not found: {self.source}")
            
            # Get file size for progress
            total_size = os.path.getsize(self.source)
            copied = 0
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(self.destination)
            if dest_dir and not os.path.exists(dest_dir):
                FileUtils.create_directory_if_not_exists(dest_dir)
            
            # Copy with progress
            with open(self.source, 'rb') as src:
                with open(self.destination, 'wb') as dst:
                    while True:
                        # Check for interruption
                        if self.isInterruptionRequested():
                            self.error.emit("Copy cancelled")
                            return
                        
                        chunk = src.read(self.chunk_size)
                        if not chunk:
                            break
                        
                        dst.write(chunk)
                        copied += len(chunk)
                        
                        if total_size > 0:
                            progress = int((copied / total_size) * 100)
                            self.progress.emit(progress)
            
            self.progress.emit(100)
            self.finished.emit(self.destination)
            logger.debug(f"Async copy completed: {self.source} -> {self.destination}")
            
        except Exception as e:
            error_msg = f"Error copying file: {e}"
            logger.error(error_msg)
            self.error.emit(error_msg)


# ==================== Convenience Functions ====================

# Global async file manager
_global_async_manager: AsyncFileManager | None = None


def get_async_file_manager() -> AsyncFileManager:
    """Get the global async file manager instance."""
    global _global_async_manager
    if _global_async_manager is None:
        _global_async_manager = AsyncFileManager()
    return _global_async_manager


def write_async(
    filepath: str,
    data: Any,
    on_complete: Callable[[str], None] | None = None,
    on_error: Callable[[str], None] | None = None,
    file_format: str = "auto"
) -> FileWriterThread:
    """
    Convenience function for async file write.
    
    Example:
        write_async("data.json", {"key": "value"}, 
                    on_complete=lambda p: print(f"Saved: {p}"))
    """
    return get_async_file_manager().write_file_async(
        filepath, data, on_complete, on_error, file_format=file_format
    )


def read_async(
    filepath: str,
    on_complete: Callable[[Any], None] | None = None,
    on_error: Callable[[str], None] | None = None,
    file_format: str = "auto"
) -> FileReaderThread:
    """
    Convenience function for async file read.
    
    Example:
        read_async("data.json", on_complete=lambda d: print(f"Loaded: {d}"))
    """
    return get_async_file_manager().read_file_async(
        filepath, on_complete, on_error, file_format=file_format
    )


# ==================== Module Exports ====================

__all__: list[str] = [
    'FileFormat',
    'FileWriterThread',
    'FileReaderThread',
    'FileCopyThread',
    'AsyncFileManager',
    'get_async_file_manager',
    'write_async',
    'read_async',
]