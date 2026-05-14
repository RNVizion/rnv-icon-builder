"""
RNV Icon Builder — Phase 7 Snapshot Tests
==========================================

Locks output formats against accidental drift. Each test regenerates a
known-good output (stylesheet text, dict shape, ICO bytes) and compares
to a reference stored in tests/snapshots.json.

When a snapshot test fails, the question to ask is:
  - Did I intentionally change this output? → regenerate the snapshot
  - Did I unintentionally change it?         → fix the regression

This phase doesn't add coverage lines (those paths are exercised by other
phases). Its value is in catching format/schema drift that no other test
would notice — e.g. someone adds a field to BatchJob.to_dict() without
updating the loader, or someone tweaks a stylesheet color without
realizing other widgets read that exact string.

Snapshots covered:
  - Scrollbar stylesheets for dark / light / image-mode themes
  - Theme color dictionary key sets (DARK / LIGHT / IMAGE_MODE)
  - Serialization shape: BatchJob, SizePreset, WatchSettings,
    SessionState, Project, ProjectSettings (top-level keys only)
  - ICO file structure for a known input (size count + parsed sizes)
  - ICO header bytes for the same known input

Regenerating snapshots:
  When you change something on purpose, regenerate by deleting the relevant
  key in tests/snapshots.json and running the bundled regeneration helper
  in this file's __main__ block:
      python tests/test_snapshots.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest


SNAPSHOT_PATH = Path(__file__).parent / "snapshots.json"


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def snapshots() -> dict:
    """Load the snapshot reference file once per test session."""
    if not SNAPSHOT_PATH.exists():
        pytest.fail(
            f"Snapshot file missing: {SNAPSHOT_PATH}. "
            "Run `python tests/test_snapshots.py` to regenerate.")
    with open(SNAPSHOT_PATH, encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════════════════════
# 1. SCROLLBAR STYLESHEETS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.snapshot
class TestScrollbarSnapshots:
    """The scrollbar stylesheet is generated from theme dictionaries; if any
    color value or property changes, this catches it character-for-character."""

    def test_scrollbar_dark(self, snapshots, fusion_qapp_or_qapp):
        from ui.theme_manager import ThemeManager

        tm = ThemeManager()
        tm.current_theme = "dark"
        assert tm.get_scrollbar_style() == snapshots["scrollbar_dark"]

    def test_scrollbar_light(self, snapshots, fusion_qapp_or_qapp):
        from ui.theme_manager import ThemeManager

        tm = ThemeManager()
        tm.current_theme = "light"
        assert tm.get_scrollbar_style() == snapshots["scrollbar_light"]

    def test_scrollbar_image_mode(self, snapshots, fusion_qapp_or_qapp):
        from ui.theme_manager import ThemeManager

        tm = ThemeManager()
        tm.current_theme = "image"
        assert tm.get_scrollbar_style() == snapshots["scrollbar_image"]


# ══════════════════════════════════════════════════════════════════════════════
# 2. THEME COLOR DICTIONARY KEY SETS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.snapshot
class TestThemeKeySnapshots:
    """Locks the *names* of color slots in each theme dict. If anyone adds,
    removes, or renames a slot, every theme that defines colors must do the
    same — these snapshots make that mismatch visible."""

    def test_dark_theme_keys(self, snapshots):
        from ui.colors import DARK_THEME_COLORS

        assert sorted(DARK_THEME_COLORS.keys()) == snapshots["dark_theme_keys"]

    def test_light_theme_keys(self, snapshots):
        from ui.colors import LIGHT_THEME_COLORS

        assert sorted(LIGHT_THEME_COLORS.keys()) == \
            snapshots["light_theme_keys"]

    def test_image_mode_keys(self, snapshots):
        from ui.colors import IMAGE_MODE_COLORS

        assert sorted(IMAGE_MODE_COLORS.keys()) == snapshots["image_mode_keys"]


# ══════════════════════════════════════════════════════════════════════════════
# 3. SERIALIZATION SHAPE — to_dict() KEY SETS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.snapshot
class TestSerializationShapeSnapshots:
    """If anyone adds a field to to_dict() without updating from_dict() —
    or vice versa — the data round-trip silently drops information. These
    snapshots make schema drift impossible to ignore."""

    def test_batchjob_dict_keys(self, snapshots):
        from core.batch_processor import BatchJob

        keys = sorted(BatchJob(source_path="/x",
                               output_path="/y").to_dict().keys())
        assert keys == snapshots["batchjob_keys"]

    def test_sizepreset_dict_keys(self, snapshots):
        from core.preset_manager import SizePreset

        keys = sorted(SizePreset(name="X", sizes=[64]).to_dict().keys())
        assert keys == snapshots["sizepreset_keys"]

    def test_watchsettings_dict_keys(self, snapshots):
        from core.folder_watcher import WatchSettings

        keys = sorted(WatchSettings(input_folder="/i",
                                    output_folder="/o").to_dict().keys())
        assert keys == snapshots["watchsettings_keys"]

    def test_sessionstate_dict_keys(self, snapshots):
        from core.session_manager import SessionState

        state = SessionState(
            loaded_files=[], selected_sizes=[],
            autofill_enabled=True, png_compression=True,
            current_project_path="",
            window_geometry={"x": 0, "y": 0, "width": 800, "height": 600},
        )
        assert sorted(state.to_dict().keys()) == \
            snapshots["sessionstate_keys"]

    def test_project_dict_keys(self, snapshots):
        from core.project_manager import Project

        proj = Project(name="X")
        assert sorted(proj.to_dict().keys()) == snapshots["project_keys"]

    def test_project_settings_dict_keys(self, snapshots):
        from core.project_manager import Project

        proj = Project(name="X")
        assert sorted(proj.settings.to_dict().keys()) == \
            snapshots["project_settings_keys"]


# ══════════════════════════════════════════════════════════════════════════════
# 4. ICO FILE STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.snapshot
class TestIcoStructureSnapshots:
    """The body of an ICO file is variable (PNG compression, timestamps),
    but its header and parsed structure are deterministic for a given input.
    This catches changes to the build pipeline like 'autofill default
    flipped from True to False' that would otherwise pass silently."""

    def test_ico_structure_for_known_input(self, snapshots, sample_rgba,
                                            tmp_dir):
        """Fixed input {64, 32} → fixed parsed structure (autofill kicks in
        and adds standard sizes; the snapshot captures *which* sizes)."""
        from core.icon_builder_core import IconBuilderCore

        images = {
            64: sample_rgba(64, 64, (255, 0, 0, 255)),
            32: sample_rgba(32, 32, (0, 255, 0, 255)),
        }
        ico_path = os.path.join(tmp_dir, "snapshot_check.ico")
        IconBuilderCore.build_ico_file(images, ico_path)
        info = IconBuilderCore.verify_ico_file(ico_path)

        actual = {"count": info["count"], "sizes": sorted(info["sizes"])}
        assert actual == snapshots["ico_structure_64_32"]

    def test_ico_header_bytes_for_known_input(self, snapshots, sample_rgba,
                                               tmp_dir):
        """First 6 bytes of an ICO are: reserved (0), type (1=ICO),
        count. For a 4-image ICO this is `00 00 01 00 04 00`."""
        from core.icon_builder_core import IconBuilderCore

        images = {
            64: sample_rgba(64, 64, (255, 0, 0, 255)),
            32: sample_rgba(32, 32, (0, 255, 0, 255)),
        }
        ico_path = os.path.join(tmp_dir, "header_check.ico")
        IconBuilderCore.build_ico_file(images, ico_path)

        with open(ico_path, "rb") as f:
            header_hex = f.read(6).hex()
        assert header_hex == snapshots["ico_header_2img_hex"]


# ══════════════════════════════════════════════════════════════════════════════
# Helper fixture — some tests need a QApplication, others don't.
# We tolerate either Fusion or default style; tests in this file only read
# theme/serialization output, none of which depend on widget palette.
# ══════════════════════════════════════════════════════════════════════════════
@pytest.fixture
def fusion_qapp_or_qapp(qapp):
    """Pass-through fixture so tests document the qapp dependency without
    forcing Fusion. Theme stylesheets are pure string output and don't
    require a styled QApplication."""
    return qapp


# ══════════════════════════════════════════════════════════════════════════════
# REGENERATION HELPER — run as `python tests/test_snapshots.py` to refresh
# ══════════════════════════════════════════════════════════════════════════════
def regenerate_snapshots() -> dict:
    """
    Build the canonical snapshot dict from the current code. Used both for
    the original generation and for intentional refresh after a real change.
    """
    # Bootstrap the same way conftest does, in case this is run standalone.
    here = Path(__file__).resolve()
    project_root = here.parent.parent
    sys.path.insert(0, str(project_root))

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    if QApplication.instance() is None:
        QApplication(sys.argv[:1])

    from ui.theme_manager import ThemeManager
    from ui.colors import (DARK_THEME_COLORS, LIGHT_THEME_COLORS,
                            IMAGE_MODE_COLORS)
    from core.batch_processor import BatchJob
    from core.preset_manager import SizePreset
    from core.folder_watcher import WatchSettings
    from core.session_manager import SessionState
    from core.project_manager import Project
    from core.icon_builder_core import IconBuilderCore
    from PIL import Image

    snap: dict = {}

    tm = ThemeManager()
    tm.current_theme = "dark"
    snap["scrollbar_dark"] = tm.get_scrollbar_style()
    tm.current_theme = "light"
    snap["scrollbar_light"] = tm.get_scrollbar_style()
    tm.current_theme = "image"
    snap["scrollbar_image"] = tm.get_scrollbar_style()

    snap["dark_theme_keys"] = sorted(DARK_THEME_COLORS.keys())
    snap["light_theme_keys"] = sorted(LIGHT_THEME_COLORS.keys())
    snap["image_mode_keys"] = sorted(IMAGE_MODE_COLORS.keys())

    snap["batchjob_keys"] = sorted(
        BatchJob(source_path="/x", output_path="/y").to_dict().keys())
    snap["sizepreset_keys"] = sorted(
        SizePreset(name="X", sizes=[64]).to_dict().keys())
    snap["watchsettings_keys"] = sorted(
        WatchSettings(input_folder="/i", output_folder="/o").to_dict().keys())

    state = SessionState(
        loaded_files=[], selected_sizes=[],
        autofill_enabled=True, png_compression=True,
        current_project_path="",
        window_geometry={"x": 0, "y": 0, "width": 800, "height": 600},
    )
    snap["sessionstate_keys"] = sorted(state.to_dict().keys())

    proj = Project(name="X")
    snap["project_keys"] = sorted(proj.to_dict().keys())
    snap["project_settings_keys"] = sorted(proj.settings.to_dict().keys())

    images = {
        64: Image.new("RGBA", (64, 64), (255, 0, 0, 255)),
        32: Image.new("RGBA", (32, 32), (0, 255, 0, 255)),
    }
    _, ico_path = tempfile.mkstemp(suffix=".ico")
    try:
        IconBuilderCore.build_ico_file(images, ico_path)
        info = IconBuilderCore.verify_ico_file(ico_path)
        snap["ico_structure_64_32"] = {
            "count": info["count"], "sizes": sorted(info["sizes"]),
        }
        with open(ico_path, "rb") as f:
            snap["ico_header_2img_hex"] = f.read(6).hex()
    finally:
        os.unlink(ico_path)

    return snap


if __name__ == "__main__":
    snap = regenerate_snapshots()
    SNAPSHOT_PATH.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    print(f"Wrote {len(snap)} snapshots → {SNAPSHOT_PATH}")
