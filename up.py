"""chart ruling 3: the Settings colour button's edge follows the mode

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-icon-builder, derived against a fresh clone at the live head (0593741).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-26, decision 3 of the colour chart: "Yes." Restyle on mode
switch.

The chart read back every stylesheet the app sets, in every mode, and found
one in light mode carrying dark's colour: the edge of the Settings dialog's
preview-background colour button, written from DARK_THEME_COLORS by name. It
takes the mode's text_disabled now (#555555 dark, #aaaaaa light). The gold
hover beside it does not move -- BRAND_GOLD in every mode is a reviewed,
permanent bypass in tests/test_brand_contrast.py.
"""
from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = 'rnv-icon-builder'
SENTINEL = 'RNV-RESTYLE-ON-SWITCH'
SENTINEL_FILE = 'ui/preview_utils.py'
GUARD = 'tests/test_preview_utils.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_preview_utils.py', 'tests/test_brand_contrast.py']
DESCRIPTION = "chart ruling 3: the Settings colour button's edge follows the mode"

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest.
SUITES = [("run_tests.py -- what both CI workflows run",
           [sys.executable, "run_tests.py"])]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': 'a25e73acb05f7498f1e3a9520ac4d5470fb50dc629deac7113759ee13502a25b', '.github/workflows/tests-windows.yml': 'eeb17b6a4fb8ba4a92b9ee6b182b16614bda3266c8a3e12da21cefc2f808ebd0'}

SHADOWS = {"colors.py", "config.py", "conftest.py", "preview_utils.py", "run_tests.py"}

LEFT_ALONE = ["the colour button's gold hover. BRAND_GOLD in every mode is a reviewed, permanent bypass: it is drawn over the user's own colour.", "the extracted-colour swatches in ColorPaletteWidget, whose edge is written from DARK_THEME_COLORS the same way. They exist only once an image is loaded, so the chart's read-back never saw one; for a ruling."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/preview_utils.py',
             '        self.current_bg = DEFAULT_PREVIEW_BACKGROUND\n        self.custom_color: tuple[int, int, int] = (128, 128, 128)  # Gray default\n        \n        self._setup_ui()\n',
             '        self.current_bg = DEFAULT_PREVIEW_BACKGROUND\n        self.custom_color: tuple[int, int, int] = (128, 128, 128)  # Gray default\n        #: The mode apply_theme() last drew this in. The colour button reads\n        #: it, because a colour change repaints the button without a mode.\n        self._is_dark: bool = True\n        \n        self._setup_ui()\n')
    tree.sub('ui/preview_utils.py',
             '    def apply_theme(self, is_dark: bool = True) -> None:\n        """Apply theme styling to background selector."""\n        colors = get_theme_colors(is_dark=is_dark)\n',
             '    def apply_theme(self, is_dark: bool = True) -> None:\n        """Apply theme styling to background selector."""\n        self._is_dark = is_dark\n        self._update_color_button()\n        colors = get_theme_colors(is_dark=is_dark)\n')
    tree.sub('ui/preview_utils.py',
             '    def _update_color_button(self) -> None:\n        """Update the color button appearance."""\n        hex_color = color_to_hex(self.custom_color)\n        self.color_btn.setStyleSheet(f"""\n            QPushButton {{\n                background-color: {hex_color};\n                border: 2px solid {DARK_THEME_COLORS[\'text_disabled\']};\n                border-radius: 3px;\n            }}\n            QPushButton:hover {{\n                border-color: {BRAND_GOLD};\n            }}\n        """)\n',
             '    def _update_color_button(self) -> None:\n        """Update the color button appearance, in the mode apply_theme() set.\n\n        RNV-RESTYLE-ON-SWITCH, 2026-09-26 (ruling 3). The edge read\n        DARK_THEME_COLORS by name, so in light mode the button kept dark\'s\n        #555555 edge while the combo beside it turned light. It takes the\n        mode\'s text_disabled now. The hover stays BRAND_GOLD in every mode:\n        a reviewed, permanent bypass in tests/test_brand_contrast.py, drawn\n        over the user\'s colour rather than a themed surface.\n        """\n        hex_color = color_to_hex(self.custom_color)\n        edge = get_theme_colors(is_dark=getattr(self, \'_is_dark\', True))[\'text_disabled\']\n        self.color_btn.setStyleSheet(f"""\n            QPushButton {{\n                background-color: {hex_color};\n                border: 2px solid {edge};\n                border-radius: 3px;\n            }}\n            QPushButton:hover {{\n                border-color: {BRAND_GOLD};\n            }}\n        """)\n')
    tree.sub('tests/test_preview_utils.py',
             '        stats = get_thumbnail_cache_stats()\n        assert isinstance(stats, dict)\n',
             '        stats = get_thumbnail_cache_stats()\n        assert isinstance(stats, dict)\n\n\n# RNV-RESTYLE-ON-SWITCH\n# ══════════════════════════════════════════════════════════════════════════════\n# The preview background\'s custom-colour button follows the mode\n# ══════════════════════════════════════════════════════════════════════════════\n@pytest.mark.ui\nclass TestBackgroundColorButtonFollowsTheMode:\n    """RNV-RESTYLE-ON-SWITCH, ruling 3 of 2026-09-26. The Settings dialog\'s\n    preview-background selector has a small button showing the custom\n    colour. Its edge was written from DARK_THEME_COLORS by name, so in light\n    mode it kept dark\'s #555555 edge while the combo beside it turned light;\n    the chart\'s read-back of every stylesheet the app sets found it there.\n    The edge takes the mode apply_theme() was given now.\n\n    The hover does not move: BRAND_GOLD in every mode, a reviewed and\n    permanent bypass in tests/test_brand_contrast.py, because it is drawn\n    over the user\'s own colour rather than a themed surface."""\n\n    @staticmethod\n    def _parts(widget):\n        sheet = widget.color_btn.styleSheet()\n        plate, _, hover = sheet.partition("QPushButton:hover")\n        return sheet, plate, hover\n\n    def test_each_mode_draws_the_button_in_its_own_colours(self, qapp):\n        from ui.colors import BRAND_GOLD, get_theme_colors\n        from ui.preview_utils import BackgroundSelectorWidget\n\n        widget = BackgroundSelectorWidget()\n        try:\n            edges = {get_theme_colors(is_dark=d)["text_disabled"] for d in (True, False)}\n            assert len(edges) == 2, "the two modes share an edge, so this proves nothing"\n            for is_dark in (False, True, False):\n                widget.apply_theme(is_dark=is_dark)\n                sheet, plate, hover = self._parts(widget)\n                edge = get_theme_colors(is_dark=is_dark)["text_disabled"]\n                assert f"border: 2px solid {edge};" in plate, sheet\n                assert f"border-color: {BRAND_GOLD};" in hover, sheet\n        finally:\n            widget.deleteLater()\n\n    def test_a_new_custom_colour_keeps_the_mode(self, qapp, monkeypatch):\n        """Choosing a colour repaints the button without being told the mode."""\n        from PyQt6.QtGui import QColor\n        from PyQt6.QtWidgets import QColorDialog\n\n        from ui.colors import BRAND_GOLD, get_theme_colors\n        from ui.preview_utils import BackgroundSelectorWidget\n\n        widget = BackgroundSelectorWidget()\n        try:\n            widget.apply_theme(is_dark=False)\n            monkeypatch.setattr(QColorDialog, "getColor",\n                                staticmethod(lambda *a, **k: QColor(10, 200, 30)))\n            widget._choose_color()\n            sheet, plate, hover = self._parts(widget)\n            assert "background-color: #0ac81e;" in plate.lower(), sheet\n            edge = get_theme_colors(is_dark=False)["text_disabled"]\n            assert f"border: 2px solid {edge};" in plate, sheet\n            assert f"border-color: {BRAND_GOLD};" in hover, sheet\n        finally:\n            widget.deleteLater()\n\n    def test_the_settings_dialog_hands_its_mode_to_the_selector(self):\n        """The chain the fix relies on: a mode change reaches the selector\n        through the Settings dialog\'s own _apply_theme()."""\n        import ast\n        import pathlib\n        src = (pathlib.Path(__file__).resolve().parents[1] / "ui" / "settings_dialog.py")\n        tree = ast.parse(src.read_text(encoding="utf-8-sig"))\n        fn = next(n for n in ast.walk(tree)\n                  if isinstance(n, ast.FunctionDef) and n.name == "_apply_theme")\n        assert "self.bg_selector.apply_theme(is_dark=is_dark)" in ast.unparse(fn)\n')


def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _function(src: str, name: str, cls: str | None = None):
    """The named function, at module level or inside the named class."""
    body = ast.parse(src).body
    if cls is not None:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == cls).body
    return next(n for n in body if isinstance(n, ast.FunctionDef) and n.name == name)


def _top(src: str) -> dict:
    """Module-level NAME -> ast.dump of the value it is assigned."""
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(t, ast.Name):
                out[t.id] = ast.dump(node.value)
    return out


def _entries(node) -> dict:
    """A dict display's literal keys -> ast.dump of each value; ** spreads
    under their own ast.dump, so a moved spread is seen too."""
    return {(k.value if k is not None else "**" + ast.dump(v)): ast.dump(v)
             for k, v in zip(node.keys, node.values)}


def _sheet_parts(call) -> list:
    """The literal text of a setStyleSheet(f"...") call, the parts between
    its placeholders, in order."""
    arg = call.args[0]
    assert isinstance(arg, ast.JoinedStr), ast.unparse(arg)[:80]
    return [v.value for v in arg.values if isinstance(v, ast.Constant)]


def _calls(fn, attr: str) -> list:
    return [c for c in ast.walk(fn) if isinstance(c, ast.Call)
            and getattr(c.func, "attr", getattr(c.func, "id", None)) == attr]


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    old_p, new_p = _original(tree, "ui/preview_utils.py"), tree.read("ui/preview_utils.py")
    old_fn = _function(old_p, "_update_color_button", "BackgroundSelectorWidget")
    new_fn = _function(new_p, "_update_color_button", "BackgroundSelectorWidget")
    old_sheet = _calls(old_fn, "setStyleSheet")[0]
    new_sheet = _calls(new_fn, "setStyleSheet")[0]
    # the same sheet, one placeholder changed: the edge, and only the edge
    assert _sheet_parts(old_sheet) == _sheet_parts(new_sheet), "the sheet's text moved"
    olds = [ast.unparse(v.value) for v in old_sheet.args[0].values if isinstance(v, ast.FormattedValue)]
    news = [ast.unparse(v.value) for v in new_sheet.args[0].values if isinstance(v, ast.FormattedValue)]
    assert olds == ["hex_color", "DARK_THEME_COLORS['text_disabled']", "BRAND_GOLD"], olds
    assert news == ["hex_color", "edge", "BRAND_GOLD"], news
    code = "\n".join(ast.unparse(s) for s in new_fn.body[1:])      # past the docstring
    assert "DARK_THEME_COLORS" not in code, "the edge still reads the dark palette by name"
    apply = ast.unparse(_function(new_p, "apply_theme", "BackgroundSelectorWidget"))
    assert "self._is_dark = is_dark" in apply and "self._update_color_button()" in apply
    init = ast.unparse(_function(new_p, "__init__", "BackgroundSelectorWidget"))
    assert init.index("self._is_dark") < init.index("self._setup_ui()")
    # DARK_THEME_COLORS is still imported, and still used by the palette swatch
    assert "DARK_THEME_COLORS['text_disabled']" in new_p
    guard = tree.read("tests/test_preview_utils.py")
    ast.parse(guard)
    assert SENTINEL in guard and "class TestBackgroundColorButtonFollowsTheMode" in guard
# ------------------------------------------------------------------ plumbing
#
# EXIT CODES ARE A TAXONOMY, NOT A BOOLEAN. Rev 6 §3.0.1. A harness that
# returns non-zero for everything tells the operator something is wrong and
# nothing about what, and the three non-zero cases want three different
# actions: read the diff, install something, re-run.
EXIT_CLEAN = 0       # everything agreed
EXIT_DISAGREES = 1   # something ran and disagreed -- read it
EXIT_CANNOT_RUN = 2  # the environment is not ready -- nothing was asked
EXIT_INCOMPLETE = 3  # it ran and did not finish -- re-run before believing it


class Stop(SystemExit):
    """A refusal this script chose, as opposed to a crash.

    Carries an exit code from the taxonomy. Bare SystemExit('message') exits 1,
    which says A TEST DISAGREED -- so every refusal used to arrive wearing the
    one verdict it was not.
    """

    def __init__(self, message: str, code: int = EXIT_CANNOT_RUN) -> None:
        super().__init__(message)
        self.code = code


#: Two files per repository that exist there and in none of the others.
#: Verified against the live fleet by _fingerprint_check.py at build time,
#: because a fingerprint that has been renamed away identifies nothing and
#: would refuse every correct checkout.
FINGERPRINTS = {
    "rnv-color-mixer": ("core/image_handler.py", "ui/canvas_view.py"),
    "rnv-color-palette-manager": ("core/color_extractor.py",
                                  "ui/batch_export_dialog.py"),
    "rnv-color-picker": ("core/hilbert_curve.py", "ui/color_swatch_widget.py"),
    "rnv-icon-builder": ("core/icon_builder_core.py", "core/project_manager.py"),
    "rnv-text-transformer": ("core/diff_engine.py", "core/text_cleaner.py"),
}


def refuse_wrong_repository(root) -> None:
    """Refuse a checkout that is not the repository this script was built for.

    CALLED FIRST IN apply(), BEFORE THE SENTINEL AND BEFORE ANY ANCHOR, and the
    order is the whole point. The five applications share file names -- four of
    them have a utils/config.py or a ui/colors.py, and several share a
    tests/conftest.py. Run in the wrong sibling, a sentinel check says "already
    applied" or "not a checkout" and an anchor check says "the file moved",
    and BOTH of those are the script guessing at the wrong question.

    A fingerprint is a file only the right repository has. Two, because one
    that gets renamed takes the check with it.
    """
    want = FINGERPRINTS.get(REPO)
    if not want:
        return
    missing = [f for f in want if not (root / f).exists()]
    if missing:
        raise Stop(
            f"this is not a {REPO} checkout.\n"
            f"  expected to find: {', '.join(want)}\n"
            f"  missing here:     {', '.join(missing)}\n"
            f"Run it from the root of {REPO}. Nothing was read or written.",
            EXIT_CANNOT_RUN)


def _left_alone() -> None:
    """Print what this round deliberately did not touch.

    LEFT_ALONE is optional and is prose, not a guard. It exists because a
    reader of a diff can see what changed and cannot see what was considered
    and declined, and the second is where a round's scope actually lives.
    """
    items = globals().get("LEFT_ALONE")
    if not items:
        return
    print("\nleft alone, deliberately:")
    for line in items:
        print(f"  - {line}")


def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        raise Stop(f"refusing to run as {name} -- it would shadow a module on "
                   f"sys.path. Rename to up.py and run again.", EXIT_CANNOT_RUN)


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}
        self.deleted: set[str] = set()
        #: rel -> (had a BOM, line endings were CRLF throughout). What a file
        #: was on disk, so flush() can put back exactly that around the edit.
        self.form: dict[str, tuple[bool, bool]] = {}

    def read(self, rel: str) -> str:
        """The file as text with LF line endings, whatever it is on disk.

        A FILE IS ITS BYTES, AND AN EDIT MUST NOT CHANGE THE ONES IT DID NOT
        MEAN TO. This used to read with read_text('utf-8-sig') and flush with
        encode('utf-8'). The first strips a byte-order mark and folds CRLF to
        LF; the second puts neither back. So a one-line edit to a CRLF file
        rewrote every line ending in it, and any edit to a file with a BOM
        deleted its first three bytes. rnv-color-picker's utils/config.py --
        the picker's palette -- carries a BOM, so its next round would have.

        Anchors are written with \\n, so a CRLF file is held as LF in memory
        and its endings are restored on write. A file that MIXES endings is
        held exactly as it is: anchors then match only its LF lines, and
        everything else round-trips untouched.
        """
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise Stop(f"missing file: {rel}", EXIT_CANNOT_RUN)
            raw = p.read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            text = (raw[3:] if bom else raw).decode("utf-8")
            crlf = text.count("\r\n")
            all_crlf = crlf > 0 and crlf == text.count("\n")
            if all_crlf:
                text = text.replace("\r\n", "\n")
            self.files[rel] = text
            self.form[rel] = (bom, all_crlf)
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def delete(self, rel: str) -> None:
        """Mark a file for removal. Nothing leaves disk until flush()."""
        if not (self.root / rel).exists() and rel not in self.files:
            raise Stop(f"cannot delete {rel}: it is not in this checkout",
                       EXIT_CANNOT_RUN)
        self.files.pop(rel, None)
        self.deleted.add(rel)

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise Stop(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.", EXIT_CANNOT_RUN)
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel in sorted(self.deleted):
            p = self.root / rel
            if p.exists():
                p.unlink()
                touched.append(f"{rel} (deleted)")
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = self.encode(rel, text)
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched

    def encode(self, rel: str, text: str) -> bytes:
        """Text back to bytes in the form the file had when it was read.

        A file never read -- one this script creates -- has no form to keep
        and is written as plain UTF-8 with LF, which is what every file in
        this fleet is unless it says otherwise.
        """
        bom, all_crlf = self.form.get(rel, (False, False))
        if all_crlf:
            text = text.replace("\n", "\r\n")
        return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort", "killed" or "env" -- only exit code 1 means a
    test failed.

    pytest exits 0 passed, 1 tests failed, 2 interrupted, 3 internal error,
    4 usage error, 5 nothing collected; a native abort arrives as 134 or -6.
    Treating every non-zero code as a failing assertion is how a tool reports
    a regression that never happened.
    """
    if code == 0:
        return "pass"
    if code in (-9, 137, -15, 143):
        return "killed"
    if code in (134, -6, 139, -11) or "Fatal Python error" in out:
        return "abort"
    if code == 1 and "INTERNALERROR" not in out:
        # EXIT 1 IS NOT ALWAYS A TEST DISAGREEING, and this used to assume it
        # was. A missing pytest PLUGIN or a missing pinned package does not
        # stop collection -- the tests are found, then fail at setup -- so
        # pytest exits 1, the same code a real regression gives.
        #
        # It shipped that way. A fresh Codespace with the app requirements and
        # none of tests/requirements-dev.txt ran a round that had landed
        # cleanly and got 85 errors ("fixture 'qtbot' not found": pytest-qt)
        # and 3 failures ("No module named 'engine'": the rnv-brand pin), and
        # the verdict was "FAILED -- the suite is not green". Not one of the 88
        # was the change disagreeing with anything.
        #
        # The discriminator is the assertion. A regression raises
        # AssertionError; a missing dependency raises nothing of the kind. If
        # the run carries environment signatures and NO assertion failure, it
        # is the environment. If it carries both, it is a failure -- the
        # conservative direction, because under-reporting a real regression is
        # the one way this verdict must never be wrong.
        if _missing_dependency(out) and not _ASSERTION.search(out):
            return "env"
        return "fail"
    return "env"


#: A dependency that is not installed, as pytest reports it. Each of these
#: arrived in a real run of this fleet's suites.
_ENV_SIGNS = (
    re.compile(r"fixture '\w+' not found"),                 # a pytest plugin
    re.compile(r"ModuleNotFoundError: No module named"),    # a package
    re.compile(r"\bis not importable\b"),                   # the register pin
    re.compile(r"ImportError: lib[\w.+-]+\.so"),            # a system library
)
#: A real regression. pytest prints the failing line under `E   ` and the
#: exception class in the summary.
_ASSERTION = re.compile(r"^E\s+assert\b|\bAssertionError\b", re.M)


def _missing_dependency(out: str) -> bool:
    return any(sign.search(out) for sign in _ENV_SIGNS)


#: verdict -> taxonomy. "abort" and "killed" are EXIT_INCOMPLETE rather than
#: EXIT_CANNOT_RUN: the environment WAS ready and the run started, which is a
#: different instruction to the operator -- re-run, do not go installing things.
_VERDICT_CODE = {
    "pass": EXIT_CLEAN,
    "fail": EXIT_DISAGREES,
    "env": EXIT_CANNOT_RUN,
    "abort": EXIT_INCOMPLETE,
    "killed": EXIT_INCOMPLETE,
}


ENV_HELP = """\
THE ENVIRONMENT IS NOT READY. NO TEST DISAGREED WITH THIS CHANGE -- the run
did not get far enough to ask one.

PyQt6 needs system libraries a fresh container does not ship; the give-away is
`ImportError: libGL.so.1`. Install those, then the Python packages:

    sudo apt-get update
    sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\
      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\
      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \\
      libxcb-xfixes0 libxcb-xkb1

    pip install -r requirements.txt -r tests/requirements-dev.txt
    python up.py --verify
"""

ABORT_HELP = """\
PYTHON ABORTED NATIVELY. That is not a failing assertion. On offscreen Linux
these suites can abort in Qt's thread teardown -- it surfaces during whatever
work is in flight and reads exactly like a regression in it.

Re-run:

    python up.py --verify

If it aborts every time on the same test, that is worth looking at. If it
comes and goes, this change is not involved.
"""

KILLED_HELP = """\
THE TEST PROCESS WAS KILLED FROM OUTSIDE. No test failed and nothing crashed --
something stopped the run, and on a small runner that is almost always the
out-of-memory killer arriving part way through a long Qt suite.

Re-run:

    python up.py --verify

If it keeps dying at roughly the same point, run the suite on its own so you
can watch it, and close anything else heavy first:

    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
"""


def run(label: str, args: list[str]) -> tuple[int, str]:
    """Stream to a temp file rather than capture_output: a long Qt suite emits
    megabytes, and buffering that in memory can get the run killed, which looks
    exactly like a failure."""
    print(f"  {label} ...", flush=True)
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8",
                                errors="replace") as fh:
        proc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.seek(0)
        out = fh.read()
    return proc.returncode, out


def _step(label: str, args: list[str]) -> int:
    code, out = run(label, args)
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass"
          else "\n".join(out.strip().splitlines()[-3:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
    elif verdict == "abort":
        print("\n" + ABORT_HELP)
    elif verdict == "killed":
        print("\n" + KILLED_HELP)
    elif verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows exactly what landed.")
    return _VERDICT_CODE[verdict]


def verify() -> int:
    # A script that changes the ENVIRONMENT its suites run in does it here,
    # not in checks(): checks() runs against the in-memory tree before
    # anything is on disk. The register pin is the case that needed it -- it
    # writes a dependency line and then runs tests that import what the line
    # declares, and DECLARING IS NOT INSTALLING.
    #
    # In verify() rather than apply() so that `--verify` gets it too; that is
    # the entry point someone uses to re-check a repository, and it has to
    # prepare the same environment.
    hook = globals().get("post_write")
    if hook is not None:
        hook()
        print()

    # GUARD_CMD is OPTIONAL and exists for a repository with no pytest. Every
    # round until 2026-09-12 ran inside one of the five applications, where a
    # guard is a test file; rnv-brand has no tests directory, no pytest
    # dependency, and a deliberate ZERO-IMPORT policy in engine/brand.py --
    # its own idiom is a function that runs AT IMPORT and raises. Installing
    # pytest there to satisfy this harness would change the shape of someone
    # else's repository to suit a tool, which is backwards. GUARD still names
    # the file that holds the check; GUARD_CMD says how to run it.
    guard_cmd = globals().get("GUARD_CMD") or [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", GUARD]
    code = _step("guard", guard_cmd)
    if code != EXIT_CLEAN:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != EXIT_CLEAN:
            return code
    print("\nGreen.")
    return EXIT_CLEAN


def apply(check_only: bool) -> int:
    root = Path.cwd()

    # FIRST. Before the sentinel, before any anchor. See the docstring.
    refuse_wrong_repository(root)

    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise Stop(globals().get("MISSING_HELP") or
                   f"run this from the root of a {REPO} checkout "
                   f"(no {SENTINEL_FILE} here)", EXIT_CANNOT_RUN)

    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8-sig"):
        # ALREADY APPLIED IS NOT AN ERROR, AND USED TO EXIT 1.
        #
        # The operator runs this from a phone and the honest question behind a
        # second run is "did this land?". Exiting 1 answered "something
        # disagreed", which is the one thing that had not happened. Re-running
        # the suites answers the question that was actually asked, and a
        # repository that has the change and passes its tests is CLEAN.
        print(f"already applied -- {SENTINEL!r} is present in "
              f"{SENTINEL_FILE}.\nNothing to write. Re-running the suites so "
              f"the answer is measured rather than assumed.\n")
        return verify()

    tree = Tree(root)
    edits(tree)

    # THE SCRIPT MUST WRITE ITS OWN SENTINEL WHERE apply() LOOKS FOR IT.
    #
    # Checked here, against the in-memory tree, before anything reaches disk.
    #
    # WHY THIS IS NOT A BUILD-TIME CHECK. The build's `sentinel-written` guard
    # asserts the marker appears at least twice in the composed script -- its
    # own declaration plus somewhere it gets written. That is a PROXY. A round
    # can carry the marker in a new guard file and never put it in
    # SENTINEL_FILE, and the build passes while the already-applied branch can
    # never fire. That shipped once, on 2026-09-24: the operator ran a landed
    # script a second time and got "expected 1 occurrence of the anchor, found
    # 0. The file moved" -- about a file that had not moved, from a script
    # that could not tell it had already run.
    #
    # Here the question is exact rather than approximated: after every edit,
    # is the marker in the file apply() reads? It fires on the FIRST run, in
    # the author's verification, rather than on the operator's second.
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise Stop(
            f"this script never writes {SENTINEL!r} into {SENTINEL_FILE}, "
            f"which is the file it reads to tell whether it has already run.\n"
            f"Applied once it would work; run again it would re-attempt "
            f"anchors that are already replaced and report them as missing.\n"
            f"Add an edit that marks {SENTINEL_FILE}. Nothing was written.",
            EXIT_CANNOT_RUN)
    # GUARD_SOURCE is OPTIONAL. Every round until 2026-09-12 installed a new
    # guard file, so the harness assumed one; the ramp-condense round adopts
    # three that already exist -- the mixer's SPLITS table and two RETIRED
    # tuples -- and adding a fourth rule for what they already watch is how a
    # suite grows checks that disagree. GUARD still names the file verify()
    # runs first; it just does not have to be a file this script wrote.
    source = globals().get("GUARD_SOURCE")
    if source is not None:
        tree.write(GUARD, source)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        _left_alone()
        return EXIT_CLEAN

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    code = verify()
    if code == EXIT_CLEAN:
        _left_alone()
    return code


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    try:
        refuse_to_shadow()
        if args.finish:
            finish()
            return EXIT_CLEAN
        if args.verify:
            return verify()
        return apply(args.check)
    except Stop as stop:
        # Print it ourselves and return the taxonomy code. Letting SystemExit
        # propagate would print the message and exit 1 regardless of .code.
        print(stop.args[0] if stop.args else "", file=sys.stderr)
        return stop.code


if __name__ == "__main__":
    raise SystemExit(main())
