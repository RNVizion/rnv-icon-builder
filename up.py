"""Settings' Watching label is drawn in the dialog's own mode, and follows a switch

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-icon-builder, derived against a fresh clone at the live head (adca8a5).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-28: "2 and 3 look fine we can make those fixes" -- item 3 of
the three-questions render.

RNV-STATUS-FAMILY moved Settings' Watching label off STATUS_ACTIVE_COLOR, a
constant, onto the palette's status_active -- read with get_theme_colors()
and no mode, which returns the default palette: dark's. A dialog in light
drew dark's value, #ad85a3 on #f5f5f5, 2.89:1; light's own, #825d79, reads
5.08:1 there. And the label's sheet was set once, when watching started, so
a switch with the dialog open kept the mode it was set in.

The label reads the dialog's own mode now, and _apply_theme() -- which every
switch reaches through apply_theme_from_manager() -- styles it again while
watching. Dark and image draw what they drew. The pin in
tests/test_status_register.py that held the mode-blind spelling moves with
it.
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
SENTINEL = 'RNV-WATCH-LABEL'
SENTINEL_FILE = 'ui/settings_dialog.py'
GUARD = 'tests/test_watch_label_follows_a_switch.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_watch_label_follows_a_switch.py', 'tests/test_status_register.py']
DESCRIPTION = "Settings' Watching label is drawn in the dialog's own mode, and follows a switch"

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest.
SUITES = [("run_tests.py -- what both CI workflows run",
           [sys.executable, "run_tests.py"])]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': 'a25e73acb05f7498f1e3a9520ac4d5470fb50dc629deac7113759ee13502a25b', '.github/workflows/tests-windows.yml': 'eeb17b6a4fb8ba4a92b9ee6b182b16614bda3266c8a3e12da21cefc2f808ebd0'}

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py", "settings_dialog.py"}

LEFT_ALONE = ["the label while not watching: its own sheet is emptied and the dialog's #status_label rule draws it, in every mode, as before.", "image mode: the dialog paints itself with dark's palette there, so the label takes dark's status_active, #ad85a3 -- the value it had.", "the palettes: status_active is light's #825d79 and dark's #ad85a3, as the register walked them; only which one the label asks for moved."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/settings_dialog.py',
             "            # RNV-STATUS-FAMILY: read per mode. This was\n            # STATUS_ACTIVE_COLOR, a module constant, on a label\n            # that is painted in dark, light and image mode.\n            _active = get_theme_colors()['status_active']\n",
             "            # RNV-STATUS-FAMILY: read per mode. This was\n            # STATUS_ACTIVE_COLOR, a module constant, on a label\n            # that is painted in dark, light and image mode.\n            # RNV-WATCH-LABEL 2026-09-28: in the dialog's own mode. This\n            # asked get_theme_colors() for no mode, which is the default\n            # palette -- dark's -- so a dialog in light drew dark's value.\n            # _apply_theme() styles the label again on a switch.\n            _active = get_theme_colors(is_dark=self._current_theme_is_dark)['status_active']\n")
    tree.sub('ui/settings_dialog.py',
             '        colors = get_theme_colors(is_dark=is_dark)\n        self.setStyleSheet(self._build_stylesheet(colors))\n        \n        # Propagate theme to child widgets with their own stylesheets\n',
             '        colors = get_theme_colors(is_dark=is_dark)\n        self.setStyleSheet(self._build_stylesheet(colors))\n        \n        # RNV-WATCH-LABEL 2026-09-28: the Watching label carries a sheet of\n        # its own while watching, in the mode\'s status_active. Set once, when\n        # watching started, it kept that mode through every switch.\n        if self._is_watching:\n            self.watch_status_label.setStyleSheet(f"color: {colors[\'status_active\']};")\n        \n        # Propagate theme to child widgets with their own stylesheets\n')
    tree.sub('tests/test_status_register.py',
             'def test_the_watch_label_reads_the_theme_rather_than_a_constant():\n    src = (ROOT / "ui" / "settings_dialog.py").read_text(encoding="utf-8-sig")\n    assert "get_theme_colors()[\'status_active\']" in src\n',
             'def test_the_watch_label_reads_the_theme_rather_than_a_constant():\n    # RNV-WATCH-LABEL 2026-09-28: and the dialog\'s own mode. This pinned\n    # get_theme_colors() with no mode -- the default palette, dark\'s -- so\n    # a dialog in light drew dark\'s value. The label as drawn in each mode\n    # is held by tests/test_watch_label_follows_a_switch.py.\n    src = (ROOT / "ui" / "settings_dialog.py").read_text(encoding="utf-8-sig")\n    assert "get_theme_colors(is_dark=self._current_theme_is_dark)[\'status_active\']" in src\n    assert not re.search(r"get_theme_colors\\s*\\(\\s*\\)\\s*\\[\\s*\'status_active\'", _code_only(src)), (\n        "the watch label asks for the default palette again")\n')
    if (tree.root / 'tests/test_watch_label_follows_a_switch.py').exists():
        raise Stop('tests/test_watch_label_follows_a_switch.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_watch_label_follows_a_switch.py', '"""\ntests/test_watch_label_follows_a_switch.py\n==========================================\nRNV-WATCH-LABEL, 2026-09-28. The Settings dialog\'s Watching label is drawn\nin its own mode\'s status_active, and follows a switch.\n\nRNV-STATUS-FAMILY moved the label off STATUS_ACTIVE_COLOR, a constant, onto\nthe palette\'s status_active key -- read with get_theme_colors() and no mode,\nwhich is the default palette: dark\'s. A dialog in light drew dark\'s value,\n#ad85a3 on #f5f5f5, 2.89:1 -- under the 4.5:1 text floor the family was\nwalked to clear, and under 3:1; light\'s own, #825d79, reads 5.08:1 there.\nAnd the label\'s sheet was set once, when watching started, so a switch\nwith the dialog open kept the mode it was set in.\n\ntests/test_status_register.py holds the palettes; this holds the label as\nthe dialog draws it. Driven through the main window\'s own opener, theme\nbutton and watch callbacks: _open_settings(), cycle_theme(),\n_on_watch_started() and _on_watch_stopped(). The fixture\'s main window has\nno image mode (it skips loading the image resources), so image is reached\nthe way the main window hands it on: apply_theme_from_manager("image").\n"""\nfrom __future__ import annotations\n\nimport collections\n\nimport pytest\nfrom PyQt6.QtCore import QPoint, QRect\nfrom PyQt6.QtGui import QColor, QPalette\nfrom PyQt6.QtWidgets import QApplication\n\nfrom ui.colors import get_theme_colors\n\nFOLDER = "C:/Users/you/Icons/incoming"\nTEXT_FLOOR = 4.5\n\n\ndef _ink(label) -> str:\n    """The colour the label\'s text is drawn in, as its sheet resolves."""\n    label.ensurePolished()\n    return label.palette().color(QPalette.ColorRole.WindowText).name()\n\n\ndef _active(mode: str) -> str:\n    """status_active from the palette the dialog is painted with in `mode`:\n    dark\'s in dark and image, light\'s in light."""\n    return get_theme_colors(is_dark=mode in ("dark", "image"))["status_active"].lower()\n\n\ndef _lum(c: QColor) -> float:\n    def ch(v):\n        v /= 255\n        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4\n    return 0.2126 * ch(c.red()) + 0.7152 * ch(c.green()) + 0.0722 * ch(c.blue())\n\n\ndef _contrast(a: QColor, b: QColor) -> float:\n    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)\n    return (hi + 0.05) / (lo + 0.05)\n\n\ndef _ground(dlg, label) -> QColor:\n    """The ground under the label as the dialog draws it: the commonest pixel\n    of the dialog\'s own grab over the label\'s rectangle. Not label.grab(),\n    which fills with the label\'s palette -- #000000 in dark, where the\n    dialog draws #1a1a1a."""\n    img = dlg.grab(QRect(label.mapTo(dlg, QPoint(0, 0)), label.size())).toImage()\n    counts = collections.Counter(img.pixelColor(x, y).name()\n                                 for y in range(img.height()) for x in range(img.width()))\n    return QColor(counts.most_common(1)[0][0])\n\n\ndef _settings(app, mode: str):\n    """Settings, opened with the main window\'s own opener in `mode`, watching."""\n    for _ in range(3):\n        if app.theme_manager.current_theme == mode:\n            break\n        app.cycle_theme()\n    assert app.theme_manager.current_theme == mode\n    app._open_settings()\n    QApplication.processEvents()\n    app._on_watch_started(FOLDER)\n    QApplication.processEvents()\n    dlg = app.settings_dialog\n    assert dlg is not None and dlg.watch_status_label.text().endswith(FOLDER)\n    label = dlg.watch_status_label\n    page = next(dlg.tabs.widget(i) for i in range(dlg.tabs.count())\n                if dlg.tabs.widget(i).isAncestorOf(label))\n    dlg.tabs.setCurrentWidget(page)                           # the tab the label is on\n    QApplication.processEvents()\n    return dlg\n\n\nclass TestTheWatchingLabelFollowsTheDialogsMode:\n\n    def test_a_dialog_opened_in_light_draws_light_s_value(self, app):\n        dlg = _settings(app, "light")\n        assert _ink(dlg.watch_status_label) == _active("light"), (\n            "a dialog in light draws another mode\'s status_active")\n        dlg.close()\n\n    def test_a_switch_with_the_dialog_open_restyles_the_label(self, app):\n        dlg = _settings(app, "dark")\n        label = dlg.watch_status_label\n        assert _ink(label) == _active("dark")\n        modes = []\n        for _ in range(2):                                   # dark -> light -> dark\n            app.cycle_theme()\n            QApplication.processEvents()\n            mode = app.theme_manager.current_theme\n            modes.append(mode)\n            assert _ink(label) == _active(mode), (mode, _ink(label))\n        assert modes == ["light", "dark"], modes\n        dlg.apply_theme_from_manager("image")                 # as the main window hands image on\n        assert _ink(label) == _active("image")\n        dlg.close()\n\n    @pytest.mark.parametrize("mode", ["dark", "light"])\n    def test_the_label_clears_the_text_floor_on_the_ground_it_is_drawn_on(self, app, mode):\n        dlg = _settings(app, "dark" if mode == "light" else "light")\n        app.cycle_theme()                                     # arrive in `mode` by a switch\n        QApplication.processEvents()\n        assert app.theme_manager.current_theme == mode\n        label = dlg.watch_status_label\n        assert label.isVisible(), "the label is not on screen"\n        ground = _ground(dlg, label)\n        ratio = _contrast(QColor(_ink(label)), ground)\n        assert ratio >= TEXT_FLOOR, f"{mode}: {_ink(label)} on {ground.name()} = {ratio:.2f}"\n        assert _ink(label) == _active(mode), (mode, _ink(label))\n        dlg.close()\n\n    def test_stopping_hands_the_label_back_to_the_dialog_s_sheet(self, app):\n        dlg = _settings(app, "dark")\n        app.cycle_theme()\n        app._on_watch_stopped()\n        QApplication.processEvents()\n        label = dlg.watch_status_label\n        assert label.styleSheet() == "" and not dlg._is_watching\n        app.cycle_theme()                                     # no longer watching: left alone\n        QApplication.processEvents()\n        assert label.styleSheet() == "", "a switch styled a label that is not watching"\n        dlg.close()\n')


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
    DIALOG, PIN, APP = "ui/settings_dialog.py", "tests/test_status_register.py", "RNV_Icon_Builder.py"

    def methods(src):
        c = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == "SettingsDialog")
        return {n.name: n for n in c.body if isinstance(n, ast.FunctionDef)}

    old_src, new_src = _original(tree, DIALOG), tree.read(DIALOG)
    o, n = methods(old_src), methods(new_src)
    assert set(o) == set(n), f"SettingsDialog: methods added or removed: {sorted(set(o) ^ set(n))}"
    moved = sorted(k for k in o if ast.dump(o[k]) != ast.dump(n[k]))
    assert moved == ["_apply_theme", "update_watch_status"], f"SettingsDialog: moved {moved}"

    # the label reads the dialog's own mode, and nothing else in the method moved
    MODE = "get_theme_colors(is_dark=self._current_theme_is_dark)"
    watch = ast.unparse(n["update_watch_status"])
    assert watch.count(MODE) == 1, "the Watching label does not read the dialog's mode"
    assert watch.replace(MODE, "get_theme_colors()") == ast.unparse(o["update_watch_status"]), \
        "update_watch_status() changed beyond reading the dialog's mode"

    # and is styled again, with the same sheet, when the dialog is
    ob = [ast.unparse(s) for s in o["_apply_theme"].body]
    nb = [ast.unparse(s) for s in n["_apply_theme"].body]
    at = ob.index("self.setStyleSheet(self._build_stylesheet(colors))") + 1
    assert nb[:at] + nb[at + 1:] == ob, "_apply_theme() changed beyond restyling the Watching label"
    hook = n["_apply_theme"].body[at]
    assert isinstance(hook, ast.If) and ast.unparse(hook.test) == "self._is_watching" \
        and len(hook.body) == 1 and not hook.orelse, \
        "the Watching label is not restyled while, and only while, watching"
    (restyle,) = _calls(hook, "setStyleSheet")
    assert ast.unparse(restyle.func.value) == "self.watch_status_label", "the switch restyles another widget"
    (first,) = [c for c in _calls(n["update_watch_status"], "setStyleSheet")
                if ast.unparse(c.func.value) == "self.watch_status_label" and isinstance(c.args[0], ast.JoinedStr)]
    assert _sheet_parts(restyle) == _sheet_parts(first), "the switch styles the label with another sheet"
    assert "colors['status_active']" in ast.unparse(restyle), "the switch styles the label from another key"

    # the premises: the flag exists before the dialog is first styled, the
    # dialog records its mode where the label reads it, and both of the main
    # window's roads hand the mode on
    init = [ast.unparse(s) for s in n["__init__"].body]
    flag = next(i for i, s in enumerate(init) if s.startswith("self._is_watching"))
    styled = next(i for i, s in enumerate(init) if s.startswith("self._apply_theme("))
    assert flag < styled, "_apply_theme() runs before the watching flag exists"
    atm = ast.unparse(n["apply_theme_from_manager"])
    assert "self._current_theme_is_dark = is_dark" in atm and "self._apply_theme(is_dark)" in atm, \
        "apply_theme_from_manager() no longer records the mode and styles the dialog"
    app = next(c for c in ast.parse(tree.read(APP)).body
               if isinstance(c, ast.ClassDef) and c.name == "IconBuilderApp")
    fns = {f.name: f for f in app.body if isinstance(f, ast.FunctionDef)}
    for road in ("cycle_theme", "_open_settings"):
        assert "self.settings_dialog.apply_theme_from_manager(" in ast.unparse(fns[road]), \
            f"{road}() does not hand the mode to the Settings dialog"

    # the pin that held the old spelling moves, and nothing else in its file
    old_pin, new_pin = _original(tree, PIN), tree.read(PIN)
    name = "test_the_watch_label_reads_the_theme_rather_than_a_constant"
    rest = lambda src: [ast.dump(x) for x in ast.parse(src).body   # noqa: E731
                        if not (isinstance(x, ast.FunctionDef) and x.name == name)]
    assert rest(old_pin) == rest(new_pin), f"{PIN} moved beyond the pin on the Watching label"
    pin = ast.unparse(_function(new_pin, name))
    assert MODE + "['status_active']" in pin, "the pin does not hold the dialog's mode"
    assert "STATUS_ACTIVE_COLOR" in pin and "asks for the default palette again" in pin, \
        "the pin lost a check"

    # the guard: new, and marked
    guard = tree.read(GUARD)
    ast.parse(guard)
    assert SENTINEL in guard and "class TestTheWatchingLabelFollowsTheDialogsMode" in guard, \
        "the guard is not the one this round writes"
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
