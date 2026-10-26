"""CI holds a coverage floor and uploads an HTML report that exists (#97 A).

WHAT WAS THERE. Both test workflows ran `python run_tests.py` with no flags.
run_tests.py ignored the report's exit code, and nothing passed a floor, so
coverage could fall to any figure and the run stayed green. Each workflow then
uploaded htmlcov/, which only `--html` writes, so the upload was always empty;
`if-no-files-found: ignore` kept that quiet.

WHAT IS THERE NOW. Both workflows run `run_tests.py --html --fail-under=66`.
`--fail-under=N` is handed to `coverage report`, and its exit code becomes the
runner's when a floor is given; without one the runner exits as it always
did. 66 is a few points under the lower platform's total when it was set.

WHAT THIS GUARD HOLDS.

1. Both test workflows pass `--html` and the same `--fail-under`, and upload
   the folder `.coveragerc` writes the HTML report to.
2. run_tests.py fails a run whose report is under the floor, passes the floor
   to coverage, writes the HTML report with `--html`, and leaves a run without
   `--fail-under` as it was.

WHAT IT CANNOT HOLD. The coverage figure itself; only a full run prints it.
"""
from __future__ import annotations

import configparser
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ("tests-linux.yml", "tests-windows.yml")
RUN = re.compile(r"^\s*run:\s*(?:xvfb-run -a\s+)?python run_tests\.py(?P<flags>.*)$", re.M)


def _workflow(name: str) -> str:
    return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def _run_flags(name: str) -> list[str]:
    runs = RUN.findall(_workflow(name))
    assert len(runs) == 1, f"{name}: expected one step that runs run_tests.py, found {len(runs)}"
    return runs[0].split()


def test_both_workflows_hold_the_same_floor_and_write_the_html_report():
    floors = {}
    for name in WORKFLOWS:
        flags = _run_flags(name)
        assert "--html" in flags, f"{name}: run_tests.py runs without --html, so htmlcov/ is empty"
        floor = [f.partition("=")[2] for f in flags if f.startswith("--fail-under=")]
        assert len(floor) == 1 and re.fullmatch(r"\d+(\.\d+)?", floor[0]), \
            f"{name}: run_tests.py runs with no numeric --fail-under"
        floors[name] = float(floor[0])
    assert len(set(floors.values())) == 1, f"the workflows hold different floors: {floors}"
    assert 50 <= next(iter(floors.values())) <= 100, floors


def test_the_upload_names_the_folder_the_html_report_is_written_to():
    config = configparser.ConfigParser()
    config.read(ROOT / ".coveragerc", encoding="utf-8")
    folder = config.get("html", "directory", fallback="htmlcov").strip()
    for name in WORKFLOWS:
        assert re.search(rf"^\s*path:\s*{re.escape(folder)}/?\s*$", _workflow(name), re.M), \
            f"{name}: the upload does not name {folder}/"


@pytest.fixture
def runner(monkeypatch, tmp_path):
    """run_tests with the suites stubbed and every subprocess recorded.

    `coverage report` exits 2 when it is given a floor above the fake total
    of 60%, as coverage does.
    """
    import run_tests

    calls: list[list[str]] = []

    def fake_call(cmd, cwd=None, stdout=None, env=None):
        calls.append(list(cmd))
        floor = [c.partition("=")[2] for c in cmd if str(c).startswith("--fail-under=")]
        if "report" in cmd and floor and float(floor[0]) > 60:
            return 2
        return 0

    monkeypatch.setattr(run_tests, "ROOT", tmp_path)
    monkeypatch.setattr(run_tests, "run_unittest_suite", lambda: 0)
    monkeypatch.setattr(run_tests, "run_pytest_suite", lambda: 0)
    monkeypatch.setattr(run_tests, "merge_data_files", lambda: 0)
    monkeypatch.setattr(run_tests.subprocess, "call", fake_call)

    def run(*flags: str) -> tuple[int, list[list[str]]]:
        calls.clear()
        monkeypatch.setattr(run_tests.sys, "argv", ["run_tests.py", *flags])
        return run_tests.main(), list(calls)

    return run


def test_a_run_under_the_floor_fails(runner):
    rc, calls = runner("--html", "--fail-under=66")
    assert rc != 0, "a report under --fail-under did not fail the run"
    assert any("report" in c and "--fail-under=66" in c for c in calls), calls
    assert any("html" in c for c in calls), "--html wrote no HTML report"


def test_a_run_over_the_floor_passes(runner):
    rc, _calls = runner("--fail-under=50")
    assert rc == 0


def test_a_run_without_a_floor_exits_as_before(runner):
    rc, calls = runner()
    assert rc == 0
    assert not any(str(c).startswith("--fail-under") for cmd in calls for c in cmd), calls
    assert not any("html" in c for c in calls), "an HTML report was written without --html"
