"""
RNV Icon Builder - Recent Files Manager
Tracks recently opened files/folders for quick access.

Features:
- Track recently opened image files
- Track recently scanned folders
- Persist history to disk
- Auto-cleanup of non-existent entries
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any

from utils.config import RECENT_FILES_PATH, MAX_RECENT_FILES
from utils.logger import Logger, get_logger_instance

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)


class RecentFilesManager:
    """
    Manages recently opened files and folders.
    
    Tracks file and folder history, persists to disk, and provides
    methods for accessing and managing the history.
    
    Attributes:
        recent_files: List of recently opened files
        recent_folders: List of recently scanned folders
        
    Example:
        >>> manager = RecentFilesManager()
        >>> manager.add_file("/path/to/icon.png")
        >>> recent = manager.get_recent_files()
        >>> for item in recent:
        ...     print(item['name'])
    """
    
    def __init__(self) -> None:
        """Initialize the recent files manager and load history from disk."""
        self.recent_files: list[dict[str, Any]] = []
        self.recent_folders: list[dict[str, Any]] = []
        self._load()
        logger.debug("RecentFilesManager initialized")
    
    def _load(self) -> None:
        """Load recent files history from disk."""
        if RECENT_FILES_PATH.exists():
            try:
                with open(RECENT_FILES_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.recent_files = data.get('files', [])
                    self.recent_folders = data.get('folders', [])
                logger.debug(f"Loaded {len(self.recent_files)} recent files, {len(self.recent_folders)} recent folders")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid recent files JSON, resetting: {e}")
                self.recent_files = []
                self.recent_folders = []
            except Exception as e:
                logger.warning(f"Failed to load recent files: {e}")
                self.recent_files = []
                self.recent_folders = []
        else:
            logger.debug("No recent files history found")
    
    def _save(self) -> None:
        """Save recent files history to disk."""
        try:
            # Ensure parent directory exists
            RECENT_FILES_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'files': self.recent_files[:MAX_RECENT_FILES],
                'folders': self.recent_folders[:MAX_RECENT_FILES],
                'version': '2.6',
                'last_updated': datetime.now().isoformat()
            }
            
            with open(RECENT_FILES_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Recent files history saved")
        except Exception as e:
            logger.warning(f"Failed to save recent files: {e}")
    
    def add_file(self, file_path: str) -> None:
        """
        Add a file to the recent files list.
        
        If the file already exists in the list, it's moved to the front.
        
        Args:
            file_path: Path to the file to add
            
        Example:
            >>> manager.add_file("/path/to/icon_256.png")
        """
        # Normalize path
        file_path = str(Path(file_path).resolve())
        
        # Remove if already exists (will be re-added at front)
        self.recent_files = [f for f in self.recent_files if f.get('path') != file_path]
        
        # Add to front of list
        self.recent_files.insert(0, {
            'path': file_path,
            'name': Path(file_path).name,
            'timestamp': datetime.now().isoformat()
        })
        
        # Trim to maximum
        self.recent_files = self.recent_files[:MAX_RECENT_FILES]
        
        # Persist to disk
        self._save()
        
        logger.debug(f"Added to recent files: {Path(file_path).name}")
    
    def add_folder(self, folder_path: str) -> None:
        """
        Add a folder to the recent folders list.
        
        If the folder already exists in the list, it's moved to the front.
        
        Args:
            folder_path: Path to the folder to add
            
        Example:
            >>> manager.add_folder("/path/to/icons/")
        """
        # Normalize path
        folder_path = str(Path(folder_path).resolve())
        
        # Remove if already exists
        self.recent_folders = [f for f in self.recent_folders if f.get('path') != folder_path]
        
        # Add to front of list
        self.recent_folders.insert(0, {
            'path': folder_path,
            'name': Path(folder_path).name,
            'timestamp': datetime.now().isoformat()
        })
        
        # Trim to maximum
        self.recent_folders = self.recent_folders[:MAX_RECENT_FILES]
        
        # Persist to disk
        self._save()
        
        logger.debug(f"Added to recent folders: {Path(folder_path).name}")
    
    def get_recent_files(self) -> list[dict[str, Any]]:
        """
        Get list of recent files that still exist.
        
        Filters out files that no longer exist on disk.
        
        Returns:
            List of file info dictionaries with 'path', 'name', 'timestamp'
            
        Example:
            >>> recent = manager.get_recent_files()
            >>> for item in recent:
            ...     print(f"{item['name']} - {item['path']}")
        """
        # Filter to only existing files
        existing = [f for f in self.recent_files if Path(f.get('path', '')).exists()]
        
        # If we filtered any, update the stored list
        if len(existing) != len(self.recent_files):
            self.recent_files = existing
            self._save()
            logger.debug(f"Cleaned up non-existent files, {len(existing)} remaining")
        
        return existing
    
    def get_recent_folders(self) -> list[dict[str, Any]]:
        """
        Get list of recent folders that still exist.
        
        Filters out folders that no longer exist on disk.
        
        Returns:
            List of folder info dictionaries with 'path', 'name', 'timestamp'
            
        Example:
            >>> recent = manager.get_recent_folders()
            >>> for item in recent:
            ...     print(f"{item['name']} - {item['path']}")
        """
        # Filter to only existing folders
        existing = [f for f in self.recent_folders if Path(f.get('path', '')).exists()]
        
        # If we filtered any, update the stored list
        if len(existing) != len(self.recent_folders):
            self.recent_folders = existing
            self._save()
            logger.debug(f"Cleaned up non-existent folders, {len(existing)} remaining")
        
        return existing
    
    def get_all_recent(self) -> list[dict[str, Any]]:
        """
        Get combined list of recent files and folders, sorted by timestamp.
        
        Returns:
            Combined list sorted by most recent first
        """
        files = self.get_recent_files()
        folders = self.get_recent_folders()
        
        # Mark each with type
        for f in files:
            f['type'] = 'file'
        for f in folders:
            f['type'] = 'folder'
        
        # Combine and sort by timestamp (newest first)
        combined = files + folders
        combined.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return combined
    
    def clear_history(self) -> None:
        """
        Clear all recent files and folders history.
        
        Example:
            >>> manager.clear_history()
        """
        self.recent_files = []
        self.recent_folders = []
        self._save()
        logger.success("Recent files history cleared")
    
    def clear_files(self) -> None:
        """Clear only the recent files list (not folders)."""
        self.recent_files = []
        self._save()
        logger.info("Recent files list cleared")
    
    def clear_folders(self) -> None:
        """Clear only the recent folders list (not files)."""
        self.recent_folders = []
        self._save()
        logger.info("Recent folders list cleared")
    
    def remove_file(self, file_path: str) -> bool:
        """
        Remove a specific file from the recent files list.
        
        Args:
            file_path: Path to remove
            
        Returns:
            True if file was found and removed
        """
        file_path = str(Path(file_path).resolve())
        original_count = len(self.recent_files)
        self.recent_files = [f for f in self.recent_files if f.get('path') != file_path]
        
        if len(self.recent_files) < original_count:
            self._save()
            logger.debug(f"Removed from recent files: {file_path}")
            return True
        return False
    
    def remove_folder(self, folder_path: str) -> bool:
        """
        Remove a specific folder from the recent folders list.
        
        Args:
            folder_path: Path to remove
            
        Returns:
            True if folder was found and removed
        """
        folder_path = str(Path(folder_path).resolve())
        original_count = len(self.recent_folders)
        self.recent_folders = [f for f in self.recent_folders if f.get('path') != folder_path]
        
        if len(self.recent_folders) < original_count:
            self._save()
            logger.debug(f"Removed from recent folders: {folder_path}")
            return True
        return False
    
    def get_file_count(self) -> int:
        """Get the number of recent files tracked."""
        return len(self.recent_files)
    
    def get_folder_count(self) -> int:
        """Get the number of recent folders tracked."""
        return len(self.recent_folders)
    
    def has_history(self) -> bool:
        """Check if there is any history (files or folders)."""
        return bool(self.recent_files or self.recent_folders)


# ==================== Module Exports ====================

__all__: list[str] = [
    'RecentFilesManager',
]
