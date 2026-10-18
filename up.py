"""The icon builder, in American spelling: color, gray, behavior, center

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-icon-builder, derived against a fresh clone at the live head (a827ea1).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-18: #59 A, "colour" becomes "color" everywhere: code, comments,
file names, map keys, markers, test names, the root suite and documents; #60 A,
and the other British spellings with it, "grey" (GREY_44 is GRAY_44),
"behaviour" and "centre"; #62 A, and the rest the census found: -ise is -ize,
licence, programme, labelled, dialled, honour, judgement, neighbour, maths.
"cancelled" stays: it is American too, and it names signals. In one round, one
file per app. A dictionary census of the result finds no British-only word.

NO GUARD IN THE APP. The rule lives in the brand, so that everything made from
scratch starts on it: a note goes to the brand chat for rnv-brand, and the
practice doc carries it (Chris, 18 October).

THE RULES, inside words and names, keeping case (COLOUR_FILE is COLOR_FILE):
  colour     -> color
  grey       -> gray
  behaviour  -> behavior
  centre(s?)(?![A-Za-z]) -> center\1
  centr(ed|ing) -> center\1
  centre(?=line|piece|point) -> center
  (normal|recogn|optim|parametr|parameter|serial|token|maxim|minim|neutral|general|organ|real|visual|util|summar|custom|initial|synchron|capital|categor|character|priorit|standard|final|local|sanit|random|stabil|memor|author|apolog|critic|special|material|raster|harmon|emphas|quant|linear|central|rational)is(e|ed|es|ing|er|ers|ation|ations|able|ably|ability) -> \1iz\2
  licenc(e|es|ed|ing) -> licens\1
  (?<![A-Za-z])programme(s?)(?![A-Za-z]) -> program\1
  (?<![A-Za-z])maths(?![A-Za-z]) -> math
  (label|travel|model|level|signal|dial|equal|fuel|channel|tunnel|total|spiral|pedal|marvel|rival|quarrel|counsel|libel|shovel|swivel|unravel|bevel|enamel|jewel|panel|pencil|stencil|duel|barrel|grovel|revel|towel|funnel)l(ed|ing|er|ers) -> \1\2
  (hon|neighb|fav|flav|hum|lab|rum|vap|harb|arm|endeav|sav|od|splend|val|clam|parl|tum|savi)our -> \1or
  dgement    -> dgment
  (off|def|pret)ence -> \1ense
  (met|lit|fib|theat|calib|spect|lust)re(s?)(?![A-Za-z]) -> \1er\2
  practis(e|ed|es|ing) -> practic\1
  sceptic    -> skeptic
  aluminium  -> aluminum
  artefact   -> artifact
  and a note beside a tree diagram keeps its column when a name before it gets shorter.

LEFT AS THEY ARE:
  CSS's own color keywords. CSS defines grey, lightgrey and the rest beside
  gray; a string that holds nothing but CSS keywords, or a regex for them, is
  CSS, and what the user can type (a search for "grey") keeps working.
  LICENSE files, which are legal text.
  Every one this round leaves, by file and count. A plain scan of the whole
  checkout, with no exception applied, must find exactly these and no more:
  tests/test_named_and_used.py (7): CSS_NAMES: CSS's own color keywords, one
      of which a color written by name must be.

WHAT LANDS.
  44 files, the same text in American spelling, 3 of them renamed:
    tests/colour_values.py -> tests/color_values.py
    tests/test_colour_values.py -> tests/test_color_values.py
    tests/test_colours_in_sync.py -> tests/test_colors_in_sync.py
NO VALUE MOVES. Every value ui/colors.py defines is what it was, under its new name.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import tokenize
import types
from pathlib import Path

REPO = 'rnv-icon-builder'
SENTINEL = 'RNV-COLOR-SYNC'   # written only by this round: the marker was spelled the other way
SENTINEL_FILE = 'tools/sync_colors.py'
GUARD = 'tests/test_colors_in_sync.py'
GUARD_FILES = ['tests/test_color_values.py', 'tests/test_colors_in_sync.py']
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *GUARD_FILES]
DESCRIPTION = "The icon builder, in American spelling"

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest.
SUITES = [("python run_tests.py  (both CI workflows)",
           [sys.executable, "run_tests.py"])]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': 'a1aae0c42b3595089f379ddf3c672fa5b2f0e329932a296edfd6b28a0ceab413', '.github/workflows/tests-windows.yml': 'f8db062dd8c6b5354da5fabe91d902cdb500ea354c27603f10b7474ebdbbe898'}

SHADOWS = ['conftest.py', 'run_tests.py', 'sync_colors.py', 'test_color_values.py', 'test_colors_in_sync.py', 'test_rnv_icon_builder.py']

LEFT_ALONE = ["every value the application draws: the same, under its American name.",
              "CSS's own color keywords, in data: a table of CSS names, a regex for them, a search the user types.",
              "LICENSE files, which are legal text.",
              "rnv-brand, which the brand chat keeps: a note goes to it."]

# ======================================================================== the transform

import ast
import io
import re
import tokenize

_L = "(?<![A-Za-z])"   # no letter before
_R = "(?![A-Za-z])"    # no letter after

#: (British pattern, American replacement), each tried case-insensitively; the
#: replacement takes the case of the letters it replaces. Patterns match inside
#: names, so COLOUR_FILE and _normalise are reached.
BASE_RULES: list[tuple[str, str]] = [
    ("colour", "color"),                       # colours, coloured, recolour, COLOUR_FILE
    ("grey", "gray"),                          # greys, greyscale, GREY_44
    ("behaviour", "behavior"),                 # behaviours, behavioural
    ("centre(s?)" + _R, r"center\1"),          # centre, centres -> center, centers
    ("centr(ed|ing)", r"center\1"),            # centred, centring -> centered, centering
    ("centre(?=line|piece|point)", "center"),  # centreline
]

#: #62 A: the further British spellings, the -ise family by its stems, so that
#: realistic, organism, criticism and optimism are not touched.
_ISE_STEMS = ("normal recogn optim parametr parameter serial token maxim minim neutral general organ real "
              "visual util summar custom initial synchron capital categor character priorit standard final "
              "local sanit random stabil memor author apolog critic special material raster harmon emphas "
              "quant linear central rational").split()
#: A final l doubled before -ed, -ing, -er: American keeps it single. Not
#: "cancelled", which is American too (#62 A).
_LL_STEMS = ("label travel model level signal dial equal fuel channel tunnel total spiral pedal marvel "
             "rival quarrel counsel libel shovel swivel unravel bevel enamel jewel panel pencil stencil "
             "duel barrel grovel revel towel funnel").split()
EXTRA_RULES: list[tuple[str, str]] = [
    ("(" + "|".join(_ISE_STEMS) + ")is(e|ed|es|ing|er|ers|ation|ations|able|ably|ability)",
     r"\1iz\2"),
    ("licenc(e|es|ed|ing)", r"licens\1"),
    (_L + "programme(s?)" + _R, r"program\1"),
    (_L + "maths" + _R, "math"),
    ("(" + "|".join(_LL_STEMS) + ")l(ed|ing|er|ers)", r"\1\2"),
    ("(hon|neighb|fav|flav|hum|lab|rum|vap|harb|arm|endeav|sav|od|splend|val|clam|parl|tum|savi)our",
     r"\1or"),
    ("dgement", "dgment"),                     # judgement, acknowledgement
    ("(off|def|pret)ence", r"\1ense"),
    ("(met|lit|fib|theat|calib|spect|lust)re(s?)" + _R, r"\1er\2"),
    ("practis(e|ed|es|ing)", r"practic\1"),
    ("sceptic", "skeptic"),
    ("aluminium", "aluminum"),
    ("artefact", "artifact"),
]

#: CSS color keywords spelled with grey; a string of only these is CSS, kept.
CSS_GREYS = frozenset({"grey", "lightgrey", "darkgrey", "dimgrey", "slategrey",
                       "darkslategrey", "lightslategrey"})
#: Every CSS color keyword (CSS Color Module Level 4), and words a regex or a
#: CSS declaration about them carries.
CSS_WORDS = frozenset("""aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue
blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue
darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid
darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink
deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold
goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush
lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey
lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime
limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen
mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin
navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise
palevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue
saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow
springgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow
yellowgreen color s b""".split())

DELIVERY_MARKER = "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP"


def rules() -> list[tuple[str, str]]:
    return BASE_RULES + EXTRA_RULES


_COMPILED: list[tuple[re.Pattern, str]] = []


def _compiled() -> list[tuple[re.Pattern, str]]:
    if len(_COMPILED) != len(rules()):
        _COMPILED[:] = [(re.compile(p, re.I), r) for p, r in rules()]
    return _COMPILED


def _cased(found: str, american: str) -> str:
    """american, in the case found was written in."""
    letters = [c for c in found if c.isalpha()]
    if letters and all(c.isupper() for c in letters):
        return american.upper()
    if found[:1].isupper():
        return american[:1].upper() + american[1:]
    return american


def fix(text: str) -> str:
    """Every British spelling in text, in American spelling, keeping its case."""
    for pattern, repl in _compiled():
        text = pattern.sub(lambda m: _cased(m.group(0), m.expand(repl).lower()), text)
    return text


def is_css_data(value: str) -> bool:
    """A string of nothing but CSS color keywords and regex or CSS syntax."""
    words = re.findall(r"[A-Za-z]+", value)
    return bool(words) and any(w in CSS_GREYS for w in words) and all(w in CSS_WORDS for w in words)


def _docstring_lines(src: str) -> set[int]:
    """The line numbers that hold a docstring, or an attribute docstring."""
    lines: set[int] = set()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return lines
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list):
            continue
        for i, item in enumerate(body):
            if isinstance(item, ast.Expr) and isinstance(getattr(item, "value", None), ast.Constant) \
                    and isinstance(item.value.value, str):
                if i == 0 and isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) \
                        or i > 0 and isinstance(body[i - 1], (ast.Assign, ast.AnnAssign)):
                    lines.update(range(item.lineno, item.end_lineno + 1))
    return lines


def _python_spans(src: str) -> list[tuple[int, int]]:
    """(start, end) offsets of the string literals that are CSS data, to keep."""
    keep = []
    docs = _docstring_lines(src)
    starts = [0]
    for line in src.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, SyntaxError):
        return keep
    for tok in tokens:
        if tok.type != tokenize.STRING or tok.start[0] in docs:
            continue
        try:
            value = ast.literal_eval(tok.string)
        except (ValueError, SyntaxError):
            continue
        if isinstance(value, str) and is_css_data(value):
            keep.append((starts[tok.start[0] - 1] + tok.start[1], starts[tok.end[0] - 1] + tok.end[1]))
    return keep


def skipped(rel: str, text: str | None = None) -> bool:
    """LICENSE files, and a delivery script at the root (up.py) that carries the
    marker. A test that only mentions the marker, to skip such a script, is
    English like any other file."""
    name = rel.rsplit("/", 1)[-1]
    if name.upper().startswith("LICENSE") or name.upper().startswith("LICENCE"):
        return True
    return "/" not in rel and re.fullmatch(r"up(_\w+)?\.py", name) is not None \
        and text is not None and DELIVERY_MARKER in text


#: A line of a tree diagram, and the gap before the note written beside it.
_TREE_LINE = re.compile("[├└]──")   # a branch drawn with box characters
_NOTE_GAP = re.compile("(?<=\\S)( {2,})(?=[#←])")  # two spaces or more, then '#' or a left arrow


def _keep_column(old: str, new: str) -> str:
    """A note beside a tree diagram keeps its column when a name before it gets
    shorter: colour_values.py is color_values.py, and the arrow after it stays
    where the arrows of the lines around it are."""
    if old == new or not _TREE_LINE.search(old):
        return new
    o, n = _NOTE_GAP.search(old), _NOTE_GAP.search(new)
    if not o or not n or o.end() == n.end():
        return new
    gap = max(2, len(n.group(1)) + o.end() - n.end())
    return new[:n.start()] + " " * gap + new[n.end():]


def _columns(old: str, new: str) -> str:
    if old == new or "──" not in old:
        return new
    old_lines, new_lines = old.split("\n"), new.split("\n")
    if len(old_lines) != len(new_lines):
        return new
    return "\n".join(_keep_column(o, n) for o, n in zip(old_lines, new_lines))


def transform_text(text: str, rel: str) -> str:
    if skipped(rel, text):
        return text
    if not rel.endswith(".py"):
        return _columns(text, fix(text))
    out, at = [], 0
    for start, end in _python_spans(text):
        out.append(fix(text[at:start]))
        out.append(text[start:end])
        at = end
    out.append(fix(text[at:]))
    return _columns(text, "".join(out))


def transform_path(rel: str) -> str:
    return fix(rel)


def british(text: str, rel: str) -> list[tuple[int, str]]:
    """Every British spelling left in text: (line, the word it is in)."""
    if skipped(rel, text):
        return []
    keep = _python_spans(text) if rel.endswith(".py") else []
    found = []
    for pattern, _ in _compiled():
        for m in pattern.finditer(text):
            if any(s <= m.start() < e for s, e in keep):
                continue
            lo, hi = m.start(), m.end()
            while lo > 0 and (text[lo - 1].isalnum() or text[lo - 1] == "_"):
                lo -= 1
            while hi < len(text) and (text[hi].isalnum() or text[hi] == "_"):
                hi += 1
            found.append((text.count("\n", 0, m.start()) + 1, text[lo:hi]))
    return sorted(found)

# ======================================================================== this round

#: Hand edits before the transform, where a renamed word would meet a name already there.
PRE = {}

#: sha256 of each file the round reaches, as the head holds it (under its old name if renamed)
BASE_SHAS = {'.github/workflows/brand-sync.yml': '990825f45a5d42af383ebd92fd57bfc91bbbc55cd5acda5d56e966f1ae924b9c', 'COLORS.md': '48ffe9ee2631f5c13e45a8f148267dfed752d5de3f7f8e67ce54312c50896708', 'README.md': '9760ab57e6556dc32887cef59a0b7ba066a799184f422276da05c2c8fa4b9a94', 'TEST_SYSTEM.md': '4e2fc5f41bc0178674af7efab0002e762f012e35685814cda8b6f4a30bf17f85', 'brand_map.json': 'a76c68e96a0108af2b3efb30386f53d29f3a482175b3eff444bd69db58b9ced7', 'cli.py': '7b60c6d20266695f74806690e0d83e63118389a855ae12188723de29bdc800d6', 'core/icon_builder_core.py': '05b6a4712978dec49964cf7cc88e7c715d7d673c68f39138266951efa31537e0', 'docs/INTERNALS.md': 'bfa6a6cf40fc87dd82550ed9d27bab67497e16e99bb0d1ffa380e66ee8f796ab', 'test_rnv_icon_builder.py': 'b5db28b56da3ca7d6326e217a519ce15d0a515e9a48f7906c7324523cf6cadfe', 'tests/conftest.py': '43f52520768c661cca472ffe4e53046c9cb310cdaae4766bcd2ee07d79fc5d11', 'tests/test_app_mirror.py': 'da6396b0fb3cfcb1073754aaff1a8b47a08f4d18044df7d499d42d980b35007c', 'tests/test_brand_contrast.py': '5ca2230edb4317ab240621dad03ad56e04da0e2bcfe3849a2d506a6d27d15fcd', 'tests/test_button_key_names.py': 'ac025e5a83c90822ba3bc0d9a8a86c681cc036776e4afa9579732ef3b30818a7', 'tests/test_collapse_252525.py': 'a8dfbd6b5125a8a098183a6e2f31cba5ecde0c2813e92cb1d80ce37217b4fd92', 'tests/test_dead_error_key.py': '4789a343fcb1439de3466de5c2a5ff7bd759d06871a6e113fdbe5a812f420fc8', 'tests/test_dependency_coherence.py': '40b3b9ecd6a7fa8d9db76bb17aa3125b367ca8b234f231dfa848e096cea3a0ad', 'tests/test_dependency_file_placement.py': '98b473c303c8a14474b88d90f01dd6c254033a5a0e4f660a8e717405085997d4', 'tests/test_derived_values.py': '1bd2646ecc60289be07dbc2f973d069f9a320fd2e08ffd4d3665e2e38ed9fef9', 'tests/test_fleet_floor.py': '4cc6dba16ba1f616ca3e8ceec0f5497e3e01f166410b3c75d9077707967a86b9', 'tests/test_gold_as_text.py': '5f1148a02dabdae299428e8a8d3f6601ec039da3f4ca11b94384ca95bf1456ff', 'tests/test_image_budget.py': 'c5aefe05de4bc3d4fdb770f816a57e21783287ef3a4455785d4b26565c7d5bef', 'tests/test_ink_on_the_golds.py': '55bb683caf1cd2183f879070152bbb78c6853b4a03717ab7ca52720e861ad124', 'tests/test_ink_rule.py': 'b94caff6c8a6ed6e1e57685d52e00d3322769ac5b198ab38bcc88606a1e67575', 'tests/test_ladder_and_plate.py': '1338b39efa8e32e7f06e4a0900a08aaa515d05a2771dda9f6620eff73d4e4714', 'tests/test_light_rewalk.py': '2792d796d1cd59cd996f2368a743b8c06397f172ee0b8aab3f397ceef7831ba1', 'tests/test_light_wiring.py': '7a6c6fd3f3491a4f803c4d7a6e798e79ccd513dc788057b9ed30a055bff03829', 'tests/test_named_and_used.py': '753e31991cfd72973473a7b84dadc782a8f33514f620b6bb81b7fccbadfc3719', 'tests/test_png_mark_draws.py': 'facd382f19ab0fc17ed85050cb64130f893be2195c1afda3f2a5e1fa226a4504', 'tests/test_preview_utils.py': '4cb1ed1dbca477f6792637b0b7b6ac25456a0baa8e5a0f2533abec5b3a95ec64', 'tests/test_readme_test_counts.py': 'f9e6f43ba5ae8b5e7ee310377c96475f742c0fee611ada87654937212354d095', 'tests/test_register_wiring.py': 'd1e0192bfe881477df9969adada90ba51aba473d391b0f72fb6b3636361a9774', 'tests/test_status_register.py': 'a86548c463eacbb73234290771a0490757e9a77796b9f657478603bd5283af53', 'tests/test_surface_alignment.py': 'b2958a07b65c2ba9790aaa249faaf8ccde2a8ab9a1acd8dd5648ab55eae5bd7e', 'tests/test_watch_label_follows_a_switch.py': '5edcb0d6c5326091b6bbfaee470ad20a2d98ed283437a49686a853e62a9f0d31', 'tools/sync_colors.py': '80e6d14160f3148bcf512e2df1cf4e7edd69311d888533fd9a50bcdb4116391e', 'ui/colors.py': '2ce38ab5c846a29964ebff8dce61454e32b440003e5814559e26b71e04f5e707', 'ui/ico_analyzer.py': 'c2fe093c626521e8223ae1545dcc1caeaac55bf2be07d4b5fa565d7c7b25f9b6', 'ui/preview_utils.py': 'a183b5ab1efddfd9288dddd1ab6666ec13629466d3b07b6793d0e35d7852000d', 'ui/settings_dialog.py': 'ed4a013ea1db3f9f23b87b0b68de2d6cbe4deed2e839e5b5bc1b432bfe1d1a08', 'ui/theme_manager.py': '5bbcad2c97de4be9e04f341b4049ef9286d6c2dc6425200ec8bf00bcd3b0a5a8', 'utils/pil_compat.py': '2f54221b7f62f4bd05f78c6a3b18baf2ad91a9efb654544674e2d16b3131425c', 'tests/colour_values.py': 'c98bea9a1ef0a0d68e06cf6ef5144d89ca8edca6cf6f21e288df06dfccb56336', 'tests/test_colour_values.py': '53ca63f0c39796dbecbc378eac1657ee876209b2dd3d9e2c5aad26dc68116b1b', 'tests/test_colours_in_sync.py': 'f7d986594bdb4fc83ceed7e668ffa156c246f2dd0173a440f3c14cc0cf1e7caf'}

#: (new name, old name)
RENAMES = [('tests/color_values.py', 'tests/colour_values.py'), ('tests/test_color_values.py', 'tests/test_colour_values.py'), ('tests/test_colors_in_sync.py', 'tests/test_colours_in_sync.py')]

NEW_FILES = {}

#: The root suite's digest, where CI holds it: (file, the head's, this round's)
DIGESTS = []

#: sha256 of every file as this round writes it
WANT = {'.github/workflows/brand-sync.yml': 'ec6a2c6346523e752b7c4d37e371e9f7d2d5da5921da7fd3dc6bebb768b571c3', 'COLORS.md': 'a904d36edcc7673a468db8d7b4cf746a03ebe2086a723ea0c979b562cff8351b', 'README.md': '46a4b078ab37d10d7a28f1604c1c7968d695acbe40ce8f35f693a35570ead1f5', 'TEST_SYSTEM.md': 'a7d51ebcd65d270641cf6e3e9615ed75559496dbf4234601f56dba4498b9471d', 'brand_map.json': '22ac0ddd3030180ac8922675e1d7a82ca439dcd16075b35ab8a9d72367f6ee4b', 'cli.py': 'fe1caf1aaa20c9a4c6d9dd6b1fb450ac3639558575f7135c5cf5f6b7e887b048', 'core/icon_builder_core.py': '6ec65da0e9897db7df327c87e5274b0f27d365b61b70f557ed4a7e903eecead9', 'docs/INTERNALS.md': '419a72940dc8581a6645632dde7ffbe63b429a6c9d9c8e34324f6d22e3a6cbd9', 'test_rnv_icon_builder.py': '479e7451265f16e09ef24ad5037d3a8f2d14e690e3adaa27607962aea21d7a9a', 'tests/color_values.py': '2acef388eee717021ab945f85601cdf1610ccb4af62d73ad7e90d5977d87692e', 'tests/conftest.py': '03e5fc923da6d85259440b91c46f800889b8b341effffe364cfdee55f13f5dff', 'tests/test_app_mirror.py': 'b2de4acdd5c7f6b3d1c048a150430ef5306badbc21d036dcfa0475caabdb3730', 'tests/test_brand_contrast.py': '9e8480700f94b059370ed7fabd5d4f99ac651a89079c90ae6e681506aa6fc9f3', 'tests/test_button_key_names.py': 'c4fa12794abebf643561722bdfb8b9098b7b0458aefc7595f10060af9c774f75', 'tests/test_collapse_252525.py': '229d1863aeabab348d0bc077a95f62406e8ca61a813df2227e9745f25daea587', 'tests/test_color_values.py': 'e523afd0781788a0255f32df2fb0d12b14089160606d46db1735f91790e7a7f7', 'tests/test_colors_in_sync.py': 'da711394c4c0fc08865d800155020ad715fde11d49d2887d7aa4ccbef8f1c4ed', 'tests/test_dead_error_key.py': '13da3543581a22ff9e33ecbb803ab042b7bb8589b7fa2dd3109e7601e18117b1', 'tests/test_dependency_coherence.py': '841e21255aee937e747c7a38e7c15b87fbbff73f3c92508a53ceecf26e6b1332', 'tests/test_dependency_file_placement.py': '7808bf16394ad22fdf075e8690ec4cceaa422505ad2f49a11ae1d1626735b648', 'tests/test_derived_values.py': '2fcf053a336edf2fd396aa05e8fb32d27c65ef71bba5e7e8372457cd5c0573e1', 'tests/test_fleet_floor.py': '99e8a8a1d5214d21b9b269f39ac25f6c2b79f7240f14aefa53966409300901e6', 'tests/test_gold_as_text.py': '2705829ee09da82669ebcfa2888fce55ce40437a80ea0491160306ad3d3f4c6b', 'tests/test_image_budget.py': '0dd0f85804f4194a4200a57be266cd17823aa49fabcb25cff3274d7609863eff', 'tests/test_ink_on_the_golds.py': 'a45948fbf3f9ef7cde8288225b5abb7b80279abcf9817c88835315c5a2107057', 'tests/test_ink_rule.py': '3bd6f5a04e49c80964026de3932d7e57395a04b953afc7ed4973d294580b71bb', 'tests/test_ladder_and_plate.py': '1e58c4fbfd0462445d7deadc986fa5510a86065a84923c7d75b7c29ec74e27c5', 'tests/test_light_rewalk.py': 'f3e139c2b04e35f68177d3b6be3d2b6ac1a709f6cba3ec0e9118508318e7d9b8', 'tests/test_light_wiring.py': '0c9fcad6a2e359f0fb0d2266660f64edf98b3dc64318e11450e004c51eaf4540', 'tests/test_named_and_used.py': '419dbbf4281a71ccb7dbe98bae468c557694787ae493ede9f910f415cc8a1570', 'tests/test_png_mark_draws.py': '1265a2b816dd525256a76b2e4e78c407600647eafaa873dd2416d0d7b9d4fd34', 'tests/test_preview_utils.py': 'c222b3faf8ab6e44554d12ac0d3ca225823bf16af187e42cf1e8594385e888b0', 'tests/test_readme_test_counts.py': 'b26be8d04b2d1e1d2bc47a6ab0b25c392847c9fd86a0849ce72ab3c491af7237', 'tests/test_register_wiring.py': '3bd8d13f037cbb78e38721468a88d72fc6bf37a9da9a4e5b7d9925830817813d', 'tests/test_status_register.py': 'd3d3c041fc9464caa21d3104f4eb1d5bec273bef0cccfae4e227f092a48157b7', 'tests/test_surface_alignment.py': 'd6044c630109059572a359aa7e65be6aa8a841b5da53a002e8921cde9f23e3a5', 'tests/test_watch_label_follows_a_switch.py': '8fc392045dda6c895c335339a064439303b8f3ef8c8ecefe73d53a84d85218ff', 'tools/sync_colors.py': 'b9bbd1c2785e5fbc56bd4f0e2b280a902874bd8ac27bdeca5768cf25e2c0818a', 'ui/colors.py': '45b48346e10552aa4c4438226ae9cab3842359da446693da9f1e257d34eeb41c', 'ui/ico_analyzer.py': '1067b656d0a055b088a3aeb216c44ed44636cddd91dbeb9b7b5ec19fcb640850', 'ui/preview_utils.py': '769a22f918c020638c010f9cc7a37e0312e209e390d69c016c62da7619082fd1', 'ui/settings_dialog.py': '0dcafd4fb72d820240f11d35709681b41218d0a35290195468e1ecfd1d75df08', 'ui/theme_manager.py': '33e74ad1dfa4a015bbcf242103c203bb153b6e3483e6e537cf9f2b843db7e96a', 'utils/pil_compat.py': '1164f16f611bd0531b923a2f17e381afb606b236ac24099226761b9ad42fce7c'}

#: Every British spelling the round leaves, {file: count}: CSS's keywords, in data (above).
KEPT = {'tests/test_named_and_used.py': 7}

COLOR_FILE = 'ui/colors.py'


def edits(tree) -> None:
    for rel, was in BASE_SHAS.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        if got != was:
            raise Stop(f"{rel} is not the head's file this round was derived from ({got[:12]}). "
                       f"Nothing was written. The file moved; re-derive before trusting the script.",
                       EXIT_CANNOT_RUN)
    old_names = {old: new for new, old in RENAMES}
    for rel in BASE_SHAS:
        text = tree.read(rel)
        for a, b in PRE.get(rel, []):
            if text.count(a) != 1:
                raise Stop(f"{rel}: the hand edit's anchor is not there once", EXIT_CANNOT_RUN)
            text = text.replace(a, b)
        new = transform_text(text, rel)
        if rel in old_names:
            tree.delete(rel)
            tree.write(old_names[rel], new)
            tree.form[old_names[rel]] = tree.form[rel]   # a renamed file keeps its BOM and line endings
        else:
            tree.write(rel, new)
    for rel, was, now in DIGESTS:
        tree.sub(rel, was, now)
    for rel, body in NEW_FILES.items():
        if (tree.root / rel).exists():
            raise Stop(f"{rel} already exists here, and this round creates it. Nothing was written.",
                       EXIT_CANNOT_RUN)
        tree.write(rel, body)


#: What the rules must do, written out, so a changed rule is refused by name.
SAMPLES = {"colour": "color", "Colours": "Colors", "COLOUR_FILE": "COLOR_FILE", "grey": "gray", "GREY_44": "GRAY_44",
           "greyscale": "grayscale", "behaviour": "behavior", "centre": "center", "centred": "centered",
           "normalise": "normalize", "optimisation": "optimization", "licence": "license", "programme": "program",
           "labelled": "labeled", "honours": "honors", "judgement": "judgment", "neighbours": "neighbors",
           "maths": "math", "Maths": "Math", "quantisation": "quantization", "linearised": "linearized",
           "centralised": "centralized", "parameterised": "parameterized", "dialled": "dialed",
           "equalled": "equaled", "mathsy": "mathsy",
           "cancelled": "cancelled", "realistic": "realistic", "programmer": "programmer", "organism": "organism",
           "central": "central", "criticism": "criticism", "emphasis": "emphasis"}


#: Where the exceptions end, written out: (text, file, what this round makes of it, what that shows).
NL = chr(10)
_TREE_WAS = "\u2502   \u251c\u2500\u2500 colour_values.py   \u2190 a" + NL
_TREE_IS = "\u2502   \u251c\u2500\u2500 color_values.py    \u2190 a" + NL
_TREE_NEXT = "\u2502   \u251c\u2500\u2500 conftest.py        \u2190 b" + NL
BOUNDARY = [
    ("names = {'grey': 1, 'lightgrey': 2}" + NL, "x.py", "names = {'grey': 1, 'lightgrey': 2}" + NL,
     "CSS's own keywords, in data, are kept"),
    ("PATTERN = r'(gray|grey)'" + NL, "x.py", "PATTERN = r'(gray|grey)'" + NL, "a regex for CSS's keywords is kept"),
    ("x = 'a grey line'" + NL, "x.py", "x = 'a gray line'" + NL, "a sentence in a string is English"),
    ('\"\"\"grey\"\"\"' + NL, "x.py", '\"\"\"gray\"\"\"' + NL, "a docstring is English, whatever its words"),
    ("# grey" + NL, "x.py", "# gray" + NL, "a comment is English"),
    ("grey" + NL, "notes.md", "gray" + NL, "a file that is not Python is English"),
    ("licence, colour" + NL, "LICENSE", "licence, colour" + NL, "legal text is kept"),
    (_TREE_WAS + _TREE_NEXT, "README.md", _TREE_IS + _TREE_NEXT, "a note beside a tree diagram keeps its column"),
]


def _checkout(tree) -> list[str]:
    """Every file git tracks here, as this round leaves them: a renamed one under its new name."""
    try:
        out = subprocess.run(["git", "-C", str(tree.root), "ls-files", "-z"], capture_output=True,
                             check=True).stdout.decode("utf-8")
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as e:
        raise Stop(f"git could not list this checkout's files ({e}). This round reads every one of them, "
                   f"to see that nothing British is left. Nothing was written.", EXIT_CANNOT_RUN)
    tracked = {rel for rel in out.split(chr(0)) if rel}
    return sorted((tracked - tree.deleted) | set(tree.files))


def _plain(tree, rel: str) -> int:
    """How many British spellings a file holds, found with no exception applied."""
    if rel in tree.files:
        text = tree.files[rel]
    else:
        path = tree.root / rel
        if not path.is_file():
            return 0
        raw = path.read_bytes()
        if b"\0" in raw:
            return 0
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return 0
    if skipped(rel, text):
        return 0
    return sum(len(pattern.findall(text)) for pattern, _ in _compiled())


def checks(tree) -> None:
    # ---- the rules do what they say, and leave what they say they leave
    wrong = {b: fix(b) for b, a in SAMPLES.items() if fix(b) != a}
    assert not wrong, f"the spelling rules give {wrong}"
    for text, rel, want, shows in BOUNDARY:
        got = transform_text(text, rel)
        assert got == want, f"{shows}, and the round makes {text!r} into {got!r}"
    # ---- no value moves: every value the color file defined is what it was, under its new name
    def values(text):
        root = str(tree.root)
        added = root not in sys.path
        if added:
            sys.path.insert(0, root)
        try:
            ns = {"__file__": str(tree.root / COLOR_FILE), "__name__": COLOR_FILE[:-3].replace("/", ".")}
            exec(compile(text, COLOR_FILE, "exec"), ns)
        finally:
            if added:
                sys.path.remove(root)
        return {k: v for k, v in ns.items() if not k.startswith("__") and not callable(v)
                and type(v).__name__ not in ("TypeAliasType", "module", "Logger")
                and not (isinstance(v, str) and os.sep in v)}
    before, after = values(_original(tree, COLOR_FILE)), values(tree.read(COLOR_FILE))
    assert sorted(fix(k) for k in before) == sorted(after), \
        f"{COLOR_FILE} defines other names: {sorted(set(map(fix, before)) ^ set(after))}"
    moved_values = sorted(k for k in before if fix(repr(before[k])) != repr(after[fix(k)]))
    assert not moved_values, f"a value moved: {moved_values}"
    assert len(before) >= 40, f"only {len(before)} values compared -- the comparison is blind"
    # ---- the map: the same entries, under the new names
    was_map = json.loads(_original(tree, "brand_map.json"))
    now_map = json.loads(tree.read("brand_map.json"))
    assert json.loads(fix(json.dumps(was_map))) == now_map, "brand_map.json holds other entries"
    assert "colors" in now_map and "color_file" in now_map, "the map's keys are not in American spelling"
    # ---- nothing British is left, outside CSS's keywords and LICENSE files
    left = [(rel, b) for rel, t in tree.files.items() for b in british(t, rel)]
    assert not left, f"British spelling left: {left[:20]}"
    # ---- the whole checkout, read plainly: exactly what this round leaves (KEPT), and no more
    found = {rel: n for rel in _checkout(tree) if (n := _plain(tree, rel))}
    differ = {rel: (found.get(rel, 0), KEPT.get(rel, 0)) for rel in sorted(set(found) | set(KEPT))
              if found.get(rel, 0) != KEPT.get(rel, 0)}
    moved = sorted(rel for rel in differ if rel not in tree.files)
    if moved:
        raise Stop(f"British spelling in files this round does not write, other than it was derived with: "
                   f"{ {rel: differ[rel] for rel in moved[:10]} } as (found, expected). The checkout moved; "
                   f"re-derive before trusting the script. Nothing was written.", EXIT_CANNOT_RUN)
    assert not differ, f"British spelling left, as (found, what this round leaves): {differ}"
    # ---- every file this round writes, as it writes it
    assert sorted(tree.files) == sorted(WANT), f"this round writes {sorted(tree.files)}"
    assert sorted(tree.deleted) == sorted(old for _, old in RENAMES), f"this round removes {sorted(tree.deleted)}"
    for rel, want in WANT.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        assert got == want, f"{rel} is not the file this round writes: {got[:12]}"

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
