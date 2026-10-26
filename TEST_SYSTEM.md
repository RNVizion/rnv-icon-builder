# RNV Icon Builder — Test System

This document is the reference for the test system added during the
Phase 1–9 expansion. It explains what's there, how to run it, and how to
maintain it going forward.

---

## TL;DR

```bash
pip install -r tests/requirements-dev.txt   # one time
python run_tests.py                    # everyday: full suite + coverage
python run_tests.py --html             # also produce htmlcov/index.html
python run_tests.py --benchmark        # timing report (no coverage)
python tests/test_snapshots.py         # regenerate snapshots after intentional output changes
python -m mutmut run                   # mutation audit of the module named in setup.cfg
```

---

## What's in here

```
RNV_Icon_Builder/
├── test_rnv_icon_builder.py    ← The original unittest suite (root)
├── tests/
│   ├── conftest.py             ← Shared fixtures + path bootstrap
│   ├── color_values.py         ← Every color value a test needs that is not the app's
│   ├── snapshots.json          ← Reference data for snapshot tests
│   ├── test_*.py               ← The pytest suite, one file per area (below)
│   └── requirements-dev.txt    ← Test dependencies, and rnv-brand at its pinned commit
├── pytest.ini                  ← pytest config, marker registry
├── .coveragerc                 ← branch coverage config
├── sitecustomize.py            ← starts coverage in subprocesses (the CLI tests)
├── setup.cfg                   ← mutmut config
└── run_tests.py                ← Unified runner (both suites + report)
```

The files in `tests/`, by what they hold:

| Files | Hold |
|---|---|
| `test_application.py` | Application-level tests of the main window (Phase 3) |
| `test_ui_interactions.py` | Dialogs and widgets via qtbot (Phase 4) |
| `test_workers.py` | BatchProcessor / FolderWatcher signals (Phase 5) |
| `test_properties.py` | Hypothesis property-based tests (Phase 6) |
| `test_snapshots.py` | Output format locks (Phase 7) |
| `test_benchmarks.py` | pytest-benchmark performance tests (Phase 8) |
| `test_utilities.py` | error, signal, font, dialog and session utilities (Phase 8b) |
| `test_cli.py` | The command-line interface, run as a subprocess and by direct calls |
| `test_main_window.py`, `test_settings_dialog.py`, `test_managers.py`, `test_image_processor.py`, `test_preview_utils.py`, `test_error_handler.py`, `test_folder_watcher.py` | Deeper tests of the main window, the Settings dialog, the managers and the core and utility modules |
| `test_settings_do_what_they_say.py`, `test_features_a_user_can_reach.py` | Restoring the last session, the project auto-save and the filename template; the metadata panel and a dropped folder |
| `test_color_values.py` and the other `test_*.py` | Guard tests: rules about colors and contrast, dependencies and setup, images, workflows and the docs (see *Guard tests* below) |

`python -m pytest tests/ --collect-only -q` lists every test.

---

## Running tests

### Everyday: full suite with coverage

```bash
python run_tests.py
```

Runs both suites (`test_rnv_icon_builder.py` via unittest, then `tests/` via
pytest), merges coverage data, and prints the report.

**Expected output:** over 400 unittest + over 600 pytest = **over 1,100 tests passing**.

Coverage is measured on every full run. `python run_tests.py --report` prints the current
figure for every module; it differs a little between Windows and Linux.

### Other run_tests.py modes

| Flag | What it does |
|---|---|
| `--report` | Print report from the cached `.coverage` file (no test run) |
| `--summary` | The printed report leaves out 100%-covered files (`--skip-covered`); with `--report` it skips the test run too |
| `--html` | Also write `htmlcov/index.html` for a clickable drill-down |
| `--fail-under=N` | Exit non-zero if total coverage is under N%. CI runs `--html --fail-under=66` and uploads `htmlcov/` |
| `--benchmark` | Run only `test_benchmarks.py` with full timing, no coverage |
| `--no-merge` | Debug — leave `.coverage.unittest` and `.coverage.pytest` unmerged, and print no report |
| `--keep-stale` | Keep `.coverage.*` files left by an earlier run instead of deleting them first |

Every report the runner prints is also written in full to `coverage_report.txt`.

### Direct pytest (when iterating on one file)

```bash
python -m pytest tests/test_workers.py -v             # one file
python -m pytest tests/test_application.py::TestIconBuilderAppInit -v   # one class
python -m pytest -m "not benchmark"                    # exclude benchmarks
python -m pytest -m "ui"                               # only UI interaction tests
```

Markers registered in `pytest.ini`: `slow`, `benchmark`, `ui`,
`integration`, `snapshot`, `property`, `application`, `worker`.

---

## Maintaining each phase

### Snapshots (Phase 7) — when a format change is intentional

When you knowingly change `BatchJob.to_dict()` shape, scrollbar styling, or
ICO pipeline defaults, the snapshot tests will fail. Regenerate:

```bash
python tests/test_snapshots.py
```

This rewrites `tests/snapshots.json` from the current code. Inspect the
diff before committing — if it contains changes you didn't make, that's
a real regression.

### Benchmarks (Phase 8) — establishing a baseline

```bash
python run_tests.py --benchmark > bench-baseline.txt
```

Re-run after performance work and `diff` against the baseline. If a hot
path got 10× slower, you'll see it.

### Mutation testing (Phase 9) — periodic audit

Mutmut introduces small mutations to your source and re-runs the tests
for each one. A surviving mutant means a test gap. `setup.cfg` is written
for mutmut 3; a fresh install of `tests/requirements-dev.txt` gets a 3.x
release.

```bash
python -m mutmut run                  # uses the [mutmut] section of setup.cfg
python -m mutmut results              # list the surviving mutants
python -m mutmut show <name>          # inspect one mutant's diff
python -m mutmut browse               # browse the results interactively
```

mutmut copies the code into `mutants/` at the repository root (git
ignores it) and runs pytest there. The `[mutmut]` section says:

- `source_paths` — the module to mutate (`ui/image_adjustments.py`);
- `also_copy` — what the tests import besides it: `core`, `utils`, `ui`,
  `pytest.ini` and `brand_map.json` (mutmut copies `tests/`,
  `setup.cfg`, `pyproject.toml` and the root `test*.py` by itself);
- `pytest_add_cli_args_test_selection` — the tests to run against each
  mutant (`test_rnv_icon_builder.py::TestImageAdjustments`).

To audit a different module, change `source_paths` and the tests named
under it. There is no HTML report in mutmut 3.

**Why one module at a time:** a full-project run generates thousands of
mutants, each needing a test run. Scoped to one module and the tests that
exercise it, a run takes minutes. Suggested rotation: when you make
significant changes to a module, run mutmut on it.

---

## What changed across the phases

| Phase | What it added | Tests | Branch coverage after |
|---|---|---|---|
| Baseline | (existing 471 unittest tests) | 471 | 30.66% |
| Phase 1 | pytest infra, `tests/`, conftest, runner | 471 | 30.66% |
| Phase 2 | Coverage measurement (no new tests) | 471 | 30.66% |
| Phase 3 | Application-level tests | +42 | 36.93% |
| Phase 4 | UI interaction tests with qtbot | +44 | 54.09% |
| Phase 5 | Worker / signal-spy tests | +22 | 55.60% |
| Phase 6 | Hypothesis property-based tests | +14 | 55.60% |
| Phase 7 | Snapshot tests for output formats | +14 | 55.62% |
| Phase 8 | pytest-benchmark performance tests | +12 | 55.75% |
| Phase 8b | Utility-module mop-up | +27 | **57.05%** |
| Phase 9 | Mutation testing audit | (no tests) | 57.05% |

**Total: 175 new pytest tests + 471 retained unittest tests = 646 tests.**

---

## Where coverage is thin

`python run_tests.py --report` lists every module, least covered last.
The gaps fall into a few kinds:

1. **`RNV_Icon_Builder.py`** — the menu handlers, export pipelines, and
   detailed widget-level paint code in the main window. Each handler is
   a small target individually but there are many of them.

2. **`ui/debug_button.py`** — `DebugButton`, the main window's action
   buttons (Select Files, Select Folder, Clear Files, Build ICO), which
   swap their base, hover and pressed images on mouse events in image
   mode. The suite drives those events only in part.

3. **`utils/async_file_ops.py`** — needs a real event loop.

The CLI is covered by `tests/test_cli.py`, through a subprocess that
`sitecustomize.py` puts under coverage, and by direct calls.

---

## Where blind spots remain

The eight critique items from the original analysis:

| # | Item | Status |
|---|---|---|
| 1 | coverage.py with branch coverage | **Done** (Phase 1) |
| 2 | pytest-qt with qtbot | **Done** (Phase 4) |
| 3 | Application-level tests | **Done** (Phase 3) |
| 4 | hypothesis property-based tests | **Done** (Phase 6) |
| 5 | mutation testing via mutmut | **Done** (Phase 9, scoped) |
| 6 | Real worker tests with QSignalSpy | **Done** (Phase 5) |
| 7 | pytest-benchmark | **Done** (Phase 8) |
| 8 | Snapshot tests | **Done** (Phase 7) |

Compared to the original "40–50% of the way there" assessment for the
Color Mixer suite, this codebase now has all eight infrastructure
components in place.

---

## Guard tests

Besides the tests of the app's behavior, a set of guard tests holds rules that span the
repository:

| Test | Holds |
|---|---|
| `tests/test_colors_in_sync.py` | the color file and `COLORS.md` are what `brand_map.json` and the pinned brand say |
| `tests/test_register_pin.py` | the installed rnv-brand is the pinned commit |
| `tests/test_atomic_state_writes.py` | every file the app keeps is written atomically |
| `tests/test_status_carried_by_a_word.py` | a status is never shown by color alone: each one has a word or a mark beside it |
| `tests/test_accent_images.py` | `ACCENT_IMAGES.md` matches the images |
| `tests/test_setup_scripts.py` | `in.sh` and `in.ps1` install the same files |
| `tests/test_readme_test_counts.py` | every test count the docs state is a floor that holds |
