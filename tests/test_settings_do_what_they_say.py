"""
SETTINGS THAT DO WHAT THEY SAY (#95 A, 24 October 2026)
========================================================

Three settings were offered and never read:

- *Restore last session on startup* and *Auto-save project periodically*
  (Settings > Auto). The handler only logged them. The project manager's
  auto_save() and save_last_session() had no caller.
- The output filename template (Settings > Export), with its live preview.
  It was stored and never used: Export PNG Set always wrote icon_{size}.png.

Each test here failed before the change. Every file the app keeps is
redirected into the test's own folder.
"""

from __future__ import annotations

import json
import os

import pytest
from PyQt6.QtWidgets import QFileDialog

import RNV_Icon_Builder

# The real startup check, taken before the `app` fixture replaces it with a
# no-op for every other test.
_REAL_CHECK_SESSION_RECOVERY = RNV_Icon_Builder.IconBuilderApp._check_session_recovery


@pytest.fixture
def kept_files(monkeypatch, tmp_dir):
    """Point settings.json, the last session and the crash-recovery files into tmp_dir."""
    from pathlib import Path
    import core.project_manager as project_module
    import core.session_manager as session_module

    base = Path(tmp_dir) / "user_data"
    base.mkdir()
    # raising=False: before #95 A the module had no settings file to point
    monkeypatch.setattr(session_module, "SETTINGS_PATH", base / "settings.json",
                        raising=False)
    monkeypatch.setattr(session_module, "SESSION_AUTO_SAVE_PATH", base / "autosave.json")
    monkeypatch.setattr(session_module, "RECOVERY_FLAG_PATH", base / ".recovery_needed")
    monkeypatch.setattr(project_module, "LAST_SESSION_PATH", base / "last_session.rnvicon")
    return base


@pytest.fixture
def quiet_dialogs(monkeypatch):
    """Record the modal dialogs instead of showing them."""
    from utils.dialog_helper import DialogHelper
    shown: dict[str, list] = {"confirm": [], "info": [], "warning": []}
    answer = {"confirm": True}
    monkeypatch.setattr(DialogHelper, "confirm", staticmethod(
        lambda parent, message, title="", **kw: shown["confirm"].append(title) or answer["confirm"]))
    monkeypatch.setattr(DialogHelper, "show_info", staticmethod(
        lambda parent, message, title="", **kw: shown["info"].append(title)))
    monkeypatch.setattr(DialogHelper, "show_warning", staticmethod(
        lambda parent, message, title="", **kw: shown["warning"].append(title)))
    shown["answer"] = answer
    return shown


def _new_window():
    """A second main window, as the next start of the app would make."""
    return RNV_Icon_Builder.IconBuilderApp()


# ══════════════════════════════════════════════════════════════════════════════
# 1. RESTORE LAST SESSION ON STARTUP
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
class TestRestoreLastSession:

    def test_the_session_settings_are_kept_for_the_next_start(self, kept_files, app):
        app._open_settings()
        app.settings_dialog.restore_session_cb.setChecked(True)
        app.settings_dialog.auto_save_cb.setChecked(False)

        stored = json.loads((kept_files / "settings.json").read_text(encoding="utf-8"))
        assert stored == {"restore_session": True, "auto_save": False}

        nxt = _new_window()
        try:
            assert nxt._restore_session_enabled is True
            assert nxt._auto_save_project_enabled is False
            nxt._open_settings()
            assert nxt.settings_dialog.get_session_settings() == {
                "restore_session": True, "auto_save": False}
        finally:
            nxt.close()

    def test_with_restore_on_the_next_start_loads_the_session_without_asking(
            self, kept_files, app, quiet_dialogs, sample_png):
        app._open_settings()
        app.settings_dialog.restore_session_cb.setChecked(True)
        large = sample_png(name="kept_256.png", size=256)
        small = sample_png(name="kept_32.png", size=32)
        app.handle_files([large, small])
        app.autofill_checkbox.setChecked(False)
        app.close()
        assert (kept_files / "last_session.rnvicon").exists()

        # The files may move or go: the session holds the images themselves.
        os.remove(small)
        nxt = _new_window()
        try:
            _REAL_CHECK_SESSION_RECOVERY(nxt)
            assert quiet_dialogs["confirm"] == [], "the restore asked first"
            assert sorted(nxt.image_processor.get_detected_images()) == [32, 256]
            assert nxt.autofill_checkbox.isChecked() is False
            assert nxt._current_project_path is None
            assert nxt.status_bar.currentMessage() == "Last session restored: 2 size(s)"
        finally:
            nxt.close()

    def test_with_restore_off_the_next_start_is_empty(self, kept_files, app,
                                                      quiet_dialogs, sample_png):
        app._open_settings()
        app.settings_dialog.restore_session_cb.setChecked(True)
        app.handle_files([sample_png(name="once_64.png", size=64)])
        app.close()
        assert (kept_files / "last_session.rnvicon").exists()

        second = _new_window()
        second._open_settings()
        second.settings_dialog.restore_session_cb.setChecked(False)
        second.close()
        assert not (kept_files / "last_session.rnvicon").exists()

        third = _new_window()
        try:
            _REAL_CHECK_SESSION_RECOVERY(third)
            assert third.image_processor.get_detected_images() == {}
        finally:
            third.close()

    @pytest.mark.parametrize("accept", [True, False])
    def test_after_a_crash_the_recovery_offer_wins(self, kept_files, app, quiet_dialogs,
                                                   sample_png, accept):
        """The last session (a 256) is kept; then a session with a 48 crashes.

        The next start offers recovery only. Accepted, the 48 comes back;
        declined, nothing does. The last session is not restored either way.
        """
        app._open_settings()
        app.settings_dialog.restore_session_cb.setChecked(True)
        app.handle_files([sample_png(name="clean_256.png", size=256)])
        app.close()

        crashed = _new_window()
        crashed.handle_files([sample_png(name="crashed_48.png", size=48)])
        crashed.session_manager.save_session(crashed._get_session_state(), async_write=False)
        (kept_files / ".recovery_needed").write_text("1", encoding="utf-8")
        # No closeEvent: the process died. (The window is dropped untidily.)
        crashed.deleteLater()

        quiet_dialogs["answer"]["confirm"] = accept
        nxt = _new_window()
        try:
            _REAL_CHECK_SESSION_RECOVERY(nxt)
            assert quiet_dialogs["confirm"] == ["Recover Session"]
            expected = [48] if accept else []
            assert sorted(nxt.image_processor.get_detected_images()) == expected
        finally:
            nxt.close()

    def test_a_clean_close_leaves_no_session_to_recover(self, qapp, kept_files):
        """The session auto-save outlived a clean close, and the next start's
        start_auto_save() set the recovery flag again before the check ran, so
        a normal close was offered for recovery like a crash."""
        from core.session_manager import SessionManager, SessionState
        first = SessionManager()
        first.start_auto_save(interval_ms=60_000)
        first.save_session(SessionState(loaded_files=["/x/a.png"]), async_write=False)
        first.on_clean_shutdown()

        second = SessionManager()
        second.start_auto_save(interval_ms=60_000)
        try:
            assert second.has_recovery() is False
        finally:
            second.stop_auto_save()


# ══════════════════════════════════════════════════════════════════════════════
# 2. AUTO-SAVE PROJECT PERIODICALLY
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
class TestAutoSaveProject:

    def test_a_saved_project_that_changed_is_auto_saved_to_its_file(
            self, kept_files, app, sample_png, tmp_dir):
        from core.project_manager import ProjectManager
        app.handle_files([sample_png(name="p_256.png", size=256)])
        path = os.path.join(tmp_dir, "work.rnvicon")
        app._save_project_to_path(path)

        assert app._auto_save_project() is False, "an unchanged project was written again"

        app.handle_files([sample_png(name="p_32.png", size=32)])
        assert app._auto_save_project() is True
        assert sorted(ProjectManager().load_project(path).images) == [32, 256]
        assert app.status_bar.currentMessage() == "Project auto-saved: work.rnvicon"
        assert not [n for n in os.listdir(tmp_dir) if n.endswith(".tmp")]

    def test_a_project_never_saved_is_not_auto_saved(self, kept_files, app, sample_png,
                                                     tmp_dir):
        before = set(os.listdir(tmp_dir)) | set(os.listdir(kept_files))
        app.handle_files([sample_png(name="u_64.png", size=64)])
        written = before | {"u_64.png"}
        assert app._current_project_path is None
        assert app._auto_save_project() is False
        assert set(os.listdir(tmp_dir)) | set(os.listdir(kept_files)) == written

    def test_the_setting_starts_and_stops_the_timer_on_the_session_interval(
            self, kept_files, app, sample_png, tmp_dir):
        from utils.config import AUTO_SAVE_INTERVAL_SECONDS
        app._open_settings()
        app.settings_dialog.auto_save_cb.setChecked(False)
        app.settings_dialog.auto_save_cb.setChecked(True)
        assert app._project_auto_save_timer.isActive()
        assert app._project_auto_save_timer.interval() == AUTO_SAVE_INTERVAL_SECONDS * 1000

        app.settings_dialog.auto_save_cb.setChecked(False)
        assert not app._project_auto_save_timer.isActive()
        app.handle_files([sample_png(name="off_64.png", size=64)])
        app._save_project_to_path(os.path.join(tmp_dir, "off.rnvicon"))
        app.handle_files([sample_png(name="off_32.png", size=32)])
        assert app._auto_save_project() is False, "auto-save ran while switched off"


# ══════════════════════════════════════════════════════════════════════════════
# 3. THE OUTPUT FILENAME TEMPLATE
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
class TestFilenameTemplate:

    @staticmethod
    def _export(app, monkeypatch, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        monkeypatch.setattr(QFileDialog, "getExistingDirectory",
                            staticmethod(lambda *a, **kw: out_dir))
        app.export_png_set()
        return sorted(os.listdir(out_dir))

    def test_png_set_files_are_named_by_the_template(self, app, monkeypatch, quiet_dialogs,
                                                     sample_png, tmp_dir):
        app.handle_files([sample_png(name="logo.png", size=256)])
        app._open_settings()
        app.settings_dialog.template_input.setText("{name}-{size}px")

        written = self._export(app, monkeypatch, os.path.join(tmp_dir, "out"))
        assert written == sorted(f"logo-{s}px.png" for s in (256, 128, 64, 48, 32, 16))
        assert app.settings_dialog.template_preview.text() == "Preview: logo-256px.png"

    def test_the_default_template_keeps_the_old_names(self, app, monkeypatch, quiet_dialogs,
                                                      sample_png, tmp_dir):
        app.handle_files([sample_png(name="logo.png", size=256)])
        written = self._export(app, monkeypatch, os.path.join(tmp_dir, "out"))
        assert written == sorted(f"icon_{s}.png" for s in (256, 128, 64, 48, 32, 16))

    def test_unsafe_characters_and_a_template_without_size_still_export(
            self, app, monkeypatch, quiet_dialogs, sample_png, tmp_dir):
        app.handle_files([sample_png(name="logo.png", size=256)])
        app._open_settings()
        app.settings_dialog.template_input.setText('../a/b:c*?"<>|\x00\t')

        out_dir = os.path.join(tmp_dir, "out")
        written = self._export(app, monkeypatch, out_dir)
        # Six files, one per size, all inside the folder chosen
        assert len(written) == 6
        assert all(os.path.isfile(os.path.join(out_dir, n)) for n in written)
        assert set(os.listdir(tmp_dir)) == {"logo.png", "out"}
        assert "_b_c" in written[0] and written[0].endswith(".png")
