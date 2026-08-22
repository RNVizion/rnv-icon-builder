"""Test dependencies live at tests/requirements-dev.txt.

All six RNV repositories converge on that path. This file MENTIONS the
retired name and is excluded from the sweep that forbids it -- the
use/mention distinction.
"""

import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
WANTED = REPO / "tests" / "requirements-dev.txt"
RETIRED = "requirements-test.txt"

# Measured, not assumed. A file that had an include and silently lost it
# would make test_every_include_resolves pass vacuously.
EXPECTED_INCLUDES = 0

SKIP_DIRS = {".git", "build", "dist", "__pycache__", ".venv", ".pytest_cache",
             "htmlcov", "scripts", ".benchmarks", ".hypothesis"}
MENTION_ONLY = {pathlib.Path(__file__).name}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".ini",
                 ".cfg", ".sh", ".bat"}

# A tree diagram names a file by basename and supplies the directory through
# indentation, so these lines -- drawn under `tests/` -- are correct as
# written. Rewriting them would read as tests/tests/... to a reader.
DIAGRAM_LINES = {
    "README.md": "│   ├── requirements-dev.txt   # Test-only dependencies",
    "TEST_SYSTEM.md": "│   └── requirements-dev.txt    ← Pinned test dependencies",
}


def _is_delivery_script(path):
    if "scripts" in path.parts:
        return True
    return path.parent == REPO and path.name.startswith("up")


def _files():
    for path in sorted(REPO.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in MENTION_ONLY or _is_delivery_script(path):
            continue
        yield path


def test_the_dependency_file_is_where_it_belongs():
    assert WANTED.is_file(), f"{WANTED} is missing"
    assert not (REPO / RETIRED).exists(), \
        f"{RETIRED} is still at the repository root"


def test_the_moved_file_still_has_content():
    lines = [ln.strip() for ln in WANTED.read_text(encoding="utf-8").splitlines()]
    packages = [ln for ln in lines if ln and not ln.startswith("#")]
    assert len(packages) >= 3, f"only {len(packages)} requirements found"


def test_every_include_resolves():
    """pip resolves a `-r` include RELATIVE TO THE FILE THAT CONTAINS IT.

    A file moved from the root into tests/ with `-r requirements.txt` intact
    starts asking for tests/requirements.txt -- a file nobody ever wrote. No
    path assertion catches it; CI dies at pip-install time naming a file that
    appears nowhere in the repository. That happened in rnv-color-picker
    during this same pass.
    """
    includes = [ln.strip().split(None, 1)[1].strip()
                for ln in WANTED.read_text(encoding="utf-8").splitlines()
                if ln.strip().startswith("-r ")]
    for include in includes:
        target = (WANTED.parent / include).resolve()
        assert target.is_file(), (
            f"{WANTED.name} includes {include!r} -> {target}, which does not "
            f"exist")
    assert len(includes) == EXPECTED_INCLUDES, (
        f"the file now has {len(includes)} include(s), not "
        f"{EXPECTED_INCLUDES}. If intended, update the constant -- the loop "
        f"above already checks each one resolves.")


def test_nothing_still_points_at_the_retired_path():
    offenders = []
    for path in _files():
        allowed = DIAGRAM_LINES.get(path.relative_to(REPO).as_posix())
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if RETIRED not in line:
                continue
            if allowed is not None and line.rstrip() == allowed:
                continue
            offenders.append(
                f"{path.relative_to(REPO).as_posix()}: {line.strip()}")
    assert not offenders, \
        "these still name the retired path:\n  " + "\n  ".join(offenders)


def test_the_cache_keys_were_not_forgotten():
    """The quiet ones.

    `cache-dependency-path:` never errors when it goes stale -- the key simply
    stops matching and every CI run reinstalls from scratch, forever, with
    nothing in the log to notice. Both workflows carry one, inside a
    multi-line block where the filename sits alone on its own line.
    """
    for workflow in ("tests-linux.yml", "tests-windows.yml"):
        text = (REPO / ".github" / "workflows" / workflow).read_text(
            encoding="utf-8")
        assert "tests/requirements-dev.txt" in text, workflow
        block = text.split("cache-dependency-path:", 1)
        assert len(block) == 2, f"{workflow} has no cache-dependency-path"
        head = block[1][:200]
        assert "tests/requirements-dev.txt" in head, (
            f"{workflow} caches on the old path; the key will never match "
            f"again and nothing will say so")


def test_both_workflows_install_from_the_new_path():
    for workflow in ("tests-linux.yml", "tests-windows.yml"):
        text = (REPO / ".github" / "workflows" / workflow).read_text(
            encoding="utf-8")
        assert "pip install -r tests/requirements-dev.txt" in text, workflow


def test_that_sweep_is_actually_looking():
    walked = {p.relative_to(REPO).as_posix() for p in _files()}
    assert len(walked) > 20, f"the sweep only found {len(walked)} files"
    for required in ("README.md", "TEST_SYSTEM.md", "pytest.ini",
                     ".github/workflows/tests-linux.yml"):
        assert required in walked, f"{required} is not being swept"


def test_the_diagram_exemptions_are_load_bearing():
    """Both directions. An exemption for a line that no longer exists is dead
    weight, and dead weight is a licence waiting for a future defect."""
    for rel, line in DIAGRAM_LINES.items():
        text = (REPO / rel).read_text(encoding="utf-8", errors="replace")
        assert line in text, (
            f"{rel} no longer contains the exempted diagram line "
            f"{line.strip()!r} -- remove it from DIAGRAM_LINES")


def test_the_mention_exemption_is_load_bearing():
    here = pathlib.Path(__file__)
    assert here.name in MENTION_ONLY
    assert RETIRED in here.read_text(encoding="utf-8"), \
        "this file no longer mentions the retired path -- drop the exemption"
