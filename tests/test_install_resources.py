"""AN INSTALLED COPY CARRIES resources/ (#97 A, 2026-10-24).

THE FAULT IT KEEPS AWAY. `pip install .` built a wheel with no fonts, icons,
button images or background in it. pyproject.toml's package search found only
core, ui and utils, and asked for the files as `"*" = ["resources/**/*"]`, but
package data is matched inside each package directory, and resources/ is not
inside core/, ui/ or utils/, so the pattern matched nothing. The installed
app then looked for site-packages/resources/, fell back to Arial, had no
window icon or button images, and could not offer Image mode.

WHAT IT HOLDS, by reading pyproject.toml (no build):
  1. the package search finds `resources` and each folder in it, so their
     files install beside core/, ui/ and utils/ (setuptools warns that it
     will drop the files of a folder that is not a package);
  2. every file under resources/ matches a package-data pattern of that
     package, matched the way setuptools matches them;
  3. the app looks for resources/ beside utils/, which is where they install.

A wheel built from this repository lists every one of them under resources/.
"""
from __future__ import annotations

import glob
import tomllib
from fnmatch import fnmatchcase
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESOURCES = ROOT / "resources"


def _setuptools() -> dict:
    with open(ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)["tool"]["setuptools"]


def _selected(package: str) -> bool:
    """Whether [tool.setuptools.packages.find] selects this package. With
    namespaces on (the pyproject.toml default) every folder is a candidate,
    and setuptools keeps a dotted name that matches an include pattern and
    no exclude pattern (fnmatchcase). setuptools itself is not imported: a
    Python 3.13 venv does not have it."""
    find = _setuptools()["packages"]["find"]
    include = find.get("include", ["*"])
    exclude = find.get("exclude", [])
    return (any(fnmatchcase(package, p) for p in include)
            and not any(fnmatchcase(package, p) for p in exclude))


def _files_under(folder: Path) -> set[str]:
    return {
        p.relative_to(folder).as_posix()
        for p in folder.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def test_resources_and_its_folders_are_installed_as_packages():
    assert _selected("resources"), (
        "the package search leaves out 'resources', so no resource file "
        "goes into the wheel")
    folders = {
        ".".join(("resources",) + p.relative_to(RESOURCES).parts)
        for p in RESOURCES.rglob("*")
        if p.is_dir() and "__pycache__" not in p.parts
    }
    assert folders, "resources/ has no folders, so this check proved nothing"
    missing = sorted(f for f in folders if not _selected(f))
    assert not missing, f"left out by the package search: {missing}"


def test_every_resource_file_matches_package_data():
    package_data = _setuptools().get("package-data", {})
    patterns = list(package_data.get("resources", [])) + list(package_data.get("*", []))
    matched: set[str] = set()
    for pattern in patterns:
        for hit in glob.glob(pattern, root_dir=RESOURCES, recursive=True):
            if (RESOURCES / hit).is_file():
                matched.add(Path(hit).as_posix())
    on_disk = _files_under(RESOURCES)
    assert on_disk, "resources/ is empty, so this check proved nothing"
    missing = sorted(on_disk - matched)
    assert not missing, f"left out of an installed copy: {missing}"


def test_the_app_looks_for_resources_beside_utils():
    from utils import config
    utils_dir = Path(config.__file__).resolve().parent
    assert _selected("utils")
    assert config.RESOURCES_DIR.resolve() == utils_dir.parent / "resources"
    assert config.FONT_PATH.resolve().is_relative_to(config.RESOURCES_DIR.resolve())
    assert config.FONT_PATH.exists()
