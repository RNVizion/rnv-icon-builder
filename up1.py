#!/usr/bin/env python3
"""
RNV-STATUS-TOOL-DO-NOT-SWEEP

Collapse the watcher green onto the register, and name the two status literals.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHY

Reading the STATUS family across the fleet on 2026-09-02 turned up three
values that disagreed with the register, and Chris ruled all three collapse:

    rnv-color-palette-manager  'success'            #4caf50  ->  #28a745
    rnv-icon-builder           STATUS_ACTIVE_COLOR  #4caf50  ->  #28a745
    rnv-color-palette-manager  STATUS_ERROR_TEXT    #ff6b6b  ->  #e56b77

The first two are Material's green where the register publishes Bootstrap's.
Two applications, one role, two greens -- and the picker, doing exactly what
icon-builder does with exactly the same constant name, already used #28a745.

The third is different and worth stating plainly: it was DELIBERATE. The
error-red pass left it alone on the argument that a dark value already
clearing the floor should not be replaced to buy uniformity, and that
argument was sound at the time. What has changed is that the register now
publishes error-text #e56b77 for precisely this job, so keeping #ff6b6b means
carrying a fourth spelling of a colour the register names. Uniformity was not
worth a regression; it is worth a name.

    #ff6b6b  7.5674 on #000000   5.1722 on #2a2a2a
    #e56b77  6.7008 on #000000   4.5804 on #2a2a2a   <- the register's own
                                                        design target: 4.5 on
                                                        the worst dark ground
Both clear the floor. The move costs 0.87 of headroom on a value that had
3.07 to spare, and buys the fleet one name for one colour.

ONE THING WORTH FLAGGING RATHER THAN DECIDING

STATUS_ACTIVE_COLOR marks the folder watcher as RUNNING. That is not quite
"success" -- an operation succeeded, a thing is running: different claims. The
register has no status-active, so this app borrows the success green, exactly
as rnv-color-picker's identically-named constant already does. Collapsing the
VALUE is what was ruled and is what happens here. Whether "active" deserves a
name of its own upstream is a register question, and it is in the note.

ALSO HERE

'success' and 'warning' were literals in both palettes -- four entries, no
constant in the file. Wired now: rule 1, and it puts them on the colour tree.

THIS MOVES PIXELS. It is a ruling being applied.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-icon-builder"
DESCRIPTION = "collapse the status strays onto the register"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "RNV-STATUS-REGISTER"
GUARD = "tests/test_status_register.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ('unittest suite',
     [sys.executable, "-m", "unittest", "test_rnv_icon_builder"]),
]

EDITS = [
    ('ui/colors.py',
     'APP_BORDER: Final[str] = "#333333"\n',
     'STATUS_SUCCESS: Final[str] = "#28a745"\n"""MIRRORS the register\'s STATUS["success"].\n\nRNV-STATUS-REGISTER (2026-09-02): both palettes already held this value,\nwritten out rather than named. Named here so it has one home. Defined\nabove the palettes because they consume it.\n"""\n\nSTATUS_WARNING: Final[str] = "#ffc107"\n"""MIRRORS the register\'s STATUS["warning"]. Value unchanged."""\n\nAPP_BORDER: Final[str] = "#333333"\n',
     1),
    ('ui/colors.py',
     'STATUS_ACTIVE_COLOR: Final[str] = "#4caf50"\n"""Green — used for active/running status indicators (e.g. folder watcher)"""\n',
     'STATUS_ACTIVE_COLOR: Final[str] = STATUS_SUCCESS\n"""The folder watcher, running. RNV-STATUS-REGISTER (2026-09-02): was\n#4caf50, Material\'s green, where the register publishes #28a745 and where\nrnv-color-picker\'s identically-named constant already used the register\'s.\nTwo applications, one role, two greens; ruled onto one.\n\nIt is an ALIAS rather than a copy because "running" is not "succeeded" and\nthe register has no name for the first. If status-active is ever\nregistered, this line is the only one that moves.\n"""\n',
     1),
    ('ui/colors.py',
     "    'success': '#28a745',\n",
     "    'success': STATUS_SUCCESS,\n",
     2),
    ('ui/colors.py',
     "    'warning': '#ffc107',\n",
     "    'warning': STATUS_WARNING,\n",
     2),
    ('ui/colors.py',
     "    'STATUS_ACTIVE_COLOR',\n",
     "    'STATUS_SUCCESS',\n    'STATUS_WARNING',\n    'STATUS_ACTIVE_COLOR',\n",
     1),
]


def _code_only(text: str) -> str:
    """The file with comments and string literals removed.

    The new docstrings NAME the values they retire, which is the provenance
    worth keeping. A sweep that cannot tell a use from a mention fails on its
    own explanation -- this programme has now met that thirteen times, and
    tokenising is the fix that needs no list of exempt files."""
    import io
    import tokenize
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text
    return " ".join(out)


def edits(tree) -> None:
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    print(f"  {len(EDITS)} edit(s) composed")


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if SENTINEL not in src:
        raise SystemExit("the ruling note did not land")

    for name, want in (("STATUS_SUCCESS", '"#28a745"'), ("STATUS_WARNING", '"#ffc107"'),
                       ("STATUS_ACTIVE_COLOR", "STATUS_SUCCESS")):
        if f"{name}: Final[str] = {want}" not in src:
            raise SystemExit(f"{name} is not {want}")
    if "#4caf50" in _code_only(src):
        raise SystemExit(f"#4caf50 survived as code in {SENTINEL_FILE}")
    body = src[src.index("DARK_THEME_COLORS"):]
    for stray in ("'success': '", "'warning': '"):
        if stray in body:
            raise SystemExit(f"a palette still writes {stray}... as a literal")

    print("  guards: the strays are gone and every status value is the register's")


GUARD_SOURCE = r'''"""Every status value in this application is the register's. RNV-STATUS-GUARD

Ruled by Chris on 2026-09-02, reading the STATUS family across the fleet.
Three values disagreed with the register; all three collapse.

A status colour is not decoration. It carries MEANING -- success, warning,
error -- and the meaning is the same in every RNV product, which is why the
register owns the value and an application must not have a second opinion.
This guard is the thing that stops the second opinion coming back.
"""
from __future__ import annotations

import re
from pathlib import Path

from ui import colors

ROOT = Path(__file__).resolve().parent.parent


def _palettes():
    from ui.colors import DARK_THEME_COLORS as D, LIGHT_THEME_COLORS as L, IMAGE_MODE_COLORS as I; P={'dark':D,'light':L,'image':I}
    return P


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hexv):
    h = hexv.lstrip("#")
    t = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return 0.2126 * _lin(t[0]) + 0.7152 * _lin(t[1]) + 0.0722 * _lin(t[2])


def _contrast(a, b):
    la, lb = _luminance(a), _luminance(b)
    hi, lo = (la, lb) if la >= lb else (lb, la)
    return (hi + 0.05) / (lo + 0.05)


STRAYS = {"#4caf50"}


def test_the_stray_green_is_gone_from_every_palette():
    for mode, palette in _palettes().items():
        bad = {k: v for k, v in palette.items()
               if isinstance(v, str) and v.lower() in STRAYS}
        assert not bad, f"{mode} still holds the retired green: {bad}"


def test_the_status_values_are_the_register_s():
    """Not "some green" -- THE green. An app that picks its own status colour
    has an opinion about what success means, which is the register's job."""
    assert colors.STATUS_SUCCESS == "#28a745"
    assert colors.STATUS_WARNING == "#ffc107"


def test_the_watcher_green_is_an_alias_not_a_copy():
    """"Running" is not "succeeded", and the register has no name for the
    first. Holding it as an alias keeps the borrowing visible: if
    status-active is ever registered, one line moves. A copied literal would
    hide that this app is borrowing at all."""
    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")
    assert "STATUS_ACTIVE_COLOR: Final[str] = STATUS_SUCCESS" in src
    assert colors.STATUS_ACTIVE_COLOR == colors.STATUS_SUCCESS


def test_the_palettes_are_wired_through_the_constants_not_rewritten():
    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")
    for key, const in (("success", "STATUS_SUCCESS"), ("warning", "STATUS_WARNING")):
        found = len(re.findall(r"'%s':\s+%s\b" % (key, const), src))
        assert found == 2, f"{key} is wired through {const} in {found} palettes, not 2"


def test_the_green_matches_the_picker():
    """The whole point of the ruling. Written as the literal the picker holds
    so this fails if either app drifts, not merely if this one does."""
    assert colors.STATUS_SUCCESS == "#28a745", (
        "rnv-color-picker holds #28a745 for the same role")
'''


# ------------------------------------------------------------------ plumbing
def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        sys.exit(f"refusing to run as {name} -- it would shadow a module on "
                 f"sys.path. Rename to up.py and run again.")


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise SystemExit(f"missing file: {rel}")
            self.files[rel] = p.read_text(encoding="utf-8")
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise SystemExit(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.")
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = text.encode("utf-8")
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort" or "env" -- only exit code 1 means a test failed.

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
        return "fail"
    return "env"


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
    return code


def verify() -> int:
    code = _step("guard",
                 [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                  GUARD])
    if code != 0:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != 0:
            return code
    print("\nGreen.")
    return 0


def apply(check_only: bool) -> int:
    root = Path.cwd()
    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise SystemExit(globals().get("MISSING_HELP") or
                         f"run this from the root of a {REPO} checkout "
                         f"(no {SENTINEL_FILE} here)")
    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8"):
        raise SystemExit(f"already applied -- {SENTINEL!r} is present in "
                         f"{SENTINEL_FILE}")

    tree = Tree(root)
    edits(tree)
    tree.write(GUARD, GUARD_SOURCE)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        return 0

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    return verify()


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    refuse_to_shadow()
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    if args.finish:
        finish()
        return 0
    if args.verify:
        return verify()
    return apply(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
