"""
run_tests.py — Unified test runner for RNV Icon Builder
=======================================================
Runs both test sources under coverage with branch analysis (configured
in .coveragerc), then merges the data files into a single coverage report.

  Suite 1 — test_rnv_icon_builder.py    (471 unittest tests, ~1s)
  Suite 2 — tests/                       (Phase 3-8 pytest tests:
                                          application, UI, workers,
                                          properties, snapshots, benchmarks)

Usage:
    python run_tests.py              # run everything, merge, show report
    python run_tests.py --report     # regenerate report from existing data
    python run_tests.py --summary    # report with --skip-covered (gaps only)
    python run_tests.py --html       # also write HTML report to htmlcov/
    python run_tests.py --benchmark  # run only benchmarks (no coverage)
    python run_tests.py --no-merge   # debug: leave both .coverage.* files

Exit code is non-zero if either suite has failures.

────────────────────────────────────────────────────────────────────────────
NOTE: The unittest suite runs via `-m unittest` rather than as a script.
This is intentional — the test file may use os._exit() to bypass PyQt6
cleanup crashes, but os._exit() also skips coverage's atexit data flush.
Running via `-m unittest` means the file's __main__ block (where the
os._exit lives) never fires, so coverage flushes normally.

Trade-off: the colored summary printed by test_rnv_icon_builder.py's
__main__ block does NOT appear under this runner — only unittest's
default output. To see the colored summary, run the file directly:
    python test_rnv_icon_builder.py
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Use the current interpreter via -m so we don't depend on coverage/pytest
# being on PATH (more reliable on Windows than bare `coverage` / `pytest`).
PYTHON = sys.executable
COVERAGE = [PYTHON, "-m", "coverage"]

# Per-suite data files so they don't overwrite each other before merge.
UNITTEST_DATA = ".coverage.unittest"
PYTEST_DATA = ".coverage.pytest"


def _run(label: str, cmd: list[str], extra_env: dict | None = None) -> int:
    """Run a subprocess, stream its output, return its exit code.

    `extra_env` is merged onto os.environ for the child process. Used by
    the pytest suite to pass COVERAGE_PROCESS_START so subprocess.run()
    calls inside tests (e.g. CLI subprocess tests) start coverage too.
    """
    print()
    print("=" * 72)
    print(f"  {label}")
    print("=" * 72)
    print(f"  $ {' '.join(cmd)}")
    print()
    env = None
    if extra_env:
        env = dict(os.environ)
        # PYTHONPATH gets prepended (not replaced) so we don't clobber
        # any path the user already had set. All other vars overwrite.
        for key, value in extra_env.items():
            if key == "PYTHONPATH" and env.get("PYTHONPATH"):
                env[key] = value + os.pathsep + env["PYTHONPATH"]
            else:
                env[key] = value
    return subprocess.call(cmd, cwd=ROOT, env=env)


# ─── Suite runners ───────────────────────────────────────────────────────────

def run_unittest_suite() -> int:
    """Run the 471-test unittest suite under coverage.

    Uses `-m unittest` rather than executing the file directly, so:
      - The file's `os._exit()` (if present) doesn't fire (allows coverage flush)
      - The QApplication setup at top of file still runs (executes on
        import, not under __main__)
    """
    return _run(
        "Suite 1 / 2 — unittest (test_rnv_icon_builder.py)",
        [
            *COVERAGE, "run",
            f"--data-file={UNITTEST_DATA}",
            "-m", "unittest", "test_rnv_icon_builder", "-v",
        ],
    )


def run_pytest_suite() -> int:
    """Run pytest tests under coverage. Skips silently if tests/ is missing.

    Pass `--benchmark-disable` so any pytest-benchmark tests still run once
    each (verifying they don't crash) but without the timing measurements
    that would clutter output and skew results under coverage.
    """
    tests_dir = ROOT / "tests"

    if not tests_dir.is_dir():
        print("\n[skip] tests/ directory not found — pytest suite skipped.")
        return 0

    test_files = list(tests_dir.glob("test_*.py"))
    if not test_files:
        print("\n[skip] tests/ has no test_*.py files — pytest suite skipped.")
        return 0

    return _run(
        "Suite 2 / 2 — pytest (tests/)",
        [
            *COVERAGE, "run",
            f"--data-file={PYTEST_DATA}",
            "-m", "pytest", "tests/", "-v",
            "--benchmark-disable",
        ],
        # Two env vars in concert make subprocess coverage work:
        #   1. PYTHONPATH adds the project root to sys.path for every
        #      child Python, which makes Python's site-init auto-import
        #      our sitecustomize.py shim.
        #   2. COVERAGE_PROCESS_START tells that shim to start coverage
        #      immediately — most importantly for the CLI subprocess tests
        #      in test_cli.py, which would otherwise leave cli.py's
        #      coverage at 0% even when the tests run successfully.
        extra_env={
            "PYTHONPATH": str(ROOT),
            "COVERAGE_PROCESS_START": str(ROOT / ".coveragerc"),
        },
    )


def run_benchmark_suite() -> int:
    """Run only the pytest-benchmark tests with full timing — no coverage,
    which would skew the measurements.

    Triggered by `python run_tests.py --benchmark`. Skips both the unittest
    suite and coverage collection.
    """
    bench_file = ROOT / "tests" / "test_benchmarks.py"
    if not bench_file.exists():
        print("\n[skip] tests/test_benchmarks.py not found.")
        return 0

    return _run(
        "Benchmarks (no coverage)",
        [
            PYTHON, "-m", "pytest", "tests/test_benchmarks.py",
            "--benchmark-only",
            "--benchmark-columns=mean,min,max,ops,stddev",
            "-v",
        ],
    )


# ─── Coverage data handling ──────────────────────────────────────────────────

def merge_data_files() -> int:
    """Combine all .coverage.* data files into the canonical .coverage.

    Three sources need to be merged:
      1. .coverage.unittest / .coverage.pytest — the parent processes
         (named by --data-file flags in run_unittest/pytest_suite).
      2. .coverage.unittest.HOST.PID.RAND / .coverage.pytest.HOST.PID.RAND
         — those parent processes themselves under parallel mode.
      3. .coverage.HOST.PID.RAND — subprocesses spawned by tests (e.g.
         cli.py subprocess tests). These have NO per-suite prefix because
         the spawned Python doesn't inherit --data-file; it just sees
         COVERAGE_PROCESS_START and writes to the default name.

    Without #3 in the glob, all CLI subprocess coverage is dropped.
    """
    parts: list[str] = []

    # Add named base files if they exist.
    for base in (UNITTEST_DATA, PYTEST_DATA):
        if (ROOT / base).exists():
            parts.append(base)

    # Glob ALL .coverage.* files — this catches both parent parallel-mode
    # output and unprefixed subprocess output. Skip the canonical .coverage
    # itself (no dot-suffix to glob anyway) and .coveragerc.
    for p in ROOT.glob(".coverage.*"):
        name = p.name
        if name == ".coveragerc":
            continue
        if not p.is_file():
            continue
        rel = str(p.relative_to(ROOT))
        if rel not in parts:
            parts.append(rel)

    if not parts:
        print("\n[error] no coverage data files found — cannot merge.")
        return 1

    # `coverage combine` deletes input files after a successful merge.
    return subprocess.call([*COVERAGE, "combine", *parts], cwd=ROOT)


def print_report(summary: bool = False, html: bool = False) -> int:
    """Print combined report. summary=True hides 100%-covered files."""
    print()
    print("=" * 72)
    print("  Coverage report" + ("  (--skip-covered)" if summary else ""))
    print("=" * 72)

    cmd = [*COVERAGE, "report", "-m"]
    if summary:
        cmd.append("--skip-covered")
    rc = subprocess.call(cmd, cwd=ROOT)

    # Archive the full report to a text file for diffing across runs.
    try:
        with open(ROOT / "coverage_report.txt", "w", encoding="utf-8") as f:
            subprocess.call([*COVERAGE, "report", "-m"], cwd=ROOT, stdout=f)
    except Exception as e:
        print(f"[warn] couldn't archive report: {e}")

    if html:
        print()
        print("Generating HTML report at htmlcov/...")
        subprocess.call([*COVERAGE, "html"], cwd=ROOT)
        print("Open htmlcov/index.html in a browser.")

    return rc


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    args = set(sys.argv[1:])
    summary = "--summary" in args
    html = "--html" in args

    # Benchmark-only mode: skip suites + coverage, run timing.
    if "--benchmark" in args:
        return run_benchmark_suite()

    # Report-only mode: skip both suites, just regenerate from existing data.
    if "--report" in args:
        return print_report(summary=summary, html=html)

    # Clean up stale .coverage.* orphans from prior runs (subprocess
    # parallel-mode files that weren't merged) so we only combine THIS
    # run's data. Keep the canonical .coverage alone in case --report
    # is used later.
    if "--keep-stale" not in args:
        for p in ROOT.glob(".coverage.*"):
            if p.name == ".coveragerc":
                continue
            try:
                p.unlink()
            except OSError:
                pass  # File locked or missing; not fatal.

    rc1 = run_unittest_suite()
    rc2 = run_pytest_suite()

    if "--no-merge" not in args:
        merge_data_files()
        print_report(summary=summary, html=html)

    # Non-zero exit if either suite failed — useful for CI gates.
    return max(rc1, rc2)


if __name__ == "__main__":
    sys.exit(main())
