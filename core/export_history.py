"""
RNV Icon Builder - Export History Module
Tracks and persists export history for user reference.

Features:
- Log all ICO/PNG exports with metadata
- Persistent JSON storage
- Query recent exports
- Clear history option
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any
from dataclasses import dataclass, field, asdict

from utils.config import USER_DATA_DIR
from utils.logger import Logger, get_logger_instance

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)

# Export history file path
EXPORT_HISTORY_PATH: Path = USER_DATA_DIR / "export_history.json"

# Maximum number of history entries to keep
MAX_HISTORY_ENTRIES: int = 100


@dataclass
class ExportEntry:
    """
    Represents a single export operation.
    
    Attributes:
        timestamp: ISO format timestamp of export
        output_path: Path where file was exported
        export_type: Type of export ('ico', 'png_set', 'icns', 'favicon', 'android', 'ios')
        sizes: List of sizes included in export
        source_count: Number of source images used
        file_size: Size of output file in bytes (if applicable)
        compression_ratio: Compression ratio achieved (if applicable)
        success: Whether export succeeded
        error_message: Error message if failed
    """
    timestamp: str
    output_path: str
    export_type: str
    sizes: list[int] = field(default_factory=list)
    source_count: int = 0
    file_size: int = 0
    compression_ratio: float = 0.0
    success: bool = True
    error_message: str = ""
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExportEntry:
        """Create ExportEntry from dictionary."""
        return cls(
            timestamp=data.get('timestamp', ''),
            output_path=data.get('output_path', ''),
            export_type=data.get('export_type', 'ico'),
            sizes=data.get('sizes', []),
            source_count=data.get('source_count', 0),
            file_size=data.get('file_size', 0),
            compression_ratio=data.get('compression_ratio', 0.0),
            success=data.get('success', True),
            error_message=data.get('error_message', '')
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @property
    def datetime(self) -> datetime:
        """Get timestamp as datetime object."""
        try:
            return datetime.fromisoformat(self.timestamp)
        except ValueError:
            return datetime.now()
    
    @property
    def formatted_time(self) -> str:
        """Get human-readable timestamp."""
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return self.timestamp
    
    @property
    def formatted_size(self) -> str:
        """Get human-readable file size."""
        if self.file_size == 0:
            return "N/A"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    @property
    def filename(self) -> str:
        """Get just the filename from the output path."""
        return Path(self.output_path).name


class ExportHistory:
    """
    Manages export history persistence and queries.
    
    Stores export history in a JSON file and provides methods
    to add, query, and clear history entries.
    
    Example:
        >>> history = ExportHistory()
        >>> history.log_export('/path/to/icon.ico', 'ico', [256, 128, 64], True)
        >>> recent = history.get_history(limit=10)
    """
    
    def __init__(self) -> None:
        """Initialize export history manager."""
        self._entries: list[ExportEntry] = []
        self._load_history()
        logger.debug(f"Export history initialized with {len(self._entries)} entries")
    
    def _ensure_directory(self) -> None:
        """Ensure the user data directory exists."""
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_history(self) -> None:
        """Load history from disk."""
        self._entries = []
        
        if not EXPORT_HISTORY_PATH.exists():
            logger.debug("No export history file found")
            return
        
        try:
            with open(EXPORT_HISTORY_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for entry_data in data:
                    try:
                        entry = ExportEntry.from_dict(entry_data)
                        self._entries.append(entry)
                    except Exception as e:
                        logger.warning(f"Skipping invalid history entry: {e}")
            
            logger.success(f"Loaded {len(self._entries)} export history entries")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Export history file corrupted: {e}")
        except Exception as e:
            logger.warning(f"Failed to load export history: {e}")
    
    def _save_history(self) -> None:
        """Save history to disk."""
        self._ensure_directory()
        
        try:
            # Trim to max entries before saving
            if len(self._entries) > MAX_HISTORY_ENTRIES:
                self._entries = self._entries[-MAX_HISTORY_ENTRIES:]
            
            data = [entry.to_dict() for entry in self._entries]
            
            with open(EXPORT_HISTORY_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self._entries)} export history entries")
            
        except Exception as e:
            logger.warning(f"Failed to save export history: {e}")
    
    def log_export(
        self,
        output_path: str,
        export_type: str,
        sizes: list[int],
        success: bool,
        source_count: int = 0,
        file_size: int = 0,
        compression_ratio: float = 0.0,
        error_message: str = ""
    ) -> ExportEntry:
        """
        Log an export operation.
        
        Args:
            output_path: Path where file was exported
            export_type: Type of export ('ico', 'png_set', 'icns', etc.)
            sizes: List of sizes included
            success: Whether export succeeded
            source_count: Number of source images
            file_size: Output file size in bytes
            compression_ratio: Compression ratio achieved
            error_message: Error message if failed
            
        Returns:
            The created ExportEntry
        """
        entry = ExportEntry(
            timestamp=datetime.now().isoformat(),
            output_path=output_path,
            export_type=export_type,
            sizes=sizes,
            source_count=source_count,
            file_size=file_size,
            compression_ratio=compression_ratio,
            success=success,
            error_message=error_message
        )
        
        self._entries.append(entry)
        self._save_history()
        
        status = "successful" if success else "failed"
        logger.info(f"Logged {status} {export_type} export: {output_path}")
        
        return entry
    
    def get_history(self, limit: int = 50) -> list[ExportEntry]:
        """
        Get recent export history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of ExportEntry objects, newest first
        """
        # Return in reverse order (newest first)
        return list(reversed(self._entries[-limit:]))
    
    def get_successful_exports(self, limit: int = 50) -> list[ExportEntry]:
        """Get only successful exports."""
        successful = [e for e in self._entries if e.success]
        return list(reversed(successful[-limit:]))
    
    def get_failed_exports(self, limit: int = 50) -> list[ExportEntry]:
        """Get only failed exports."""
        failed = [e for e in self._entries if not e.success]
        return list(reversed(failed[-limit:]))
    
    def get_exports_by_type(self, export_type: str, limit: int = 50) -> list[ExportEntry]:
        """Get exports of a specific type."""
        filtered = [e for e in self._entries if e.export_type == export_type]
        return list(reversed(filtered[-limit:]))
    
    def clear_history(self) -> None:
        """Clear all export history."""
        self._entries = []
        self._save_history()
        logger.success("Export history cleared")
    
    def get_statistics(self) -> dict[str, Any]:
        """
        Get overall export statistics.
        
        Returns:
            Dictionary with stats like total exports, success rate, etc.
        """
        total = len(self._entries)
        successful = sum(1 for e in self._entries if e.success)
        failed = total - successful
        
        # Count by type
        by_type: dict[str, int] = {}
        for entry in self._entries:
            by_type[entry.export_type] = by_type.get(entry.export_type, 0) + 1
        
        # Total bytes exported
        total_bytes = sum(e.file_size for e in self._entries if e.success)
        
        return {
            'total_exports': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'by_type': by_type,
            'total_bytes_exported': total_bytes
        }
    
    @property
    def count(self) -> int:
        """Get total number of history entries."""
        return len(self._entries)
    
    @property
    def is_empty(self) -> bool:
        """Check if history is empty."""
        return len(self._entries) == 0


# Module exports
__all__: list[str] = [
    'ExportEntry',
    'ExportHistory',
    'EXPORT_HISTORY_PATH',
    'MAX_HISTORY_ENTRIES',
]
