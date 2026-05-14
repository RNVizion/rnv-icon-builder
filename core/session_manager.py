"""
RNV Icon Builder - Session Manager Module
Handles automatic session backup and crash recovery.

Features:
- Timer-based auto-save (configurable interval)
- Session state persistence
- Crash recovery detection
- Recovery dialog on startup
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Any, TYPE_CHECKING
from dataclasses import dataclass, field, asdict

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from utils.config import USER_DATA_DIR
from utils.logger import Logger, get_logger_instance
from utils.async_file_ops import write_async

if TYPE_CHECKING:
    from PIL import Image

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)

# Session file paths
SESSION_DIR: Path = USER_DATA_DIR / "sessions"
SESSION_AUTO_SAVE_PATH: Path = SESSION_DIR / "autosave.json"
RECOVERY_FLAG_PATH: Path = SESSION_DIR / ".recovery_needed"

# Default auto-save interval (5 minutes in milliseconds)
DEFAULT_AUTO_SAVE_INTERVAL: int = 5 * 60 * 1000  # 5 minutes


@dataclass
class SessionState:
    """
    Represents the state of an application session.
    
    Attributes:
        timestamp: When the session was saved
        loaded_files: List of file paths that were loaded
        selected_sizes: List of selected size values
        autofill_enabled: Whether autofill was enabled
        png_compression: Whether PNG compression was enabled
        current_project_path: Path to current project (if any)
        window_geometry: Window position and size
        settings: Additional settings dict
    """
    timestamp: str = ""
    loaded_files: list[str] = field(default_factory=list)
    selected_sizes: list[int] = field(default_factory=list)
    autofill_enabled: bool = True
    png_compression: bool = True
    current_project_path: str = ""
    window_geometry: dict[str, int] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionState:
        """Create SessionState from dictionary."""
        return cls(
            timestamp=data.get('timestamp', ''),
            loaded_files=data.get('loaded_files', []),
            selected_sizes=data.get('selected_sizes', []),
            autofill_enabled=data.get('autofill_enabled', True),
            png_compression=data.get('png_compression', True),
            current_project_path=data.get('current_project_path', ''),
            window_geometry=data.get('window_geometry', {}),
            settings=data.get('settings', {})
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @property
    def is_valid(self) -> bool:
        """Check if session has any meaningful state to restore."""
        return bool(self.loaded_files or self.current_project_path)
    
    @property
    def age_seconds(self) -> float:
        """Get age of session in seconds."""
        if not self.timestamp:
            return float('inf')
        try:
            saved_time = datetime.fromisoformat(self.timestamp)
            return (datetime.now() - saved_time).total_seconds()
        except ValueError:
            return float('inf')
    
    @property
    def formatted_time(self) -> str:
        """Get human-readable timestamp."""
        if not self.timestamp:
            return "Unknown"
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return self.timestamp


class SessionManager(QObject):
    """
    Manages application session auto-save and recovery.
    
    Provides automatic periodic saving of session state and
    detection/recovery from unexpected closures.
    
    Signals:
        session_saved: Emitted when session is auto-saved
        recovery_available: Emitted when recoverable session found
        
    Example:
        >>> manager = SessionManager()
        >>> manager.start_auto_save(interval_ms=300000)  # 5 minutes
        >>> manager.save_session(state)
        >>> if manager.has_recovery():
        ...     state = manager.get_recovery_state()
    """
    
    session_saved = pyqtSignal()
    recovery_available = pyqtSignal(object)  # SessionState
    
    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the session manager."""
        super().__init__(parent)
        
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._on_auto_save_timer)
        
        self._current_state: SessionState | None = None
        self._state_getter: callable | None = None
        self._is_auto_save_enabled: bool = False
        
        # Ensure session directory exists
        self._ensure_directory()
        
        logger.debug("Session manager initialized")
    
    def _ensure_directory(self) -> None:
        """Ensure the session directory exists."""
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
    
    def set_state_getter(self, getter: callable) -> None:
        """
        Set a callback function that returns current session state.
        
        Args:
            getter: Callable that returns SessionState
        """
        self._state_getter = getter
    
    def start_auto_save(self, interval_ms: int = DEFAULT_AUTO_SAVE_INTERVAL) -> None:
        """
        Start automatic session saving.
        
        Args:
            interval_ms: Save interval in milliseconds (default 5 minutes)
        """
        self._is_auto_save_enabled = True
        self._auto_save_timer.start(interval_ms)
        
        # Create recovery flag to detect crashes
        self._set_recovery_flag()
        
        interval_min = interval_ms / 60000
        logger.success(f"Auto-save started (every {interval_min:.1f} minutes)")
    
    def stop_auto_save(self) -> None:
        """Stop automatic session saving."""
        self._is_auto_save_enabled = False
        self._auto_save_timer.stop()
        
        # Clear recovery flag on clean shutdown
        self._clear_recovery_flag()
        
        logger.debug("Auto-save stopped")
    
    def _on_auto_save_timer(self) -> None:
        """Handle auto-save timer tick."""
        if self._state_getter:
            try:
                state = self._state_getter()
                if state and state.is_valid:
                    self.save_session(state)
            except Exception as e:
                logger.warning(f"Auto-save failed: {e}")
    
    def save_session(self, state: SessionState, async_write: bool = True) -> bool:
        """
        Save session state to disk.
        
        Args:
            state: Session state to save
            async_write: If True, write asynchronously (non-blocking)
            
        Returns:
            True if save initiated successfully
        """
        self._ensure_directory()
        
        try:
            state.timestamp = datetime.now().isoformat()
            data = state.to_dict()
            
            if async_write:
                # Non-blocking write for auto-save
                write_async(
                    str(SESSION_AUTO_SAVE_PATH),
                    data,
                    on_complete=lambda p: self._on_save_complete(state),
                    on_error=lambda e: logger.warning(f"Async save failed: {e}")
                )
                return True
            else:
                # Synchronous write for manual save
                with open(SESSION_AUTO_SAVE_PATH, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                self._on_save_complete(state)
                return True
            
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")
            return False
    
    def _on_save_complete(self, state: SessionState) -> None:
        """Handle successful session save."""
        self._current_state = state
        self.session_saved.emit()
        logger.debug(f"Session saved: {len(state.loaded_files)} files")
    
    def load_session(self) -> SessionState | None:
        """
        Load session state from disk.
        
        Returns:
            SessionState if found, None otherwise
        """
        if not SESSION_AUTO_SAVE_PATH.exists():
            return None
        
        try:
            with open(SESSION_AUTO_SAVE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state = SessionState.from_dict(data)
            logger.debug(f"Session loaded: {len(state.loaded_files)} files")
            return state
            
        except Exception as e:
            logger.warning(f"Failed to load session: {e}")
            return None
    
    def _set_recovery_flag(self) -> None:
        """Set flag indicating app is running (for crash detection)."""
        try:
            with open(RECOVERY_FLAG_PATH, 'w') as f:
                f.write(str(time.time()))
        except Exception as e:
            logger.debug(f"Could not set recovery flag: {e}")
    
    def _clear_recovery_flag(self) -> None:
        """Clear recovery flag on clean shutdown."""
        try:
            if RECOVERY_FLAG_PATH.exists():
                RECOVERY_FLAG_PATH.unlink()
        except Exception as e:
            logger.debug(f"Could not clear recovery flag: {e}")
    
    def has_recovery(self) -> bool:
        """
        Check if there's a session to recover from crash.
        
        Returns:
            True if recovery is available and needed
        """
        # Check if recovery flag exists (indicates crash)
        if not RECOVERY_FLAG_PATH.exists():
            return False
        
        # Check if we have a saved session
        if not SESSION_AUTO_SAVE_PATH.exists():
            self._clear_recovery_flag()
            return False
        
        # Load and validate session
        state = self.load_session()
        if not state or not state.is_valid:
            self._clear_recovery_flag()
            return False
        
        # Check session age (don't recover sessions older than 24 hours)
        if state.age_seconds > 24 * 60 * 60:
            logger.debug("Recovery session too old, ignoring")
            self._clear_recovery_flag()
            return False
        
        return True
    
    def get_recovery_state(self) -> SessionState | None:
        """
        Get the session state for recovery.
        
        Returns:
            SessionState if available, None otherwise
        """
        if not self.has_recovery():
            return None
        
        return self.load_session()
    
    def clear_recovery(self) -> None:
        """Clear recovery data after successful recovery or decline."""
        self._clear_recovery_flag()
        
        # Optionally clear the saved session too
        try:
            if SESSION_AUTO_SAVE_PATH.exists():
                SESSION_AUTO_SAVE_PATH.unlink()
        except Exception as e:
            logger.debug(f"Could not clear saved session: {e}")
    
    def on_clean_shutdown(self) -> None:
        """Called when application shuts down cleanly."""
        self.stop_auto_save()
        self._clear_recovery_flag()
        logger.debug("Clean shutdown recorded")
    
    @property
    def is_auto_save_enabled(self) -> bool:
        """Check if auto-save is currently enabled."""
        return self._is_auto_save_enabled
    
    @property
    def last_save_time(self) -> str:
        """Get formatted time of last save."""
        if self._current_state:
            return self._current_state.formatted_time
        return "Never"


# Module exports
__all__: list[str] = [
    'SessionManager',
    'SessionState',
    'SESSION_DIR',
    'SESSION_AUTO_SAVE_PATH',
    'DEFAULT_AUTO_SAVE_INTERVAL',
]