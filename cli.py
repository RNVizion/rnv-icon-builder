#!/usr/bin/env python3
"""
RNV Icon Builder - Command-Line Interface
Provides CLI access to icon building functionality for automation.

Features:
- Build ICO files from PNG/ICO/SVG sources
- Use presets or custom size selections
- Batch processing of multiple files/folders
- Platform-specific exports (favicon, Android, iOS)
- PNG compression options

Usage examples:
    python cli.py input.png -o output.ico --sizes 256,48,32,16
    python cli.py input.png -o output.ico --preset favicon
    python cli.py folder/ -o icons/ --batch
    python cli.py input.png --favicon-package -o web/
"""

from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path
from typing import Any

# Add parent directory to path for imports when running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image

# Import core modules
from core.icon_builder_core import IconBuilderCore
from core.image_processor import ImageProcessor
from core.preset_manager import get_preset_manager, SizePreset
from utils.config import ICON_SIZES, SUPPORTED_EXTENSIONS, APP_VERSION
from utils.file_utils import FileUtils
from utils.logger import Logger, get_logger_instance

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)


# ==================== Constants ====================

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_INVALID_ARGS = 2

# Platform export configurations
FAVICON_SIZES = [16, 32, 48]
ANDROID_SIZES = {
    'mdpi': 48,
    'hdpi': 72,
    'xhdpi': 96,
    'xxhdpi': 144,
    'xxxhdpi': 192
}
IOS_SIZES = [20, 29, 40, 58, 60, 76, 80, 87, 120, 152, 167, 180, 1024]


# ==================== CLI Functions ====================

def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog='rnv-icon-builder',
        description='RNV Icon Builder - Create multi-resolution ICO files and platform icons',
        epilog='Examples:\n'
               '  %(prog)s logo.png -o icon.ico\n'
               '  %(prog)s logo.png -o icon.ico --sizes 256,48,32,16\n'
               '  %(prog)s logo.png -o icon.ico --preset favicon\n'
               '  %(prog)s images/ -o icons/ --batch\n'
               '  %(prog)s logo.png --favicon-package -o web/\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Positional arguments
    parser.add_argument(
        'input',
        type=str,
        help='Input file (PNG, ICO, SVG) or folder for batch mode'
    )
    
    # Output options
    parser.add_argument(
        '-o', '--output',
        type=str,
        required=True,
        help='Output file path (for single file) or folder (for batch/platform exports)'
    )
    
    # Size options (mutually exclusive group)
    size_group = parser.add_mutually_exclusive_group()
    size_group.add_argument(
        '--sizes',
        type=str,
        help='Comma-separated list of sizes (e.g., 256,48,32,16)'
    )
    size_group.add_argument(
        '--preset',
        type=str,
        help='Use a named preset (e.g., favicon, windows, macos, all)'
    )
    
    # Processing options
    parser.add_argument(
        '--autofill', '--auto-fill',
        action='store_true',
        default=True,
        help='Auto-fill missing smaller sizes from largest image (default: enabled)'
    )
    parser.add_argument(
        '--no-autofill', '--no-auto-fill',
        action='store_true',
        help='Disable auto-fill of missing sizes'
    )
    parser.add_argument(
        '--png-compression',
        action='store_true',
        default=True,
        help='Use PNG compression for 256x256 and 128x128 (default: enabled)'
    )
    parser.add_argument(
        '--no-png-compression',
        action='store_true',
        help='Disable PNG compression (use BMP for all sizes)'
    )
    
    # Mode options
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Batch mode: process all images in input folder'
    )
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Recursively scan subfolders in batch mode'
    )
    
    # Platform export options
    platform_group = parser.add_mutually_exclusive_group()
    platform_group.add_argument(
        '--favicon-package',
        action='store_true',
        help='Export favicon package (16, 32, 48 PNGs + ICO + manifest)'
    )
    platform_group.add_argument(
        '--android',
        action='store_true',
        help='Export Android icon set (mdpi through xxxhdpi)'
    )
    platform_group.add_argument(
        '--ios',
        action='store_true',
        help='Export iOS App Icon set with Contents.json'
    )
    
    # Utility options
    parser.add_argument(
        '--list-presets',
        action='store_true',
        help='List all available presets and exit'
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze an existing ICO file and show its contents'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress all output except errors'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {APP_VERSION}'
    )
    
    return parser


def print_msg(message: str, verbose: bool = False, quiet: bool = False, is_error: bool = False) -> None:
    """
    Print a message respecting verbose/quiet flags.
    
    Also routes errors and warnings to the logger for persistent tracking.
    
    Args:
        message: Message to print
        verbose: Only print if verbose is True
        quiet: Don't print if quiet is True (unless is_error)
        is_error: Always print errors, print to stderr
    """
    if is_error:
        logger.error(f"CLI: {message}")
        print(f"Error: {message}", file=sys.stderr)
    elif not quiet and (not verbose or verbose):
        print(message)


def list_presets(quiet: bool = False) -> int:
    """
    List all available presets.
    
    Args:
        quiet: Suppress output
        
    Returns:
        Exit code
    """
    if quiet:
        return EXIT_SUCCESS
    
    preset_manager = get_preset_manager()
    presets = preset_manager.list_presets()
    
    print("\nAvailable Presets:")
    print("-" * 50)
    
    for preset in presets:
        builtin = " (built-in)" if preset.is_builtin else ""
        sizes_str = ", ".join(str(s) for s in sorted(preset.sizes, reverse=True))
        print(f"\n  {preset.name}{builtin}")
        print(f"    Sizes: {sizes_str}")
        if preset.description:
            print(f"    Description: {preset.description}")
        print(f"    Autofill: {'Yes' if preset.autofill else 'No'}")
        print(f"    PNG Compression: {'Yes' if preset.png_compression else 'No'}")
    
    print("\n" + "-" * 50)
    print(f"Total: {len(presets)} presets")
    
    return EXIT_SUCCESS


def analyze_ico(file_path: str, quiet: bool = False) -> int:
    """
    Analyze an ICO file and display its contents.
    
    Args:
        file_path: Path to ICO file
        quiet: Suppress output
        
    Returns:
        Exit code
    """
    if not FileUtils.validate_file_path(file_path, must_exist=True):
        print_msg(f"File not found: {file_path}", is_error=True)
        return EXIT_ERROR
    
    if not file_path.lower().endswith('.ico'):
        print_msg(f"Not an ICO file: {file_path}", is_error=True)
        return EXIT_ERROR
    
    info = IconBuilderCore.get_ico_info(file_path)
    
    if not info or not info.get('valid', False):
        error = info.get('error', 'Unknown error') if info else 'Failed to read file'
        print_msg(f"Invalid ICO file: {error}", is_error=True)
        return EXIT_ERROR
    
    if quiet:
        return EXIT_SUCCESS
    
    print(f"\nICO File Analysis: {info['file_name']}")
    print("-" * 50)
    print(f"  File Size: {info['file_size']:,} bytes")
    print(f"  Images: {info['image_count']}")
    print(f"  Sizes: {', '.join(info['sizes'])}")
    
    compression = []
    if info.get('has_png'):
        compression.append("PNG")
    if info.get('has_bmp'):
        compression.append("BMP")
    print(f"  Compression: {' + '.join(compression) if compression else 'Unknown'}")
    
    print("\n  Image Details:")
    for img in info.get('images', []):
        comp = img.get('compression', 'Unknown')
        bpp = img.get('bits_per_pixel', 0)
        size_bytes = img.get('bytes', 0)
        print(f"    {img['width']}x{img['height']}: {comp}, {bpp}-bit, {size_bytes:,} bytes")
    
    print("-" * 50)
    
    return EXIT_SUCCESS


def get_sizes_from_args(args: argparse.Namespace) -> list[int]:
    """
    Determine which sizes to use based on arguments.
    
    Args:
        args: Parsed arguments
        
    Returns:
        List of sizes to include
    """
    if args.sizes:
        # Parse comma-separated sizes
        try:
            sizes = [int(s.strip()) for s in args.sizes.split(',')]
            # Validate sizes
            for size in sizes:
                if size not in ICON_SIZES and size not in IOS_SIZES:
                    print_msg(f"Warning: Size {size} is not a standard icon size", is_error=False)
            return sorted(sizes, reverse=True)
        except ValueError as e:
            print_msg(f"Invalid sizes format: {args.sizes}", is_error=True)
            return ICON_SIZES
    
    elif args.preset:
        # Load from preset
        preset_manager = get_preset_manager()
        preset = preset_manager.get_preset(args.preset)
        if preset:
            return list(preset.sizes)
        else:
            print_msg(f"Preset not found: {args.preset}. Using default sizes.", is_error=True)
            return ICON_SIZES
    
    else:
        # Default to all sizes
        return ICON_SIZES


def load_source_image(input_path: str, verbose: bool = False, quiet: bool = False) -> ImageProcessor | None:
    """
    Load source image(s) from input path.
    
    Args:
        input_path: Path to source file
        verbose: Enable verbose output
        quiet: Suppress output
        
    Returns:
        ImageProcessor with loaded images, or None on error
    """
    processor = ImageProcessor()
    
    ext = os.path.splitext(input_path)[1].lower()
    
    if ext == '.png':
        if processor.load_png(input_path):
            print_msg(f"Loaded PNG: {input_path}", verbose=verbose, quiet=quiet)
        else:
            print_msg(f"Failed to load PNG: {input_path}", is_error=True)
            return None
    
    elif ext == '.ico':
        count = processor.load_ico(input_path)
        if count > 0:
            print_msg(f"Loaded {count} size(s) from ICO: {input_path}", verbose=verbose, quiet=quiet)
        else:
            print_msg(f"Failed to load ICO: {input_path}", is_error=True)
            return None
    
    elif ext == '.svg':
        count = processor.load_svg(input_path)
        if count > 0:
            print_msg(f"Rendered {count} size(s) from SVG: {input_path}", verbose=verbose, quiet=quiet)
        else:
            print_msg(f"Failed to render SVG: {input_path}", is_error=True)
            return None
    
    else:
        print_msg(f"Unsupported file format: {ext}", is_error=True)
        return None
    
    return processor


def build_single_ico(
    input_path: str,
    output_path: str,
    sizes: list[int],
    autofill: bool,
    png_compression: bool,
    verbose: bool = False,
    quiet: bool = False
) -> int:
    """
    Build a single ICO file from input.
    
    Args:
        input_path: Source image path
        output_path: Output ICO path
        sizes: List of sizes to include
        autofill: Enable auto-fill of missing sizes
        png_compression: Use PNG compression
        verbose: Enable verbose output
        quiet: Suppress output
        
    Returns:
        Exit code
    """
    logger.info(f"CLI build_single_ico: {input_path} -> {output_path}")
    
    # Ensure output has .ico extension
    if not output_path.lower().endswith('.ico'):
        output_path += '.ico'
    
    # Load source
    processor = load_source_image(input_path, verbose, quiet)
    if not processor:
        return EXIT_ERROR
    
    images = processor.get_detected_images()
    if not images:
        print_msg("No images loaded from source", is_error=True)
        return EXIT_ERROR
    
    # Build ICO
    print_msg(f"Building ICO with sizes: {', '.join(str(s) for s in sizes)}", verbose=verbose, quiet=quiet)
    
    success, message, info = IconBuilderCore.build_ico_file(
        images_dict=images,
        output_path=output_path,
        autofill=autofill,
        selected_sizes=sizes,
        use_png_compression=png_compression
    )
    
    if success:
        file_size = info.get('file_size', 0)
        sizes_str = ', '.join(info.get('sizes', []))
        print_msg(f"Created: {output_path} ({file_size:,} bytes)", quiet=quiet)
        print_msg(f"  Sizes: {sizes_str}", verbose=verbose, quiet=quiet)
        return EXIT_SUCCESS
    else:
        print_msg(f"Failed to create ICO: {message}", is_error=True)
        return EXIT_ERROR


def batch_process(
    input_folder: str,
    output_folder: str,
    sizes: list[int],
    autofill: bool,
    png_compression: bool,
    recursive: bool = False,
    verbose: bool = False,
    quiet: bool = False
) -> int:
    """
    Process all images in a folder.
    
    Args:
        input_folder: Source folder path
        output_folder: Output folder path
        sizes: List of sizes to include
        autofill: Enable auto-fill of missing sizes
        png_compression: Use PNG compression
        recursive: Scan subfolders
        verbose: Enable verbose output
        quiet: Suppress output
        
    Returns:
        Exit code
    """
    if not os.path.isdir(input_folder):
        print_msg(f"Input is not a folder: {input_folder}", is_error=True)
        return EXIT_ERROR
    
    logger.info(f"CLI batch_process: {input_folder} -> {output_folder}, recursive={recursive}")
    
    # Create output folder
    FileUtils.create_directory_if_not_exists(output_folder)
    
    # Find all image files
    files: list[str] = []
    for root, _, filenames in os.walk(input_folder):
        for filename in filenames:
            if any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                files.append(os.path.join(root, filename))
        if not recursive:
            break
    
    if not files:
        print_msg(f"No image files found in: {input_folder}", is_error=True)
        return EXIT_ERROR
    
    print_msg(f"Processing {len(files)} file(s)...", quiet=quiet)
    
    success_count = 0
    error_count = 0
    
    for file_path in files:
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        output_path = os.path.join(output_folder, f"{name_without_ext}.ico")
        
        result = build_single_ico(
            file_path, output_path, sizes, autofill, png_compression, verbose, quiet=True
        )
        
        if result == EXIT_SUCCESS:
            success_count += 1
            print_msg(f"  ✓ {filename}", verbose=verbose, quiet=quiet)
        else:
            error_count += 1
            print_msg(f"  ✗ {filename}", quiet=quiet)
    
    print_msg(f"\nCompleted: {success_count} succeeded, {error_count} failed", quiet=quiet)
    
    logger.info(f"CLI batch complete: {success_count} succeeded, {error_count} failed")
    
    return EXIT_SUCCESS if error_count == 0 else EXIT_ERROR


def export_favicon_package(
    input_path: str,
    output_folder: str,
    verbose: bool = False,
    quiet: bool = False
) -> int:
    """
    Export favicon package (PNGs + ICO + manifest).
    
    Args:
        input_path: Source image path
        output_folder: Output folder path
        verbose: Enable verbose output
        quiet: Suppress output
        
    Returns:
        Exit code
    """
    # Load source
    processor = load_source_image(input_path, verbose, quiet)
    if not processor:
        return EXIT_ERROR
    
    images = processor.get_detected_images()
    if not images:
        print_msg("No images loaded from source", is_error=True)
        return EXIT_ERROR
    
    # Create output folder
    FileUtils.create_directory_if_not_exists(output_folder)
    
    # Get base image for resizing
    base_size = processor.get_largest_size()
    if not base_size:
        print_msg("No valid source image found", is_error=True)
        return EXIT_ERROR
    
    base_image = images[base_size]
    
    print_msg(f"Exporting favicon package to: {output_folder}", quiet=quiet)
    
    # Export PNGs
    for size in FAVICON_SIZES:
        if size in images:
            img = images[size]
        else:
            img = base_image.resize((size, size), Image.Resampling.LANCZOS)
        
        png_path = os.path.join(output_folder, f"favicon-{size}x{size}.png")
        img.save(png_path, format='PNG', optimize=True)
        print_msg(f"  Created: favicon-{size}x{size}.png", verbose=verbose, quiet=quiet)
    
    # Build ICO
    ico_path = os.path.join(output_folder, "favicon.ico")
    success, message, info = IconBuilderCore.build_ico_file(
        images_dict=images,
        output_path=ico_path,
        autofill=True,
        selected_sizes=FAVICON_SIZES,
        use_png_compression=True
    )
    
    if success:
        print_msg(f"  Created: favicon.ico", verbose=verbose, quiet=quiet)
    else:
        print_msg(f"Failed to create favicon.ico: {message}", is_error=True)
    
    # Create site.webmanifest
    manifest = {
        "name": "",
        "short_name": "",
        "icons": [
            {
                "src": f"favicon-{size}x{size}.png",
                "sizes": f"{size}x{size}",
                "type": "image/png"
            }
            for size in FAVICON_SIZES
        ],
        "theme_color": "#ffffff",
        "background_color": "#ffffff",
        "display": "standalone"
    }
    
    import json
    manifest_path = os.path.join(output_folder, "site.webmanifest")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    print_msg(f"  Created: site.webmanifest", verbose=verbose, quiet=quiet)
    
    # Create HTML snippet
    html_snippet = """<!-- Favicon -->
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="manifest" href="/site.webmanifest">
"""
    html_path = os.path.join(output_folder, "favicon-html.txt")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_snippet)
    print_msg(f"  Created: favicon-html.txt", verbose=verbose, quiet=quiet)
    
    print_msg(f"\nFavicon package exported successfully!", quiet=quiet)
    return EXIT_SUCCESS


def export_android_icons(
    input_path: str,
    output_folder: str,
    verbose: bool = False,
    quiet: bool = False
) -> int:
    """
    Export Android app icon set.
    
    Args:
        input_path: Source image path
        output_folder: Output folder path
        verbose: Enable verbose output
        quiet: Suppress output
        
    Returns:
        Exit code
    """
    # Load source
    processor = load_source_image(input_path, verbose, quiet)
    if not processor:
        return EXIT_ERROR
    
    images = processor.get_detected_images()
    if not images:
        print_msg("No images loaded from source", is_error=True)
        return EXIT_ERROR
    
    # Get base image for resizing
    base_size = processor.get_largest_size()
    if not base_size:
        print_msg("No valid source image found", is_error=True)
        return EXIT_ERROR
    
    base_image = images[base_size]
    
    print_msg(f"Exporting Android icons to: {output_folder}", quiet=quiet)
    
    # Create res folder structure
    for density, size in ANDROID_SIZES.items():
        density_folder = os.path.join(output_folder, f"mipmap-{density}")
        FileUtils.create_directory_if_not_exists(density_folder)
        
        if size in images:
            img = images[size]
        else:
            img = base_image.resize((size, size), Image.Resampling.LANCZOS)
        
        # Standard launcher icon
        icon_path = os.path.join(density_folder, "ic_launcher.png")
        img.save(icon_path, format='PNG', optimize=True)
        print_msg(f"  Created: mipmap-{density}/ic_launcher.png ({size}x{size})", verbose=verbose, quiet=quiet)
        
        # Round variant (same image, different name)
        round_path = os.path.join(density_folder, "ic_launcher_round.png")
        img.save(round_path, format='PNG', optimize=True)
    
    print_msg(f"\nAndroid icons exported successfully!", quiet=quiet)
    return EXIT_SUCCESS


def export_ios_icons(
    input_path: str,
    output_folder: str,
    verbose: bool = False,
    quiet: bool = False
) -> int:
    """
    Export iOS App Icon set with Contents.json.
    
    Args:
        input_path: Source image path
        output_folder: Output folder path
        verbose: Enable verbose output
        quiet: Suppress output
        
    Returns:
        Exit code
    """
    # Load source
    processor = load_source_image(input_path, verbose, quiet)
    if not processor:
        return EXIT_ERROR
    
    images = processor.get_detected_images()
    if not images:
        print_msg("No images loaded from source", is_error=True)
        return EXIT_ERROR
    
    # Get base image for resizing
    base_size = processor.get_largest_size()
    if not base_size:
        print_msg("No valid source image found", is_error=True)
        return EXIT_ERROR
    
    base_image = images[base_size]
    
    # Create AppIcon.appiconset folder
    iconset_folder = os.path.join(output_folder, "AppIcon.appiconset")
    FileUtils.create_directory_if_not_exists(iconset_folder)
    
    print_msg(f"Exporting iOS icons to: {iconset_folder}", quiet=quiet)
    
    # iOS icon specifications
    ios_icons = [
        # iPhone
        {"size": 20, "scale": 2, "idiom": "iphone"},
        {"size": 20, "scale": 3, "idiom": "iphone"},
        {"size": 29, "scale": 2, "idiom": "iphone"},
        {"size": 29, "scale": 3, "idiom": "iphone"},
        {"size": 40, "scale": 2, "idiom": "iphone"},
        {"size": 40, "scale": 3, "idiom": "iphone"},
        {"size": 60, "scale": 2, "idiom": "iphone"},
        {"size": 60, "scale": 3, "idiom": "iphone"},
        # iPad
        {"size": 20, "scale": 1, "idiom": "ipad"},
        {"size": 20, "scale": 2, "idiom": "ipad"},
        {"size": 29, "scale": 1, "idiom": "ipad"},
        {"size": 29, "scale": 2, "idiom": "ipad"},
        {"size": 40, "scale": 1, "idiom": "ipad"},
        {"size": 40, "scale": 2, "idiom": "ipad"},
        {"size": 76, "scale": 1, "idiom": "ipad"},
        {"size": 76, "scale": 2, "idiom": "ipad"},
        {"size": 83.5, "scale": 2, "idiom": "ipad"},
        # App Store
        {"size": 1024, "scale": 1, "idiom": "ios-marketing"},
    ]
    
    # Contents.json structure
    contents_images = []
    
    for icon_spec in ios_icons:
        base_size_pt = icon_spec["size"]
        scale = icon_spec["scale"]
        idiom = icon_spec["idiom"]
        
        # Calculate pixel size
        pixel_size = int(base_size_pt * scale)
        
        # Generate filename
        if scale == 1:
            filename = f"icon_{int(base_size_pt)}x{int(base_size_pt)}.png"
        else:
            filename = f"icon_{int(base_size_pt)}x{int(base_size_pt)}@{scale}x.png"
        
        # Resize and save
        if pixel_size in images:
            img = images[pixel_size]
        else:
            img = base_image.resize((pixel_size, pixel_size), Image.Resampling.LANCZOS)
        
        icon_path = os.path.join(iconset_folder, filename)
        img.save(icon_path, format='PNG', optimize=True)
        print_msg(f"  Created: {filename} ({pixel_size}x{pixel_size})", verbose=verbose, quiet=quiet)
        
        # Add to Contents.json
        contents_images.append({
            "filename": filename,
            "idiom": idiom,
            "scale": f"{scale}x",
            "size": f"{int(base_size_pt)}x{int(base_size_pt)}"
        })
    
    # Write Contents.json
    import json
    contents = {
        "images": contents_images,
        "info": {
            "author": "RNV Icon Builder",
            "version": 1
        }
    }
    
    contents_path = os.path.join(iconset_folder, "Contents.json")
    with open(contents_path, 'w', encoding='utf-8') as f:
        json.dump(contents, f, indent=2)
    print_msg(f"  Created: Contents.json", verbose=verbose, quiet=quiet)
    
    print_msg(f"\niOS icons exported successfully!", quiet=quiet)
    return EXIT_SUCCESS


def main() -> int:
    """
    Main CLI entry point.
    
    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args()
    
    logger.info(f"CLI invoked with: {' '.join(sys.argv[1:])}")
    
    # Handle utility commands
    if args.list_presets:
        return list_presets(args.quiet)
    
    if args.analyze:
        return analyze_ico(args.input, args.quiet)
    
    # Validate input
    if not FileUtils.validate_file_path(args.input, must_exist=True):
        print_msg(f"Input not found: {args.input}", is_error=True)
        return EXIT_INVALID_ARGS
    
    # Determine options
    autofill = not args.no_autofill
    png_compression = not args.no_png_compression
    
    # Get sizes
    sizes = get_sizes_from_args(args)
    
    # Route to appropriate handler
    if args.favicon_package:
        return export_favicon_package(args.input, args.output, args.verbose, args.quiet)
    
    elif args.android:
        return export_android_icons(args.input, args.output, args.verbose, args.quiet)
    
    elif args.ios:
        return export_ios_icons(args.input, args.output, args.verbose, args.quiet)
    
    elif args.batch or os.path.isdir(args.input):
        return batch_process(
            args.input, args.output, sizes, autofill, png_compression,
            args.recursive, args.verbose, args.quiet
        )
    
    else:
        return build_single_ico(
            args.input, args.output, sizes, autofill, png_compression,
            args.verbose, args.quiet
        )


if __name__ == "__main__":
    sys.exit(main())
