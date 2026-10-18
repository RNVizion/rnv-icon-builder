"""Every color value the tests need that is not the application's color.

RNV-COLOR-SYNC, #53 A (2026-10-17). The application's own colors and the
brand's are named in utils/colors.py, which brand_map.json names, and a test
reads them from there. Every other color value a test or the root suite
writes is named here, once, with why: samples given to a helper or to the
color math (EXAMPLE_), what a file, a parser or a sweep's probe holds
(DATA_), values the application no longer uses (RETIRED_), a value the brand
publishes that this application does not draw (REGISTER_), and values written
wrongly on purpose (INVALID_). tests/test_color_values.py holds this file: no
color value is written anywhere else in tests/ or in test_rnv_icon_builder.py,
and every name here says what kind it is, says why, and is used.

Tests import from here by name (`from tests.color_values import ...`);
tests/test_colors_in_sync.py loads it by path.

RNV-COLLAPSE-GUARD
This file quotes the retired card stray, RETIRED_DARK_STRAY_GRAY, in order to
forbid it, so the source sweep in tests/test_collapse_252525.py skips it.

RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN
This file names retired values on purpose, the retired app gold among them,
so a tool that rewrites color values must leave it alone.
"""

# ------------------------------------------------------------------ examples

EXAMPLE_GROUND_WHITE = "#ffffff"
"""A light ground given to contrast_ink(), swatch_edge() and the contrast
math: one end of the 21:1 range. A sample, not WHITE: it must not follow a
brand move."""

EXAMPLE_GROUND_BLACK = "#000000"
"""A dark ground given to contrast_ink(), swatch_edge() and the contrast
math: the other end of the 21:1 range. A sample, not TRUE_BLACK."""

EXAMPLE_GROUND_GREEN = "#00ff00"
"""Pure green, the saturated ground the old (r + g + b) / 3 rule got wrong:
a light ground the mean called dark. Also the hex half of the hex-or-triple
check."""

EXAMPLE_GROUND_GREEN_SHORT = "#0f0"
"""The same green in three digits. The spelling is the point: the test shows
the ink rule expands it to EXAMPLE_GROUND_GREEN."""

EXAMPLE_GROUND_YELLOW = "#ffff00"
"""A saturated light ground on which the two old call sites disagreed."""

EXAMPLE_GROUND_TEAL = "#20b0b0"
"""A mid-luminance saturated ground, for the ink/edge agreement check and the
sample shared with the color picker's identical block."""

EXAMPLE_GROUND_OLIVE = "#9a9a30"
"""A ground near the ink rule's crossover, in the sample shared with the
color picker's identical block."""

EXAMPLE_GROUND_BLUE = "#3060d0"
"""A saturated dark ground, in the sample shared with the color picker's
identical block."""

EXAMPLE_GROUND_GRAY_77 = "#777777"
"""A mid gray: measured against itself for the 1:1 end of contrast_ratio(),
and a swatch the edge rule is tried on."""

EXAMPLE_GROUND_GRAY_80 = "#808080"
"""A mid gray ground for the ink/edge agreement check and the shared sample.
It is DEFAULT_CUSTOM_BG_COLOR's value today, but a sample here."""

EXAMPLE_GROUND_GRAY_10 = "#101010"
"""A near-black ground for the ink/edge agreement check."""

EXAMPLE_GROUND_GOLD = "#d2bc93"
"""A swatch the ink rule is tried on, in the sample shared with the color
picker. It is BRAND_GOLD's value today, but a sample: it must not follow the
brand."""

EXAMPLE_GROUND_DARK_GOLD = "#8c7337"
"""A swatch the ink and edge rules are tried on. It is BRAND_DARK_GOLD's value
today, but a sample: it must not follow the brand."""

EXAMPLE_HEX_BLACK = "#000000"
"""What color_to_hex() makes of (0, 0, 0), and what hex_to_color() reads
back to it."""

EXAMPLE_HEX_WHITE_UPPER = "#FFFFFF"
"""What color_to_hex() makes of (255, 255, 255), in the upper case it writes,
and what hex_to_color() reads back. The case is the point."""

EXAMPLE_HEX_RED_UPPER = "#FF0000"
"""What color_to_hex() makes of (255, 0, 0), upper case, and the input of the
test that hex_to_color() reads upper case. The case is the point."""

EXAMPLE_HEX_GOLD = "#d2bc93"
"""What color_to_hex() makes of (210, 188, 147), compared in lower case. It
is the bright gold's value today, but a sample: the channels beside it are
written out, so it must not follow the brand."""

EXAMPLE_LIGHTEN_BASE = "#8c7337"
"""The base lighten(base, -14) is tried on, to show the shift is the same on
every channel. It is BRAND_DARK_GOLD's value today; the real derivation is
held by name in tests/test_brand_contrast.py."""

EXAMPLE_CLAMP_WHITE = "#ffffff"
"""The top of the channel range: lighten() at +40 must hand it back
unchanged, which is clamping rather than wrapping."""

EXAMPLE_CLAMP_BLACK = "#000000"
"""The bottom of the channel range: lighten() at -40 must hand it back
unchanged."""

EXAMPLE_TRANSLUCENT_BASE = "#1a1a1a"
"""The base translucent() is tried on, and the good base passed while bad
alphas are tried. Six digits with its '#'."""

EXAMPLE_TRANSLUCENT_BASE_BARE = "1a1a1a"
"""EXAMPLE_TRANSLUCENT_BASE without its '#', which translucent() also takes."""

EXAMPLE_TRANSLUCENT_RESULT = "#ed1a1a1a"
"""What translucent() makes of EXAMPLE_TRANSLUCENT_BASE at alpha 0xED:
eight digits, alpha first, lower case, which is how the 2026-09-25 ruling
spells an eight-digit value."""

EXAMPLE_TRANSLUCENT_UPPER_BASE = "#D2BC93"
"""A base written in upper case. The case is the point: the test shows
translucent() writes lower case whatever it is given."""

EXAMPLE_TRANSLUCENT_UPPER_RESULT = "#33d2bc93"
"""What translucent() makes of EXAMPLE_TRANSLUCENT_UPPER_BASE at alpha 0x33,
in lower case."""

EXAMPLE_HAND_EDIT = "#123456"
"""A value planted on one of the color file's lines, as a hand edit the sync
must put back (tests/test_colors_in_sync.py). Any color the map does not
hold will do."""

EXAMPLE_HAND_EDIT_FALLBACK = "#654321"
"""The planted value to use when the line already holds EXAMPLE_HAND_EDIT."""

EXAMPLE_MOVED_ACCENT = "#6f94bc"
"""Where a pretend brand move puts APP.accent, so the test can see that one
line, and only that one, takes it (tests/test_colors_in_sync.py)."""

EXAMPLE_MOVED_ACCENT_FALLBACK = "#456c91"
"""The pretend move to use when the brand's accent already is
EXAMPLE_MOVED_ACCENT."""

# ---------------------------------------------------------------------- data

DATA_PROBE_HEX = "#ffcccc"
"""The hex in the probe source tests/test_named_and_used.py hands its sweep,
and the find it must report. The probe text is built from this name."""

DATA_PROBE_RGBA = "rgba(255, 255, 255, 230)"
"""The rgba() in the same probe, and the find the sweep must report, spaced
as the sweep normalizes it."""

DATA_PROBE_CLEAR_RGBA = "rgba(0, 0, 0, 0)"
"""Clear, at alpha 0, in the probe source tests/test_named_and_used.py hands
its sweep as what it must NOT report: clear is how a widget is told to paint
nothing, not a color."""

DATA_CUSTOM_BG_CHOICE = "#0ac81e"
"""The custom preview background a person picks in the color dialog,
QColor(10, 200, 30), as the background selector's button writes it into its
stylesheet, compared in lower case (tests/test_preview_utils.py)."""

DATA_SHEET_INK_BLACK_SHORT = "#000"
"""The selection ink the ink reader's sample sheet writes, in three digits,
so the reader must expand it (tests/test_ink_on_the_golds.py)."""

DATA_SHEET_INK_WHITE = "#ffffff"
"""The ink the sample sheet writes on a label over an eight-digit lookalike
of the dark gold, which the reader must not take for the gold."""

DATA_PARSED_WHITE = "#ffffff"
"""What the ink reader makes of the sample sheet's CSS word `white`: QColor's
name for it. A parse result, not WHITE, so a brand move does not change it."""

DATA_PARSED_BLACK = "#000000"
"""What the ink reader makes of DATA_SHEET_INK_BLACK_SHORT. A parse result,
not TRUE_BLACK."""

DATA_OS_SIM_CHROME_GRAY = "#333333"
"""What OS_SIM_COLORS paints the Windows taskbar edge, the Finder text,
Chrome's tab title and its bookmarks text with: another system's chrome, and
the value APP_BORDER held when these entries were unbound from it. Not
APP_BORDER: the depiction must not follow this brand."""

DATA_OS_SIM_CHROME_BLACK = "#000000"
"""What OS_SIM_COLORS paints the light Windows taskbar's text and Explorer's
text with: the value TRUE_BLACK held when they were unbound from it. Not
TRUE_BLACK, for the same reason."""

DATA_OS_SIM_TASKBAR_LIGHT = "#f0f0f0"
"""What OS_SIM_COLORS paints the simulated light Windows taskbar with:
another system's chrome, which the 2026-09-06 collapse of this application's
light strays left alone. It shares a hex with RETIRED_LIGHT_HOVER_AND_HEADER
and nothing else; tests/test_light_wiring.py exempts its one line of
utils/colors.py by exact text."""

# ------------------------------------------------------------------- retired

RETIRED_DARK_STRAY_GRAY = "#252525"
"""The dark platform button, scrollbar and alternate list row until
2026-09-02, when it was ruled onto APP_CARD: a third of the way from panel to
card, on neither the surface ladder nor the ink grid, and not a visible step
from its neighbors."""

RETIRED_LIGHT_PLATFORM_BG = "#fafafa"
"""The light platform button until 2026-09-06, collapsed onto
APP_SURFACE_LIGHT_2. Lower case: the source sweep matches it by text."""

RETIRED_LIGHT_LIST_ALT = "#f8f8f8"
"""The light alternate list row until 2026-09-06, collapsed onto
APP_SURFACE_LIGHT_2. Lower case, for the same sweep."""

RETIRED_LIGHT_HOVER_AND_HEADER = "#f0f0f0"
"""The light platform-button hover and list header until 2026-09-06,
collapsed onto one gray in two roles: APP_HOVER_LIGHT for the hover, GRAY_EE
for the header. The simulated Windows light taskbar still has this hex, as
DATA_OS_SIM_TASKBAR_LIGHT: another system's color, not this application's."""

RETIRED_APP_GOLD = "#b19145"
"""An app-local approximation of the brand dark gold, retired: it carried
white text at 2.9976:1."""

RETIRED_LIGHT_HOVER_TINT = "#c4a458"
"""The old light hover tint, RETIRED_APP_GOLD lifted 19 on every channel. It
was written down rather than derived, so when the accent moved it went on
pointing at a value no longer in the palette, with nothing to flag it."""

RETIRED_ERROR_RED = "#dc3545"
"""What the orphaned 'error' palette key held in every palette until it was
deleted; nothing drew it."""

RETIRED_MATERIAL_GREEN = "#4caf50"
"""Material's green, held for the folder watcher until it was ruled onto the
register's on 2026-09-02."""

RETIRED_BOOTSTRAP_GREEN = "#28a745"
"""Bootstrap's green, retired by the register on 2026-09-03: it and
Bootstrap's red were one olive under deuteranopia, about 4 apart."""

RETIRED_BOOTSTRAP_AMBER = "#ffc107"
"""Bootstrap's amber, retired by the register on 2026-09-03: it could not
clear a 3:1 fill floor on any light ground, reading 1.63 on WHITE."""

RETIRED_SUCCESS_TEXT_LIGHT_REV30 = "#8a6581"
"""STATUS["success-text-light"] at register rev 30, walked against
APP_SURFACE_LIGHT_3 as the worst light ground. Rev 31 re-walked it against
REGISTER_GOLD_TEXT_GROUND_FLOOR as STATUS_SUCCESS_TEXT_LIGHT."""

RETIRED_WARNING_TEXT_LIGHT_REV30 = "#976633"
"""STATUS["warning-text-light"] at register rev 30, walked against
APP_SURFACE_LIGHT_3; rev 31 re-walked it as REGISTER_STATUS_WARNING_TEXT_LIGHT."""

RETIRED_ERROR_TEXT_LIGHT_REV30 = "#b84e58"
"""STATUS["error-text-light"] at register rev 30, walked against
APP_SURFACE_LIGHT_3 and re-walked at rev 31."""

RETIRED_HANDLE_GRAY = "#505050"
"""Ruled onto GRAY_44 on 2026-09-02 (RNV-COLLAPSE-505050), and still the
color half of image mode's scrollbar handle until 2026-09-24, because the
alpha form was written out as rgba() and every sweep compared six-digit hex.
A test looks for it, without its '#', inside the eight-digit value."""

RETIRED_SCRIM_RGBA = "rgba(26, 26, 26, 0.93)"
"""Image mode's window and panel ground as it was written out: BRAND_BLACK at
93%, spelled as rgba(), which QColor cannot parse, so QPalette painted it
opaque black. translucent(BRAND_BLACK, SCRIM_ALPHA) replaced it."""

# ------------------------------------------------------------------ register

REGISTER_GOLD_TEXT_GROUND_FLOOR = "#e8e8e8"
"""The register's gold text floor: the darkest light ground on which the gold
family and the light status text still carry text at 4.5:1. The rungs are
walked against it; this application does not draw it."""

REGISTER_APP_CANVAS = "#0a0a0a"
"""APP["canvas"], the dark surface ladder's lowest rung, registered in rnv-brand
rev 22. This application has no canvas surface and does not draw it."""

REGISTER_STATUS_SUCCESS = "#926c89"
"""STATUS["success"], the register's success fill. This application draws no
status fill and dropped it on 2026-10-04."""

REGISTER_STATUS_WARNING_TEXT_LIGHT = "#8e5e2b"
"""STATUS["warning-text-light"], the warning's text on light grounds,
re-walked against REGISTER_GOLD_TEXT_GROUND_FLOOR at rev 31. This application
draws no warning."""

# ------------------------------------------------------------------- invalid

INVALID_EIGHT_DIGIT_BASE = "#1a1a1a1a"
"""Eight digits where translucent() takes a six-digit base, so it must be
refused."""

INVALID_FIVE_DIGIT_BASE = "#1a1a1"
"""Five digits, one short of a color, so translucent() must refuse it."""

INVALID_EIGHT_DIGIT_UPPER = "#ED1A1A1A"
"""EXAMPLE_TRANSLUCENT_RESULT in upper case: the spelling of an eight-digit
value the 2026-09-25 ruling forbids. Qt reads either case; the lower-case
guard in tests/test_derived_values.py refuses this one."""


REGISTER_REFS = {
    "REGISTER_GOLD_TEXT_GROUND_FLOOR": "GOLD_TEXT_GROUND_FLOOR",
    "REGISTER_APP_CANVAS": "APP.canvas",
    "REGISTER_STATUS_SUCCESS": "STATUS.success",
    "REGISTER_STATUS_WARNING_TEXT_LIGHT": "STATUS.warning-text-light",
}
"""The brand's name for each REGISTER_ value; tests/test_color_values.py
holds each against the register at the pin."""
