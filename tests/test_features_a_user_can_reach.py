"""
FEATURES A USER CAN REACH (#96 A, 24 October 2026)
==================================================

Two features were in the code and out of every user's reach:

- MetadataPanel, exported by ui/__init__.py and never created. It now sits
  beside the thumbnails and shows the details of the size clicked in the
  thumbnails or the size list, the largest loaded size by default.
- A folder dropped on the window: handle_files() skipped a path with no
  image extension, so nothing loaded. A dropped folder now loads its images
  as Select Folder does, honoring "Scan subfolders when selecting folder".

The third, the .rnvicon project auto-save and session restore that nothing
called, is wired by #95 A (tests/test_settings_do_what_they_say.py); the last
test here holds that none of that code is left without a caller.

Each test here failed before the change.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from PyQt6.QtCore import QMimeData, QPointF, Qt, QUrl
from PyQt6.QtGui import QDropEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QLabel

ROOT = Path(__file__).resolve().parent.parent


def _panel_rows(app) -> dict[str, str]:
    """The metadata panel's visible label: value rows."""
    from ui.metadata_panel import MetadataPanel
    panel = app.findChild(MetadataPanel)
    assert panel is not None, "the main window has no metadata panel"
    rows: dict[str, str] = {}
    for grid in (panel.file_grid, panel.image_grid):
        for i in range(0, grid.count() - 1, 2):
            label, value = grid.itemAt(i).widget(), grid.itemAt(i + 1).widget()
            if isinstance(label, QLabel) and isinstance(value, QLabel):
                rows[label.text().rstrip(":")] = value.text()
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# 4. THE METADATA PANEL
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
class TestMetadataPanel:

    def test_the_panel_shows_the_largest_size_then_the_one_clicked(self, app, sample_png):
        assert _panel_rows(app) == {"Status": "No images loaded"}

        app.handle_files([sample_png(name="big_256.png", size=256),
                          sample_png(name="small_32.png", size=32)])
        rows = _panel_rows(app)
        assert rows["Name"] == "big_256.png"
        assert rows["Size Slot"] == "256x256"
        assert rows["Dimensions"] == "256 × 256 px"

        QTest.mouseClick(app.thumbnail_widgets[32], Qt.MouseButton.LeftButton)
        rows = _panel_rows(app)
        assert rows["Name"] == "small_32.png"
        assert rows["Size Slot"] == "32x32"
        assert app.file_listbox.currentRow() == 4, "the size list did not follow"

    def test_a_row_of_the_size_list_selects_too(self, app, sample_png):
        app.handle_files([sample_png(name="big_256.png", size=256)])
        app.file_listbox.setCurrentRow(2)  # 64x64, autofilled
        rows = _panel_rows(app)
        assert rows["Source"] == "In-memory image"
        assert rows["Size Slot"] == "64x64"


# ══════════════════════════════════════════════════════════════════════════════
# 5. A FOLDER DROPPED ON THE WINDOW
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.application
class TestFolderDrop:

    @staticmethod
    def _drop(app, *paths: str) -> None:
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(p) for p in paths])
        app.dropEvent(QDropEvent(QPointF(0, 0), Qt.DropAction.CopyAction, mime,
                                 Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))

    @staticmethod
    def _folder(tmp_dir, sample_rgba) -> str:
        folder = os.path.join(tmp_dir, "icons")
        os.makedirs(os.path.join(folder, "sub"))
        sample_rgba(256, 256).save(os.path.join(folder, "app_256.png"))
        sample_rgba(48, 48).save(os.path.join(folder, "app_48.png"))
        sample_rgba(16, 16).save(os.path.join(folder, "sub", "app_16.png"))
        with open(os.path.join(folder, "notes.txt"), "w", encoding="utf-8") as f:
            f.write("not an image")
        return folder

    @pytest.mark.parametrize("subfolders, expected", [(True, [16, 48, 256]),
                                                      (False, [48, 256])])
    def test_a_dropped_folder_loads_its_images(self, app, tmp_dir, sample_rgba,
                                               subfolders, expected):
        folder = self._folder(tmp_dir, sample_rgba)
        app.recursive_checkbox.setChecked(subfolders)
        self._drop(app, folder)
        assert sorted(app.image_processor.get_detected_images()) == expected

    def test_a_folder_dropped_with_a_file_loads_both(self, app, tmp_dir, sample_rgba,
                                                     sample_png):
        folder = self._folder(tmp_dir, sample_rgba)
        self._drop(app, folder, sample_png(name="loose_128.png", size=128))
        assert sorted(app.image_processor.get_detected_images()) == [16, 48, 128, 256]

    def test_a_folder_with_no_images_says_so(self, app, tmp_dir, monkeypatch):
        from utils.dialog_helper import DialogHelper
        warned: list[str] = []
        monkeypatch.setattr(DialogHelper, "show_warning", staticmethod(
            lambda parent, message, title="", **kw: warned.append(title)))
        empty = os.path.join(tmp_dir, "empty")
        os.mkdir(empty)
        self._drop(app, empty)
        assert warned == ["No Files"]
        assert app.status_bar.currentMessage() == "No valid files found in folder"


# ══════════════════════════════════════════════════════════════════════════════
# 6. NO PROJECT AUTO-SAVE OR SESSION CODE LEFT WITHOUT A CALLER
# ══════════════════════════════════════════════════════════════════════════════
def test_the_project_auto_save_and_last_session_code_is_called():
    """Each of the project manager's auto-save and last-session methods, and the
    main window's restore methods, is called from the application's code."""
    source = (ROOT / "RNV_Icon_Builder.py").read_text(encoding="utf-8")
    for name in ("auto_save", "save_last_session", "load_last_session",
                 "has_last_session", "clear_last_session",
                 "_check_session_restore", "_restore_last_session"):
        assert re.search(rf"\.{name}\(", source), f"{name}() has no caller"
    project_manager = (ROOT / "core" / "project_manager.py").read_text(encoding="utf-8")
    for gone in ("def load_auto_save", "def clear_auto_save"):
        assert gone not in project_manager, f"{gone}: nothing writes the file it reads"
