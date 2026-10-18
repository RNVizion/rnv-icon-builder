"""A PNG row in the ICO analyzer is marked, and the mark is drawn.

RNV-RULINGS-2026-10-05, item 1. Ruled 2026-10-05: "Yes".

WHAT WAS THERE. The analyzer set Qt's dark green on a PNG row's Compression
cell, and it was never drawn. The dialog's sheet colored every cell
(`QTableWidget::item { color: ... }`), and a sheet wins over a cell's own
color, so PNG was drawn like BMP in every mode. Shown on 2026-10-04 with a
magenta control: the cell set to magenta moved no pixel.

WHAT IS THERE NOW. The item rule sets no color, so a cell's own color is
drawn; a cell that has none takes the table's, which is the color the rule
gave it. And the mark is the palette's `status_active`, which holds each
mode's success text.

WHAT THIS GUARD HOLDS.

1. A PNG cell holds the mode's success text. A BMP cell holds no color of
   its own.
2. The mark is DRAWN. Read back from the table's own pixels, as a
   comparison: how far a PNG cell's text stands from its ground, against how
   far a BMP cell's does. Text is drawn with soft edges, more or less so
   from one machine to the next, and the comparison does not care how soft.
   This is the test the old line would have failed.
3. The sheet's item rule sets no color. That is why the mark draws, and it
   is the line a tidy-up would put back.
4. The mark follows the mode: a theme applied again marks again.
5. The mark can be read where it sits: 4.5:1 or better on both of the
   table's row grounds, in both palettes.
"""
from __future__ import annotations

import re

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication

from utils.colors import get_theme_colors

INFO = {
    "file_name": "sample.ico", "file_size": 4096, "image_count": 3, "has_png": True, "has_bmp": True,
    "sizes": ["256x256", "48x48", "16x16"],
    "images": [
        {"width": 256, "height": 256, "compression": "PNG", "bits_per_pixel": 32, "bytes": 3072},
        {"width": 48, "height": 48, "compression": "BMP", "bits_per_pixel": 32, "bytes": 768},
        {"width": 16, "height": 16, "compression": "PNG", "bits_per_pixel": 32, "bytes": 256},
    ],
}
PNG_ROWS, BMP_ROWS, COMPRESSION = (0, 2), (1,), 1
MODES = (("dark", True), ("light", False), ("image", True))


def _lum(color: str) -> float:
    c = QColor(color)
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(c.red()) + 0.7152 * lin(c.green()) + 0.0722 * lin(c.blue())


def _ratio(a: str, b: str) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _far(a: QColor, b: QColor) -> int:
    return abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue())


def _reach(table, row: int, column: int) -> tuple:
    """(the cell's ground, how far its text stands from that ground): the
    distance of the pixel furthest from the ground."""
    image = table.viewport().grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)
    rect = table.visualItemRect(table.item(row, column))
    ground = image.pixelColor(rect.left() + 2, rect.top() + 2)
    far = max(_far(image.pixelColor(x, y), ground)
              for y in range(rect.top() + 2, rect.bottom() - 1)
              for x in range(rect.left() + 2, rect.right() - 1))
    assert far > 60, f"no text was found in cell ({row}, {column})"
    return ground, far


@pytest.fixture
def analyzer(qapp, qtbot):
    from ui.ico_analyzer import IcoAnalyzerDialog
    qapp.setStyle("Fusion")                 # the style the application runs in
    kept = []                               # a dialog nothing holds is deleted, and its table with it

    def build(mode: str):
        dialog = IcoAnalyzerDialog(parent=None)
        kept.append(dialog)
        qtbot.addWidget(dialog)
        dialog.apply_theme_from_manager(mode)
        dialog._display_info(INFO)
        dialog.resize(700, 520)
        dialog.show()
        table = dialog.images_table
        table.clearSelection()
        table.setCurrentCell(-1, -1)
        table.clearFocus()
        QApplication.processEvents()
        return dialog
    return build


@pytest.mark.ui
@pytest.mark.parametrize("mode,is_dark", MODES)
def test_a_png_cell_holds_the_modes_success_text(analyzer, mode, is_dark):
    table = analyzer(mode).images_table
    palette = get_theme_colors(is_dark=is_dark)
    for row in PNG_ROWS:
        item = table.item(row, COMPRESSION)
        assert item.text() == "PNG"
        assert item.foreground().color().name() == QColor(palette["status_active"]).name(), \
            f"{mode}: row {row}'s PNG cell does not hold status_active"
    for row in BMP_ROWS:
        assert table.item(row, COMPRESSION).data(Qt.ItemDataRole.ForegroundRole) is None, \
            f"{mode}: a BMP cell was given a color of its own"


@pytest.mark.ui
@pytest.mark.parametrize("mode,is_dark", MODES)
def test_the_mark_is_drawn(analyzer, mode, is_dark):
    """Read back from the pixels. Setting a color on a cell is not drawing it."""
    dialog = analyzer(mode)
    table = dialog.images_table
    palette = get_theme_colors(is_dark=is_dark)
    mark, text = QColor(palette["status_active"]), QColor(palette["text_primary"])
    bmp_ground, bmp = _reach(table, BMP_ROWS[0], COMPRESSION)
    for row in PNG_ROWS:
        ground, png = _reach(table, row, COMPRESSION)
        want = _far(mark, ground) / _far(text, bmp_ground)
        as_plain_text = _far(text, ground) / _far(text, bmp_ground)
        assert abs(want - as_plain_text) > 0.25, f"{mode}: the two inks are too alike for this test to tell them apart"
        got = png / bmp
        assert abs(got - want) < 0.12, (
            f"{mode}: row {row}'s PNG stands {got:.2f} as far from its ground as BMP does from its own. In "
            f"the success text it stands {want:.2f} as far; at {as_plain_text:.2f} it is drawn in the "
            f"table's text, which is what a sheet that colors every cell does")
        beside_ground, beside = _reach(table, row, 0)
        assert abs(beside / bmp - _far(text, beside_ground) / _far(text, bmp_ground)) < 0.12, \
            f"{mode}: the cell beside the mark in row {row} is not drawn in the table's text"


@pytest.mark.ui
@pytest.mark.parametrize("mode,is_dark", MODES)
def test_the_sheets_item_rule_sets_no_color(analyzer, mode, is_dark):
    sheet = analyzer(mode).styleSheet()
    rules = re.findall(r"QTableWidget::item \{([^}]*)\}", sheet)
    assert len(rules) == 1, f"{mode}: {len(rules)} plain item rules in the analyzer's sheet"
    properties = [line.split(":")[0].strip() for line in rules[0].split(";") if ":" in line]
    assert "color" not in properties, (
        f"{mode}: the item rule sets a color again ({properties}). A sheet wins over a cell's "
        f"own color, so the PNG mark would stop drawing.")
    table_rule = re.search(r"QTableWidget \{([^}]*)\}", sheet)
    assert table_rule and re.search(r"(?<![a-z-])color:\s*" + re.escape(get_theme_colors(is_dark=is_dark)["text_primary"]),
                                    table_rule.group(1)), \
        f"{mode}: the table no longer gives its cells the text color the item rule gave them"


@pytest.mark.ui
def test_the_mark_follows_the_mode(analyzer):
    dialog = analyzer("dark")
    table = dialog.images_table
    dark, light = get_theme_colors(is_dark=True), get_theme_colors(is_dark=False)
    assert dark["status_active"] != light["status_active"]
    dialog.apply_theme_from_manager("light")
    QApplication.processEvents()
    for row in PNG_ROWS:
        assert table.item(row, COMPRESSION).foreground().color().name() == QColor(light["status_active"]).name(), \
            "a theme applied again left the mark in the old mode's color"
    bmp_ground, bmp = _reach(table, BMP_ROWS[0], COMPRESSION)
    ground, png = _reach(table, PNG_ROWS[0], COMPRESSION)
    want = _far(QColor(light["status_active"]), ground) / _far(QColor(light["text_primary"]), bmp_ground)
    assert abs(png / bmp - want) < 0.12, "after the switch the mark is not drawn in light's success text"


@pytest.mark.parametrize("is_dark", [True, False])
def test_the_mark_can_be_read_on_both_row_grounds(is_dark):
    palette = get_theme_colors(is_dark=is_dark)
    for ground in ("list_bg", "list_alt_bg"):
        ratio = _ratio(palette["status_active"], palette[ground])
        assert ratio >= 4.5, f"status_active on {ground} is {ratio:.2f}:1, under 4.5"
