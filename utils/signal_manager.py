"""
RNV Icon Builder - Signal Manager Module
Tracks Qt signal connections to prevent memory leaks and simplify cleanup.

Features:
- Track all signal connections by widget
- Disconnect all signals for a widget on cleanup
- Statistics tracking for debugging
- SignalMixin for easy integration into classes

Usage Examples:
    # In a class that creates dynamic widgets:
    class MyDialog(QDialog, SignalMixin):
        def __init__(self):
            super().__init__()
            self.init_signal_manager()
            
            # Track connections
            self.track_connection(button, button.clicked, self.on_click)
            
        def closeEvent(self, event):
            self.disconnect_all_signals()
            super().closeEvent(event)

    # Standalone usage:
    manager = SignalConnectionManager()
    manager.connect(button, button.clicked, handler, "button_click")
    manager.disconnect_widget(button)
"""

from __future__ import annotations

from typing import Any, Callable
from dataclasses import dataclass
from collections import defaultdict

from PyQt6.QtCore import QObject, pyqtBoundSignal, QTimer

from utils.logger import Logger, get_logger_instance

# Setup logger
logger: Logger = get_logger_instance(__name__)


@dataclass
class ConnectionInfo:
    """Information about a signal connection."""
    widget: QObject
    signal: pyqtBoundSignal
    slot: Callable
    name: str
    connected: bool = True


class SignalConnectionManager:
    """
    Manages Qt signal connections to prevent memory leaks.
    
    Tracks all signal connections and provides methods to disconnect
    them individually or in bulk. Useful for dialogs and widgets that
    create many dynamic connections.
    
    Benefits:
    - Prevents memory leaks from orphaned signal connections
    - Easy bulk disconnection on widget cleanup
    - Statistics for debugging connection issues
    - Named connections for better tracking
    
    Example:
        manager = SignalConnectionManager()
        
        # Connect with tracking
        manager.connect(button, button.clicked, self.on_click, "save_button")
        manager.connect(slider, slider.valueChanged, self.on_value, "zoom_slider")
        
        # Disconnect all for a widget
        manager.disconnect_widget(button)
        
        # Disconnect all
        manager.disconnect_all()
        
        # View stats
        print(manager.get_stats())
    """
    
    def __init__(self) -> None:
        """Initialize the signal connection manager."""
        # Connections by widget (weak references to allow garbage collection)
        self._connections: dict[int, list[ConnectionInfo]] = defaultdict(list)
        
        # Statistics
        self._total_connected: int = 0
        self._total_disconnected: int = 0
    
    def connect(
        self,
        widget: QObject,
        signal: pyqtBoundSignal,
        slot: Callable,
        name: str = ""
    ) -> bool:
        """
        Connect a signal to a slot with tracking.
        
        Args:
            widget: Widget that owns the signal
            signal: The Qt signal to connect
            slot: The slot/function to call
            name: Optional name for debugging
            
        Returns:
            True if connection was successful
        
        Example:
            manager.connect(button, button.clicked, self.handle_click, "save_btn")
        """
        try:
            # Make the connection
            signal.connect(slot)
            
            # Track it
            widget_id = id(widget)
            info = ConnectionInfo(
                widget=widget,
                signal=signal,
                slot=slot,
                name=name or f"connection_{self._total_connected}",
                connected=True
            )
            self._connections[widget_id].append(info)
            self._total_connected += 1
            
            logger.debug(f"Connected signal: {info.name} on {widget.__class__.__name__}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting signal: {e}")
            return False
    
    def disconnect(
        self,
        widget: QObject,
        signal: pyqtBoundSignal,
        slot: Callable
    ) -> bool:
        """
        Disconnect a specific signal connection.
        
        Args:
            widget: Widget that owns the signal
            signal: The Qt signal
            slot: The connected slot
            
        Returns:
            True if disconnection was successful
        """
        try:
            signal.disconnect(slot)
            
            # Update tracking
            widget_id = id(widget)
            for info in self._connections.get(widget_id, []):
                if info.signal is signal and info.slot is slot and info.connected:
                    info.connected = False
                    self._total_disconnected += 1
                    logger.debug(f"Disconnected signal: {info.name}")
                    break
            
            return True
            
        except Exception as e:
            logger.debug(f"Error disconnecting signal (may already be disconnected): {e}")
            return False
    
    def disconnect_widget(self, widget: QObject) -> int:
        """
        Disconnect all signals for a specific widget.
        
        Args:
            widget: Widget to disconnect all signals from
            
        Returns:
            Number of connections disconnected
        
        Example:
            # When destroying a widget
            count = manager.disconnect_widget(my_button)
            print(f"Disconnected {count} signals")
        """
        widget_id = id(widget)
        connections = self._connections.get(widget_id, [])
        
        disconnected = 0
        for info in connections:
            if info.connected:
                try:
                    info.signal.disconnect(info.slot)
                    info.connected = False
                    disconnected += 1
                    self._total_disconnected += 1
                except Exception as e:
                    logger.debug(f"Signal already disconnected: {e}")
        
        if disconnected > 0:
            logger.debug(f"Disconnected {disconnected} signals from {widget.__class__.__name__}")
        
        return disconnected
    
    def disconnect_all(self) -> int:
        """
        Disconnect all tracked signals.
        
        Returns:
            Total number of connections disconnected
        
        Example:
            # On dialog close
            count = manager.disconnect_all()
        """
        total_disconnected = 0
        
        for widget_id, connections in self._connections.items():
            for info in connections:
                if info.connected:
                    try:
                        info.signal.disconnect(info.slot)
                        info.connected = False
                        total_disconnected += 1
                        self._total_disconnected += 1
                    except Exception as e:
                        logger.debug(f"Signal already disconnected: {e}")
        
        logger.debug(f"Disconnected all signals: {total_disconnected} total")
        return total_disconnected
    
    def disconnect_by_name(self, name: str) -> int:
        """
        Disconnect all signals with a specific name.
        
        Args:
            name: Connection name to disconnect
            
        Returns:
            Number of connections disconnected
        """
        disconnected = 0
        
        for connections in self._connections.values():
            for info in connections:
                if info.name == name and info.connected:
                    try:
                        info.signal.disconnect(info.slot)
                        info.connected = False
                        disconnected += 1
                        self._total_disconnected += 1
                    except Exception as e:
                        logger.debug(f"Signal disconnect skipped: {e}")
        
        return disconnected
    
    def get_active_count(self) -> int:
        """Get number of currently active connections."""
        count = 0
        for connections in self._connections.values():
            count += sum(1 for c in connections if c.connected)
        return count
    
    def get_widget_connection_count(self, widget: QObject) -> int:
        """Get number of active connections for a widget."""
        widget_id = id(widget)
        connections = self._connections.get(widget_id, [])
        return sum(1 for c in connections if c.connected)
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            Dictionary with:
            - active_connections: Currently connected
            - total_connected: Total connections made
            - total_disconnected: Total disconnections
            - widgets_tracked: Number of widgets with connections
        """
        active = self.get_active_count()
        widgets_with_connections = sum(
            1 for connections in self._connections.values()
            if any(c.connected for c in connections)
        )
        
        return {
            'active_connections': active,
            'total_connected': self._total_connected,
            'total_disconnected': self._total_disconnected,
            'widgets_tracked': widgets_with_connections
        }
    
    def print_stats(self) -> None:
        """Print connection statistics."""
        stats = self.get_stats()
        logger.info("=" * 50)
        logger.info("Signal Connection Manager Statistics:")
        logger.info("=" * 50)
        logger.info(f"  Active Connections:   {stats['active_connections']}")
        logger.info(f"  Total Connected:      {stats['total_connected']}")
        logger.info(f"  Total Disconnected:   {stats['total_disconnected']}")
        logger.info(f"  Widgets Tracked:      {stats['widgets_tracked']}")
        logger.info("=" * 50)
    
    def list_connections(self, widget: QObject | None = None) -> list[str]:
        """
        List all tracked connections (for debugging).
        
        Args:
            widget: Optional widget to filter by
            
        Returns:
            List of connection descriptions
        """
        result = []
        
        if widget is not None:
            widget_id = id(widget)
            connections = self._connections.get(widget_id, [])
            for info in connections:
                status = "connected" if info.connected else "disconnected"
                result.append(f"{info.name}: {status}")
        else:
            for widget_id, connections in self._connections.items():
                for info in connections:
                    status = "connected" if info.connected else "disconnected"
                    widget_name = info.widget.__class__.__name__
                    result.append(f"{widget_name}.{info.name}: {status}")
        
        return result
    
    def clear(self) -> None:
        """Clear all tracking data (does NOT disconnect signals)."""
        self._connections.clear()
        self._total_connected = 0
        self._total_disconnected = 0


class SignalMixin:
    """
    Mixin class that adds signal management to any QObject subclass.
    
    Provides convenient methods for tracking signal connections
    and automatic cleanup.
    
    Usage:
        class MyDialog(QDialog, SignalMixin):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.init_signal_manager()
                
                # Use track_connection instead of signal.connect
                self.track_connection(
                    self.button, 
                    self.button.clicked, 
                    self.on_click
                )
            
            def closeEvent(self, event):
                self.disconnect_all_signals()
                super().closeEvent(event)
    """
    
    _signal_manager: SignalConnectionManager | None = None
    
    def init_signal_manager(self) -> None:
        """Initialize the signal manager. Call this in __init__."""
        self._signal_manager = SignalConnectionManager()
    
    def track_connection(
        self,
        widget: QObject,
        signal: pyqtBoundSignal,
        slot: Callable,
        name: str = ""
    ) -> bool:
        """
        Connect and track a signal.
        
        Args:
            widget: Widget that owns the signal
            signal: Signal to connect
            slot: Slot to connect to
            name: Optional name for debugging
            
        Returns:
            True if connection was successful
        """
        if self._signal_manager is None:
            self.init_signal_manager()
        return self._signal_manager.connect(widget, signal, slot, name)
    
    def untrack_connection(
        self,
        widget: QObject,
        signal: pyqtBoundSignal,
        slot: Callable
    ) -> bool:
        """Disconnect and untrack a signal."""
        if self._signal_manager is None:
            return False
        return self._signal_manager.disconnect(widget, signal, slot)
    
    def disconnect_widget_signals(self, widget: QObject) -> int:
        """Disconnect all signals for a widget."""
        if self._signal_manager is None:
            return 0
        return self._signal_manager.disconnect_widget(widget)
    
    def disconnect_all_signals(self) -> int:
        """Disconnect all tracked signals."""
        if self._signal_manager is None:
            return 0
        return self._signal_manager.disconnect_all()
    
    def get_signal_stats(self) -> dict[str, Any]:
        """Get signal connection statistics."""
        if self._signal_manager is None:
            return {}
        return self._signal_manager.get_stats()


class WindowMoveMixin:
    """
    Mixin to ensure clean rendering after window drag on Windows.
    
    Tracks movement via a short timer and forces a repaint after the
    drag ends, preventing stale rendering artifacts.
    
    Note:
        Previous versions used setUpdatesEnabled(False) during drag to
        prevent compositor flicker, but this caused blank-screen bugs
        in reusable dialogs (show() triggers moveEvent on Windows, which
        disabled updates before child widgets could paint).
    
    Usage:
        class MyDialog(QDialog, SignalMixin, WindowMoveMixin):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.init_signal_manager()
                self.init_move_handler()
            
            def moveEvent(self, event):
                self._handle_move_event(event)
                super().moveEvent(event)
            
            def closeEvent(self, event):
                self.cleanup_move_handler()
                self.disconnect_all_signals()
                super().closeEvent(event)
    """
    
    _move_timer: QTimer | None = None
    _is_moving: bool = False
    
    def init_move_handler(self, interval: int = 50) -> None:
        """
        Initialize the move handler timer.
        
        Args:
            interval: Milliseconds to wait after movement stops before
                     re-enabling updates. Default 50ms works well.
        """
        self._move_timer = QTimer(self)
        self._move_timer.setSingleShot(True)
        self._move_timer.setInterval(interval)
        self._move_timer.timeout.connect(self._on_move_finished)
        self._is_moving = False
    
    def _handle_move_event(self, event) -> None:
        """
        Handle window move events to ensure clean rendering after drag.
        
        Call this from your moveEvent() override, then call super().moveEvent(event).
        
        Note:
            Previous implementation used setUpdatesEnabled(False) during moves
            to prevent compositor flicker, but this caused blank-screen bugs when
            reusable dialogs were closed mid-move or reopened at a moved position
            (show() triggers moveEvent on Windows, which disabled updates before
            child widgets could paint). Now uses repaint-after-move instead.
        """
        if self._move_timer is not None:
            self._is_moving = True
            self._move_timer.start()
    
    def _on_move_finished(self) -> None:
        """Force a clean repaint after movement stops."""
        self._is_moving = False
        self.repaint()
    
    def cleanup_move_handler(self) -> None:
        """
        Clean up move handler resources.
        
        Call this in closeEvent before calling super().closeEvent().
        """
        if self._move_timer is not None and self._move_timer.isActive():
            self._move_timer.stop()
        self._is_moving = False


# Global signal manager for application-wide tracking
_global_signal_manager: SignalConnectionManager | None = None


def get_global_signal_manager() -> SignalConnectionManager:
    """
    Get the global signal manager instance.
    
    Returns:
        Global SignalConnectionManager instance
    """
    global _global_signal_manager
    if _global_signal_manager is None:
        _global_signal_manager = SignalConnectionManager()
    return _global_signal_manager


def track_signal(
    widget: QObject,
    signal: pyqtBoundSignal,
    slot: Callable,
    name: str = ""
) -> bool:
    """
    Convenience function to track a signal with the global manager.
    
    Args:
        widget: Widget that owns the signal
        signal: Signal to connect
        slot: Slot to connect to
        name: Optional name for debugging
        
    Returns:
        True if connection was successful
    """
    return get_global_signal_manager().connect(widget, signal, slot, name)


def untrack_signal(
    widget: QObject,
    signal: pyqtBoundSignal,
    slot: Callable
) -> bool:
    """Convenience function to untrack a signal with the global manager."""
    return get_global_signal_manager().disconnect(widget, signal, slot)


# ==================== Module Exports ====================

__all__: list[str] = [
    'SignalConnectionManager',
    'SignalMixin',
    'WindowMoveMixin',
    'ConnectionInfo',
    'get_global_signal_manager',
    'track_signal',
    'untrack_signal',
]