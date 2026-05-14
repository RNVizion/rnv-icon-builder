"""
RNV Icon Builder — Folder Watcher Tests
========================================

Phase 10A coverage push for folder_watcher.py (currently 46%).

Targets _process_file (the actual ICO build path), the _is_valid_image
gate, and process_file_manually's happy path. Together these cover
~half of what's currently uncovered.

Tests use real PNG files and real ICO output to exercise the genuine
pipeline rather than mocking out the work.
"""

from __future__ import annotations

import os
import pytest


def _make_watcher_with_settings(tmp_dir, sample_png):
    """Helper: build a watcher with valid settings and pre-create dirs."""
    from core.folder_watcher import FolderWatcher, WatchSettings

    in_dir = os.path.join(tmp_dir, "watch_in")
    out_dir = os.path.join(tmp_dir, "watch_out")
    os.makedirs(in_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    fw = FolderWatcher()
    fw.start_watching(WatchSettings(
        input_folder=in_dir, output_folder=out_dir,
        sizes=[64, 32], autofill=False, png_compression=True,
        overwrite_existing=True, delete_source=False,
    ))
    return fw, in_dir, out_dir


# ══════════════════════════════════════════════════════════════════════════════
# 1. _is_valid_image
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.worker
class TestFolderWatcherIsValidImage:

    def test_valid_png_returns_true(self, qapp, tmp_dir, sample_png):
        from core.folder_watcher import FolderWatcher

        fw = FolderWatcher()
        png = sample_png(name="image.png")
        assert fw._is_valid_image(png) is True

    def test_text_file_returns_false(self, qapp, tmp_dir):
        from core.folder_watcher import FolderWatcher
        from pathlib import Path

        fw = FolderWatcher()
        txt = os.path.join(tmp_dir, "not_an_image.txt")
        Path(txt).write_text("hi")
        assert fw._is_valid_image(txt) is False


# ══════════════════════════════════════════════════════════════════════════════
# 2. _process_file — the real ICO build pipeline
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.worker
class TestFolderWatcherProcessFile:

    def test_process_file_no_settings_returns_false(self, qapp, sample_png):
        """Without start_watching first, _process_file refuses."""
        from core.folder_watcher import FolderWatcher

        fw = FolderWatcher()
        result = fw._process_file(sample_png(name="orphan.png"))
        assert result is False

    def test_process_file_already_processed_short_circuits(
            self, qapp, tmp_dir, sample_png, qtbot):
        """A file already in _processed_files set returns True without rebuilding."""
        fw, in_dir, _ = _make_watcher_with_settings(tmp_dir, sample_png)
        try:
            from PIL import Image
            png_path = os.path.join(in_dir, "already_done.png")
            Image.new("RGBA", (64, 64), (200, 100, 50, 255)).save(png_path)

            fw._processed_files.add(os.path.abspath(png_path))
            result = fw._process_file(png_path)
            assert result is True
        finally:
            fw.stop_watching()

    def test_process_file_missing_source_returns_false(
            self, qapp, tmp_dir, sample_png):
        """Source file deleted between detection and processing."""
        fw, _, _ = _make_watcher_with_settings(tmp_dir, sample_png)
        try:
            result = fw._process_file("/no/such/source.png")
            assert result is False
        finally:
            fw.stop_watching()

    def test_process_file_real_png_builds_ico(
            self, qapp, tmp_dir, sample_png, qtbot):
        """End-to-end: drop a PNG in input dir, _process_file produces ICO."""
        fw, in_dir, out_dir = _make_watcher_with_settings(tmp_dir, sample_png)
        try:
            from PIL import Image
            png_path = os.path.join(in_dir, "real.png")
            Image.new("RGBA", (64, 64), (200, 100, 50, 255)).save(png_path)

            with qtbot.waitSignal(fw.file_processed, timeout=10_000):
                result = fw._process_file(png_path)

            assert result is True
            expected_ico = os.path.join(out_dir, "real.ico")
            assert os.path.exists(expected_ico)
        finally:
            fw.stop_watching()

    def test_process_file_unsupported_extension_returns_false(
            self, qapp, tmp_dir, sample_png):
        """An .xyz file slips past the gate but _process_file rejects it."""
        from pathlib import Path

        fw, in_dir, _ = _make_watcher_with_settings(tmp_dir, sample_png)
        try:
            xyz_path = os.path.join(in_dir, "fake.xyz")
            Path(xyz_path).write_bytes(b"\x89PNG\r\n\x1a\n")  # Valid header.

            result = fw._process_file(xyz_path)
            assert result is False
        finally:
            fw.stop_watching()


# ══════════════════════════════════════════════════════════════════════════════
# 3. process_file_manually — public API for "process this file now"
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.worker
class TestProcessFileManually:

    def test_process_file_manually_with_no_settings_returns_false(
            self, qapp):
        from core.folder_watcher import FolderWatcher

        fw = FolderWatcher()
        result = fw.process_file_manually("/whatever.png")
        assert result is False

    def test_process_file_manually_real_file_succeeds(
            self, qapp, tmp_dir, sample_png, qtbot):
        """The public "process now" path produces a real ICO."""
        fw, in_dir, out_dir = _make_watcher_with_settings(tmp_dir, sample_png)
        try:
            from PIL import Image
            png_path = os.path.join(in_dir, "manual.png")
            Image.new("RGBA", (64, 64), (50, 100, 200, 255)).save(png_path)

            with qtbot.waitSignal(fw.file_processed, timeout=10_000):
                result = fw.process_file_manually(png_path)

            assert result is True
            assert os.path.exists(os.path.join(out_dir, "manual.ico"))
        finally:
            fw.stop_watching()


# ══════════════════════════════════════════════════════════════════════════════
# 4. Settings accessors
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.worker
class TestWatcherAccessors:

    def test_get_processed_count_returns_int(self, qapp):
        from core.folder_watcher import FolderWatcher

        fw = FolderWatcher()
        assert fw.get_processed_count() == 0

    def test_processed_count_increments_after_processing(
            self, qapp, tmp_dir, sample_png, qtbot):
        fw, in_dir, _ = _make_watcher_with_settings(tmp_dir, sample_png)
        try:
            from PIL import Image
            png_path = os.path.join(in_dir, "count_me.png")
            Image.new("RGBA", (64, 64), (1, 2, 3, 255)).save(png_path)

            before = fw.get_processed_count()
            with qtbot.waitSignal(fw.file_processed, timeout=10_000):
                fw._process_file(png_path)
            after = fw.get_processed_count()
            assert after == before + 1
        finally:
            fw.stop_watching()
