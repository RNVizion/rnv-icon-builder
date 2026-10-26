# RNV Icon Builder — Internals

Architectural reference for developers working on or extending the codebase. For end-user documentation, see the [README](../README.md).

---

## Table of Contents

1. [Package Architecture](#package-architecture)
2. [Application Lifecycle](#application-lifecycle)
3. [Theme System](#theme-system)
4. [ICO File Format Implementation](#ico-file-format-implementation)
5. [Project File Format (`.rnvicon`)](#project-file-format-rnvicon)
6. [Data Persistence & Format Versioning](#data-persistence--format-versioning)
7. [Image Processing Pipeline](#image-processing-pipeline)
8. [Signal Management](#signal-management)
9. [Error Handling](#error-handling)
10. [Logging](#logging)
11. [Caching Strategy](#caching-strategy)
12. [Testing](#testing)
13. [Notable Design Decisions](#notable-design-decisions)

---

## Package Architecture

The project is split into three packages, each with an `__init__.py` that re-exports its public names:

```
core/    ← Business logic: no widgets, but Qt signals, timers and SVG rendering
ui/      ← PyQt6 widgets, dialogs, theme rendering
utils/   ← Cross-cutting concerns: config, logging, I/O helpers
```

**How they import each other today** (a convention, not something a test enforces):
- `core/` imports from `utils/`, and `core/image_processor.py` imports the transforms in `ui/image_adjustments.py` inside the methods that use them (which loads the whole `ui` package the first time)
- `ui/` imports from `core/` and `utils/`
- `utils/` imports nothing from `core/` or `ui/`; `utils/error_handler.py` and `utils/dialog_helper.py` use QtWidgets message boxes
- The main entry point `RNV_Icon_Builder.py` sits at the root and composes all three

The CLI (`cli.py`) imports `core/` and `utils/`, so it loads PyQt6, QtWidgets included, but it creates no window.

---

## Application Lifecycle

The main entry point is `RNV_Icon_Builder.py:main()`. Startup proceeds in this order:

1. **Logger setup** — File + colored console handlers configured before anything else
2. **QApplication** — Fusion style applied globally for consistent cross-platform rendering
3. **Font loading** — `utils/font_loader.py` loads embedded Montserrat-Black, with graceful fallback to system fonts if the font file is missing
4. **Application icon** — Loaded from `resources/icons/icon.png` if present
5. **Main window** — `IconBuilderApp` instantiates all managers (theme, session, batch, folder watcher, etc.), reads the two session settings from `settings.json`, and builds the widgets and shortcuts
6. **Auto-save timers** — The session auto-save starts at a 5-minute interval (`AUTO_SAVE_INTERVAL_SECONDS` in config). With *Auto-save project periodically* on, the project auto-save runs on the same interval: it writes the open `.rnvicon` project to its own file when its images or options differ from what was last saved or loaded, and skips a project that has never been saved
7. **Session check** — Scheduled with `QTimer.singleShot(500, ...)` at the end of construction, so it runs after `show()` and the first paint. After a crash it offers to recover the session auto-save, and that is all it does. Otherwise, with *Restore last session on startup* on, it loads `last_session.rnvicon` without asking
8. **Event filter** — An application-level `eventFilter` intercepts `QEvent.Type.ToolTip` to enable the custom themed tooltip system
9. **Show** — `main()` calls `window.show()` and starts the event loop

Shutdown (`closeEvent`) reverses this: removes the app-level event filter, hides the tooltip singleton, keeps the loaded images and options in `last_session.rnvicon` when *Restore last session on startup* is on (and removes that file otherwise, or when nothing is loaded), stops timers, cancels batch processing, clears caches, performs a clean session shutdown, which removes the session auto-save and the recovery flag, and stops the folder watcher.

---

## Theme System

Three themes are supported: **Dark**, **Light**, and **Image Mode** (background image with translucent panels).

### Color Architecture

All colors are named in `utils/colors.py`. Their values are written there by `tools/sync_colors.py`, from `brand_map.json` and the pinned rnv-brand; `COLORS.md` charts every one (see *Changing a color* in the [README](../README.md#changing-a-color)).

- `BRAND_GOLD` — Primary brand accent
- `BRAND_DARK_GOLD` — Light-mode gold FILLS: pressed states, borders, selections. Carries white text.
- `BRAND_DARK_GOLD_DEEP` (derived) — Light-mode gold TEXT. `BRAND_DARK_GOLD`
  clears 4.5:1 as text only against pure white, so gold text on any gray
  surface uses this instead. Computed from `BRAND_DARK_GOLD` with
  `lighten()`, never written down.
- `DARK_THEME_COLORS` / `LIGHT_THEME_COLORS` / `IMAGE_MODE_COLORS` — Dictionaries keyed by semantic role (`window_bg`, `panel_bg`, `text_primary`, `dialog_btn_hover_bg`, etc.)

The `get_theme_colors(is_dark=True, is_image_mode=False)` helper returns the appropriate dict for dialogs.

### Two Button Systems

The project deliberately uses two separate button color schemes:

- **Main window buttons** — Neutral inverse monochrome hover system. No brand gold. The hover background is `main_btn_hover_bg`; the text is unchanged.
- **Dialog buttons** — Gold accent system. Hover reveals `BRAND_GOLD` borders/text in dark mode.

This is intentional — main window buttons sit against backgrounds where gold hover would be visually loud, while dialog buttons benefit from the accent. See `utils/colors.py` for the `main_btn_*` vs `dialog_btn_*` key split.

### Palette vs Stylesheet

Theme application happens in two layers:

1. **`QPalette`** — Set via `_apply_palette()` / `_apply_image_mode_palette()`. Critical for Fusion style's checkbox, selection, and input rendering. Must set both `QPalette.Highlight` and `QPalette.HighlightedText` roles.
2. **Stylesheet** — Applied via `_apply_main_stylesheet()` for everything else.

### Custom Tooltip System

Native Qt tooltips on Windows create an OS-level popup window that ignores CSS `border-radius`. To get pixel-perfect themed tooltips, the app:

1. Defines `_ThemedToolTip` — a frameless `QLabel` with `WA_TranslucentBackground`
2. Paints its own rounded-rect background in `paintEvent` using `QPainter`
3. Installs an application-level `eventFilter` that catches `QEvent.Type.ToolTip` events
4. Renders the custom tooltip singleton at the event position

The hover-zoom HTML preview on thumbnails uses native `QToolTip.showText()` separately, since that content is HTML-rich and benefits from the native renderer.

---

## ICO File Format Implementation

`core/icon_builder_core.py` contains a custom ICO encoder that writes the binary format directly rather than delegating to Pillow. This gives precise control over PNG compression flags and BMP encoding.

### File Structure

```
[ICONDIR header — 6 bytes]
[ICONDIRENTRY × N — 16 bytes each]
[Image data × N — BMP or PNG encoded]
```

### Key Constants (from `utils/config.py`)

- `ICO_HEADER_SIZE = 6` — ICONDIR header
- `ICO_DIR_ENTRY_SIZE = 16` — Per-image directory entry
- `BMP_HEADER_SIZE = 40` — BITMAPINFOHEADER
- `BITS_PER_PIXEL = 32` — BGRA
- `BYTES_PER_PIXEL = 4`
- `COLOR_PLANES = 1`

### Encoding Strategy

For each image size:

- **256 and 128 px** — PNG encoded by default (`use_png_compression=True`). This is the "modern" ICO format, supported since Windows Vista, and produces significantly smaller files.
- **64 px and smaller** — Always BMP encoded (32-bit BGRA) with an AND mask for transparency

The user can override per-export via the *Use PNG compression* checkbox; with it off, every size is BMP.

### Other Export Formats

The same module exports:

- **ICNS** — macOS icon format (custom binary writer)
- **Favicon Package** — `favicon.ico` (16, 32, 48), `favicon-16x16.png`, `favicon-32x32.png`, `apple-touch-icon.png`, `android-chrome-192x192.png`, `android-chrome-512x512.png`, `site.webmanifest`, `browserconfig.xml` and `mstile-150x150.png`
- **Android** — `res/mipmap-<density>/ic_launcher.png` (mdpi through xxxhdpi)
- **iOS** — `AppIcon.appiconset/` with a `Contents.json` manifest

The PNG set is written by the main window (`export_png_set`), one file per selected size. Its names come from `FileUtils.render_filename_template()` (`utils/file_utils.py`), with the template from Settings > Export; the Settings preview calls the same function, so it shows the name the export writes. `{name}` is the base name of the file the largest loaded size came from (`icon` when there is none). The template names nothing else: the ICO and `.icns` names are chosen in a save dialog, the platform exports use the names their platforms expect, batch and watch-folder ICOs are named after their source, and ICO extraction after the ICO and each frame's size.

`cli.py` has its own favicon and Android writers: its favicon package is `favicon.ico`, three PNGs (16, 32, 48), `site.webmanifest` and `favicon-html.txt`, and its Android export adds `ic_launcher_round.png` beside each `ic_launcher.png`, without the `res/` folder.

---

## Project File Format (`.rnvicon`)

Defined in `core/project_manager.py`. A project file is a JSON document with the following structure:

```json
{
  "name": "My Project",
  "version": "2.11",
  "settings": {
    "selected_sizes": [256, 128, 64, 48, 32, 16],
    "autofill": true,
    "png_compression": true,
    "preset_name": ""
  },
  "images": {
    "256": {
      "size": 256,
      "source_path": "/path/to/original.png",
      "embedded_data": "<base64 PNG>",
      "is_embedded": true,
      "is_autofilled": false
    }
  },
  "created": "2026-01-15T10:30:00",
  "modified": "2026-01-15T14:22:00"
}
```

### Embedded vs Referenced Images

When `is_embedded = true`, the full PNG bytes are base64-encoded in `embedded_data`. This makes project files portable but larger. When false, only `source_path` is stored and images are loaded on open.

Default is embedded, for portability.

The app also records each loaded size's `source_path`, the file it came from, when there is one. Loading a project uses it to show that file in the metadata panel and as the filename template's `{name}`. A project saved before has empty paths and loads as before.

---

## Data Persistence & Format Versioning

Application version and data format versions are tracked **independently**:

- **`APP_VERSION`** (defined in `utils/config.py`) — The application version as the app reports it. All runtime references (`__init__.py`, `cli.py --version`, `about_dialog.py`) import this value. `pyproject.toml` states the same version separately, for packaging, so a version bump changes both.
- **Data format versions** — Each persistent JSON format tracks its own version for backward compatibility:
  - `.rnvicon` project files: version `2.11`
  - `recent_files.json`: version `2.6`
  - `presets.json`: version `2.11`

Data format versions only bump when the file schema changes in a way that requires migration logic.

### Storage Locations

User data lives outside the install directory under `~/.rnv_icon_builder/`:

```
~/.rnv_icon_builder/
├── logs/                    # Rotating log files (icon_builder_YYYYMMDD.log)
├── sessions/
│   ├── autosave.json        # The session auto-save, used for crash recovery; a clean shutdown removes it
│   └── .recovery_needed     # Present while the app runs; a clean shutdown removes it
├── settings.json            # The session settings: restore_session and auto_save
├── last_session.rnvicon     # The session kept at close for "Restore last session on startup"
├── recent_files.json        # Recent files/folders history
├── presets.json             # Custom size presets (the built-ins are in code)
└── export_history.json      # Log of ICO builds, shown on the Info tab
```

`utils/config.py` also creates empty `cache/`, `presets/` and `projects/` folders there when it is imported. `.rnvicon` projects are saved wherever the user chooses.

The JSON files, the last session and the recovery flag are written through `utils/atomic_write.py` (see *Files the app keeps* in the [README](../README.md#files-the-app-keeps)).

---

## Image Processing Pipeline

`core/image_processor.py` is the central image container. Key concepts:

### Detected Images

`detected_images: dict[int, Image.Image]` — A dictionary keyed by target size. Each value is a PIL `Image`. A size comes from the image's pixel dimensions: a square PNG whose width is a standard size, each standard-size frame of an ICO, or an SVG rendered at every standard size. Nothing reads sizes from filenames.

### Adjustment Application

Transforms and color adjustments in `ui/image_adjustments.py` are pure functions: `(image, params) → new_image`. The `ImageProcessor` calls these on every loaded size and replaces the entries in `detected_images`.

The color sliders go through one function, `apply_combined_adjustments`, whenever any of brightness, contrast or saturation is non-zero. It splits off the alpha channel once, applies each non-zero `ImageEnhance` step to the same RGB image, and merges the alpha back once.

### Undo/Redo

`ImageProcessor` keeps one undo stack and one redo stack for all sizes (`MAX_UNDO_STATES = 20`, in `core/image_processor.py`). Before an adjustment, a copy of every loaded size is pushed as one state; the oldest state is dropped past 20. A new adjustment clears the redo stack.

Pillow's `Image.MAX_IMAGE_PIXELS` is left at its default for user images. `ui/theme_manager.py` raises it to `MAX_IMAGE_PIXELS` from config only while it loads the Image-mode background, then restores it.

---

## Signal Management

`utils/signal_manager.py` provides three tools for Qt signal lifecycle:

### `SignalConnectionManager`

Tracks connections in a `dict[widget_id, list[ConnectionInfo]]`. On widget cleanup, `disconnect_widget(widget)` removes every connection made via this manager — no more orphaned signals firing on deleted Qt objects.

### `SignalMixin`

Adds `track_connection(widget, signal, slot)` and `disconnect_all_signals()` methods to any class. Used by every `BaseDialog` subclass.

### `WindowMoveMixin`

Mitigates a specific Windows compositor bug: `setUpdatesEnabled(False)` during move events causes blank-screen glitches when `show()` triggers `moveEvent` before child widgets paint. This mixin replaces that pattern with a `repaint()` after drag ends.

**Related constraint:** `setFixedSize()` causes related compositor issues during window drag. Use `setMinimumSize()` + `setMaximumSize()` instead.

---

## Error Handling

`utils/error_handler.py` centralizes all error reporting:

### `ErrorCategory`

String constants for semantic error grouping: `FILE_IO`, `IMAGE_PROCESSING`, `VALIDATION`, `PERMISSION`, `NETWORK`, `UNKNOWN`, `USER_CANCELLED` and `RESOURCE`. Used for log messages and the suggestion shown in error dialogs.

### `ErrorHandler`

Static methods for common patterns:
- `safe_execute(func, operation_name, args=(), kwargs=None, default_return=None, show_error_dialog=False, parent_widget=None, error_category=ErrorCategory.UNKNOWN, critical=False)` — Runs `func` and returns `(success, result)`; on an exception it logs it, optionally shows a dialog, and returns `(False, default_return)`
- `show_error_dialog(parent, title, message, details="", critical=False)` — Themed error dialog
- `confirm_action(parent, title, message, details="", default_yes=False)` — Themed confirmation dialog
- Handlers integrate with `DialogHelper` for consistent theming

```python
import json
from utils.error_handler import ErrorHandler, ErrorCategory, exception_handler, safe_method

success, data = ErrorHandler.safe_execute(
    func=json.loads,
    operation_name="Reading a preset file",
    args=('{"sizes": [256, 48]}',),
    error_category=ErrorCategory.FILE_IO,
)
# (True, {'sizes': [256, 48]}); with "not json" instead: (False, None), and the error is logged
```

In a widget, pass `show_error_dialog=True, parent_widget=self` to show the themed dialog as well.

### `safe_method` Decorator

`safe_method(operation_name=None, show_error=False, default_return=None, critical=False)` wraps a method in `safe_execute`: the exception is logged and the method returns `default_return`. It shows an error dialog only with `show_error=True`, parented to `self` when `self` is a widget.

```python
class Loader:
    @safe_method(operation_name="Loading presets", default_return=[])
    def load(self):
        raise OSError("disk gone")

Loader().load()   # logs the error and returns []
```

### `exception_handler` Context Manager

Same idea, but as a `with` block. The signature is `exception_handler(operation_name, parent=None, show_error=True, critical=False)`. It logs the exception under `ErrorCategory.UNKNOWN`, shows a dialog if `show_error` is true, and suppresses the exception:

```python
with exception_handler("Loading config", show_error=False):
    json.loads("not json")   # logged, then suppressed; the code after the block runs
```

---

## Logging

`utils/logger.py` wraps the stdlib `logging` module:

### Features

- **Colored console output** — ANSI codes with auto-detection for Windows Terminal, VS Code, and Unix terminals
- **Rotating file handler** — `setup_logger()` writes `~/.rnv_icon_builder/logs/icon_builder_YYYYMMDD.log`, size-capped at 5 MB with 3 backups (the same values as `LOG_FILE_MAX_SIZE` and `LOG_FILE_BACKUP_COUNT` in config)
- **Module name shortening** — `core.image_processor` → `ImageProcessor` in console output
- **Symbol-prefixed messages** — `logger.success()` prepends `+`, which the formatters show as a SUCCESS level. The older module functions `log_success()`, `log_failure()` and `log_warning_symbol()` prepend `+`, `X` and `!`.

### Logger Class Wrapper

The `Logger` class wraps `logging.Logger` with a cleaner API: `debug()`, `info()`, `success()`, `warning()`, `error()`, `exception()`, `critical()`, `header()`, `separator()`, `blank()` and `indent()`. Each module obtains its own instance via `get_logger_instance(__name__)`.

---

## Caching Strategy

`utils/pixmap_cache.py` provides three layered caches:

### `QPixmapCache`

LRU cache for arbitrary `QPixmap` objects, keyed by any tuple. Default capacity 15 entries; it keeps hit, miss and eviction counts.

### `ImagePixmapCache`

Subclass for one image at several zoom levels or sizes, keyed by `(image_path, zoom_level, image_size)` or `(image_path, "size", target_size)`. `set_current_image()` clears it when a different path is set, and `invalidate_image()` drops one path's entries. It does not look at file times.

### `ThumbnailCache`

Subclass for thumbnails, keyed by `(source_path, size, variant)`; default capacity 50. `ui/preview_utils.py` holds one, sized by `THUMBNAIL_CACHE_MAX_SIZE` (50), behind `get_cached_thumbnail()`, where the variant gains a `_checker` suffix when the thumbnail is drawn on the checkerboard. The main window draws its preview thumbnails directly and clears this cache whenever it clears the preview.

---

## Testing

The test system as a whole — both suites, the runner, coverage, mutation testing and the guard tests — is described in [TEST_SYSTEM.md](../TEST_SYSTEM.md). This section covers the root unittest suite.

`test_rnv_icon_builder.py` runs without a display server (`QT_QPA_PLATFORM=offscreen`). Over 400 tests.

### Modules it tests

- Core modules: `icon_builder_core`, `image_processor`, `batch_processor`, `folder_watcher`, `preset_manager`, `project_manager`, `recent_files`, `session_manager`, `export_history`
- UI modules: `theme_manager`, `preview_utils`, `image_adjustments`
- Utils: `colors`, `config`, `logger`, `error_handler`, `file_utils`, `pixmap_cache`, `dialog_helper`

### Mocking

At import, the file replaces `RecentFilesManager._load` / `_save`, `ExportHistory._load_history` / `_save_history` / `_ensure_directory`, and `SessionManager._ensure_directory` with no-ops, so the suite does not touch the history files in `~/.rnv_icon_builder/`.

### Running

```bash
python test_rnv_icon_builder.py         # Standard
python test_rnv_icon_builder.py -v      # Verbose
```

---

## Notable Design Decisions

- **Flat test bootstrap** — The test file supports both flat (single-dir) and subdirectory (core/ui/utils) project layouts via a runtime import shim. This lets the tests run during refactoring without breaking.
- **No settings dialog lazy loading** — Previously attempted and reverted; lazy tab loading caused `RuntimeError` on deleted Qt objects. All tabs instantiate eagerly.
- **Monolithic `config.py`** — Splitting was attempted (as Phase 3.3) and reverted. Tight coupling between constants made the split create more import complexity than it saved.
- **`settings_dialog.py` size** — It is the largest UI file. Kept monolithic for the same coupling reasons — the tabs share state extensively.
