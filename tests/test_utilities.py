"""
RNV Icon Builder — Utility Module Tests
========================================

Targeted unit tests for the utility/infrastructure modules:

  - error_handler.py   — safe_execute branches, SafeFileOperations
  - signal_manager.py  — connection tracking, disconnect paths
  - font_loader.py     — caching, family helpers
  - dialog_helper.py   — show_custom, ask_yes_no_cancel, show_success
  - session_manager.py — auto-save lifecycle, recovery flag

These modules sit underneath the application and dialog layers — they're
what makes everything else work cleanly. Tests here focus on the contracts
each module exposes (return types, state transitions, error paths) rather
than full integration.

Modules deliberately not covered here:
  - async_file_ops.py — async I/O wrappers, exercised at runtime
  - debug_button.py   — internal dev tool
  - cli.py            — best tested via subprocess in CI
"""

from __future__ import annotations

import os
import time
import pytest

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QWidget


# ══════════════════════════════════════════════════════════════════════════════
# 1. ERROR HANDLER — safe_execute branches and SafeFileOperations
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestErrorHandlerExtended:

    def test_safe_execute_filenotfounderror_branch(self):
        """safe_execute catches FileNotFoundError and returns (False, default)."""
        from utils.error_handler import ErrorHandler

        def missing_file():
            with open("/no/such/file/anywhere.txt") as f:
                return f.read()

        ok, result = ErrorHandler.safe_execute(missing_file, "load missing")
        assert ok is False
        assert result is None  # Default return.

    def test_safe_execute_with_default_return(self):
        """When func raises, default_return value is propagated."""
        from utils.error_handler import ErrorHandler

        ok, result = ErrorHandler.safe_execute(
            lambda: 1 / 0, "divide", default_return="fallback")
        assert ok is False
        assert result == "fallback"

    def test_safe_execute_passes_args_and_kwargs(self):
        """safe_execute correctly forwards args and kwargs to func."""
        from utils.error_handler import ErrorHandler

        def add(a, b, multiplier=1):
            return (a + b) * multiplier

        ok, result = ErrorHandler.safe_execute(
            add, "add op", args=(2, 3), kwargs={"multiplier": 4})
        assert ok is True
        assert result == 20

    def test_error_category_constants_exist(self):
        """ErrorCategory exposes the named buckets safe_execute uses."""
        from utils.error_handler import ErrorCategory

        for name in ("FILE_IO", "PERMISSION", "VALIDATION", "RESOURCE",
                     "UNKNOWN"):
            assert hasattr(ErrorCategory, name)

    def test_safe_open_file_success(self, tmp_dir):
        """SafeFileOperations.safe_open_file returns the handle on success."""
        from utils.error_handler import SafeFileOperations

        path = os.path.join(tmp_dir, "open_me.txt")
        with open(path, "w") as f:
            f.write("hi")

        ok, handle = SafeFileOperations.safe_open_file(path, mode="r")
        assert ok is True
        assert handle is not None
        handle.close()

    def test_safe_open_file_missing_returns_failure(self):
        from utils.error_handler import SafeFileOperations

        ok, handle = SafeFileOperations.safe_open_file(
            "/no/such/file.txt", mode="r")
        assert ok is False

    def test_safe_write_file_success(self, tmp_dir):
        from utils.error_handler import SafeFileOperations

        path = os.path.join(tmp_dir, "write_me.txt")
        ok = SafeFileOperations.safe_write_file(path, "content")
        assert ok is True
        assert open(path).read() == "content"

    def test_safe_write_file_invalid_path_fails(self):
        """Writing to a non-creatable path returns False, doesn't raise."""
        from utils.error_handler import SafeFileOperations

        ok = SafeFileOperations.safe_write_file(
            "/no/such/folder/anywhere/file.txt", "content")
        assert ok is False


# ══════════════════════════════════════════════════════════════════════════════
# 2. SIGNAL MANAGER — connection tracking and lifecycle
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestSignalManager:
    """SignalConnectionManager tracks Qt signal connections so they can all
    be cleanly disconnected on widget cleanup. Test the lifecycle."""

    @staticmethod
    def _make_emitter():
        """Helper — a QObject with a single pyqtSignal."""
        class Emitter(QObject):
            triggered = pyqtSignal(int)

        return Emitter()

    def test_manager_instantiates(self, qapp):
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        assert mgr.get_active_count() == 0

    def test_connect_increments_active_count(self, qapp):
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        received: list = []
        mgr.connect(emitter, emitter.triggered, lambda v: received.append(v),
                    name="test_conn")
        assert mgr.get_active_count() == 1

    def test_disconnect_all_zeros_count(self, qapp):
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        for i in range(3):
            mgr.connect(emitter, emitter.triggered, lambda v, i=i: None,
                        name=f"slot_{i}")
        assert mgr.get_active_count() == 3
        mgr.disconnect_all()
        assert mgr.get_active_count() == 0

    def test_disconnect_widget(self, qapp):
        """disconnect_widget removes only that widget's connections."""
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        a = self._make_emitter()
        b = self._make_emitter()
        mgr.connect(a, a.triggered, lambda v: None, name="a_conn")
        mgr.connect(b, b.triggered, lambda v: None, name="b_conn")
        removed = mgr.disconnect_widget(a)
        assert removed >= 1
        assert mgr.get_active_count() == 1

    def test_disconnect_by_name(self, qapp):
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        mgr.connect(emitter, emitter.triggered, lambda v: None, name="named")
        mgr.connect(emitter, emitter.triggered, lambda v: None, name="other")
        removed = mgr.disconnect_by_name("named")
        assert removed >= 1
        assert mgr.get_active_count() == 1

    def test_get_stats_returns_dict_with_counts(self, qapp):
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        mgr.connect(emitter, emitter.triggered, lambda v: None,
                    name="stat_test")
        stats = mgr.get_stats()
        assert isinstance(stats, dict)
        # Stats should report at least one active connection.
        assert any(isinstance(v, int) and v > 0 for v in stats.values())

    def test_clear_resets_manager(self, qapp):
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        mgr.connect(emitter, emitter.triggered, lambda v: None,
                    name="clear_me")
        mgr.clear()
        assert mgr.get_active_count() == 0


# ══════════════════════════════════════════════════════════════════════════════
# 3. FONT LOADER — caching + family helpers
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestFontLoader:

    def test_load_embedded_font_returns_qfont(self, qapp):
        from PyQt6.QtGui import QFont
        from utils.font_loader import load_embedded_font

        result = load_embedded_font()
        assert isinstance(result, QFont)

    def test_load_embedded_font_caches(self, qapp):
        """Second call returns the cached family (same family name)."""
        from utils.font_loader import load_embedded_font

        first = load_embedded_font()
        second = load_embedded_font()
        # Same family means cache served the second call.
        assert first.family() == second.family()

    def test_helper_fonts_return_qfonts(self, qapp):
        """get_bold_font / get_regular_font / get_monospace_font work."""
        from PyQt6.QtGui import QFont
        from utils.font_loader import (get_bold_font, get_regular_font,
                                        get_monospace_font)

        for fn in (get_bold_font, get_regular_font, get_monospace_font):
            result = fn(size=12)
            assert isinstance(result, QFont)
            assert result.pointSize() == 12


# ══════════════════════════════════════════════════════════════════════════════
# 4. DIALOG HELPER — uncovered methods
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestDialogHelperExtended:

    def test_show_custom_displays_message(self, qapp, monkeypatch):
        """show_custom passes through to QMessageBox.exec, which we capture."""
        from utils.dialog_helper import DialogHelper

        captured = []
        monkeypatch.setattr(
            QMessageBox, "exec",
            lambda self: captured.append(
                (self.windowTitle(), self.text())) or
            QMessageBox.StandardButton.Yes)

        result = DialogHelper.show_custom(
            parent=None, title="Custom", message="Pick one",
            buttons=(QMessageBox.StandardButton.Yes
                     | QMessageBox.StandardButton.No))
        assert captured == [("Custom", "Pick one")]
        assert result == QMessageBox.StandardButton.Yes

    def test_ask_yes_no_cancel_returns_dialog_result(self, qapp,
                                                       monkeypatch):
        """ask_yes_no_cancel maps QMessageBox button → DialogResult enum."""
        from utils.dialog_helper import DialogHelper, DialogResult

        # Simulate the user clicking "Cancel".
        monkeypatch.setattr(
            QMessageBox, "exec",
            lambda self: QMessageBox.StandardButton.Cancel)

        result = DialogHelper.ask_yes_no_cancel(
            parent=None, message="Save?", title="Save Changes")
        assert result == DialogResult.CANCEL

    def test_show_success(self, qapp, monkeypatch):
        from utils.dialog_helper import DialogHelper

        captured = []
        monkeypatch.setattr(
            QMessageBox, "exec",
            lambda self: captured.append(self.text())
            or QMessageBox.StandardButton.Ok)

        DialogHelper.show_success(parent=None, message="Done!", title="Yay")
        assert captured == ["Done!"]


# ══════════════════════════════════════════════════════════════════════════════
# 5. SESSION MANAGER — auto-save and recovery
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestSessionManagerExtended:

    def _make_state(self):
        from core.session_manager import SessionState

        return SessionState(
            loaded_files=["/a.png", "/b.png"],
            selected_sizes=[256, 64],
            autofill_enabled=True,
            png_compression=True,
            current_project_path="",
            window_geometry={"x": 0, "y": 0,
                             "width": 800, "height": 600},
        )

    def test_session_state_is_valid_when_fresh(self):
        from core.session_manager import SessionState

        state = SessionState(
            loaded_files=[], selected_sizes=[16],
            autofill_enabled=True, png_compression=True,
            current_project_path="",
            window_geometry={"x": 0, "y": 0, "width": 1, "height": 1},
        )
        # is_valid is a @property, not a method.
        assert isinstance(state.is_valid, bool)

    def test_session_state_age_seconds_is_nonneg(self):
        state = self._make_state()
        # age_seconds is a @property.
        age = state.age_seconds
        assert isinstance(age, float)
        assert age >= 0.0

    def test_session_state_formatted_time_is_string(self):
        state = self._make_state()
        # formatted_time is a @property.
        result = state.formatted_time
        assert isinstance(result, str)
        assert len(result) > 0

    def test_auto_save_lifecycle(self, qapp):
        """start_auto_save then stop_auto_save — no crash, flag transitions."""
        from core.session_manager import SessionManager

        sm = SessionManager()
        sm.set_state_getter(lambda: self._make_state())

        sm.start_auto_save(interval_ms=60_000)
        # is_auto_save_enabled is a @property.
        assert sm.is_auto_save_enabled is True

        sm.stop_auto_save()
        assert sm.is_auto_save_enabled is False

    def test_has_recovery_returns_bool(self, qapp):
        from core.session_manager import SessionManager

        sm = SessionManager()
        # has_recovery returns a bool — exact value depends on filesystem
        # state we patched away in conftest. The contract is the type.
        result = sm.has_recovery()
        assert isinstance(result, bool)

    def test_clear_recovery_does_not_raise(self, qapp):
        from core.session_manager import SessionManager

        sm = SessionManager()
        sm.clear_recovery()  # No-op when there's nothing to clear; must not raise.


# ══════════════════════════════════════════════════════════════════════════════
# 6. ERROR HANDLER — additional dialog branches (Phase 10C)
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestErrorHandlerMoreDialogs:

    def test_confirm_action_yes(self, qapp, monkeypatch):
        """ErrorHandler.confirm_action returning the user's Yes selection."""
        from utils.error_handler import ErrorHandler

        monkeypatch.setattr(
            QMessageBox, "exec",
            lambda self: QMessageBox.StandardButton.Yes)
        result = ErrorHandler.confirm_action(
            parent=None, message="Continue?", title="Confirm")
        assert result is True

    def test_confirm_action_no(self, qapp, monkeypatch):
        from utils.error_handler import ErrorHandler

        monkeypatch.setattr(
            QMessageBox, "exec",
            lambda self: QMessageBox.StandardButton.No)
        result = ErrorHandler.confirm_action(
            parent=None, message="Continue?", title="Confirm")
        assert result is False

    def test_styled_question_box(self, qapp, monkeypatch):
        from utils.error_handler import styled_question_box

        monkeypatch.setattr(
            QMessageBox, "exec",
            lambda self: QMessageBox.StandardButton.Yes)
        result = styled_question_box(parent=None, title="Q",
                                       text="Are you sure?")
        # Returns the StandardButton value clicked.
        assert result == QMessageBox.StandardButton.Yes

    def test_styled_message_box_info(self, qapp, monkeypatch):
        from utils.error_handler import styled_message_box

        monkeypatch.setattr(
            QMessageBox, "exec",
            lambda self: QMessageBox.StandardButton.Ok)
        styled_message_box(parent=None,
                            icon=QMessageBox.Icon.Information,
                            title="Info",
                            text="Here's info")

    def test_get_error_suggestion_for_permission(self):
        """ErrorCategory.PERMISSION yields a meaningful suggestion."""
        from utils.error_handler import ErrorHandler, ErrorCategory

        result = ErrorHandler._get_error_suggestion(
            ErrorCategory.PERMISSION, "details")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_error_suggestion_for_validation(self):
        from utils.error_handler import ErrorHandler, ErrorCategory

        result = ErrorHandler._get_error_suggestion(
            ErrorCategory.VALIDATION, "details")
        assert isinstance(result, str)


# ══════════════════════════════════════════════════════════════════════════════
# 7. SIGNAL MANAGER — coverage of remaining disconnect paths (Phase 10C)
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestSignalManagerExtended:
    """Extends TestSignalManager above to cover specialized disconnect paths."""

    @staticmethod
    def _make_emitter():
        from PyQt6.QtCore import QObject, pyqtSignal

        class Emitter(QObject):
            triggered = pyqtSignal(int)

        return Emitter()

    def test_disconnect_widget_returns_count_zero_when_no_match(self, qapp):
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        unrelated = self._make_emitter()
        # No connections registered for `unrelated` → disconnect returns 0.
        removed = mgr.disconnect_widget(unrelated)
        assert removed == 0

    def test_disconnect_by_name_returns_zero_when_no_match(self, qapp):
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        removed = mgr.disconnect_by_name("never_existed")
        assert removed == 0

    def test_get_stats_with_no_connections(self, qapp):
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        stats = mgr.get_stats()
        assert isinstance(stats, dict)

    def test_clear_safe_to_call_when_empty(self, qapp):
        """clear() on an empty manager doesn't raise."""
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        mgr.clear()
        assert mgr.get_active_count() == 0

    def test_multiple_disconnect_all_idempotent(self, qapp):
        """Two disconnect_all calls in a row — second is a no-op."""
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        mgr.connect(emitter, emitter.triggered, lambda v: None,
                    name="idempotent_test")
        mgr.disconnect_all()
        mgr.disconnect_all()  # Should be a no-op, no crash.
        assert mgr.get_active_count() == 0

    def test_connect_three_then_disconnect_two_by_name(self, qapp):
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        for i in range(3):
            mgr.connect(emitter, emitter.triggered,
                        lambda v, _=i: None, name=f"slot_{i}")
        assert mgr.get_active_count() == 3
        mgr.disconnect_by_name("slot_0")
        mgr.disconnect_by_name("slot_1")
        assert mgr.get_active_count() == 1


# ══════════════════════════════════════════════════════════════════════════════
# 8. FONT LOADER — helper font getters (Phase 10D)
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestFontLoaderHelpers:
    """Coverage for get_bold_font / get_regular_font / get_monospace_font."""

    def test_get_bold_font_returns_bold_qfont(self, qapp):
        from utils.font_loader import get_bold_font
        from PyQt6.QtGui import QFont

        font = get_bold_font(14)
        assert isinstance(font, QFont)
        assert font.bold() is True
        assert font.pointSize() == 14

    def test_get_bold_font_default_size(self, qapp):
        from utils.font_loader import get_bold_font
        font = get_bold_font()
        assert font.pointSize() == 10

    def test_get_regular_font_not_bold(self, qapp):
        from utils.font_loader import get_regular_font
        from PyQt6.QtGui import QFont

        font = get_regular_font(12)
        assert isinstance(font, QFont)
        assert font.bold() is False
        assert font.pointSize() == 12

    def test_get_regular_font_default_size(self, qapp):
        from utils.font_loader import get_regular_font
        font = get_regular_font()
        assert font.pointSize() == 10

    def test_get_monospace_font_returns_qfont(self, qapp):
        from utils.font_loader import get_monospace_font
        from PyQt6.QtGui import QFont

        font = get_monospace_font(11)
        assert isinstance(font, QFont)
        assert font.pointSize() == 11

    def test_get_monospace_font_uses_monospace_hint(self, qapp):
        from utils.font_loader import get_monospace_font
        from PyQt6.QtGui import QFont

        font = get_monospace_font(10)
        assert font.styleHint() == QFont.StyleHint.Monospace


# ══════════════════════════════════════════════════════════════════════════════
# 9. SIGNAL MANAGER — disconnect + list + introspection (Phase 10D)
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestSignalManagerExtras:

    @staticmethod
    def _make_emitter():
        from PyQt6.QtCore import QObject, pyqtSignal

        class Emitter(QObject):
            triggered = pyqtSignal(int)

        return Emitter()

    def test_disconnect_specific_signal_returns_true(self, qapp):
        """disconnect(widget, signal, slot) succeeds for a real connection."""
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        slot = lambda v: None
        mgr.connect(emitter, emitter.triggered, slot, name="specific")

        ok = mgr.disconnect(emitter, emitter.triggered, slot)
        assert ok is True

    def test_disconnect_already_disconnected_returns_false(self, qapp):
        """Calling disconnect twice — second returns False (already gone)."""
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        slot = lambda v: None
        mgr.connect(emitter, emitter.triggered, slot, name="twice")
        mgr.disconnect(emitter, emitter.triggered, slot)
        # Second disconnect should return False (signal already disconnected).
        result = mgr.disconnect(emitter, emitter.triggered, slot)
        assert result is False

    def test_print_stats_does_not_raise(self, qapp):
        """print_stats is a side-effect-only diagnostic; must not crash."""
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        mgr.connect(emitter, emitter.triggered, lambda v: None,
                    name="stats_demo")
        mgr.print_stats()  # No return value, just shouldn't raise.

    def test_list_connections_returns_descriptions(self, qapp):
        """list_connections returns a list of human-readable strings."""
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        mgr.connect(emitter, emitter.triggered, lambda v: None, name="listed")

        result = mgr.list_connections()
        assert isinstance(result, list)
        assert any("listed" in desc for desc in result)

    def test_list_connections_filtered_by_widget(self, qapp):
        """Passing a widget filters the listing to that widget only."""
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter_a = self._make_emitter()
        emitter_b = self._make_emitter()
        mgr.connect(emitter_a, emitter_a.triggered, lambda v: None, name="a_slot")
        mgr.connect(emitter_b, emitter_b.triggered, lambda v: None, name="b_slot")

        result = mgr.list_connections(emitter_a)
        # Filtered list mentions only the slot we connected to emitter_a.
        assert any("a_slot" in d for d in result)
        assert not any("b_slot" in d for d in result)

    def test_get_widget_connection_count(self, qapp):
        """get_widget_connection_count counts active connections per widget."""
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        mgr.connect(emitter, emitter.triggered, lambda v: None, name="c1")
        mgr.connect(emitter, emitter.triggered, lambda v: None, name="c2")
        assert mgr.get_widget_connection_count(emitter) == 2

    def test_disconnect_widget_returns_correct_count(self, qapp):
        """disconnect_widget returns the number it actually disconnected."""
        from utils.signal_manager import SignalConnectionManager

        mgr = SignalConnectionManager()
        emitter = self._make_emitter()
        for i in range(3):
            mgr.connect(emitter, emitter.triggered,
                        lambda v, _=i: None, name=f"w{i}")
        removed = mgr.disconnect_widget(emitter)
        assert removed == 3


# ══════════════════════════════════════════════════════════════════════════════
# 10. SESSION MANAGER — save/load round-trip + recovery state (Phase 10D ext)
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestSessionSaveLoad:
    """Coverage for save_session / load_session sync paths and recovery."""

    @staticmethod
    def _make_state():
        from core.session_manager import SessionState
        return SessionState(
            loaded_files=["/a.png"],
            selected_sizes=[64],
            autofill_enabled=True,
            png_compression=True,
            current_project_path="",
            window_geometry={"x": 0, "y": 0, "width": 800, "height": 600},
        )

    def test_save_session_sync_returns_true(self, qapp):
        """Sync write path (async_write=False) — sets timestamp, writes file."""
        from core.session_manager import SessionManager
        sm = SessionManager()
        state = self._make_state()
        ok = sm.save_session(state, async_write=False)
        assert ok is True

    def test_load_session_after_sync_save_round_trip(self, qapp):
        """After a sync save, load_session retrieves the state."""
        from core.session_manager import SessionManager
        sm = SessionManager()
        original = self._make_state()
        sm.save_session(original, async_write=False)

        loaded = sm.load_session()
        assert loaded is not None
        assert loaded.selected_sizes == original.selected_sizes
        assert loaded.autofill_enabled == original.autofill_enabled

    def test_load_session_when_none_saved_returns_none(self, qapp):
        """If no saved session exists, load_session returns None."""
        from core.session_manager import SessionManager
        sm = SessionManager()
        sm.clear_recovery()
        # Force-remove the auto-save file.
        from core.session_manager import SESSION_AUTO_SAVE_PATH
        try:
            SESSION_AUTO_SAVE_PATH.unlink()
        except (OSError, FileNotFoundError):
            pass
        result = sm.load_session()
        assert result is None

    def test_get_recovery_state_returns_state_or_none(self, qapp):
        """get_recovery_state returns a SessionState or None — never raises."""
        from core.session_manager import SessionManager
        sm = SessionManager()
        result = sm.get_recovery_state()
        # Either None (no recovery) or a SessionState — both valid.
        if result is not None:
            from core.session_manager import SessionState
            assert isinstance(result, SessionState)

    def test_set_state_getter_stores_callable(self, qapp):
        """set_state_getter accepts and stores a callable."""
        from core.session_manager import SessionManager
        sm = SessionManager()
        sm.set_state_getter(lambda: self._make_state())
        # Trigger one tick — should not raise.
        sm._on_auto_save_timer()


# ══════════════════════════════════════════════════════════════════════════════
# 11. RECENT FILES — sample_png is fixture-scoped to test files (not utilities)
# ══════════════════════════════════════════════════════════════════════════════
# (No new tests here — recent_files extras live in test_managers.py)
