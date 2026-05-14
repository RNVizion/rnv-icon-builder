"""
RNV Icon Builder - File Utilities Module
Generic file handling utilities for path validation, safe filename generation,
and common file operations.

Features:
- Path validation and extension handling
- Safe filename generation (removes invalid characters)
- Directory creation helpers
- File size utilities
- Backup file creation
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from utils.logger import Logger, get_logger_instance

# Setup logger
logger: Logger = get_logger_instance(__name__)


class FileUtils:
    """
    Utilities for file operations and path handling.
    
    All methods are static for convenience.
    
    Example:
        # Validate a path
        if FileUtils.validate_file_path(path, must_exist=True):
            process_file(path)
        
        # Ensure file has extension
        path = FileUtils.ensure_file_extension(path, ".ico")
        
        # Create safe filename
        safe_name = FileUtils.get_safe_filename("my:file*name.txt")
    """
    
    # Invalid characters for filenames (Windows)
    INVALID_FILENAME_CHARS: str = '<>:"/\\|?*'
    
    # Maximum filename length
    MAX_FILENAME_LENGTH: int = 255
    
    @staticmethod
    def ensure_file_extension(filepath: str, default_ext: str) -> str:
        """
        Ensure file has proper extension.
        
        If the file doesn't have an extension, appends the default extension.
        
        Args:
            filepath: Original file path
            default_ext: Default extension to add if missing (include the dot)
            
        Returns:
            File path with proper extension
        
        Example:
            >>> FileUtils.ensure_file_extension("icon", ".ico")
            'icon.ico'
            >>> FileUtils.ensure_file_extension("icon.ico", ".ico")
            'icon.ico'
        """
        if not filepath:
            return filepath
            
        if not os.path.splitext(filepath)[1]:
            return filepath + default_ext
        return filepath
    
    @staticmethod
    def validate_file_path(
        filepath: str, 
        must_exist: bool = False,
        check_writable: bool = False
    ) -> bool:
        """
        Validate a file path.
        
        Args:
            filepath: Path to validate
            must_exist: Whether file must already exist
            check_writable: Whether to check if location is writable
            
        Returns:
            True if path is valid
        
        Example:
            >>> FileUtils.validate_file_path("/path/to/file.ico", must_exist=True)
            False  # If file doesn't exist
        """
        if not filepath:
            return False
            
        try:
            path = Path(filepath)
            
            # Check if file exists (for load operations)
            if must_exist and not path.exists():
                return False
            
            # Check if directory exists (for save operations)
            directory = path.parent
            if directory and str(directory) != '.' and not directory.exists():
                return False
            
            # Check if writable
            if check_writable and directory.exists():
                return os.access(directory, os.W_OK)
                
            return True
            
        except Exception as e:
            logger.debug(f"Path validation failed for '{filepath}': {e}")
            return False
    
    @staticmethod
    def get_safe_filename(
        filename: str, 
        max_length: int | None = None,
        replacement: str = "_"
    ) -> str:
        """
        Create a safe filename by removing invalid characters.
        
        Args:
            filename: Original filename
            max_length: Maximum filename length (default: 255)
            replacement: Character to replace invalid chars with
            
        Returns:
            Safe filename
        
        Example:
            >>> FileUtils.get_safe_filename('my:file*name.ico')
            'my_file_name.ico'
        """
        if not filename:
            return "unnamed"
        
        max_length = max_length or FileUtils.MAX_FILENAME_LENGTH
        
        # Replace invalid characters
        safe_name = ''.join(
            replacement if c in FileUtils.INVALID_FILENAME_CHARS else c 
            for c in filename
        )
        
        # Remove leading/trailing spaces and dots
        safe_name = safe_name.strip('. ')
        
        # Limit length while preserving extension
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:max_length - len(ext)] + ext
        
        # Ensure we have something
        if not safe_name:
            safe_name = "unnamed"
            
        return safe_name
    
    @staticmethod
    def create_directory_if_not_exists(directory: str | Path) -> bool:
        """
        Create directory if it doesn't exist.
        
        Args:
            directory: Directory path to create
            
        Returns:
            True if directory exists or was created successfully
        
        Example:
            >>> FileUtils.create_directory_if_not_exists("/path/to/output")
            True
        """
        try:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")
            return False
    
    @staticmethod
    def get_file_size_bytes(filepath: str | Path) -> int:
        """
        Get file size in bytes.
        
        Args:
            filepath: Path to file
            
        Returns:
            File size in bytes or 0 if file doesn't exist
        
        Example:
            >>> FileUtils.get_file_size_bytes("icon.ico")
            45678
        """
        try:
            return os.path.getsize(filepath)
        except Exception as e:
            logger.debug(f"Could not get file size for '{filepath}': {e}")
            return 0
    
    @staticmethod
    def get_file_size_mb(filepath: str | Path) -> float | None:
        """
        Get file size in megabytes.
        
        Args:
            filepath: Path to file
            
        Returns:
            File size in MB or None if file doesn't exist
        
        Example:
            >>> FileUtils.get_file_size_mb("large_icon.ico")
            1.25
        """
        try:
            size_bytes = os.path.getsize(filepath)
            return size_bytes / (1024 * 1024)
        except Exception as e:
            logger.debug(f"Could not get file size for '{filepath}': {e}")
            return None
    
    @staticmethod
    def get_file_size_formatted(filepath: str | Path) -> str:
        """
        Get file size as formatted string (auto-selects unit).
        
        Args:
            filepath: Path to file
            
        Returns:
            Formatted size string like "1.5 MB" or "256 KB"
        
        Example:
            >>> FileUtils.get_file_size_formatted("icon.ico")
            '45.2 KB'
        """
        try:
            size_bytes = os.path.getsize(filepath)
            
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
                
        except Exception as e:
            logger.debug(f"Could not get file size for '{filepath}': {e}")
            return "Unknown"
    
    @staticmethod
    def backup_file(
        filepath: str | Path, 
        backup_suffix: str = ".bak",
        max_backups: int = 5
    ) -> str | None:
        """
        Create a backup copy of a file.
        
        If multiple backups are allowed, uses numbered suffixes (.bak1, .bak2, etc.)
        
        Args:
            filepath: Original file path
            backup_suffix: Suffix to add to backup filename
            max_backups: Maximum number of backup files to keep
            
        Returns:
            Backup file path or None if failed
        
        Example:
            >>> FileUtils.backup_file("icon.ico")
            'icon.ico.bak'
        """
        try:
            path = Path(filepath)
            
            if not path.exists():
                return None
            
            # Simple backup (single file)
            if max_backups == 1:
                backup_path = Path(str(filepath) + backup_suffix)
                shutil.copy2(filepath, backup_path)
                return str(backup_path)
            
            # Multiple backups with rotation
            # Find next available backup number
            for i in range(1, max_backups + 1):
                backup_path = Path(f"{filepath}{backup_suffix}{i}")
                if not backup_path.exists():
                    shutil.copy2(filepath, backup_path)
                    return str(backup_path)
            
            # All slots full - rotate (delete oldest, shift others)
            oldest = Path(f"{filepath}{backup_suffix}1")
            if oldest.exists():
                oldest.unlink()
            
            # Shift existing backups
            for i in range(2, max_backups + 1):
                current = Path(f"{filepath}{backup_suffix}{i}")
                previous = Path(f"{filepath}{backup_suffix}{i-1}")
                if current.exists():
                    current.rename(previous)
            
            # Create new backup at highest number
            backup_path = Path(f"{filepath}{backup_suffix}{max_backups}")
            shutil.copy2(filepath, backup_path)
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Error creating backup of {filepath}: {e}")
            return None
    
    @staticmethod
    def get_unique_filename(
        directory: str | Path,
        base_name: str,
        extension: str
    ) -> str:
        """
        Generate a unique filename in a directory.
        
        If the filename exists, appends a number (file_1.ext, file_2.ext, etc.)
        
        Args:
            directory: Target directory
            base_name: Base filename without extension
            extension: File extension (include the dot)
            
        Returns:
            Unique filename (not full path)
        
        Example:
            >>> FileUtils.get_unique_filename("/output", "icon", ".ico")
            'icon_2.ico'  # If icon.ico and icon_1.ico exist
        """
        directory = Path(directory)
        
        # Try original name first
        filename = f"{base_name}{extension}"
        if not (directory / filename).exists():
            return filename
        
        # Add number suffix
        counter = 1
        while True:
            filename = f"{base_name}_{counter}{extension}"
            if not (directory / filename).exists():
                return filename
            counter += 1
            
            # Safety limit
            if counter > 9999:
                raise ValueError("Too many files with same base name")
    
    @staticmethod
    def get_file_extension(filepath: str | Path) -> str:
        """
        Get file extension (lowercase, with dot).
        
        Args:
            filepath: File path
            
        Returns:
            Lowercase extension with dot, or empty string
        
        Example:
            >>> FileUtils.get_file_extension("Icon.PNG")
            '.png'
        """
        return os.path.splitext(str(filepath))[1].lower()
    
    @staticmethod
    def is_valid_image_file(filepath: str | Path) -> bool:
        """
        Check if file has a valid image extension.
        
        Args:
            filepath: File path to check
            
        Returns:
            True if file has valid image extension
        """
        valid_extensions = {'.png', '.jpg', '.jpeg', '.ico', '.svg', '.bmp', '.gif', '.webp'}
        return FileUtils.get_file_extension(filepath) in valid_extensions
    
    @staticmethod
    def copy_file(source: str | Path, destination: str | Path) -> bool:
        """
        Copy a file to a new location.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if successful
        """
        try:
            shutil.copy2(source, destination)
            return True
        except Exception as e:
            logger.error(f"Error copying {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def move_file(source: str | Path, destination: str | Path) -> bool:
        """
        Move a file to a new location.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if successful
        """
        try:
            shutil.move(str(source), str(destination))
            return True
        except Exception as e:
            logger.error(f"Error moving {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def delete_file(filepath: str | Path) -> bool:
        """
        Delete a file.
        
        Args:
            filepath: File path to delete
            
        Returns:
            True if successful or file doesn't exist
        """
        try:
            path = Path(filepath)
            if path.exists():
                path.unlink()
            return True
        except Exception as e:
            logger.error(f"Error deleting {filepath}: {e}")
            return False
    
    @staticmethod
    def list_files(
        directory: str | Path,
        pattern: str = "*",
        recursive: bool = False
    ) -> list[Path]:
        """
        List files in a directory matching a pattern.
        
        Args:
            directory: Directory to search
            pattern: Glob pattern (e.g., "*.png", "icon_*")
            recursive: Whether to search subdirectories
            
        Returns:
            List of matching file paths
        """
        try:
            directory = Path(directory)
            
            if recursive:
                return list(directory.rglob(pattern))
            else:
                return list(directory.glob(pattern))
                
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {e}")
            return []


# ==================== Convenience Functions ====================

def ensure_extension(filepath: str, ext: str) -> str:
    """Shorthand for FileUtils.ensure_file_extension()"""
    return FileUtils.ensure_file_extension(filepath, ext)


def safe_filename(name: str) -> str:
    """Shorthand for FileUtils.get_safe_filename()"""
    return FileUtils.get_safe_filename(name)


def file_exists(filepath: str) -> bool:
    """Check if file exists."""
    return FileUtils.validate_file_path(filepath, must_exist=True)


def mkdir(directory: str | Path) -> bool:
    """Shorthand for FileUtils.create_directory_if_not_exists()"""
    return FileUtils.create_directory_if_not_exists(directory)


# ==================== Module Exports ====================

__all__: list[str] = [
    'FileUtils',
    'ensure_extension',
    'safe_filename',
    'file_exists',
    'mkdir',
]