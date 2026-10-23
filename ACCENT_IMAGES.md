# Images that carry the accent

Written by `tools/accent_images.py` (#86 A). Do not edit by hand: after adding or changing an image, run `python tools/accent_images.py`. `tests/test_accent_images.py` fails until this file is what the tool writes.

If the accent ever moves, the code moves it in ten lines; these images do not move with it. **shaded** art is hand-made and is remade by hand (#84). **flat** art could be recolored by swapping exact colors. A **screenshot** is retaken. A **fixture** is a test input. Accent: hue within 6 degrees of `BRAND_GOLD` or `BRAND_DARK_GOLD`, saturation and value at least 0.15; an image carries it from 1% of its pixels; flat means its three commonest accent colors cover at least 90% of them. The tool's docstring says why.

**19 images of art carry the accent, 19 of them distinct.**

| folder | files | shaded | flat | screenshot | fixture | none |
|---|---|---|---|---|---|---|
| `resources/background_images` | 1 | 1 | 0 | 0 | 0 | 0 |
| `resources/button_images` | 15 | 15 | 0 | 0 | 0 | 0 |
| `resources/icons` | 3 | 3 | 0 | 0 | 0 | 0 |
| `resources/screenshots` | 6 | 0 | 0 | 6 | 0 | 0 |

## `resources/background_images`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `background.png` | 3840x2169 | 47.7% | 5042 | shaded |  |

## `resources/button_images`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `build-ico_base.png` | 834x168 | 29.1% | 2673 | shaded |  |
| `build-ico_hover.png` | 834x168 | 29.6% | 2580 | shaded |  |
| `build-ico_pressed.png` | 834x168 | 39.1% | 2787 | shaded |  |
| `clear-files_base.png` | 834x168 | 31.0% | 2286 | shaded |  |
| `clear-files_hover.png` | 834x168 | 33.3% | 2762 | shaded |  |
| `clear-files_pressed.png` | 834x168 | 42.5% | 2904 | shaded |  |
| `select-files_base.png` | 834x168 | 32.9% | 2954 | shaded |  |
| `select-files_hover.png` | 834x168 | 35.6% | 3617 | shaded |  |
| `select-files_pressed.png` | 834x168 | 40.0% | 2749 | shaded |  |
| `select-folder_base.png` | 834x168 | 33.6% | 2811 | shaded |  |
| `select-folder_hover.png` | 834x168 | 33.3% | 2470 | shaded |  |
| `select-folder_pressed.png` | 834x168 | 40.6% | 2940 | shaded |  |
| `settings_gear_base.png` | 512x512 | 93.4% | 3390 | shaded |  |
| `settings_gear_hover.png` | 512x512 | 92.9% | 2888 | shaded |  |
| `settings_gear_pressed.png` | 512x512 | 93.1% | 3418 | shaded |  |

## `resources/icons`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `app_icon.ico` | 256x256 | 81.5% | 1363 | shaded |  |
| `icon.ico` | 256x256 | 81.5% | 1363 | shaded |  |
| `icon.png` | 512x512 | 81.1% | 3602 | shaded |  |

## `resources/screenshots`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `Image-mode.png` | 1920x1080 | 7.2% | 10478 | screenshot |  |
| `context-preview.png` | 1920x1080 | 7.1% | 11622 | screenshot |  |
| `dark-mode.png` | 1920x1080 | 0.8% | 5573 | screenshot |  |
| `ico-analyzer.png` | 1920x1080 | 6.2% | 12246 | screenshot |  |
| `light-mode.png` | 1920x1080 | 2.8% | 5325 | screenshot |  |
| `settings-export.png` | 1920x1080 | 7.1% | 11411 | screenshot |  |
