# Changelog

All notable changes to RNV Icon Builder are recorded here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Earlier history, from the 3.0.0 release of 14 May 2026 back, is in the git log.

## [Unreleased]

### Changed

- **Python 3.13 is now required.** `pyproject.toml` declares `requires-python = ">=3.13"`,
  and CI runs 3.13 only, on Ubuntu and Windows. Python 3.10 to 3.12 are no longer supported.
- **Dependency ranges have upper bounds and agree everywhere.** PyQt6 is `>=6.6.0,<7.0`
  and Pillow `>=10.0.0,<13.0`, the same in `requirements.txt` and `pyproject.toml`. The
  test tools share their ranges with the other RNV applications, and `pytest-timeout` turns
  a hung test into a failure.
- **Test dependencies moved** to `tests/requirements-dev.txt`, the path every RNV repository uses.
- **Colors come from the brand, through a map.** `utils/colors.py` (moved from
  `ui/colors.py`) holds the names; `brand_map.json` says where each value comes from,
  rnv-brand or this app, and `tools/sync_colors.py` writes the values and `COLORS.md`, the
  chart of this app's colors. The `brand-sync` workflow checks rnv-brand every day and opens
  a pull request only when a color this app uses has moved.
- **rnv-brand is pinned to a commit** in `tests/requirements-dev.txt`, so the brand
  revision this app mirrors is written down and moves only by an edit.
- **Contrast and the gold.** Light mode draws gold text in a deeper derived gold where the
  standard one would fall under 4.5:1; which ink goes on a colored ground is decided by
  measured contrast; status colors come from each mode's own palette; Image mode's
  translucent panels are written as colors with alpha that Qt can read.
- **Bundled images are smaller.** The Image-mode background is 3840 px on its long edge and
  the settings gear and app icon 512 px, down from many times that.
- **Pillow 14 is prepared for.** Pixel reads go through `utils/pil_compat.py`, which uses
  `get_flattened_data()` where Pillow has it and `getdata()` where it does not.
- **CI actions** are at the versions built for the Node 24 runners (checkout v5,
  setup-python v6, upload-artifact v6).
- **American spelling** throughout the code, tests and docs.
- **Restore last session on startup starts off.** The checkbox showed checked but did
  nothing; now that it works, it is off until you turn it on, so no one's next start changes
  without asking. *Auto-save project periodically* starts on, as it showed.

### Added

- **Restore last session on startup works.** With it on, closing the app keeps the loaded
  images and the autofill and PNG compression options in `last_session.rnvicon`, and the
  next start loads them without asking. After an unexpected close, the offer to recover
  the session comes instead, and the last session is not restored. Both session settings
  are kept in `settings.json`, so they last from one start to the next.
- **Auto-save project periodically works.** With it on, an open `.rnvicon` project that has
  changed is saved to its own file every 5 minutes, the same interval as the session
  auto-save, and the status bar says *Project auto-saved*. A project never saved has no
  file, so it is not auto-saved.
- **The output filename template names the PNG set.** Export PNG Set names its files by
  the template in Settings > Export, and the preview shows the name it will write, with the
  loaded file's name for `{name}`. The default, `icon_{size}`, keeps the names it always
  wrote. A template without `{size}` gets `_{size}` added, and characters a file name cannot
  hold become `_`.
- **Metadata panel.** Beside the thumbnails, the file name, folder, file size and format of
  the size you click in the thumbnails or the size list, with its dimensions, color mode,
  bit depth and transparency.
- **A folder dropped on the window loads its images,** as Select Folder does, with its
  subfolders when *Scan subfolders when selecting folder* is checked. It used to load nothing.

- **Setup scripts.** `./in.sh` (Linux and Codespaces) installs both requirements files and
  the Qt system libraries; `.\in.ps1` (Windows) makes a Python 3.13 `.venv` if there is
  none and installs the same two files.
- **Atomic state writes.** Session recovery data, export history, presets, recent files
  and `.rnvicon` projects are written through `utils/atomic_write.py`, so a crash or a full
  disk during a save leaves the old file or the new one, never half of each.
- **Accent images list.** `ACCENT_IMAGES.md` lists every bundled image with the gold drawn
  into its pixels, written by `tools/accent_images.py`, so a gold change in the brand shows
  which images need redrawing.
- **CHANGELOG.md**, this file.
- **Guard tests** that hold rules across the repository, among them: the color file and
  `COLORS.md` match the map and the pinned brand; the installed rnv-brand is the pinned
  commit; every state file is written atomically; a status is never shown by color alone;
  `ACCENT_IMAGES.md` matches the images; `in.sh` and `in.ps1` install the same files;
  every test count in the docs is a floor that holds; images stay within their size
  budget; no test can pass without checking anything.

### Fixed

- **A normal close was offered for recovery at the next start,** once the session had been
  auto-saved: the session auto-save outlived the close. A clean close now removes it, so
  the offer comes only after an unexpected close.
- **Saving or deleting a preset in Settings closed the app.** The preset was saved or
  deleted, then refreshing the preset list raised an error and Qt aborted. Both now refresh
  the list and the app stays open.
- **Session recovery restored no files.** The session stored the file list's labels, such
  as *256x256 ✓*, instead of the files' paths, so recovering brought back only the window and
  two options. It now stores the paths, and recovering loads those files again. A session
  saved by an earlier version still recovers the window and options; what in it is not a
  file path is skipped.
- **`pip install -e .` failed** with every setuptools, because `pyproject.toml` named a build
  backend that does not exist. It names `setuptools.build_meta` and includes the two root
  modules, so the install works and adds the `rnv-icon-builder` and `rnv-icon-cli` commands.
- **A regular `pip install .` left out `resources/`,** so the installed app had no font,
  icons, button images or Image-mode background. `resources/` and its folders are now
  installed beside the code, where the app looks for them.
- **CI had no coverage floor, and its HTML coverage upload was always empty.** Both
  workflows run `python run_tests.py --html --fail-under=66`: the run fails if total
  coverage falls under 66%, and `htmlcov/` is written before it is uploaded.
- The project links in `pyproject.toml` point at `RNVizion/rnv-icon-builder`.
- **Command line:** `python cli.py --list-presets` runs with no input and no `-o`, and
  `python cli.py app.ico --analyze` without `-o`; both used to exit with a usage error.
  Preset names ignore case, so `--preset favicon` finds *Favicon* instead of reporting it
  missing and building all six sizes. A build still needs the input and `-o`.
- The ICO analyzer's PNG mark is drawn: the table's style sheet used to paint over it, so
  PNG and BMP rows looked the same.
- The Settings dialog's *Watching* label is drawn in its own mode's color, and follows a
  theme switch while the dialog is open.
- The preview background's custom-color button takes the current mode's edge color.
- Image mode's window background is translucent as intended; it had been written in a form
  Qt could not read, and was painted opaque.
- **The drop zone's text could not be read while files were dragged over the window.** The
  highlight drew black text on the dark mode tint and white text on the light mode tint. The
  text now takes the mode's own text color on the tint. In Image mode, where the tint lay
  over the background picture, the drop zone fills with the gold and takes black text, as a
  selected row does.
- In-app help: the About dialog's feature and gesture lists, and three tooltips, now match
  the app (sizes come from pixel dimensions, one shared undo history, the iOS export's
  `AppIcon.appiconset/`, `Ctrl+T` for the theme, no `Ctrl+Z`/`Ctrl+Y` bindings).
- `setup.cfg` is written for mutmut 3, so `python -m mutmut run` works.

### Removed

- Visual Studio's `.vs/` index files from the repository; `.gitignore` now keeps them out.

### Documentation

- README, TEST_SYSTEM.md and docs/INTERNALS.md were checked against the code and
  corrected: the Python version, the keyboard shortcuts and mouse gestures, the CLI
  commands and options, the exports' outputs, the project tree, the files the app keeps,
  the error-handler examples, and the mutation-testing instructions. New sections cover
  setting up for development, changing a color, the files the app keeps, and the guard
  tests. Coverage figures that drift are replaced by the command that prints them.
