# RNV Icon Builder — Test System

This document is the reference for the test system added during the
Phase 1–9 expansion. It explains what's there, how to run it, and how to
maintain it going forward.

---

## TL;DR

```bash
pip install -r requirements-test.txt   # one time
python run_tests.py                    # everyday: full suite + coverage
python run_tests.py --html             # also produce htmlcov/index.html
python run_tests.py --benchmark        # timing report (no coverage)
python tests/test_snapshots.py         # regenerate snapshots after intentional output changes
mutmut run                              # mutation audit (slow — minutes to hours per module)
```

---

## What's in here

```
RNV_Icon_Builder/
├── test_rnv_icon_builder.py    ← Original 471-test unittest suite (root)
├── tests/
│   ├── conftest.py             ← Shared fixtures + path bootstrap
│   ├── test_application.py     ← Application-level (Phase 3)
│   ├── test_ui_interactions.py ← Dialogs / widgets via qtbot (Phase 4)
│   ├── test_workers.py         ← BatchProcessor / FolderWatcher signals (Phase 5)
│   ├── test_properties.py      ← Hypothesis property-based tests (Phase 6)
│   ├── test_snapshots.py       ← Output format locks (Phase 7)
│   ├── test_benchmarks.py      ← pytest-benchmark perf tests (Phase 8)
│   ├── test_utilities.py       ← error/signal/font/dialog/session (Phase 8b)
│   └── snapshots.json          ← Reference data for snapshot tests
├── pytest.ini                  ← pytest config, marker registry
├── .coveragerc                 ← branch coverage config
├── setup.cfg                   ← mutmut config
├── requirements-test.txt       ← Pinned test dependencies
└── run_tests.py                ← Unified runner (both suites + report)
```

---

## Running tests

### Everyday: full suite with coverage

```bash
python run_tests.py
```

Runs both suites (`test_rnv_icon_builder.py` via unittest, then `tests/` via
pytest), merges coverage data, and prints the report.

**Expected output:** 471 unittest + 175 pytest = **646 tests passing**,
**~57% branch coverage**.

### Other run_tests.py modes

| Flag | What it does |
|---|---|
| `--report` | Print report from the cached `.coverage` file (no test run) |
| `--summary` | Same, with `--skip-covered` (hide 100%-covered files) |
| `--html` | Also write `htmlcov/index.html` for a clickable drill-down |
| `--benchmark` | Run only `test_benchmarks.py` with full timing, no coverage |
| `--no-merge` | Debug — leave both `.coverage.unittest` and `.coverage.pytest` |

### Direct pytest (when iterating on one file)

```bash
pytest tests/test_workers.py -v             # one file
pytest tests/test_application.py::TestIconBuilderAppInit -v   # one class
pytest -m "not benchmark"                    # exclude benchmarks
pytest -m "ui"                               # only UI interaction tests
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

Mutmut introduces small mutations to your source and re-runs the test
suite for each one. A surviving mutant means a test gap.

```bash
mutmut run                  # uses setup.cfg [mutmut] config
mutmut results              # see surviving mutants
mutmut show <id>            # inspect a specific mutant
```

`setup.cfg` is set to mutate one module at a time (default: `colors.py`).
Edit the `paths_to_mutate` line to audit a different module.

**Why one module at a time:** a full-project mutation run generates
thousands of mutants × ~30s per test run = many hours. Running per-module
keeps each audit under an hour. Suggested rotation: when you make
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

## Honest assessment of coverage

The aggregate is 57.05%. Most of the remaining 43% falls into three
categories — only the first is worth chasing:

1. **`error_handler.py` (33%)** — the QMessageBox-driven dialog paths.
   Pushable to ~70% with maybe 15 more tests, all involving deeper
   monkeypatching of QMessageBox. Real value, real gap.

2. **`RNV_Icon_Builder.py` (30%)** — the menu handlers, export
   pipelines, and detailed widget-level paint code in the 1,614-line
   main window. Each handler is a small target individually but there
   are many of them. Diminishing returns past Phase 4's 30%.

3. **`cli.py` (0%), `async_file_ops.py` (19%), `debug_button.py` (16%)** —
   by-design low coverage. CLI is best tested via subprocess in CI.
   async_file_ops needs a real event loop. debug_button is a dev tool.

Hitting 70% aggregate is achievable; hitting 80% would require pulling
from category 2, which mostly tests Qt rather than your code.

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
