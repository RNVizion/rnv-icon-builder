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

---

## Package Architecture

The project uses a three-package separation enforced by explicit `__init__.py` re-exports:

```
core/    ← Business logic, no Qt UI dependencies
ui/      ← PyQt6 widgets, dialogs, theme rendering
utils/   ← Cross-cutting concerns: config, logging, I/O helpers
```

**Directionality rules:**
- `core/` → may import from `utils/` only
- `ui/` → may import from `core/` and `utils/`
- `utils/` → no cross-package imports (leaf package)
- The main entry point `RNV_Icon_Builder.py` sits at the root and composes all three

This keeps `core/` pure enough to be invoked from the CLI (`cli.py`) without pulling in any Qt widget machinery.

---

## Application Lifecycle

The main entry point is `RNV_Icon_Builder.py:main()`. Startup proceeds in this order:

1. **Logger setup** — File + colored console handlers configured before anything else
2. **QApplication** — Fusion style applied globally for consistent cross-platform rendering
3. **Font loading** — `utils/font_loader.py` loads embedded Montserrat-Black, with graceful fallback to system fonts if the font file is missing
4. **Application icon** — Loaded from `resources/icons/icon.png` if present
5. **Main window** — `IconBuilderApp` instantiates all managers (theme, session, batch, folder watcher, etc.)
6. **Event filter** — An application-level `eventFilter` intercepts `QEvent.Type.ToolTip` to enable the custom themed tooltip system
7. **Auto-save timer** — Starts at a 5-minute interval (`AUTO_SAVE_INTERVAL_SECONDS` in config)
8. **Session recovery check** — Fired 500ms after `show()` via `QTimer.singleShot` to avoid blocking the initial paint

Shutdown (`closeEvent`) reverses this: removes the app-level event filter, hides the tooltip singleton, stops timers, cancels batch processing, clears caches, performs a clean session shutdown, and stops the folder watcher.

---

## Theme System

Three themes are supported: **Dark**, **Light**, and **Image Mode** (background image with translucent panels).

### Color Architecture

All colors are defined in `ui/colors.py`:

- `BRAND_GOLD` (`#d2bc93`) — Primary brand accent
- `BRAND_GOLD_DARK` (`#b19145`) — Pressed states, borders
- `DARK_THEME_COLORS` / `LIGHT_THEME_COLORS` / `IMAGE_MODE_COLORS` — Dictionaries keyed by semantic role (`window_bg`, `panel_bg`, `text_primary`, `button_hover_bg`, etc.)

The `get_theme_colors(is_dark: bool)` helper returns the appropriate dict for dialogs.

### Two Button Systems

The project deliberately uses two separate button color schemes:

- **Main window buttons** — Neutral inverse monochrome hover system. No brand gold. Dark mode hover: `#333333` background, text unchanged.
- **Dialog buttons** — Gold accent system. Hover reveals `BRAND_GOLD` borders/text.

This is intentional — main window buttons sit against backgrounds where gold hover would be visually loud, while dialog buttons benefit from the accent. See `ui/colors.py` for the `main_btn_*` vs `button_*` key split.

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

- **Small sizes (≤ 48px)** — Always BMP encoded with an AND mask for transparency
- **Large sizes (256, 128, 64)** — PNG encoded by default (`png_compression=True`). This is the "modern" ICO format, supported since Windows Vista, and produces significantly smaller files.

The user can override per-export via the PNG Compression checkbox.

### Other Export Formats

The same module exports:

- **ICNS** — macOS icon format (custom binary writer)
- **Favicon Package** — ICO + PNGs + `site.webmanifest` JSON
- **Android** — Mipmap folder structure (mdpi through xxxhdpi)
- **iOS** — `Assets.xcassets` with `Contents.json` manifest

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

---

## Data Persistence & Format Versioning

Application version and data format versions are tracked **independently**:

- **`APP_VERSION`** (defined in `utils/config.py`) — The single source of truth for the application version. All runtime references (`__init__.py`, `cli.py --version`, `about_dialog.py`) import this value.
- **Data format versions** — Each persistent JSON format tracks its own version for backward compatibility:
  - `.rnvicon` project files: version `2.11`
  - `recent_files.json`: version `2.6`
  - `presets.json`: version `2.11`

Data format versions only bump when the file schema changes in a way that requires migration logic.

### Storage Locations

User data lives outside the install directory under `~/.rnv_icon_builder/`:

```
~/.rnv_icon_builder/
├── logs/                    # Rotating log files
├── sessions/                # Session snapshots
├── cache/                   # Thumbnail cache
├── presets/                 # User-defined size presets
├── projects/                # User-saved .rnvicon files (default)
├── autosave.rnvicon         # Current auto-save
├── last_session.rnvicon     # Last clean-shutdown state
├── settings.json            # App settings
├── watch_config.json        # Folder watcher config
├── recent_files.json        # Recent files/folders history
└── presets.json             # Preset registry
```

---

## Image Processing Pipeline

`core/image_processor.py` is the central image container. Key concepts:

### Detected Images

`detected_images: dict[int, Image.Image]` — A dictionary keyed by target size. Each value is a PIL `Image` in RGBA mode.

### Adjustment Application

Transforms and color adjustments in `ui/image_adjustments.py` are pure functions: `(image, params) → new_image`. The `ImageProcessor` calls these and replaces entries in `detected_images`.

A combined adjustment function (`apply_combined_adjustments`) applies brightness + contrast + saturation in a single pass when all three are non-default, avoiding three separate PIL `Image.Enhance` round-trips.

### Undo/Redo

Each size slot maintains its own undo stack (default capacity 20 states, defined in config). When an adjustment is applied, the pre-state is pushed to the per-size stack. Redo follows the standard stack-based pattern.

`Image.MAX_IMAGE_PIXELS = None` is set at module import to suppress Pillow's `DecompressionBombWarning` — legitimate 256×256 icon sources occasionally come from larger source art.

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

String constants for semantic error grouping: `FILE_IO`, `IMAGE_PROCESSING`, `VALIDATION`, `UI`, `SYSTEM`, etc. Used for log filtering and user-facing messages.

### `ErrorHandler`

Static methods for common patterns:
- `show_error(parent, message, category)` — Themed error dialog
- `confirm_action(parent, title, message, default_yes)` — Themed confirmation dialog
- Handlers integrate with `DialogHelper` for consistent theming

### `safe_method` Decorator

Wraps class methods in a try/except that logs the exception and shows a user-facing error dialog, keeping the app stable when non-critical operations fail.

### `exception_handler` Context Manager

Same idea, but as a `with` block:

```python
with exception_handler("Loading config", category=ErrorCategory.FILE_IO):
    load_config()
```

---

## Logging

`utils/logger.py` wraps the stdlib `logging` module:

### Features

- **Colored console output** — ANSI codes with auto-detection for Windows Terminal, VS Code, and Unix terminals
- **Rotating file handler** — Size-capped at `LOG_FILE_MAX_SIZE` with `LOG_FILE_BACKUP_COUNT` backups
- **Module name shortening** — `core.image_processor` → `ImageProcessor` in console output
- **Symbol-prefixed methods** — `logger.success()`, `logger.failure()`, `logger.warning_symbol()` prepend ✓ / ✗ / ⚠ for quick scanning

### Logger Class Wrapper

The `Logger` class wraps `logging.Logger` with a cleaner API (`logger.success()`, `logger.exception()`, `logger.header()`, `logger.separator()`). Each module obtains its own instance via `get_logger_instance(__name__)`.

---

## Caching Strategy

`utils/pixmap_cache.py` provides three layered caches:

### `QPixmapCache`

LRU cache for arbitrary `QPixmap` objects. Default capacity defined by `THUMBNAIL_CACHE_MAX_SIZE` in config (50 entries).

### `ImagePixmapCache`

Subclass keyed by `(source_path, mtime)` to invalidate automatically when a source file changes on disk.

### `ThumbnailCache`

Subclass for thumbnail-specific caching, keyed by `(source_path, size, variant)` where `variant` encodes background style (checkerboard, white, custom color, etc.).

---

## Testing

`test_rnv_icon_builder.py` runs without a display server (`QT_QPA_PLATFORM=offscreen`). 471 tests across 24 classes.

### Coverage

- Core modules: `icon_builder_core`, `image_processor`, `batch_processor`, `folder_watcher`, `preset_manager`, `project_manager`, `recent_files`, `session_manager`, `export_history`
- UI modules: `colors`, `preview_utils`, `image_adjustments`
- Utils: `config`, `logger`, `error_handler`, `file_utils`, `signal_manager`, `pixmap_cache`, `dialog_helper`

### Mocking

Tests patch file-system-touching methods on `RecentFilesManager`, `ExportHistory`, and `SessionManager` to avoid writing to `~/.rnv_icon_builder/` during test runs.

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
- **`settings_dialog.py` size** — At ~2,700 lines, it's the largest UI file. Kept monolithic for the same coupling reasons — the tabs share state extensively.
