"""
RNV Icon Builder — Phase 8 Performance Benchmarks
==================================================

pytest-benchmark microbenchmarks for the hot paths in the codebase. Each
benchmark records a tight timing distribution; running them periodically
catches performance regressions that no other test would notice.

Default behavior: benchmarks are collected and run, but timing is *disabled*
via run_tests.py passing --benchmark-disable. This means:
  - Each benchmark function still executes once (so we know it doesn't crash)
  - No time-measurement overhead, no noisy timing tables in default output
  - Coverage numbers are unaffected

Full timing report: `python run_tests.py --benchmark` runs only this file
without coverage (which would skew the timings).

Scope (per Phase 8 plan):
  - Pixmap cache hit / miss / put
  - Font loader caching
  - Theme stylesheet generation
  - Serialization round-trips (BatchJob, SizePreset)
  - Color conversion round-trip
  - PIL-to-QPixmap conversion
  - Dominant color extraction
  - End-to-end ICO build
"""

from __future__ import annotations

import os
import pytest
from PIL import Image


# ══════════════════════════════════════════════════════════════════════════════
# 1. PIXMAP CACHE HOT PATHS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.benchmark
class TestCacheBenchmarks:

    def test_bench_qpixmap_cache_hit(self, qapp, benchmark):
        """Cache hit on a primed key — what users see most of the time."""
        from utils.pixmap_cache import QPixmapCache
        from PyQt6.QtGui import QPixmap

        cache = QPixmapCache(max_size=50)
        cache.put(("hot", 64), QPixmap(64, 64))

        # Each call: pure dict lookup.
        benchmark(cache.get, ("hot", 64))

    def test_bench_qpixmap_cache_miss(self, qapp, benchmark):
        """Cache miss — measures the lookup cost when absent."""
        from utils.pixmap_cache import QPixmapCache

        cache = QPixmapCache(max_size=50)
        benchmark(cache.get, ("never-stored", 64))

    def test_bench_qpixmap_cache_put_evict(self, qapp, benchmark):
        """Putting into a near-full cache (evicts oldest on overflow)."""
        from utils.pixmap_cache import QPixmapCache
        from PyQt6.QtGui import QPixmap

        cache = QPixmapCache(max_size=10)
        # Pre-fill so every benchmark iteration triggers eviction.
        for i in range(10):
            cache.put((f"prime", i), QPixmap(64, 64))

        counter = {"n": 0}

        def put_one():
            counter["n"] += 1
            cache.put((f"new", counter["n"]), QPixmap(32, 32))

        benchmark(put_one)


# ══════════════════════════════════════════════════════════════════════════════
# 2. FONT LOADER CACHING
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.benchmark
class TestFontCacheBenchmark:

    def test_bench_load_embedded_font_cached(self, qapp, benchmark):
        """After the first call, load_embedded_font should be near-instant.
        This benchmark warms it then measures the cached path."""
        from utils.font_loader import load_embedded_font

        load_embedded_font()  # Warm the module-level cache.
        benchmark(load_embedded_font)


# ══════════════════════════════════════════════════════════════════════════════
# 3. THEME STYLESHEET GENERATION
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.benchmark
class TestThemeBenchmark:

    def test_bench_get_scrollbar_style(self, qapp, benchmark):
        """get_scrollbar_style returns a pre-built constant — should be O(1)."""
        from ui.theme_manager import ThemeManager

        tm = ThemeManager()
        tm.current_theme = "dark"
        benchmark(tm.get_scrollbar_style)


# ══════════════════════════════════════════════════════════════════════════════
# 4. SERIALIZATION ROUND-TRIPS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.benchmark
class TestSerializationBenchmarks:

    def test_bench_batchjob_to_dict(self, benchmark):
        from core.batch_processor import BatchJob

        job = BatchJob(source_path="/in/a.png", output_path="/out/a.ico",
                       settings={"sizes": [256, 128, 64, 32, 16],
                                 "png_compression": True})
        benchmark(job.to_dict)

    def test_bench_batchjob_round_trip(self, benchmark):
        """Full to_dict/from_dict cycle — what saves and loads cost."""
        from core.batch_processor import BatchJob

        original = BatchJob(source_path="/in/a.png", output_path="/out/a.ico",
                            settings={"sizes": [256, 128, 64, 32, 16]})

        def round_trip():
            return BatchJob.from_dict(original.to_dict())

        benchmark(round_trip)

    def test_bench_sizepreset_round_trip(self, benchmark):
        from core.preset_manager import SizePreset

        original = SizePreset(name="Bench", sizes=[256, 128, 64, 32, 16],
                              description="benchmark preset")

        def round_trip():
            return SizePreset.from_dict(original.to_dict())

        benchmark(round_trip)


# ══════════════════════════════════════════════════════════════════════════════
# 5. COLOR CONVERSION
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.benchmark
class TestColorBenchmark:

    def test_bench_color_hex_round_trip(self, benchmark):
        """color_to_hex + hex_to_color — used by every color picker tick."""
        from ui.preview_utils import color_to_hex, hex_to_color

        def round_trip():
            return hex_to_color(color_to_hex((127, 64, 200)))

        benchmark(round_trip)


# ══════════════════════════════════════════════════════════════════════════════
# 6. IMAGE PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.benchmark
class TestImageBenchmarks:

    def test_bench_pil_to_qpixmap_64(self, qapp, benchmark, sample_rgba):
        """Converting a PIL image to a QPixmap — runs every preview update."""
        from ui.preview_utils import pil_to_qpixmap

        img = sample_rgba(64, 64, (200, 100, 50, 255))
        benchmark(pil_to_qpixmap, img)

    def test_bench_extract_dominant_colors(self, benchmark, sample_rgba):
        """Color quantization pass — used in metadata panel and analyzer."""
        from ui.preview_utils import extract_dominant_colors

        img = sample_rgba(64, 64, (180, 90, 60, 255))
        benchmark(extract_dominant_colors, img, 5)

    def test_bench_build_ico_two_sizes(self, benchmark, sample_rgba, tmp_dir):
        """End-to-end ICO build for a 2-size input — the whole pipeline."""
        from core.icon_builder_core import IconBuilderCore

        images = {64: sample_rgba(64, 64, (200, 100, 50, 255)),
                  32: sample_rgba(32, 32, (200, 100, 50, 255))}
        out_path = os.path.join(tmp_dir, "bench.ico")

        def build():
            IconBuilderCore.build_ico_file(images, out_path)

        benchmark(build)
