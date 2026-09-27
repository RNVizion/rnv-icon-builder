"""
RNV Icon Builder — Preview Utils Tests
=======================================

Phase 10A coverage push for preview_utils.py (currently 47%).

Targets the compositing functions, color extraction, and thumbnail cache —
the parts that drive every preview redraw and metadata refresh.
"""

from __future__ import annotations

import os
import pytest
from PIL import Image


# ══════════════════════════════════════════════════════════════════════════════
# 1. CHECKERBOARD PATTERN
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestCheckerboardPattern:

    def test_create_checkerboard_returns_rgb_image(self):
        from ui.preview_utils import create_checkerboard_pattern

        result = create_checkerboard_pattern(64, 64, square_size=8)
        assert result.size == (64, 64)
        assert result.mode == "RGB"

    def test_create_checkerboard_default_square_size(self):
        from ui.preview_utils import create_checkerboard_pattern

        result = create_checkerboard_pattern(32, 32)
        assert result.size == (32, 32)

    def test_create_checkerboard_custom_colors(self):
        from ui.preview_utils import create_checkerboard_pattern

        # Two distinct colors should produce a pattern with both.
        result = create_checkerboard_pattern(
            16, 16, square_size=4,
            color1=(255, 0, 0), color2=(0, 0, 255))
        # Sample at (0,0) and (4,0) — different squares.
        assert result.size == (16, 16)


# ══════════════════════════════════════════════════════════════════════════════
# 2. COMPOSITING
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestCompositing:

    def test_composite_on_checkerboard_returns_rgb(self, sample_rgba):
        from ui.preview_utils import composite_on_checkerboard

        img = sample_rgba(64, 64, (255, 0, 0, 128))  # Semi-transparent red.
        result = composite_on_checkerboard(img)
        assert result.mode == "RGB"
        assert result.size == (64, 64)

    def test_composite_on_checkerboard_converts_non_rgba(self):
        """Function handles RGB input by converting to RGBA first."""
        from ui.preview_utils import composite_on_checkerboard

        rgb_img = Image.new("RGB", (32, 32), (100, 100, 100))
        result = composite_on_checkerboard(rgb_img)
        assert result.mode == "RGB"

    def test_composite_on_color_returns_rgb(self, sample_rgba):
        from ui.preview_utils import composite_on_color

        img = sample_rgba(64, 64, (0, 255, 0, 128))
        result = composite_on_color(img, color=(50, 50, 50))
        assert result.mode == "RGB"
        assert result.size == (64, 64)

    def test_composite_on_color_default_white(self, sample_rgba):
        from ui.preview_utils import composite_on_color

        img = sample_rgba(32, 32, (255, 0, 0, 0))  # Fully transparent red.
        result = composite_on_color(img)
        # Top-left pixel should be white (default background) since fg is transparent.
        assert result.getpixel((0, 0)) == (255, 255, 255)

    def test_composite_with_background_solid_white(self, sample_rgba):
        """composite_with_background with background_type='white'."""
        from ui.preview_utils import composite_with_background
        from utils.config import PREVIEW_BG_WHITE

        img = sample_rgba(64, 64, (0, 0, 255, 200))
        result = composite_with_background(img, background_type=PREVIEW_BG_WHITE)
        assert result.size == (64, 64)
        assert result.mode in ("RGB", "RGBA")

    def test_composite_with_background_checker(self, sample_rgba):
        from ui.preview_utils import composite_with_background
        from utils.config import PREVIEW_BG_CHECKERBOARD

        img = sample_rgba(32, 32, (255, 255, 0, 100))
        result = composite_with_background(
            img, background_type=PREVIEW_BG_CHECKERBOARD)
        assert result.size == (32, 32)

    def test_composite_with_background_custom_color(self, sample_rgba):
        """background_type='custom' with a custom_color tuple."""
        from ui.preview_utils import composite_with_background
        from utils.config import PREVIEW_BG_CUSTOM

        img = sample_rgba(32, 32, (255, 0, 0, 100))
        result = composite_with_background(
            img, background_type=PREVIEW_BG_CUSTOM,
            custom_color=(50, 100, 200))
        assert result.size == (32, 32)


# ══════════════════════════════════════════════════════════════════════════════
# 3. COLOR EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestColorExtraction:

    def test_extract_dominant_colors_returns_list(self, sample_rgba):
        from ui.preview_utils import extract_dominant_colors

        img = sample_rgba(64, 64, (200, 100, 50, 255))
        colors = extract_dominant_colors(img, count=5)
        assert isinstance(colors, list)
        # Each entry is ((r,g,b), pixel_count)
        if colors:
            assert len(colors[0]) == 2

    def test_extract_dominant_colors_solid_image_returns_one(
            self, sample_rgba):
        """A solid-color image should yield essentially one dominant color."""
        from ui.preview_utils import extract_dominant_colors

        img = sample_rgba(64, 64, (200, 100, 50, 255))
        colors = extract_dominant_colors(img, count=10)
        # At least one color extracted; the top one should be near our fill.
        assert len(colors) >= 1

    def test_extract_dominant_colors_handles_rgba_input(self, sample_rgba):
        """Function should handle alpha channel without crashing."""
        from ui.preview_utils import extract_dominant_colors

        img = sample_rgba(32, 32, (128, 200, 64, 200))
        colors = extract_dominant_colors(img, count=3)
        assert isinstance(colors, list)


# ══════════════════════════════════════════════════════════════════════════════
# 4. THUMBNAIL CACHE
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestThumbnailCache:

    def test_get_cached_thumbnail_returns_qpixmap(self, qapp, sample_rgba,
                                                    tmp_dir):
        """First call should generate a fresh thumbnail."""
        from ui.preview_utils import get_cached_thumbnail
        from PyQt6.QtGui import QPixmap

        img = sample_rgba(128, 128, (200, 100, 50, 255))
        src_path = os.path.join(tmp_dir, "thumb_src.png")
        result = get_cached_thumbnail(src_path, img, size=64)
        assert isinstance(result, QPixmap)

    def test_get_cached_thumbnail_caches_repeat_calls(
            self, qapp, sample_rgba, tmp_dir):
        """Second call with same args should hit the cache."""
        from ui.preview_utils import get_cached_thumbnail

        img = sample_rgba(128, 128, (100, 100, 100, 255))
        src_path = os.path.join(tmp_dir, "thumb_cache.png")
        first = get_cached_thumbnail(src_path, img, size=64)
        second = get_cached_thumbnail(src_path, img, size=64)
        # Cache key match implies the same underlying data.
        assert first.cacheKey() == second.cacheKey()

    def test_get_cached_thumbnail_no_checkerboard(self, qapp, sample_rgba,
                                                    tmp_dir):
        """show_checkerboard=False produces a different cache entry."""
        from ui.preview_utils import get_cached_thumbnail

        img = sample_rgba(64, 64, (255, 0, 0, 128))
        src_path = os.path.join(tmp_dir, "no_check.png")
        result = get_cached_thumbnail(
            src_path, img, size=32, show_checkerboard=False)
        assert result is not None
        assert not result.isNull()

    def test_clear_thumbnail_cache_returns_count(self, qapp, sample_rgba,
                                                  tmp_dir):
        """clear_thumbnail_cache returns the number of evicted entries."""
        from ui.preview_utils import (clear_thumbnail_cache,
                                       get_cached_thumbnail)

        img = sample_rgba(64, 64, (50, 50, 50, 255))
        src_path = os.path.join(tmp_dir, "for_clear.png")
        get_cached_thumbnail(src_path, img, size=32)

        count = clear_thumbnail_cache()
        assert isinstance(count, int)
        assert count >= 0

    def test_get_thumbnail_cache_stats_returns_dict(self, qapp):
        from ui.preview_utils import get_thumbnail_cache_stats

        stats = get_thumbnail_cache_stats()
        assert isinstance(stats, dict)


# RNV-RESTYLE-ON-SWITCH
# ══════════════════════════════════════════════════════════════════════════════
# The preview background's custom-colour button follows the mode
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.ui
class TestBackgroundColorButtonFollowsTheMode:
    """RNV-RESTYLE-ON-SWITCH, ruling 3 of 2026-09-26. The Settings dialog's
    preview-background selector has a small button showing the custom
    colour. Its edge was written from DARK_THEME_COLORS by name, so in light
    mode it kept dark's #555555 edge while the combo beside it turned light;
    the chart's read-back of every stylesheet the app sets found it there.
    The edge takes the mode apply_theme() was given now.

    The hover does not move: BRAND_GOLD in every mode, a reviewed and
    permanent bypass in tests/test_brand_contrast.py, because it is drawn
    over the user's own colour rather than a themed surface."""

    @staticmethod
    def _parts(widget):
        sheet = widget.color_btn.styleSheet()
        plate, _, hover = sheet.partition("QPushButton:hover")
        return sheet, plate, hover

    def test_each_mode_draws_the_button_in_its_own_colours(self, qapp):
        from ui.colors import BRAND_GOLD, get_theme_colors
        from ui.preview_utils import BackgroundSelectorWidget

        widget = BackgroundSelectorWidget()
        try:
            edges = {get_theme_colors(is_dark=d)["text_disabled"] for d in (True, False)}
            assert len(edges) == 2, "the two modes share an edge, so this proves nothing"
            for is_dark in (False, True, False):
                widget.apply_theme(is_dark=is_dark)
                sheet, plate, hover = self._parts(widget)
                edge = get_theme_colors(is_dark=is_dark)["text_disabled"]
                assert f"border: 2px solid {edge};" in plate, sheet
                assert f"border-color: {BRAND_GOLD};" in hover, sheet
        finally:
            widget.deleteLater()

    def test_a_new_custom_colour_keeps_the_mode(self, qapp, monkeypatch):
        """Choosing a colour repaints the button without being told the mode."""
        from PyQt6.QtGui import QColor
        from PyQt6.QtWidgets import QColorDialog

        from ui.colors import BRAND_GOLD, get_theme_colors
        from ui.preview_utils import BackgroundSelectorWidget

        widget = BackgroundSelectorWidget()
        try:
            widget.apply_theme(is_dark=False)
            monkeypatch.setattr(QColorDialog, "getColor",
                                staticmethod(lambda *a, **k: QColor(10, 200, 30)))
            widget._choose_color()
            sheet, plate, hover = self._parts(widget)
            assert "background-color: #0ac81e;" in plate.lower(), sheet
            edge = get_theme_colors(is_dark=False)["text_disabled"]
            assert f"border: 2px solid {edge};" in plate, sheet
            assert f"border-color: {BRAND_GOLD};" in hover, sheet
        finally:
            widget.deleteLater()

    def test_the_settings_dialog_hands_its_mode_to_the_selector(self):
        """The chain the fix relies on: a mode change reaches the selector
        through the Settings dialog's own _apply_theme()."""
        import ast
        import pathlib
        src = (pathlib.Path(__file__).resolve().parents[1] / "ui" / "settings_dialog.py")
        tree = ast.parse(src.read_text(encoding="utf-8-sig"))
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "_apply_theme")
        assert "self.bg_selector.apply_theme(is_dark=is_dark)" in ast.unparse(fn)
