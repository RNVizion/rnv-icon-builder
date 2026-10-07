"""the icon builder's rulings of 5 October: the analyzer's PNG mark is drawn, the workflows' actions are at the versions built for Node 24, and the README's test counts cannot go stale

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-icon-builder, derived against a fresh clone at the live head (dee779a).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-05, items 1, 14 and 18 of the list of 4 October:

  1   "Yes"
  14  "Yes do it."
  18  "Do B."

ITEM 1. The ICO analyzer marks a PNG row by colouring its Compression cell.
It set Qt's dark green there, and the mark was never drawn: the dialog's
stylesheet coloured every cell, and a stylesheet wins over a cell's own
colour. PNG was drawn like BMP in every mode. Now the item rule sets no
colour, so a cell's own colour is drawn, and a cell without one takes the
table's, which is the value the rule gave it. The mark is the palette's
status_active, each mode's success text: 5.52:1 on the dark table's rows
and 4.55:1 on its alternate rows, 5.54:1 and 5.35:1 on the light one's.
Dark green would have read 3.39:1 on the dark table.

PROVEN BEFORE BUILDING, on the pixels, in dark, light and image. A table
with no PNG row is drawn as it was. A table with PNG rows differs inside
the PNG cells and nowhere else. A selected row keeps the selection's ink.

ITEM 14. The workflows used actions/checkout@v4, actions/setup-python@v5
and actions/upload-artifact@v4. Each is built for Node 20, which GitHub
took off its runners on 2026-09-23; since then they are run on Node 24 with
a warning on every job. They move to the first versions built for Node 24:
checkout v5, setup-python v6, upload-artifact v6, the versions the brand
repository moved to on 2026-10-04. Each action's own action.yml was read at
both versions: every input these workflows pass is an input of the newer
one, with the same default.

ITEM 18. The README stated 896 tests; pytest collected 1,163. Every count is
a floor now: over 1,100 tests, over 400 in the root suite, over 600 under
tests/. A floor is the number of test functions the suite defines, rounded
down to the hundred, so the next test leaves it true. The count beside the
file tree is dropped.

THE GUARDS. tests/test_png_mark_draws.py reads the mark back from the
table's own pixels. tests/test_workflow_actions.py holds every action in
every workflow at its floor. tests/test_readme_test_counts.py holds every
count in the README to a floor, and every floor to the truth.

WHAT ONLY A RUN ON GITHUB SHOWS. That the workflows run with the newer
actions. The first run after this is committed is that test.
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
SENTINEL = 'RNV-RULINGS-2026-10-05'
SENTINEL_FILE = '.github/workflows/tests-linux.yml'
GUARD = 'tests/test_png_mark_draws.py'
GUARD_FILES = ['tests/test_png_mark_draws.py', 'tests/test_workflow_actions.py', 'tests/test_readme_test_counts.py']
ROOT_SUITE = 'test_rnv_icon_builder.py'
ACTIONS_GUARD = 'tests/test_workflow_actions.py'
README_GUARD = 'tests/test_readme_test_counts.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_png_mark_draws.py', 'tests/test_workflow_actions.py', 'tests/test_readme_test_counts.py']
DESCRIPTION = "the icon builder's rulings of 5 October: the analyzer's PNG mark is drawn, the workflows' actions are at the versions built for Node 24, and the README's test counts cannot go stale"

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest.
SUITES = [("python run_tests.py  (both CI workflows)",
           [sys.executable, "run_tests.py"])]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': 'a25e73acb05f7498f1e3a9520ac4d5470fb50dc629deac7113759ee13502a25b', '.github/workflows/tests-windows.yml': 'eeb17b6a4fb8ba4a92b9ee6b182b16614bda3266c8a3e12da21cefc2f808ebd0'}

SHADOWS = {"conftest.py", "run_tests.py", "test_rnv_icon_builder.py", "ico_analyzer.py", "colors.py", "test_named_and_used.py", "test_png_mark_draws.py", "test_workflow_actions.py", "test_readme_test_counts.py"}

LEFT_ALONE = ["a selected row: its text is the selection's ink, PNG included, as before. The mark shows on the rows that are not selected.", "the counts other documents state: TEST_SYSTEM.md, docs/INTERNALS.md and the runner's banner. Item 18 ruled the README.", 'the coverage figure printed beside the counts: a coverage figure depends on the platform it was taken on.', "the rulings still open on the list of 5 October: white or black text on the light gold fill (item 4), the Find and Replace dialog's clipped buttons (12), the transformer's line-number editor (7) and its Export tab (9). Nothing here touches them."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/ico_analyzer.py',
             'from PyQt6.QtGui import QFont\n',
             'from PyQt6.QtGui import QColor, QFont\n')
    tree.sub('ui/ico_analyzer.py',
             "            comp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)\n            # Color code: green for PNG, default for BMP\n            if compression == 'PNG':\n                comp_item.setForeground(Qt.GlobalColor.darkGreen)\n            self.images_table.setItem(row, 1, comp_item)\n",
             '            comp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)\n            self.images_table.setItem(row, 1, comp_item)\n')
    tree.sub('ui/ico_analyzer.py',
             '            pct_item = QTableWidgetItem(f"{percentage:.1f}%")\n            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)\n            self.images_table.setItem(row, 4, pct_item)\n    \n    def _format_bytes(self, size: int) -> str:\n',
             '            pct_item = QTableWidgetItem(f"{percentage:.1f}%")\n            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)\n            self.images_table.setItem(row, 4, pct_item)\n        \n        self._mark_png_rows()\n    \n    def _mark_png_rows(self) -> None:\n        """\n        Draw PNG in the mode\'s success text. BMP keeps the table\'s own.\n        \n        RNV-RULINGS-2026-10-05, item 1. The mark was Qt\'s dark green, set on the\n        cell and never drawn: the sheet\'s QTableWidget::item rule coloured\n        every cell, and a sheet wins over a cell\'s own colour. That rule no\n        longer sets one (see _apply_theme), and the mark is the palette\'s\n        status_active, which holds each mode\'s success text.\n        \n        Called when the table is filled and when the theme is applied, so\n        a mark made in one mode is not left in another\'s colour.\n        """\n        mark = QColor(get_theme_colors(is_dark=self._dark_mode)[\'status_active\'])\n        for row in range(self.images_table.rowCount()):\n            item = self.images_table.item(row, 1)\n            if item is not None and item.text() == \'PNG\':\n                item.setForeground(mark)\n    \n    def _format_bytes(self, size: int) -> str:\n')
    tree.sub('ui/ico_analyzer.py',
             '        """Apply theme styling to the dialog."""\n        c = get_theme_colors(is_dark=dark_mode)\n',
             '        """Apply theme styling to the dialog."""\n        # The mode the PNG mark is drawn for: _mark_png_rows() reads it.\n        self._dark_mode = bool(dark_mode)\n        c = get_theme_colors(is_dark=dark_mode)\n')
    tree.sub('ui/ico_analyzer.py',
             "            QTableWidget::item {{\n                padding: 5px;\n                background-color: {c['list_bg']};\n                color: {c['text_primary']};\n            }}\n",
             "            QTableWidget::item {{\n                padding: 5px;\n                background-color: {c['list_bg']};\n            }}\n")
    tree.sub('ui/ico_analyzer.py',
             '            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{\n                height: 0px;\n            }}\n        """)\n    \n    def apply_theme_from_manager(self, theme_name: str) -> None:\n',
             '            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{\n                height: 0px;\n            }}\n        """)\n        # RNV-RULINGS-2026-10-05, item 1. QTableWidget::item above sets no colour: a\n        # cell\'s own colour is drawn, and a cell without one takes the\n        # table\'s (QTableWidget\'s `color`, the same value). With a colour\n        # there, the sheet won and the PNG mark was never drawn.\n        self._mark_png_rows()\n    \n    def apply_theme_from_manager(self, theme_name: str) -> None:\n')
    tree.sub('tests/test_named_and_used.py',
             '    ("utils/config.py", "black"):\n        "the name a preview background choice is stored under: an option, not a colour",\n    ("ui/ico_analyzer.py", "Qt.GlobalColor.darkGreen"):\n        "HELD, and not data. Set on a PNG row\'s cell and never drawn: the table\'s stylesheet "\n        "colours every cell, and the sheet wins. Proven 2026-10-04 with a magenta control, in "\n        "all three modes. A ruling is asked: draw the mark, or drop the line",\n}\n',
             '    ("utils/config.py", "black"):\n        "the name a preview background choice is stored under: an option, not a colour",\n}\n')
    tree.sub('.github/workflows/tests-linux.yml',
             'uses: actions/checkout@v4\n',
             'uses: actions/checkout@v5\n')
    tree.sub('.github/workflows/tests-linux.yml',
             'uses: actions/setup-python@v5\n',
             'uses: actions/setup-python@v6\n')
    tree.sub('.github/workflows/tests-linux.yml',
             'uses: actions/upload-artifact@v4\n',
             'uses: actions/upload-artifact@v6\n')
    tree.sub('.github/workflows/tests-linux.yml',
             '\njobs:\n',
             '\n# RNV-RULINGS-2026-10-05, item 14. Each action below is at the first version\n# built for Node 24: checkout v5, setup-python v6 and upload-artifact v6.\n# GitHub took Node 20 off its runners on 2026-09-23, and ran the versions\n# before these on Node 24 with a warning. tests/test_workflow_actions.py\n# holds the floor.\njobs:\n')
    tree.sub('.github/workflows/tests-windows.yml',
             'uses: actions/checkout@v4\n',
             'uses: actions/checkout@v5\n')
    tree.sub('.github/workflows/tests-windows.yml',
             'uses: actions/setup-python@v5\n',
             'uses: actions/setup-python@v6\n')
    tree.sub('.github/workflows/tests-windows.yml',
             'uses: actions/upload-artifact@v4\n',
             'uses: actions/upload-artifact@v6\n')
    tree.sub('.github/workflows/tests-windows.yml',
             '\njobs:\n',
             '\n# RNV-RULINGS-2026-10-05, item 14. Each action below is at the first version\n# built for Node 24: checkout v5, setup-python v6 and upload-artifact v6.\n# GitHub took Node 20 off its runners on 2026-09-23, and ran the versions\n# before these on Node 24 with a warning. tests/test_workflow_actions.py\n# holds the floor.\njobs:\n')
    tree.sub('README.md',
             '![Tests](https://img.shields.io/badge/tests-896%20passing-brightgreen)\n',
             '![Tests](https://img.shields.io/badge/tests-1100%2B%20passing-brightgreen)\n')
    tree.sub('README.md',
             '├── test_rnv_icon_builder.py   # Legacy unittest suite (471 tests)\n',
             '├── test_rnv_icon_builder.py   # Legacy unittest suite\n')
    tree.sub('README.md',
             'two complementary test suites totaling **896 tests** with **70.21% branch coverage**',
             'two complementary test suites totaling **over 1,100 tests** with **70.21% branch coverage**')
    tree.sub('README.md',
             '| Legacy unittest | `test_rnv_icon_builder.py` | 471 | Original test suite, run via `unittest` |\n',
             '| Legacy unittest | `test_rnv_icon_builder.py` | over 400 | Original test suite, run via `unittest` |\n')
    tree.sub('README.md',
             '| pytest | `tests/` | 425 | Modern fixtures, qtbot, hypothesis, subprocess, snapshots |\n',
             '| pytest | `tests/` | over 600 | Modern fixtures, qtbot, hypothesis, subprocess, snapshots |\n')
    if (tree.root / 'tests/test_png_mark_draws.py').exists():
        raise Stop('tests/test_png_mark_draws.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_png_mark_draws.py', '"""A PNG row in the ICO analyzer is marked, and the mark is drawn.\n\nRNV-RULINGS-2026-10-05, item 1. Ruled 2026-10-05: "Yes".\n\nWHAT WAS THERE. The analyzer set Qt\'s dark green on a PNG row\'s Compression\ncell, and it was never drawn. The dialog\'s sheet coloured every cell\n(`QTableWidget::item { color: ... }`), and a sheet wins over a cell\'s own\ncolour, so PNG was drawn like BMP in every mode. Shown on 2026-10-04 with a\nmagenta control: the cell set to magenta moved no pixel.\n\nWHAT IS THERE NOW. The item rule sets no colour, so a cell\'s own colour is\ndrawn; a cell that has none takes the table\'s, which is the colour the rule\ngave it. And the mark is the palette\'s `status_active`, which holds each\nmode\'s success text.\n\nWHAT THIS GUARD HOLDS.\n\n1. A PNG cell holds the mode\'s success text. A BMP cell holds no colour of\n   its own.\n2. The mark is DRAWN. Read back from the table\'s own pixels, as a\n   comparison: how far a PNG cell\'s text stands from its ground, against how\n   far a BMP cell\'s does. Text is drawn with soft edges, more or less so\n   from one machine to the next, and the comparison does not care how soft.\n   This is the test the old line would have failed.\n3. The sheet\'s item rule sets no colour. That is why the mark draws, and it\n   is the line a tidy-up would put back.\n4. The mark follows the mode: a theme applied again marks again.\n5. The mark can be read where it sits: 4.5:1 or better on both of the\n   table\'s row grounds, in both palettes.\n"""\nfrom __future__ import annotations\n\nimport re\n\nimport pytest\nfrom PyQt6.QtCore import Qt\nfrom PyQt6.QtGui import QColor, QImage\nfrom PyQt6.QtWidgets import QApplication\n\nfrom ui.colors import get_theme_colors\n\nINFO = {\n    "file_name": "sample.ico", "file_size": 4096, "image_count": 3, "has_png": True, "has_bmp": True,\n    "sizes": ["256x256", "48x48", "16x16"],\n    "images": [\n        {"width": 256, "height": 256, "compression": "PNG", "bits_per_pixel": 32, "bytes": 3072},\n        {"width": 48, "height": 48, "compression": "BMP", "bits_per_pixel": 32, "bytes": 768},\n        {"width": 16, "height": 16, "compression": "PNG", "bits_per_pixel": 32, "bytes": 256},\n    ],\n}\nPNG_ROWS, BMP_ROWS, COMPRESSION = (0, 2), (1,), 1\nMODES = (("dark", True), ("light", False), ("image", True))\n\n\ndef _lum(colour: str) -> float:\n    c = QColor(colour)\n    def lin(v):\n        v /= 255\n        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4\n    return 0.2126 * lin(c.red()) + 0.7152 * lin(c.green()) + 0.0722 * lin(c.blue())\n\n\ndef _ratio(a: str, b: str) -> float:\n    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)\n    return (hi + 0.05) / (lo + 0.05)\n\n\ndef _far(a: QColor, b: QColor) -> int:\n    return abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue())\n\n\ndef _reach(table, row: int, column: int) -> tuple:\n    """(the cell\'s ground, how far its text stands from that ground): the\n    distance of the pixel furthest from the ground."""\n    image = table.viewport().grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)\n    rect = table.visualItemRect(table.item(row, column))\n    ground = image.pixelColor(rect.left() + 2, rect.top() + 2)\n    far = max(_far(image.pixelColor(x, y), ground)\n              for y in range(rect.top() + 2, rect.bottom() - 1)\n              for x in range(rect.left() + 2, rect.right() - 1))\n    assert far > 60, f"no text was found in cell ({row}, {column})"\n    return ground, far\n\n\n@pytest.fixture\ndef analyzer(qapp, qtbot):\n    from ui.ico_analyzer import IcoAnalyzerDialog\n    qapp.setStyle("Fusion")                 # the style the application runs in\n    kept = []                               # a dialog nothing holds is deleted, and its table with it\n\n    def build(mode: str):\n        dialog = IcoAnalyzerDialog(parent=None)\n        kept.append(dialog)\n        qtbot.addWidget(dialog)\n        dialog.apply_theme_from_manager(mode)\n        dialog._display_info(INFO)\n        dialog.resize(700, 520)\n        dialog.show()\n        table = dialog.images_table\n        table.clearSelection()\n        table.setCurrentCell(-1, -1)\n        table.clearFocus()\n        QApplication.processEvents()\n        return dialog\n    return build\n\n\n@pytest.mark.ui\n@pytest.mark.parametrize("mode,is_dark", MODES)\ndef test_a_png_cell_holds_the_modes_success_text(analyzer, mode, is_dark):\n    table = analyzer(mode).images_table\n    palette = get_theme_colors(is_dark=is_dark)\n    for row in PNG_ROWS:\n        item = table.item(row, COMPRESSION)\n        assert item.text() == "PNG"\n        assert item.foreground().color().name() == QColor(palette["status_active"]).name(), \\\n            f"{mode}: row {row}\'s PNG cell does not hold status_active"\n    for row in BMP_ROWS:\n        assert table.item(row, COMPRESSION).data(Qt.ItemDataRole.ForegroundRole) is None, \\\n            f"{mode}: a BMP cell was given a colour of its own"\n\n\n@pytest.mark.ui\n@pytest.mark.parametrize("mode,is_dark", MODES)\ndef test_the_mark_is_drawn(analyzer, mode, is_dark):\n    """Read back from the pixels. Setting a colour on a cell is not drawing it."""\n    dialog = analyzer(mode)\n    table = dialog.images_table\n    palette = get_theme_colors(is_dark=is_dark)\n    mark, text = QColor(palette["status_active"]), QColor(palette["text_primary"])\n    bmp_ground, bmp = _reach(table, BMP_ROWS[0], COMPRESSION)\n    for row in PNG_ROWS:\n        ground, png = _reach(table, row, COMPRESSION)\n        want = _far(mark, ground) / _far(text, bmp_ground)\n        as_plain_text = _far(text, ground) / _far(text, bmp_ground)\n        assert abs(want - as_plain_text) > 0.25, f"{mode}: the two inks are too alike for this test to tell them apart"\n        got = png / bmp\n        assert abs(got - want) < 0.12, (\n            f"{mode}: row {row}\'s PNG stands {got:.2f} as far from its ground as BMP does from its own. In "\n            f"the success text it stands {want:.2f} as far; at {as_plain_text:.2f} it is drawn in the "\n            f"table\'s text, which is what a sheet that colours every cell does")\n        beside_ground, beside = _reach(table, row, 0)\n        assert abs(beside / bmp - _far(text, beside_ground) / _far(text, bmp_ground)) < 0.12, \\\n            f"{mode}: the cell beside the mark in row {row} is not drawn in the table\'s text"\n\n\n@pytest.mark.ui\n@pytest.mark.parametrize("mode,is_dark", MODES)\ndef test_the_sheets_item_rule_sets_no_colour(analyzer, mode, is_dark):\n    sheet = analyzer(mode).styleSheet()\n    rules = re.findall(r"QTableWidget::item \\{([^}]*)\\}", sheet)\n    assert len(rules) == 1, f"{mode}: {len(rules)} plain item rules in the analyzer\'s sheet"\n    properties = [line.split(":")[0].strip() for line in rules[0].split(";") if ":" in line]\n    assert "color" not in properties, (\n        f"{mode}: the item rule sets a colour again ({properties}). A sheet wins over a cell\'s "\n        f"own colour, so the PNG mark would stop drawing.")\n    table_rule = re.search(r"QTableWidget \\{([^}]*)\\}", sheet)\n    assert table_rule and re.search(r"(?<![a-z-])color:\\s*" + re.escape(get_theme_colors(is_dark=is_dark)["text_primary"]),\n                                    table_rule.group(1)), \\\n        f"{mode}: the table no longer gives its cells the text colour the item rule gave them"\n\n\n@pytest.mark.ui\ndef test_the_mark_follows_the_mode(analyzer):\n    dialog = analyzer("dark")\n    table = dialog.images_table\n    dark, light = get_theme_colors(is_dark=True), get_theme_colors(is_dark=False)\n    assert dark["status_active"] != light["status_active"]\n    dialog.apply_theme_from_manager("light")\n    QApplication.processEvents()\n    for row in PNG_ROWS:\n        assert table.item(row, COMPRESSION).foreground().color().name() == QColor(light["status_active"]).name(), \\\n            "a theme applied again left the mark in the old mode\'s colour"\n    bmp_ground, bmp = _reach(table, BMP_ROWS[0], COMPRESSION)\n    ground, png = _reach(table, PNG_ROWS[0], COMPRESSION)\n    want = _far(QColor(light["status_active"]), ground) / _far(QColor(light["text_primary"]), bmp_ground)\n    assert abs(png / bmp - want) < 0.12, "after the switch the mark is not drawn in light\'s success text"\n\n\n@pytest.mark.parametrize("is_dark", [True, False])\ndef test_the_mark_can_be_read_on_both_row_grounds(is_dark):\n    palette = get_theme_colors(is_dark=is_dark)\n    for ground in ("list_bg", "list_alt_bg"):\n        ratio = _ratio(palette["status_active"], palette[ground])\n        assert ratio >= 4.5, f"status_active on {ground} is {ratio:.2f}:1, under 4.5"\n')
    if (tree.root / 'tests/test_workflow_actions.py').exists():
        raise Stop('tests/test_workflow_actions.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_workflow_actions.py', '"""Every action the workflows use is at a version built for the Node the runners have.\n\nRNV-RULINGS-2026-10-05, item 14. Ruled 2026-10-05: "Yes do it".\n\nWHAT WAS THERE. actions/checkout@v4, actions/setup-python@v5 and, where a\nworkflow keeps something from the run, actions/upload-artifact@v4. Each of\nthose declares `using: node20` in its own action.yml. GitHub took Node 20\noff its hosted runners on 2026-09-23. Since then an action that declares it\nis run on Node 24 instead, and the job carries a warning that names it.\n\nWHAT IS THERE NOW. The first version of each that declares node24: checkout\nv5, setup-python v6, upload-artifact v6. They are the versions the brand\nrepository moved its own workflows to on 2026-10-04.\n\nREAD, NOT ASSUMED. Each action\'s action.yml was read at both tags on\n2026-10-05. Every input these workflows pass is an input of the newer\nversion, with the same default and the same `required`. No input the older\nversion had is gone from the newer one.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every `uses:` in every workflow names an action in FLOOR, at that major\n   version or a later one. An action that is not in FLOOR is a new one: read\n   which Node it is built for, then add it.\n2. The reader is looking. It finds the steps of every workflow, in either\n   way YAML writes one, and it flags a version under the floor.\n\nWHAT IT CANNOT HOLD. That a workflow runs. Only a run on GitHub shows that.\n"""\nfrom __future__ import annotations\n\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nWORKFLOWS = ROOT / ".github" / "workflows"\n\n#: The lowest major version of each action that declares node24.\nFLOOR = {\n    "actions/checkout": 5,\n    "actions/setup-python": 6,\n    "actions/upload-artifact": 6,\n}\n\n#: Every workflow checks the repository out and sets Python up.\nEVERY_WORKFLOW_USES = ("actions/checkout", "actions/setup-python")\n\nUSES = re.compile(r"^\\s*(?:-\\s+)?uses:\\s*([^\\s#]+)")\nVERSION = re.compile(r"^v(\\d+)(?:\\.\\d+)*$")\n\n\ndef _uses(text: str) -> list:\n    """(line number, action, ref) for every step that uses an action."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        match = USES.match(line)\n        if match:\n            action, _, ref = match.group(1).partition("@")\n            found.append((number, action, ref))\n    return found\n\n\ndef _problems(name: str, text: str) -> list:\n    out = []\n    for number, action, ref in _uses(text):\n        where = f"{name}:{number}: {action}@{ref}"\n        if action not in FLOOR:\n            out.append(f"{where} is not an action this guard knows. Read which Node its "\n                       f"action.yml declares at that version, then add it to FLOOR.")\n            continue\n        version = VERSION.match(ref)\n        if not version:\n            out.append(f"{where} is pinned by something other than a version tag, which "\n                       f"this guard cannot compare.")\n        elif int(version.group(1)) < FLOOR[action]:\n            out.append(f"{where} is under v{FLOOR[action]}, the first version built for "\n                       f"Node 24.")\n    return out\n\n\ndef _workflows() -> dict:\n    return {path.name: path.read_text(encoding="utf-8")\n            for path in sorted(WORKFLOWS.glob("*.y*ml"))}\n\n\ndef test_every_action_is_at_a_version_built_for_node_24():\n    problems = [p for name, text in _workflows().items() for p in _problems(name, text)]\n    assert not problems, (\n        "GitHub\'s runners no longer have Node 20:\\n  " + "\\n  ".join(problems))\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds no step passes the test above."""\n    workflows = _workflows()\n    assert workflows, f"no workflow found under {WORKFLOWS}"\n    for name, text in workflows.items():\n        used = {action for _n, action, _ref in _uses(text)}\n        missing = [a for a in EVERY_WORKFLOW_USES if a not in used]\n        assert not missing, f"{name}: the reader finds no step that uses {missing}"\n\n    sample = ("    steps:\\n"\n              "      - uses: actions/checkout@v4\\n"\n              "      - name: Python\\n"\n              "        uses: actions/setup-python@v6  # a comment\\n"\n              "      - name: Something new\\n"\n              "        uses: someone/something@v1\\n"\n              "      - name: Pinned\\n"\n              "        uses: actions/upload-artifact@main\\n"\n              "      - run: echo uses: actions/checkout@v1\\n")\n    assert _uses(sample) == [(2, "actions/checkout", "v4"), (4, "actions/setup-python", "v6"),\n                             (6, "someone/something", "v1"), (8, "actions/upload-artifact", "main")], \\\n        "the reader does not find a step written as a list item, or under a name"\n    flagged = _problems("sample.yml", sample)\n    assert len(flagged) == 3, flagged\n    assert "under v5" in flagged[0] and "not an action this guard knows" in flagged[1] \\\n        and "other than a version tag" in flagged[2], flagged\n')
    if (tree.root / 'tests/test_readme_test_counts.py').exists():
        raise Stop('tests/test_readme_test_counts.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_readme_test_counts.py', '"""The README says how many tests there are in a way that stays true.\n\nRNV-RULINGS-2026-10-05, item 18. Ruled 2026-10-05: "Do B".\n\nWHAT WAS THERE. Exact totals, written once and kept in step by nothing. On\n2026-10-05 the README said 896 tests and pytest collected 1,163.\n\nWHAT IS THERE NOW. Every figure is a floor: "over N". N is the number of\ntest functions the suites define, rounded down to the hundred. A test added\nleaves it true, so there is nothing to keep in step. pytest collects more\nthan that number, because a parametrised function is written once and\ncollected once for each case.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every number of tests the README states is a floor. An exact count,\n   written as a sentence, as a badge or as a cell of the suites\' table, is\n   how the old ones went stale.\n2. Every floor is true. The suite it speaks of defines more test functions\n   than it says. Take tests away until one is not, and this names it: lower\n   the README\'s number.\n3. The reader is looking. It finds the README\'s floors, and it tells an\n   exact count from a floor in each of the three ways one is written.\n\nWHAT IT DOES NOT HOLD. The coverage figures beside the counts: a coverage\nfigure depends on the platform it was taken on.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nREADME = ROOT / "README.md"\n\n#: The unittest suite at the repository root.\nROOT_SUITE = "test_rnv_icon_builder.py"\n\n#: The README states this many floors. Fewer and the reader has gone blind,\n#: or the README has stopped saying.\nMIN_FLOORS = 4\n\nNUMBER = r"\\d{1,3}(?:,\\d{3})+|\\d+"\nSENTENCE = re.compile(rf"(?P<n>{NUMBER})\\s+(?:(?:unittest|pytest|passing|automated)\\s+)?tests\\b", re.I)\nBADGE = re.compile(r"\\btests-(?P<n>\\d+)(?P<plus>%2B)?", re.I)\nCELL = re.compile(rf"\\|\\s*\\**(?P<over>over\\s+)?(?P<n>{NUMBER})\\**\\s*(?=\\|)", re.I)\nOVER_BEFORE = re.compile(r"over\\s+\\**$", re.I)\nA_SUITE_ROW = re.compile(r"unittest|pytest|\\btests\\b|coverage", re.I)\n\n\ndef _claims(text: str) -> list:\n    """(line number, the number, whether it is a floor, which suites it\n    counts) for every number of tests the text states."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        seen = set()\n\n        def add(match, floor: bool) -> None:\n            if match.start("n") in seen:\n                return\n            seen.add(match.start("n"))\n            low = line.lower()\n            root = "unittest" in low or ROOT_SUITE.lower() in low\n            modern = "pytest" in low or "`tests/`" in low\n            suites = "root" if root and not modern else "pytest" if modern and not root else "all"\n            found.append((number, int(match.group("n").replace(",", "")), floor, suites))\n\n        for match in BADGE.finditer(line):\n            add(match, bool(match.group("plus")))\n        for match in SENTENCE.finditer(line):\n            add(match, bool(OVER_BEFORE.search(line[:match.start("n")])))\n        if line.lstrip().startswith("|") and A_SUITE_ROW.search(line):\n            for match in CELL.finditer(line):\n                add(match, bool(match.group("over")))\n    return found\n\n\ndef _defined_in(source: str, unittest_file: bool) -> int:\n    """How many test functions a file\'s text defines: a lower bound on what\n    is collected from it, since a function is collected at least once."""\n    tree = ast.parse(source)\n    count = 0\n    for node in tree.body:\n        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n            count += node.name.startswith("test_") and not unittest_file\n        elif isinstance(node, ast.ClassDef) and (unittest_file or node.name.startswith("Test")):\n            prefix = "test" if unittest_file else "test_"\n            count += sum(1 for member in node.body\n                         if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))\n                         and member.name.startswith(prefix))\n    return count\n\n\ndef _defined(path: pathlib.Path, unittest_file: bool) -> int:\n    return _defined_in(path.read_text(encoding="utf-8-sig"), unittest_file)\n\n\ndef _suites() -> dict:\n    root = _defined(ROOT / ROOT_SUITE, unittest_file=True)\n    modern = sum(_defined(path, unittest_file=False)\n                 for path in sorted((ROOT / "tests").glob("test_*.py")))\n    return {"root": root, "pytest": modern, "all": root + modern}\n\n\ndef test_every_number_of_tests_the_readme_states_is_a_floor():\n    exact = [f"README.md:{line}: {n:,}" for line, n, floor, _s in\n             _claims(README.read_text(encoding="utf-8")) if not floor]\n    assert not exact, (\n        "the README states an exact number of tests, which goes stale with the next "\n        "test:\\n  " + "\\n  ".join(exact) + "\\nSay it as a floor: over N.")\n\n\ndef test_every_floor_is_true():\n    defined = _suites()\n    names = {"root": ROOT_SUITE, "pytest": "tests/", "all": "the two suites together"}\n    false = [f"README.md:{line}: over {n:,}, and {names[suites]} defines {defined[suites]:,}"\n             for line, n, floor, suites in _claims(README.read_text(encoding="utf-8"))\n             if floor and not n < defined[suites]]\n    assert not false, (\n        "the README promises more tests than the suites define:\\n  " + "\\n  ".join(false)\n        + "\\nLower the README\'s number.")\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds nothing passes both tests above."""\n    floors = [c for c in _claims(README.read_text(encoding="utf-8")) if c[2]]\n    assert len(floors) >= MIN_FLOORS, f"the reader finds {len(floors)} floors in the README, not {MIN_FLOORS}"\n    assert {c[3] for c in floors} == {"root", "pytest", "all"}, \\\n        f"the README\'s floors speak of {sorted({c[3] for c in floors})}, not of each suite and of both"\n    defined = _suites()\n    assert defined["root"] > 100 and defined["pytest"] > 100, f"the count of test functions has gone blind: {defined}"\n\n    sample = ("![Tests](https://img.shields.io/badge/tests-786%20passing-brightgreen)\\n"\n              "![Tests](https://img.shields.io/badge/tests-1000%2B%20passing-brightgreen)\\n"\n              "ships with **786 tests across two suites**, and with **over 1,000 tests** too\\n"\n              f"| `{ROOT_SUITE}` (unittest) | 398 | Frozen |\\n"\n              "| `tests/` (pytest) | over 600 | Modern, with 27 snapshots |\\n"\n              "| Ctrl+T | 12 | a row of some other table |\\n"\n              "Python 3.13, 2 suites, tests/test_x.py\\n")\n    assert _claims(sample) == [\n        (1, 786, False, "all"), (2, 1000, True, "all"),\n        (3, 786, False, "all"), (3, 1000, True, "all"),\n        (4, 398, False, "root"),\n        (5, 600, True, "pytest"),\n    ], _claims(sample)\n')


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
    def units(src):
        """Every function, method and assignment a source defines, each under its
        name -> its text. A comment is not part of it; a docstring is."""
        out = dict()
        for node in ast.parse(src).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[node.name + "()"] = ast.unparse(node)
            elif isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out[node.name + "." + sub.name + "()"] = ast.unparse(sub)
                    elif isinstance(sub, (ast.Assign, ast.AnnAssign)) and sub.value is not None:
                        t = sub.targets[0] if isinstance(sub, ast.Assign) else sub.target
                        if isinstance(t, ast.Name):
                            out[node.name + "." + t.id] = ast.unparse(sub.value)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                t = node.targets[0] if isinstance(node, ast.Assign) else node.target
                if isinstance(t, ast.Name):
                    out[t.id] = ast.unparse(node.value)
        return out

    def code(src):
        """units() of a source with every docstring taken out: what the code
        does, not what it says of itself."""
        module = ast.parse(src)
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                        and isinstance(first.value.value, str):
                    node.body = node.body[1:] or [ast.Pass()]
        return units(ast.unparse(module))

    def moved(was_src, now_src):
        """(what arrives, what goes, what changes) between two sources, by name."""
        was, now = units(was_src), units(now_src)
        return (sorted(set(now) - set(was)), sorted(set(was) - set(now)),
                sorted(k for k in set(was) & set(now) if was[k] != now[k]))

    def as_written(rel):
        """A file as this round leaves it: from the tree if the round holds it, else from disk."""
        if rel in tree.files:
            return tree.files[rel]
        return (tree.root / rel).read_text(encoding="utf-8-sig", errors="replace")

    def app_sources():
        """(path, text) of the application's Python as this round leaves it: no
        tests, no runner, no delivery script."""
        skip = ("tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__",
                "venv", "env", "htmlcov", "node_modules")
        paths = set(p.relative_to(tree.root).as_posix() for p in tree.root.rglob("*.py"))
        paths |= set(r for r in tree.files if r.endswith(".py"))
        for rel in sorted(paths - tree.deleted):
            parts = rel.split("/")
            if any(q in skip or q.startswith(".") for q in parts[:-1]):
                continue
            if len(parts) == 1 and parts[0].startswith(("test_", "conftest", "run_tests")):
                continue
            text = as_written(rel)
            if len(parts) == 1 and "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
                continue
            yield rel, text

    def names_in(text):
        """Every name, attribute and imported name a source reaches for, and
        every string it writes out whole."""
        found = set()
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Name):
                found.add(node.id)
            elif isinstance(node, ast.Attribute):
                found.add(node.attr)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                found.update(a.name for a in node.names)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                found.add(node.value)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                found.add(node.name)
        return found

    def tests_in(src):
        return [n.name for n in ast.walk(ast.parse(src))
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test")]

    def check_moves(table):
        """Each file moves by what the table lists for it, and by nothing else."""
        for rel, arrives, goes, changes in table:
            got = moved(_original(tree, rel), tree.read(rel))
            assert got == (arrives, goes, changes), (
                f"{rel} moved by other than what this round lists: arrives {got[0]}, goes {got[1]}, "
                f"changes {got[2]}")
    ANALYZER, NAMED, COLORS = "ui/ico_analyzer.py", "tests/test_named_and_used.py", "ui/colors.py"
    MOVES = [('tests/test_named_and_used.py', [], [], ['DATA']), ('ui/ico_analyzer.py', ['IcoAnalyzerDialog._mark_png_rows()'], [], ['IcoAnalyzerDialog._apply_theme()', 'IcoAnalyzerDialog._populate_table()'])]
    check_moves(MOVES)
    src = tree.read(ANALYZER)

    # ---- item 1: Qt's dark green is written nowhere in the application, and the mark is the palette's
    swept = 0
    for rel, text in app_sources():
        swept += 1
        assert "darkGreen" not in names_in(text), f"{rel} sets Qt's dark green"
    assert swept >= 37, f"the sweep read {swept} files"
    mark = _function(src, "_mark_png_rows", cls="IcoAnalyzerDialog")
    read = [n.slice.value for n in ast.walk(mark)
            if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)]
    assert read == ["status_active"], f"_mark_png_rows() reads {read} from the palette"
    callers = sorted(name for name, text in code(src).items()
                     if "self._mark_png_rows()" in text and not name.endswith("._mark_png_rows()"))
    assert callers == ["IcoAnalyzerDialog._apply_theme()", "IcoAnalyzerDialog._populate_table()"], \
        f"the mark is made by {callers}: it has to be made when the table is filled and when the theme is applied"

    # ---- both palettes hold the mark, each its own
    palettes = dict()
    for node in ast.parse(as_written(COLORS)).body:
        target = node.target if isinstance(node, ast.AnnAssign) else None
        if getattr(target, "id", None) in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS"):
            palettes[target.id] = _entries(node.value)
    assert sorted(palettes) == ["DARK_THEME_COLORS", "LIGHT_THEME_COLORS"], sorted(palettes)
    marks = [palettes[name].get("status_active") for name in sorted(palettes)]
    assert all(marks) and marks[0] != marks[1], "the two palettes do not each hold a status_active of their own"

    # ---- the sheet: the plain item rule sets no colour, and the table's own rule still gives the text one
    theme = _function(src, "_apply_theme", cls="IcoAnalyzerDialog")
    sheets = _calls(theme, "setStyleSheet")
    assert len(sheets) == 1, f"_apply_theme() sets {len(sheets)} sheets"
    sheet = "\x00".join(_sheet_parts(sheets[0]))
    rule = re.findall(r"QTableWidget::item \{([^}]*)\}", sheet)
    assert len(rule) == 1, f"{len(rule)} plain item rules in the analyzer's sheet"
    properties = [line.split(":")[0].strip() for line in rule[0].split(";") if ":" in line]
    assert properties == ["padding", "background-color"], (
        f"the item rule sets {properties}: with a colour there the sheet wins over a cell's own, and the "
        f"mark is not drawn")
    table = re.findall(r"QTableWidget \{([^}]*)\}", sheet)
    assert len(table) == 1 and re.search(r"(?<![a-z-])color:", table[0]), \
        "the table's own rule gives its cells no text colour to fall back on"

    # ---- the guard that held the dark green as set and never drawn holds one entry fewer
    def table_keys(text):
        node = next(n for n in ast.parse(text).body
                    if isinstance(n, (ast.Assign, ast.AnnAssign))
                    and getattr(n.targets[0] if isinstance(n, ast.Assign) else n.target, "id", None) == "DATA")
        return [ast.literal_eval(k) for k in node.value.keys if k is not None]
    was_keys, now_keys = table_keys(_original(tree, NAMED)), table_keys(tree.read(NAMED))
    assert [k for k in was_keys if k not in now_keys] == [("ui/ico_analyzer.py", "Qt.GlobalColor.darkGreen")] \
        and [k for k in now_keys if k not in was_keys] == [], f"{NAMED}: its table moved by other than the dark green"
    assert tests_in(tree.read(GUARD)) == ['test_a_png_cell_holds_the_modes_success_text', 'test_the_mark_is_drawn', 'test_the_sheets_item_rule_sets_no_colour', 'test_the_mark_follows_the_mode', 'test_the_mark_can_be_read_on_both_row_grounds'], f"{GUARD}: its tests are {tests_in(tree.read(GUARD))}"

    # ================= item 14: the workflows' actions, each at the first version built for Node 24
    ACTIONS = (('actions/checkout', 'v4', 'v5'), ('actions/setup-python', 'v5', 'v6'), ('actions/upload-artifact', 'v4', 'v6'))
    WORKFLOW_STEPS = (('.github/workflows/tests-linux.yml', (('actions/checkout', 1), ('actions/setup-python', 1), ('actions/upload-artifact', 1))), ('.github/workflows/tests-windows.yml', (('actions/checkout', 1), ('actions/setup-python', 1), ('actions/upload-artifact', 1))))
    NOTE_OPENS = '# RNV-RULINGS-2026-10-05, item 14. Each action below is at the first version'
    here = sorted(p.relative_to(tree.root).as_posix()
                  for p in (tree.root / ".github" / "workflows").glob("*.y*ml"))
    assert here == [wf for wf, _steps in WORKFLOW_STEPS], f"the workflows here are {here}"
    ag = dict(__name__="workflow_actions_guard", __file__=str(tree.root / ACTIONS_GUARD))
    exec(compile(tree.read(ACTIONS_GUARD), ACTIONS_GUARD, "exec"), ag)
    assert ag["FLOOR"] == dict((action, int(new[1:])) for action, _old, new in ACTIONS), \
        f"{ACTIONS_GUARD}: its floor is {ag['FLOOR']}"
    assert tests_in(tree.read(ACTIONS_GUARD)) == ['test_every_action_is_at_a_version_built_for_node_24', 'test_the_reader_is_looking'], f"{ACTIONS_GUARD}: its tests are {tests_in(tree.read(ACTIONS_GUARD))}"
    for wf, steps in WORKFLOW_STEPS:
        was, now = _original(tree, wf).splitlines(), tree.read(wf).splitlines()
        opens = [n for n, line in enumerate(now) if line == NOTE_OPENS]
        assert len(opens) == 1, f"{wf}: the note is there {len(opens)} times"
        ends = opens[0]
        while now[ends].startswith("#"):
            ends += 1
        assert now[ends] == "jobs:" and ends - opens[0] == 5, f"{wf}: the note is not the five lines above jobs:"
        short = [action.split("/")[1] + " " + new for action, _old, new in ACTIONS if dict(steps).get(action)]
        said = (", ".join(short[:-1]) + " and " + short[-1]) if len(short) > 1 else short[0]
        assert now[opens[0] + 1] == f"# built for Node 24: {said}.", \
            f"{wf}: the note names {now[opens[0] + 1]!r}, and the file's steps are {said}"
        rest = now[:opens[0]] + now[ends:]
        assert len(rest) == len(was), f"{wf}: lines came or went beyond the note"
        counted = dict()
        for before, after in zip(was, rest):
            if before == after:
                continue
            hit = [action for action, old, new in ACTIONS
                   if before.strip() in (f"uses: {action}@{old}", f"- uses: {action}@{old}")
                   and after == before.replace(f"{action}@{old}", f"{action}@{new}")]
            assert len(hit) == 1, (
                f"{wf}: a line moved that is not one of the three actions going to its new version: "
                f"{before.strip()!r} -> {after.strip()!r}")
            counted[hit[0]] = counted.get(hit[0], 0) + 1
        assert sorted(counted.items()) == sorted(steps), f"{wf}: the steps moved are {sorted(counted.items())}"
        name = wf.rsplit("/", 1)[1]
        flagged = ag["_problems"](name, "\n".join(was))
        assert len(flagged) == sum(n for _a, n in steps) and all("is under v" in p for p in flagged), \
            f"{wf}: as it is here, the guard names {flagged}"
        still = ag["_problems"](name, "\n".join(now))
        assert still == [], f"{wf}: the guard would still name {still}"

    # ================= item 18: every count the README states is a floor, and true of this checkout as it will be
    FLOORS = [(400, 'root'), (600, 'pytest'), (1100, 'all'), (1100, 'all')]
    WAS_EXACT = 5
    rg = dict(__name__="readme_counts_guard", __file__=str(tree.root / README_GUARD))
    exec(compile(tree.read(README_GUARD), README_GUARD, "exec"), rg)
    assert rg["ROOT_SUITE"] == ROOT_SUITE and rg["MIN_FLOORS"] == len(FLOORS), \
        f"{README_GUARD}: it is set for {rg['ROOT_SUITE']} and {rg['MIN_FLOORS']} floors"
    assert tests_in(tree.read(README_GUARD)) == ['test_every_number_of_tests_the_readme_states_is_a_floor', 'test_every_floor_is_true', 'test_the_reader_is_looking'], f"{README_GUARD}: its tests are {tests_in(tree.read(README_GUARD))}"
    was_claims, now_claims = rg["_claims"](_original(tree, "README.md")), rg["_claims"](tree.read("README.md"))
    exact = [f"README.md:{line}: {n:,}" for line, n, floor, _s in was_claims if not floor]
    assert len(exact) == WAS_EXACT and len(was_claims) == WAS_EXACT, \
        f"README.md states {len(exact)} exact counts here, of {len(was_claims)} counts: {exact}"
    left = [f"README.md:{line}: {n:,}" for line, n, floor, _s in now_claims if not floor]
    assert not left, f"README.md would still state an exact count: {left}"
    assert sorted((n, s) for _l, n, _f, s in now_claims) == FLOORS, \
        f"README.md would state {sorted((n, s) for _l, n, _f, s in now_claims)}"
    modern = sorted((set(p.relative_to(tree.root).as_posix() for p in (tree.root / "tests").glob("test_*.py"))
                     | set(r for r in tree.files if r.startswith("tests/test_") and r.count("/") == 1
                           and r.endswith(".py"))) - tree.deleted)
    defined = dict(root=rg["_defined_in"](as_written(ROOT_SUITE), True),
                   pytest=sum(rg["_defined_in"](as_written(rel), False) for rel in modern))
    defined["all"] = defined["root"] + defined["pytest"]
    assert len(modern) >= 39 and defined["root"] > 100, f"the count of tests has gone blind: {len(modern)} files, {defined}"
    for number, suites in FLOORS:
        assert number < defined[suites], \
            f"README.md would say over {number:,}, and here {suites} defines {defined[suites]:,}"
    for wf, _steps in WORKFLOW_STEPS[:1]:
        assert SENTINEL in tree.read(wf) and SENTINEL in tree.read(ACTIONS_GUARD) and SENTINEL in tree.read(README_GUARD), \
            "the sentinel is not in the workflow and the two guards"
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
