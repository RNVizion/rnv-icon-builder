#!/usr/bin/env python3
"""rnv-icon-builder -- a dead palette key, and the test deps move.

WHAT THIS CHANGES

1. A DEAD PALETTE KEY, DELETED

       'error': '#dc3545'

   It sits in DARK_THEME_COLORS and LIGHT_THEME_COLORS. IMAGE_MODE_COLORS
   gets it too, but only through `{**DARK_THEME_COLORS, ...}` -- so two
   literal lines produce three palette entries, and deleting the two removes
   all three.

   No application code path reads it. That was not concluded from a grep:
   each value was replaced in place with an instrumented string and the full
   suite run. Across 968 tests the key was touched 35 times, every one from
   tests/test_brand_contrast.py sweeping all palette values, while a known-
   live control key lit up 101 times in the same run. The control is the part
   that matters -- the first version of that watcher reported "unused" for
   window_bg as well, and was measuring nothing at all.

   This app renders no error text, so nothing in the error-red ruling applies
   here. There is no colour to derive; there is only a value nobody draws.

   test_rnv_icon_builder.py:241 lists 'error' in a _REQUIRED_KEYS assertion
   against all three palettes, so that entry goes with it. A value watcher
   cannot find that on its own: `assertIn(key, theme)` tests the KEY's
   membership and never touches the value object. This one was known in
   advance; its sibling in rnv-color-palette-manager was found the honest
   way, by the suite going red.

2. TEST DEPENDENCIES MOVE

       requirements-test.txt  ->  tests/requirements-dev.txt

   All six repositories converge on that name and place. Ten references, and
   two of them are the quiet kind:

       cache-dependency-path: |
         requirements.txt
         requirements-test.txt          <- this line, in BOTH workflows

   A stale cache-dependency-path never errors. The key simply stops matching,
   every run reinstalls from scratch forever, and nothing in the log says so.

TREE DIAGRAMS ARE NOT PATHS

   README.md and TEST_SYSTEM.md draw the file in a tree, where indentation
   supplies the directory. Those entries move to sit under `tests/` rather
   than being rewritten to `tests/requirements-dev.txt`, which would read as
   tests/tests/... to anyone looking at the diagram.

USAGE

    python up.py --check     # dry run; every pass runs, nothing written
    python up.py             # apply
    python up.py --finish    # delete this script

Runs from the repository root. Safe to run twice.
"""

from __future__ import annotations

import os
import subprocess
import sys

COLORS = "ui/colors.py"
BASELINE = "test_rnv_icon_builder.py"
OLD_DEPS = "requirements-test.txt"
NEW_DEPS = "tests/requirements-dev.txt"


# --------------------------------------------------------------------------
# 1. The dead key
# --------------------------------------------------------------------------

SNAPSHOTS = "tests/snapshots.json"

DEAD_KEY_EDITS = (
    (COLORS, "    'error': '#dc3545',\n", "", 2,
     "the orphaned key -- two literals, three palettes, because IMAGE splats "
     "DARK"),
    (BASELINE,
     "        'success', 'warning', 'error',\n",
     "        'success', 'warning',\n", 1,
     "the baseline suite's _REQUIRED_KEYS -- key membership is invisible to a "
     "value watcher, so this had to be found by reading the test"),
    # Three theme key-set snapshots, one per palette, each a sorted list of
    # 76 names. All three must lose the key, so the count IS the assertion:
    # three, or something has diverged and the run stops.
    #
    # Rewritten here rather than regenerated. The bundled helper would rebuild
    # all three lists from whatever the palettes currently hold and accept any
    # OTHER key that had appeared or vanished alongside -- which is the whole
    # reason a key-set snapshot exists.
    (SNAPSHOTS, '    "error",\n', "", 3,
     "the three theme key-set snapshots, edited rather than regenerated"),
)


# --------------------------------------------------------------------------
# 2. Dependencies
# --------------------------------------------------------------------------

DEP_REWRITES = (
    (".github/workflows/tests-linux.yml",
     "            requirements-test.txt",
     "            tests/requirements-dev.txt", 1,
     "LIVE-QUIET -- cache-dependency-path; a stale key never errors, it just "
     "stops matching"),
    (".github/workflows/tests-linux.yml",
     "pip install -r requirements-test.txt",
     "pip install -r tests/requirements-dev.txt", 1,
     "LIVE -- CI fails outright without this"),
    (".github/workflows/tests-windows.yml",
     "            requirements-test.txt",
     "            tests/requirements-dev.txt", 1,
     "LIVE-QUIET -- cache-dependency-path"),
    (".github/workflows/tests-windows.yml",
     "pip install -r requirements-test.txt",
     "pip install -r tests/requirements-dev.txt", 1,
     "LIVE"),
    ("pytest.ini",
     "# Phase 1 of test-system expansion. See requirements-test.txt for dependencies.",
     "# Phase 1 of test-system expansion. See tests/requirements-dev.txt for dependencies.",
     1, "DOCS -- a comment pointing at the file"),
    ("README.md",
     "├── requirements-test.txt      # Test-only dependencies\n",
     "", 1,
     "DOCS -- drop the root tree entry; it moves under tests/ below"),
    ("README.md",
     "├── tests/\n"
     "│   ├── conftest.py            # Shared fixtures + Qt/font/theme bootstrapping\n",
     "├── tests/\n"
     "│   ├── requirements-dev.txt   # Test-only dependencies\n"
     "│   ├── conftest.py            # Shared fixtures + Qt/font/theme bootstrapping\n",
     1, "DOCS -- and draw it where it now lives"),
    ("README.md",
     "pip install -r requirements-test.txt",
     "pip install -r tests/requirements-dev.txt", 1,
     "DOCS -- an instruction a reader will actually run"),
    ("TEST_SYSTEM.md",
     "pip install -r requirements-test.txt   # one time",
     "pip install -r tests/requirements-dev.txt   # one time", 1,
     "DOCS"),
    ("TEST_SYSTEM.md",
     "├── requirements-test.txt       ← Pinned test dependencies\n",
     "", 1,
     "DOCS -- drop the root tree entry"),
    ("TEST_SYSTEM.md",
     "│   └── snapshots.json          ← Reference data for snapshot tests\n",
     "│   ├── snapshots.json          ← Reference data for snapshot tests\n"
     "│   └── requirements-dev.txt    ← Pinned test dependencies\n", 1,
     "DOCS -- and draw it under tests/, taking over the closing branch"),
)

SELF_REWRITES = (
    ("#     pip install -r requirements-test.txt",
     "#     pip install -r tests/requirements-dev.txt",
     "its own install line would name a path that no longer exists"),
)

EXPECTED_INCLUDES = 0

DEP_EXEMPT = {
    "tests/test_dependency_file_placement.py":
        "the guard; its job is to name the retired path",
}

# Tree-diagram lines: the basename is correct because indentation supplies the
# directory. Named explicitly, and asserted to exist, rather than waved
# through by a looser rule that would also hide a real stale reference.
DIAGRAM_LINES = {
    "README.md": "│   ├── requirements-dev.txt   # Test-only dependencies",
    "TEST_SYSTEM.md": "│   └── requirements-dev.txt    ← Pinned test dependencies",
}


# --------------------------------------------------------------------------
# 3. Guards
# --------------------------------------------------------------------------

DEAD_GUARD_PATH = "tests/test_dead_error_key.py"

DEAD_GUARD_SOURCE = r'''"""The orphaned 'error' key stays gone.

It held #dc3545 in every palette and nothing drew it. An unread wrong value
is still a wrong value waiting for a reader -- and a palette key that exists
is an invitation to use it, which is how a colour nobody ruled ends up on
screen.

This app renders no error text at all, so there is nothing to replace it
with. If one is ever needed, take the derived value the family ruled --
lighten('#dc3545', -20) for light grounds -- rather than reviving this.
"""

import pytest

from ui import colors

PALETTES = ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS")


@pytest.mark.parametrize("name", PALETTES)
def test_the_dead_error_key_is_gone(name):
    palette = getattr(colors, name)
    assert "error" not in palette, (
        f"{name} has an 'error' key again. It was deleted as an orphan: "
        f"nothing in the app read it across 968 tests.")


@pytest.mark.parametrize("name", PALETTES)
def test_image_mode_did_not_reintroduce_it_through_the_splat(name):
    """IMAGE_MODE_COLORS is built as {**DARK_THEME_COLORS, ...}, so a key
    added back to DARK reappears here without anyone editing this palette.
    Asserted separately because that is the route a reintroduction would
    take."""
    assert "error" not in getattr(colors, name)


def test_that_check_is_actually_looking():
    """Guard the guard.

    The assertions above pass trivially against an empty dict. If a palette
    ever turns up empty -- a refactor, a rename, an import that silently
    yields the wrong object -- they would report clean while checking
    nothing.
    """
    for name in PALETTES:
        palette = getattr(colors, name)
        assert len(palette) > 40, f"{name} has only {len(palette)} keys"
        assert "window_bg" in palette, f"{name} does not look like a palette"
    planted = {"error": "#dc3545"}
    assert "error" in planted, \
        "the membership check no longer detects a known offender"


def test_no_palette_still_carries_the_value_under_another_name():
    """Deleting the key is not the same as removing the value. If #dc3545
    reappears on some other key it is back on screen under a new name, which
    is exactly how a retired colour survives a rename sweep."""
    retired = "#dc3545"
    for name in PALETTES:
        offenders = [k for k, v in getattr(colors, name).items()
                     if isinstance(v, str) and v.lower() == retired]
        assert not offenders, f"{name} carries {retired} on {offenders}"
'''

GUARD_PATH = "tests/test_dependency_file_placement.py"

GUARD_SOURCE = r'''"""Test dependencies live at tests/requirements-dev.txt.

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
'''


# --------------------------------------------------------------------------
# Machinery
# --------------------------------------------------------------------------

class Halt(SystemExit):
    pass


def _this_script() -> str:
    return os.path.relpath(os.path.realpath(__file__),
                           os.path.realpath(os.getcwd())).replace(os.sep, "/")


class Tree:
    SKIP_DIRS = {".git", "__pycache__", "build", "dist", ".venv", "scripts",
                 ".pytest_cache", "htmlcov", ".benchmarks", ".hypothesis"}
    TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".ini",
                     ".cfg", ".sh", ".bat"}

    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.dirty: set[str] = set()

    def get(self, path: str) -> str:
        if path not in self.files:
            with open(path, "r", encoding="utf-8") as handle:
                self.files[path] = handle.read()
        return self.files[path]

    def sweep_text(self, path: str) -> str:
        if path in self.files:
            return self.files[path]
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def set(self, path: str, text: str) -> None:
        self.files[path] = text
        self.dirty.add(path)

    def texts(self):
        me = _this_script()
        for root, dirs, names in os.walk("."):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for name in sorted(names):
                if os.path.splitext(name)[1] not in self.TEXT_SUFFIXES:
                    continue
                path = os.path.relpath(os.path.join(root, name),
                                       ".").replace(os.sep, "/")
                if path != me:
                    yield path

    def flush(self) -> int:
        for path in sorted(self.dirty):
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(self.files[path])
        return len(self.dirty)


def git(*args: str) -> str:
    result = subprocess.run(("git",) + args, capture_output=True, text=True)
    if result.returncode:
        raise Halt(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


ALL_EDITS = DEAD_KEY_EDITS + DEP_REWRITES


def already_done() -> bool:
    if os.path.exists(COLORS) and "'error': '#dc3545'" not in open(
            COLORS, encoding="utf-8").read():
        print("Already applied -- ui/colors.py has no 'error' key.")
        print("Nothing to do. This is the idempotent exit, not an error.")
        return True
    return False


def check_fingerprint(tree: Tree) -> None:
    problems = []
    for path, old, _new, expected, why in ALL_EDITS:
        if not os.path.exists(path):
            problems.append(f"  {path} does not exist")
            continue
        count = tree.sweep_text(path).count(old)
        if count != expected:
            problems.append(
                f"  {path}: expected {expected} occurrence(s) of "
                f"{old.splitlines()[0].strip()[:56]!r}, found {count}\n"
                f"      ({why})")
    if not os.path.exists(OLD_DEPS):
        problems.append(f"  {OLD_DEPS} is not at the repository root")
    if os.path.exists(NEW_DEPS):
        problems.append(f"  {NEW_DEPS} already exists")
    if problems:
        raise Halt("This is not the tree this script was written against:\n"
                   + "\n".join(problems)
                   + "\n\nRun it from the root of a clean checkout of main.")


def apply_edits(tree: Tree, edits, heading: str) -> None:
    print(heading)
    for path, old, new, expected, why in edits:
        tree.set(path, tree.get(path).replace(old, new, expected))
        print(f"  {path}: {why}")


def assert_no_dep_reference_was_missed(tree: Tree) -> None:
    listed = {path for path, _o, _n, _c, _w in DEP_REWRITES}
    exempt = set(DEP_EXEMPT) | {OLD_DEPS, GUARD_PATH}
    unaccounted = []
    for path in tree.texts():
        if path in listed or path in exempt:
            continue
        for line in tree.sweep_text(path).splitlines():
            if OLD_DEPS in line:
                unaccounted.append(f"{path}: {line.strip()}")
    if unaccounted:
        raise Halt(
            "These name the dependency file but are in neither the rewrite\n"
            "list nor the exemption list -- decide which each one is:\n  "
            + "\n  ".join(unaccounted))
    print(f"  every file naming the dependency path is accounted for "
          f"({len(listed)} files, {len(DEP_REWRITES)} references)")


def move_the_deps(tree: Tree, dry: bool) -> None:
    body = tree.get(OLD_DEPS)
    includes = [ln for ln in body.splitlines() if ln.strip().startswith("-r ")]
    if len(includes) != EXPECTED_INCLUDES:
        raise Halt(
            f"{OLD_DEPS} has {len(includes)} `-r` include(s), expected "
            f"{EXPECTED_INCLUDES}. pip resolves an include relative to the "
            f"file holding it, so each needs a `../` prefix after this move. "
            f"Refusing to move it blind.")
    for old_line, new_line, why in SELF_REWRITES:
        if old_line not in body:
            raise Halt(f"{OLD_DEPS} does not contain {old_line!r}\n  ({why})")
        body = body.replace(old_line, new_line, 1)
    tree.set(NEW_DEPS, body)
    if not dry:
        git("mv", OLD_DEPS, NEW_DEPS)
    print(f"  {OLD_DEPS} -> {NEW_DEPS}  (git mv; {EXPECTED_INCLUDES} includes)")


def install_guards(tree: Tree) -> None:
    tree.set(GUARD_PATH, GUARD_SOURCE)
    tree.set(DEAD_GUARD_PATH, DEAD_GUARD_SOURCE)
    print(f"  {GUARD_PATH}: {len(GUARD_SOURCE.splitlines())} lines")
    print(f"  {DEAD_GUARD_PATH}: {len(DEAD_GUARD_SOURCE.splitlines())} lines")


def verify(tree: Tree) -> None:
    problems = []

    colours = tree.get(COLORS)
    if "'error':" in colours:
        problems.append("a palette still carries the dead 'error' key")
    # The value itself must survive nowhere in the palettes -- deleting a key
    # is not the same as removing a value.
    if "#dc3545" in colours:
        problems.append("ui/colors.py still holds #dc3545 somewhere")

    snapshots = tree.get(SNAPSHOTS)
    import json as _json
    parsed = _json.loads(snapshots)
    for name in ("dark_theme_keys", "light_theme_keys", "image_mode_keys"):
        keys = parsed.get(name)
        if keys is None:
            problems.append(f"snapshot {name} is missing entirely")
        elif "error" in keys:
            problems.append(f"snapshot {name} still lists 'error'")
        elif len(keys) != 75:
            problems.append(
                f"snapshot {name} has {len(keys)} keys, expected 75 -- one "
                f"fewer than the 76 it held. Something other than 'error' "
                f"moved.")

    baseline = tree.get(BASELINE)
    if "'success', 'warning', 'error'," in baseline:
        problems.append("the baseline _REQUIRED_KEYS still demands 'error'")
    if "'success', 'warning'," not in baseline:
        problems.append("the baseline required-keys list lost more than it should")

    swept = 0
    for path in tree.texts():
        if path in DEP_EXEMPT or path in (OLD_DEPS, NEW_DEPS):
            continue
        swept += 1
        allowed = DIAGRAM_LINES.get(path)
        for line in tree.sweep_text(path).splitlines():
            if OLD_DEPS not in line:
                continue
            if allowed is not None and line.rstrip() == allowed:
                continue
            problems.append(f"{path} still names the retired path: {line.strip()}")
    if swept < 20:
        problems.append(f"the sweep visited only {swept} files; it is not looking")
    if OLD_DEPS not in f"pip install -r {OLD_DEPS}":
        problems.append("the sweep pattern no longer matches a known offender")

    for path, line in DIAGRAM_LINES.items():
        if line not in tree.get(path):
            problems.append(
                f"{path} no longer contains the exempted diagram line "
                f"{line.strip()!r}; remove it from DIAGRAM_LINES")

    # Both cache keys, checked the way a stale one would otherwise hide.
    for workflow in (".github/workflows/tests-linux.yml",
                     ".github/workflows/tests-windows.yml"):
        text = tree.get(workflow)
        head = text.split("cache-dependency-path:", 1)[-1][:200]
        if "tests/requirements-dev.txt" not in head:
            problems.append(f"{workflow} still caches on the old path")
        if "pip install -r tests/requirements-dev.txt" not in text:
            problems.append(f"{workflow} does not install from the new path")

    body = tree.get(NEW_DEPS)
    packages = [ln for ln in (l.strip() for l in body.splitlines())
                if ln and not ln.startswith("#")]
    if len(packages) < 3:
        problems.append(f"the moved file holds only {len(packages)} requirements")

    if problems:
        raise Halt("VERIFY FAILED -- nothing was written:\n  "
                   + "\n  ".join(problems))
    print(f"  verify: 'error' gone and #dc3545 with it; both cache keys and "
          f"both installs moved;")
    print(f"    {swept} files swept; {len(packages)} requirements intact")


def finish() -> None:
    here = os.path.abspath(__file__)
    os.remove(here)
    print(f"Removed {here}")


def main() -> int:
    if "--finish" in sys.argv:
        finish()
        return 0

    dry = "--check" in sys.argv

    if not os.path.isdir(".git"):
        raise Halt("run this from the repository root (.git not found)")
    if already_done():
        return 0

    tree = Tree()
    check_fingerprint(tree)

    print("DRY RUN -- every pass runs, nothing is written\n" if dry
          else "Applying\n")

    apply_edits(tree, DEAD_KEY_EDITS,
                "1. the dead 'error' key, and the test that required it")

    print("\n2. dependencies")
    assert_no_dep_reference_was_missed(tree)
    move_the_deps(tree, dry)
    apply_edits(tree, DEP_REWRITES, "   references:")

    print("\n3. guards")
    install_guards(tree)

    print("\n4. verify the pending tree")
    verify(tree)

    if dry:
        print(f"\nDry run complete. {len(tree.dirty)} files would change; "
              f"none were written. The git mv did not run.")
        return 0

    written = tree.flush()
    print(f"\n5. wrote {written} files")

    print("\nDone. Now run, from the repository root:")
    print("    QT_QPA_PLATFORM=offscreen xvfb-run -a python run_tests.py")
    print(f"\nThen, once green:  python {_this_script()} --finish")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Halt as stop:
        print(f"\n{stop}", file=sys.stderr)
        sys.exit(1)
