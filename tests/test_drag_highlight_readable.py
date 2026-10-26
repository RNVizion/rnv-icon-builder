"""The drop zone's text can be read while files are dragged over the window.

#99 A, ruled 25 October 2026: fix the display faults, rendered first.

THE FAULT. Dragging files or a folder over the window lights the drop zone:
a dashed accent edge and a gold tint. The tint is translucent, so the ground
the text sits on is the tint over whatever is under the label: the black
window in dark mode, the light window in light mode, the background image in
Image mode. The text took `text_on_accent`, the ink for text on the SOLID
accent: black on the dark tint (1.39:1) and white on the light one (1.26:1).
In Image mode the tint lay over the picture itself.

WHAT THIS HOLDS. In each of the three modes, a real drag enters the window
and the drop zone's sheet is read as Qt was given it. Its text color against
its ground clears the app's 4.5 floor for text. A translucent ground is
measured over what is under it: the window's own ground in dark and light;
in Image mode the picture, which can be any color, so the ground is measured
over black and over white, the two ends of what a picture can show, and the
text must lie on one side of both. The highlight must still be a highlight:
its edge is the mode's accent.
"""
from __future__ import annotations

import re

import pytest
from PyQt6.QtCore import QMimeData, QPoint, Qt, QUrl
from PyQt6.QtGui import QColor, QDragEnterEvent, QPixmap

from utils.colors import (TRUE_BLACK, WHITE, contrast_ratio, get_theme_colors,
                          relative_luminance)

TEXT_FLOOR = 4.5
MODES = ("dark", "light", "image")
DECL = re.compile(r"(?<![-\w])([a-z-]+)\s*:\s*([^;]+);")


def _enter_mode(window, mode: str) -> None:
    """Put the main window in a mode, as the theme button leaves it."""
    tm = window.theme_manager
    if mode == "image":
        # The fixture skips the real background; any picture will do, since
        # the measurement below holds for every color a picture can show.
        tm.image_mode_available = True
        tm.background_pixmap = QPixmap(16, 16)
        tm.background_pixmap.fill(QColor(WHITE))
    assert tm.set_theme(mode), f"the theme manager would not take {mode!r}"
    window.apply_theme()


def _drag_folder_over(window, folder: str) -> None:
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(folder)])
    window.dragEnterEvent(QDragEnterEvent(
        QPoint(10, 10), Qt.DropAction.CopyAction, mime,
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))


def _sheet(label) -> dict[str, str]:
    """The drop zone's declarations, as written in its sheet."""
    return {k.lower(): v.strip() for k, v in DECL.findall(label.styleSheet())}


def _over(top: QColor, under: str) -> str:
    """A translucent color laid over an opaque one, as #rrggbb."""
    below = QColor(under)
    a = top.alpha() / 255
    return QColor(*(round(a * t + (1 - a) * u) for t, u in (
        (top.red(), below.red()), (top.green(), below.green()), (top.blue(), below.blue())))).name()


def _grounds(window, mode: str, ground: str) -> list[str]:
    """Every opaque ground the drop zone's text can sit on."""
    color = QColor(ground)
    assert color.isValid(), f"{mode}: the drop zone's ground {ground!r} is not a color"
    if color.alpha() == 255:
        return [color.name()]
    if mode == "image":
        return [_over(color, TRUE_BLACK), _over(color, WHITE)]
    return [_over(color, window.theme_manager.get_current_theme()['window_bg'])]


@pytest.mark.application
@pytest.mark.parametrize("mode", MODES)
def test_the_drag_highlight_text_clears_the_floor(app, tmp_path, mode):
    app.resize(1280, 800)
    _enter_mode(app, mode)
    _drag_folder_over(app, str(tmp_path))
    decl = _sheet(app.drop_label)
    palette = get_theme_colors(is_dark=mode != "light", is_image_mode=mode == "image")

    assert palette['border_accent'].lower() in decl.get("border", "").lower(), (
        f"{mode}: the drag no longer lights the drop zone's edge: {decl.get('border')!r}")
    text = QColor(decl["color"]).name()
    grounds = _grounds(app, mode, decl["background-color"])
    ratios = [contrast_ratio(text, g) for g in grounds]
    sides = {relative_luminance(g) > relative_luminance(text) for g in grounds}
    assert len(sides) == 1, (
        f"{mode}: the text {text} lies between the grounds {grounds}: somewhere in between it vanishes")
    assert min(ratios) >= TEXT_FLOOR, (
        f"{mode}: the drop zone's text {text} on {grounds} reads "
        f"{', '.join(f'{r:.2f}' for r in ratios)}:1 while a file is dragged over it, "
        f"under the {TEXT_FLOOR} floor for text")
