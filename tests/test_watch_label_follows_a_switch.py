"""
tests/test_watch_label_follows_a_switch.py
==========================================
RNV-WATCH-LABEL, 2026-09-28. The Settings dialog's Watching label is drawn
in its own mode's status_active, and follows a switch.

RNV-STATUS-FAMILY moved the label off STATUS_ACTIVE_COLOR, a constant, onto
the palette's status_active key -- read with get_theme_colors() and no mode,
which is the default palette: dark's. A dialog in light drew dark's value,
#ad85a3 on #f5f5f5, 2.89:1 -- under the 4.5:1 text floor the family was
walked to clear, and under 3:1; light's own, #825d79, reads 5.08:1 there.
And the label's sheet was set once, when watching started, so a switch
with the dialog open kept the mode it was set in.

tests/test_status_register.py holds the palettes; this holds the label as
the dialog draws it. Driven through the main window's own opener, theme
button and watch callbacks: _open_settings(), cycle_theme(),
_on_watch_started() and _on_watch_stopped(). The fixture's main window has
no image mode (it skips loading the image resources), so image is reached
the way the main window hands it on: apply_theme_from_manager("image").
"""
from __future__ import annotations

import collections

import pytest
from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from ui.colors import get_theme_colors

FOLDER = "C:/Users/you/Icons/incoming"
TEXT_FLOOR = 4.5


def _ink(label) -> str:
    """The colour the label's text is drawn in, as its sheet resolves."""
    label.ensurePolished()
    return label.palette().color(QPalette.ColorRole.WindowText).name()


def _active(mode: str) -> str:
    """status_active from the palette the dialog is painted with in `mode`:
    dark's in dark and image, light's in light."""
    return get_theme_colors(is_dark=mode in ("dark", "image"))["status_active"].lower()


def _lum(c: QColor) -> float:
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c.red()) + 0.7152 * ch(c.green()) + 0.0722 * ch(c.blue())


def _contrast(a: QColor, b: QColor) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _ground(dlg, label) -> QColor:
    """The ground under the label as the dialog draws it: the commonest pixel
    of the dialog's own grab over the label's rectangle. Not label.grab(),
    which fills with the label's palette -- #000000 in dark, where the
    dialog draws #1a1a1a."""
    img = dlg.grab(QRect(label.mapTo(dlg, QPoint(0, 0)), label.size())).toImage()
    counts = collections.Counter(img.pixelColor(x, y).name()
                                 for y in range(img.height()) for x in range(img.width()))
    return QColor(counts.most_common(1)[0][0])


def _settings(app, mode: str):
    """Settings, opened with the main window's own opener in `mode`, watching."""
    for _ in range(3):
        if app.theme_manager.current_theme == mode:
            break
        app.cycle_theme()
    assert app.theme_manager.current_theme == mode
    app._open_settings()
    QApplication.processEvents()
    app._on_watch_started(FOLDER)
    QApplication.processEvents()
    dlg = app.settings_dialog
    assert dlg is not None and dlg.watch_status_label.text().endswith(FOLDER)
    label = dlg.watch_status_label
    page = next(dlg.tabs.widget(i) for i in range(dlg.tabs.count())
                if dlg.tabs.widget(i).isAncestorOf(label))
    dlg.tabs.setCurrentWidget(page)                           # the tab the label is on
    QApplication.processEvents()
    return dlg


class TestTheWatchingLabelFollowsTheDialogsMode:

    def test_a_dialog_opened_in_light_draws_light_s_value(self, app):
        dlg = _settings(app, "light")
        assert _ink(dlg.watch_status_label) == _active("light"), (
            "a dialog in light draws another mode's status_active")
        dlg.close()

    def test_a_switch_with_the_dialog_open_restyles_the_label(self, app):
        dlg = _settings(app, "dark")
        label = dlg.watch_status_label
        assert _ink(label) == _active("dark")
        modes = []
        for _ in range(2):                                   # dark -> light -> dark
            app.cycle_theme()
            QApplication.processEvents()
            mode = app.theme_manager.current_theme
            modes.append(mode)
            assert _ink(label) == _active(mode), (mode, _ink(label))
        assert modes == ["light", "dark"], modes
        dlg.apply_theme_from_manager("image")                 # as the main window hands image on
        assert _ink(label) == _active("image")
        dlg.close()

    @pytest.mark.parametrize("mode", ["dark", "light"])
    def test_the_label_clears_the_text_floor_on_the_ground_it_is_drawn_on(self, app, mode):
        dlg = _settings(app, "dark" if mode == "light" else "light")
        app.cycle_theme()                                     # arrive in `mode` by a switch
        QApplication.processEvents()
        assert app.theme_manager.current_theme == mode
        label = dlg.watch_status_label
        assert label.isVisible(), "the label is not on screen"
        ground = _ground(dlg, label)
        ratio = _contrast(QColor(_ink(label)), ground)
        assert ratio >= TEXT_FLOOR, f"{mode}: {_ink(label)} on {ground.name()} = {ratio:.2f}"
        assert _ink(label) == _active(mode), (mode, _ink(label))
        dlg.close()

    def test_stopping_hands_the_label_back_to_the_dialog_s_sheet(self, app):
        dlg = _settings(app, "dark")
        app.cycle_theme()
        app._on_watch_stopped()
        QApplication.processEvents()
        label = dlg.watch_status_label
        assert label.styleSheet() == "" and not dlg._is_watching
        app.cycle_theme()                                     # no longer watching: left alone
        QApplication.processEvents()
        assert label.styleSheet() == "", "a switch styled a label that is not watching"
        dlg.close()
