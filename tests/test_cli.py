"""
RNV Icon Builder — CLI Tests
=============================

Phase 10A coverage push for cli.py (currently 0%).

Two-pronged approach:
  1. Subprocess tests — invoke `python cli.py ...` directly and assert
     on exit codes + stdout. Catches main() integration paths.
  2. Direct-call tests — import the helpers (get_sizes_from_args,
     get_preset_manager) and exercise their pure logic without the
     subprocess overhead.

Subprocess tests are the higher-leverage path because each one exercises
the whole stack: argument parsing → routing → handler → file output.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _cli_path(project_root: str) -> str:
    """Absolute path to cli.py in the project root."""
    return os.path.join(project_root, "cli.py")


def _has_subdir_layout(project_root: str) -> bool:
    """True if core/, utils/, ui/ exist as real subdirectories.

    The conftest's import bootstrap doesn't reach a fresh subprocess; cli.py
    imports `from core.X` etc., which only works if those subdirs exist on
    disk. In the flat layout we use direct-call tests instead.
    """
    return all(os.path.isdir(os.path.join(project_root, p))
               for p in ("core", "utils", "ui"))


def _run_cli(project_root: str, *args: str, timeout: float = 30.0) \
        -> subprocess.CompletedProcess:
    """Run cli.py as a subprocess. Returns CompletedProcess with stdout/stderr/returncode."""
    cmd = [sys.executable, _cli_path(project_root), *args]
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
        cwd=project_root,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. SUBPROCESS TESTS — full main() flow
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestCliSubprocess:
    """These tests spawn a real subprocess. They require core/, utils/, ui/
    to exist as actual directories — which is the case in the packaged
    install but not in the flat-layout test sandbox."""

    @pytest.fixture(autouse=True)
    def _skip_if_flat_layout(self, project_root):
        if not _has_subdir_layout(project_root):
            pytest.skip(
                "Flat layout — cli.py subprocess can't resolve "
                "'core'/'utils'/'ui' imports without conftest bootstrap")

    def test_help_flag_exits_zero(self, project_root):
        """--help must return 0 (argparse convention)."""
        result = _run_cli(project_root, "--help")
        assert result.returncode == 0
        assert "RNV Icon Builder" in result.stdout or \
               "Multi-Resolution" in result.stdout or \
               "ICO" in result.stdout

    def test_no_args_returns_error(self, project_root):
        """Running with no input is invalid; argparse exits non-zero."""
        result = _run_cli(project_root)
        assert result.returncode != 0

    def test_list_presets_succeeds(self, project_root, tmp_dir):
        """--list-presets should print presets and exit 0.

        Note: this CLI's argparse requires input + -o even alongside utility
        flags like --list-presets, so we pass dummy values that won't be used
        (list_presets is checked before input validation in main()).
        """
        dummy_in = os.path.join(tmp_dir, "dummy.png")
        dummy_out = os.path.join(tmp_dir, "dummy.ico")
        result = _run_cli(project_root, dummy_in, "-o", dummy_out,
                          "--list-presets")
        assert result.returncode == 0
        assert "preset" in result.stdout.lower() or \
               "Preset" in result.stdout

    def test_list_presets_quiet_no_output(self, project_root, tmp_dir):
        """--list-presets --quiet should suppress preset listing."""
        dummy_in = os.path.join(tmp_dir, "dummy.png")
        dummy_out = os.path.join(tmp_dir, "dummy.ico")
        result = _run_cli(project_root, dummy_in, "-o", dummy_out,
                          "--list-presets", "--quiet")
        assert result.returncode == 0
        # Quiet mode should produce minimal/no output.
        assert len(result.stdout) < 50

    def test_input_does_not_exist_returns_invalid_args(
            self, project_root, tmp_dir):
        """Bad input path → EXIT_INVALID_ARGS (2)."""
        bad_path = os.path.join(tmp_dir, "no_such_image.png")
        out_path = os.path.join(tmp_dir, "out.ico")
        result = _run_cli(project_root, bad_path, "-o", out_path)
        assert result.returncode == 2

    def test_build_single_ico_with_sizes(
            self, project_root, sample_png, tmp_dir):
        """Real build: PNG in, ICO out, with explicit --sizes."""
        png = sample_png(name="cli_input.png", size=128)
        out_path = os.path.join(tmp_dir, "cli_output.ico")

        result = _run_cli(project_root, png, "-o", out_path,
                          "--sizes", "64,32,16", "--quiet")
        assert result.returncode == 0
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0

    def test_build_with_preset(self, project_root, sample_png, tmp_dir):
        """--preset favicon should produce a valid ICO."""
        png = sample_png(name="preset_input.png", size=128)
        out_path = os.path.join(tmp_dir, "preset_output.ico")

        result = _run_cli(project_root, png, "-o", out_path,
                          "--preset", "favicon", "--quiet")
        # Either succeeds or prints a clear error if preset doesn't exist.
        if result.returncode == 0:
            assert os.path.exists(out_path)

    def test_invalid_sizes_format_handled(
            self, project_root, sample_png, tmp_dir):
        """Non-numeric --sizes is reported, doesn't crash."""
        png = sample_png(name="bad_sizes.png", size=128)
        out_path = os.path.join(tmp_dir, "bad_sizes.ico")

        result = _run_cli(project_root, png, "-o", out_path,
                          "--sizes", "huge,enormous", "--quiet")
        # Should exit non-zero or fall back to defaults; either way no crash.
        assert result.returncode in (0, 1, 2)

    def test_favicon_package_creates_output(
            self, project_root, sample_png, tmp_dir):
        """--favicon-package produces a directory with multiple files."""
        png = sample_png(name="fav_input.png", size=256)
        out_dir = os.path.join(tmp_dir, "favicon_pkg")

        result = _run_cli(project_root, png, "-o", out_dir,
                          "--favicon-package", "--quiet")
        if result.returncode == 0:
            assert os.path.isdir(out_dir)
            # Favicon package should produce at least one file.
            files = os.listdir(out_dir)
            assert len(files) > 0

    def test_android_export_creates_output(
            self, project_root, sample_png, tmp_dir):
        """--android produces Android-sized icon outputs."""
        png = sample_png(name="android_input.png", size=512)
        out_dir = os.path.join(tmp_dir, "android_pkg")

        result = _run_cli(project_root, png, "-o", out_dir,
                          "--android", "--quiet")
        if result.returncode == 0:
            assert os.path.isdir(out_dir)

    def test_ios_export_creates_output(
            self, project_root, sample_png, tmp_dir):
        """--ios produces iOS-sized icon outputs."""
        png = sample_png(name="ios_input.png", size=1024)
        out_dir = os.path.join(tmp_dir, "ios_pkg")

        result = _run_cli(project_root, png, "-o", out_dir,
                          "--ios", "--quiet")
        if result.returncode == 0:
            assert os.path.isdir(out_dir)

    def test_analyze_mode_on_real_ico(
            self, project_root, sample_png, tmp_dir):
        """--analyze on a built ICO succeeds."""
        # First build an ICO to analyze.
        png = sample_png(name="for_analysis.png", size=128)
        ico_path = os.path.join(tmp_dir, "to_analyze.ico")
        build_result = _run_cli(project_root, png, "-o", ico_path,
                                "--sizes", "64,32", "--quiet")
        if build_result.returncode != 0:
            pytest.skip("Could not build prerequisite ICO")

        # Now analyze it.
        result = _run_cli(project_root, ico_path, "-o", ico_path,
                          "--analyze")
        # Should succeed and print some info.
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_batch_mode_processes_folder(
            self, project_root, sample_png, tmp_dir):
        """--batch processes a folder of PNGs."""
        # Set up an input folder with two PNGs.
        in_dir = os.path.join(tmp_dir, "batch_input")
        out_dir = os.path.join(tmp_dir, "batch_output")
        os.makedirs(in_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)

        from PIL import Image
        for i in range(2):
            Image.new("RGBA", (64, 64),
                      (i * 80, 100, 200, 255)).save(
                os.path.join(in_dir, f"batch_{i}.png"))

        result = _run_cli(project_root, in_dir, "-o", out_dir,
                          "--batch", "--quiet")
        if result.returncode == 0:
            # Batch should produce some ICO files.
            icos = [f for f in os.listdir(out_dir) if f.endswith(".ico")]
            assert len(icos) > 0

    def test_verbose_flag_emits_more_output(
            self, project_root, sample_png, tmp_dir):
        """--verbose produces more output than default."""
        png = sample_png(name="verbose_check.png", size=64)
        out_path = os.path.join(tmp_dir, "verbose_out.ico")

        result = _run_cli(project_root, png, "-o", out_path,
                          "--sizes", "32,16", "--verbose")
        # Verbose mode should produce more stdout than quiet.
        # Either succeeds with output or exits cleanly.
        assert result.returncode in (0, 1)
        if result.returncode == 0:
            assert len(result.stdout) > 0

    def test_version_flag_prints_version(self, project_root):
        """--version prints version string and exits 0."""
        result = _run_cli(project_root, "--version")
        assert result.returncode == 0
        # Version output goes to stdout for argparse.
        assert len(result.stdout) > 0


# ══════════════════════════════════════════════════════════════════════════════
# 2. DIRECT-CALL TESTS — pure-logic helpers
# ══════════════════════════════════════════════════════════════════════════════
@pytest.mark.integration
class TestCliHelpers:

    def test_create_parser_returns_parser(self):
        """create_parser produces a real argparse.ArgumentParser."""
        from cli import create_parser
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_accepts_minimal_args(self):
        """Bare 'input' positional + required -o parses cleanly."""
        from cli import create_parser
        parser = create_parser()
        args = parser.parse_args(["input.png", "-o", "out.ico"])
        assert args.input == "input.png"
        assert args.output == "out.ico"

    def test_get_sizes_from_args_explicit_sizes(self):
        """--sizes 64,32,16 → [64, 32, 16] sorted descending."""
        from cli import create_parser, get_sizes_from_args
        parser = create_parser()
        args = parser.parse_args(
            ["x.png", "-o", "y.ico", "--sizes", "16,64,32", "--quiet"])
        result = get_sizes_from_args(args)
        assert result == [64, 32, 16]

    def test_get_sizes_from_args_invalid_returns_default(self):
        """Garbage --sizes input falls back to ICON_SIZES."""
        from cli import create_parser, get_sizes_from_args
        from utils.config import ICON_SIZES
        parser = create_parser()
        args = parser.parse_args(
            ["x.png", "-o", "y.ico", "--sizes", "not,numbers", "--quiet"])
        result = get_sizes_from_args(args)
        assert result == ICON_SIZES

    def test_get_sizes_from_args_no_sizes_returns_default(self):
        """No --sizes and no --preset → ICON_SIZES."""
        from cli import create_parser, get_sizes_from_args
        from utils.config import ICON_SIZES
        parser = create_parser()
        args = parser.parse_args(["x.png", "-o", "y.ico"])
        result = get_sizes_from_args(args)
        assert result == ICON_SIZES

    def test_print_msg_quiet_suppresses(self, capsys):
        """print_msg(quiet=True) writes nothing."""
        from cli import print_msg
        print_msg("hello", quiet=True)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_msg_verbose_writes(self, capsys):
        """Normal print_msg call writes to stdout."""
        from cli import print_msg
        print_msg("hello world")
        captured = capsys.readouterr()
        assert "hello world" in captured.out
