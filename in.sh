#!/usr/bin/env bash
# Codespace setup + test run for any of the five RNV PyQt6 apps.
#
# WHY THIS EXISTS IN THIS FORM
#
# The previous version installed from `requirements-test.txt` by name. Three
# of the five repos have now moved that file to `tests/requirements-dev.txt`,
# so a hardcoded path breaks the moment its repo is updated -- and it breaks
# in the least helpful way: pip exits non-zero, the shell carries on, and the
# failure surfaces three commands later as "No module named coverage".
#
# So this looks for the file instead of assuming where it is, and REFUSES to
# continue if the install fails rather than letting a later step report the
# symptom instead of the cause.

set -euo pipefail

# ---------------------------------------------------------------------------
# 1. System libraries
#
# PyQt6's wheels bundle Qt itself but not the X/GL libraries it links against.
# A fresh codespace has none of them, which surfaces as
# `ImportError: libGL.so.1: cannot open shared object file` at import time --
# a message that names a file pip cannot install and never mentions Qt.
#
# xvfb is deliberately NOT installed. QT_QPA_PLATFORM=offscreen below makes Qt
# skip the display entirely, so there is nothing for a virtual X server to do.
# ---------------------------------------------------------------------------

echo "==> system libraries"
sudo apt-get update -qq
sudo apt-get install -y -qq --no-install-recommends \
  libegl1 libgl1 libglib2.0-0 libxkbcommon0 \
  libdbus-1-3 libfontconfig1 libxcb-cursor0 \
  libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
  libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
  libxcb-sync1 libxcb-xfixes0 libxcb-xinerama0 \
  libxcb-xkb1 libxkbcommon-x11-0

# ---------------------------------------------------------------------------
# 2. Python dependencies
#
# Found, not assumed. The test-dependency file is at one of two paths
# depending on whether that repo's move has landed yet.
# ---------------------------------------------------------------------------

echo "==> python dependencies"
# Non-fatal. On a Debian-managed interpreter this fails with "Cannot
# uninstall pip ... installed by debian", and under `set -e` that would abort
# the whole script over a cosmetic upgrade nobody asked for.
python -m pip install --quiet --upgrade pip 2>/dev/null \
  || echo "  (pip self-upgrade skipped -- system-managed pip)"

if [ -f requirements.txt ]; then
  pip install --quiet -r requirements.txt
else
  echo "  no requirements.txt at the repository root -- are you in the right"
  echo "  directory?" >&2
  exit 1
fi

TEST_DEPS=""
for candidate in tests/requirements-dev.txt requirements-dev.txt \
                 tests/requirements-test.txt requirements-test.txt; do
  if [ -f "$candidate" ]; then
    TEST_DEPS="$candidate"
    break
  fi
done

if [ -z "$TEST_DEPS" ]; then
  echo "  could not find a test-dependency file. Looked for:" >&2
  echo "    tests/requirements-dev.txt   (where all six repos are heading)" >&2
  echo "    requirements-dev.txt" >&2
  echo "    tests/requirements-test.txt" >&2
  echo "    requirements-test.txt" >&2
  exit 1
fi

echo "  test dependencies: $TEST_DEPS"
pip install --quiet -r "$TEST_DEPS"

# Prove the thing every runner actually needs is importable. Without this the
# next failure is "No module named coverage" from inside a subprocess, several
# screens away from the install that did not happen.
python - <<'PY'
# `import importlib` alone does NOT bind importlib.util -- it is a submodule
# and needs importing by name. Written the short way this raises
# AttributeError, the check fails every single time, and the script aborts
# reporting a missing package that is sitting right there. A guard that fails
# like the thing it guards is worse than no guard.
import importlib.util
import sys
missing = [name for name in ("coverage", "pytest")
           if importlib.util.find_spec(name) is None]
if missing:
    sys.exit(f"  installed, but still cannot import: {', '.join(missing)}")
print("  coverage and pytest are importable")
PY

# ---------------------------------------------------------------------------
# 3. Run
#
# QT_QPA_PLATFORM must be set in the ENVIRONMENT, not left to conftest.py.
# Several of these repos set it in tests/conftest.py -- but conftest is a
# pytest mechanism, and the unittest half of the suite never loads it. Setting
# it here covers both halves.
# ---------------------------------------------------------------------------

export QT_QPA_PLATFORM=offscreen

echo "==> tests"
if [ -f run_tests.py ]; then
  python run_tests.py "$@"
else
  # Repos without a unified runner: both suites, explicitly.
  for locked in test_rnv_*.py; do
    [ -e "$locked" ] || continue
    echo "--- $locked ---"
    python -m pytest "$locked" -q
  done
  echo "--- tests/ ---"
  python -m pytest tests/ -q
fi
