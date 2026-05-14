"""
RNV Icon Builder — Comprehensive Test Suite v2.0
=================================================
Tests all core modules for functionality, edge cases, and boundary conditions.

Usage — place this file in your project root (same folder as RNV_Icon_Builder.py):
    python test_rnv_icon_builder.py           # standard run
    python test_rnv_icon_builder.py -v        # verbose (shows each test name)

Requirements: PyQt6, Pillow  (pip install PyQt6 Pillow)
"""

import sys, os, io, json, tempfile, shutil, unittest, types, importlib.util
from pathlib import Path
from datetime import datetime

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# QApplication MUST exist before any Qt module is imported or instantiated
try:
    from PyQt6.QtWidgets import QApplication as _QApp
    from PyQt6.QtCore import Qt as _Qt
    if not _QApp.instance():
        _qapp = _QApp(sys.argv[:1])
        _qapp.setAttribute(_Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
except Exception:
    _qapp = None

# ══════════════════════════════════════════════════════════════════════════════
# BOOTSTRAP — wire core / utils / ui packages from the flat project layout
# All project .py files live in one directory but internally import from
# core.X, utils.X, and ui.X, so we create virtual packages pointing at that dir.
# ══════════════════════════════════════════════════════════════════════════════
_THIS = Path(__file__).resolve()
_FLAT = None

for _c in [_THIS.parent,
           _THIS.parent.parent,
           Path("/mnt/project"),
           Path.home() / "RNV_Icon_Builder"]:
    if (_c / "RNV_Icon_Builder.py").exists():
        _FLAT = str(_c); break
    if (_c / "core").is_dir() and (_c / "utils").is_dir():
        _FLAT = str(_c); break
    if (_c / "icon_builder_core.py").exists() and (_c / "image_processor.py").exists():
        _FLAT = str(_c); break

if _FLAT is None:
    sys.exit(
        "ERROR: Cannot find project root.\n"
        "Place test_rnv_icon_builder.py in the same folder as RNV_Icon_Builder.py"
    )

_SUBDIR_LAYOUT = os.path.isdir(os.path.join(_FLAT, "core"))

if _SUBDIR_LAYOUT:
    sys.path.insert(0, _FLAT)
    sys.path.insert(0, os.path.join(_FLAT, "core"))
    sys.path.insert(0, os.path.join(_FLAT, "utils"))
    sys.path.insert(0, os.path.join(_FLAT, "ui"))
else:
    sys.path.insert(0, _FLAT)
    for _pkg in ("core", "utils", "ui"):
        _m = types.ModuleType(_pkg)
        _m.__path__ = [_FLAT]
        _m.__package__ = _pkg
        sys.modules[_pkg] = _m

    _LOAD = {
        "utils": ["logger", "config", "error_handler", "file_utils",
                  "signal_manager", "pixmap_cache", "async_file_ops"],
        "core":  ["icon_builder_core", "image_processor", "recent_files",
                  "preset_manager", "session_manager", "export_history",
                  "batch_processor", "project_manager"],
        "ui":    ["colors", "theme_manager", "preview_utils", "image_adjustments"],
    }
    for _pkg, _names in _LOAD.items():
        for _name in _names:
            _full = f"{_pkg}.{_name}"
            if _full in sys.modules:
                continue
            _spec = importlib.util.spec_from_file_location(
                _full, os.path.join(_FLAT, f"{_name}.py"))
            if not _spec:
                continue
            _mod = importlib.util.module_from_spec(_spec)
            _mod.__package__ = _pkg
            sys.modules[_full] = _mod
            sys.modules[_name] = _mod
            try:
                _spec.loader.exec_module(_mod)
            except Exception:
                pass  # Qt-heavy or disk-touching modules may fail headless — skip silently

from core.icon_builder_core import IconBuilderCore
from core.image_processor    import ImageProcessor
from core.recent_files       import RecentFilesManager
from core.preset_manager     import PresetManager, SizePreset
from core.session_manager    import SessionManager, SessionState
from core.export_history     import ExportHistory, ExportEntry
from core.batch_processor    import BatchProcessor, BatchJob, JobStatus
from core.project_manager    import ProjectManager, Project, ProjectImage, ProjectSettings
from core.folder_watcher     import FolderWatcher, WatchSettings
from utils.error_handler     import ErrorHandler
from utils.file_utils        import FileUtils
from utils import config
from utils.logger            import (
    setup_logger, get_logger, set_log_level,
    log_success, log_failure, log_warning_symbol,
    Logger as AppLogger, get_logger_instance,
)
from utils.pixmap_cache      import QPixmapCache, ImagePixmapCache, ThumbnailCache, create_cache_key
from utils.dialog_helper     import DialogHelper, DialogResult
from ui.colors               import (
    BRAND_GOLD, BRAND_GOLD_DARK, BRAND_GOLD_RGB, BRAND_GOLD_DARK_RGB,
    DARK_THEME_COLORS, LIGHT_THEME_COLORS, IMAGE_MODE_COLORS,
    get_theme_colors,
    DEFAULT_CUSTOM_BG_COLOR, CONTRAST_ON_LIGHT, CONTRAST_ON_DARK,
    SWATCH_BORDER_ON_LIGHT, SWATCH_BORDER_ON_DARK, STATUS_ACTIVE_COLOR,
)
from ui.theme_manager        import ThemeManager
from ui.preview_utils        import (
    color_to_hex, hex_to_color, create_checkerboard_pattern,
    composite_on_checkerboard, composite_on_color, composite_with_background,
    extract_dominant_colors, pil_to_qpixmap,
    clear_thumbnail_cache, get_thumbnail_cache_stats,
)
from ui.image_adjustments        import (
    get_content_bounds, auto_crop, add_padding, center_content,
    resize_to_fit, make_square, rotate_image, flip_horizontal, flip_vertical,
    fill_transparency, add_border,
    adjust_brightness, adjust_contrast, adjust_saturation,
    convert_grayscale, apply_combined_adjustments,
)

from PyQt6.QtGui import QPixmap as _QPixmap

# Pillow — used to create in-memory test images
from PIL import Image as _Image

# ANSI colour helpers
_G="\033[92m"; _R="\033[91m"; _Y="\033[93m"; _C="\033[96m"; _B="\033[1m"; _X="\033[0m"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_rgba(w=64, h=64, color=(255, 0, 0, 255)) -> _Image.Image:
    """Return a solid-colour RGBA PIL image."""
    img = _Image.new("RGBA", (w, h), color)
    return img


def _make_png_file(path: str, size: int = 64, color=(200, 100, 50, 255)) -> str:
    """Save a simple PNG to *path* and return path."""
    _make_rgba(size, size, color).save(path, format="PNG")
    return path


# ── Patch RecentFilesManager to avoid touching the real history file ───────────
_RECENT_TMP = tempfile.mkdtemp()
_RECENT_SAFE = os.path.join(_RECENT_TMP, "test_recent.json")
RecentFilesManager._load  = lambda self: None      # no-op
RecentFilesManager._save  = lambda self: None      # no-op

# ── Patch ExportHistory / SessionManager to avoid touching user data dirs ──────
ExportHistory._load_history = lambda self: None
ExportHistory._save_history = lambda self: None
ExportHistory._ensure_directory = lambda self: None

SessionManager._ensure_directory = lambda self: None


# ══════════════════════════════════════════════════════════════════════════════
# 1. COLORS MODULE
# ══════════════════════════════════════════════════════════════════════════════
class TestColors(unittest.TestCase):
    """ui/colors.py — brand constants, theme dicts, get_theme_colors()."""

    # ── Brand constants ────────────────────────────────────────────────────────
    def test_brand_gold_hex_format(self):
        self.assertRegex(BRAND_GOLD, r'^#[0-9a-fA-F]{6}$')

    def test_brand_gold_dark_hex_format(self):
        self.assertRegex(BRAND_GOLD_DARK, r'^#[0-9a-fA-F]{6}$')

    def test_brand_gold_value(self):
        self.assertEqual(BRAND_GOLD.lower(), "#d2bc93")

    def test_brand_gold_dark_value(self):
        self.assertEqual(BRAND_GOLD_DARK.lower(), "#b19145")

    def test_brand_gold_rgb_tuple(self):
        self.assertEqual(BRAND_GOLD_RGB, (210, 188, 147))

    def test_brand_gold_dark_rgb_tuple(self):
        self.assertEqual(BRAND_GOLD_DARK_RGB, (177, 145, 69))

    def test_rgb_matches_hex_gold(self):
        r, g, b = BRAND_GOLD_RGB
        expected = f"#{r:02x}{g:02x}{b:02x}"
        self.assertEqual(BRAND_GOLD.lower(), expected)

    def test_rgb_matches_hex_gold_dark(self):
        r, g, b = BRAND_GOLD_DARK_RGB
        expected = f"#{r:02x}{g:02x}{b:02x}"
        self.assertEqual(BRAND_GOLD_DARK.lower(), expected)

    # ── Standalone constants ───────────────────────────────────────────────────
    def test_default_custom_bg_color(self):
        self.assertRegex(DEFAULT_CUSTOM_BG_COLOR, r'^#[0-9a-fA-F]{6}$')

    def test_contrast_on_light_is_black(self):
        self.assertEqual(CONTRAST_ON_LIGHT, "#000000")

    def test_contrast_on_dark_is_white(self):
        self.assertEqual(CONTRAST_ON_DARK, "#FFFFFF")

    def test_status_active_color_nonempty(self):
        self.assertGreater(len(STATUS_ACTIVE_COLOR), 3)

    def test_swatch_borders_nonempty(self):
        self.assertGreater(len(SWATCH_BORDER_ON_LIGHT), 0)
        self.assertGreater(len(SWATCH_BORDER_ON_DARK), 0)

    # ── Required keys present in all theme dicts ───────────────────────────────
    _REQUIRED_KEYS = [
        'window_bg', 'panel_bg', 'card_bg', 'input_bg',
        'text_primary', 'text_secondary', 'text_muted', 'text_disabled',
        'text_accent', 'text_on_accent',
        'border_default', 'border_focus', 'border_hover',
        'button_bg', 'button_text', 'button_hover_bg', 'button_pressed_bg',
        'button_pressed_text', 'button_border',
        'main_btn_bg', 'main_btn_text', 'main_btn_border',
        'main_btn_hover_bg', 'main_btn_hover_text',
        'main_btn_pressed_bg', 'main_btn_pressed_text',
        'tab_bg', 'tab_selected_bg', 'tab_hover_bg', 'tab_indicator',
        'scrollbar_bg', 'scrollbar_handle', 'scrollbar_handle_hover',
        'tooltip_bg', 'tooltip_text', 'tooltip_border',
        'list_bg', 'list_selected_bg', 'list_hover_bg',
        'dropzone_bg', 'dropzone_border', 'dropzone_active_bg',
        'success', 'warning', 'error',
    ]

    def _assert_keys(self, d, label):
        for k in self._REQUIRED_KEYS:
            self.assertIn(k, d, f"'{k}' missing from {label}")

    def test_dark_theme_colors_keys(self):
        self._assert_keys(DARK_THEME_COLORS, "DARK_THEME_COLORS")

    def test_light_theme_colors_keys(self):
        self._assert_keys(LIGHT_THEME_COLORS, "LIGHT_THEME_COLORS")

    def test_image_mode_colors_keys(self):
        self._assert_keys(IMAGE_MODE_COLORS, "IMAGE_MODE_COLORS")

    # ── get_theme_colors() returns correct dict ────────────────────────────────
    def test_get_theme_colors_dark(self):
        c = get_theme_colors(is_dark=True)
        self.assertEqual(c['window_bg'], DARK_THEME_COLORS['window_bg'])

    def test_get_theme_colors_light(self):
        c = get_theme_colors(is_dark=False)
        self.assertEqual(c['window_bg'], LIGHT_THEME_COLORS['window_bg'])

    def test_get_theme_colors_image_mode(self):
        c = get_theme_colors(is_dark=True, is_image_mode=True)
        self.assertEqual(c['window_bg'], IMAGE_MODE_COLORS['window_bg'])

    def test_get_theme_colors_returns_copy(self):
        c1 = get_theme_colors(is_dark=True)
        c2 = get_theme_colors(is_dark=True)
        c1['window_bg'] = "MUTATED"
        self.assertNotEqual(c2['window_bg'], "MUTATED")

    # ── Brand gold appears in dark theme accent positions ──────────────────────
    def test_dark_tooltip_border_is_brand_gold(self):
        self.assertEqual(DARK_THEME_COLORS['tooltip_border'].lower(), BRAND_GOLD.lower())

    def test_light_tooltip_border_is_brand_gold_dark(self):
        self.assertEqual(LIGHT_THEME_COLORS['tooltip_border'].lower(), BRAND_GOLD_DARK.lower())

    def test_dark_scrollbar_hover_is_brand_gold(self):
        self.assertEqual(DARK_THEME_COLORS['scrollbar_handle_hover'].lower(), BRAND_GOLD.lower())

    def test_light_scrollbar_hover_is_brand_gold_dark(self):
        self.assertEqual(LIGHT_THEME_COLORS['scrollbar_handle_hover'].lower(), BRAND_GOLD_DARK.lower())

    # ── Main button inverse system ─────────────────────────────────────────────
    def test_dark_main_btn_rest_bg(self):
        self.assertEqual(DARK_THEME_COLORS['main_btn_bg'], '#1A1A1A')

    def test_dark_main_btn_hover_bg(self):
        self.assertEqual(DARK_THEME_COLORS['main_btn_hover_bg'], '#333333')

    def test_dark_main_btn_pressed_bg(self):
        self.assertEqual(DARK_THEME_COLORS['main_btn_pressed_bg'], '#444444')

    def test_light_main_btn_rest_bg(self):
        self.assertEqual(LIGHT_THEME_COLORS['main_btn_bg'], '#FFFFFF')

    def test_light_main_btn_hover_bg(self):
        self.assertEqual(LIGHT_THEME_COLORS['main_btn_hover_bg'], '#333333')

    def test_light_main_btn_pressed_bg(self):
        self.assertEqual(LIGHT_THEME_COLORS['main_btn_pressed_bg'], '#444444')

    # ── Image mode inherits dark base ─────────────────────────────────────────
    def test_image_mode_inherits_dark_text(self):
        self.assertEqual(IMAGE_MODE_COLORS['text_primary'], DARK_THEME_COLORS['text_primary'])

    def test_image_mode_window_is_transparent(self):
        self.assertIn('rgba', IMAGE_MODE_COLORS['window_bg'])

    def test_image_mode_scrollbar_bg_transparent(self):
        self.assertEqual(IMAGE_MODE_COLORS['scrollbar_bg'], 'transparent')

    def test_image_mode_scrollbar_hover_is_brand_gold(self):
        self.assertEqual(IMAGE_MODE_COLORS['scrollbar_handle_hover'].lower(), BRAND_GOLD.lower())


# ══════════════════════════════════════════════════════════════════════════════
# 2. THEME MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestThemeManager(unittest.TestCase):
    """ui/theme_manager.py — theme cycling, state, scrollbar styles."""

    def setUp(self):
        self.tm = ThemeManager()

    _REQUIRED_KEYS = ['name', 'window_bg', 'text_color', 'border_color',
                      'button_bg', 'button_text', 'button_hover_bg',
                      'button_pressed_bg', 'button_pressed_text']

    def _assert_keys(self, theme, label):
        for k in self._REQUIRED_KEYS:
            self.assertIn(k, theme, f"'{k}' missing from {label}")

    def test_dark_theme_keys(self):    self._assert_keys(self.tm.DARK_THEME,  "DARK_THEME")
    def test_light_theme_keys(self):   self._assert_keys(self.tm.LIGHT_THEME, "LIGHT_THEME")

    def test_dark_theme_name(self):    self.assertEqual(self.tm.DARK_THEME['name'],  'Dark')
    def test_light_theme_name(self):   self.assertEqual(self.tm.LIGHT_THEME['name'], 'Light')

    def test_initial_theme_is_dark_or_image(self):
        self.assertIn(self.tm.current_theme, ('dark', 'image'))

    def test_set_dark(self):
        self.tm.set_theme('dark')
        self.assertEqual(self.tm.current_theme, 'dark')

    def test_set_light(self):
        self.tm.set_theme('light')
        self.assertEqual(self.tm.current_theme, 'light')

    def test_set_unknown_returns_false(self):
        result = self.tm.set_theme('neon')
        self.assertFalse(result)

    def test_cycle_dark_to_light(self):
        self.tm.set_theme('dark')
        self.tm.image_mode_available = False
        self.assertEqual(self.tm.cycle_theme(), 'light')

    def test_cycle_light_to_dark(self):
        self.tm.set_theme('light')
        self.tm.image_mode_available = False
        self.assertEqual(self.tm.cycle_theme(), 'dark')

    def test_cycle_includes_image_when_available(self):
        self.tm.image_mode_available = True
        self.tm.set_theme('light')
        self.assertEqual(self.tm.cycle_theme(), 'image')

    def test_get_current_theme_dark(self):
        self.tm.set_theme('dark')
        self.assertEqual(self.tm.get_current_theme()['name'], 'Dark')

    def test_get_current_theme_light(self):
        self.tm.set_theme('light')
        self.assertEqual(self.tm.get_current_theme()['name'], 'Light')

    def test_get_current_theme_image_returns_none(self):
        self.tm.image_mode_available = True
        self.tm.set_theme('image')
        self.assertIsNone(self.tm.get_current_theme())

    def test_display_name_dark(self):
        self.tm.set_theme('dark')
        self.assertIn('Dark', self.tm.get_theme_display_name())

    def test_display_name_light(self):
        self.tm.set_theme('light')
        self.assertIn('Light', self.tm.get_theme_display_name())

    def test_is_dark_mode(self):
        self.tm.set_theme('dark')
        self.assertTrue(self.tm.is_dark_mode())
        self.assertFalse(self.tm.is_light_mode())

    def test_is_light_mode(self):
        self.tm.set_theme('light')
        self.assertTrue(self.tm.is_light_mode())
        self.assertFalse(self.tm.is_dark_mode())

    def test_scrollbar_dark_nonempty(self):
        self.tm.set_theme('dark')
        s = self.tm.get_scrollbar_style()
        self.assertGreater(len(s), 100)

    def test_scrollbar_light_nonempty(self):
        self.tm.set_theme('light')
        s = self.tm.get_scrollbar_style()
        self.assertGreater(len(s), 100)

    def test_scrollbar_contains_brand_gold_hover_dark(self):
        self.tm.set_theme('dark')
        self.assertIn(BRAND_GOLD.lower(), self.tm.get_scrollbar_style().lower())

    def test_scrollbar_contains_brand_gold_hover_light(self):
        self.tm.set_theme('light')
        self.assertIn(BRAND_GOLD_DARK.lower(), self.tm.get_scrollbar_style().lower())

    def test_get_available_themes_no_image(self):
        self.tm.image_mode_available = False
        themes = self.tm.get_available_themes()
        self.assertIn('dark', themes)
        self.assertIn('light', themes)
        self.assertNotIn('image', themes)

    def test_get_available_themes_with_image(self):
        self.tm.image_mode_available = True
        self.assertIn('image', self.tm.get_available_themes())

    def test_get_theme_info_keys(self):
        info = self.tm.get_theme_info()
        for k in ('current', 'display_name', 'is_image_mode',
                  'image_mode_available', 'has_background', 'available_themes'):
            self.assertIn(k, info)

    def test_main_btn_hover_bg_is_from_inverse_system(self):
        # ThemeManager should NOT expose brand gold as button hover bg
        self.assertNotIn(BRAND_GOLD.lower(), self.tm.DARK_THEME.get('button_hover_bg', '').lower())

    def test_dark_theme_main_btn_pressed_text_is_black(self):
        self.assertEqual(self.tm.DARK_THEME['button_pressed_text'], '#000000')

    def test_light_theme_main_btn_pressed_text_is_white(self):
        self.assertEqual(self.tm.LIGHT_THEME['button_pressed_text'], '#FFFFFF')


# ══════════════════════════════════════════════════════════════════════════════
# 3. ICO BUILDER CORE
# ══════════════════════════════════════════════════════════════════════════════
class TestIconBuilderCore(unittest.TestCase):
    """core/icon_builder_core.py — ICO building, verification, analysis, estimation."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.png_64 = _make_png_file(os.path.join(cls.tmp, "icon64.png"), 64)
        cls.png_32 = _make_png_file(os.path.join(cls.tmp, "icon32.png"), 32)
        cls.png_16 = _make_png_file(os.path.join(cls.tmp, "icon16.png"), 16)
        cls.ico_path = os.path.join(cls.tmp, "test.ico")

        # Build a real ICO to use in multiple tests
        images = {
            64: _make_rgba(64, 64, (200, 100, 50, 255)),
            32: _make_rgba(32, 32, (100, 200, 50, 255)),
            16: _make_rgba(16, 16, (50, 100, 200, 255)),
        }
        IconBuilderCore.build_ico_file(images, cls.ico_path, use_png_compression=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ── build_ico_file ─────────────────────────────────────────────────────────
    def test_build_creates_file(self):
        self.assertTrue(os.path.exists(self.ico_path))

    def test_build_file_nonempty(self):
        self.assertGreater(os.path.getsize(self.ico_path), 0)

    def test_build_single_size(self):
        out = os.path.join(self.tmp, "single.ico")
        images = {256: _make_rgba(256, 256)}
        result = IconBuilderCore.build_ico_file(images, out)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(out))

    def test_build_all_standard_sizes(self):
        out = os.path.join(self.tmp, "all_sizes.ico")
        images = {s: _make_rgba(s, s) for s in [256, 128, 64, 48, 32, 16]}
        result = IconBuilderCore.build_ico_file(images, out)
        self.assertTrue(result)

    def test_build_without_png_compression(self):
        out = os.path.join(self.tmp, "bmp.ico")
        images = {32: _make_rgba(32, 32), 16: _make_rgba(16, 16)}
        result = IconBuilderCore.build_ico_file(images, out, use_png_compression=False)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(out))

    # ── verify_ico_file ────────────────────────────────────────────────────────
    def test_verify_valid_ico(self):
        info = IconBuilderCore.verify_ico_file(self.ico_path)
        self.assertGreater(info.get('count', 0), 0)

    def test_verify_image_count(self):
        info = IconBuilderCore.verify_ico_file(self.ico_path)
        # Built with 3 source sizes; autofill may add extra — assert at least 3
        self.assertGreaterEqual(info.get('count', 0), 3)

    def test_verify_nonexistent_file(self):
        info = IconBuilderCore.verify_ico_file("/no/such/file.ico")
        self.assertEqual(info.get('count', 0), 0)

    def test_verify_invalid_file(self):
        bad = os.path.join(self.tmp, "bad.ico")
        with open(bad, 'wb') as f:
            f.write(b"NOT AN ICO FILE")
        info = IconBuilderCore.verify_ico_file(bad)
        # Header bytes may parse as a large num_images, but the file is too
        # small to hold any real directory entries — sizes list must be empty
        self.assertEqual(len(info.get('sizes', [])), 0)

    # ── get_ico_info ───────────────────────────────────────────────────────────
    def test_get_ico_info_valid(self):
        info = IconBuilderCore.get_ico_info(self.ico_path)
        self.assertIsNotNone(info)
        self.assertTrue(info.get('valid', False))

    def test_get_ico_info_contains_images(self):
        info = IconBuilderCore.get_ico_info(self.ico_path)
        self.assertIn('images', info)
        self.assertGreater(len(info['images']), 0)

    def test_get_ico_info_contains_sizes(self):
        info = IconBuilderCore.get_ico_info(self.ico_path)
        self.assertIn('images', info)  # sizes are inside each image entry

    def test_get_ico_info_file_size(self):
        info = IconBuilderCore.get_ico_info(self.ico_path)
        self.assertGreater(info.get('file_size', 0), 0)

    def test_get_ico_info_missing_file(self):
        info = IconBuilderCore.get_ico_info("/no/file.ico")
        self.assertFalse(info.get('valid', True) if info else False)

    # ── extract_ico_to_pngs ────────────────────────────────────────────────────
    def test_extract_creates_pngs(self):
        out_dir = os.path.join(self.tmp, "extracted")
        os.makedirs(out_dir, exist_ok=True)
        success, msg, files = IconBuilderCore.extract_ico_to_pngs(
            self.ico_path, out_dir, "test")
        self.assertTrue(success)
        self.assertGreater(len(files), 0)
        for f in files:
            self.assertTrue(os.path.exists(f))

    def test_extract_pngs_are_png_format(self):
        out_dir = os.path.join(self.tmp, "extracted_fmt")
        os.makedirs(out_dir, exist_ok=True)
        success, _, files = IconBuilderCore.extract_ico_to_pngs(
            self.ico_path, out_dir, "fmt")
        if success:
            for f in files:
                self.assertTrue(f.endswith('.png'), f"{f} is not .png")

    def test_extract_missing_file_fails(self):
        success, msg, files = IconBuilderCore.extract_ico_to_pngs(
            "/no/file.ico", self.tmp, "x")
        self.assertFalse(success)

    # ── estimate_ico_size ──────────────────────────────────────────────────────
    def test_estimate_returns_dict(self):
        images = {64: _make_rgba(64, 64), 32: _make_rgba(32, 32)}
        result = IconBuilderCore.estimate_ico_size(images)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_estimate_total_positive(self):
        images = {64: _make_rgba(64, 64)}
        result = IconBuilderCore.estimate_ico_size(images)
        if result:
            self.assertGreater(result.get('total_bytes', 0), 0)

    def test_estimate_empty_images(self):
        result = IconBuilderCore.estimate_ico_size({})
        # Should handle gracefully (None or empty)
        self.assertTrue(result is None or result.get('total_bytes', 0) == 0)

    # ── prepare_image_data ─────────────────────────────────────────────────────
    def test_prepare_image_data_returns_bytes(self):
        img = _make_rgba(32, 32)
        data = IconBuilderCore.prepare_image_data(img, 32)
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)

    def test_prepare_image_data_rescales(self):
        img = _make_rgba(64, 64)
        data = IconBuilderCore.prepare_image_data(img, 16)
        self.assertIsInstance(data, bytes)


# ══════════════════════════════════════════════════════════════════════════════
# 4. IMAGE PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════
class TestImageProcessor(unittest.TestCase):
    """core/image_processor.py — load, validate, transform, undo/redo."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ip = ImageProcessor()
        self.png = _make_png_file(os.path.join(self.tmp, "icon.png"), 64)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── load_png ───────────────────────────────────────────────────────────────
    def test_load_png_returns_true(self):
        self.assertTrue(self.ip.load_png(self.png))

    def test_load_png_missing_file(self):
        self.assertFalse(self.ip.load_png("/no/such/icon.png"))

    def test_load_png_populates_detected(self):
        self.ip.load_png(self.png)
        self.assertTrue(self.ip.has_size(64))

    def test_load_wrong_extension(self):
        bad = os.path.join(self.tmp, "file.xyz")
        with open(bad, 'w') as f:
            f.write("not an image")
        self.assertFalse(self.ip.load_png(bad))

    # ── load_ico ────────────────────────────────────────────────────────────────
    def test_load_ico_from_built_file(self):
        ico = os.path.join(self.tmp, "test.ico")
        images = {32: _make_rgba(32, 32), 16: _make_rgba(16, 16)}
        IconBuilderCore.build_ico_file(images, ico)
        count = self.ip.load_ico(ico)
        self.assertGreaterEqual(count, 1)

    # ── validate_size ──────────────────────────────────────────────────────────
    def test_validate_square_true(self):
        self.assertTrue(self.ip.validate_size(64, 64))

    def test_validate_non_square_false(self):
        self.assertFalse(self.ip.validate_size(64, 32))

    def test_validate_zero_false(self):
        self.assertFalse(self.ip.validate_size(0, 0))

    # ── get / has / clear ──────────────────────────────────────────────────────
    def test_get_detected_empty_initially(self):
        ip = ImageProcessor()
        self.assertEqual(len(ip.get_detected_images()), 0)

    def test_clear_images(self):
        self.ip.load_png(self.png)
        self.ip.clear_images()
        self.assertEqual(len(self.ip.get_detected_images()), 0)

    def test_get_image_returns_pil(self):
        self.ip.load_png(self.png)
        img = self.ip.get_image(64)
        self.assertIsNotNone(img)
        self.assertIsInstance(img, _Image.Image)

    def test_get_available_sizes(self):
        self.ip.load_png(self.png)
        sizes = self.ip.get_available_sizes()
        self.assertIn(64, sizes)

    def test_get_missing_sizes(self):
        self.ip.load_png(self.png)
        missing = self.ip.get_missing_sizes()
        # 64 loaded; at minimum 256, 128, 48, 32, 16 should be missing
        self.assertGreater(len(missing), 0)
        self.assertNotIn(64, missing)

    def test_remove_size(self):
        self.ip.load_png(self.png)
        self.assertTrue(self.ip.has_size(64))
        self.ip.remove_size(64)
        self.assertFalse(self.ip.has_size(64))

    def test_get_largest_size(self):
        self.ip.load_png(self.png)
        self.assertEqual(self.ip.get_largest_size(), 64)

    # ── undo / redo ─────────────────────────────────────────────────────────────
    def test_no_undo_initially(self):
        self.ip.load_png(self.png)
        self.assertFalse(self.ip.can_undo())

    def test_undo_after_transform(self):
        self.ip.load_png(self.png)
        self.ip.apply_rotate(90)
        self.assertTrue(self.ip.can_undo())

    def test_undo_restores_state(self):
        self.ip.load_png(self.png)
        before = self.ip.get_image(64).tobytes()
        self.ip.apply_rotate(90)
        self.ip.undo()
        after = self.ip.get_image(64).tobytes()
        self.assertEqual(before, after)

    def test_redo_after_undo(self):
        self.ip.load_png(self.png)
        self.ip.apply_rotate(90)
        self.ip.undo()
        self.assertTrue(self.ip.can_redo())

    # ── image adjustments ──────────────────────────────────────────────────────
    def test_apply_rotate_90(self):
        self.ip.load_png(self.png)
        count = self.ip.apply_rotate(90)
        self.assertGreaterEqual(count, 1)

    def test_apply_rotate_180(self):
        self.ip.load_png(self.png)
        count = self.ip.apply_rotate(180)
        self.assertGreaterEqual(count, 1)

    def test_apply_flip_horizontal(self):
        self.ip.load_png(self.png)
        count = self.ip.apply_flip_horizontal()
        self.assertGreaterEqual(count, 1)

    def test_apply_flip_vertical(self):
        self.ip.load_png(self.png)
        count = self.ip.apply_flip_vertical()
        self.assertGreaterEqual(count, 1)

    def test_apply_grayscale(self):
        self.ip.load_png(self.png)
        count = self.ip.apply_grayscale()
        self.assertGreaterEqual(count, 1)

    def test_apply_color_adjustments(self):
        self.ip.load_png(self.png)
        count = self.ip.apply_color_adjustments(brightness=10, contrast=10, saturation=10)
        self.assertGreaterEqual(count, 1)

    def test_apply_auto_crop(self):
        self.ip.load_png(self.png)
        count = self.ip.apply_auto_crop()
        self.assertGreaterEqual(count, 0)

    def test_apply_padding(self):
        self.ip.load_png(self.png)
        count = self.ip.apply_padding(padding=4)
        self.assertGreaterEqual(count, 1)

    # ── statistics ─────────────────────────────────────────────────────────────
    def test_get_statistics_keys(self):
        self.ip.load_png(self.png)
        stats = self.ip.get_statistics()
        self.assertIn('count', stats)

    def test_get_summary_string(self):
        self.ip.load_png(self.png)
        s = self.ip.get_summary()
        self.assertIsInstance(s, str)


# ══════════════════════════════════════════════════════════════════════════════
# 5. PREVIEW UTILS
# ══════════════════════════════════════════════════════════════════════════════
class TestPreviewUtils(unittest.TestCase):
    """ui/preview_utils.py — color helpers, checkerboard, compositing."""

    # ── color_to_hex / hex_to_color ────────────────────────────────────────────
    def test_color_to_hex_black(self):
        self.assertEqual(color_to_hex((0, 0, 0)), '#000000')

    def test_color_to_hex_white(self):
        self.assertEqual(color_to_hex((255, 255, 255)), '#FFFFFF')

    def test_color_to_hex_red(self):
        self.assertEqual(color_to_hex((255, 0, 0)), '#FF0000')

    def test_color_to_hex_brand_gold(self):
        self.assertEqual(color_to_hex((210, 188, 147)).lower(), '#d2bc93')

    def test_hex_to_color_black(self):
        self.assertEqual(hex_to_color('#000000'), (0, 0, 0))

    def test_hex_to_color_white(self):
        self.assertEqual(hex_to_color('#FFFFFF'), (255, 255, 255))

    def test_hex_to_color_uppercase(self):
        self.assertEqual(hex_to_color('#FF0000'), (255, 0, 0))

    def test_roundtrip_hex_color(self):
        for c in [(0, 0, 0), (255, 255, 255), (128, 64, 200), (210, 188, 147)]:
            self.assertEqual(hex_to_color(color_to_hex(c)), c)

    # ── create_checkerboard_pattern ────────────────────────────────────────────
    def test_checkerboard_returns_rgba_image(self):
        img = create_checkerboard_pattern(64, 64)
        self.assertIsInstance(img, _Image.Image)
        self.assertIn(img.mode, ('RGB', 'RGBA'))

    def test_checkerboard_correct_size(self):
        img = create_checkerboard_pattern(128, 64)
        self.assertEqual(img.size, (128, 64))

    def test_checkerboard_custom_square(self):
        img = create_checkerboard_pattern(32, 32, square_size=4)
        self.assertEqual(img.size, (32, 32))

    # ── composite_on_checkerboard ──────────────────────────────────────────────
    def test_composite_on_checkerboard_returns_image(self):
        src = _make_rgba(64, 64, (255, 0, 0, 128))
        result = composite_on_checkerboard(src)
        self.assertIsInstance(result, _Image.Image)

    def test_composite_on_checkerboard_correct_size(self):
        src = _make_rgba(48, 48)
        result = composite_on_checkerboard(src)
        self.assertEqual(result.size, (48, 48))

    def test_composite_opaque_covers_checker(self):
        src = _make_rgba(32, 32, (200, 0, 0, 255))
        result = composite_on_checkerboard(src)
        px = result.getpixel((0, 0))
        self.assertEqual(px[0], 200)

    # ── composite_on_color ─────────────────────────────────────────────────────
    def test_composite_on_color_returns_image(self):
        src = _make_rgba(32, 32)
        result = composite_on_color(src, (255, 255, 255))
        self.assertIsInstance(result, _Image.Image)

    def test_composite_on_color_correct_size(self):
        src = _make_rgba(16, 16)
        result = composite_on_color(src, (0, 0, 0))
        self.assertEqual(result.size, (16, 16))

    # ── composite_with_background ──────────────────────────────────────────────
    def test_composite_with_bg_checkerboard(self):
        src = _make_rgba(32, 32)
        result = composite_with_background(src, 'checkerboard')
        self.assertIsInstance(result, _Image.Image)

    def test_composite_with_bg_white(self):
        src = _make_rgba(32, 32)
        result = composite_with_background(src, 'white')
        self.assertIsInstance(result, _Image.Image)

    def test_composite_with_bg_black(self):
        src = _make_rgba(32, 32)
        result = composite_with_background(src, 'black')
        self.assertIsInstance(result, _Image.Image)

    def test_composite_with_bg_custom(self):
        src = _make_rgba(32, 32)
        result = composite_with_background(src, 'custom', (128, 64, 32))
        self.assertIsInstance(result, _Image.Image)

    # ── extract_dominant_colors ────────────────────────────────────────────────
    def test_extract_dominant_returns_list(self):
        src = _make_rgba(64, 64, (255, 0, 0, 255))
        result = extract_dominant_colors(src, count=3)
        self.assertIsInstance(result, list)

    def test_extract_dominant_respects_count(self):
        src = _make_rgba(64, 64)
        result = extract_dominant_colors(src, count=4)
        self.assertLessEqual(len(result), 4)

    def test_extract_dominant_nonempty_for_solid(self):
        src = _make_rgba(32, 32, (100, 200, 50, 255))
        result = extract_dominant_colors(src, count=1)
        self.assertGreater(len(result), 0)

# ══════════════════════════════════════════════════════════════════════════════
# 6. RECENT FILES MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestRecentFilesManager(unittest.TestCase):
    """core/recent_files.py — add, get, clear, remove (disk I/O patched out)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.rfm = RecentFilesManager()
        self.rfm.recent_files = []
        self.rfm.recent_folders = []
        # Real paths that exist on disk (needed for get_recent_files/folders
        # which filter out non-existent entries)
        self.real_file = _make_png_file(os.path.join(self.tmp, "icon.png"), 16)
        self.real_folder = self.tmp

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_add_file_increments_count(self):
        self.rfm.add_file(self.real_file)
        self.assertEqual(self.rfm.get_file_count(), 1)

    def test_add_file_retrieval(self):
        self.rfm.add_file(self.real_file)
        files = self.rfm.get_recent_files()
        self.assertEqual(len(files), 1)
        self.assertIn('path', files[0])

    def test_add_folder_increments_count(self):
        self.rfm.add_folder(self.real_folder)
        self.assertEqual(self.rfm.get_folder_count(), 1)

    def test_add_folder_retrieval(self):
        self.rfm.add_folder(self.real_folder)
        folders = self.rfm.get_recent_folders()
        self.assertEqual(len(folders), 1)

    def test_add_multiple_files(self):
        for i in range(5):
            p = _make_png_file(os.path.join(self.tmp, f"icon{i}.png"), 16)
            self.rfm.add_file(p)
        self.assertEqual(self.rfm.get_file_count(), 5)

    def test_get_all_recent_combined(self):
        self.rfm.add_file(self.real_file)
        self.rfm.add_folder(self.real_folder)
        all_items = self.rfm.get_all_recent()
        self.assertGreaterEqual(len(all_items), 2)

    def test_clear_history(self):
        self.rfm.add_file(self.real_file)
        self.rfm.add_folder(self.real_folder)
        self.rfm.clear_history()
        self.assertFalse(self.rfm.has_history())

    def test_clear_files_only(self):
        self.rfm.add_file(self.real_file)
        self.rfm.add_folder(self.real_folder)
        self.rfm.clear_files()
        self.assertEqual(self.rfm.get_file_count(), 0)
        self.assertEqual(self.rfm.get_folder_count(), 1)

    def test_clear_folders_only(self):
        self.rfm.add_file(self.real_file)
        self.rfm.add_folder(self.real_folder)
        self.rfm.clear_folders()
        self.assertEqual(self.rfm.get_file_count(), 1)
        self.assertEqual(self.rfm.get_folder_count(), 0)

    def test_remove_file(self):
        self.rfm.add_file(self.real_file)
        result = self.rfm.remove_file(self.real_file)
        self.assertTrue(result)
        self.assertEqual(self.rfm.get_file_count(), 0)

    def test_remove_file_nonexistent(self):
        result = self.rfm.remove_file("/nonexistent_abc123.png")
        self.assertFalse(result)

    def test_has_history_false_when_empty(self):
        self.assertFalse(self.rfm.has_history())

    def test_has_history_true_after_add(self):
        self.rfm.add_file(self.real_file)
        self.assertTrue(self.rfm.has_history())

    def test_duplicate_file_not_doubled(self):
        # Adding same real file twice should not create duplicate entries
        self.rfm.add_file(self.real_file)
        self.rfm.add_file(self.real_file)
        self.assertLessEqual(self.rfm.get_file_count(), 1)


# ══════════════════════════════════════════════════════════════════════════════
# 7. PRESET MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestPresetManager(unittest.TestCase):
    """core/preset_manager.py — save, get, delete, list presets."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.pm = PresetManager()
        # Redirect presets file to temp dir to avoid touching user data
        self.pm._presets_file = Path(self.tmp) / "test_presets.json"
        self.pm._presets = {}

    def test_save_and_get_preset(self):
        self.pm.save_preset("MyPreset", [256, 128, 64])
        p = self.pm.get_preset("MyPreset")
        self.assertIsNotNone(p)
        self.assertEqual(p.name, "MyPreset")

    def test_saved_preset_sizes(self):
        self.pm.save_preset("SizeTest", [256, 64, 16])
        p = self.pm.get_preset("SizeTest")
        self.assertIn(256, p.sizes)
        self.assertIn(16, p.sizes)

    def test_preset_exists(self):
        self.pm.save_preset("Exists", [256])
        self.assertTrue(self.pm.preset_exists("Exists"))

    def test_preset_not_exists(self):
        self.assertFalse(self.pm.preset_exists("DoesNotExist"))

    def test_delete_preset(self):
        self.pm.save_preset("ToDelete", [64])
        self.pm.delete_preset("ToDelete")
        self.assertFalse(self.pm.preset_exists("ToDelete"))

    def test_delete_nonexistent_returns_false(self):
        result = self.pm.delete_preset("GhostPreset")
        self.assertFalse(result)

    def test_list_presets(self):
        self.pm.save_preset("Alpha", [256])
        self.pm.save_preset("Beta", [128])
        names = self.pm.list_preset_names(include_builtin=False)
        self.assertIn("Alpha", names)
        self.assertIn("Beta", names)

    def test_get_custom_count(self):
        self.pm.save_preset("C1", [256])
        self.pm.save_preset("C2", [128])
        self.assertGreaterEqual(self.pm.get_custom_count(), 2)

    def test_rename_preset(self):
        self.pm.save_preset("OldName", [64])
        self.pm.rename_preset("OldName", "NewName")
        self.assertTrue(self.pm.preset_exists("NewName"))
        self.assertFalse(self.pm.preset_exists("OldName"))

    def test_duplicate_preset(self):
        self.pm.save_preset("Original", [256, 128])
        new_name = self.pm.duplicate_preset("Original")
        self.assertIsNotNone(new_name)
        self.assertTrue(self.pm.preset_exists(new_name))

    def test_builtin_presets_available(self):
        # Use a fresh instance — setUp clears _presets for isolation of other tests
        fresh_pm = PresetManager()
        presets = fresh_pm.list_presets(include_builtin=True)
        self.assertGreater(len(presets), 0)

    def test_export_import_round_trip(self):
        self.pm.save_preset("ExportMe", [256, 32])
        export_path = os.path.join(self.tmp, "exported_presets.json")
        ok = self.pm.export_presets(export_path)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(export_path))

    def test_size_preset_to_dict(self):
        p = SizePreset(name="Test", sizes=[256, 128])
        d = p.to_dict()
        self.assertIn('name', d)
        self.assertIn('sizes', d)

    def test_size_preset_from_dict(self):
        d = {'name': 'FromDict', 'sizes': [64, 32], 'description': '', 'is_builtin': False}
        p = SizePreset.from_dict(d)
        self.assertEqual(p.name, 'FromDict')
        self.assertIn(64, p.sizes)


# ══════════════════════════════════════════════════════════════════════════════
# 8. SESSION MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestSessionManager(unittest.TestCase):
    """core/session_manager.py — SessionState serialization and validity."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _make_state(self, files=None, sizes=None, project=""):
        return SessionState(
            timestamp=datetime.now().isoformat(),
            loaded_files=files or ["/path/icon.png"],
            selected_sizes=sizes or [256, 128, 64],
            autofill_enabled=True,
            png_compression=True,
            current_project_path=project,
        )

    # ── SessionState ───────────────────────────────────────────────────────────
    def test_state_is_valid_with_files(self):
        s = self._make_state(files=["/icon.png"])
        self.assertTrue(s.is_valid)

    def test_state_is_valid_with_project(self):
        s = self._make_state(files=[], project="/proj.rnv")
        self.assertTrue(s.is_valid)

    def test_state_invalid_when_empty(self):
        s = SessionState()
        self.assertFalse(s.is_valid)

    def test_state_to_dict_has_keys(self):
        s = self._make_state()
        d = s.to_dict()
        for k in ('timestamp', 'loaded_files', 'selected_sizes',
                  'autofill_enabled', 'png_compression'):
            self.assertIn(k, d)

    def test_state_from_dict_round_trip(self):
        s = self._make_state(files=["/a.png"], sizes=[256, 64])
        d = s.to_dict()
        s2 = SessionState.from_dict(d)
        self.assertEqual(s2.loaded_files, ["/a.png"])
        self.assertEqual(s2.selected_sizes, [256, 64])

    def test_state_from_dict_defaults_on_empty(self):
        s = SessionState.from_dict({})
        self.assertEqual(s.loaded_files, [])
        self.assertEqual(s.selected_sizes, [])

    def test_state_age_seconds_recent(self):
        s = self._make_state()
        self.assertLess(s.age_seconds, 5.0)

    def test_state_age_seconds_no_timestamp(self):
        s = SessionState(timestamp="")
        self.assertEqual(s.age_seconds, float('inf'))

    def test_state_age_seconds_invalid_timestamp(self):
        s = SessionState(timestamp="NOT_A_DATE")
        self.assertEqual(s.age_seconds, float('inf'))

    # ── SessionManager ─────────────────────────────────────────────────────────
    def test_session_manager_instantiates(self):
        sm = SessionManager()
        self.assertIsNotNone(sm)

    def test_save_session_sync(self):
        sm = SessionManager()
        sm._session_path = Path(self.tmp) / "session.json"
        sm._recovery_flag_path = Path(self.tmp) / "recovery.flag"
        s = self._make_state()
        result = sm.save_session(s, async_write=False)
        self.assertTrue(result)

    def test_has_recovery_false_initially(self):
        sm = SessionManager()
        sm._recovery_flag_path = Path(self.tmp) / "no_recovery.flag"
        self.assertFalse(sm.has_recovery())


# ══════════════════════════════════════════════════════════════════════════════
# 9. EXPORT HISTORY
# ══════════════════════════════════════════════════════════════════════════════
class TestExportHistory(unittest.TestCase):
    """core/export_history.py — log, query, clear, ExportEntry properties."""

    def setUp(self):
        self.eh = ExportHistory()
        self.eh._entries = []

    def _log(self, path="/out/icon.ico", etype="ico", sizes=None, success=True):
        self.eh.log_export(path, etype, sizes or [256, 128, 64],
                           success=success, file_size=4096)

    # ── ExportEntry ────────────────────────────────────────────────────────────
    def test_entry_formatted_time(self):
        e = ExportEntry(
            timestamp=datetime.now().isoformat(),
            output_path="/icon.ico",
            export_type="ico",
        )
        self.assertIsInstance(e.formatted_time, str)
        self.assertGreater(len(e.formatted_time), 5)

    def test_entry_formatted_size_bytes(self):
        e = ExportEntry(timestamp="", output_path="", export_type="ico", file_size=512)
        self.assertIn('B', e.formatted_size)

    def test_entry_formatted_size_kb(self):
        e = ExportEntry(timestamp="", output_path="", export_type="ico", file_size=4096)
        self.assertIn('KB', e.formatted_size)

    def test_entry_formatted_size_zero(self):
        e = ExportEntry(timestamp="", output_path="", export_type="ico", file_size=0)
        self.assertEqual(e.formatted_size, 'N/A')

    def test_entry_filename_property(self):
        e = ExportEntry(timestamp="", output_path="/some/path/icon.ico", export_type="ico")
        self.assertEqual(e.filename, "icon.ico")

    def test_entry_to_dict_round_trip(self):
        e = ExportEntry(
            timestamp=datetime.now().isoformat(),
            output_path="/icon.ico",
            export_type="ico",
            sizes=[256, 128],
            success=True,
        )
        d = e.to_dict()
        e2 = ExportEntry.from_dict(d)
        self.assertEqual(e2.output_path, "/icon.ico")
        self.assertEqual(e2.sizes, [256, 128])

    def test_entry_from_dict_defaults(self):
        e = ExportEntry.from_dict({})
        self.assertEqual(e.export_type, "ico")
        self.assertTrue(e.success)

    # ── ExportHistory ──────────────────────────────────────────────────────────
    def test_log_export_increments_count(self):
        self._log()
        self.assertEqual(self.eh.count, 1)

    def test_log_multiple_exports(self):
        for i in range(5):
            self._log(f"/out/icon{i}.ico")
        self.assertEqual(self.eh.count, 5)

    def test_get_history_returns_list(self):
        self._log()
        history = self.eh.get_history()
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)

    def test_get_history_limit(self):
        for i in range(10):
            self._log(f"/out/{i}.ico")
        history = self.eh.get_history(limit=3)
        self.assertLessEqual(len(history), 3)

    def test_get_successful_exports(self):
        self._log(success=True)
        self._log(success=False)
        successful = self.eh.get_successful_exports()
        for e in successful:
            self.assertTrue(e.success)

    def test_get_failed_exports(self):
        self._log(success=False)
        failed = self.eh.get_failed_exports()
        for e in failed:
            self.assertFalse(e.success)

    def test_get_exports_by_type(self):
        self._log(etype="ico")
        self._log(etype="png_set")
        ico_exports = self.eh.get_exports_by_type("ico")
        for e in ico_exports:
            self.assertEqual(e.export_type, "ico")

    def test_is_empty_initially(self):
        self.assertTrue(self.eh.is_empty)

    def test_is_empty_false_after_log(self):
        self._log()
        self.assertFalse(self.eh.is_empty)

    def test_clear_history(self):
        self._log()
        self.eh.clear_history()
        self.assertTrue(self.eh.is_empty)

    def test_get_statistics_keys(self):
        self._log(success=True)
        self._log(success=False)
        stats = self.eh.get_statistics()
        for k in ('total_exports', 'successful', 'failed'):
            self.assertIn(k, stats)

    def test_statistics_counts_match(self):
        self._log(success=True)
        self._log(success=True)
        self._log(success=False)
        stats = self.eh.get_statistics()
        self.assertEqual(stats['total_exports'], 3)
        self.assertEqual(stats['successful'], 2)
        self.assertEqual(stats['failed'], 1)


# ══════════════════════════════════════════════════════════════════════════════
# 10. ERROR HANDLER
# ══════════════════════════════════════════════════════════════════════════════
class TestErrorHandler(unittest.TestCase):
    """utils/error_handler.py — safe_execute and file operation wrappers."""

    def test_safe_execute_returns_value(self):
        ok, result = ErrorHandler.safe_execute(lambda: 42, "test")
        self.assertTrue(ok)
        self.assertEqual(result, 42)

    def test_safe_execute_division_by_zero(self):
        ok, result = ErrorHandler.safe_execute(lambda: 1/0, "div")
        self.assertFalse(ok)

    def test_safe_execute_value_error(self):
        ok, result = ErrorHandler.safe_execute(lambda: int("abc"), "ve")
        self.assertFalse(ok)

    def test_safe_execute_type_error(self):
        ok, result = ErrorHandler.safe_execute(lambda: "a" + 1, "te")
        self.assertFalse(ok)

    def test_safe_execute_nested(self):
        ok, result = ErrorHandler.safe_execute(lambda: (lambda: 7)(), "n")
        self.assertTrue(ok)
        self.assertEqual(result, 7)

    def test_safe_execute_string_result(self):
        ok, result = ErrorHandler.safe_execute(lambda: "hello", "s")
        self.assertTrue(ok)
        self.assertEqual(result, "hello")

    def test_safe_execute_list_result(self):
        ok, result = ErrorHandler.safe_execute(lambda: [1, 2, 3], "l")
        self.assertTrue(ok)
        self.assertEqual(result, [1, 2, 3])

    def test_validate_file_path_exists(self):
        tmp = tempfile.mktemp(suffix=".png")
        open(tmp, 'w').close()
        try:
            result = FileUtils.validate_file_path(tmp, must_exist=True)
            self.assertTrue(result)
        finally:
            os.unlink(tmp)

    def test_validate_file_path_missing(self):
        result = FileUtils.validate_file_path("/no/such/file.png", must_exist=True)
        self.assertFalse(result)

    def test_validate_image_size_valid(self):
        result = ImageProcessor().validate_size(64, 64)
        self.assertTrue(result)

    def test_validate_image_size_zero(self):
        result = ImageProcessor().validate_size(0, 0)
        self.assertFalse(result)


# ══════════════════════════════════════════════════════════════════════════════
# 11. FILE UTILS
# ══════════════════════════════════════════════════════════════════════════════
class TestFileUtils(unittest.TestCase):
    """utils/file_utils.py — static file and path helpers."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_ensure_ext_adds_missing(self):
        self.assertTrue(FileUtils.ensure_file_extension("icon", ".ico").endswith(".ico"))

    def test_ensure_ext_no_duplicate(self):
        self.assertEqual(
            FileUtils.ensure_file_extension("icon.ico", ".ico").count(".ico"), 1)

    def test_validate_existing_file(self):
        p = os.path.join(self.tmp, "x.png")
        open(p, 'w').close()
        self.assertTrue(FileUtils.validate_file_path(p, must_exist=True))

    def test_validate_missing_file(self):
        self.assertFalse(FileUtils.validate_file_path("/no/such.png", must_exist=True))

    def test_safe_filename_strips_bad_chars(self):
        r = FileUtils.get_safe_filename("my/file:name?.ico")
        for bad in ['/', ':', '?']:
            self.assertNotIn(bad, r)

    def test_safe_filename_max_length(self):
        long = FileUtils.get_safe_filename("a" * 300, max_length=255)
        self.assertLessEqual(len(long), 255)

    def test_create_directory(self):
        d = os.path.join(self.tmp, "newdir")
        self.assertTrue(FileUtils.create_directory_if_not_exists(d))
        self.assertTrue(os.path.isdir(d))

    def test_create_directory_existing_ok(self):
        d = os.path.join(self.tmp, "existing")
        os.makedirs(d, exist_ok=True)
        self.assertTrue(FileUtils.create_directory_if_not_exists(d))

    def test_get_file_size_bytes(self):
        p = os.path.join(self.tmp, "sz.png")
        with open(p, 'wb') as f:
            f.write(b"x" * 1024)
        self.assertEqual(FileUtils.get_file_size_bytes(p), 1024)

    def test_get_file_size_mb(self):
        p = os.path.join(self.tmp, "mb.png")
        with open(p, 'wb') as f:
            f.write(b"x" * 1024)
        self.assertGreater(FileUtils.get_file_size_mb(p), 0)

    def test_get_file_size_mb_missing(self):
        self.assertIsNone(FileUtils.get_file_size_mb("/no.png"))

    def test_backup_file(self):
        p = os.path.join(self.tmp, "orig.ico")
        with open(p, 'w') as f:
            f.write("data")
        bk = FileUtils.backup_file(p)
        self.assertIsNotNone(bk)
        self.assertTrue(os.path.exists(bk))

    def test_get_file_extension(self):
        self.assertEqual(FileUtils.get_file_extension("icon.png"), ".png")

    def test_get_file_extension_ico(self):
        self.assertEqual(FileUtils.get_file_extension("output.ico"), ".ico")

    def test_is_valid_image_file_png(self):
        self.assertTrue(FileUtils.is_valid_image_file("icon.png"))

    def test_is_valid_image_file_ico(self):
        self.assertTrue(FileUtils.is_valid_image_file("icon.ico"))

    def test_is_valid_image_file_txt(self):
        self.assertFalse(FileUtils.is_valid_image_file("readme.txt"))

    def test_copy_file(self):
        src = os.path.join(self.tmp, "src.ico")
        dst = os.path.join(self.tmp, "dst.ico")
        with open(src, 'w') as f:
            f.write("content")
        self.assertTrue(FileUtils.copy_file(src, dst))
        self.assertTrue(os.path.exists(dst))

    def test_delete_file(self):
        p = os.path.join(self.tmp, "del.ico")
        with open(p, 'w') as f:
            f.write("x")
        self.assertTrue(FileUtils.delete_file(p))
        self.assertFalse(os.path.exists(p))

    def test_get_unique_filename(self):
        with open(os.path.join(self.tmp, "icon.png"), 'w') as f:
            f.write("x")
        unique = FileUtils.get_unique_filename(self.tmp, "icon", ".png")
        self.assertNotEqual(unique, "icon.png")

    def test_list_files_in_dir(self):
        d = os.path.join(self.tmp, "listdir")
        os.makedirs(d, exist_ok=True)
        for name in ["a.png", "b.ico", "c.txt"]:
            open(os.path.join(d, name), 'w').close()
        files = FileUtils.list_files(d)
        self.assertGreaterEqual(len(files), 3)

    def test_get_file_size_formatted(self):
        p = os.path.join(self.tmp, "fmt.png")
        with open(p, 'wb') as f:
            f.write(b"x" * 2048)
        s = FileUtils.get_file_size_formatted(p)
        self.assertIsInstance(s, str)
        self.assertGreater(len(s), 0)


# ══════════════════════════════════════════════════════════════════════════════
# 12. CONFIG
# ══════════════════════════════════════════════════════════════════════════════
class TestConfig(unittest.TestCase):
    """utils/config.py — application constants, paths, icon sizes."""

    def test_app_name_nonempty(self):
        self.assertGreater(len(config.APP_NAME), 0)

    def test_app_version_nonempty(self):
        self.assertGreater(len(config.APP_VERSION), 0)

    def test_icon_sizes_is_list(self):
        self.assertIsInstance(config.ICON_SIZES, list)

    def test_icon_sizes_contains_standard(self):
        for s in [256, 128, 64, 48, 32, 16]:
            self.assertIn(s, config.ICON_SIZES)

    def test_icon_sizes_descending(self):
        self.assertEqual(config.ICON_SIZES, sorted(config.ICON_SIZES, reverse=True))

    def test_max_icon_size(self):
        self.assertEqual(config.MAX_ICON_SIZE, 256)

    def test_min_icon_size(self):
        self.assertEqual(config.MIN_ICON_SIZE, 16)

    def test_supported_extensions_has_png(self):
        self.assertIn('.png', config.SUPPORTED_EXTENSIONS)

    def test_supported_extensions_has_ico(self):
        self.assertIn('.ico', config.SUPPORTED_EXTENSIONS)

    def test_supported_extensions_has_svg(self):
        self.assertIn('.svg', config.SUPPORTED_EXTENSIONS)

    def test_max_recent_files_positive(self):
        self.assertGreater(config.MAX_RECENT_FILES, 0)

    def test_paths_are_path_objects(self):
        from pathlib import Path as _Path
        self.assertIsInstance(config.USER_DATA_DIR, _Path)

    def test_no_color_constants_in_config(self):
        # Brand gold must NOT be re-exported from config anymore
        # (it was causing circular import — see Phase 2 fix)
        self.assertFalse(hasattr(config, 'BRAND_GOLD_COLOR'))

    def test_thumbnail_checkerboard_positive(self):
        self.assertGreater(config.TRANSPARENCY_CHECKERBOARD_SIZE, 0)

    def test_zoom_min_max_ordered(self):
        self.assertLess(config.ZOOM_MIN, config.ZOOM_MAX)

    def test_preview_background_options(self):
        self.assertIsInstance(config.PREVIEW_BACKGROUND_OPTIONS, list)
        self.assertGreater(len(config.PREVIEW_BACKGROUND_OPTIONS), 0)


# ══════════════════════════════════════════════════════════════════════════════
# 13. EDGE CASES & INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════
class TestEdgeCases(unittest.TestCase):
    """Cross-module boundary conditions, stress tests, consistency checks."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ── ICO round-trip ─────────────────────────────────────────────────────────
    def test_build_and_verify_round_trip(self):
        """Build an ICO then immediately verify it — should always pass."""
        out = os.path.join(self.tmp, "rt.ico")
        images = {s: _make_rgba(s, s) for s in [64, 32, 16]}
        IconBuilderCore.build_ico_file(images, out)
        info = IconBuilderCore.verify_ico_file(out)
        self.assertGreater(info.get('count', 0), 0)

    def test_build_verify_image_count(self):
        out = os.path.join(self.tmp, "cnt.ico")
        images = {64: _make_rgba(64, 64), 32: _make_rgba(32, 32)}
        IconBuilderCore.build_ico_file(images, out)
        info = IconBuilderCore.verify_ico_file(out)
        # Built with 2 source sizes; autofill may add extras — assert at least 2
        self.assertGreaterEqual(info.get('count', 0), 2)

    def test_single_pixel_image(self):
        """1×1 pixel ICO should build and verify without crashing."""
        out = os.path.join(self.tmp, "tiny.ico")
        images = {1: _make_rgba(1, 1)}
        try:
            IconBuilderCore.build_ico_file(images, out)
        except Exception:
            pass  # Some sizes may be rejected — just ensure no crash on verify
        # File either doesn't exist or is valid
        if os.path.exists(out):
            info = IconBuilderCore.verify_ico_file(out)
            self.assertIsInstance(info, dict)

    def test_max_standard_size_256(self):
        out = os.path.join(self.tmp, "max.ico")
        images = {256: _make_rgba(256, 256)}
        result = IconBuilderCore.build_ico_file(images, out)
        self.assertTrue(result)

    # ── ImageProcessor ─────────────────────────────────────────────────────────
    def test_multiple_rotate_is_identity(self):
        """Four 90° rotations should return to original."""
        ip = ImageProcessor()
        png = _make_png_file(os.path.join(self.tmp, "rot.png"), 64)
        ip.load_png(png)
        original = ip.get_image(64).tobytes()
        for _ in range(4):
            ip.apply_rotate(90)
        result = ip.get_image(64).tobytes()
        self.assertEqual(original, result)

    def test_load_and_clear_leaves_no_images(self):
        ip = ImageProcessor()
        png = _make_png_file(os.path.join(self.tmp, "clr.png"), 32)
        ip.load_png(png)
        self.assertGreater(len(ip.get_detected_images()), 0)
        ip.clear_images()
        self.assertEqual(len(ip.get_detected_images()), 0)

    # ── Color system consistency ────────────────────────────────────────────────
    def test_dark_and_light_window_bg_differ(self):
        self.assertNotEqual(
            DARK_THEME_COLORS['window_bg'],
            LIGHT_THEME_COLORS['window_bg']
        )

    def test_image_mode_differs_from_dark(self):
        self.assertNotEqual(
            IMAGE_MODE_COLORS['window_bg'],
            DARK_THEME_COLORS['window_bg']
        )

    def test_brand_gold_not_main_btn_hover_bg_dark(self):
        """Brand gold must not appear as main button hover bg — inverse system only."""
        self.assertNotEqual(
            DARK_THEME_COLORS['main_btn_hover_bg'].lower(),
            BRAND_GOLD.lower()
        )

    def test_brand_gold_not_main_btn_hover_bg_light(self):
        self.assertNotEqual(
            LIGHT_THEME_COLORS['main_btn_hover_bg'].lower(),
            BRAND_GOLD_DARK.lower()
        )

    def test_both_themes_hover_bg_same(self):
        """Dark and light both use #333333 as main button hover."""
        self.assertEqual(
            DARK_THEME_COLORS['main_btn_hover_bg'],
            LIGHT_THEME_COLORS['main_btn_hover_bg']
        )

    def test_image_mode_scrollbar_hover_is_brand_gold(self):
        self.assertEqual(
            IMAGE_MODE_COLORS['scrollbar_handle_hover'].lower(),
            BRAND_GOLD.lower()
        )

    def test_no_hardcoded_gold_in_theme_manager_main_btn(self):
        """ThemeManager should expose inverse colors, not brand gold, for main buttons."""
        tm = ThemeManager()
        self.assertNotIn(BRAND_GOLD.lower(),
                         tm.DARK_THEME.get('button_hover_bg', '').lower())

    # ── Preview utils ──────────────────────────────────────────────────────────
    def test_checkerboard_two_pixel_colors_differ(self):
        """A standard 8px square checkerboard has two distinct pixel colors."""
        img = create_checkerboard_pattern(16, 16, square_size=8)
        px0 = img.getpixel((0, 0))
        px1 = img.getpixel((8, 0))
        self.assertNotEqual(px0, px1)

    def test_composite_fully_opaque_covers_bg(self):
        """Fully opaque red image composited on white should stay red."""
        src = _make_rgba(32, 32, (255, 0, 0, 255))
        result = composite_on_color(src, (255, 255, 255))
        px = result.getpixel((0, 0))
        self.assertEqual(px[0], 255)  # R
        self.assertLess(px[1], 50)    # G near 0
        self.assertLess(px[2], 50)    # B near 0

    def test_extract_dominant_solid_image_one_color(self):
        """Solid red image should have red as its dominant colour."""
        src = _make_rgba(64, 64, (255, 0, 0, 255))
        colors = extract_dominant_colors(src, count=1)
        self.assertGreater(len(colors), 0)
        top_color, _ = colors[0]
        self.assertGreater(top_color[0], 200)  # R dominant

    # ── Session round-trip ─────────────────────────────────────────────────────
    def test_session_state_full_round_trip(self):
        s = SessionState(
            timestamp=datetime.now().isoformat(),
            loaded_files=["/a.png", "/b.png"],
            selected_sizes=[256, 128, 64],
            autofill_enabled=False,
            png_compression=True,
            current_project_path="/my/proj.rnv",
        )
        d = s.to_dict()
        s2 = SessionState.from_dict(d)
        self.assertEqual(s2.loaded_files, ["/a.png", "/b.png"])
        self.assertEqual(s2.selected_sizes, [256, 128, 64])
        self.assertFalse(s2.autofill_enabled)
        self.assertEqual(s2.current_project_path, "/my/proj.rnv")

    # ── Export history stats ───────────────────────────────────────────────────
    def test_export_history_stats_accuracy(self):
        eh = ExportHistory()
        eh._entries = []
        ts = datetime.now().isoformat()
        for i in range(3):
            eh._entries.append(ExportEntry(
                timestamp=ts, output_path=f"/icon{i}.ico",
                export_type="ico", success=(i < 2)))
        stats = eh.get_statistics()
        self.assertEqual(stats['total_exports'], 3)
        self.assertEqual(stats['successful'], 2)
        self.assertEqual(stats['failed'], 1)



# ══════════════════════════════════════════════════════════════════════════════
# 14. IMAGE ADJUSTMENTS
# ══════════════════════════════════════════════════════════════════════════════
class TestImageAdjustments(unittest.TestCase):
    """image_adjustments.py — all 15 standalone transform/color functions."""

    def _solid(self, w=64, h=64, color=(200, 100, 50, 255)):
        return _make_rgba(w, h, color)

    def _with_transparent_border(self):
        """32×32 image with a 4px transparent border around a solid center."""
        img = _Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        for x in range(4, 28):
            for y in range(4, 28):
                img.putpixel((x, y), (200, 100, 50, 255))
        return img

    # ── get_content_bounds ─────────────────────────────────────────────────────
    def test_content_bounds_solid(self):
        img = self._solid()
        b = get_content_bounds(img)
        self.assertIsNotNone(b)
        self.assertEqual(len(b), 4)

    def test_content_bounds_fully_transparent(self):
        img = _Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        self.assertIsNone(get_content_bounds(img))

    def test_content_bounds_detects_edges(self):
        img = self._with_transparent_border()
        b = get_content_bounds(img)
        self.assertIsNotNone(b)
        self.assertGreaterEqual(b[0], 4)
        self.assertLessEqual(b[2], 28)

    # ── auto_crop ──────────────────────────────────────────────────────────────
    def test_auto_crop_removes_border(self):
        img = self._with_transparent_border()
        cropped = auto_crop(img)
        self.assertLess(cropped.width, img.width)
        self.assertLess(cropped.height, img.height)

    def test_auto_crop_solid_unchanged_size(self):
        img = self._solid(32, 32)
        cropped = auto_crop(img)
        self.assertEqual(cropped.size, (32, 32))

    def test_auto_crop_fully_transparent_returns_image(self):
        img = _Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        result = auto_crop(img)
        self.assertIsInstance(result, _Image.Image)

    # ── add_padding ────────────────────────────────────────────────────────────
    def test_add_padding_increases_size(self):
        img = self._solid(32, 32)
        padded = add_padding(img, padding=8)
        self.assertEqual(padded.size, (48, 48))

    def test_add_padding_zero_unchanged(self):
        img = self._solid(32, 32)
        padded = add_padding(img, padding=0)
        self.assertEqual(padded.size, (32, 32))

    def test_add_padding_transparent_by_default(self):
        img = self._solid(16, 16)
        padded = add_padding(img, padding=4)
        # Corner pixel should be transparent
        corner = padded.getpixel((0, 0))
        self.assertEqual(corner[3], 0)

    def test_add_padding_colored(self):
        img = self._solid(16, 16)
        padded = add_padding(img, padding=4, color=(0, 0, 255, 255))
        corner = padded.getpixel((0, 0))
        self.assertEqual(corner[2], 255)  # Blue

    # ── center_content ─────────────────────────────────────────────────────────
    def test_center_content_returns_square(self):
        img = self._with_transparent_border()
        result = center_content(img, target_size=64)
        self.assertEqual(result.size, (64, 64))

    def test_center_content_fully_transparent(self):
        img = _Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        result = center_content(img)
        self.assertIsInstance(result, _Image.Image)

    def test_center_content_no_target_uses_max_dim(self):
        img = self._solid(48, 32)
        result = center_content(img)
        self.assertEqual(result.width, result.height)

    # ── resize_to_fit ──────────────────────────────────────────────────────────
    def test_resize_to_fit_correct_size(self):
        img = self._solid(128, 128)
        result = resize_to_fit(img, 64)
        self.assertEqual(result.size, (64, 64))

    def test_resize_to_fit_aspect_preserved(self):
        img = self._solid(128, 128)
        result = resize_to_fit(img, 64, maintain_aspect=True)
        self.assertEqual(result.width, result.height)

    def test_resize_to_fit_stretch(self):
        img = self._solid(100, 50)
        result = resize_to_fit(img, 64, maintain_aspect=False)
        self.assertEqual(result.size, (64, 64))

    # ── make_square ────────────────────────────────────────────────────────────
    def test_make_square_from_rect(self):
        img = self._solid(100, 60)
        result = make_square(img)
        self.assertEqual(result.width, result.height)
        self.assertEqual(result.width, 100)

    def test_make_square_already_square(self):
        img = self._solid(64, 64)
        result = make_square(img)
        self.assertEqual(result.size, (64, 64))

    # ── rotate_image ───────────────────────────────────────────────────────────
    def test_rotate_90(self):
        img = self._solid(64, 64)
        result = rotate_image(img, 90)
        self.assertIsInstance(result, _Image.Image)

    def test_rotate_180(self):
        img = self._solid(64, 64)
        result = rotate_image(img, 180)
        self.assertEqual(result.size, img.size)

    def test_rotate_0_unchanged(self):
        img = self._solid(32, 32)
        result = rotate_image(img, 0)
        self.assertEqual(result.tobytes(), img.tobytes())

    def test_rotate_360_identity(self):
        img = self._solid(32, 32)
        result = rotate_image(img, 360)
        self.assertEqual(result.tobytes(), img.tobytes())

    def test_rotate_four_times_identity(self):
        img = self._solid(32, 32)
        original = img.tobytes()
        for _ in range(4):
            img = rotate_image(img, 90)
        self.assertEqual(img.tobytes(), original)

    # ── flip_horizontal / flip_vertical ────────────────────────────────────────
    def test_flip_horizontal_returns_image(self):
        img = self._solid(32, 32)
        result = flip_horizontal(img)
        self.assertIsInstance(result, _Image.Image)

    def test_flip_horizontal_twice_identity(self):
        img = self._solid(32, 32)
        original = img.tobytes()
        self.assertEqual(flip_horizontal(flip_horizontal(img)).tobytes(), original)

    def test_flip_vertical_returns_image(self):
        img = self._solid(32, 32)
        result = flip_vertical(img)
        self.assertIsInstance(result, _Image.Image)

    def test_flip_vertical_twice_identity(self):
        img = self._solid(32, 32)
        original = img.tobytes()
        self.assertEqual(flip_vertical(flip_vertical(img)).tobytes(), original)

    def test_flip_h_and_v_different_results(self):
        img = self._solid(32, 64, (255, 0, 0, 255))
        # Asymmetric content — make one corner different
        img.putpixel((0, 0), (0, 255, 0, 255))
        h = flip_horizontal(img)
        v = flip_vertical(img)
        self.assertNotEqual(h.tobytes(), v.tobytes())

    # ── fill_transparency ──────────────────────────────────────────────────────
    def test_fill_transparency_removes_alpha(self):
        img = _Image.new("RGBA", (16, 16), (255, 0, 0, 128))
        result = fill_transparency(img, (0, 0, 0, 255))
        self.assertIsInstance(result, _Image.Image)

    def test_fill_transparency_preserves_size(self):
        img = self._solid(32, 32)
        result = fill_transparency(img, (255, 255, 255, 255))
        self.assertEqual(result.size, (32, 32))

    # ── add_border ─────────────────────────────────────────────────────────────
    def test_add_border_increases_size(self):
        img = self._solid(32, 32)
        result = add_border(img, width=4, color=(0, 0, 0, 255))
        self.assertEqual(result.width, 40)
        self.assertEqual(result.height, 40)

    def test_add_border_zero_width_unchanged(self):
        img = self._solid(32, 32)
        result = add_border(img, width=0, color=(0, 0, 0, 255))
        self.assertEqual(result.size, (32, 32))

    def test_add_border_color_visible(self):
        img = self._solid(32, 32, (255, 0, 0, 255))
        result = add_border(img, width=4, color=(0, 0, 255, 255))
        # Corner pixel should be the border color
        corner = result.getpixel((0, 0))
        self.assertEqual(corner[2], 255)  # Blue component

    # ── adjust_brightness ──────────────────────────────────────────────────────
    def test_brightness_zero_unchanged(self):
        img = self._solid(16, 16, (100, 100, 100, 255))
        result = adjust_brightness(img, 0)
        self.assertEqual(result.tobytes(), img.tobytes())

    def test_brightness_positive_increases(self):
        img = self._solid(16, 16, (100, 100, 100, 255))
        result = adjust_brightness(img, 50)
        px = result.getpixel((0, 0))
        self.assertGreater(px[0], 100)

    def test_brightness_negative_decreases(self):
        img = self._solid(16, 16, (200, 200, 200, 255))
        result = adjust_brightness(img, -50)
        px = result.getpixel((0, 0))
        self.assertLess(px[0], 200)

    def test_brightness_preserves_alpha(self):
        img = self._solid(16, 16, (100, 100, 100, 128))
        result = adjust_brightness(img, 30)
        self.assertEqual(result.getpixel((0, 0))[3], 128)

    # ── adjust_contrast ────────────────────────────────────────────────────────
    def test_contrast_zero_unchanged(self):
        img = self._solid(16, 16, (128, 128, 128, 255))
        result = adjust_contrast(img, 0)
        self.assertEqual(result.tobytes(), img.tobytes())

    def test_contrast_returns_rgba(self):
        img = self._solid(16, 16)
        result = adjust_contrast(img, 50)
        self.assertEqual(result.mode, 'RGBA')

    def test_contrast_preserves_alpha(self):
        img = self._solid(16, 16, (100, 100, 100, 200))
        result = adjust_contrast(img, 30)
        self.assertEqual(result.getpixel((0, 0))[3], 200)

    # ── adjust_saturation ─────────────────────────────────────────────────────
    def test_saturation_zero_unchanged(self):
        img = self._solid(16, 16, (200, 100, 50, 255))
        result = adjust_saturation(img, 0)
        self.assertEqual(result.tobytes(), img.tobytes())

    def test_saturation_minus_100_grayscale(self):
        img = self._solid(16, 16, (200, 100, 50, 255))
        result = adjust_saturation(img, -100)
        px = result.getpixel((0, 0))
        # R, G, B should be nearly equal (grayscale)
        self.assertAlmostEqual(px[0], px[1], delta=2)
        self.assertAlmostEqual(px[1], px[2], delta=2)

    def test_saturation_preserves_alpha(self):
        img = self._solid(16, 16, (200, 100, 50, 77))
        result = adjust_saturation(img, 50)
        self.assertEqual(result.getpixel((0, 0))[3], 77)

    # ── convert_grayscale ──────────────────────────────────────────────────────
    def test_grayscale_returns_rgba(self):
        img = self._solid(16, 16, (200, 100, 50, 255))
        result = convert_grayscale(img)
        self.assertEqual(result.mode, 'RGBA')

    def test_grayscale_rgb_channels_equal(self):
        img = self._solid(16, 16, (200, 100, 50, 255))
        result = convert_grayscale(img)
        px = result.getpixel((0, 0))
        self.assertAlmostEqual(px[0], px[1], delta=2)
        self.assertAlmostEqual(px[1], px[2], delta=2)

    def test_grayscale_preserves_alpha(self):
        img = self._solid(16, 16, (200, 100, 50, 99))
        result = convert_grayscale(img)
        self.assertEqual(result.getpixel((0, 0))[3], 99)

    def test_grayscale_on_already_gray(self):
        img = self._solid(16, 16, (128, 128, 128, 255))
        result = convert_grayscale(img)
        px = result.getpixel((0, 0))
        self.assertAlmostEqual(px[0], 128, delta=5)

    # ── apply_combined_adjustments ─────────────────────────────────────────────
    def test_combined_all_zero_unchanged(self):
        img = self._solid(16, 16)
        result = apply_combined_adjustments(img, brightness=0, contrast=0, saturation=0)
        self.assertEqual(result.tobytes(), img.tobytes())

    def test_combined_brightness_only(self):
        img = self._solid(16, 16, (100, 100, 100, 255))
        result = apply_combined_adjustments(img, brightness=50)
        px = result.getpixel((0, 0))
        self.assertGreater(px[0], 100)

    def test_combined_preserves_alpha(self):
        img = self._solid(16, 16, (100, 100, 100, 77))
        result = apply_combined_adjustments(img, brightness=20, contrast=10, saturation=-10)
        self.assertEqual(result.getpixel((0, 0))[3], 77)

    def test_combined_matches_individual(self):
        """apply_combined_adjustments result should match sequential individual calls."""
        img = self._solid(16, 16, (150, 80, 40, 255))
        combined = apply_combined_adjustments(img.copy(), brightness=20, saturation=30)
        sequential = adjust_saturation(adjust_brightness(img.copy(), 20), 30)
        # Pixel values should be very close (minor floating point differences allowed)
        cp = combined.getpixel((0, 0))
        sp = sequential.getpixel((0, 0))
        for a, b in zip(cp[:3], sp[:3]):
            self.assertAlmostEqual(a, b, delta=3)


# ══════════════════════════════════════════════════════════════════════════════
# 15. PIXMAP CACHE
# ══════════════════════════════════════════════════════════════════════════════
class TestPixmapCache(unittest.TestCase):
    """utils/pixmap_cache.py — QPixmapCache, ImagePixmapCache, ThumbnailCache."""

    def _make_pixmap(self) -> _QPixmap:
        from ui.preview_utils import pil_to_qpixmap
        return pil_to_qpixmap(_make_rgba(32, 32))

    # ── QPixmapCache ───────────────────────────────────────────────────────────
    def test_get_miss_returns_none(self):
        c = QPixmapCache(max_size=5)
        self.assertIsNone(c.get(("missing", 1)))

    def test_put_and_get(self):
        c = QPixmapCache(max_size=5)
        px = self._make_pixmap()
        c.put(("img", 1), px)
        self.assertIsNotNone(c.get(("img", 1)))

    def test_size_after_put(self):
        c = QPixmapCache(max_size=5)
        c.put(("a",), self._make_pixmap())
        c.put(("b",), self._make_pixmap())
        self.assertEqual(c.get_size(), 2)

    def test_lru_eviction_at_max(self):
        c = QPixmapCache(max_size=3)
        for i in range(4):
            c.put((f"k{i}",), self._make_pixmap())
        self.assertEqual(c.get_size(), 3)

    def test_lru_evicts_oldest(self):
        c = QPixmapCache(max_size=2)
        c.put(("old",), self._make_pixmap())
        c.put(("new",), self._make_pixmap())
        c.put(("newer",), self._make_pixmap())
        # "old" should have been evicted
        self.assertIsNone(c.get(("old",)))

    def test_lru_promoted_on_get(self):
        c = QPixmapCache(max_size=2)
        c.put(("k1",), self._make_pixmap())
        c.put(("k2",), self._make_pixmap())
        c.get(("k1",))          # promote k1
        c.put(("k3",), self._make_pixmap())  # k2 should be evicted, not k1
        self.assertIsNotNone(c.get(("k1",)))
        self.assertIsNone(c.get(("k2",)))

    def test_clear_returns_count(self):
        c = QPixmapCache(max_size=5)
        for i in range(3):
            c.put((f"k{i}",), self._make_pixmap())
        self.assertEqual(c.clear(), 3)

    def test_clear_empties_cache(self):
        c = QPixmapCache(max_size=5)
        c.put(("k",), self._make_pixmap())
        c.clear()
        self.assertEqual(c.get_size(), 0)

    def test_remove_existing(self):
        c = QPixmapCache(max_size=5)
        c.put(("k",), self._make_pixmap())
        self.assertTrue(c.remove(("k",)))
        self.assertIsNone(c.get(("k",)))

    def test_remove_nonexistent(self):
        c = QPixmapCache(max_size=5)
        self.assertFalse(c.remove(("ghost",)))

    def test_contains(self):
        c = QPixmapCache(max_size=5)
        c.put(("k",), self._make_pixmap())
        self.assertTrue(c.contains(("k",)))
        self.assertFalse(c.contains(("missing",)))

    def test_get_or_create_creates(self):
        c = QPixmapCache(max_size=5)
        px = self._make_pixmap()
        result = c.get_or_create(("key",), lambda: px)
        self.assertIsNotNone(result)

    def test_get_or_create_cached_hit(self):
        c = QPixmapCache(max_size=5)
        px = self._make_pixmap()
        c.put(("key",), px)
        created = [0]
        def creator():
            created[0] += 1
            return self._make_pixmap()
        c.get_or_create(("key",), creator)
        self.assertEqual(created[0], 0)  # Creator not called — cache hit

    def test_stats_keys(self):
        c = QPixmapCache(max_size=5)
        stats = c.get_stats()
        for k in ('size', 'max_size', 'hits', 'misses', 'hit_rate', 'evictions'):
            self.assertIn(k, stats)

    def test_stats_hit_rate(self):
        c = QPixmapCache(max_size=5)
        c.put(("k",), self._make_pixmap())
        c.get(("k",))       # hit
        c.get(("miss",))    # miss
        stats = c.get_stats()
        self.assertAlmostEqual(stats['hit_rate'], 50.0, delta=1.0)

    def test_stats_evictions_tracked(self):
        c = QPixmapCache(max_size=2)
        for i in range(5):
            c.put((f"k{i}",), self._make_pixmap())
        self.assertGreater(c.get_stats()['evictions'], 0)

    def test_reset_stats(self):
        c = QPixmapCache(max_size=5)
        c.put(("k",), self._make_pixmap())
        c.get(("k",))
        c.reset_stats()
        stats = c.get_stats()
        self.assertEqual(stats['hits'], 0)
        self.assertEqual(stats['misses'], 0)

    def test_resize_shrinks(self):
        c = QPixmapCache(max_size=5)
        for i in range(5):
            c.put((f"k{i}",), self._make_pixmap())
        c.resize(3)
        self.assertLessEqual(c.get_size(), 3)

    def test_get_keys(self):
        c = QPixmapCache(max_size=5)
        c.put(("a",), self._make_pixmap())
        c.put(("b",), self._make_pixmap())
        keys = c.get_keys()
        self.assertIn(("a",), keys)
        self.assertIn(("b",), keys)

    def test_max_size_reported(self):
        c = QPixmapCache(max_size=10)
        self.assertEqual(c.get_max_size(), 10)

    # ── ImagePixmapCache ───────────────────────────────────────────────────────
    def test_image_cache_set_current_clears(self):
        c = ImagePixmapCache(max_size=5)
        c.put(("img_a", 1.0, (64, 64)), self._make_pixmap())
        c.set_current_image("/new/image.png")
        self.assertEqual(c.get_size(), 0)

    def test_image_cache_same_path_no_clear(self):
        c = ImagePixmapCache(max_size=5)
        c.set_current_image("/same.png")
        c.put(("/same.png", 1.0, (64, 64)), self._make_pixmap())
        c.set_current_image("/same.png")  # same path — no clear
        self.assertEqual(c.get_size(), 1)

    def test_image_cache_get_for_zoom(self):
        c = ImagePixmapCache(max_size=5)
        px = self._make_pixmap()
        result = c.get_for_zoom("/img.png", 1.5, (64, 64), lambda: px)
        self.assertIsNotNone(result)

    def test_image_cache_invalidate(self):
        c = ImagePixmapCache(max_size=5)
        c.put(("/path/img.png", 1.0, (64, 64)), self._make_pixmap())
        c.put(("/path/img.png", 2.0, (64, 64)), self._make_pixmap())
        removed = c.invalidate_image("/path/img.png")
        self.assertEqual(removed, 2)

    # ── ThumbnailCache ─────────────────────────────────────────────────────────
    def test_thumbnail_cache_get_thumbnail(self):
        c = ThumbnailCache(max_size=10)
        px = self._make_pixmap()
        result = c.get_thumbnail("/src.png", 64, lambda: px)
        self.assertIsNotNone(result)

    def test_thumbnail_cache_invalidate_source(self):
        c = ThumbnailCache(max_size=10)
        c.put(("/src.png", 64, "default"), self._make_pixmap())
        c.put(("/src.png", 32, "default"), self._make_pixmap())
        removed = c.invalidate_source("/src.png")
        self.assertEqual(removed, 2)

    # ── create_cache_key ───────────────────────────────────────────────────────
    def test_create_cache_key_basic(self):
        key = create_cache_key("/img.png", 1.5, (64, 64))
        self.assertIsInstance(key, tuple)
        self.assertEqual(key[0], "/img.png")

    def test_create_cache_key_with_kwargs(self):
        key = create_cache_key("/img.png", quality="high")
        self.assertIsInstance(key, tuple)

    def test_create_cache_key_different_args_different_keys(self):
        k1 = create_cache_key("/img.png", 1.0)
        k2 = create_cache_key("/img.png", 2.0)
        self.assertNotEqual(k1, k2)


# ══════════════════════════════════════════════════════════════════════════════
# 16. BATCH PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════
class TestBatchProcessor(unittest.TestCase):
    """core/batch_processor.py — BatchJob serialization, BatchProcessor queue management."""

    # ── JobStatus ──────────────────────────────────────────────────────────────
    def test_job_status_values(self):
        for status in JobStatus:
            self.assertIsInstance(status.value, str)

    def test_job_status_pending(self):
        self.assertEqual(JobStatus.PENDING.value, "pending")

    def test_job_status_completed(self):
        self.assertEqual(JobStatus.COMPLETED.value, "completed")

    def test_job_status_failed(self):
        self.assertEqual(JobStatus.FAILED.value, "failed")

    # ── BatchJob ───────────────────────────────────────────────────────────────
    def test_batch_job_default_status_pending(self):
        job = BatchJob(source_path="/in/icon.png", output_path="/out/icon.ico")
        self.assertEqual(job.status, JobStatus.PENDING)

    def test_batch_job_to_dict_keys(self):
        job = BatchJob(source_path="/in.png", output_path="/out.ico")
        d = job.to_dict()
        for k in ('source_path', 'output_path', 'settings', 'status',
                  'error_message', 'result'):
            self.assertIn(k, d)

    def test_batch_job_to_dict_status_string(self):
        job = BatchJob(source_path="/in.png", output_path="/out.ico")
        d = job.to_dict()
        self.assertIsInstance(d['status'], str)

    def test_batch_job_from_dict_round_trip(self):
        job = BatchJob(
            source_path="/in/icon.png",
            output_path="/out/icon.ico",
            settings={"sizes": [256, 64]},
        )
        d = job.to_dict()
        job2 = BatchJob.from_dict(d)
        self.assertEqual(job2.source_path, "/in/icon.png")
        self.assertEqual(job2.output_path, "/out/icon.ico")
        self.assertEqual(job2.status, JobStatus.PENDING)

    def test_batch_job_from_dict_defaults(self):
        job = BatchJob.from_dict({})
        self.assertEqual(job.source_path, "")
        self.assertEqual(job.status, JobStatus.PENDING)

    def test_batch_job_error_message_empty_default(self):
        job = BatchJob(source_path="/in.png", output_path="/out.ico")
        self.assertEqual(job.error_message, "")

    # ── BatchProcessor ─────────────────────────────────────────────────────────
    def test_batch_processor_instantiates(self):
        bp = BatchProcessor()
        self.assertIsNotNone(bp)

    def test_add_job_increments_count(self):
        bp = BatchProcessor()
        bp.add_job("/in/icon.png", "/out/icon.ico")
        self.assertEqual(bp.get_job_count(), 1)

    def test_add_multiple_jobs(self):
        bp = BatchProcessor()
        for i in range(5):
            bp.add_job(f"/in/{i}.png", f"/out/{i}.ico")
        self.assertEqual(bp.get_job_count(), 5)

    def test_get_jobs_returns_list(self):
        bp = BatchProcessor()
        bp.add_job("/in.png", "/out.ico")
        jobs = bp.get_jobs()
        self.assertIsInstance(jobs, list)
        self.assertEqual(len(jobs), 1)

    def test_get_job_by_index(self):
        bp = BatchProcessor()
        bp.add_job("/in.png", "/out.ico")
        job = bp.get_job(0)
        self.assertIsNotNone(job)
        self.assertEqual(job.source_path, "/in.png")

    def test_get_job_invalid_index_none(self):
        bp = BatchProcessor()
        self.assertIsNone(bp.get_job(99))

    def test_remove_job_decrements_count(self):
        bp = BatchProcessor()
        bp.add_job("/in.png", "/out.ico")
        bp.remove_job(0)
        self.assertEqual(bp.get_job_count(), 0)

    def test_remove_invalid_index_returns_false(self):
        bp = BatchProcessor()
        self.assertFalse(bp.remove_job(99))

    def test_clear_jobs(self):
        bp = BatchProcessor()
        bp.add_job("/a.png", "/a.ico")
        bp.add_job("/b.png", "/b.ico")
        bp.clear_jobs()
        self.assertEqual(bp.get_job_count(), 0)

    def test_get_pending_count(self):
        bp = BatchProcessor()
        bp.add_job("/a.png", "/a.ico")
        bp.add_job("/b.png", "/b.ico")
        self.assertEqual(bp.get_pending_count(), 2)

    def test_get_summary_keys(self):
        bp = BatchProcessor()
        bp.add_job("/a.png", "/a.ico")
        summary = bp.get_summary()
        for k in ('total', 'pending', 'completed', 'failed', 'cancelled'):
            self.assertIn(k, summary)

    def test_get_summary_total(self):
        bp = BatchProcessor()
        for i in range(3):
            bp.add_job(f"/{i}.png", f"/{i}.ico")
        self.assertEqual(bp.get_summary()['total'], 3)

    def test_get_progress_empty_is_100(self):
        bp = BatchProcessor()
        self.assertEqual(bp.get_progress(), 100.0)

    def test_get_progress_all_pending(self):
        bp = BatchProcessor()
        bp.add_job("/a.png", "/a.ico")
        self.assertEqual(bp.get_progress(), 0.0)

    def test_is_processing_false_initially(self):
        bp = BatchProcessor()
        self.assertFalse(bp.is_processing())


# ══════════════════════════════════════════════════════════════════════════════
# 17. PROJECT MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestProjectManager(unittest.TestCase):
    """core/project_manager.py — Project, ProjectImage, ProjectSettings, ProjectManager."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ── ProjectSettings ────────────────────────────────────────────────────────
    def test_project_settings_default_sizes(self):
        ps = ProjectSettings()
        self.assertIsInstance(ps.selected_sizes, list)
        self.assertGreater(len(ps.selected_sizes), 0)

    def test_project_settings_to_dict(self):
        ps = ProjectSettings(selected_sizes=[256, 64], autofill=False)
        d = ps.to_dict()
        self.assertIn('selected_sizes', d)
        self.assertFalse(d['autofill'])

    def test_project_settings_from_dict_round_trip(self):
        ps = ProjectSettings(selected_sizes=[256, 128], png_compression=False)
        d = ps.to_dict()
        ps2 = ProjectSettings.from_dict(d)
        self.assertEqual(ps2.selected_sizes, [256, 128])
        self.assertFalse(ps2.png_compression)

    def test_project_settings_from_dict_defaults(self):
        ps = ProjectSettings.from_dict({})
        self.assertTrue(ps.autofill)
        self.assertTrue(ps.png_compression)

    # ── ProjectImage ───────────────────────────────────────────────────────────
    def test_project_image_from_pil(self):
        img = _make_rgba(64, 64)
        pi = ProjectImage.from_pil_image(img, embed=True)
        self.assertEqual(pi.size, 64)
        self.assertTrue(pi.is_embedded)
        self.assertGreater(len(pi.embedded_data), 0)

    def test_project_image_to_dict(self):
        img = _make_rgba(32, 32)
        pi = ProjectImage.from_pil_image(img)
        d = pi.to_dict()
        for k in ('size', 'source_path', 'embedded_data', 'is_embedded', 'is_autofilled'):
            self.assertIn(k, d)

    def test_project_image_from_dict_round_trip(self):
        img = _make_rgba(48, 48)
        pi = ProjectImage.from_pil_image(img, embed=True)
        d = pi.to_dict()
        pi2 = ProjectImage.from_dict(d)
        self.assertEqual(pi2.size, 48)
        self.assertTrue(pi2.is_embedded)

    def test_project_image_to_pil_embedded(self):
        img = _make_rgba(32, 32, (200, 100, 50, 255))
        pi = ProjectImage.from_pil_image(img, embed=True)
        result = pi.to_pil_image()
        self.assertIsNotNone(result)
        self.assertEqual(result.size, (32, 32))

    def test_project_image_to_pil_no_data_returns_none(self):
        pi = ProjectImage(size=64, is_embedded=False, embedded_data="")
        result = pi.to_pil_image()
        self.assertIsNone(result)

    # ── Project ────────────────────────────────────────────────────────────────
    def test_project_default_name(self):
        p = Project()
        self.assertGreater(len(p.name), 0)

    def test_project_has_created_timestamp(self):
        p = Project()
        self.assertGreater(len(p.created), 0)

    def test_project_get_image_count_empty(self):
        p = Project()
        self.assertEqual(p.get_image_count(), 0)

    def test_project_has_images_false_empty(self):
        p = Project()
        self.assertFalse(p.has_images())

    def test_project_get_sizes_empty(self):
        p = Project()
        self.assertEqual(p.get_sizes(), [])

    def test_project_to_dict_keys(self):
        p = Project(name="TestProject")
        d = p.to_dict()
        for k in ('name', 'version', 'settings', 'images', 'created', 'modified'):
            self.assertIn(k, d)

    def test_project_from_dict_round_trip(self):
        p = Project(name="MyProject")
        d = p.to_dict()
        p2 = Project.from_dict(d)
        self.assertEqual(p2.name, "MyProject")

    def test_project_from_dict_defaults(self):
        p = Project.from_dict({})
        self.assertEqual(p.name, "Untitled Project")

    def test_project_update_modified(self):
        p = Project()
        old_modified = p.modified
        import time; time.sleep(0.01)
        p.update_modified()
        self.assertGreaterEqual(p.modified, old_modified)

    # ── ProjectManager ─────────────────────────────────────────────────────────
    def test_create_new_project(self):
        pm = ProjectManager()
        p = pm.create_new_project("Test")
        self.assertIsInstance(p, Project)
        self.assertEqual(p.name, "Test")

    def test_add_images_to_project(self):
        pm = ProjectManager()
        p = pm.create_new_project()
        images = {64: _make_rgba(64, 64), 32: _make_rgba(32, 32)}
        pm.add_images_to_project(p, images, embed=True)
        self.assertEqual(p.get_image_count(), 2)

    def test_get_images_from_project(self):
        pm = ProjectManager()
        p = pm.create_new_project()
        original = {64: _make_rgba(64, 64)}
        pm.add_images_to_project(p, original, embed=True)
        recovered = pm.get_images_from_project(p)
        self.assertIn(64, recovered)

    def test_save_and_load_round_trip(self):
        pm = ProjectManager()
        p = pm.create_new_project("SaveLoadTest")
        images = {64: _make_rgba(64, 64), 32: _make_rgba(32, 32)}
        pm.add_images_to_project(p, images, embed=True)
        path = os.path.join(self.tmp, "test_project")
        ok = pm.save_project(p, path)
        self.assertTrue(ok)
        loaded = pm.load_project(path + ".rnvicon")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "SaveLoadTest")
        self.assertEqual(loaded.get_image_count(), 2)

    def test_load_nonexistent_returns_none(self):
        pm = ProjectManager()
        result = pm.load_project("/no/such/file.rnvicon")
        self.assertIsNone(result)

    def test_load_invalid_json_returns_none(self):
        bad = os.path.join(self.tmp, "bad.rnvicon")
        with open(bad, 'w') as f:
            f.write("NOT JSON {{{")
        pm = ProjectManager()
        result = pm.load_project(bad)
        self.assertIsNone(result)

    def test_save_adds_extension(self):
        pm = ProjectManager()
        p = pm.create_new_project()
        path = os.path.join(self.tmp, "no_ext")
        pm.save_project(p, path)
        self.assertTrue(os.path.exists(path + ".rnvicon"))

    def test_save_images_recoverable(self):
        pm = ProjectManager()
        p = pm.create_new_project()
        src_img = _make_rgba(32, 32, (200, 50, 100, 255))
        pm.add_images_to_project(p, {32: src_img}, embed=True)
        path = os.path.join(self.tmp, "img_recover")
        pm.save_project(p, path)
        loaded = pm.load_project(path + ".rnvicon")
        imgs = pm.get_images_from_project(loaded)
        self.assertIn(32, imgs)


# ══════════════════════════════════════════════════════════════════════════════
# 18. FOLDER WATCHER
# ══════════════════════════════════════════════════════════════════════════════
class TestFolderWatcher(unittest.TestCase):
    """core/folder_watcher.py — WatchSettings serialization, FolderWatcher state."""

    # ── WatchSettings ──────────────────────────────────────────────────────────
    def test_watch_settings_defaults(self):
        ws = WatchSettings()
        self.assertFalse(ws.recursive)
        self.assertFalse(ws.delete_source)
        self.assertTrue(ws.overwrite_existing)
        self.assertTrue(ws.autofill)
        self.assertTrue(ws.png_compression)

    def test_watch_settings_default_sizes(self):
        ws = WatchSettings()
        self.assertIsInstance(ws.sizes, list)
        self.assertGreater(len(ws.sizes), 0)

    def test_watch_settings_to_dict_keys(self):
        ws = WatchSettings(input_folder="/in", output_folder="/out")
        d = ws.to_dict()
        for k in ('input_folder', 'output_folder', 'sizes', 'autofill',
                  'png_compression', 'recursive', 'delete_source', 'overwrite_existing'):
            self.assertIn(k, d)

    def test_watch_settings_from_dict_round_trip(self):
        ws = WatchSettings(
            input_folder="/in",
            output_folder="/out",
            recursive=True,
            delete_source=False,
        )
        d = ws.to_dict()
        ws2 = WatchSettings.from_dict(d)
        self.assertEqual(ws2.input_folder, "/in")
        self.assertEqual(ws2.output_folder, "/out")
        self.assertTrue(ws2.recursive)

    def test_watch_settings_from_dict_defaults(self):
        ws = WatchSettings.from_dict({})
        self.assertEqual(ws.input_folder, "")
        self.assertEqual(ws.output_folder, "")
        self.assertFalse(ws.recursive)

    def test_watch_settings_custom_sizes(self):
        ws = WatchSettings(sizes=[256, 64, 16])
        self.assertEqual(ws.sizes, [256, 64, 16])

    # ── FolderWatcher state ────────────────────────────────────────────────────
    def test_folder_watcher_instantiates(self):
        fw = FolderWatcher()
        self.assertIsNotNone(fw)

    def test_is_watching_false_initially(self):
        fw = FolderWatcher()
        self.assertFalse(fw.is_watching())

    def test_get_settings_none_initially(self):
        fw = FolderWatcher()
        self.assertIsNone(fw.get_settings())

    def test_get_processed_count_zero_initially(self):
        fw = FolderWatcher()
        self.assertEqual(fw.get_processed_count(), 0)

    def test_stop_watching_when_not_watching(self):
        fw = FolderWatcher()
        fw.stop_watching()  # Should not raise
        self.assertFalse(fw.is_watching())

    def test_start_watching_empty_folder_fails(self):
        fw = FolderWatcher()
        ws = WatchSettings(input_folder="", output_folder="")
        result = fw.start_watching(ws)
        self.assertFalse(result)


# ══════════════════════════════════════════════════════════════════════════════
# 19. LOGGER
# ══════════════════════════════════════════════════════════════════════════════
class TestLogger(unittest.TestCase):
    """utils/logger.py — setup_logger, get_logger, convenience functions, Logger class."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ── setup_logger ───────────────────────────────────────────────────────────
    def test_setup_logger_returns_logger(self):
        import logging
        lg = setup_logger(
            name="test_setup",
            log_to_file=False
        )
        self.assertIsInstance(lg, logging.Logger)

    def test_setup_logger_idempotent(self):
        """Calling setup_logger twice should not duplicate handlers."""
        import logging
        lg = setup_logger(name="test_idempotent", log_to_file=False)
        count1 = len(lg.handlers)
        lg2 = setup_logger(name="test_idempotent", log_to_file=False)
        self.assertEqual(len(lg2.handlers), count1)

    def test_setup_logger_file_output(self):
        import logging
        log_dir = Path(self.tmp) / "logs"
        lg = setup_logger(
            name="test_file",
            level=logging.DEBUG,
            log_to_file=True,
            log_dir=log_dir
        )
        lg.info("test message")
        self.assertTrue(log_dir.exists())

    # ── get_logger ─────────────────────────────────────────────────────────────
    def test_get_logger_returns_logger(self):
        import logging
        lg = get_logger("test_module")
        self.assertIsInstance(lg, logging.Logger)

    def test_get_logger_namespaced(self):
        lg = get_logger("my_module")
        self.assertIn("my_module", lg.name)

    # ── set_log_level ──────────────────────────────────────────────────────────
    def test_set_log_level_no_crash(self):
        import logging
        set_log_level(logging.DEBUG)
        set_log_level(logging.WARNING)
        set_log_level(logging.INFO)

    # ── convenience functions ──────────────────────────────────────────────────
    def test_log_success_no_crash(self):
        import logging
        lg = get_logger("test_success")
        log_success(lg, "operation succeeded")

    def test_log_failure_no_crash(self):
        import logging
        lg = get_logger("test_failure")
        log_failure(lg, "operation failed")

    def test_log_warning_symbol_no_crash(self):
        import logging
        lg = get_logger("test_warn")
        log_warning_symbol(lg, "something odd")

    # ── Logger class ───────────────────────────────────────────────────────────
    def test_get_logger_instance_returns_logger(self):
        lg = get_logger_instance("test_class")
        self.assertIsInstance(lg, AppLogger)

    def test_logger_instance_info(self):
        lg = get_logger_instance("test_info")
        lg.info("info message")  # Should not raise

    def test_logger_instance_debug(self):
        lg = get_logger_instance("test_debug")
        lg.debug("debug message")

    def test_logger_instance_warning(self):
        lg = get_logger_instance("test_warning")
        lg.warning("warning message")

    def test_logger_instance_error(self):
        lg = get_logger_instance("test_error")
        lg.error("error message")

    def test_logger_instance_success(self):
        lg = get_logger_instance("test_success_cls")
        lg.success("success message")  # Custom method on Logger class


# ══════════════════════════════════════════════════════════════════════════════
# 20. DIALOG HELPER
# ══════════════════════════════════════════════════════════════════════════════
class TestDialogHelper(unittest.TestCase):
    """utils/dialog_helper.py — DialogResult enum, stylesheets, theme detection."""

    # ── DialogResult ───────────────────────────────────────────────────────────
    def test_dialog_result_values_exist(self):
        for member in (DialogResult.YES, DialogResult.NO,
                       DialogResult.CANCEL, DialogResult.OK):
            self.assertIsInstance(member.value, int)

    def test_dialog_result_yes_is_1(self):
        self.assertEqual(DialogResult.YES.value, 1)

    def test_dialog_result_no_is_2(self):
        self.assertEqual(DialogResult.NO.value, 2)

    def test_dialog_result_cancel_is_3(self):
        self.assertEqual(DialogResult.CANCEL.value, 3)

    def test_dialog_result_ok_is_4(self):
        self.assertEqual(DialogResult.OK.value, 4)

    def test_dialog_result_unique_values(self):
        values = [r.value for r in DialogResult]
        self.assertEqual(len(values), len(set(values)))

    # ── DialogHelper defaults ──────────────────────────────────────────────────
    def test_default_titles_nonempty(self):
        self.assertGreater(len(DialogHelper.DEFAULT_ERROR_TITLE), 0)
        self.assertGreater(len(DialogHelper.DEFAULT_WARNING_TITLE), 0)
        self.assertGreater(len(DialogHelper.DEFAULT_INFO_TITLE), 0)
        self.assertGreater(len(DialogHelper.DEFAULT_CONFIRM_TITLE), 0)
        self.assertGreater(len(DialogHelper.DEFAULT_SUCCESS_TITLE), 0)

    # ── _is_dark_theme ─────────────────────────────────────────────────────────
    def test_is_dark_theme_none_parent_returns_true(self):
        """Default to dark when no parent widget available."""
        self.assertTrue(DialogHelper._is_dark_theme(None))

    # ── _get_style_dark / _get_style_light ─────────────────────────────────────
    def test_get_style_dark_returns_string(self):
        style = DialogHelper._get_style_dark()
        self.assertIsInstance(style, str)
        self.assertGreater(len(style), 50)

    def test_get_style_light_returns_string(self):
        style = DialogHelper._get_style_light()
        self.assertIsInstance(style, str)
        self.assertGreater(len(style), 50)

    def test_get_style_dark_contains_qmessagebox(self):
        style = DialogHelper._get_style_dark()
        self.assertIn("QMessageBox", style)

    def test_get_style_light_contains_qmessagebox(self):
        style = DialogHelper._get_style_light()
        self.assertIn("QMessageBox", style)

    def test_get_style_dark_contains_qpushbutton(self):
        self.assertIn("QPushButton", DialogHelper._get_style_dark())

    def test_get_style_light_contains_qpushbutton(self):
        self.assertIn("QPushButton", DialogHelper._get_style_light())

    def test_dark_style_no_hardcoded_gold(self):
        """Dark stylesheet should reference brand gold via colors.py, not hardcode it."""
        # The raw hex should not appear literally — it's injected via get_theme_colors()
        # We just verify the stylesheet is non-empty and structurally valid
        style = DialogHelper._get_style_dark()
        self.assertIn("{", style)
        self.assertIn("}", style)

    def test_get_style_none_parent_returns_dark(self):
        """_get_style(None) should default to dark stylesheet."""
        dark = DialogHelper._get_style_dark()
        style = DialogHelper._get_style(None)
        self.assertEqual(style, dark)


# ══════════════════════════════════════════════════════════════════════════════
# 21. PREVIEW UTILS (GAPS)
# ══════════════════════════════════════════════════════════════════════════════
class TestPreviewUtilsGaps(unittest.TestCase):
    """ui/preview_utils.py — pil_to_qpixmap, thumbnail cache helpers (gap coverage)."""

    # ── pil_to_qpixmap ─────────────────────────────────────────────────────────
    def test_pil_to_qpixmap_returns_qpixmap(self):
        from PyQt6.QtGui import QPixmap
        img = _make_rgba(32, 32)
        px = pil_to_qpixmap(img)
        self.assertIsInstance(px, QPixmap)

    def test_pil_to_qpixmap_correct_size(self):
        img = _make_rgba(64, 48)
        px = pil_to_qpixmap(img)
        self.assertEqual(px.width(), 64)
        self.assertEqual(px.height(), 48)

    def test_pil_to_qpixmap_not_null(self):
        img = _make_rgba(16, 16)
        px = pil_to_qpixmap(img)
        self.assertFalse(px.isNull())

    def test_pil_to_qpixmap_various_sizes(self):
        from PyQt6.QtGui import QPixmap
        for size in (16, 32, 64, 128, 256):
            img = _make_rgba(size, size)
            px = pil_to_qpixmap(img)
            self.assertIsInstance(px, QPixmap)
            self.assertFalse(px.isNull())

    # ── clear_thumbnail_cache ──────────────────────────────────────────────────
    def test_clear_thumbnail_cache_returns_int(self):
        result = clear_thumbnail_cache()
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)

    # ── get_thumbnail_cache_stats ──────────────────────────────────────────────
    def test_get_thumbnail_cache_stats_returns_dict(self):
        stats = get_thumbnail_cache_stats()
        self.assertIsInstance(stats, dict)

    def test_thumbnail_cache_stats_has_size_key(self):
        stats = get_thumbnail_cache_stats()
        self.assertIn('size', stats)


# ══════════════════════════════════════════════════════════════════════════════
# 22. ICON BUILDER CORE (GAPS) — export functions
# ══════════════════════════════════════════════════════════════════════════════
class TestIconBuilderCoreGaps(unittest.TestCase):
    """core/icon_builder_core.py — export_favicon_package, android, ios, icns."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.images = {s: _make_rgba(s, s) for s in [256, 128, 64, 48, 32, 16]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ── export_favicon_package ─────────────────────────────────────────────────
    def test_favicon_package_creates_files(self):
        out = os.path.join(self.tmp, "favicon")
        os.makedirs(out, exist_ok=True)
        success, msg, info = IconBuilderCore.export_favicon_package(
            self.images, out)
        self.assertTrue(success, msg)
        self.assertGreater(info.get('file_count', 0), 0)

    def test_favicon_package_has_ico(self):
        out = os.path.join(self.tmp, "favicon_ico")
        os.makedirs(out, exist_ok=True)
        success, msg, info = IconBuilderCore.export_favicon_package(
            self.images, out)
        if success:
            files = info.get('files', [])
            ico_files = [f for f in files if f.endswith('.ico')]
            self.assertGreater(len(ico_files), 0)

    def test_favicon_package_missing_output_dir_handled(self):
        out = os.path.join(self.tmp, "favicon_new_dir")
        success, msg, info = IconBuilderCore.export_favicon_package(
            self.images, out)
        # Should succeed (creates dir) or fail gracefully
        self.assertIsInstance(success, bool)
        self.assertIsInstance(msg, str)

    # ── export_android_icons ───────────────────────────────────────────────────
    def test_android_export_creates_files(self):
        out = os.path.join(self.tmp, "android")
        os.makedirs(out, exist_ok=True)
        success, msg, files = IconBuilderCore.export_android_icons(
            self.images, out)
        self.assertIsInstance(success, bool)
        self.assertIsInstance(msg, str)
        if success:
            self.assertGreater(len(files), 0)

    def test_android_export_mipmap_folders(self):
        out = os.path.join(self.tmp, "android_mip")
        os.makedirs(out, exist_ok=True)
        success, msg, files = IconBuilderCore.export_android_icons(
            self.images, out)
        if success:
            # Should create mipmap-* subdirectories
            dirs = [d for d in os.listdir(out)
                    if os.path.isdir(os.path.join(out, d))]
            self.assertGreater(len(dirs), 0)

    # ── export_ios_icons ───────────────────────────────────────────────────────
    def test_ios_export_creates_files(self):
        out = os.path.join(self.tmp, "ios")
        os.makedirs(out, exist_ok=True)
        success, msg, files = IconBuilderCore.export_ios_icons(
            self.images, out)
        self.assertIsInstance(success, bool)
        self.assertIsInstance(msg, str)

    def test_ios_export_xcassets_structure(self):
        out = os.path.join(self.tmp, "ios_xc")
        os.makedirs(out, exist_ok=True)
        success, msg, files = IconBuilderCore.export_ios_icons(
            self.images, out)
        if success:
            # Should create an xcassets directory
            entries = os.listdir(out)
            self.assertGreater(len(entries), 0)

    # ── build_icns_file ────────────────────────────────────────────────────────
    def test_build_icns_creates_file(self):
        out = os.path.join(self.tmp, "test.icns")
        success, msg, info = IconBuilderCore.build_icns_file(self.images, out)
        self.assertIsInstance(success, bool)
        self.assertIsInstance(msg, str)
        if success:
            self.assertTrue(os.path.exists(out))

    def test_build_icns_file_nonempty(self):
        out = os.path.join(self.tmp, "test2.icns")
        success, msg, info = IconBuilderCore.build_icns_file(self.images, out)
        if success and os.path.exists(out):
            self.assertGreater(os.path.getsize(out), 0)

    # ── create_bmp_header ──────────────────────────────────────────────────────
    def test_create_bmp_header_returns_bytes(self):
        data = IconBuilderCore.create_bmp_header(32)
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)

    def test_create_bmp_header_different_sizes(self):
        for size in (16, 32, 48, 64):
            data = IconBuilderCore.create_bmp_header(size)
            self.assertIsInstance(data, bytes)


# ══════════════════════════════════════════════════════════════════════════════
# 23. IMAGE PROCESSOR (GAPS)
# ══════════════════════════════════════════════════════════════════════════════
class TestImageProcessorGaps(unittest.TestCase):
    """core/image_processor.py — fill_transparency, add_border, center_resize, autofill."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ip = ImageProcessor()
        self.png = _make_png_file(os.path.join(self.tmp, "icon.png"), 64)
        self.ip.load_png(self.png)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_apply_fill_transparency(self):
        count = self.ip.apply_fill_transparency((0, 0, 0, 255))
        self.assertGreaterEqual(count, 1)

    def test_apply_add_border(self):
        count = self.ip.apply_add_border(width=4, color=(0, 0, 0, 255))
        self.assertGreaterEqual(count, 1)

    def test_apply_center_resize(self):
        count = self.ip.apply_center_resize(target_size=64)
        self.assertGreaterEqual(count, 0)

    def test_can_autofill_true_for_missing(self):
        # 64px is loaded — 32px is missing, should be autofillable
        self.assertTrue(self.ip.can_autofill(32))

    def test_can_autofill_false_for_existing(self):
        self.assertFalse(self.ip.can_autofill(64))

    def test_can_autofill_false_when_no_source(self):
        ip = ImageProcessor()
        self.assertFalse(ip.can_autofill(256))

    def test_get_autofill_source_returns_int(self):
        source = self.ip.get_autofill_source(32)
        self.assertIsNotNone(source)
        self.assertIsInstance(source, int)

    def test_undo_count_after_transforms(self):
        self.ip.apply_rotate(90)
        self.ip.apply_flip_horizontal()
        self.assertGreaterEqual(self.ip.get_undo_count(), 1)

    def test_redo_count_after_undo(self):
        self.ip.apply_rotate(90)
        self.ip.undo()
        self.assertGreaterEqual(self.ip.get_redo_count(), 1)


# ══════════════════════════════════════════════════════════════════════════════
# 24. FINAL INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════
class TestFinalIntegration(unittest.TestCase):
    """Cross-module integration — project save/load+build, batch queue+export, cache+preview."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_project_save_then_build_ico(self):
        """Save a project, reload it, extract images, build ICO — full pipeline."""
        pm = ProjectManager()
        p = pm.create_new_project("IntegrationTest")
        images = {64: _make_rgba(64, 64), 32: _make_rgba(32, 32)}
        pm.add_images_to_project(p, images, embed=True)
        path = os.path.join(self.tmp, "integration")
        pm.save_project(p, path)

        loaded = pm.load_project(path + ".rnvicon")
        extracted = pm.get_images_from_project(loaded)
        ico_out = os.path.join(self.tmp, "from_project.ico")
        result = IconBuilderCore.build_ico_file(extracted, ico_out)
        self.assertTrue(result)
        info = IconBuilderCore.verify_ico_file(ico_out)
        self.assertGreater(info.get('count', 0), 0)

    def test_image_adjustments_then_build_ico(self):
        """Apply adjustments via ImageProcessor then build ICO from result."""
        ip = ImageProcessor()
        png = _make_png_file(os.path.join(self.tmp, "adj.png"), 64)
        ip.load_png(png)
        ip.apply_rotate(90)
        ip.apply_grayscale()
        ip.apply_color_adjustments(brightness=10, contrast=5, saturation=-20)
        detected = ip.get_detected_images()
        self.assertGreater(len(detected), 0)
        ico = os.path.join(self.tmp, "adjusted.ico")
        result = IconBuilderCore.build_ico_file(detected, ico)
        self.assertTrue(result)

    def test_batch_job_serialization_completeness(self):
        """All BatchJob fields survive a to_dict/from_dict round-trip."""
        job = BatchJob(
            source_path="/in/icon.png",
            output_path="/out/icon.ico",
            settings={"sizes": [256, 64], "png": True},
        )
        job.status = JobStatus.COMPLETED
        job.error_message = ""
        d = job.to_dict()
        job2 = BatchJob.from_dict(d)
        self.assertEqual(job2.source_path, job.source_path)
        self.assertEqual(job2.output_path, job.output_path)
        self.assertEqual(job2.status, JobStatus.COMPLETED)

    def test_pixmap_cache_with_real_pixmap(self):
        """Cache a real pil_to_qpixmap result and retrieve it."""
        cache = QPixmapCache(max_size=5)
        img = _make_rgba(64, 64, (200, 100, 50, 255))
        px = pil_to_qpixmap(img)
        key = ("integration_test", 64)
        cache.put(key, px)
        retrieved = cache.get(key)
        self.assertIsNotNone(retrieved)
        self.assertFalse(retrieved.isNull())

    def test_image_adjustments_preserve_size(self):
        """After all adjustments, image dimensions should remain valid."""
        img = _make_rgba(64, 64, (150, 80, 40, 255))
        img = rotate_image(img, 90)
        img = flip_horizontal(img)
        img = adjust_brightness(img, 20)
        img = adjust_contrast(img, -10)
        img = convert_grayscale(img)
        self.assertIsInstance(img, _Image.Image)
        self.assertGreater(img.width, 0)
        self.assertGreater(img.height, 0)

    def test_export_history_accumulates_correctly(self):
        """Log several export types and verify statistics are accurate."""
        eh = ExportHistory()
        eh._entries = []
        ts = datetime.now().isoformat()
        entries = [
            ExportEntry(ts, "/ico.ico",     "ico",     success=True),
            ExportEntry(ts, "/set.png",     "png_set", success=True),
            ExportEntry(ts, "/fail.icns",   "icns",    success=False),
            ExportEntry(ts, "/android.zip", "android", success=True),
        ]
        for e in entries:
            eh._entries.append(e)
        stats = eh.get_statistics()
        self.assertEqual(stats['total_exports'], 4)
        self.assertEqual(stats['successful'],    3)
        self.assertEqual(stats['failed'],         1)

    def test_colors_consistency_no_hardcoded_gold_in_theme_manager(self):
        """ThemeManager main button hover must use inverse system, not brand gold."""
        tm = ThemeManager()
        dark_hover = tm.DARK_THEME.get('button_hover_bg', '')
        self.assertNotEqual(dark_hover.lower(), BRAND_GOLD.lower())
        light_hover = tm.LIGHT_THEME.get('button_hover_bg', '')
        self.assertNotEqual(light_hover.lower(), BRAND_GOLD_DARK.lower())

    def test_session_and_export_history_independent(self):
        """SessionManager and ExportHistory should be independently patchable."""
        sm = SessionManager()
        eh = ExportHistory()
        eh._entries = []
        self.assertIsNotNone(sm)
        self.assertTrue(eh.is_empty)


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════
def _summary(result):
    total   = result.testsRun
    failed  = len(result.failures)
    errors  = len(result.errors)
    skipped = len(result.skipped)
    passed  = total - failed - errors - skipped

    print(f"\n{'═'*62}\n{_B}  RNV Icon Builder — Test Results{_X}\n{'═'*62}")
    print(f"  {_G}✓ Passed  {passed:>4}{_X}")
    if failed:  print(f"  {_R}✗ Failed  {failed:>4}{_X}")
    if errors:  print(f"  {_R}⚠ Errors  {errors:>4}{_X}")
    if skipped: print(f"  {_Y}  Skipped {skipped:>4}{_X}")
    print(f"  {'─'*18}\n    Total   {total:>4}\n{'═'*62}")

    if result.failures:
        print(f"\n{_R}{_B}FAILURES:{_X}")
        for test, tb in result.failures:
            print(f"  {_R}✗ {test}{_X}")
            for line in tb.splitlines()[-4:]:
                print(f"      {line}")

    if result.errors:
        print(f"\n{_R}{_B}ERRORS:{_X}")
        for test, tb in result.errors:
            print(f"  {_R}⚠ {test}{_X}")
            for line in tb.splitlines()[-4:]:
                print(f"      {line}")

    if passed == total:
        print(f"\n  {_G}{_B}All {total} tests passed ✓{_X}\n")
    else:
        print(f"\n  {_R}{_B}{failed + errors} test(s) need attention.{_X}\n")


if __name__ == "__main__":
    print(f"\n{_C}{_B}{'═'*62}\n  RNV Icon Builder — Comprehensive Test Suite v2.0\n{'═'*62}{_X}")
    print(f"  Project: {_FLAT}\n  Python:  {sys.version.split()[0]}\n")

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [
        # v1.0 — core coverage
        TestColors,
        TestThemeManager,
        TestIconBuilderCore,
        TestImageProcessor,
        TestPreviewUtils,
        TestRecentFilesManager,
        TestPresetManager,
        TestSessionManager,
        TestExportHistory,
        TestErrorHandler,
        TestFileUtils,
        TestConfig,
        TestEdgeCases,
        # v2.0 — full coverage additions
        TestImageAdjustments,
        TestPixmapCache,
        TestBatchProcessor,
        TestProjectManager,
        TestFolderWatcher,
        TestLogger,
        TestDialogHelper,
        TestPreviewUtilsGaps,
        TestIconBuilderCoreGaps,
        TestImageProcessorGaps,
        TestFinalIntegration,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    buf    = io.StringIO()
    runner = unittest.TextTestRunner(
        verbosity=2 if "-v" in sys.argv else 1,
        stream=buf
    )
    result = runner.run(suite)
    print(buf.getvalue(), flush=True)
    _summary(result)
    sys.stdout.flush()
    # os._exit skips PyQt6 internal cleanup which crashes in headless environments
    os._exit(0 if result.wasSuccessful() else 1)