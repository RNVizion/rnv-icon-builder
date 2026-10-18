"""The icon builder: the colors live in utils/colors.py

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-icon-builder, derived against a fresh clone at the live head (4bdd120).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-18: #63 A. Every app keeps its colors in one file, in one
place: utils/colors.py. Here they lived in ui/colors.py, and the file moves
to utils/colors.py. Every import, path and mention of the old place follows
it, and nothing is left there. brand_map.json, the sync tool's chart
(COLORS.md), the daily brand sync and the docs name the new place.

WHAT LANDS.
  ui/colors.py -> utils/colors.py: the file moves, and only what in it named
      its old place changes.
  42 more files: every import, path and mention follows the colors;
      COLORS.md names the new place, as tools/sync_colors.py writes it.

JUDGMENT CALLS, each reported:
  - ui/__init__.py re-exported six names from the color file. Nothing read
    them there, and the re-export goes; the package exports what is in it.
  - utils/dialog_helper.py explained its two inline imports of the colors as
    avoiding a circular import, utils to ui and back. From utils/ to utils/
    there is none: the explanation goes, the imports stay where they are.
  - cli.py and core/icon_builder_core.py import the manifest's colors
    inline, so that writing no manifest loaded no ui package. From utils/ no
    import loads it: the reason goes, the imports stay.
  - tests/test_brand_contrast.py lists files from git's index, which still
    names ui/colors.py until the move is committed. It also reads files not
    yet committed (--others) and skips a listed file that is gone, so the
    round's own run reads utils/colors.py.
  - tests/test_brand_contrast.py found ui/settings_dialog.py beside the
    color module. It finds it from the project's root.
  - The two flat-layout loaders, in the root suite and tests/conftest.py,
    register each module under its package for a checkout that holds every
    file in one folder. They list colors under utils.

NO VALUE MOVES. Every value ui/colors.py defined is what it was.
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
SENTINEL = '"color_file": "utils/colors.py"'   # brand_map.json names the new place
SENTINEL_FILE = 'brand_map.json'
GUARD = 'tests/test_colors_in_sync.py'
GUARD_FILES = ['tests/test_colors_in_sync.py', 'tests/test_named_and_used.py']
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *GUARD_FILES]
DESCRIPTION = "The icon builder: the colors live in utils/colors.py"

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest.
SUITES = [("python run_tests.py  (both CI workflows)",
           [sys.executable, "run_tests.py"])]

#: The workflows SUITES mirrors, by content hash, as this round leaves them.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': 'a1aae0c42b3595089f379ddf3c672fa5b2f0e329932a296edfd6b28a0ceab413', '.github/workflows/tests-windows.yml': 'f8db062dd8c6b5354da5fabe91d902cdb500ea354c27603f10b7474ebdbbe898'}

SHADOWS = ['colors.py', 'config.py', 'conftest.py', 'run_tests.py', 'sync_colors.py', 'test_colors_in_sync.py', 'test_named_and_used.py', 'test_rnv_icon_builder.py']

LEFT_ALONE = ['every color value: the file moves as it is, and only what names the old place changes.', 'coverage_report.txt, which run_tests.py writes: its next run writes the new path.', 'the image files, and their paths.', 'rnv-brand, which the brand chat keeps.']

# ======================================================================== this round

OLD_PLACE = 'ui/colors.py'
COLOR_FILE = 'utils/colors.py'

#: Every name that leaves utils/config.py for utils/colors.py
MOVED = []

#: sha256 of each file the round reaches, as the head holds it (under its old name if moved)
BASE_SHAS = {'.github/workflows/brand-sync.yml': 'ec6a2c6346523e752b7c4d37e371e9f7d2d5da5921da7fd3dc6bebb768b571c3', 'COLORS.md': 'a904d36edcc7673a468db8d7b4cf746a03ebe2086a723ea0c979b562cff8351b', 'README.md': '46a4b078ab37d10d7a28f1604c1c7968d695acbe40ce8f35f693a35570ead1f5', 'RNV_Icon_Builder.py': '9c6759d6167bb9feabbc40d683f260e83b082bd6e162565cf5a51785beda3c6e', 'brand_map.json': '22ac0ddd3030180ac8922675e1d7a82ca439dcd16075b35ab8a9d72367f6ee4b', 'cli.py': 'fe1caf1aaa20c9a4c6d9dd6b1fb450ac3639558575f7135c5cf5f6b7e887b048', 'core/icon_builder_core.py': '6ec65da0e9897db7df327c87e5274b0f27d365b61b70f557ed4a7e903eecead9', 'docs/INTERNALS.md': '419a72940dc8581a6645632dde7ffbe63b429a6c9d9c8e34324f6d22e3a6cbd9', 'test_rnv_icon_builder.py': '479e7451265f16e09ef24ad5037d3a8f2d14e690e3adaa27607962aea21d7a9a', 'tests/color_values.py': '2acef388eee717021ab945f85601cdf1610ccb4af62d73ad7e90d5977d87692e', 'tests/conftest.py': '03e5fc923da6d85259440b91c46f800889b8b341effffe364cfdee55f13f5dff', 'tests/test_app_mirror.py': 'b2de4acdd5c7f6b3d1c048a150430ef5306badbc21d036dcfa0475caabdb3730', 'tests/test_brand_contrast.py': '9e8480700f94b059370ed7fabd5d4f99ac651a89079c90ae6e681506aa6fc9f3', 'tests/test_button_key_names.py': 'c4fa12794abebf643561722bdfb8b9098b7b0458aefc7595f10060af9c774f75', 'tests/test_collapse_252525.py': '229d1863aeabab348d0bc077a95f62406e8ca61a813df2227e9745f25daea587', 'tests/test_dead_error_key.py': '13da3543581a22ff9e33ecbb803ab042b7bb8589b7fa2dd3109e7601e18117b1', 'tests/test_derived_values.py': '2fcf053a336edf2fd396aa05e8fb32d27c65ef71bba5e7e8372457cd5c0573e1', 'tests/test_gold_as_text.py': '2705829ee09da82669ebcfa2888fce55ce40437a80ea0491160306ad3d3f4c6b', 'tests/test_ink_on_the_golds.py': 'a45948fbf3f9ef7cde8288225b5abb7b80279abcf9817c88835315c5a2107057', 'tests/test_ink_rule.py': '3bd6f5a04e49c80964026de3932d7e57395a04b953afc7ed4973d294580b71bb', 'tests/test_ladder_and_plate.py': '1e58c4fbfd0462445d7deadc986fa5510a86065a84923c7d75b7c29ec74e27c5', 'tests/test_light_rewalk.py': 'f3e139c2b04e35f68177d3b6be3d2b6ac1a709f6cba3ec0e9118508318e7d9b8', 'tests/test_light_wiring.py': '0c9fcad6a2e359f0fb0d2266660f64edf98b3dc64318e11450e004c51eaf4540', 'tests/test_named_and_used.py': '419dbbf4281a71ccb7dbe98bae468c557694787ae493ede9f910f415cc8a1570', 'tests/test_png_mark_draws.py': '1265a2b816dd525256a76b2e4e78c407600647eafaa873dd2416d0d7b9d4fd34', 'tests/test_preview_utils.py': 'c222b3faf8ab6e44554d12ac0d3ca225823bf16af187e42cf1e8594385e888b0', 'tests/test_register_wiring.py': '3bd8d13f037cbb78e38721468a88d72fc6bf37a9da9a4e5b7d9925830817813d', 'tests/test_snapshots.py': '18011e356bbc597d40fb3881f6227b42c20df90de9540d225f506ca0255c8b56', 'tests/test_status_register.py': 'd3d3c041fc9464caa21d3104f4eb1d5bec273bef0cccfae4e227f092a48157b7', 'tests/test_surface_alignment.py': 'd6044c630109059572a359aa7e65be6aa8a841b5da53a002e8921cde9f23e3a5', 'tests/test_watch_label_follows_a_switch.py': '8fc392045dda6c895c335339a064439303b8f3ef8c8ecefe73d53a84d85218ff', 'ui/__init__.py': '77484dddbfc873049c951e302dbce35cfa89aab4ed63eacc1dc4e4e1399c4f8d', 'ui/about_dialog.py': '2dd6e5ef0a50809ee8d421299db615b0c923a99d2d1782f49269b7404aab7d7b', 'ui/base_dialog.py': '26da43a39c19221e13fbd574cb52d641fe3655627cc94d5d1b5f7ddb921ff849', 'ui/context_preview.py': '09f3a3c92eef3fa113a9f4ef81e4fb86a222d0e819566a5293dcc45432ec9112', 'ui/ico_analyzer.py': '1067b656d0a055b088a3aeb216c44ed44636cddd91dbeb9b7b5ec19fcb640850', 'ui/metadata_panel.py': 'f220f481edf530f8ea2204a021a69ab7f1063e28d8ee3548a0c72012fc8ab944', 'ui/preview_utils.py': '769a22f918c020638c010f9cc7a37e0312e209e390d69c016c62da7619082fd1', 'ui/settings_dialog.py': '0dcafd4fb72d820240f11d35709681b41218d0a35290195468e1ecfd1d75df08', 'ui/theme_manager.py': '33e74ad1dfa4a015bbcf242103c203bb153b6e3483e6e537cf9f2b843db7e96a', 'utils/__init__.py': '13a51665a50759109b7f2f229a5e49be144abbb1359175d28d0973cca57517b6', 'ui/colors.py': '45b48346e10552aa4c4438226ae9cab3842359da446693da9f1e257d34eeb41c', 'utils/dialog_helper.py': '20d983633ca9ff5fedb84f3dbb87372561c9467a11508f477870ed4882fe7897'}

#: (new name, old name)
RENAMES = [('utils/colors.py', 'ui/colors.py')]

#: (file, anchor, replacement), applied in order; each anchor is found exactly once
SUBS = [('.github/workflows/brand-sync.yml', '#                                     request is opened with the new pin,\n#                                     ui/colors.py and COLORS.md. If it is\n#                                     still open the next day, it is updated,\n', '#                                     request is opened with the new pin,\n#                                     utils/colors.py and COLORS.md. If it is\n#                                     still open the next day, it is updated,\n'), ('.github/workflows/brand-sync.yml', '          python tools/sync_colors.py | tee sync.log\n          if git diff --quiet -- ui/colors.py; then\n            echo "No color this app uses moved at rnv-brand ${head:0:7}. Nothing to open."\n', '          python tools/sync_colors.py | tee sync.log\n          if git diff --quiet -- utils/colors.py; then\n            echo "No color this app uses moved at rnv-brand ${head:0:7}. Nothing to open."\n'), ('.github/workflows/brand-sync.yml', '          git switch -C brand-sync\n          git add tests/requirements-dev.txt ui/colors.py COLORS.md\n          git commit -m "Brand sync: rnv-brand@${HEAD:0:7}"\n', '          git switch -C brand-sync\n          git add tests/requirements-dev.txt utils/colors.py COLORS.md\n          git commit -m "Brand sync: rnv-brand@${HEAD:0:7}"\n'), ('COLORS.md', "\nGenerated by `python tools/sync_colors.py` from `brand_map.json`, `ui/colors.py` and rnv-brand at `b4fa970`, the commit pinned in `tests/requirements-dev.txt`. Don't edit it by hand: change the map and run the script. `tests/test_colors_in_sync.py` fails when this file is out of date.\n\n16 colors come from the brand and 15 are the application's own. 7 more are worked out in `ui/colors.py` from those, so they follow them.\n\n", "\nGenerated by `python tools/sync_colors.py` from `brand_map.json`, `utils/colors.py` and rnv-brand at `b4fa970`, the commit pinned in `tests/requirements-dev.txt`. Don't edit it by hand: change the map and run the script. `tests/test_colors_in_sync.py` fails when this file is out of date.\n\n16 colors come from the brand and 15 are the application's own. 7 more are worked out in `utils/colors.py` from those, so they follow them.\n\n"), ('README.md', '│   ├── base_dialog.py         # Base dialog with signal/move mixins\n│   ├── colors.py              # Brand colors, theme palettes\n│   ├── theme_manager.py       # Dark/Light/Image theme cycling\n', '│   ├── base_dialog.py         # Base dialog with signal/move mixins\n│   ├── theme_manager.py       # Dark/Light/Image theme cycling\n'), ('README.md', '│   ├── py.typed\n│   ├── config.py              # Constants, paths, feature flags\n', '│   ├── py.typed\n│   ├── colors.py              # Brand colors, theme palettes\n│   ├── config.py              # Constants, paths, feature flags\n'), ('README.md', '├── tools/\n│   └── sync_colors.py         # Writes the colors in ui/colors.py, and COLORS.md\n├── tests/\n', '├── tools/\n│   └── sync_colors.py         # Writes the colors in utils/colors.py, and COLORS.md\n├── tests/\n'), ('RNV_Icon_Builder.py', ')\nfrom ui.colors import (\n    BRAND_GOLD, BRAND_DARK_GOLD,\n', ')\nfrom utils.colors import (\n    BRAND_GOLD, BRAND_DARK_GOLD,\n'), ('brand_map.json', '{\n  "about": "Where each color in ui/colors.py comes from. A string is a name in rnv-brand (TABLE.key, or one of its own constants, in engine/brand.py); an object is a value this application owns, with the reason. Edit this file, then run: python tools/sync_colors.py",\n  "app": "RNV Icon Builder",\n  "color_file": "ui/colors.py",\n  "palettes": [\n    {\n      "file": "ui/colors.py",\n      "dict": "DARK_THEME_COLORS"\n    },\n    {\n      "file": "ui/colors.py",\n      "dict": "LIGHT_THEME_COLORS"\n    },\n    {\n      "file": "ui/colors.py",\n      "dict": "IMAGE_MODE_COLORS"\n', '{\n  "about": "Where each color in utils/colors.py comes from. A string is a name in rnv-brand (TABLE.key, or one of its own constants, in engine/brand.py); an object is a value this application owns, with the reason. Edit this file, then run: python tools/sync_colors.py",\n  "app": "RNV Icon Builder",\n  "color_file": "utils/colors.py",\n  "palettes": [\n    {\n      "file": "utils/colors.py",\n      "dict": "DARK_THEME_COLORS"\n    },\n    {\n      "file": "utils/colors.py",\n      "dict": "LIGHT_THEME_COLORS"\n    },\n    {\n      "file": "utils/colors.py",\n      "dict": "IMAGE_MODE_COLORS"\n'), ('cli.py', "    # RNV-COLOR-SYNC, #56 A (2026-10-17): the colors it declares are named in\n    # ui/colors.py, the application's own data. Imported where the file is\n    # written, so a run that writes no manifest does not load the ui package.\n    from ui.colors import WEB_MANIFEST_THEME_COLOR, WEB_MANIFEST_BACKGROUND_COLOR\n    manifest = {\n", "    # RNV-COLOR-SYNC, #56 A (2026-10-17): the colors it declares are named in\n    # utils/colors.py, the application's own data.\n    from utils.colors import WEB_MANIFEST_THEME_COLOR, WEB_MANIFEST_BACKGROUND_COLOR\n    manifest = {\n"), ('core/icon_builder_core.py', "            # RNV-COLOR-SYNC, #56 A (2026-10-17): the colors the manifest and\n            # browserconfig.xml declare are named in ui/colors.py, the\n            # application's own data. Imported here, as image_processor imports\n            # from ui, so importing this module does not load the ui package.\n            from ui.colors import (WEB_MANIFEST_THEME_COLOR,\n                                   WEB_MANIFEST_BACKGROUND_COLOR,\n                                   BROWSERCONFIG_TILE_COLOR)\n            manifest = {\n", "            # RNV-COLOR-SYNC, #56 A (2026-10-17): the colors the manifest and\n            # browserconfig.xml declare are named in utils/colors.py, the\n            # application's own data.\n            from utils.colors import (WEB_MANIFEST_THEME_COLOR,\n                                      WEB_MANIFEST_BACKGROUND_COLOR,\n                                      BROWSERCONFIG_TILE_COLOR)\n            manifest = {\n"), ('docs/INTERNALS.md', '\nAll colors are defined in `ui/colors.py`:\n\n', '\nAll colors are defined in `utils/colors.py`:\n\n'), ('docs/INTERNALS.md', '\nThis is intentional — main window buttons sit against backgrounds where gold hover would be visually loud, while dialog buttons benefit from the accent. See `ui/colors.py` for the `main_btn_*` vs `button_*` key split.\n\n', '\nThis is intentional — main window buttons sit against backgrounds where gold hover would be visually loud, while dialog buttons benefit from the accent. See `utils/colors.py` for the `main_btn_*` vs `button_*` key split.\n\n'), ('docs/INTERNALS.md', '- Core modules: `icon_builder_core`, `image_processor`, `batch_processor`, `folder_watcher`, `preset_manager`, `project_manager`, `recent_files`, `session_manager`, `export_history`\n- UI modules: `colors`, `preview_utils`, `image_adjustments`\n- Utils: `config`, `logger`, `error_handler`, `file_utils`, `signal_manager`, `pixmap_cache`, `dialog_helper`\n\n', '- Core modules: `icon_builder_core`, `image_processor`, `batch_processor`, `folder_watcher`, `preset_manager`, `project_manager`, `recent_files`, `session_manager`, `export_history`\n- UI modules: `preview_utils`, `image_adjustments`\n- Utils: `colors`, `config`, `logger`, `error_handler`, `file_utils`, `signal_manager`, `pixmap_cache`, `dialog_helper`\n\n'), ('test_rnv_icon_builder.py', '    _LOAD = {\n        "utils": ["logger", "config", "error_handler", "file_utils",\n                  "signal_manager", "pixmap_cache", "async_file_ops"],\n        "core":  ["icon_builder_core", "image_processor", "recent_files",\n                  "preset_manager", "session_manager", "export_history",\n                  "batch_processor", "project_manager"],\n        "ui":    ["colors", "theme_manager", "preview_utils", "image_adjustments"],\n    }\n', '    _LOAD = {\n        "utils": ["logger", "colors", "config", "error_handler", "file_utils",\n                  "signal_manager", "pixmap_cache", "async_file_ops"],\n        "core":  ["icon_builder_core", "image_processor", "recent_files",\n                  "preset_manager", "session_manager", "export_history",\n                  "batch_processor", "project_manager"],\n        "ui":    ["theme_manager", "preview_utils", "image_adjustments"],\n    }\n'), ('test_rnv_icon_builder.py', 'from utils.dialog_helper     import DialogHelper, DialogResult\nfrom ui.colors               import (\n    BRAND_GOLD, BRAND_DARK_GOLD, _to_rgb,\n', 'from utils.dialog_helper     import DialogHelper, DialogResult\nfrom utils.colors            import (\n    BRAND_GOLD, BRAND_DARK_GOLD, _to_rgb,\n'), ('test_rnv_icon_builder.py', 'class TestColors(unittest.TestCase):\n    """ui/colors.py — brand constants, theme dicts, get_theme_colors()."""\n\n', 'class TestColors(unittest.TestCase):\n    """utils/colors.py — brand constants, theme dicts, get_theme_colors()."""\n\n'), ('tests/color_values.py', "RNV-COLOR-SYNC, #53 A (2026-10-17). The application's own colors and the\nbrand's are named in ui/colors.py, which brand_map.json names, and a test\nreads them from there. Every other color value a test or the root suite\n", "RNV-COLOR-SYNC, #53 A (2026-10-17). The application's own colors and the\nbrand's are named in utils/colors.py, which brand_map.json names, and a test\nreads them from there. Every other color value a test or the root suite\n"), ('tests/color_values.py', 'and nothing else; tests/test_light_wiring.py exempts its one line of\nui/colors.py by exact text."""\n\n', 'and nothing else; tests/test_light_wiring.py exempts its one line of\nutils/colors.py by exact text."""\n\n'), ('tests/conftest.py', '        "utils": [\n            "logger", "config", "error_handler", "file_utils",\n            "signal_manager", "pixmap_cache", "async_file_ops",\n', '        "utils": [\n            "logger", "colors", "config", "error_handler", "file_utils",\n            "signal_manager", "pixmap_cache", "async_file_ops",\n'), ('tests/conftest.py', '        "ui": [\n            "colors", "theme_manager", "preview_utils",\n            "image_adjustments", "base_dialog", "context_preview",\n', '        "ui": [\n            "theme_manager", "preview_utils",\n            "image_adjustments", "base_dialog", "context_preview",\n'), ('tests/test_app_mirror.py', "\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                       LIGHT_THEME_COLORS as LIGHT)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'ui' / 'colors.py'\n\n", "\nfrom utils import colors\nfrom utils.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'utils' / 'colors.py'\n\n"), ('tests/test_app_mirror.py', "#: was PINNED, each name with its value written beside it; the values are\n#: written into ui/colors.py from the register now, and held there.\nNEUTRALS = ('TRUE_BLACK', 'WHITE', 'BRAND_BLACK', 'APP_CARD', 'APP_BORDER',\n", "#: was PINNED, each name with its value written beside it; the values are\n#: written into utils/colors.py from the register now, and held there.\nNEUTRALS = ('TRUE_BLACK', 'WHITE', 'BRAND_BLACK', 'APP_CARD', 'APP_BORDER',\n"), ('tests/test_app_mirror.py', "#: hex code they share; the pressed plate is the register's, the other two\n#: the ramp's (the split in ui/colors.py).\nLIGHT_SURFACE_KEYS = {'pressed_bg': 'APP_PRESSED_LIGHT', 'tab_bg': 'GRAY_E0',\n", "#: hex code they share; the pressed plate is the register's, the other two\n#: the ramp's (the split in utils/colors.py).\nLIGHT_SURFACE_KEYS = {'pressed_bg': 'APP_PRESSED_LIGHT', 'tab_bg': 'GRAY_E0',\n"), ('tests/test_app_mirror.py', "                return node.value\n    raise AssertionError(f'{name} is not a dict literal in ui/colors.py')\n\n", "                return node.value\n    raise AssertionError(f'{name} is not a dict literal in utils/colors.py')\n\n"), ('tests/test_app_mirror.py', "    for name in NEUTRALS:\n        assert hasattr(colors, name), f'ui.colors has no {name}'\n\n", "    for name in NEUTRALS:\n        assert hasattr(colors, name), f'utils.colors has no {name}'\n\n"), ('tests/test_brand_contrast.py', '\nfrom ui import colors as C\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n', '\nfrom utils import colors as C\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n'), ('tests/test_brand_contrast.py', 'PROJECT_ROOT = Path(__file__).resolve().parent.parent\nCOLORS_PY = PROJECT_ROOT / "ui" / "colors.py"\n\n', 'PROJECT_ROOT = Path(__file__).resolve().parent.parent\nCOLORS_PY = PROJECT_ROOT / "utils" / "colors.py"\n\n'), ('tests/test_brand_contrast.py', '    assert name in assigns, (\n        f"{name} is expected to exist in ui/colors.py and does not. "\n        f"If it was deliberately removed, remove it from DERIVED_CONSTANTS "\n', '    assert name in assigns, (\n        f"{name} is expected to exist in utils/colors.py and does not. "\n        f"If it was deliberately removed, remove it from DERIVED_CONSTANTS "\n'), ('tests/test_brand_contrast.py', '    assigns = _module_level_assignments()\n    assert name in assigns, f"{name} missing from ui/colors.py"\n    node = assigns[name]\n', '    assigns = _module_level_assignments()\n    assert name in assigns, f"{name} missing from utils/colors.py"\n    node = assigns[name]\n'), ('tests/test_brand_contrast.py', '    root = pathlib.Path(C.__file__).resolve().parent.parent\n    files = subprocess.run(["git", "ls-files", "*.py"], cwd=root,\n                           capture_output=True, text=True).stdout.split()\n    for rel in files:\n        if rel == "ui/colors.py" or rel.startswith("tests/") or rel.startswith("test_"):\n            continue\n', '    root = pathlib.Path(C.__file__).resolve().parent.parent\n    # --others --exclude-standard: a file a change adds is read before it\n    # is committed, as the commit will hold it.\n    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],\n                           cwd=root, capture_output=True, text=True).stdout.split()\n    for rel in files:\n        if rel == "utils/colors.py" or rel.startswith("tests/") or rel.startswith("test_"):\n            continue\n        # A file git still lists but which is gone -- a move not yet\n        # committed, as the color file\'s from ui/ to utils/ was (#63 A,\n        # 2026-10-18) -- is not a source.\n        if not (root / rel).exists():\n            continue\n'), ('tests/test_brand_contrast.py', '    """The one bypass this pass fixed, pinned so it cannot come back."""\n    src = (pathlib.Path(C.__file__).resolve().parent / "settings_dialog.py"\n           ).read_text(encoding="utf-8")\n', '    """The one bypass this pass fixed, pinned so it cannot come back."""\n    src = (PROJECT_ROOT / "ui" / "settings_dialog.py"\n           ).read_text(encoding="utf-8")\n'), ('tests/test_button_key_names.py', '    """Each key\'s constant, as the value it holds."""\n    from ui import colors\n    return {key: getattr(colors, name) for key, name in pins.items()}\n\n\ndef _palettes():\n    from ui.colors import (DARK_THEME_COLORS, LIGHT_THEME_COLORS,\n                           IMAGE_MODE_COLORS)\n    return {"dark": DARK_THEME_COLORS, "light": LIGHT_THEME_COLORS,\n', '    """Each key\'s constant, as the value it holds."""\n    from utils import colors\n    return {key: getattr(colors, name) for key, name in pins.items()}\n\n\ndef _palettes():\n    from utils.colors import (DARK_THEME_COLORS, LIGHT_THEME_COLORS,\n                              IMAGE_MODE_COLORS)\n    return {"dark": DARK_THEME_COLORS, "light": LIGHT_THEME_COLORS,\n'), ('tests/test_collapse_252525.py', 'EXPECT = {\'dark\': [\'platform_btn_bg\', \'scrollbar_bg\', \'list_alt_bg\'], \'image\': [\'platform_btn_bg\', \'list_alt_bg\']}\nPALETTE_FILE = "ui/colors.py"\n\n\ndef _palettes():\n    from ui.colors import DARK_THEME_COLORS as D, IMAGE_MODE_COLORS as I; P={\'dark\':D,\'image\':I}\n    return P\n\n\ndef _new_value():\n    """The constant the keys were ruled onto, as the value it holds."""\n    from ui import colors\n    return getattr(colors, CONST)\n', 'EXPECT = {\'dark\': [\'platform_btn_bg\', \'scrollbar_bg\', \'list_alt_bg\'], \'image\': [\'platform_btn_bg\', \'list_alt_bg\']}\nPALETTE_FILE = "utils/colors.py"\n\n\ndef _palettes():\n    from utils.colors import DARK_THEME_COLORS as D, IMAGE_MODE_COLORS as I; P={\'dark\':D,\'image\':I}\n    return P\n\n\ndef _new_value():\n    """The constant the keys were ruled onto, as the value it holds."""\n    from utils import colors\n    return getattr(colors, CONST)\n'), ('tests/test_dead_error_key.py', '\nfrom ui import colors\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n', '\nfrom utils import colors\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n'), ('tests/test_derived_values.py', '\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       LIGHT_THEME_COLORS as LIGHT,\n                       IMAGE_MODE_COLORS as IMAGE,\n                       OS_SIM_COLORS as OS_SIM,\n                       translucent)\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n', '\nfrom utils import colors\nfrom utils.colors import (DARK_THEME_COLORS as DARK,\n                          LIGHT_THEME_COLORS as LIGHT,\n                          IMAGE_MODE_COLORS as IMAGE,\n                          OS_SIM_COLORS as OS_SIM,\n                          translucent)\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n'), ('tests/test_derived_values.py', 'ROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / "ui" / "colors.py"\n\n', 'ROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / "utils" / "colors.py"\n\n'), ('tests/test_derived_values.py', '    for name, (byte, _was) in ALPHAS.items():\n        assert hasattr(colors, name), f"ui.colors has no {name}"\n        assert getattr(colors, name) == byte, (\n', '    for name, (byte, _was) in ALPHAS.items():\n        assert hasattr(colors, name), f"utils.colors has no {name}"\n        assert getattr(colors, name) == byte, (\n'), ('tests/test_derived_values.py', '                    bad.append(f"{where} {pos} names {arg.id}, which does not "\n                               f"exist in ui.colors")\n            if isinstance(alpha, ast.Name) and alpha.id not in ALPHAS:\n', '                    bad.append(f"{where} {pos} names {arg.id}, which does not "\n                               f"exist in utils.colors")\n            if isinstance(alpha, ast.Name) and alpha.id not in ALPHAS:\n'), ('tests/test_derived_values.py', "\nLOWER8_MODULES = ('ui.colors', 'ui.preview_utils', 'ui.theme_manager')\n#: Found when this was written; below the floor, the sweep has gone blind.\n", "\nLOWER8_MODULES = ('utils.colors', 'ui.preview_utils', 'ui.theme_manager')\n#: Found when this was written; below the floor, the sweep has gone blind.\n"), ('tests/test_gold_as_text.py', '\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       IMAGE_MODE_COLORS as IMAGE,\n                       LIGHT_THEME_COLORS as LIGHT)\n\n', '\nfrom utils import colors\nfrom utils.colors import (DARK_THEME_COLORS as DARK,\n                          IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\n\n'), ('tests/test_gold_as_text.py', '            #: its palette with a lazy import inside each style function --\n            #: `from ui.colors import LIGHT_THEME_COLORS as colors` -- to break\n            #: a circular dependency. Reading only Assign missed that, so a\n', '            #: its palette with a lazy import inside each style function --\n            #: `from utils.colors import LIGHT_THEME_COLORS as colors` -- to break\n            #: a circular dependency. Reading only Assign missed that, so a\n'), ('tests/test_ink_on_the_golds.py', '\nfrom ui.colors import BRAND_DARK_GOLD, BRAND_GOLD, TRUE_BLACK, WHITE\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n', '\nfrom utils.colors import BRAND_DARK_GOLD, BRAND_GOLD, TRUE_BLACK, WHITE\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n'), ('tests/test_ink_rule.py', '\nfrom ui import colors\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n', '\nfrom utils import colors\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n'), ('tests/test_ink_rule.py', '    see."""\n    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")\n    hits = re.findall(r"""[\'"]#[0-9a-fA-F]{3}[\'"]""", src)\n', '    see."""\n    src = (ROOT / "utils" / "colors.py").read_text(encoding="utf-8-sig")\n    hits = re.findall(r"""[\'"]#[0-9a-fA-F]{3}[\'"]""", src)\n'), ('tests/test_ladder_and_plate.py', "\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       IMAGE_MODE_COLORS as IMAGE,\n                       LIGHT_THEME_COLORS as LIGHT)\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n# are not the application's colors are named once, in tests/color_values.py.\nfrom tests.color_values import REGISTER_GOLD_TEXT_GROUND_FLOOR\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'ui/colors.py'\n\n", "\nfrom utils import colors\nfrom utils.colors import (DARK_THEME_COLORS as DARK,\n                          IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n# are not the application's colors are named once, in tests/color_values.py.\nfrom tests.color_values import REGISTER_GOLD_TEXT_GROUND_FLOOR\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'utils/colors.py'\n\n"), ('tests/test_ladder_and_plate.py', "                return node.value\n    raise AssertionError(f'{name} is not a dict literal in ui/colors.py')\n\n", "                return node.value\n    raise AssertionError(f'{name} is not a dict literal in utils/colors.py')\n\n"), ('tests/test_light_rewalk.py', '\nfrom ui import colors as C\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n', '\nfrom utils import colors as C\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n'), ('tests/test_light_wiring.py', "\nfrom ui import colors as C\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n# are not the application's colors are named once, in tests/color_values.py.\nfrom tests.color_values import (DATA_OS_SIM_TASKBAR_LIGHT, RETIRED_LIGHT_HOVER_AND_HEADER,\n                                 RETIRED_LIGHT_LIST_ALT, RETIRED_LIGHT_PLATFORM_BG)\n\nROOT = Path(__file__).resolve().parent.parent\nSOURCE = ROOT / 'ui/colors.py'\nPALETTES = ['DARK_THEME_COLORS', 'LIGHT_THEME_COLORS', 'IMAGE_MODE_COLORS']\n", "\nfrom utils import colors as C\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n# are not the application's colors are named once, in tests/color_values.py.\nfrom tests.color_values import (DATA_OS_SIM_TASKBAR_LIGHT, RETIRED_LIGHT_HOVER_AND_HEADER,\n                                 RETIRED_LIGHT_LIST_ALT, RETIRED_LIGHT_PLATFORM_BG)\n\nROOT = Path(__file__).resolve().parent.parent\nSOURCE = ROOT / 'utils/colors.py'\nPALETTES = ['DARK_THEME_COLORS', 'LIGHT_THEME_COLORS', 'IMAGE_MODE_COLORS']\n"), ('tests/test_named_and_used.py', '#: Where this application writes its colors: the one place a literal belongs.\nCOLOR_MODULES = ("ui/colors.py",)\n#: Where its palettes are written: their own keys are not lookups.\nPALETTE_MODULES = ("ui/colors.py", "ui/theme_manager.py")\nSKIP_DIRS = {"tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__"}\n\nfrom ui.colors import DARK_THEME_COLORS, IMAGE_MODE_COLORS, LIGHT_THEME_COLORS, OS_SIM_COLORS  # noqa: E402\nfrom ui.theme_manager import ThemeManager  # noqa: E402\n', '#: Where this application writes its colors: the one place a literal belongs.\nCOLOR_MODULES = ("utils/colors.py",)\n#: Where its palettes are written: their own keys are not lookups.\nPALETTE_MODULES = ("utils/colors.py", "ui/theme_manager.py")\nSKIP_DIRS = {"tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__"}\n\nfrom utils.colors import DARK_THEME_COLORS, IMAGE_MODE_COLORS, LIGHT_THEME_COLORS, OS_SIM_COLORS  # noqa: E402\nfrom ui.theme_manager import ThemeManager  # noqa: E402\n'), ('tests/test_named_and_used.py', "    # cli.py and core/icon_builder_core.py, and browserconfig.xml's tile color\n    # stood here. They are named in ui/colors.py now, as the application's own\n    # data, and both writers read the names.\n", "    # cli.py and core/icon_builder_core.py, and browserconfig.xml's tile color\n    # stood here. They are named in utils/colors.py now, as the application's own\n    # data, and both writers read the names.\n"), ('tests/test_png_mark_draws.py', '\nfrom ui.colors import get_theme_colors\n\n', '\nfrom utils.colors import get_theme_colors\n\n'), ('tests/test_preview_utils.py', '    def test_each_mode_draws_the_button_in_its_own_colors(self, qapp):\n        from ui.colors import BRAND_GOLD, get_theme_colors\n        from ui.preview_utils import BackgroundSelectorWidget\n', '    def test_each_mode_draws_the_button_in_its_own_colors(self, qapp):\n        from utils.colors import BRAND_GOLD, get_theme_colors\n        from ui.preview_utils import BackgroundSelectorWidget\n'), ('tests/test_preview_utils.py', '\n        from ui.colors import BRAND_GOLD, get_theme_colors\n        from ui.preview_utils import BackgroundSelectorWidget\n', '\n        from utils.colors import BRAND_GOLD, get_theme_colors\n        from ui.preview_utils import BackgroundSelectorWidget\n'), ('tests/test_register_wiring.py', "\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       IMAGE_MODE_COLORS as IMAGE)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'ui/colors.py'\n\n", "\nfrom utils import colors\nfrom utils.colors import (DARK_THEME_COLORS as DARK,\n                          IMAGE_MODE_COLORS as IMAGE)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'utils/colors.py'\n\n"), ('tests/test_snapshots.py', '    def test_dark_theme_keys(self, snapshots):\n        from ui.colors import DARK_THEME_COLORS\n\n        assert sorted(DARK_THEME_COLORS.keys()) == snapshots["dark_theme_keys"]\n\n    def test_light_theme_keys(self, snapshots):\n        from ui.colors import LIGHT_THEME_COLORS\n\n        assert sorted(LIGHT_THEME_COLORS.keys()) == \\\n            snapshots["light_theme_keys"]\n\n    def test_image_mode_keys(self, snapshots):\n        from ui.colors import IMAGE_MODE_COLORS\n\n', '    def test_dark_theme_keys(self, snapshots):\n        from utils.colors import DARK_THEME_COLORS\n\n        assert sorted(DARK_THEME_COLORS.keys()) == snapshots["dark_theme_keys"]\n\n    def test_light_theme_keys(self, snapshots):\n        from utils.colors import LIGHT_THEME_COLORS\n\n        assert sorted(LIGHT_THEME_COLORS.keys()) == \\\n            snapshots["light_theme_keys"]\n\n    def test_image_mode_keys(self, snapshots):\n        from utils.colors import IMAGE_MODE_COLORS\n\n'), ('tests/test_snapshots.py', '    from ui.theme_manager import ThemeManager\n    from ui.colors import (DARK_THEME_COLORS, LIGHT_THEME_COLORS,\n                            IMAGE_MODE_COLORS)\n    from core.batch_processor import BatchJob\n', '    from ui.theme_manager import ThemeManager\n    from utils.colors import (DARK_THEME_COLORS, LIGHT_THEME_COLORS,\n                              IMAGE_MODE_COLORS)\n    from core.batch_processor import BatchJob\n'), ('tests/test_status_register.py', '\nfrom ui import colors\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n', '\nfrom utils import colors\n# RNV-COLOR-SYNC, #53 A (2026-10-17): the color values this file needs that\n'), ('tests/test_status_register.py', 'def _palettes():\n    from ui.colors import (DARK_THEME_COLORS as D, LIGHT_THEME_COLORS as L,\n                           IMAGE_MODE_COLORS as I)\n    return {"dark": D, "light": L, "image": I}\n', 'def _palettes():\n    from utils.colors import (DARK_THEME_COLORS as D, LIGHT_THEME_COLORS as L,\n                              IMAGE_MODE_COLORS as I)\n    return {"dark": D, "light": L, "image": I}\n'), ('tests/test_status_register.py', '\nSWEPT = ("ui/colors.py", "ui/settings_dialog.py")\n# the success text: a value ui/colors.py holds. It was the success fill\'s\n# until RNV-NAMED-AND-USED, 2026-10-04, when the fill went. RNV-COLOR-SYNC,\n# 2026-10-16: read from the constant, where it was written out; the sync\n# writes it into ui/colors.py as a literal, which is what the sweep must see.\nLIVE_VALUE = colors.STATUS_SUCCESS_TEXT\n', '\nSWEPT = ("utils/colors.py", "ui/settings_dialog.py")\n# the success text: a value utils/colors.py holds. It was the success fill\'s\n# until RNV-NAMED-AND-USED, 2026-10-04, when the fill went. RNV-COLOR-SYNC,\n# 2026-10-16: read from the constant, where it was written out; the sync\n# writes it into utils/colors.py as a literal, which is what the sweep must see.\nLIVE_VALUE = colors.STATUS_SUCCESS_TEXT\n'), ('tests/test_surface_alignment.py', '\nfrom ui.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\nfrom ui.colors import APP_SURFACE_LIGHT_3, BRAND_BLACK\n\n', '\nfrom utils.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\nfrom utils.colors import APP_SURFACE_LIGHT_3, BRAND_BLACK\n\n'), ('tests/test_watch_label_follows_a_switch.py', '\nfrom ui.colors import get_theme_colors\n\n', '\nfrom utils.colors import get_theme_colors\n\n'), ('ui/__init__.py', '    debug_button: Developer debug information button\n    colors: Color constants, theme color dictionaries\n    base_dialog: Base dialog class with SignalMixin + WindowMoveMixin\n"""\n\nfrom .theme_manager import ThemeManager\nfrom .colors import (\n    BRAND_GOLD, BRAND_DARK_GOLD,\n    DARK_THEME_COLORS, LIGHT_THEME_COLORS, IMAGE_MODE_COLORS,\n    get_theme_colors,\n)\nfrom .base_dialog import BaseDialog\n', '    debug_button: Developer debug information button\n    base_dialog: Base dialog class with SignalMixin + WindowMoveMixin\n"""\n\nfrom .theme_manager import ThemeManager\nfrom .base_dialog import BaseDialog\n'), ('ui/__init__.py', "    'ThemeManager',\n    # Colors\n    'BRAND_GOLD', 'BRAND_DARK_GOLD',\n    'DARK_THEME_COLORS', 'LIGHT_THEME_COLORS', 'IMAGE_MODE_COLORS',\n    'get_theme_colors',\n    # Base\n", "    'ThemeManager',\n    # Base\n"), ('ui/about_dialog.py', 'from utils.logger import Logger, get_logger_instance\nfrom ui.colors import BRAND_GOLD, get_theme_colors\nlogger: Logger = get_logger_instance("AboutDialog")\n', 'from utils.logger import Logger, get_logger_instance\nfrom utils.colors import BRAND_GOLD, get_theme_colors\nlogger: Logger = get_logger_instance("AboutDialog")\n'), ('ui/base_dialog.py', 'from utils.dialog_helper import DialogHelper\nfrom ui.colors import get_theme_colors, BRAND_GOLD, BRAND_DARK_GOLD\n\n', 'from utils.dialog_helper import DialogHelper\nfrom utils.colors import get_theme_colors, BRAND_GOLD, BRAND_DARK_GOLD\n\n'), ('ui/context_preview.py', 'from ui.base_dialog import BaseDialog\nfrom ui.colors import BRAND_GOLD, BRAND_DARK_GOLD, OS_SIM_COLORS, OS_SIM_GROUNDS_RGB, get_theme_colors\nfrom ui.preview_utils import pil_to_qpixmap, composite_on_checkerboard\n', 'from ui.base_dialog import BaseDialog\nfrom utils.colors import BRAND_GOLD, BRAND_DARK_GOLD, OS_SIM_COLORS, OS_SIM_GROUNDS_RGB, get_theme_colors\nfrom ui.preview_utils import pil_to_qpixmap, composite_on_checkerboard\n'), ('ui/ico_analyzer.py', 'from ui.base_dialog import BaseDialog\nfrom ui.colors import BRAND_GOLD, BRAND_DARK_GOLD, get_theme_colors\nfrom core.icon_builder_core import IconBuilderCore\n', 'from ui.base_dialog import BaseDialog\nfrom utils.colors import BRAND_GOLD, BRAND_DARK_GOLD, get_theme_colors\nfrom core.icon_builder_core import IconBuilderCore\n'), ('ui/metadata_panel.py', '\nfrom ui.colors import get_theme_colors\nfrom utils.logger import Logger, get_logger_instance\n', '\nfrom utils.colors import get_theme_colors\nfrom utils.logger import Logger, get_logger_instance\n'), ('ui/preview_utils.py', 'from ui.base_dialog import BaseDialog\nfrom ui.colors import (\n    BRAND_GOLD, BRAND_DARK_GOLD, get_theme_colors,\n', 'from ui.base_dialog import BaseDialog\nfrom utils.colors import (\n    BRAND_GOLD, BRAND_DARK_GOLD, get_theme_colors,\n'), ('ui/settings_dialog.py', 'from utils.config import ICON_SIZES\nfrom ui.colors import (\n    BRAND_GOLD, get_theme_colors,\n', 'from utils.config import ICON_SIZES\nfrom utils.colors import (\n    BRAND_GOLD, get_theme_colors,\n'), ('ui/theme_manager.py', 'from utils.logger import Logger, get_logger_instance\nfrom ui.colors import (\n    DARK_THEME_COLORS,\n', 'from utils.logger import Logger, get_logger_instance\nfrom utils.colors import (\n    DARK_THEME_COLORS,\n'), ('ui/theme_manager.py', '# Type alias for theme dictionary.\n# RNV-FLEET-FLOOR, 2026-09-11. PEP 695, matching ui/colors.py in the palette\n# manager, now that this application declares requires-python >= 3.13. The\n', '# Type alias for theme dictionary.\n# RNV-FLEET-FLOOR, 2026-09-11. PEP 695, matching utils/colors.py in the palette\n# manager, now that this application declares requires-python >= 3.13. The\n'), ('ui/theme_manager.py', '    # Five more keys were copied across and one alias made, and nothing read\n    # any of the six: the dialogs take their colors from ui/colors.py.\n\n', '    # Five more keys were copied across and one alias made, and nothing read\n    # any of the six: the dialogs take their colors from utils/colors.py.\n\n'), ('utils/__init__.py', 'Modules:\n    config: All configuration constants, paths, window dimensions\n', 'Modules:\n    colors: Color constants, theme color dictionaries\n    config: All configuration constants, paths, window dimensions\n'), ('utils/dialog_helper.py', "from utils.logger import Logger, get_logger_instance\n\n# NOTE: ui.colors is NOT imported at the top level here.\n# utils.dialog_helper is imported early in the startup chain (via utils/__init__.py\n# and utils.error_handler), before ui is fully initialized. A top-level\n# 'from ui.colors import ...' would create a circular import: utils -> ui -> utils.\n# Instead, get_theme_colors() is imported lazily inside each method that needs it.\n\n", 'from utils.logger import Logger, get_logger_instance\n\n'), ('utils/dialog_helper.py', '        """\n        from ui.colors import get_theme_colors  # lazy import - avoids circular dependency\n        c = get_theme_colors(is_dark=True)\n', '        """\n        from utils.colors import get_theme_colors\n        c = get_theme_colors(is_dark=True)\n'), ('utils/dialog_helper.py', '        """\n        from ui.colors import get_theme_colors  # lazy import - avoids circular dependency\n        c = get_theme_colors(is_dark=False)\n', '        """\n        from utils.colors import get_theme_colors\n        c = get_theme_colors(is_dark=False)\n')]

#: Files carried whole: most of what they held leaves them
FULL = {}

#: Files this round creates
NEW_FILES = {}

#: sha256 of every file as this round writes it
WANT = {'.github/workflows/brand-sync.yml': '627fd5ab003524d4832fd3d26991fa8285a475631a145c02a23b0db9d2cbaeb5', 'COLORS.md': '1616ca1776932aca8440a55d7d59b8f7ee89ea3c3e100c18d6346e80aab6f3de', 'README.md': '663d4fbec4c8b6dedc922544d961e97e7587285cf19d718003469270819efd8e', 'RNV_Icon_Builder.py': 'fa476b9a1541e40e9862765362a54cc4a7d27027f909da09159af5e0c0640e41', 'brand_map.json': '6fc7c1b5fd75ddf9e9e66c8309b0ea5d1d62a71788ea40e2a894df9ca1527be1', 'cli.py': '661548cdcb704659be42ae75fed86d3b52670e11c06d9978034098ca55f0046d', 'core/icon_builder_core.py': 'd609cd09523b9e32a23ddd158f21d186b7f8873cc14a414b3c06595bd526940a', 'docs/INTERNALS.md': 'ee6ac179669b6cd557126ea4c4d56c2fab4044aec6e40571f4b7a4af159cbebf', 'test_rnv_icon_builder.py': '67ac556f6304e0560b48db28752214a218cc69fbcb78f371737bda0f5fc450ae', 'tests/color_values.py': 'a66442064491cfe4868b5150a688fb012bf5a048da2d0cb102c89ffe400cca00', 'tests/conftest.py': '5cd472b5a859393a1d8a859fa729b507467ccc7c0de3eba5a026b7e8b86bcd6c', 'tests/test_app_mirror.py': 'd9106d493b6df28d66bc8f2a4e522ac8666a99ce4c423432ee07fbbccefad13a', 'tests/test_brand_contrast.py': '5ebfcaaa0567872ff3605a2080350d36c20d91137bc9bddc47d84611ef10d3e6', 'tests/test_button_key_names.py': 'b64f9ca2e9de121fc126b9e989e4d31761e8a7ff712f535d0380f3ebc34fa773', 'tests/test_collapse_252525.py': '53f68b4196bc803c45254e04f393528ce6bd75a5647908c4c12e3dfb22bc8583', 'tests/test_dead_error_key.py': 'bfd51f4de9b427d6752730e157c6c8c693765f6376bacf2fd49be0dfcc91ea6c', 'tests/test_derived_values.py': 'e12d725230490eeaf84183c8949620d1ff3459fac32ed7db4c6b09249cb8d76e', 'tests/test_gold_as_text.py': 'b072fb91ff5ab17c1ac11708af31891b1671767e65afd37bf77a57666f75c35b', 'tests/test_ink_on_the_golds.py': 'ccea484eec719ac04fec4ae362004ac11d6e247684fcd702a8534488cc8d6c51', 'tests/test_ink_rule.py': '1f0ca0a612610a984b824300712421ce882323c0b22fb092113d8704a8180155', 'tests/test_ladder_and_plate.py': '00e8a5f7f9ca571b2b063d1a460c090050532a985b8f3193fcb4fb6734edb147', 'tests/test_light_rewalk.py': 'd4a35be4004bf88c09b4d4491192addccf86c5ad5d1ae9a8b1ec4700c4125ba5', 'tests/test_light_wiring.py': 'fa8a339a72568ad2d92fff87597b03b090ffca4bec7cadb36347fb1f12cd5211', 'tests/test_named_and_used.py': '0f97e05b373c556ee1815880b0624470a1693ee0f36ed5f20f74b4a56dd7833c', 'tests/test_png_mark_draws.py': '6f630861ec841249dc543d806f229d8447b63f73c710f800e9e61004835ee057', 'tests/test_preview_utils.py': 'dfc7c864c77bb97ab29a5ce3f8b1295355d1168b948ac70aa5a69d76ed71ae2c', 'tests/test_register_wiring.py': '8f5bb9e38f097456fac959e3813071434e40f89fdcbc2d3775960c0370d1c6da', 'tests/test_snapshots.py': '832b29ea8de391da7715da356dcef17bd4358f32e6ddc397b4e6ab1c4294d51a', 'tests/test_status_register.py': '3c6bff9b35878ff2fe748339f9572b52e1d3197a57f35a630fc19e9fe2c9d412', 'tests/test_surface_alignment.py': '0512f2b5091b35d78de8711ad541c398858a97f4491d001f0d0917766aca8c4f', 'tests/test_watch_label_follows_a_switch.py': 'fd02506d980b3e77e6730b08a535eac3aef6bdfa8ae96483f44222e7068f2efe', 'ui/__init__.py': '99b0250edab5ca1c749cce6b882c01e7cc9ea3bc2d6b5bfa022aedcf5d9627de', 'ui/about_dialog.py': '8805087517fa5e26b8068ea2b0df567dbb2930cf14f7037649f8604e8bb83b57', 'ui/base_dialog.py': '1d1a45b43c747445cc9f509cd16d83e8dc0c7d4616e1d968fec0b644ea38b581', 'ui/context_preview.py': 'e4e81682935a3dbf7c94a0f21813940a75810e06d25609e8c412c6d4f0125da1', 'ui/ico_analyzer.py': '91f30bcc3d1e364f5c758142621930203e9a5ea163bf68252efce4b40e0855d8', 'ui/metadata_panel.py': '18d5bcd36114ea9fd3200c3480bf596ecf414b917b50787cd87c4b3075950334', 'ui/preview_utils.py': '6d146f50e0bcace7f79000798581f2c2fd5f3570a734d09551e6cea6a941837b', 'ui/settings_dialog.py': 'c161145de964badb65dcc170ad96236bc9371b10863c2df157cd4915c70ae611', 'ui/theme_manager.py': '11ffb0ff76110531372e40e995098cdbd8218c4ef4a4854f999ca6d987dd0ddb', 'utils/__init__.py': '333d1a52172d839f2d9a88ad0b3690d0926d1fa6be9be45e2b0e369ca1224852', 'utils/colors.py': '45b48346e10552aa4c4438226ae9cab3842359da446693da9f1e257d34eeb41c', 'utils/dialog_helper.py': 'dd0bc47218b20d1e76ea3962d21b493f8bf18f313531beb9fd79acfdc2c55bfa'}


def edits(tree) -> None:
    for rel, was in BASE_SHAS.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        if got != was:
            raise Stop(f"{rel} is not the head's file this round was derived from ({got[:12]}). "
                       f"Nothing was written. The file moved; re-derive before trusting the script.",
                       EXIT_CANNOT_RUN)
    for new, old in RENAMES:
        if (tree.root / new).exists():
            raise Stop(f"{new} already exists here, and this round moves {old} there. "
                       f"Nothing was written.", EXIT_CANNOT_RUN)
        text = tree.read(old)
        tree.write(new, text)
        tree.form[new] = tree.form[old]          # a moved file keeps its BOM and line endings
        tree.delete(old)
    for rel, old, new in SUBS:
        tree.sub(rel, old, new)
    for rel, body in FULL.items():
        tree.write(rel, body)                     # BASE_SHAS held the head's file
    for rel, body in NEW_FILES.items():
        if (tree.root / rel).exists():
            raise Stop(f"{rel} already exists here, and this round creates it. Nothing was written.",
                       EXIT_CANNOT_RUN)
        tree.write(rel, body)


def _checkout(tree) -> list[str]:
    """Every file in this checkout as this round leaves it: what git tracks, less
    what the round removes, and what it writes."""
    try:
        out = subprocess.run(["git", "-C", str(tree.root), "ls-files", "-z"], capture_output=True,
                             check=True).stdout.decode("utf-8")
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as e:
        raise Stop(f"git could not list this checkout's files ({e}). This round reads every one of "
                   f"them, to see that nothing is left at the old place. Nothing was written.",
                   EXIT_CANNOT_RUN)
    tracked = {rel for rel in out.split(chr(0)) if rel}
    return sorted((tracked - tree.deleted) | set(tree.files))


def _text(tree, rel: str):
    if rel in tree.files:
        return tree.files[rel]
    raw = (tree.root / rel).read_bytes()
    if b"\0" in raw:
        return None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


class _Modules:
    """Run module text as a module of this checkout, with the round's own files
    standing in for theirs: none of them is on disk yet."""

    def __init__(self, tree) -> None:
        self.tree = tree
        self.saved = {}

    def __enter__(self):
        self.added = str(self.tree.root) not in sys.path
        if self.added:
            sys.path.insert(0, str(self.tree.root))
        return self

    def load(self, rel: str, text: str, register: bool = False):
        name = rel[:-3].replace("/", ".")
        module = types.ModuleType(name)
        module.__file__ = str(self.tree.root / rel)
        if register:
            self.saved.setdefault(name, sys.modules.get(name))
            sys.modules[name] = module
        exec(compile(text, rel, "exec"), module.__dict__)
        return module

    def __exit__(self, *exc) -> None:
        for name, module in self.saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        if self.added:
            sys.path.remove(str(self.tree.root))


def _comparable(value) -> bool:
    """A value that says what it is: compared by ==, not by identity or by repr."""
    if isinstance(value, (types.ModuleType, types.FunctionType, type)) or callable(value):
        return False
    return type(value).__eq__ is not object.__eq__


def _values(module) -> dict:
    return {k: v for k, v in vars(module).items() if not k.startswith("__") and _comparable(v)}


def _class_values(module) -> dict:
    """Each class the module defines -> its own attributes that say what they are."""
    out = {}
    for k, v in vars(module).items():
        if isinstance(v, type) and v.__module__ == module.__name__:
            out[k] = {a: x for a, x in vars(v).items() if not a.startswith("__") and _comparable(x)}
    return out


def _same(a, b) -> bool:
    return type(a) is type(b) and a == b


def _reads_from_config(src: str) -> list[str]:
    """Each moved name this source reads from utils.config: imported from it, or
    read as an attribute of a name bound to it."""
    tree = ast.parse(src)
    aliases, found = set(), []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module == "utils.config":
            found += [a.name for a in n.names if a.name in MOVED]
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module == "utils":
            aliases |= {a.asname or a.name for a in n.names if a.name == "config"}
        elif isinstance(n, ast.Import):
            aliases |= {a.asname for a in n.names if a.name == "utils.config" and a.asname}
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr in MOVED:
            v = n.value
            if isinstance(v, ast.Name) and v.id in aliases:
                found.append(n.attr)
            elif (isinstance(v, ast.Attribute) and v.attr == "config" and isinstance(v.value, ast.Name)
                  and v.value.id == "utils"):
                found.append(n.attr)
    return found


#: What names the old place, in a file of any kind
OLD_PLACE_TEXT = re.compile(r"(?<![\w.])ui\.colors\b|\bfrom\s+ui\s+import\s+colors\b"
                            r"|(?<![\w./\\-])ui/colors\.py\b|([\"'])ui\1\s*/\s*([\"'])colors\.py\2")


def checks(tree) -> None:
    root_files = _checkout(tree)
    # ---- no value moves
    with _Modules(tree) as m:
        before = m.load(OLD_PLACE, _original(tree, OLD_PLACE))
        colors = m.load(COLOR_FILE, tree.read(COLOR_FILE), register=True)
        was, now = _values(before), _values(colors)
        if MOVED:
            config = m.load("utils/config.py", tree.read("utils/config.py"))
            stayed = _values(config)
            missing = sorted(set(MOVED) - set(vars(colors)))
            assert not missing, f"{COLOR_FILE} does not define {missing}"
            moved = sorted(k for k in was if not _same(was[k], (now if k in MOVED else stayed).get(k)))
            assert not moved, f"a value moved: {moved}"
            classes_was, classes_now = _class_values(before), _class_values(config)
            for cls, attrs in classes_was.items():
                gone = sorted(a for a, v in attrs.items() if not _same(v, classes_now.get(cls, {}).get(a)))
                assert not gone, f"{cls} serves other values: {gone}"
            for cls, attrs in classes_now.items():
                for a, v in attrs.items():
                    if a in MOVED and isinstance(v, dict):
                        assert v is getattr(colors, a), f"{cls}.{a} is a copy, not {COLOR_FILE}'s {a}"
            defined = sorted(t.id for n in ast.parse(tree.read("utils/config.py")).body
                             if isinstance(n, (ast.Assign, ast.AnnAssign))
                             for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
                             if isinstance(t, ast.Name) and t.id in MOVED)
            assert not defined, f"utils/config.py defines colors again: {defined}"
        else:
            assert sorted(was) == sorted(now), f"{COLOR_FILE} defines other names: {sorted(set(was) ^ set(now))}"
            moved = sorted(k for k in was if not _same(was[k], now[k]))
            assert not moved, f"a value moved: {moved}"
        assert len(was) >= 40, f"only {len(was)} values compared -- the comparison is blind"
    # ---- nothing is left at the old place, in any file of the checkout
    left, elsewhere = [], []
    for rel in root_files:
        if rel.endswith(('coverage_report.txt',)) or rel.rsplit("/", 1)[-1].upper().startswith("LICENSE"):
            continue
        text = _text(tree, rel)
        if text is None or "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
            continue
        found = []
        if MOVED:
            if rel.endswith(".py") and rel != "utils/config.py":
                found = [f"{rel}: reads {name} from utils.config" for name in _reads_from_config(text)]
        elif OLD_PLACE_TEXT.search(text):
            found = [f"{rel}: names {OLD_PLACE}"]
        (left if rel in tree.files else elsewhere).extend(found)
    if elsewhere:
        raise Stop("files this round does not write still reach the old place:\n  " + "\n  ".join(elsewhere[:20])
                   + "\nThe checkout moved; re-derive before trusting the script. Nothing was written.",
                   EXIT_CANNOT_RUN)
    assert not left, "the old place is still read:\n  " + "\n  ".join(left[:20])
    assert COLOR_FILE in root_files, f"{COLOR_FILE} is not here"
    if not MOVED:
        assert OLD_PLACE not in root_files, f"{OLD_PLACE} is still here"
    # ---- the map names the new place
    brand_map = json.loads(tree.read("brand_map.json"))
    assert brand_map["color_file"] == COLOR_FILE, brand_map["color_file"]
    for palette in brand_map.get("palettes", []):
        assert palette["file"] == COLOR_FILE, palette
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
