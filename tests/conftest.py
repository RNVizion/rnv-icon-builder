"""
RNV Icon Builder — Shared pytest fixtures and bootstrap
=======================================================

This conftest.py runs automatically before any test in the tests/ folder.
It centralizes everything that test_rnv_icon_builder.py previously did inline,
so future test files (Phases 3-8) inherit the setup for free.

Responsibilities:
  1. Set the headless Qt platform before any Qt module is imported.
  2. Locate the project root (parent of this tests/ folder).
  3. Wire the flat project layout into virtual core/utils/ui packages
     so tests can write `from core.icon_builder_core import ...`.
  4. Patch modules that touch user-data dirs to no-op during tests.
  5. Provide shared fixtures: qapp, tmp_dir, sample_rgba, sample_png.
"""

import os
import sys
import types
import importlib.util
import tempfile
import shutil
from pathlib import Path

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# 1. HEADLESS QT — must run before any PyQt6 module is imported anywhere
# ══════════════════════════════════════════════════════════════════════════════
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# ══════════════════════════════════════════════════════════════════════════════
# 2. LOCATE PROJECT ROOT (the folder that contains RNV_Icon_Builder.py)
# ══════════════════════════════════════════════════════════════════════════════
_THIS = Path(__file__).resolve()
_PROJECT_ROOT: str | None = None

for _candidate in [
    _THIS.parent.parent,                      # tests/.. — the normal case
    _THIS.parent,                              # legacy: conftest at root
    Path("/mnt/project"),                      # sandboxed environments
    Path.home() / "RNV_Icon_Builder",          # default install location
]:
    if (_candidate / "RNV_Icon_Builder.py").exists():
        _PROJECT_ROOT = str(_candidate)
        break
    if (_candidate / "icon_builder_core.py").exists() and \
       (_candidate / "image_processor.py").exists():
        _PROJECT_ROOT = str(_candidate)
        break

if _PROJECT_ROOT is None:
    raise RuntimeError(
        "Cannot find RNV Icon Builder project root.\n"
        "The tests/ folder must sit alongside RNV_Icon_Builder.py."
    )


# ══════════════════════════════════════════════════════════════════════════════
# 3. WIRE FLAT LAYOUT INTO VIRTUAL core / utils / ui PACKAGES
# ══════════════════════════════════════════════════════════════════════════════
# All project .py files live in one flat directory but internally import from
# core.X, utils.X, and ui.X. We create empty namespace packages that point at
# the flat directory, then preload each module under its dotted name.
#
# This block is idempotent — re-running is a no-op thanks to the
# `if X in sys.modules: continue` guards.
_SUBDIR_LAYOUT = os.path.isdir(os.path.join(_PROJECT_ROOT, "core"))

if _SUBDIR_LAYOUT:
    # Real subdirectory layout — just add to path.
    sys.path.insert(0, _PROJECT_ROOT)
    sys.path.insert(0, os.path.join(_PROJECT_ROOT, "core"))
    sys.path.insert(0, os.path.join(_PROJECT_ROOT, "utils"))
    sys.path.insert(0, os.path.join(_PROJECT_ROOT, "ui"))
else:
    # Flat layout — synthesize virtual packages.
    sys.path.insert(0, _PROJECT_ROOT)
    for _pkg in ("core", "utils", "ui"):
        if _pkg in sys.modules:
            continue
        _module = types.ModuleType(_pkg)
        _module.__path__ = [_PROJECT_ROOT]
        _module.__package__ = _pkg
        sys.modules[_pkg] = _module

    _MODULES_BY_PACKAGE = {
        "utils": [
            "logger", "config", "error_handler", "file_utils",
            "signal_manager", "pixmap_cache", "async_file_ops",
            "dialog_helper", "font_loader",
        ],
        "core": [
            "icon_builder_core", "image_processor", "recent_files",
            "preset_manager", "session_manager", "export_history",
            "batch_processor", "project_manager", "folder_watcher",
        ],
        "ui": [
            "colors", "theme_manager", "preview_utils",
            "image_adjustments", "base_dialog", "context_preview",
            "metadata_panel", "ico_analyzer", "debug_button",
            "about_dialog", "settings_dialog",
        ],
    }
    for _pkg, _names in _MODULES_BY_PACKAGE.items():
        for _name in _names:
            _full = f"{_pkg}.{_name}"
            if _full in sys.modules:
                continue
            _spec = importlib.util.spec_from_file_location(
                _full, os.path.join(_PROJECT_ROOT, f"{_name}.py"))
            if not _spec:
                continue
            _mod = importlib.util.module_from_spec(_spec)
            _mod.__package__ = _pkg
            sys.modules[_full] = _mod
            sys.modules[_name] = _mod
            try:
                _spec.loader.exec_module(_mod)
            except Exception:
                # Qt-heavy or disk-touching modules may fail headless.
                # Skip silently; tests that need them will surface the error.
                pass


# ══════════════════════════════════════════════════════════════════════════════
# 4. PATCH MODULES THAT TOUCH USER-DATA DIRECTORIES
# ══════════════════════════════════════════════════════════════════════════════
# These patches prevent the test suite from reading or writing to
# the real ~/.config / AppData paths during test runs.
def _apply_user_data_patches() -> None:
    try:
        from core.recent_files import RecentFilesManager
        RecentFilesManager._load = lambda self: None
        RecentFilesManager._save = lambda self: None
    except Exception:
        pass

    try:
        from core.export_history import ExportHistory
        ExportHistory._load_history = lambda self: None
        ExportHistory._save_history = lambda self: None
        ExportHistory._ensure_directory = lambda self: None
    except Exception:
        pass

    try:
        from core.session_manager import SessionManager
        SessionManager._ensure_directory = lambda self: None
    except Exception:
        pass


_apply_user_data_patches()


# ══════════════════════════════════════════════════════════════════════════════
# 5. SHARED FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def qapp():
    """
    Provide a single QApplication for the whole test session.

    pytest-qt also creates one automatically via its `qapp` fixture, but
    declaring our own makes the dependency explicit and lets non-qtbot tests
    request it directly. The fixture is session-scoped because Qt only
    permits one QApplication per process.
    """
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
        app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    yield app
    # No explicit quit — letting Python tear down avoids the headless
    # cleanup crash that the standalone runner works around with os._exit.


@pytest.fixture
def tmp_dir():
    """An isolated temp directory, cleaned up after the test."""
    d = tempfile.mkdtemp(prefix="rnv_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_rgba():
    """
    Factory: sample_rgba(w=64, h=64, color=(255, 0, 0, 255)) -> PIL.Image.

    Returns a callable so each test can produce as many distinct images
    as it needs without re-importing PIL or repeating defaults.
    """
    from PIL import Image

    def _make(w: int = 64, h: int = 64, color=(255, 0, 0, 255)):
        return Image.new("RGBA", (w, h), color)

    return _make


@pytest.fixture
def sample_png(tmp_dir, sample_rgba):
    """
    Factory: sample_png(name="test.png", size=64, color=(...)) -> path.

    Writes a small PNG into the per-test tmp_dir and returns the path.
    """
    def _make(name: str = "test.png",
              size: int = 64,
              color=(200, 100, 50, 255)) -> str:
        path = os.path.join(tmp_dir, name)
        sample_rgba(size, size, color).save(path, format="PNG")
        return path

    return _make


@pytest.fixture
def project_root() -> str:
    """The absolute path to the RNV Icon Builder project root."""
    return _PROJECT_ROOT


@pytest.fixture
def app(qapp, monkeypatch):
    """
    Yield a fresh IconBuilderApp for each test; close + delete on teardown.

    Used by Phase 3 (application tests) and Phase 4 (UI interaction tests
    that need keyboard shortcuts driven against the real main window).

    Patches applied before construction:
      * _setup_auto_save — would start a long-running QTimer that leaks
        across tests.
      * _check_session_recovery — would prompt or read the user's session
        file; we don't want that in a test environment.
      * ErrorHandler.confirm_action — auto-confirms so destructive actions
        like clear_files() don't block on a hidden QMessageBox.

    Fusion style is set on the QApplication because IconBuilderApp's palette
    application paths require it (per the project's documented theming rules).
    """
    from PyQt6.QtWidgets import QApplication

    qapp.setStyle("Fusion")

    # Resolve IconBuilderApp robustly. On some installs the project root
    # contains BOTH a `RNV_Icon_Builder` package directory AND a
    # `RNV_Icon_Builder.py` file. Python imports the package first, which may
    # be empty, so a plain `import RNV_Icon_Builder` won't find IconBuilderApp.
    # Strategy: try the normal import; if the class isn't there, load
    # RNV_Icon_Builder.py from disk as a standalone module.
    import RNV_Icon_Builder as rnv_module

    if not hasattr(rnv_module, "IconBuilderApp"):
        import importlib.util
        rnv_py_path = os.path.join(_PROJECT_ROOT, "RNV_Icon_Builder.py")
        if os.path.exists(rnv_py_path):
            spec = importlib.util.spec_from_file_location(
                "_rnv_icon_builder_app_module", rnv_py_path)
            rnv_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(rnv_module)

    from utils.error_handler import ErrorHandler

    monkeypatch.setattr(rnv_module.IconBuilderApp,
                        "_setup_auto_save",
                        lambda self: None)
    monkeypatch.setattr(rnv_module.IconBuilderApp,
                        "_check_session_recovery",
                        lambda self: None)
    monkeypatch.setattr(ErrorHandler,
                        "confirm_action",
                        staticmethod(lambda **kwargs: True))

    # Skip loading the high-res background image during tests. The real
    # image is ~144 megapixels and gets loaded on every IconBuilderApp
    # construction — across 42 application tests that's ~12 minutes of
    # PIL decoding. The few tests that care about theme resources patch
    # this back themselves.
    from ui.theme_manager import ThemeManager
    monkeypatch.setattr(ThemeManager, "detect_image_resources",
                        lambda self: False)

    window = rnv_module.IconBuilderApp()
    yield window

    # Teardown — let closeEvent run for proper cleanup, then drop the widget.
    try:
        window.close()
    except Exception:
        pass
    try:
        window.deleteLater()
    except Exception:
        pass
    QApplication.processEvents()
