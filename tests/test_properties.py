"""
RNV Icon Builder — Phase 6 Property-Based Tests
================================================

Hypothesis-driven property tests for color math, serialization round-trips,
and image-adjustment invariants. Each property generates many examples,
exploring edges that hand-picked unit tests miss.

Phase 6 doesn't typically add coverage lines (those paths are already
exercised by earlier phases) — the value is in *strengthening* the
existing tests against subtle math bugs that pass type-checks but produce
wrong output. Surviving these properties gives confidence that the contracts
hold across input space, not just at the few values we happened to pick.

Scope (per Phase 6 plan):
  - hex/RGB round-trip and format invariants
  - BatchJob, SizePreset, WatchSettings, SessionState serialization
  - Padding monotonicity, rotation mod-360, flip involution
  - Brightness/contrast/saturation clamp idempotence
  - make_square and dimension-preservation invariants

Performance note: Image-touching properties cap examples low (10–30) because
each example creates a real PIL Image and runs PIL ops. Pure-logic properties
(color, serialization) run at the default 100 examples.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from PIL import Image


# ══════════════════════════════════════════════════════════════════════════════
# STRATEGIES — reusable input generators
# ══════════════════════════════════════════════════════════════════════════════

# Color components and full RGBA tuples.
rgb_component = st.integers(min_value=0, max_value=255)
rgb_tuple = st.tuples(rgb_component, rgb_component, rgb_component)
rgba_tuple = st.tuples(rgb_component, rgb_component, rgb_component,
                       rgb_component)


@st.composite
def small_rgba_image(draw, min_dim: int = 8, max_dim: int = 48):
    """Generate a solid-color RGBA image with random size and color.

    Solid color (rather than per-pixel random) keeps generation fast — the
    properties under test are about *operations on images*, not about
    particular pixel patterns.
    """
    w = draw(st.integers(min_value=min_dim, max_value=max_dim))
    h = draw(st.integers(min_value=min_dim, max_value=max_dim))
    color = draw(rgba_tuple)
    return Image.new("RGBA", (w, h), color)


# ══════════════════════════════════════════════════════════════════════════════
# 1. COLOR CONVERSION PROPERTIES
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.property
class TestColorProperties:

    @given(color=rgb_tuple)
    @settings(max_examples=200)
    def test_hex_round_trip(self, color):
        """hex_to_color(color_to_hex(rgb)) == rgb for every RGB tuple."""
        from ui.preview_utils import color_to_hex, hex_to_color

        assert hex_to_color(color_to_hex(color)) == color

    @given(color=rgb_tuple)
    @settings(max_examples=200)
    def test_hex_output_format(self, color):
        """color_to_hex always produces '#' + 6 uppercase hex chars."""
        from ui.preview_utils import color_to_hex

        result = color_to_hex(color)
        assert result.startswith("#")
        assert len(result) == 7
        assert all(c in "0123456789ABCDEF" for c in result[1:])

    @given(color=rgb_tuple)
    @settings(max_examples=100)
    def test_hex_to_color_accepts_with_or_without_hash(self, color):
        """hex_to_color is permissive about the '#' prefix."""
        from ui.preview_utils import color_to_hex, hex_to_color

        with_hash = color_to_hex(color)              # "#RRGGBB"
        without_hash = with_hash.lstrip("#")          # "RRGGBB"
        assert hex_to_color(with_hash) == hex_to_color(without_hash)


# ══════════════════════════════════════════════════════════════════════════════
# 2. SERIALIZATION ROUND-TRIP PROPERTIES
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.property
class TestSerializationProperties:

    @given(
        source=st.text(min_size=0, max_size=50),
        output=st.text(min_size=0, max_size=50),
        status_value=st.sampled_from(
            ["pending", "processing", "completed", "failed", "cancelled"]
        ),
        error=st.text(min_size=0, max_size=100),
    )
    @settings(max_examples=100)
    def test_batchjob_round_trip(self, source, output, status_value, error):
        """BatchJob.from_dict(job.to_dict()) preserves all top-level fields."""
        from core.batch_processor import BatchJob, JobStatus

        original = BatchJob(source_path=source, output_path=output,
                            settings={"sizes": [256, 64]})
        original.status = JobStatus(status_value)
        original.error_message = error

        restored = BatchJob.from_dict(original.to_dict())
        assert restored.source_path == original.source_path
        assert restored.output_path == original.output_path
        assert restored.status == original.status
        assert restored.error_message == original.error_message

    @given(
        name=st.text(min_size=1, max_size=50),
        sizes=st.lists(
            st.sampled_from([16, 24, 32, 48, 64, 128, 256]),
            min_size=1, max_size=7, unique=True,
        ),
        autofill=st.booleans(),
        png_compression=st.booleans(),
        description=st.text(min_size=0, max_size=200),
    )
    @settings(max_examples=100)
    def test_sizepreset_round_trip(self, name, sizes, autofill,
                                    png_compression, description):
        """SizePreset survives to_dict/from_dict losslessly."""
        from core.preset_manager import SizePreset

        original = SizePreset(name=name, sizes=sizes, autofill=autofill,
                              png_compression=png_compression,
                              description=description)
        restored = SizePreset.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.sizes == original.sizes
        assert restored.autofill == original.autofill
        assert restored.png_compression == original.png_compression
        assert restored.description == original.description

    @given(
        input_folder=st.text(min_size=0, max_size=80),
        output_folder=st.text(min_size=0, max_size=80),
        recursive=st.booleans(),
        delete_source=st.booleans(),
        overwrite=st.booleans(),
    )
    @settings(max_examples=100)
    def test_watchsettings_round_trip(self, input_folder, output_folder,
                                       recursive, delete_source, overwrite):
        """WatchSettings serialization is lossless on the boolean flags."""
        from core.folder_watcher import WatchSettings

        original = WatchSettings(
            input_folder=input_folder, output_folder=output_folder,
            recursive=recursive, delete_source=delete_source,
            overwrite_existing=overwrite,
        )
        restored = WatchSettings.from_dict(original.to_dict())
        assert restored.input_folder == original.input_folder
        assert restored.output_folder == original.output_folder
        assert restored.recursive == original.recursive
        assert restored.delete_source == original.delete_source
        assert restored.overwrite_existing == original.overwrite_existing

    @given(
        loaded_files=st.lists(st.text(min_size=0, max_size=50),
                              min_size=0, max_size=10),
        selected_sizes=st.lists(
            st.sampled_from([16, 24, 32, 48, 64, 128, 256]),
            min_size=0, max_size=7, unique=True,
        ),
        autofill=st.booleans(),
        png_compression=st.booleans(),
    )
    @settings(max_examples=100)
    def test_sessionstate_round_trip(self, loaded_files, selected_sizes,
                                      autofill, png_compression):
        """SessionState round-trips losslessly on its primitive fields."""
        from core.session_manager import SessionState

        original = SessionState(
            loaded_files=loaded_files,
            selected_sizes=selected_sizes,
            autofill_enabled=autofill,
            png_compression=png_compression,
            current_project_path="",
            window_geometry={"x": 0, "y": 0, "width": 800, "height": 600},
        )
        restored = SessionState.from_dict(original.to_dict())
        assert restored.loaded_files == original.loaded_files
        assert restored.selected_sizes == original.selected_sizes
        assert restored.autofill_enabled == original.autofill_enabled
        assert restored.png_compression == original.png_compression


# ══════════════════════════════════════════════════════════════════════════════
# 3. IMAGE ADJUSTMENT INVARIANT PROPERTIES
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.property
class TestImageAdjustmentProperties:

    @given(img=small_rgba_image(), padding=st.integers(min_value=0,
                                                       max_value=20))
    @settings(max_examples=30, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    def test_padding_monotonicity(self, img, padding):
        """add_padding always grows dimensions by exactly 2*padding."""
        from ui.image_adjustments import add_padding

        result = add_padding(img, padding)
        assert result.width == img.width + 2 * padding
        assert result.height == img.height + 2 * padding

    @given(
        img=small_rgba_image(),
        a=st.integers(min_value=0, max_value=10),
        b=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=20, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    def test_padding_additivity(self, img, a, b):
        """Padding by `a+b` once = padding by `a` then `b` (dimensions only)."""
        from ui.image_adjustments import add_padding

        once = add_padding(img, a + b)
        twice = add_padding(add_padding(img, a), b)
        assert once.size == twice.size

    @given(img=small_rgba_image(),
           multiplier=st.integers(min_value=0, max_value=4))
    @settings(max_examples=20, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    def test_rotation_full_circle_preserves_size(self, img, multiplier):
        """Rotation by any multiple of 360° leaves dimensions unchanged."""
        from ui.image_adjustments import rotate_image

        result = rotate_image(img, multiplier * 360)
        assert result.size == img.size

    @given(img=small_rgba_image())
    @settings(max_examples=20, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    def test_flip_horizontal_is_involution(self, img):
        """flip_horizontal applied twice returns to the original image."""
        from ui.image_adjustments import flip_horizontal

        twice = flip_horizontal(flip_horizontal(img))
        # Same dimensions, and pixel data should match.
        assert twice.size == img.size
        # Use tobytes() — getdata() is deprecated in modern Pillow.
        assert twice.tobytes() == img.tobytes()

    @given(
        img=small_rgba_image(),
        value=st.integers(min_value=-200, max_value=200),
    )
    @settings(max_examples=20, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    def test_brightness_clamp_does_not_crash(self, img, value):
        """Out-of-range brightness values are clamped, not raised.

        The function documents -100..+100 but should accept any int safely;
        internal clamp keeps the enhancement factor in [0.0, 2.0]."""
        from ui.image_adjustments import adjust_brightness

        result = adjust_brightness(img, value)
        assert result.size == img.size
        assert result.mode == "RGBA"


# ══════════════════════════════════════════════════════════════════════════════
# 4. IMAGE STRUCTURAL INVARIANTS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.property
class TestImageInvariantProperties:

    @given(img=small_rgba_image())
    @settings(max_examples=30, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    def test_make_square_produces_square(self, img):
        """make_square always returns an image where width == height."""
        from ui.image_adjustments import make_square

        result = make_square(img)
        assert result.width == result.height

    @given(img=small_rgba_image())
    @settings(max_examples=30, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    def test_grayscale_preserves_dimensions(self, img):
        """convert_grayscale never changes width/height."""
        from ui.image_adjustments import convert_grayscale

        result = convert_grayscale(img)
        assert result.size == img.size
