"""
RNV Icon Builder - Core Icon Building Module
Handles creation of multi-resolution ICO files with proper BMP encoding.

Features:
- Multi-resolution ICO file generation
- Proper BGRA pixel format handling
- AND mask creation for transparency
- ICO file verification
- ICO to PNG extraction
- macOS .icns export
- File size estimation
- Favicon Package export
- Android Adaptive Icons export
- iOS App Icon Set export
"""

from __future__ import annotations

import struct
import os
import io
import json
from typing import Any

from PIL import Image

from utils.config import (
    ICON_SIZES,
    BMP_HEADER_SIZE,
    ICO_HEADER_SIZE,
    ICO_DIR_ENTRY_SIZE,
    BITS_PER_PIXEL,
    BYTES_PER_PIXEL,
    COLOR_PLANES,
    ALPHA_THRESHOLD
)
from utils.file_utils import FileUtils
from utils.logger import Logger, get_logger_instance

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)


class IconBuilderCore:
    """
    Core ICO file building functionality with proper BMP encoding.
    
    All methods are static for easy testing and reuse.
    
    Example:
        >>> images = {256: large_img, 64: medium_img, 16: small_img}
        >>> success, message, info = IconBuilderCore.build_ico_file(
        ...     images, "output.ico", autofill=True
        ... )
    """
    
    @staticmethod
    def prepare_image_data(img: Image.Image, size: int) -> bytes:
        """
        Prepare image data in BGRA format with vertical flip for BMP.
        
        ICO files use BMP format which requires:
        - BGRA byte order (not RGBA)
        - Vertical flip (bottom row first)
        
        Args:
            img: Input PIL Image
            size: Target size (width and height)
            
        Returns:
            BGRA pixel data with vertical flip
            
        Example:
            >>> data = IconBuilderCore.prepare_image_data(img, 256)
            >>> len(data)  # 256 * 256 * 4 = 262144
        """
        # Convert to RGBA if needed
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Get raw RGBA pixel data
        rgba_data: bytes = img.tobytes('raw', 'RGBA')
        
        # Convert RGBA to BGRA (required for BMP/ICO)
        rgba_bytes = bytearray(rgba_data)
        bgra_bytes = bytearray(len(rgba_bytes))
        
        for i in range(0, len(rgba_bytes), BYTES_PER_PIXEL):
            bgra_bytes[i] = rgba_bytes[i + 2]      # B <- R
            bgra_bytes[i + 1] = rgba_bytes[i + 1]  # G <- G
            bgra_bytes[i + 2] = rgba_bytes[i]      # R <- B
            bgra_bytes[i + 3] = rgba_bytes[i + 3]  # A <- A
        
        # Flip vertically by reversing row order (BMP requirement)
        row_size: int = size * BYTES_PER_PIXEL
        flipped_bytes = bytearray()
        
        for row in range(size - 1, -1, -1):
            start: int = row * row_size
            end: int = start + row_size
            flipped_bytes.extend(bgra_bytes[start:end])
        
        return bytes(flipped_bytes)
    
    @staticmethod
    def create_bmp_header(size: int) -> bytes:
        """
        Create BITMAPINFOHEADER for ICO file.
        
        Creates a 40-byte BITMAPINFOHEADER structure.
        
        Args:
            size: Image size (width and height)
            
        Returns:
            40-byte BITMAPINFOHEADER
            
        Example:
            >>> header = IconBuilderCore.create_bmp_header(256)
            >>> len(header)  # 40
        """
        header: bytes = struct.pack('<I', BMP_HEADER_SIZE)  # Header size
        header += struct.pack('<i', size)                    # Width
        header += struct.pack('<i', size * 2)                # Height (doubled for AND mask)
        header += struct.pack('<HH', COLOR_PLANES, BITS_PER_PIXEL)  # Planes, BPP
        header += struct.pack('<I', 0)                       # Compression (0 = none)
        header += struct.pack('<I', 0)                       # Image size
        header += struct.pack('<i', 0)                       # X pixels per meter
        header += struct.pack('<i', 0)                       # Y pixels per meter
        header += struct.pack('<I', 0)                       # Colors used
        header += struct.pack('<I', 0)                       # Important colors
        
        return header
    
    @staticmethod
    def create_and_mask(pixel_data: bytes, size: int) -> bytes:
        """
        Create AND mask from alpha channel (1 bit per pixel).
        
        The AND mask defines transparency: 0 = opaque, 1 = transparent.
        
        Args:
            pixel_data: BGRA pixel data
            size: Image size
            
        Returns:
            AND mask data (1 bit per pixel, padded to 4-byte rows)
            
        Example:
            >>> mask = IconBuilderCore.create_and_mask(pixel_data, 256)
        """
        # Calculate bytes per row (must be multiple of 4)
        mask_bytes_per_row: int = ((size + 31) // 32) * 4
        and_mask = bytearray(mask_bytes_per_row * size)
        
        # Extract alpha channel and create mask
        pixel_bytes = bytearray(pixel_data)
        
        for y in range(size):
            for x in range(size):
                # Get alpha value (last byte in BGRA)
                pixel_idx: int = (y * size + x) * BYTES_PER_PIXEL
                alpha: int = pixel_bytes[pixel_idx + 3]
                
                # Set mask bit: 0 if opaque, 1 if transparent
                byte_idx: int = y * mask_bytes_per_row + (x // 8)
                bit_idx: int = 7 - (x % 8)
                
                if alpha <= ALPHA_THRESHOLD:
                    and_mask[byte_idx] |= (1 << bit_idx)
                else:
                    and_mask[byte_idx] &= ~(1 << bit_idx)
        
        return bytes(and_mask)
    
    @staticmethod
    def build_ico_file(
        images_dict: dict[int, Image.Image],
        output_path: str,
        autofill: bool = True,
        selected_sizes: list[int] | None = None,
        use_png_compression: bool = True
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Build a multi-resolution ICO file from provided images.
        
        Args:
            images_dict: Dictionary mapping size (int) to PIL Image
            output_path: Path where ICO file should be saved
            autofill: If True, auto-fill missing sizes from largest image
            selected_sizes: List of sizes to include (None = all ICON_SIZES)
            use_png_compression: Use PNG compression for 256x256 and 128x128
            
        Returns:
            Tuple of (success, message, file_info dict)
            
        Raises:
            Exception: If ICO file cannot be created
            
        Example:
            >>> images = {256: img256, 64: img64}
            >>> success, msg, info = IconBuilderCore.build_ico_file(
            ...     images, "output.ico", autofill=True,
            ...     selected_sizes=[256, 48, 32, 16],
            ...     use_png_compression=True
            ... )
            >>> if success:
            ...     print(f"Created {info['file_size']} byte ICO")
        """
        if not images_dict:
            return False, "No images provided", {}
        
        # Determine which sizes to include
        target_sizes = selected_sizes if selected_sizes else ICON_SIZES
        
        logger.info(f"Building ICO: {len(images_dict)} source image(s), "
                     f"{len(target_sizes)} target size(s), "
                     f"PNG compression={'on' if use_png_compression else 'off'}")
        
        # Get base size for auto-filling
        base_size: int = max(images_dict.keys())
        
        # Prepare images to save
        images_to_save: dict[int, Image.Image] = {}
        
        for size in target_sizes:
            if size in images_dict:
                images_to_save[size] = images_dict[size]
            elif autofill and size < base_size:
                # Resize from largest available image
                images_to_save[size] = images_dict[base_size].resize(
                    (size, size),
                    Image.Resampling.LANCZOS
                )
        
        if not images_to_save:
            return False, "No valid images to save", {}
        
        try:
            # Sort sizes (largest first is conventional)
            sorted_sizes: list[int] = sorted(images_to_save.keys(), reverse=True)
            
            # Sizes that use PNG compression (256 and 128 if enabled)
            png_sizes: set[int] = {256, 128} if use_png_compression else set()
            
            # Prepare all image data
            images_data: list[tuple[int, bytes, bool]] = []  # (size, data, is_png)
            
            for size in sorted_sizes:
                img: Image.Image = images_to_save[size]
                
                if size in png_sizes:
                    # Use PNG compression for large sizes
                    import io
                    png_buffer = io.BytesIO()
                    # Ensure RGBA mode for PNG
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.save(png_buffer, format='PNG', optimize=True)
                    image_data: bytes = png_buffer.getvalue()
                    images_data.append((size, image_data, True))
                else:
                    # Use BMP format for smaller sizes
                    pixels: bytes = IconBuilderCore.prepare_image_data(img, size)
                    bmp_header: bytes = IconBuilderCore.create_bmp_header(size)
                    and_mask: bytes = IconBuilderCore.create_and_mask(pixels, size)
                    image_data = bmp_header + pixels + and_mask
                    images_data.append((size, image_data, False))
            
            # Write ICO file
            with open(output_path, 'wb') as f:
                # Calculate offsets
                header_size: int = ICO_HEADER_SIZE
                dir_entry_size: int = ICO_DIR_ENTRY_SIZE
                dir_total_size: int = len(images_data) * dir_entry_size
                image_data_start: int = header_size + dir_total_size
                
                # Write ICO header (6 bytes)
                f.write(struct.pack('<HHH', 0, 1, len(images_data)))
                
                # Collect offsets
                current_offset: int = image_data_start
                offsets: list[int] = []
                
                for size, image_data, is_png in images_data:
                    offsets.append(current_offset)
                    current_offset += len(image_data)
                
                # Write directory entries
                for i, (size, image_data, is_png) in enumerate(images_data):
                    # Use 0 for 256x256 (ICO format requirement)
                    width: int = 0 if size == 256 else size
                    height: int = 0 if size == 256 else size
                    
                    f.write(struct.pack('<BBBBHHII',
                        width,               # Width
                        height,              # Height
                        0,                   # Color palette
                        0,                   # Reserved
                        COLOR_PLANES,        # Color planes
                        BITS_PER_PIXEL,      # Bits per pixel
                        len(image_data),     # Bytes in image
                        offsets[i]           # Offset
                    ))
                
                # Write all image data
                for size, image_data, is_png in images_data:
                    f.write(image_data)
            
            # Verify the file
            verification: dict[str, Any] = IconBuilderCore.verify_ico_file(output_path)
            
            # Add compression info
            png_used = [size for size, _, is_png in images_data if is_png]
            if png_used:
                verification['png_compressed'] = png_used
            
            # Add detailed compression statistics
            compression_stats = IconBuilderCore._calculate_compression_stats(
                images_to_save, images_data, output_path
            )
            verification['compression_stats'] = compression_stats
            
            logger.success(f"ICO file created: {len(images_data)} image(s), "
                           f"{os.path.getsize(output_path):,} bytes")
            
            return True, "ICO file created successfully", verification
            
        except Exception as e:
            logger.error(f"Failed to create ICO: {e}", error=e)
            return False, f"Failed to create ICO: {str(e)}", {}
    
    @staticmethod
    def verify_ico_file(file_path: str) -> dict[str, Any]:
        """
        Verify ICO file structure and return information.
        
        Args:
            file_path: Path to ICO file
            
        Returns:
            Dictionary with file info (sizes, count, file_size)
            
        Example:
            >>> info = IconBuilderCore.verify_ico_file("output.ico")
            >>> print(f"Contains {info['count']} images: {info['sizes']}")
        """
        try:
            info: dict[str, Any] = {
                'file_size': os.path.getsize(file_path),
                'sizes': [],
                'count': 0
            }
            
            with open(file_path, 'rb') as f:
                # Read ICO header
                header: bytes = f.read(ICO_HEADER_SIZE)
                if len(header) >= ICO_HEADER_SIZE:
                    reserved, file_type, num_images = struct.unpack('<HHH', header)
                    info['count'] = num_images
                    
                    # Read directory entries
                    for i in range(num_images):
                        f.seek(ICO_HEADER_SIZE + (i * ICO_DIR_ENTRY_SIZE))
                        entry: bytes = f.read(ICO_DIR_ENTRY_SIZE)
                        if len(entry) >= ICO_DIR_ENTRY_SIZE:
                            width, height = struct.unpack('<BB', entry[0:2])
                            # 0 means 256
                            width = 256 if width == 0 else width
                            height = 256 if height == 0 else height
                            info['sizes'].append(f"{width}x{height}")
            
            return info
            
        except Exception as e:
            logger.error(f"Error verifying ICO file: {e}", error=e)
            return {
                'file_size': 0,
                'sizes': [],
                'count': 0,
                'error': str(e)
            }
    
    @staticmethod
    def _calculate_compression_stats(
        images_to_save: dict[int, Image.Image],
        images_data: list[tuple[int, bytes, bool]],
        output_path: str
    ) -> dict[str, Any]:
        """
        Calculate compression statistics for the ICO build.
        
        Args:
            images_to_save: Dictionary of size -> PIL Image
            images_data: List of (size, data_bytes, is_png) tuples
            output_path: Path to the output ICO file
            
        Returns:
            Dictionary with compression statistics
        """
        stats: dict[str, Any] = {
            'total_uncompressed': 0,
            'total_compressed': 0,
            'compression_ratio': 0.0,
            'savings_bytes': 0,
            'savings_percent': 0.0,
            'per_size': {}
        }
        
        try:
            for size, data, is_png in images_data:
                img = images_to_save.get(size)
                if img is None:
                    continue
                
                # Calculate uncompressed BMP size for this image
                # BMP data = header (40 bytes) + pixels (size * size * 4) + AND mask
                bmp_header_size = 40
                pixel_data_size = size * size * 4  # BGRA
                and_mask_row = ((size + 31) // 32) * 4
                and_mask_size = and_mask_row * size
                uncompressed_size = bmp_header_size + pixel_data_size + and_mask_size
                
                compressed_size = len(data)
                
                # Calculate savings for PNG-compressed sizes
                if is_png:
                    savings = uncompressed_size - compressed_size
                    ratio = compressed_size / uncompressed_size if uncompressed_size > 0 else 1.0
                else:
                    savings = 0
                    ratio = 1.0
                
                stats['per_size'][size] = {
                    'uncompressed': uncompressed_size,
                    'compressed': compressed_size,
                    'is_png': is_png,
                    'savings': savings,
                    'ratio': ratio
                }
                
                stats['total_uncompressed'] += uncompressed_size
                stats['total_compressed'] += compressed_size
            
            # Calculate overall statistics
            if stats['total_uncompressed'] > 0:
                stats['compression_ratio'] = stats['total_compressed'] / stats['total_uncompressed']
                stats['savings_bytes'] = stats['total_uncompressed'] - stats['total_compressed']
                stats['savings_percent'] = (stats['savings_bytes'] / stats['total_uncompressed']) * 100
            
            # Get actual file size
            if os.path.exists(output_path):
                stats['actual_file_size'] = os.path.getsize(output_path)
            
        except Exception as e:
            logger.error(f"Error calculating compression stats: {e}", error=e)
            stats['error'] = str(e)
        
        return stats
    
    @staticmethod
    def get_ico_info(file_path: str) -> dict[str, Any] | None:
        """
        Get detailed information about an existing ICO file.
        
        Includes compression detection (PNG vs BMP) for each image.
        
        Args:
            file_path: Path to ICO file
            
        Returns:
            Dictionary with detailed ICO information, or None on error
            
        Example:
            >>> info = IconBuilderCore.get_ico_info("app.ico")
            >>> if info:
            ...     for size_info in info['images']:
            ...         print(f"{size_info['size']}x{size_info['size']}: {size_info['compression']}")
        """
        # PNG magic bytes
        PNG_MAGIC = b'\x89PNG'
        
        try:
            if not FileUtils.validate_file_path(file_path, must_exist=True):
                return None
            
            info: dict[str, Any] = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': FileUtils.get_file_size_bytes(file_path),
                'images': [],
                'valid': False,
                'has_png': False,
                'has_bmp': False
            }
            
            with open(file_path, 'rb') as f:
                # Read and validate header
                header = f.read(ICO_HEADER_SIZE)
                if len(header) < ICO_HEADER_SIZE:
                    return info
                
                reserved, file_type, num_images = struct.unpack('<HHH', header)
                
                # ICO files have type = 1, CUR files have type = 2
                if file_type == 1:
                    info['file_type'] = 'ICO'
                elif file_type == 2:
                    info['file_type'] = 'CUR'
                else:
                    info['error'] = f"Invalid file type: {file_type} (expected 1 for ICO)"
                    return info
                
                info['image_count'] = num_images
                
                # Read each directory entry
                for i in range(num_images):
                    f.seek(ICO_HEADER_SIZE + (i * ICO_DIR_ENTRY_SIZE))
                    entry = f.read(ICO_DIR_ENTRY_SIZE)
                    
                    if len(entry) < ICO_DIR_ENTRY_SIZE:
                        break
                    
                    width, height, colors, reserved_byte, planes, bpp, size_bytes, offset = \
                        struct.unpack('<BBBBHHII', entry)
                    
                    # 0 means 256
                    width = 256 if width == 0 else width
                    height = 256 if height == 0 else height
                    
                    # Detect compression by reading first bytes of image data
                    current_pos = f.tell()
                    f.seek(offset)
                    magic_bytes = f.read(4)
                    f.seek(current_pos)
                    
                    if magic_bytes[:4] == PNG_MAGIC:
                        compression = 'PNG'
                        info['has_png'] = True
                    else:
                        compression = 'BMP'
                        info['has_bmp'] = True
                    
                    image_info: dict[str, Any] = {
                        'index': i,
                        'width': width,
                        'height': height,
                        'size': width,  # Assuming square
                        'colors': colors if colors > 0 else 256 if bpp <= 8 else 0,
                        'color_planes': planes,
                        'bits_per_pixel': bpp,
                        'bytes': size_bytes,
                        'offset': offset,
                        'compression': compression
                    }
                    info['images'].append(image_info)
                
                # Sort images by size (largest first)
                info['images'].sort(key=lambda x: x['size'], reverse=True)
                
                # Summary info
                info['sizes'] = [f"{img['size']}x{img['size']}" for img in info['images']]
                info['valid'] = True
            
            return info
            
        except Exception as e:
            logger.error(f"Error reading ICO info for {file_path}: {e}", error=e)
            return {
                'file_path': file_path,
                'error': str(e),
                'valid': False
            }
    
    # ==================== Export Formats ====================
    
    @staticmethod
    def extract_ico_to_pngs(
        ico_path: str,
        output_folder: str,
        base_name: str = "icon"
    ) -> tuple[bool, str, list[str]]:
        """
        Extract all images from an ICO file as separate PNG files.
        
        Args:
            ico_path: Path to ICO file to extract
            output_folder: Folder to save extracted PNGs
            base_name: Base name for output files (default: "icon")
            
        Returns:
            Tuple of (success, message, list of extracted file paths)
            
        Example:
            >>> success, msg, files = IconBuilderCore.extract_ico_to_pngs(
            ...     "app.ico", "/output/", "app_icon"
            ... )
            >>> if success:
            ...     print(f"Extracted {len(files)} images")
        """
        extracted_files: list[str] = []
        
        logger.info(f"Extracting ICO to PNGs: {ico_path}")
        
        try:
            if not FileUtils.validate_file_path(ico_path, must_exist=True):
                return False, f"ICO file not found: {ico_path}", []
            
            # Ensure output folder exists
            FileUtils.create_directory_if_not_exists(output_folder)
            
            # Open ICO file with PIL
            with Image.open(ico_path) as ico:
                n_frames = getattr(ico, 'n_frames', 1)
                
                for frame_idx in range(n_frames):
                    try:
                        ico.seek(frame_idx)
                        w, h = ico.size
                        
                        # Convert to RGBA for PNG export
                        img = ico.copy().convert('RGBA')
                        
                        # Generate output filename
                        output_path = os.path.join(
                            output_folder, 
                            f"{base_name}_{w}x{h}.png"
                        )
                        
                        # Handle duplicate sizes by adding index
                        if output_path in extracted_files:
                            output_path = os.path.join(
                                output_folder,
                                f"{base_name}_{w}x{h}_{frame_idx}.png"
                            )
                        
                        # Save as PNG
                        img.save(output_path, format='PNG', optimize=True)
                        extracted_files.append(output_path)
                        
                    except Exception as e:
                        # Continue with other frames even if one fails
                        logger.warning(f"Failed to extract frame {frame_idx}: {e}")
                        continue
            
            if extracted_files:
                logger.success(f"Extracted {len(extracted_files)} image(s) from ICO")
                return True, f"Extracted {len(extracted_files)} image(s)", extracted_files
            else:
                logger.warning("No images could be extracted from ICO")
                return False, "No images could be extracted", []
                
        except Exception as e:
            logger.error(f"ICO extraction failed: {e}", error=e)
            return False, f"Extraction failed: {str(e)}", []
    
    @staticmethod
    def estimate_ico_size(
        images_dict: dict[int, Image.Image],
        selected_sizes: list[int] | None = None,
        autofill: bool = True,
        use_png_compression: bool = True
    ) -> dict[str, Any]:
        """
        Estimate the file size of an ICO file before building.
        
        Args:
            images_dict: Dictionary mapping size (int) to PIL Image
            selected_sizes: List of sizes to include (None = all ICON_SIZES)
            autofill: If True, auto-fill missing sizes from largest image
            use_png_compression: Use PNG compression for 256x256 and 128x128
            
        Returns:
            Dictionary with size estimation info:
            - total_bytes: Estimated total file size
            - total_kb: Size in KB (formatted string)
            - breakdown: Dict of size -> estimated bytes
            - image_count: Number of images
            
        Example:
            >>> info = IconBuilderCore.estimate_ico_size(images, [256, 128, 64])
            >>> print(f"Estimated size: {info['total_kb']}")
        """
        if not images_dict:
            return {
                'total_bytes': 0,
                'total_kb': "0 KB",
                'breakdown': {},
                'image_count': 0
            }
        
        # Determine which sizes to include
        target_sizes = selected_sizes if selected_sizes else ICON_SIZES
        
        # Get base size for auto-filling
        base_size = max(images_dict.keys()) if images_dict else 0
        
        # Sizes that use PNG compression
        png_sizes = {256, 128} if use_png_compression else set()
        
        # Calculate sizes
        breakdown: dict[int, int] = {}
        
        for size in target_sizes:
            # Check if we have this size or can autofill it
            has_size = size in images_dict
            can_autofill = autofill and size < base_size
            
            if not has_size and not can_autofill:
                continue
            
            # Get or generate image for size estimation
            if has_size:
                img = images_dict[size]
            else:
                # Estimate based on resized image
                img = images_dict[base_size].resize(
                    (size, size),
                    Image.Resampling.LANCZOS
                )
            
            if size in png_sizes:
                # Estimate PNG size (compress to get actual size)
                buffer = io.BytesIO()
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img.save(buffer, format='PNG', optimize=True)
                estimated_bytes = len(buffer.getvalue())
            else:
                # BMP size: header (40) + pixels (size*size*4) + AND mask
                mask_row_size = ((size + 31) // 32) * 4
                mask_size = mask_row_size * size
                estimated_bytes = BMP_HEADER_SIZE + (size * size * BYTES_PER_PIXEL) + mask_size
            
            breakdown[size] = estimated_bytes
        
        # Calculate total (add ICO header overhead)
        image_count = len(breakdown)
        header_overhead = ICO_HEADER_SIZE + (ICO_DIR_ENTRY_SIZE * image_count)
        total_bytes = sum(breakdown.values()) + header_overhead
        
        # Format as KB
        total_kb = total_bytes / 1024
        if total_kb < 1:
            total_kb_str = f"{total_bytes} B"
        elif total_kb < 1024:
            total_kb_str = f"{total_kb:.1f} KB"
        else:
            total_kb_str = f"{total_kb / 1024:.2f} MB"
        
        return {
            'total_bytes': total_bytes,
            'total_kb': total_kb_str,
            'breakdown': breakdown,
            'image_count': image_count
        }
    
    @staticmethod
    def build_icns_file(
        images_dict: dict[int, Image.Image],
        output_path: str,
        autofill: bool = True,
        selected_sizes: list[int] | None = None
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Build a macOS .icns icon file from provided images.
        
        The ICNS format requires specific sizes. This function will use
        available images and optionally autofill missing sizes.
        
        Required sizes for ICNS: 16, 32, 64, 128, 256, 512, 1024
        
        Args:
            images_dict: Dictionary mapping size (int) to PIL Image
            output_path: Path where ICNS file should be saved
            autofill: If True, auto-fill missing sizes from largest image
            selected_sizes: List of sizes to include (None = all available)
            
        Returns:
            Tuple of (success, message, file_info dict)
            
        Example:
            >>> success, msg, info = IconBuilderCore.build_icns_file(
            ...     images, "app.icns", autofill=True
            ... )
        """
        # ICNS icon types and their sizes
        # Format: (ostype, size, scale_factor)
        ICNS_TYPES = [
            (b'ic07', 128, 1),    # 128x128
            (b'ic08', 256, 1),    # 256x256  
            (b'ic09', 512, 1),    # 512x512
            (b'ic10', 1024, 1),   # 1024x1024 (512@2x)
            (b'ic11', 32, 2),     # 16@2x (32x32)
            (b'ic12', 64, 2),     # 32@2x (64x64)
            (b'ic13', 256, 2),    # 128@2x (256x256)
            (b'ic14', 512, 2),    # 256@2x (512x512)
            (b'icp4', 16, 1),     # 16x16
            (b'icp5', 32, 1),     # 32x32
            (b'icp6', 64, 1),     # 64x64 (48 in some docs)
        ]
        
        if not images_dict:
            return False, "No images provided", {}
        
        logger.info(f"Building ICNS: {len(images_dict)} source image(s)")
        
        # Get base size for auto-filling
        base_size = max(images_dict.keys())
        
        try:
            # Prepare images for each ICNS type
            icon_data: list[tuple[bytes, bytes]] = []
            sizes_included: list[str] = []
            
            for ostype, size, scale in ICNS_TYPES:
                # Skip if size not in selected_sizes (when specified)
                if selected_sizes is not None and size not in selected_sizes:
                    continue
                
                # Check if we have this size or can autofill
                if size in images_dict:
                    img = images_dict[size]
                elif autofill and size <= base_size:
                    img = images_dict[base_size].resize(
                        (size, size),
                        Image.Resampling.LANCZOS
                    )
                else:
                    continue
                
                # Convert to RGBA
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Ensure correct size
                if img.size != (size, size):
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # Save as PNG to buffer
                buffer = io.BytesIO()
                img.save(buffer, format='PNG', optimize=True)
                png_data = buffer.getvalue()
                
                icon_data.append((ostype, png_data))
                sizes_included.append(f"{size}x{size}")
            
            if not icon_data:
                return False, "No valid sizes could be included", {}
            
            # Build ICNS file
            # ICNS header: 'icns' + total file size (4 bytes)
            # Each entry: ostype (4) + size including header (4) + data
            
            # Calculate total size
            total_size = 8  # ICNS header
            for ostype, data in icon_data:
                total_size += 8 + len(data)  # type + size + data
            
            with open(output_path, 'wb') as f:
                # Write ICNS header
                f.write(b'icns')
                f.write(struct.pack('>I', total_size))
                
                # Write each icon
                for ostype, data in icon_data:
                    f.write(ostype)
                    f.write(struct.pack('>I', len(data) + 8))
                    f.write(data)
            
            # Get actual file size
            file_size = os.path.getsize(output_path)
            
            logger.success(f"ICNS file created: {len(icon_data)} image(s), "
                           f"{file_size:,} bytes")
            
            return True, "ICNS file created successfully", {
                'file_size': file_size,
                'sizes': sizes_included,
                'count': len(icon_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to create ICNS: {e}", error=e)
            return False, f"Failed to create ICNS: {str(e)}", {}
    
    # ==================== Platform-Specific Exports ====================
    
    @staticmethod
    def export_favicon_package(
        images_dict: dict[int, Image.Image],
        output_folder: str,
        autofill: bool = True,
        site_name: str = "My Website"
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Export a complete favicon package for web use.
        
        Generates:
        - favicon.ico (16, 32, 48)
        - favicon-16x16.png
        - favicon-32x32.png  
        - apple-touch-icon.png (180x180)
        - android-chrome-192x192.png
        - android-chrome-512x512.png
        - site.webmanifest
        - browserconfig.xml
        
        Args:
            images_dict: Dictionary mapping size (int) to PIL Image
            output_folder: Folder where files should be saved
            autofill: If True, auto-fill missing sizes from largest image
            site_name: Name for manifest file
            
        Returns:
            Tuple of (success, message, info dict)
            
        Example:
            >>> success, msg, info = IconBuilderCore.export_favicon_package(
            ...     images, "/path/to/output", site_name="My App"
            ... )
        """
        if not images_dict:
            return False, "No images provided", {}
        
        logger.info(f"Exporting favicon package to: {output_folder}")
        
        try:
            FileUtils.create_directory_if_not_exists(output_folder)
            
            # Get base size for auto-filling
            base_size = max(images_dict.keys())
            base_image = images_dict[base_size]
            if base_image.mode != 'RGBA':
                base_image = base_image.convert('RGBA')
            
            generated_files: list[str] = []
            
            # Helper to get or generate image at size
            def get_image(size: int) -> Image.Image:
                if size in images_dict:
                    img = images_dict[size]
                elif autofill:
                    img = base_image.resize((size, size), Image.Resampling.LANCZOS)
                else:
                    return None
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                return img
            
            # 1. Generate favicon.ico (16, 32, 48)
            ico_path = os.path.join(output_folder, "favicon.ico")
            ico_images = {}
            for size in [16, 32, 48]:
                img = get_image(size)
                if img:
                    ico_images[size] = img
            
            if ico_images:
                success, msg, _ = IconBuilderCore.build_ico_file(
                    ico_images, ico_path, 
                    autofill=False,  # Already have the images
                    selected_sizes=[16, 32, 48],
                    use_png_compression=False  # Use BMP for max compatibility
                )
                if success:
                    generated_files.append("favicon.ico")
            
            # 2. Generate PNG favicons
            png_sizes = [
                (16, "favicon-16x16.png"),
                (32, "favicon-32x32.png"),
            ]
            
            for size, filename in png_sizes:
                img = get_image(size)
                if img:
                    png_path = os.path.join(output_folder, filename)
                    img.save(png_path, format='PNG', optimize=True)
                    generated_files.append(filename)
            
            # 3. Apple Touch Icon (180x180)
            apple_img = get_image(180) or get_image(192) or base_image.resize(
                (180, 180), Image.Resampling.LANCZOS
            )
            if apple_img:
                if apple_img.size != (180, 180):
                    apple_img = apple_img.resize((180, 180), Image.Resampling.LANCZOS)
                apple_path = os.path.join(output_folder, "apple-touch-icon.png")
                apple_img.save(apple_path, format='PNG', optimize=True)
                generated_files.append("apple-touch-icon.png")
            
            # 4. Android Chrome Icons
            android_sizes = [
                (192, "android-chrome-192x192.png"),
                (512, "android-chrome-512x512.png"),
            ]
            
            for size, filename in android_sizes:
                img = get_image(size)
                if img is None:
                    # Generate from base
                    img = base_image.resize((size, size), Image.Resampling.LANCZOS)
                android_path = os.path.join(output_folder, filename)
                img.save(android_path, format='PNG', optimize=True)
                generated_files.append(filename)
            
            # 5. Generate site.webmanifest
            manifest = {
                "name": site_name,
                "short_name": site_name,
                "icons": [
                    {
                        "src": "/android-chrome-192x192.png",
                        "sizes": "192x192",
                        "type": "image/png"
                    },
                    {
                        "src": "/android-chrome-512x512.png",
                        "sizes": "512x512",
                        "type": "image/png"
                    }
                ],
                "theme_color": "#ffffff",
                "background_color": "#ffffff",
                "display": "standalone"
            }
            
            manifest_path = os.path.join(output_folder, "site.webmanifest")
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            generated_files.append("site.webmanifest")
            
            # 6. Generate browserconfig.xml (for IE/Edge)
            browserconfig = '''<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square150x150logo src="/mstile-150x150.png"/>
            <TileColor>#da532c</TileColor>
        </tile>
    </msapplication>
</browserconfig>'''
            
            browserconfig_path = os.path.join(output_folder, "browserconfig.xml")
            with open(browserconfig_path, 'w', encoding='utf-8') as f:
                f.write(browserconfig)
            generated_files.append("browserconfig.xml")
            
            # Generate mstile-150x150.png for browserconfig
            mstile_img = get_image(150) or base_image.resize((150, 150), Image.Resampling.LANCZOS)
            mstile_path = os.path.join(output_folder, "mstile-150x150.png")
            mstile_img.save(mstile_path, format='PNG', optimize=True)
            generated_files.append("mstile-150x150.png")
            
            logger.success(f"Favicon package exported: {len(generated_files)} file(s)")
            
            return True, "Favicon package exported successfully", {
                'output_folder': output_folder,
                'files': generated_files,
                'file_count': len(generated_files)
            }
            
        except Exception as e:
            logger.error(f"Failed to export favicon package: {e}", error=e)
            return False, f"Failed to export favicon package: {str(e)}", {}
    
    @staticmethod
    def export_android_icons(
        images_dict: dict[int, Image.Image],
        output_folder: str,
        autofill: bool = True,
        icon_name: str = "ic_launcher"
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Export Android adaptive icon set with proper density folders.
        
        Generates:
        res/
          mipmap-mdpi/ic_launcher.png (48x48)
          mipmap-hdpi/ic_launcher.png (72x72)
          mipmap-xhdpi/ic_launcher.png (96x96)
          mipmap-xxhdpi/ic_launcher.png (144x144)
          mipmap-xxxhdpi/ic_launcher.png (192x192)
        
        Args:
            images_dict: Dictionary mapping size (int) to PIL Image
            output_folder: Base folder where 'res' directory will be created
            autofill: If True, auto-fill missing sizes from largest image
            icon_name: Name for the icon files (default: ic_launcher)
            
        Returns:
            Tuple of (success, message, info dict)
            
        Example:
            >>> success, msg, info = IconBuilderCore.export_android_icons(
            ...     images, "/path/to/android_project"
            ... )
        """
        # Android density buckets and their sizes
        ANDROID_DENSITIES = [
            ("mipmap-mdpi", 48),
            ("mipmap-hdpi", 72),
            ("mipmap-xhdpi", 96),
            ("mipmap-xxhdpi", 144),
            ("mipmap-xxxhdpi", 192),
        ]
        
        if not images_dict:
            return False, "No images provided", {}
        
        logger.info(f"Exporting Android icons to: {output_folder}")
        
        try:
            # Create res directory
            res_folder = os.path.join(output_folder, "res")
            FileUtils.create_directory_if_not_exists(res_folder)
            
            # Get base size for auto-filling
            base_size = max(images_dict.keys())
            base_image = images_dict[base_size]
            if base_image.mode != 'RGBA':
                base_image = base_image.convert('RGBA')
            
            generated_files: list[str] = []
            
            for density_folder, size in ANDROID_DENSITIES:
                # Create density folder
                folder_path = os.path.join(res_folder, density_folder)
                FileUtils.create_directory_if_not_exists(folder_path)
                
                # Get or generate image at size
                if size in images_dict:
                    img = images_dict[size]
                elif autofill:
                    img = base_image.resize((size, size), Image.Resampling.LANCZOS)
                else:
                    continue
                
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Ensure correct size
                if img.size != (size, size):
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # Save PNG
                icon_path = os.path.join(folder_path, f"{icon_name}.png")
                img.save(icon_path, format='PNG', optimize=True)
                generated_files.append(f"res/{density_folder}/{icon_name}.png")
            
            if not generated_files:
                return False, "No valid sizes could be generated", {}
            
            logger.success(f"Android icons exported: {len(generated_files)} file(s)")
            
            return True, "Android icons exported successfully", {
                'output_folder': res_folder,
                'files': generated_files,
                'file_count': len(generated_files)
            }
            
        except Exception as e:
            logger.error(f"Failed to export Android icons: {e}", error=e)
            return False, f"Failed to export Android icons: {str(e)}", {}
    
    @staticmethod
    def export_ios_icons(
        images_dict: dict[int, Image.Image],
        output_folder: str,
        autofill: bool = True
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Export iOS App Icon Set with Contents.json manifest.
        
        Generates:
        AppIcon.appiconset/
          Contents.json
          Icon-20.png, Icon-20@2x.png, Icon-20@3x.png
          Icon-29.png, Icon-29@2x.png, Icon-29@3x.png
          Icon-40.png, Icon-40@2x.png, Icon-40@3x.png
          Icon-60@2x.png, Icon-60@3x.png
          Icon-76.png, Icon-76@2x.png
          Icon-83.5@2x.png
          Icon-1024.png
        
        Args:
            images_dict: Dictionary mapping size (int) to PIL Image
            output_folder: Base folder where AppIcon.appiconset will be created
            autofill: If True, auto-fill missing sizes from largest image
            
        Returns:
            Tuple of (success, message, info dict)
            
        Example:
            >>> success, msg, info = IconBuilderCore.export_ios_icons(
            ...     images, "/path/to/ios_project"
            ... )
        """
        # iOS icon specifications: (base_size, scale, idiom, filename)
        # Note: actual pixel size = base_size * scale
        IOS_ICONS = [
            # iPhone Notification
            (20, 2, "iphone", "Icon-20@2x.png"),
            (20, 3, "iphone", "Icon-20@3x.png"),
            # iPhone Settings
            (29, 2, "iphone", "Icon-29@2x.png"),
            (29, 3, "iphone", "Icon-29@3x.png"),
            # iPhone Spotlight
            (40, 2, "iphone", "Icon-40@2x.png"),
            (40, 3, "iphone", "Icon-40@3x.png"),
            # iPhone App
            (60, 2, "iphone", "Icon-60@2x.png"),
            (60, 3, "iphone", "Icon-60@3x.png"),
            # iPad Notification
            (20, 1, "ipad", "Icon-20.png"),
            (20, 2, "ipad", "Icon-20~ipad@2x.png"),
            # iPad Settings
            (29, 1, "ipad", "Icon-29.png"),
            (29, 2, "ipad", "Icon-29~ipad@2x.png"),
            # iPad Spotlight
            (40, 1, "ipad", "Icon-40.png"),
            (40, 2, "ipad", "Icon-40~ipad@2x.png"),
            # iPad App
            (76, 1, "ipad", "Icon-76.png"),
            (76, 2, "ipad", "Icon-76@2x.png"),
            # iPad Pro
            (83.5, 2, "ipad", "Icon-83.5@2x.png"),
            # App Store
            (1024, 1, "ios-marketing", "Icon-1024.png"),
        ]
        
        if not images_dict:
            return False, "No images provided", {}
        
        logger.info(f"Exporting iOS icons to: {output_folder}")
        
        try:
            # Create AppIcon.appiconset directory
            appiconset_folder = os.path.join(output_folder, "AppIcon.appiconset")
            FileUtils.create_directory_if_not_exists(appiconset_folder)
            
            # Get base size for auto-filling
            base_size = max(images_dict.keys())
            base_image = images_dict[base_size]
            if base_image.mode != 'RGBA':
                base_image = base_image.convert('RGBA')
            
            generated_files: list[str] = []
            contents_images: list[dict] = []
            
            for base, scale, idiom, filename in IOS_ICONS:
                # Calculate actual pixel size
                pixel_size = int(base * scale)
                
                # Get or generate image at pixel size
                if pixel_size in images_dict:
                    img = images_dict[pixel_size]
                elif autofill:
                    img = base_image.resize((pixel_size, pixel_size), Image.Resampling.LANCZOS)
                else:
                    continue
                
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Ensure correct size
                if img.size != (pixel_size, pixel_size):
                    img = img.resize((pixel_size, pixel_size), Image.Resampling.LANCZOS)
                
                # Save PNG
                icon_path = os.path.join(appiconset_folder, filename)
                img.save(icon_path, format='PNG', optimize=True)
                generated_files.append(filename)
                
                # Add to Contents.json images array
                size_str = f"{int(base)}x{int(base)}" if base == int(base) else f"{base}x{base}"
                contents_images.append({
                    "size": size_str,
                    "idiom": idiom,
                    "filename": filename,
                    "scale": f"{scale}x"
                })
            
            if not generated_files:
                return False, "No valid sizes could be generated", {}
            
            # Generate Contents.json
            contents = {
                "images": contents_images,
                "info": {
                    "version": 1,
                    "author": "RNV Icon Builder"
                }
            }
            
            contents_path = os.path.join(appiconset_folder, "Contents.json")
            with open(contents_path, 'w', encoding='utf-8') as f:
                json.dump(contents, f, indent=2)
            generated_files.append("Contents.json")
            
            logger.success(f"iOS App Icons exported: {len(generated_files)} file(s)")
            
            return True, "iOS App Icons exported successfully", {
                'output_folder': appiconset_folder,
                'files': generated_files,
                'file_count': len(generated_files)
            }
            
        except Exception as e:
            logger.error(f"Failed to export iOS icons: {e}", error=e)
            return False, f"Failed to export iOS icons: {str(e)}", {}


# ==================== Module Exports ====================

__all__: list[str] = [
    'IconBuilderCore',
]