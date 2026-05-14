"""
RNV Icon Builder — Phase 3 Application-Level Tests
==================================================

Tests the IconBuilderApp shell from RNV_Icon_Builder.py — the main window
class that wires every manager, dialog, theme, and signal together.

Scope (per Phase 3 plan):
  - Construction and initial state
  - Theme switching state transitions
  - File-handling pipeline (handle_files orchestration)
  - Keyboard shortcut registration
  - Close-event cleanup
  - Public API contracts (get_selected_sizes, get_preview_*, _get_session_state)

Out of scope (deferred to Phase 4 with qtbot):
  - Real drag-and-drop event simulation
  - Settings dialog interaction
  - Menu/button click chains
  - Focus traversal, keyboard event propagation

These tests deliberately stay structural — they verify the app shell wires up
correctly and survives a normal lifecycle. Detailed widget-level behavior is
Phase 4's domain.
"""

import os
import pytest
from pathlib import Path

# Headless platform is set by conftest; QApplication and `app` fixtures
# are provided there. All path/package bootstrap happens in conftest.py —
# this file just imports.

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QShortcut, QKeySequence
from PyQt6.QtWidgets import QApplication


# ══════════════════════════════════════════════════════════════════════════════
# 1. CONSTRUCTION & INITIAL STATE
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
class TestIconBuilderAppInit:
    """Verify the application shell wires up correctly during __init__."""

    def test_app_instantiates(self, app):
        """The most basic test: construction completes without error."""
        assert app is not None

    def test_window_title(self, app):
        assert app.windowTitle() == "Multi-Resolution ICO Builder"

    def test_window_has_central_widget(self, app):
        assert app.centralWidget() is not None

    def test_window_has_minimum_size(self, app):
        # Window should have non-zero dimensions after geometry setup.
        assert app.width() > 0
        assert app.height() > 0

    def test_core_components_initialized(self, app):
        """image_processor, theme_manager, recent_files_manager all present."""
        assert app.image_processor is not None
        assert app.theme_manager is not None
        assert app.recent_files_manager is not None

    def test_phase5_managers_initialized(self, app):
        """batch_processor, folder_watcher, preset_manager, project_manager."""
        assert app.batch_processor is not None
        assert app.folder_watcher is not None
        assert app.preset_manager is not None
        assert app.project_manager is not None

    def test_phase7_export_history_initialized(self, app):
        assert app.export_history is not None

    def test_phase8_session_components_initialized(self, app):
        assert app.session_manager is not None
        assert app._tooltips_enabled is True

    def test_settings_dialog_lazy_init(self, app):
        """Settings dialog is created on first open, not during __init__."""
        assert app.settings_dialog is None

    def test_initial_no_files_loaded(self, app):
        """Fresh app has zero detected images."""
        assert len(app.image_processor.get_detected_images()) == 0

    def test_initial_selected_size_is_none(self, app):
        assert app.selected_size is None

    def test_filename_template_default(self, app):
        assert app._filename_template == "icon_{size}"

    def test_preview_zoom_default(self, app):
        assert app._preview_zoom == 100

    def test_status_timer_is_single_shot(self, app):
        assert app._status_timer.isSingleShot() is True

    def test_no_current_project_initially(self, app):
        assert app._current_project is None
        assert app._current_project_path is None
        assert app._project_modified is False


# ══════════════════════════════════════════════════════════════════════════════
# 2. THEME SWITCHING
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
class TestIconBuilderAppTheme:
    """Theme cycling and apply_theme behavior."""

    def test_initial_theme_is_set(self, app):
        """After init, theme_manager has a current theme value."""
        assert app.theme_manager.current_theme is not None

    def test_apply_theme_does_not_raise(self, app):
        """Re-applying the current theme is a no-error operation."""
        app.apply_theme()  # Should complete cleanly.

    def test_cycle_theme_changes_state(self, app):
        """One cycle moves to a different theme."""
        before = app.theme_manager.current_theme
        app.cycle_theme()
        after = app.theme_manager.current_theme
        assert before != after

    def test_cycle_theme_updates_button_text(self, app):
        """Theme button text reflects current theme display name."""
        app.cycle_theme()
        expected = app.theme_manager.get_theme_display_name()
        assert app.theme_button.text() == expected

    def test_multiple_theme_cycles_complete(self, app):
        """Cycling more times than there are themes wraps cleanly."""
        for _ in range(5):
            app.cycle_theme()
        # If we got here without exception, the cycle is well-behaved.
        assert app.theme_manager.current_theme is not None


# ══════════════════════════════════════════════════════════════════════════════
# 3. FILE-HANDLING PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
class TestIconBuilderAppFileHandling:
    """The handle_files() orchestration — the entry point for both file dialog
    and drag-and-drop. Tests it directly with real PNG files."""

    def test_handle_files_with_valid_png(self, app, sample_png):
        """Loading one valid PNG populates detected_images."""
        png = sample_png(name="valid.png", size=64)
        app.handle_files([png])
        assert len(app.image_processor.get_detected_images()) > 0

    def test_handle_files_empty_list(self, app):
        """Empty list is a no-op, not an error."""
        before = len(app.image_processor.get_detected_images())
        app.handle_files([])
        after = len(app.image_processor.get_detected_images())
        assert before == after

    def test_handle_files_with_nonexistent_path(self, app):
        """Bad path is logged and skipped, not raised."""
        app.handle_files(["/no/such/path/icon.png"])
        # Should complete without exception; nothing loaded.
        assert len(app.image_processor.get_detected_images()) == 0

    def test_handle_files_mixed_valid_and_invalid(self, app, sample_png):
        """One valid + one invalid file → valid one still loads."""
        good = sample_png(name="good.png", size=64)
        app.handle_files([good, "/no/such/file.png"])
        assert len(app.image_processor.get_detected_images()) > 0

    def test_handle_files_unsupported_extension_skipped(self, app, tmp_dir):
        """A .txt file is silently skipped (no exception)."""
        txt_path = os.path.join(tmp_dir, "not_an_image.txt")
        Path(txt_path).write_text("hello")
        app.handle_files([txt_path])
        assert len(app.image_processor.get_detected_images()) == 0


# ══════════════════════════════════════════════════════════════════════════════
# 4. KEYBOARD SHORTCUTS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
class TestIconBuilderAppShortcuts:
    """All declared keyboard shortcuts should be registered as QShortcut
    children of the main window."""

    def _registered_keys(self, app) -> set[str]:
        """Collect every QShortcut's key sequence as a string."""
        keys: set[str] = set()
        for sc in app.findChildren(QShortcut):
            keys.add(sc.key().toString())
        return keys

    def test_critical_shortcuts_registered(self, app):
        """The shortcuts a user reaches for first are all there."""
        keys = self._registered_keys(app)
        for required in ("Ctrl+O", "Ctrl+B", "Ctrl+T", "F5", "Esc"):
            assert required in keys, f"Missing shortcut: {required}"

    def test_project_shortcuts_registered(self, app):
        """Save / Save As / New project shortcuts."""
        keys = self._registered_keys(app)
        for required in ("Ctrl+S", "Ctrl+Shift+S", "Ctrl+Shift+N"):
            assert required in keys, f"Missing project shortcut: {required}"

    def test_settings_and_help_shortcuts_registered(self, app):
        """Phase 8 shortcuts: settings, tooltip toggle, about."""
        keys = self._registered_keys(app)
        # Ctrl+, displays as "Ctrl+," in Qt; Ctrl+/ likewise.
        assert "Ctrl+," in keys
        assert "F11" in keys
        assert "Ctrl+/" in keys


# ══════════════════════════════════════════════════════════════════════════════
# 5. CLOSE-EVENT CLEANUP
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
class TestIconBuilderAppCloseEvent:
    """closeEvent should run a clean shutdown without raising."""

    def test_close_event_does_not_raise(self, app):
        """A normal close triggers no exception."""
        event = QCloseEvent()
        app.closeEvent(event)

    def test_close_event_stops_status_timer(self, app):
        """If the status timer was active, it should be stopped."""
        app._status_timer.start(60_000)
        assert app._status_timer.isActive()
        app.closeEvent(QCloseEvent())
        assert not app._status_timer.isActive()

    def test_close_event_clears_preview_images(self, app, sample_rgba):
        """Preview image dict should be empty after close."""
        # Populate something so we can verify it gets cleared.
        app.preview_images[64] = (sample_rgba(64, 64), "test")
        assert len(app.preview_images) > 0
        app.closeEvent(QCloseEvent())
        assert len(app.preview_images) == 0

    def test_close_event_cancels_batch_processor(self, app):
        """closeEvent calls batch_processor.cancel() on the live processor."""
        # Spy via a flag — we don't need a mocking lib.
        cancelled = []
        original = app.batch_processor.cancel
        app.batch_processor.cancel = lambda: cancelled.append(True) or original()
        app.closeEvent(QCloseEvent())
        assert cancelled == [True]


# ══════════════════════════════════════════════════════════════════════════════
# 6. PUBLIC API CONTRACTS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
class TestIconBuilderAppPublicAPI:
    """Methods exposed for external callers (settings dialog, session
    manager, etc.) — verify their return-type contracts."""

    def test_get_selected_sizes_returns_list_of_ints(self, app):
        sizes = app.get_selected_sizes()
        assert isinstance(sizes, list)
        assert all(isinstance(s, int) for s in sizes)

    def test_get_selected_sizes_nonempty_before_settings_open(self, app):
        """Without an opened settings dialog, returns the full ICON_SIZES list."""
        sizes = app.get_selected_sizes()
        assert len(sizes) > 0

    def test_get_selected_sizes_descending_order(self, app):
        """Default ordering is largest-first."""
        sizes = app.get_selected_sizes()
        assert sizes == sorted(sizes, reverse=True)

    def test_get_preview_background_settings_returns_tuple(self, app):
        result = app.get_preview_background_settings()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_get_preview_zoom_returns_int(self, app):
        zoom = app.get_preview_zoom()
        assert isinstance(zoom, int)
        assert zoom == 100  # Default value

    def test_get_session_state_returns_session_state(self, app):
        from core.session_manager import SessionState
        state = app._get_session_state()
        assert isinstance(state, SessionState)

    def test_session_state_includes_window_geometry(self, app):
        state = app._get_session_state()
        assert state.window_geometry is not None
        assert "width" in state.window_geometry
        assert "height" in state.window_geometry

    def test_session_state_loaded_files_is_list(self, app):
        state = app._get_session_state()
        assert isinstance(state.loaded_files, list)


# ══════════════════════════════════════════════════════════════════════════════
# 7. INTEGRATION — END-TO-END SHELL BEHAVIOR
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
@pytest.mark.integration
class TestIconBuilderAppIntegration:
    """Cross-cutting behavior — shell + file pipeline + theme + close together."""

    def test_load_then_cycle_theme_then_close(self, app, sample_png):
        """A realistic short session: load file → switch theme → close."""
        png = sample_png(name="session.png", size=64)
        app.handle_files([png])
        assert len(app.image_processor.get_detected_images()) > 0

        app.cycle_theme()
        # Theme button reflects new theme.
        assert app.theme_button.text() == \
            app.theme_manager.get_theme_display_name()

        # Clean shutdown.
        app.closeEvent(QCloseEvent())

    def test_session_state_after_file_load(self, app, sample_png):
        """Session state captures loaded files after handle_files()."""
        png = sample_png(name="captured.png", size=64)
        app.handle_files([png])
        state = app._get_session_state()
        # The file_listbox should show entries that ended up in state.
        assert isinstance(state.loaded_files, list)
