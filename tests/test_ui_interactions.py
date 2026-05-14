"""
RNV Icon Builder — Phase 4 UI Interaction Tests
================================================

Drives the dialog and panel widgets directly with pytest-qt's qtbot, plus
keyboard shortcuts on the main window. All bootstrap, the QApplication, and
the `app` fixture come from conftest.py.

Scope (per Phase 4 plan):
  - BaseDialog inheritance and constructor options
  - AboutDialog instantiation, theme switching, cleanup
  - IcoAnalyzerDialog file analysis (valid + invalid)
  - MetadataPanel set_image / clear / theme / signal emission
  - ContextPreviewDialog instantiation and theming
  - SettingsDialog instantiation, signals, size-checkbox state
  - DialogHelper static methods (with QMessageBox.exec patched)
  - Main window keyboard shortcuts via qtbot.keyClick

Out of scope (deferred):
  - Worker / signal-spy tests (Phase 5)
  - Property-based fuzz tests (Phase 6)
  - Snapshot locking (Phase 7)
  - Performance benchmarks (Phase 8)
"""

import os
import tempfile
from pathlib import Path

import pytest

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QCheckBox, QMessageBox, QTabWidget


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS — small fixtures local to UI tests
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def fusion_qapp(qapp):
    """qapp with Fusion style applied — required for proper palette behavior
    in any dialog that uses QPalette roles."""
    qapp.setStyle("Fusion")
    return qapp


@pytest.fixture
def patch_message_box(monkeypatch):
    """
    Replace QMessageBox.exec with a recorder so DialogHelper's modal calls
    don't block. Returns a list that captures (title, text) per call and a
    setter for the simulated user click.
    """
    captured: list[tuple[str, str]] = []
    response = {"value": QMessageBox.StandardButton.Ok}

    def fake_exec(self):
        captured.append((self.windowTitle(), self.text()))
        return response["value"]

    monkeypatch.setattr(QMessageBox, "exec", fake_exec)

    class _Helper:
        calls = captured

        @staticmethod
        def set_response(button: QMessageBox.StandardButton) -> None:
            response["value"] = button

    return _Helper


# ══════════════════════════════════════════════════════════════════════════════
# 1. BASE DIALOG — verify the inheritance plumbing
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.ui
class TestBaseDialog:
    """BaseDialog is abstract-ish — exercised through its concrete subclasses."""

    def test_base_dialog_with_fixed_size(self, fusion_qapp, qtbot):
        from ui.base_dialog import BaseDialog

        dlg = BaseDialog(parent=None, title="FixedTest", fixed_size=(400, 300))
        qtbot.addWidget(dlg)
        # fixed_size sets both min and max to lock the dimensions
        # (per the project's documented Windows-compositor workaround).
        assert dlg.minimumWidth() == 400
        assert dlg.maximumWidth() == 400
        assert dlg.minimumHeight() == 300
        assert dlg.maximumHeight() == 300

    def test_base_dialog_with_min_max(self, fusion_qapp, qtbot):
        from ui.base_dialog import BaseDialog

        dlg = BaseDialog(parent=None, title="MinMaxTest",
                         min_size=(300, 200), max_size=(800, 600))
        qtbot.addWidget(dlg)
        assert dlg.minimumWidth() == 300
        assert dlg.maximumWidth() == 800

    def test_base_dialog_title_set(self, fusion_qapp, qtbot):
        from ui.base_dialog import BaseDialog

        dlg = BaseDialog(parent=None, title="HelloDialog")
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "HelloDialog"

    def test_base_dialog_signal_manager_initialized(self, fusion_qapp, qtbot):
        """init_signal_manager() runs in __init__ and sets up tracking."""
        from ui.base_dialog import BaseDialog

        dlg = BaseDialog(parent=None)
        qtbot.addWidget(dlg)
        # SignalMixin gives _managed_connections (or similar) — just verify
        # the dialog has at least one signal-tracking attribute.
        attrs = dir(dlg)
        assert any("signal" in a.lower() or "connection" in a.lower()
                   for a in attrs)


# ══════════════════════════════════════════════════════════════════════════════
# 2. ABOUT DIALOG
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.ui
class TestAboutDialog:

    def test_about_dialog_instantiates(self, fusion_qapp, qtbot):
        from ui.about_dialog import AboutDialog

        dlg = AboutDialog(parent=None, is_dark=True)
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_about_dialog_window_title(self, fusion_qapp, qtbot):
        from ui.about_dialog import AboutDialog

        dlg = AboutDialog(parent=None, is_dark=True)
        qtbot.addWidget(dlg)
        assert "About" in dlg.windowTitle()
        assert "RNV Icon Builder" in dlg.windowTitle()

    def test_about_dialog_has_tab_widget(self, fusion_qapp, qtbot):
        """About dialog uses tabs (About / Features / Shortcuts / Credits)."""
        from ui.about_dialog import AboutDialog

        dlg = AboutDialog(parent=None, is_dark=True)
        qtbot.addWidget(dlg)
        tabs = dlg.findChildren(QTabWidget)
        assert len(tabs) > 0

    def test_about_dialog_set_theme_dark(self, fusion_qapp, qtbot):
        from ui.about_dialog import AboutDialog

        dlg = AboutDialog(parent=None, is_dark=False)
        qtbot.addWidget(dlg)
        dlg.set_theme(True)
        assert dlg._is_dark is True

    def test_about_dialog_set_theme_light(self, fusion_qapp, qtbot):
        from ui.about_dialog import AboutDialog

        dlg = AboutDialog(parent=None, is_dark=True)
        qtbot.addWidget(dlg)
        dlg.set_theme(False)
        assert dlg._is_dark is False


# ══════════════════════════════════════════════════════════════════════════════
# 3. ICO ANALYZER DIALOG
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.ui
class TestIcoAnalyzerDialog:

    def test_ico_analyzer_instantiates(self, fusion_qapp, qtbot):
        from ui.ico_analyzer import IcoAnalyzerDialog

        dlg = IcoAnalyzerDialog(parent=None)
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_ico_analyzer_window_title(self, fusion_qapp, qtbot):
        from ui.ico_analyzer import IcoAnalyzerDialog

        dlg = IcoAnalyzerDialog(parent=None)
        qtbot.addWidget(dlg)
        assert "ICO" in dlg.windowTitle()

    def test_ico_analyzer_extract_button_initially_disabled(
            self, fusion_qapp, qtbot):
        from ui.ico_analyzer import IcoAnalyzerDialog

        dlg = IcoAnalyzerDialog(parent=None)
        qtbot.addWidget(dlg)
        assert dlg.extract_btn.isEnabled() is False

    def test_ico_analyzer_initial_info_is_none(self, fusion_qapp, qtbot):
        from ui.ico_analyzer import IcoAnalyzerDialog

        dlg = IcoAnalyzerDialog(parent=None)
        qtbot.addWidget(dlg)
        assert dlg._current_info is None

    def test_ico_analyzer_handles_missing_file(self, fusion_qapp, qtbot):
        """Analyzing a nonexistent path returns False, doesn't crash."""
        from ui.ico_analyzer import IcoAnalyzerDialog

        dlg = IcoAnalyzerDialog(parent=None)
        qtbot.addWidget(dlg)
        result = dlg.analyze_file("/no/such/file.ico")
        assert result is False
        assert dlg.extract_btn.isEnabled() is False

    def test_ico_analyzer_analyzes_valid_ico(self, fusion_qapp, qtbot,
                                              tmp_dir, sample_rgba):
        """Generate a real ICO, then analyze it."""
        from ui.ico_analyzer import IcoAnalyzerDialog
        from core.icon_builder_core import IconBuilderCore

        # Build a real multi-size ICO file to feed the analyzer.
        images = {64: sample_rgba(64, 64), 32: sample_rgba(32, 32)}
        ico_path = os.path.join(tmp_dir, "valid.ico")
        IconBuilderCore.build_ico_file(images, ico_path)

        dlg = IcoAnalyzerDialog(parent=None)
        qtbot.addWidget(dlg)
        result = dlg.analyze_file(ico_path)
        assert result is True
        assert dlg._current_info is not None
        assert dlg.extract_btn.isEnabled() is True


# ══════════════════════════════════════════════════════════════════════════════
# 4. METADATA PANEL — has the only public signal we can drive
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.ui
class TestMetadataPanel:

    def test_metadata_panel_instantiates(self, fusion_qapp, qtbot):
        from ui.metadata_panel import MetadataPanel

        panel = MetadataPanel(parent=None)
        qtbot.addWidget(panel)
        assert panel is not None

    def test_metadata_panel_initial_state(self, fusion_qapp, qtbot):
        from ui.metadata_panel import MetadataPanel

        panel = MetadataPanel(parent=None)
        qtbot.addWidget(panel)
        assert panel._current_image is None
        assert panel._current_path is None

    def test_metadata_panel_set_image_none_clears_state(
            self, fusion_qapp, qtbot, sample_rgba):
        from ui.metadata_panel import MetadataPanel

        panel = MetadataPanel(parent=None)
        qtbot.addWidget(panel)
        # Populate then clear.
        panel.set_image(sample_rgba(64, 64), file_path="/x.png", size_label=64)
        panel.set_image(None)
        assert panel._current_image is None

    def test_metadata_panel_set_image_stores_reference(
            self, fusion_qapp, qtbot, sample_rgba):
        from ui.metadata_panel import MetadataPanel

        panel = MetadataPanel(parent=None)
        qtbot.addWidget(panel)
        img = sample_rgba(128, 128)
        panel.set_image(img, file_path="/test.png", size_label=128)
        assert panel._current_image is img
        assert panel._current_path == "/test.png"

    def test_metadata_panel_emits_signal_on_set_image(
            self, fusion_qapp, qtbot, sample_rgba):
        """set_image() with a real image emits metadata_updated."""
        from ui.metadata_panel import MetadataPanel

        panel = MetadataPanel(parent=None)
        qtbot.addWidget(panel)
        with qtbot.waitSignal(panel.metadata_updated, timeout=1000):
            panel.set_image(sample_rgba(64, 64),
                            file_path="/x.png",
                            size_label=64)

    def test_metadata_panel_clear(self, fusion_qapp, qtbot, sample_rgba):
        from ui.metadata_panel import MetadataPanel

        panel = MetadataPanel(parent=None)
        qtbot.addWidget(panel)
        panel.set_image(sample_rgba(64, 64), file_path="/x.png", size_label=64)
        panel.clear()
        assert panel._current_image is None
        assert panel._current_path is None

    def test_metadata_panel_apply_theme(self, fusion_qapp, qtbot):
        from ui.metadata_panel import MetadataPanel

        panel = MetadataPanel(parent=None)
        qtbot.addWidget(panel)
        panel.apply_theme(is_dark=True)   # Should not raise.
        panel.apply_theme(is_dark=False)  # Should not raise.


# ══════════════════════════════════════════════════════════════════════════════
# 5. CONTEXT PREVIEW DIALOG
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.ui
class TestContextPreviewDialog:

    def test_context_preview_instantiates_with_images(
            self, fusion_qapp, qtbot, sample_rgba):
        from ui.context_preview import ContextPreviewDialog

        images = {64: sample_rgba(64, 64), 32: sample_rgba(32, 32)}
        dlg = ContextPreviewDialog(images=images, parent=None)
        qtbot.addWidget(dlg)
        assert dlg.images == images

    def test_context_preview_window_title(self, fusion_qapp, qtbot,
                                           sample_rgba):
        from ui.context_preview import ContextPreviewDialog

        dlg = ContextPreviewDialog(images={64: sample_rgba(64, 64)},
                                    parent=None)
        qtbot.addWidget(dlg)
        assert "Context" in dlg.windowTitle()

    def test_context_preview_fixed_size(self, fusion_qapp, qtbot,
                                         sample_rgba):
        """Dialog declares fixed_size=(600, 500)."""
        from ui.context_preview import ContextPreviewDialog

        dlg = ContextPreviewDialog(images={64: sample_rgba(64, 64)},
                                    parent=None)
        qtbot.addWidget(dlg)
        assert dlg.minimumWidth() == 600
        assert dlg.maximumWidth() == 600

    def test_context_preview_apply_theme_does_not_raise(
            self, fusion_qapp, qtbot, sample_rgba):
        from ui.context_preview import ContextPreviewDialog

        dlg = ContextPreviewDialog(images={64: sample_rgba(64, 64)},
                                    parent=None)
        qtbot.addWidget(dlg)
        # Theme switch — should complete cleanly.
        dlg.apply_theme_from_manager("Light")
        dlg.apply_theme_from_manager("Dark")


# ══════════════════════════════════════════════════════════════════════════════
# 6. SETTINGS DIALOG — biggest UI surface, biggest coverage gain
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.ui
class TestSettingsDialog:

    def _make_dialog(self, qtbot):
        """Helper — instantiate with no managers (defensive for tests)."""
        from ui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(parent=None)
        qtbot.addWidget(dlg)
        return dlg

    def test_settings_dialog_instantiates(self, fusion_qapp, qtbot):
        dlg = self._make_dialog(qtbot)
        assert dlg is not None

    def test_settings_dialog_window_title(self, fusion_qapp, qtbot):
        dlg = self._make_dialog(qtbot)
        assert "Settings" in dlg.windowTitle()

    def test_settings_dialog_size_checkboxes_populated(
            self, fusion_qapp, qtbot):
        from utils.config import ICON_SIZES

        dlg = self._make_dialog(qtbot)
        # Every ICON_SIZES value should have a corresponding checkbox.
        for size in ICON_SIZES:
            assert size in dlg.size_checkboxes
            assert isinstance(dlg.size_checkboxes[size], QCheckBox)

    def test_settings_dialog_get_selected_sizes_returns_list(
            self, fusion_qapp, qtbot):
        dlg = self._make_dialog(qtbot)
        sizes = dlg.get_selected_sizes()
        assert isinstance(sizes, list)
        assert all(isinstance(s, int) for s in sizes)

    def test_settings_dialog_signals_exist(self, fusion_qapp, qtbot):
        dlg = self._make_dialog(qtbot)
        # Spot-check the headline signals — these are the public API
        # the main window connects to.
        assert hasattr(dlg, "settings_changed")
        assert hasattr(dlg, "export_png_requested")
        assert hasattr(dlg, "analyze_ico_requested")
        assert hasattr(dlg, "auto_crop_requested")

    def test_settings_dialog_initial_fill_color_is_white(
            self, fusion_qapp, qtbot):
        dlg = self._make_dialog(qtbot)
        assert dlg._fill_color == (255, 255, 255, 255)

    def test_settings_dialog_initial_border_color_is_black(
            self, fusion_qapp, qtbot):
        dlg = self._make_dialog(qtbot)
        assert dlg._border_color == (0, 0, 0, 255)

    def test_settings_dialog_not_watching_initially(self, fusion_qapp, qtbot):
        dlg = self._make_dialog(qtbot)
        assert dlg._is_watching is False


# ══════════════════════════════════════════════════════════════════════════════
# 7. DIALOG HELPER — static methods, QMessageBox.exec patched
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.ui
class TestDialogHelper:

    def test_show_error_displays_title_and_message(
            self, fusion_qapp, patch_message_box):
        from utils.dialog_helper import DialogHelper

        DialogHelper.show_error(parent=None, message="Boom!", title="Crash")
        assert len(patch_message_box.calls) == 1
        title, text = patch_message_box.calls[0]
        assert title == "Crash"
        assert text == "Boom!"

    def test_show_error_uses_default_title(self, fusion_qapp,
                                            patch_message_box):
        from utils.dialog_helper import DialogHelper

        DialogHelper.show_error(parent=None, message="No title here")
        title, _ = patch_message_box.calls[0]
        # DEFAULT_ERROR_TITLE is "Error" or similar — just verify non-empty.
        assert title != ""

    def test_show_info(self, fusion_qapp, patch_message_box):
        from utils.dialog_helper import DialogHelper

        DialogHelper.show_info(parent=None, message="FYI", title="Info")
        assert ("Info", "FYI") in patch_message_box.calls

    def test_show_warning(self, fusion_qapp, patch_message_box):
        from utils.dialog_helper import DialogHelper

        DialogHelper.show_warning(parent=None, message="Careful",
                                  title="Watch out")
        assert ("Watch out", "Careful") in patch_message_box.calls

    def test_confirm_returns_true_when_yes(self, fusion_qapp,
                                            patch_message_box):
        from utils.dialog_helper import DialogHelper

        patch_message_box.set_response(QMessageBox.StandardButton.Yes)
        result = DialogHelper.confirm(parent=None, message="Sure?",
                                      title="Confirm")
        assert result is True

    def test_confirm_returns_false_when_no(self, fusion_qapp,
                                            patch_message_box):
        from utils.dialog_helper import DialogHelper

        patch_message_box.set_response(QMessageBox.StandardButton.No)
        result = DialogHelper.confirm(parent=None, message="Sure?",
                                      title="Confirm")
        assert result is False


# ══════════════════════════════════════════════════════════════════════════════
# 8. MAIN WINDOW KEYBOARD SHORTCUTS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.ui
class TestMainWindowShortcuts:
    """
    Validate that QShortcuts are wired to handlers that produce the expected
    state changes. We trigger via `shortcut.activated.emit()` rather than
    qtbot.keyClick because Qt::WindowShortcut context doesn't fire reliably
    in offscreen mode (no real focus). Phase 3 already verified the key
    sequences are registered; this phase verifies the bindings *do* something.
    """

    @staticmethod
    def _find_shortcut(app, key_sequence_str: str):
        """Return the QShortcut whose key matches, or None."""
        from PyQt6.QtGui import QShortcut
        for sc in app.findChildren(QShortcut):
            if sc.key().toString() == key_sequence_str:
                return sc
        return None

    def test_ctrl_t_cycles_theme(self, app, qtbot):
        """Activating the Ctrl+T shortcut changes the theme."""
        before = app.theme_manager.current_theme
        sc = self._find_shortcut(app, "Ctrl+T")
        assert sc is not None, "Ctrl+T shortcut not registered"
        sc.activated.emit()
        QApplication.processEvents()
        assert app.theme_manager.current_theme != before

    def test_f5_refreshes_preview(self, app, qtbot):
        """F5 → refresh_preview() → status bar shows 'Preview refreshed'."""
        sc = self._find_shortcut(app, "F5")
        assert sc is not None, "F5 shortcut not registered"
        sc.activated.emit()
        QApplication.processEvents()
        assert "refresh" in app.status_bar.currentMessage().lower()

    def test_escape_clears_selection(self, app, qtbot):
        """Esc → _clear_selection() → selected_size becomes None."""
        app.selected_size = 64  # Pretend something was selected.
        sc = self._find_shortcut(app, "Esc")
        assert sc is not None, "Esc shortcut not registered"
        sc.activated.emit()
        QApplication.processEvents()
        assert app.selected_size is None

    def test_ctrl_n_clears_files_with_autoconfirm(self, app, qtbot,
                                                    sample_png):
        """Ctrl+N → clear_files(); ErrorHandler.confirm_action is auto-True
        (patched in the conftest `app` fixture)."""
        png = sample_png(name="precleared.png", size=64)
        app.handle_files([png])
        assert len(app.image_processor.get_detected_images()) > 0

        sc = self._find_shortcut(app, "Ctrl+N")
        assert sc is not None, "Ctrl+N shortcut not registered"
        sc.activated.emit()
        QApplication.processEvents()
        assert len(app.image_processor.get_detected_images()) == 0
