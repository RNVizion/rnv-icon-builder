"""`pip install -e .` builds, and the two commands it installs can start (#97 A).

WHAT WAS THERE. pyproject.toml named the build backend
`setuptools.backends._legacy:_Backend`. No setuptools has that module, so pip
stopped with BackendUnavailable before building anything, whatever setuptools
was installed. Behind it was a second fault: both entry points live in root
modules (RNV_Icon_Builder.py and cli.py), which the package list did not
include, so an install that did build would have left `rnv-icon-builder` and
`rnv-icon-cli` unable to import. The project URLs named a repository that does
not exist under that name.

WHAT THIS GUARD HOLDS, statically (no build runs here):

1. The backend pyproject.toml names can be imported, and it has the hooks pip
   calls for a wheel and for an editable install.
2. Every module an entry point names is a root module listed in `py-modules`,
   or sits in a package the package search includes.
3. Every entry point names a function defined at the top of its module.
4. The project URLs and the README's clone command name the same repository.

WHAT IT CANNOT HOLD. That pip runs. The fix was proved by installing into a
throwaway venv with setuptools 68.1 and with the newest one; the README says
how to do it.
"""
from __future__ import annotations

import ast
import importlib
import pathlib
import re
import tomllib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
REPOSITORY = "https://github.com/RNVizion/rnv-icon-builder"


def _entry_points() -> dict:
    return PYPROJECT["project"]["scripts"]


def _is_installed(module: str) -> bool:
    """Whether setuptools puts this dotted module into the wheel."""
    setuptools = PYPROJECT.get("tool", {}).get("setuptools", {})
    top = module.split(".")[0]
    if "." not in module and module in setuptools.get("py-modules", []):
        return True
    include = setuptools.get("packages", {}).get("find", {}).get("include", [])
    return any(re.fullmatch(pattern.replace("*", ".*"), top) for pattern in include) \
        and (ROOT / top / "__init__.py").exists()


def _module_file(module: str) -> pathlib.Path:
    parts = module.split(".")
    path = ROOT.joinpath(*parts).with_suffix(".py")
    return path if path.exists() else ROOT.joinpath(*parts, "__init__.py")


#: setuptools' real PEP 517 backends. The one pyproject named before, which
#: no setuptools has ever had, is how `pip install -e .` failed.
SETUPTOOLS_BACKENDS = {"setuptools.build_meta", "setuptools.build_meta:__legacy__"}


def test_the_build_backend_is_one_setuptools_has():
    backend = PYPROJECT["build-system"]["build-backend"]
    assert backend in SETUPTOOLS_BACKENDS, f"{backend} is not a backend setuptools provides"
    assert any(req.startswith("setuptools") for req in PYPROJECT["build-system"]["requires"])


def test_the_build_backend_can_be_imported():
    # pip installs the backend into an isolated build environment of its own.
    # A Python 3.12+ venv (Chris's, CI's) carries no setuptools, so the import
    # is checked where setuptools is installed; the name is held above either way.
    pytest.importorskip("setuptools")
    backend = PYPROJECT["build-system"]["build-backend"]
    module_name, _, attribute = backend.partition(":")
    module = importlib.import_module(module_name)
    hooks = getattr(module, attribute) if attribute else module
    for hook in ("build_wheel", "build_sdist", "build_editable"):
        assert callable(getattr(hooks, hook, None)), f"{backend} has no {hook} hook"


def test_every_entry_point_module_is_installed():
    assert _entry_points(), "pyproject.toml declares no [project.scripts]"
    missing = [f"{name} = {target}" for name, target in _entry_points().items()
               if not _is_installed(target.partition(":")[0])]
    assert not missing, ("these commands name a module the install leaves out; list a root "
                         "module in [tool.setuptools] py-modules:\n  " + "\n  ".join(missing))


def test_every_entry_point_names_a_function_its_module_defines():
    for name, target in _entry_points().items():
        module, _, function = target.partition(":")
        path = _module_file(module)
        assert path.exists(), f"{name}: no file for module {module}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        defined = {node.name for node in tree.body
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        assert function in defined, f"{name}: {path.name} defines no top-level {function}()"


def test_the_project_urls_name_this_repository():
    urls = PYPROJECT["project"]["urls"]
    assert urls, "pyproject.toml declares no [project.urls]"
    wrong = {key: url for key, url in urls.items()
             if url.rstrip("/") != REPOSITORY and not url.startswith(REPOSITORY + "/")}
    assert not wrong, f"these URLs do not name {REPOSITORY}: {wrong}"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"git clone {REPOSITORY}.git" in readme, "the README clones another repository"


def test_the_reader_is_looking():
    """A reader that finds nothing passes the tests above."""
    assert _is_installed("core.icon_builder_core")
    assert not _is_installed("tools")
    assert not _is_installed("sitecustomize")
    assert _module_file("cli").name == "cli.py"
