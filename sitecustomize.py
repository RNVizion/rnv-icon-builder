"""
RNV Icon Builder — sitecustomize.py
====================================

This module is imported automatically by every Python interpreter startup
in the project root. We use it to bootstrap coverage measurement in
subprocesses so the CLI tests in test_cli.py actually contribute coverage
data for cli.py.

How it works:
  - When run_tests.py runs the suite, it sets the environment variable
    COVERAGE_PROCESS_START=.coveragerc.
  - When pytest spawns `python cli.py ...` via subprocess.run, the new
    Python process imports this file at startup.
  - The check below detects the env var and starts coverage immediately,
    so cli.py executes under coverage measurement.
  - On normal app runs (no env var), this is a no-op — zero overhead.

This file is NOT imported when running the actual application; only when
the test runner has explicitly opted in via COVERAGE_PROCESS_START.
"""

import os

if os.environ.get("COVERAGE_PROCESS_START"):
    try:
        import coverage
        coverage.process_startup()
    except ImportError:
        # coverage isn't installed in this env (e.g. production install);
        # silently no-op so the app still starts cleanly.
        pass
