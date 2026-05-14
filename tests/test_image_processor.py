"""
RNV Icon Builder — Image Processor Tests
=========================================

Phase 10A coverage push for image_processor.py (currently 67%).

Targets the undo/redo system, autofill detection, validate_size edge
paths, and the missing-sizes / largest-size accessors.
"""

from __future__ import annotations

import os
import pytest
from PIL import Image


# ══════════════════════════════════════════════════════════════════════════════
# 1. UNDO / REDO LIFECYCLE
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestImageProcessorUndoRedo:

    def test_fresh_processor_cannot_undo_or_redo(self):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        assert ip.can_undo() is False
        assert ip.can_redo() is False
        assert ip.get_undo_count() == 0
        assert ip.get_redo_count() == 0

    def test_undo_returns_false_when_no_history(self):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        assert ip.undo() is False

    def test_redo_returns_false_when_no_history(self):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        assert ip.redo() is False

    def test_save_state_then_undo(self, sample_rgba):
        """Manual _save_state then undo should restore previous state."""
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        ip.detected_images[64] = sample_rgba(64, 64, (255, 0, 0, 255))
        ip._save_state()

        # Modify state, then undo back to saved snapshot.
        ip.detected_images[32] = sample_rgba(32, 32, (0, 255, 0, 255))
        result = ip.undo()
        assert result is True
        # 32 should be gone; 64 still there.
        assert 32 not in ip.detected_images
        assert 64 in ip.detected_images


# ══════════════════════════════════════════════════════════════════════════════
# 2. SIZE / IMAGE ACCESSORS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestImageProcessorAccessors:

    def test_has_size_true_when_present(self, sample_rgba):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        ip.detected_images[64] = sample_rgba(64, 64)
        assert ip.has_size(64) is True

    def test_has_size_false_when_absent(self):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        assert ip.has_size(64) is False

    def test_get_largest_size_returns_max(self, sample_rgba):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        for s in (16, 64, 32):
            ip.detected_images[s] = sample_rgba(s, s)
        assert ip.get_largest_size() == 64

    def test_get_largest_size_empty_returns_none(self):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        assert ip.get_largest_size() is None

    def test_get_image_returns_pil_image(self, sample_rgba):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        img = sample_rgba(64, 64, (10, 20, 30, 255))
        ip.detected_images[64] = img
        assert ip.get_image(64) is img

    def test_get_image_missing_returns_none(self):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        assert ip.get_image(64) is None

    def test_get_available_sizes_sorted(self, sample_rgba):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        for s in (32, 16, 64):
            ip.detected_images[s] = sample_rgba(s, s)
        result = ip.get_available_sizes()
        # Order is descending (largest first), per project convention.
        assert result == sorted(result, reverse=True)

    def test_get_missing_sizes_excludes_present(self, sample_rgba):
        """get_missing_sizes returns ICON_SIZES minus what's loaded."""
        from core.image_processor import ImageProcessor
        from utils.config import ICON_SIZES

        ip = ImageProcessor()
        ip.detected_images[ICON_SIZES[0]] = sample_rgba(
            ICON_SIZES[0], ICON_SIZES[0])
        missing = ip.get_missing_sizes()
        assert ICON_SIZES[0] not in missing
        # Other ICON_SIZES values should be in missing.
        for s in ICON_SIZES[1:]:
            assert s in missing


# ══════════════════════════════════════════════════════════════════════════════
# 3. AUTOFILL LOGIC
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestImageProcessorAutofill:

    def test_can_autofill_from_larger_returns_true(self, sample_rgba):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        ip.detected_images[256] = sample_rgba(256, 256)
        # 64 missing, but 256 exists — autofill possible.
        assert ip.can_autofill(64) is True

    def test_can_autofill_no_larger_returns_false(self, sample_rgba):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        ip.detected_images[16] = sample_rgba(16, 16)
        # Asking for 256 when only 16 exists — can't downscale up.
        assert ip.can_autofill(256) is False

    def test_get_autofill_source_returns_smallest_larger(self, sample_rgba):
        """Autofill source should be the smallest image >= target."""
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        for s in (32, 128, 256):
            ip.detected_images[s] = sample_rgba(s, s)
        # For target=64, smallest larger is 128.
        result = ip.get_autofill_source(64)
        assert result == 128

    def test_get_autofill_source_no_source_returns_none(self):
        from core.image_processor import ImageProcessor

        ip = ImageProcessor()
        assert ip.get_autofill_source(64) is None
