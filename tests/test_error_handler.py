"""
RNV Icon Builder — Error Handler Tests
=======================================

Phase 10A coverage push for error_handler.py (currently 33%).

Targets the dialog paths, ValidationHelper, exception_handler context
manager, and SafeFileOperations. Heavy use of monkeypatch for QMessageBox
to avoid blocking on modal dialogs.
"""

from __future__ import annotations

import os
import pytest

from PyQt6.QtWidgets import QMessageBox, QWidget


# ══════════════════════════════════════════════════════════════════════════════
# 1. ERROR HANDLER — show_error_dialog and _get_error_suggestion
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestErrorHandlerDialog:

    def test_show_error_dialog_normal(self, qapp, monkeypatch):
        from utils.error_handler import ErrorHandler

        captured: list = []
        monkeypatch.setattr(
            QMessageBox, "exec",
            lambda self: captured.append(
                ("normal", self.windowTitle(), self.text())))

        parent = QWidget()
        ErrorHandler.show_error_dialog(
            parent=parent, title="LoadError", message="Failed to load")
        assert len(captured) == 1
        assert "LoadError" in captured[0][1]

    def test_show_error_dialog_critical(self, qapp, monkeypatch):
        from utils.error_handler import ErrorHandler

        captured: list = []
        monkeypatch.setattr(
            QMessageBox, "exec",
            lambda self: captured.append(self.windowTitle()))

        parent = QWidget()
        ErrorHandler.show_error_dialog(
            parent=parent, title="DiskFull",
            message="Disk full", critical=True)
        assert "Critical" in captured[0]

    def test_get_error_suggestion_for_known_category(self):
        """ErrorCategory.FILE_IO should produce a non-empty suggestion."""
        from utils.error_handler import ErrorHandler, ErrorCategory

        result = ErrorHandler._get_error_suggestion(
            ErrorCategory.FILE_IO, "details")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_error_suggestion_for_unknown_returns_empty_or_default(self):
        """Unknown category → empty string or default suggestion."""
        from utils.error_handler import ErrorHandler

        result = ErrorHandler._get_error_suggestion(
            "MadeUpCategory", "details")
        assert isinstance(result, str)


# ══════════════════════════════════════════════════════════════════════════════
# 2. VALIDATION HELPER — pure-logic wins
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestValidationHelper:

    def test_validate_file_path_empty_returns_false(self):
        from utils.error_handler import ValidationHelper

        valid, error = ValidationHelper.validate_file_path("")
        assert valid is False
        assert "empty" in error.lower()

    def test_validate_file_path_missing_returns_false(self):
        from utils.error_handler import ValidationHelper

        valid, error = ValidationHelper.validate_file_path(
            "/no/such/file.png", must_exist=True)
        assert valid is False
        assert "exist" in error.lower()

    def test_validate_file_path_existing_returns_true(self, sample_png):
        from utils.error_handler import ValidationHelper

        path = sample_png(name="exists.png")
        valid, error = ValidationHelper.validate_file_path(
            path, must_exist=True)
        assert valid is True
        assert error == ""

    def test_validate_file_path_wrong_extension_returns_false(
            self, sample_png):
        from utils.error_handler import ValidationHelper

        path = sample_png(name="mismatch.png")
        valid, error = ValidationHelper.validate_file_path(
            path, must_exist=True, extensions=[".ico", ".svg"])
        assert valid is False
        assert "type" in error.lower() or "extension" in error.lower()

    def test_validate_image_size_non_square_fails(self):
        from utils.error_handler import ValidationHelper

        valid, error = ValidationHelper.validate_image_size(
            64, 32, must_be_square=True)
        assert valid is False
        assert "square" in error.lower()

    def test_validate_image_size_invalid_in_list_fails(self):
        from utils.error_handler import ValidationHelper

        valid, error = ValidationHelper.validate_image_size(
            100, 100, valid_sizes=[16, 32, 64, 128, 256])
        assert valid is False
        assert "size" in error.lower() or "valid" in error.lower()

    def test_validate_image_size_valid_returns_true(self):
        from utils.error_handler import ValidationHelper

        valid, error = ValidationHelper.validate_image_size(
            64, 64, valid_sizes=[16, 32, 64, 128])
        assert valid is True
        assert error == ""

    def test_validate_image_size_zero_dim_fails(self):
        from utils.error_handler import ValidationHelper

        valid, error = ValidationHelper.validate_image_size(
            0, 0, must_be_square=False)
        assert valid is False


# ══════════════════════════════════════════════════════════════════════════════
# 3. EXCEPTION HANDLER CONTEXT MANAGER
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestExceptionHandlerContextManager:

    def test_exception_handler_swallows_exception(self):
        """exception_handler context manager catches and logs exceptions."""
        from utils.error_handler import exception_handler

        # Should not raise — the context manager swallows it.
        with exception_handler("test_op", show_error=False):
            raise ValueError("boom")

    def test_exception_handler_no_exception_runs_clean(self):
        from utils.error_handler import exception_handler

        result_set = []
        with exception_handler("clean_op", show_error=False):
            result_set.append("ran")
        assert result_set == ["ran"]


# ══════════════════════════════════════════════════════════════════════════════
# 4. STYLED MESSAGE BOX HELPERS
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestStyledMessageBoxes:

    def test_get_message_box_style_returns_string(self, qapp):
        from utils.error_handler import get_message_box_style

        result = get_message_box_style(parent=None)
        assert isinstance(result, str)
        # Must contain at least one CSS-style declaration.
        assert "{" in result and "}" in result
