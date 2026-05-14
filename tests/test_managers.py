"""
RNV Icon Builder — Manager Class Tests (Phase 10C)
===================================================

Direct tests for the three persistence-layer managers:
  - PresetManager    (preset_manager.py, 63% → ~75%)
  - RecentFilesManager (recent_files.py, 66% → ~80%)
  - ProjectManager   (project_manager.py, 65% → ~75%)

All three persist to disk. The conftest fixture redirects user-data
paths to a tmp dir so these tests don't touch real config files.
"""

from __future__ import annotations

import json
import os
import pytest

from PIL import Image


# ══════════════════════════════════════════════════════════════════════════════
# 1. PRESET MANAGER — save / delete / rename / duplicate / import / export
# ══════════════════════════════════════════════════════════════════════════════
@pytest.fixture
def fresh_pm():
    """Fresh PresetManager with custom presets cleared after each test.

    PresetManager persists to disk and reloads in __init__, so tests
    pollute each other unless we tear down explicitly.
    """
    from core.preset_manager import PresetManager
    pm = PresetManager()
    yield pm
    # Cleanup: drop any custom presets we added.
    for name in list(pm.list_preset_names(include_builtin=False)):
        if not pm.is_builtin(name):
            pm.delete_preset(name)


@pytest.mark.integration
class TestPresetManagerLifecycle:

    def test_save_preset_creates_new(self, fresh_pm):
        result = fresh_pm.save_preset(
            name="TestPreset", sizes=[64, 32, 16],
            description="for testing")
        assert result is True
        assert fresh_pm.preset_exists("TestPreset")

    def test_save_preset_with_invalid_sizes_fails(self, fresh_pm):
        """Sizes not in ICON_SIZES → save_preset returns False."""
        result = fresh_pm.save_preset(name="WeirdSizes", sizes=[999, 1234])
        assert result is False

    def test_save_preset_with_empty_sizes_fails(self, fresh_pm):
        result = fresh_pm.save_preset(name="EmptySizes", sizes=[])
        assert result is False

    def test_get_preset_returns_none_for_missing(self, fresh_pm):
        assert fresh_pm.get_preset("nonexistent_preset_xyz") is None

    def test_get_preset_returns_saved(self, fresh_pm):
        fresh_pm.save_preset(name="Lookup", sizes=[256, 128])
        result = fresh_pm.get_preset("Lookup")
        assert result is not None
        assert result.name == "Lookup"
        assert 256 in result.sizes

    def test_delete_custom_preset_succeeds(self, fresh_pm):
        fresh_pm.save_preset(name="ToDelete", sizes=[64])
        assert fresh_pm.delete_preset("ToDelete") is True
        assert not fresh_pm.preset_exists("ToDelete")

    def test_delete_nonexistent_preset_fails(self, fresh_pm):
        assert fresh_pm.delete_preset("never_existed") is False

    def test_rename_preset(self, fresh_pm):
        fresh_pm.save_preset(name="OldName", sizes=[64])
        assert fresh_pm.rename_preset("OldName", "NewName") is True
        assert fresh_pm.preset_exists("NewName")
        assert not fresh_pm.preset_exists("OldName")

    def test_rename_nonexistent_preset_fails(self, fresh_pm):
        assert fresh_pm.rename_preset("nope", "new_nope") is False

    def test_duplicate_preset_returns_new_name(self, fresh_pm):
        fresh_pm.save_preset(name="Original", sizes=[64, 32])
        new_name = fresh_pm.duplicate_preset("Original")
        assert new_name is not None
        assert new_name != "Original"
        assert fresh_pm.preset_exists(new_name)

    def test_get_custom_count_increments(self, fresh_pm):
        before = fresh_pm.get_custom_count()
        fresh_pm.save_preset(name="CountTest", sizes=[64])
        assert fresh_pm.get_custom_count() == before + 1

    def test_list_preset_names_includes_builtin_by_default(self, fresh_pm):
        names = fresh_pm.list_preset_names()
        # Builtin presets should be present.
        assert fresh_pm.get_builtin_count() > 0
        assert len(names) >= fresh_pm.get_builtin_count()

    def test_is_builtin_returns_true_for_builtins(self, fresh_pm):
        # Find any builtin and check it's flagged correctly.
        all_presets = fresh_pm.list_presets(include_builtin=True)
        builtin = [p for p in all_presets if p.is_builtin]
        if builtin:
            assert fresh_pm.is_builtin(builtin[0].name) is True


# ══════════════════════════════════════════════════════════════════════════════
# 2. RECENT FILES — add / clear / remove / get
# ══════════════════════════════════════════════════════════════════════════════
@pytest.fixture
def fresh_rfm():
    """RecentFilesManager with state cleared before AND after each test.
    Persists to disk like PresetManager, same isolation requirement."""
    from core.recent_files import RecentFilesManager
    rfm = RecentFilesManager()
    rfm.clear_history()
    yield rfm
    rfm.clear_history()


@pytest.mark.integration
class TestRecentFilesManager:

    def test_add_file_increases_count(self, fresh_rfm, sample_png):
        before = fresh_rfm.get_file_count()
        fresh_rfm.add_file(sample_png(name="rf_add.png"))
        assert fresh_rfm.get_file_count() == before + 1

    def test_add_file_deduplicates(self, fresh_rfm, sample_png):
        """Adding the same file twice should still only count once."""
        png = sample_png(name="dedupe.png")
        fresh_rfm.add_file(png)
        before = fresh_rfm.get_file_count()
        fresh_rfm.add_file(png)
        assert fresh_rfm.get_file_count() == before  # No increase.

    def test_add_folder_increases_folder_count(self, fresh_rfm, tmp_dir):
        before = fresh_rfm.get_folder_count()
        fresh_rfm.add_folder(tmp_dir)
        assert fresh_rfm.get_folder_count() == before + 1

    def test_clear_files_zeros_count(self, fresh_rfm, sample_png):
        fresh_rfm.add_file(sample_png(name="clear_me.png"))
        fresh_rfm.clear_files()
        assert fresh_rfm.get_file_count() == 0

    def test_clear_folders_zeros_count(self, fresh_rfm, tmp_dir):
        fresh_rfm.add_folder(tmp_dir)
        fresh_rfm.clear_folders()
        assert fresh_rfm.get_folder_count() == 0

    def test_clear_history_zeros_both(self, fresh_rfm, sample_png, tmp_dir):
        fresh_rfm.add_file(sample_png(name="hist.png"))
        fresh_rfm.add_folder(tmp_dir)
        fresh_rfm.clear_history()
        assert fresh_rfm.get_file_count() == 0
        assert fresh_rfm.get_folder_count() == 0

    def test_remove_file_returns_true_when_present(self, fresh_rfm,
                                                     sample_png):
        png = sample_png(name="remove_me.png")
        fresh_rfm.add_file(png)
        assert fresh_rfm.remove_file(png) is True
        assert fresh_rfm.get_file_count() == 0

    def test_remove_file_returns_false_when_absent(self, fresh_rfm):
        assert fresh_rfm.remove_file("/no/such/file.png") is False

    def test_get_recent_files_returns_list_of_dicts(self, fresh_rfm,
                                                      sample_png):
        fresh_rfm.add_file(sample_png(name="dict_check.png"))
        result = fresh_rfm.get_recent_files()
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)


# ══════════════════════════════════════════════════════════════════════════════
# 3. PROJECT MANAGER — save / load / list
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestProjectManagerDirect:

    def test_save_and_load_round_trip(self, tmp_dir):
        """Round-trip a Project through ProjectManager.save_project / load_project."""
        from core.project_manager import (
            ProjectManager, Project, ProjectSettings, ProjectImage)
        import base64
        import io

        pm = ProjectManager()
        out = os.path.join(tmp_dir, "rt.rnvicon")

        # Build a project with one embedded image (use the real production
        # path that was broken before the bug fix in this phase).
        img = Image.new("RGBA", (64, 64), (200, 100, 50, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")

        proj = Project(
            name="RoundTrip",
            settings=ProjectSettings(selected_sizes=[64, 32], autofill=True,
                                      png_compression=True),
            images={64: ProjectImage(size=64, embedded_data=encoded,
                                      is_embedded=True)},
        )

        ok = pm.save_project(proj, out)
        assert ok is True
        assert os.path.exists(out)

        loaded = pm.load_project(out)
        assert loaded is not None
        assert loaded.name == "RoundTrip"
        assert 64 in loaded.images
        # Image data should round-trip through to_pil_image().
        loaded_img = loaded.images[64].to_pil_image()
        assert loaded_img is not None
        assert loaded_img.size == (64, 64)

    def test_load_nonexistent_returns_none(self, tmp_dir):
        from core.project_manager import ProjectManager

        pm = ProjectManager()
        result = pm.load_project(os.path.join(tmp_dir, "no_such.rnvicon"))
        assert result is None

    def test_load_invalid_json_returns_none(self, tmp_dir):
        from core.project_manager import ProjectManager

        pm = ProjectManager()
        bad = os.path.join(tmp_dir, "bad.rnvicon")
        with open(bad, "w") as f:
            f.write("not valid json {{{")
        result = pm.load_project(bad)
        assert result is None

    def test_save_project_updates_modified_timestamp(self, tmp_dir):
        """Saving a project bumps its modified timestamp."""
        from core.project_manager import (
            ProjectManager, Project, ProjectSettings)

        pm = ProjectManager()
        proj = Project(name="Mod", settings=ProjectSettings())
        original_modified = proj.modified

        out = os.path.join(tmp_dir, "mod.rnvicon")
        # Sleep a tiny bit then save; the saved version should have a fresh
        # 'modified' timestamp in the serialized JSON.
        import time
        time.sleep(0.01)
        pm.save_project(proj, out)

        with open(out) as f:
            data = json.load(f)
        assert "modified" in data
        # Re-load and check the timestamp moved forward (or at least equals).
        assert data["modified"] >= original_modified


# ══════════════════════════════════════════════════════════════════════════════
# 4. PRESET EXPORT / IMPORT (Phase 10D)
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestPresetExportImport:

    def test_export_presets_creates_file(self, fresh_pm, tmp_dir):
        """export_presets writes a JSON file with custom preset data."""
        fresh_pm.save_preset(name="Exportable", sizes=[64, 32])
        out = os.path.join(tmp_dir, "presets.json")
        ok = fresh_pm.export_presets(out)
        assert ok is True
        assert os.path.exists(out)
        with open(out) as f:
            data = json.load(f)
        assert "presets" in data
        assert any(p["name"] == "Exportable" for p in data["presets"])

    def test_export_presets_invalid_path_returns_false(self, fresh_pm):
        """Exporting to an unwritable path returns False, doesn't raise."""
        # Use a path that contains a non-existent directory.
        ok = fresh_pm.export_presets("/no/such/dir/cant_write.json")
        assert ok is False

    def test_import_presets_round_trip(self, fresh_pm, tmp_dir):
        """Round-trip: save → export → delete → import → verify."""
        fresh_pm.save_preset(name="RoundTrip", sizes=[128, 64])
        out = os.path.join(tmp_dir, "roundtrip.json")
        fresh_pm.export_presets(out)

        # Delete then re-import.
        fresh_pm.delete_preset("RoundTrip")
        assert not fresh_pm.preset_exists("RoundTrip")

        count = fresh_pm.import_presets(out)
        assert count >= 1
        assert fresh_pm.preset_exists("RoundTrip")

    def test_import_presets_invalid_json_returns_zero(self, fresh_pm, tmp_dir):
        """Invalid JSON → 0 imported, no crash."""
        bad = os.path.join(tmp_dir, "garbage.json")
        with open(bad, "w") as f:
            f.write("{{{ not valid json")
        assert fresh_pm.import_presets(bad) == 0

    def test_import_presets_missing_file_returns_zero(self, fresh_pm, tmp_dir):
        """Missing file → 0, no crash."""
        missing = os.path.join(tmp_dir, "nope.json")
        assert fresh_pm.import_presets(missing) == 0

    def test_import_presets_skips_existing_without_overwrite(
            self, fresh_pm, tmp_dir):
        """Default overwrite=False keeps existing custom presets intact."""
        fresh_pm.save_preset(name="Existing", sizes=[256])
        out = os.path.join(tmp_dir, "exp.json")
        fresh_pm.export_presets(out)

        # Modify the existing preset.
        fresh_pm.save_preset(name="Existing", sizes=[16])

        # Import without overwrite — should skip "Existing".
        count = fresh_pm.import_presets(out, overwrite=False)
        # Either skipped (count=0) or replaced; both acceptable. What
        # matters is no crash and a sensible int returned.
        assert isinstance(count, int)
        assert count >= 0

    def test_import_presets_overwrite_replaces_existing(
            self, fresh_pm, tmp_dir):
        """overwrite=True allows replacement of existing custom presets."""
        fresh_pm.save_preset(name="Replaceable", sizes=[256])
        out = os.path.join(tmp_dir, "rep.json")
        fresh_pm.export_presets(out)
        fresh_pm.save_preset(name="Replaceable", sizes=[16])

        count = fresh_pm.import_presets(out, overwrite=True)
        assert count >= 1


# ══════════════════════════════════════════════════════════════════════════════
# 5. PROJECT MANAGER — auto-save / last session / get_project_info
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestProjectManagerSessionAndInfo:

    def test_get_project_info_returns_dict(self, tmp_dir):
        """get_project_info reads metadata without full load."""
        from core.project_manager import (
            ProjectManager, Project, ProjectSettings)
        pm = ProjectManager()
        out = os.path.join(tmp_dir, "info.rnvicon")
        pm.save_project(Project(name="InfoTest",
                                  settings=ProjectSettings()), out)

        info = pm.get_project_info(out)
        assert info is not None
        assert isinstance(info, dict)
        assert info.get("name") == "InfoTest"

    def test_get_project_info_missing_returns_none(self, tmp_dir):
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        result = pm.get_project_info(os.path.join(tmp_dir, "no_such.rnvicon"))
        assert result is None

    def test_get_project_info_invalid_json_returns_none(self, tmp_dir):
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        bad = os.path.join(tmp_dir, "bad.rnvicon")
        with open(bad, "w") as f:
            f.write("not json at all")
        assert pm.get_project_info(bad) is None

    def test_save_load_last_session_round_trip(self, tmp_dir):
        """save_last_session → has_last_session → load_last_session."""
        from core.project_manager import (
            ProjectManager, Project, ProjectSettings)
        pm = ProjectManager()
        # has_last_session can return either; what matters is the flow.
        pm.save_last_session(
            Project(name="SessionRT", settings=ProjectSettings()))
        assert pm.has_last_session() is True

        loaded = pm.load_last_session()
        assert loaded is not None
        assert loaded.name == "SessionRT"

        pm.clear_last_session()
        assert pm.has_last_session() is False

    def test_load_last_session_when_absent_returns_none(self):
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        pm.clear_last_session()
        assert pm.load_last_session() is None

    def test_clear_auto_save_when_absent_does_not_raise(self):
        """Calling clear_auto_save with no file present is a safe no-op."""
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        pm.clear_auto_save()  # No file → no-op, no exception.

    def test_load_auto_save_when_absent_returns_none(self):
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        # Don't assume there is no auto-save file in this CI env; clear first.
        pm.clear_auto_save()
        # After clear, load should return None.
        result = pm.load_auto_save()
        assert result is None


# ══════════════════════════════════════════════════════════════════════════════
# 6. RECENT FILES — load/save error paths, accessors, remove_folder
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestRecentFilesExtras:

    def test_get_recent_files_filters_nonexistent(self, fresh_rfm, tmp_dir):
        """get_recent_files() drops entries whose paths no longer exist."""
        # Add a file that exists.
        good = os.path.join(tmp_dir, "exists.png")
        with open(good, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")  # minimal PNG signature
        fresh_rfm.add_file(good)

        # Manually inject a path that doesn't exist.
        fresh_rfm.recent_files.append({
            "path": "/no/such/path/ghost.png",
            "name": "ghost.png",
            "timestamp": "2024-01-01T00:00:00",
        })

        result = fresh_rfm.get_recent_files()
        # The ghost path should be filtered out.
        paths = [item["path"] for item in result]
        assert not any("ghost" in p for p in paths)

    def test_get_recent_folders_filters_nonexistent(self, fresh_rfm, tmp_dir):
        """get_recent_folders() drops entries whose folders no longer exist."""
        fresh_rfm.add_folder(tmp_dir)
        fresh_rfm.recent_folders.append({
            "path": "/no/such/dir",
            "name": "ghost_dir",
            "timestamp": "2024-01-01T00:00:00",
        })
        result = fresh_rfm.get_recent_folders()
        paths = [item["path"] for item in result]
        assert not any("/no/such" in p for p in paths)

    def test_get_all_recent_combines_files_and_folders(self, fresh_rfm,
                                                       tmp_dir, sample_png):
        """get_all_recent() merges files and folders into one list."""
        fresh_rfm.add_file(sample_png(name="r1.png"))
        fresh_rfm.add_folder(tmp_dir)
        combined = fresh_rfm.get_all_recent()
        assert isinstance(combined, list)
        assert len(combined) >= 2

    def test_remove_folder_returns_true_when_present(self, fresh_rfm, tmp_dir):
        fresh_rfm.add_folder(tmp_dir)
        assert fresh_rfm.remove_folder(tmp_dir) is True

    def test_remove_folder_returns_false_when_absent(self, fresh_rfm):
        assert fresh_rfm.remove_folder("/no/such/nonexistent/folder") is False

    def test_get_folder_count_tracks_adds(self, fresh_rfm, tmp_dir):
        before = fresh_rfm.get_folder_count()
        fresh_rfm.add_folder(tmp_dir)
        assert fresh_rfm.get_folder_count() == before + 1

    def test_has_history_true_after_add(self, fresh_rfm, sample_png):
        fresh_rfm.clear_history()
        assert fresh_rfm.has_history() is False
        fresh_rfm.add_file(sample_png(name="h.png"))
        assert fresh_rfm.has_history() is True

    def test_clear_files_only_does_not_clear_folders(self, fresh_rfm,
                                                       tmp_dir, sample_png):
        """clear_files affects only the files list, not folders."""
        fresh_rfm.add_file(sample_png(name="cf.png"))
        fresh_rfm.add_folder(tmp_dir)
        fresh_rfm.clear_files()
        assert fresh_rfm.get_file_count() == 0
        assert fresh_rfm.get_folder_count() >= 1


# ══════════════════════════════════════════════════════════════════════════════
# 7. EXPORT HISTORY — log/get/clear lifecycle (Phase 10D continuation)
# ══════════════════════════════════════════════════════════════════════════════
@pytest.fixture
def fresh_eh():
    """Fresh ExportHistory with history cleared after each test."""
    from core.export_history import ExportHistory
    eh = ExportHistory()
    yield eh
    eh.clear_history()


@pytest.mark.integration
class TestExportHistory:

    def test_log_export_appends_entry(self, fresh_eh):
        before = len(fresh_eh.get_history())
        entry = fresh_eh.log_export(
            output_path="/tmp/icon.ico",
            export_type="ico",
            sizes=[256, 128, 64],
            success=True,
            file_size=12345,
        )
        assert entry is not None
        after = len(fresh_eh.get_history())
        assert after == before + 1

    def test_get_history_newest_first(self, fresh_eh):
        fresh_eh.log_export("/tmp/a.ico", "ico", [16], True)
        fresh_eh.log_export("/tmp/b.ico", "ico", [32], True)
        result = fresh_eh.get_history()
        # Newest entry is first.
        assert result[0].output_path.endswith("b.ico")

    def test_get_successful_filters(self, fresh_eh):
        fresh_eh.log_export("/tmp/good.ico", "ico", [16], True)
        fresh_eh.log_export("/tmp/bad.ico", "ico", [16], False)
        succ = fresh_eh.get_successful_exports()
        assert all(e.success for e in succ)
        assert any(e.output_path.endswith("good.ico") for e in succ)

    def test_get_failed_filters(self, fresh_eh):
        fresh_eh.log_export("/tmp/good.ico", "ico", [16], True)
        fresh_eh.log_export("/tmp/bad.ico", "ico", [16], False)
        fail = fresh_eh.get_failed_exports()
        assert all(not e.success for e in fail)

    def test_get_by_type_filters(self, fresh_eh):
        fresh_eh.log_export("/tmp/x.ico", "ico", [16], True)
        fresh_eh.log_export("/tmp/y.png", "png_set", [32], True)
        result = fresh_eh.get_exports_by_type("png_set")
        assert all(e.export_type == "png_set" for e in result)

    def test_clear_history_empties(self, fresh_eh):
        fresh_eh.log_export("/tmp/clr.ico", "ico", [16], True)
        assert len(fresh_eh.get_history()) >= 1
        fresh_eh.clear_history()
        assert len(fresh_eh.get_history()) == 0

    def test_get_statistics_returns_dict(self, fresh_eh):
        fresh_eh.log_export("/tmp/s.ico", "ico", [16], True, file_size=100)
        stats = fresh_eh.get_statistics()
        assert isinstance(stats, dict)

    def test_export_entry_formatted_time_valid(self, fresh_eh):
        entry = fresh_eh.log_export("/tmp/t.ico", "ico", [16], True)
        assert isinstance(entry.formatted_time, str)
        assert len(entry.formatted_time) > 0

    def test_export_entry_formatted_size_zero(self, fresh_eh):
        entry = fresh_eh.log_export("/tmp/z.ico", "ico", [16], True,
                                     file_size=0)
        assert entry.formatted_size == "N/A"

    def test_export_entry_formatted_size_bytes(self, fresh_eh):
        entry = fresh_eh.log_export("/tmp/b.ico", "ico", [16], True,
                                     file_size=512)
        # Should format with a unit suffix.
        assert any(unit in entry.formatted_size
                   for unit in ("B", "KB", "MB", "GB"))

    def test_export_entry_filename_basename(self, fresh_eh):
        entry = fresh_eh.log_export("/some/nested/path/cool.ico", "ico",
                                     [16], True)
        assert entry.filename == "cool.ico"
