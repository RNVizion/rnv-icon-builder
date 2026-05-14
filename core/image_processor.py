"""
RNV Icon Builder - Image Processor Module
Handles loading and processing PNG, ICO, and SVG files with safe error handling.

Features:
- Load and validate PNG files
- Extract frames from ICO files
- Render SVG files at multiple resolutions
- Image size validation
- Statistics and summaries
- Undo/Redo support for adjustments
- Brightness/Contrast/Saturation adjustments
- Grayscale conversion
"""

from __future__ import annotations

import io
from typing import Any, Callable

from PIL import Image

# PyQt6 imports for SVG rendering
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer

from utils.config import ICON_SIZES
from utils.logger import Logger, get_logger_instance
from utils.error_handler import ErrorHandler, ErrorCategory, safe_method, exception_handler

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)

# Maximum number of undo states to keep (prevents memory issues)
MAX_UNDO_STATES: int = 20


class ImageProcessor:
    """
    Handles loading and validating image files for icon building.
    
    Supports PNG, ICO, and SVG files. SVG files are rendered at all
    standard icon sizes for crisp, resolution-independent icons.
    
    Attributes:
        detected_images: Dictionary mapping size (int) to PIL Image
        _undo_stack: Stack of previous image states for undo
        _redo_stack: Stack of undone states for redo
        
    Example:
        >>> processor = ImageProcessor()
        >>> processor.load_png("icon_256.png")
        >>> processor.load_ico("existing.ico")
        >>> processor.load_svg("icon.svg")  # Renders at all sizes
        >>> images = processor.get_detected_images()
    """
    
    def __init__(self) -> None:
        """Initialize the image processor with empty image dictionary."""
        self.detected_images: dict[int, Image.Image] = {}
        self._undo_stack: list[dict[int, Image.Image]] = []
        self._redo_stack: list[dict[int, Image.Image]] = []
        logger.debug("ImageProcessor initialized")
    
    @safe_method(operation_name="Loading PNG file", show_error=True, default_return=False)
    def load_png(self, file_path: str) -> bool:
        """
        Load a PNG file and validate its size.
        
        Only accepts square images that match ICON_SIZES.
        
        Args:
            file_path: Path to PNG file
            
        Returns:
            True if successfully loaded and valid
            
        Raises:
            Exception: If file cannot be opened or processed
            
        Note:
            @safe_method decorator automatically handles exceptions
            
        Example:
            >>> processor = ImageProcessor()
            >>> if processor.load_png("icon_256.png"):
            ...     print("Loaded successfully!")
        """
        # Use context manager to ensure file handle is properly closed
        with Image.open(file_path) as img:
            img.load()  # Load image data into memory
            w, h = img.size
            
            # Only accept square images
            if w != h:
                logger.warning(f"Skipped {file_path}: Not square ({w}x{h})")
                return False
            
            # Only accept standard icon sizes
            if w in ICON_SIZES:
                self.detected_images[w] = img.copy()
                logger.success(f"Loaded {w}x{w} from: {file_path}")
                return True
            else:
                logger.warning(f"Skipped {file_path}: Size {w}x{w} not in standard sizes")
                return False
    
    def load_ico(self, file_path: str) -> int:
        """
        Load an ICO file and extract all valid frames.
        
        Supports multi-frame ICO files.
        
        Args:
            file_path: Path to ICO file
            
        Returns:
            Number of valid frames loaded
            
        Example:
            >>> processor = ImageProcessor()
            >>> count = processor.load_ico("app.ico")
            >>> print(f"Loaded {count} sizes from ICO")
        """
        loaded_count: int = 0
        
        # Use ErrorHandler.safe_execute for more control
        success, im = ErrorHandler.safe_execute(
            func=Image.open,
            operation_name=f"Opening ICO file: {file_path}",
            args=(file_path,),
            show_error_dialog=False,  # We'll handle errors manually
            error_category=ErrorCategory.IMAGE_PROCESSING
        )
        
        if not success or im is None:
            logger.error(f"Failed to open ICO file: {file_path}")
            return 0
        
        # Try to load all frames from the ICO file
        n_frames: int = getattr(im, 'n_frames', 1)
        for frame_idx in range(n_frames):
            # Use context manager for safe frame loading
            with exception_handler(f"Loading ICO frame {frame_idx}", show_error=False):
                im.seek(frame_idx)
                w, h = im.size
                
                # Only accept square images that match our sizes
                if w == h and w in ICON_SIZES:
                    self.detected_images[w] = im.copy()
                    logger.success(f"Loaded {w}x{w} from ICO frame {frame_idx}: {file_path}")
                    loaded_count += 1
                else:
                    logger.warning(f"Skipped ICO frame {frame_idx}: {w}x{h}")
        
        if loaded_count > 0:
            logger.info(f"Loaded {loaded_count} frame(s) from ICO file")
        else:
            logger.warning(f"No valid frames found in ICO file: {file_path}")
        
        return loaded_count
    
    def load_svg(self, file_path: str) -> int:
        """
        Load an SVG file and render it at all standard icon sizes.
        
        SVG files are rendered at each ICON_SIZE for crisp, resolution-independent icons.
        
        Args:
            file_path: Path to SVG file
            
        Returns:
            Number of sizes successfully rendered
            
        Example:
            >>> processor = ImageProcessor()
            >>> count = processor.load_svg("icon.svg")
            >>> print(f"Rendered {count} sizes from SVG")
        """
        logger.info(f"Loading SVG file: {file_path}")
        loaded_count: int = 0
        
        try:
            # Read SVG file content
            with open(file_path, 'rb') as f:
                svg_data = f.read()
            
            # Create SVG renderer
            renderer = QSvgRenderer(QByteArray(svg_data))
            
            if not renderer.isValid():
                logger.error(f"Invalid SVG file: {file_path}")
                return 0
            
            # Get original SVG dimensions for aspect ratio
            svg_size = renderer.defaultSize()
            logger.debug(f"SVG default size: {svg_size.width()}x{svg_size.height()}")
            
            # Render at each standard icon size
            for size in ICON_SIZES:
                try:
                    # Create QImage with transparent background
                    qimage = QImage(size, size, QImage.Format.Format_ARGB32)
                    qimage.fill(Qt.GlobalColor.transparent)
                    
                    # Render SVG to QImage
                    painter = QPainter(qimage)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    renderer.render(painter)
                    painter.end()
                    
                    # Convert QImage to PIL Image
                    pil_image = self._qimage_to_pil(qimage)
                    
                    if pil_image:
                        self.detected_images[size] = pil_image
                        loaded_count += 1
                        logger.debug(f"Rendered SVG at {size}x{size}")
                    else:
                        logger.warning(f"Failed to convert {size}x{size} to PIL Image")
                        
                except Exception as e:
                    logger.warning(f"Error rendering SVG at {size}x{size}: {e}")
            
            if loaded_count > 0:
                logger.success(f"Rendered {loaded_count} sizes from SVG: {file_path}")
            else:
                logger.error(f"Failed to render any sizes from SVG: {file_path}")
            
        except FileNotFoundError:
            logger.error(f"SVG file not found: {file_path}")
        except PermissionError:
            logger.error(f"Permission denied: {file_path}")
        except Exception as e:
            logger.error(f"Error loading SVG: {e}")
            logger.exception("Full SVG load error:")
        
        return loaded_count
    
    def _qimage_to_pil(self, qimage: QImage) -> Image.Image | None:
        """
        Convert a QImage to a PIL Image.
        
        Args:
            qimage: QImage to convert
            
        Returns:
            PIL Image or None on failure
        """
        try:
            # Ensure ARGB32 format
            if qimage.format() != QImage.Format.Format_ARGB32:
                qimage = qimage.convertToFormat(QImage.Format.Format_ARGB32)
            
            width = qimage.width()
            height = qimage.height()
            
            # Get raw bytes
            ptr = qimage.bits()
            ptr.setsize(height * width * 4)
            
            # Create PIL Image from raw ARGB data
            # QImage uses ARGB (or BGRA in memory), PIL needs RGBA
            pil_image = Image.frombuffer(
                'RGBA',
                (width, height),
                bytes(ptr),
                'raw',
                'BGRA',  # QImage stores as BGRA
                0,
                1
            )
            
            return pil_image.copy()  # Return a copy to avoid memory issues
            
        except Exception as e:
            logger.error(f"QImage to PIL conversion failed: {e}")
            return None
    
    def validate_size(self, width: int, height: int) -> bool:
        """
        Check if image dimensions are valid for icon building.
        
        Args:
            width: Image width
            height: Image height
            
        Returns:
            True if valid square image in ICON_SIZES
            
        Example:
            >>> processor = ImageProcessor()
            >>> processor.validate_size(256, 256)  # True
            >>> processor.validate_size(100, 100)  # False
        """
        is_valid: bool = width == height and width in ICON_SIZES
        if is_valid:
            logger.debug(f"Size {width}x{height} validated successfully")
        else:
            logger.debug(f"Size {width}x{height} is not valid")
        return is_valid
    
    def get_detected_images(self) -> dict[int, Image.Image]:
        """
        Get dictionary of all detected images.
        
        Returns:
            Dictionary mapping size (int) to PIL Image object
            
        Example:
            >>> images = processor.get_detected_images()
            >>> for size, img in images.items():
            ...     print(f"Size: {size}x{size}")
        """
        logger.debug(f"Returning {len(self.detected_images)} detected images")
        return self.detected_images
    
    def clear_images(self) -> None:
        """
        Clear all loaded images and undo/redo history.
        
        Example:
            >>> processor.clear_images()
        """
        count: int = len(self.detected_images)
        self.detected_images.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        logger.success(f"Cleared {count} image(s) and history")
    
    # ==================== Undo/Redo Methods ====================
    
    def _save_state(self) -> None:
        """
        Save current state to undo stack before making changes.
        
        Called internally by apply_* methods before modifications.
        Clears redo stack since new changes invalidate redo history.
        """
        if not self.detected_images:
            return
        
        # Deep copy current images
        state = {size: img.copy() for size, img in self.detected_images.items()}
        self._undo_stack.append(state)
        
        # Limit stack size to prevent memory issues
        if len(self._undo_stack) > MAX_UNDO_STATES:
            self._undo_stack.pop(0)
        
        # Clear redo stack - new changes invalidate redo history
        self._redo_stack.clear()
        
        logger.debug(f"Saved state to undo stack (depth: {len(self._undo_stack)})")
    
    def undo(self) -> bool:
        """
        Undo the last adjustment operation.
        
        Returns:
            True if undo was successful, False if nothing to undo
            
        Example:
            >>> if processor.undo():
            ...     print("Undone!")
        """
        if not self._undo_stack:
            logger.warning("Nothing to undo")
            return False
        
        # Save current state to redo stack
        if self.detected_images:
            redo_state = {size: img.copy() for size, img in self.detected_images.items()}
            self._redo_stack.append(redo_state)
        
        # Restore previous state
        self.detected_images = self._undo_stack.pop()
        
        logger.success(f"Undo successful (remaining: {len(self._undo_stack)})")
        return True
    
    def redo(self) -> bool:
        """
        Redo a previously undone adjustment operation.
        
        Returns:
            True if redo was successful, False if nothing to redo
            
        Example:
            >>> if processor.redo():
            ...     print("Redone!")
        """
        if not self._redo_stack:
            logger.warning("Nothing to redo")
            return False
        
        # Save current state to undo stack
        if self.detected_images:
            undo_state = {size: img.copy() for size, img in self.detected_images.items()}
            self._undo_stack.append(undo_state)
        
        # Restore redo state
        self.detected_images = self._redo_stack.pop()
        
        logger.success(f"Redo successful (remaining: {len(self._redo_stack)})")
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0
    
    def get_undo_count(self) -> int:
        """Get number of available undo steps."""
        return len(self._undo_stack)
    
    def get_redo_count(self) -> int:
        """Get number of available redo steps."""
        return len(self._redo_stack)
    
    def has_size(self, size: int) -> bool:
        """
        Check if a specific size exists in detected images.
        
        Args:
            size: Size to check
            
        Returns:
            True if size exists
            
        Example:
            >>> if processor.has_size(256):
            ...     print("256x256 is available")
        """
        exists: bool = size in self.detected_images
        logger.debug(f"Size {size}x{size} {'exists' if exists else 'does not exist'}")
        return exists
    
    def get_largest_size(self) -> int | None:
        """
        Get the largest available size from detected images.
        
        Returns:
            Largest size or None if no images
            
        Example:
            >>> largest = processor.get_largest_size()
            >>> if largest:
            ...     print(f"Largest: {largest}x{largest}")
        """
        if self.detected_images:
            largest: int = max(self.detected_images.keys())
            logger.debug(f"Largest size: {largest}x{largest}")
            return largest
        logger.debug("No images available, returning None")
        return None
    
    def get_image(self, size: int) -> Image.Image | None:
        """
        Get image for specific size.
        
        Args:
            size: Requested size
            
        Returns:
            PIL Image object or None if not found
            
        Example:
            >>> img = processor.get_image(64)
            >>> if img:
            ...     img.save("icon_64.png")
        """
        img: Image.Image | None = self.detected_images.get(size)
        if img:
            logger.debug(f"Retrieved image for size {size}x{size}")
        else:
            logger.debug(f"No image found for size {size}x{size}")
        return img
    
    def get_available_sizes(self) -> list[int]:
        """
        Get list of all available sizes.
        
        Returns:
            Sorted list of available sizes (largest first)
            
        Example:
            >>> sizes = processor.get_available_sizes()
            >>> print(f"Available: {sizes}")  # [256, 128, 64]
        """
        sizes: list[int] = sorted(self.detected_images.keys(), reverse=True)
        logger.debug(f"Available sizes: {sizes}")
        return sizes
    
    def get_missing_sizes(self) -> list[int]:
        """
        Get list of standard sizes not yet loaded.
        
        Returns:
            List of missing sizes from ICON_SIZES
            
        Example:
            >>> missing = processor.get_missing_sizes()
            >>> print(f"Need to add: {missing}")
        """
        missing: list[int] = [s for s in ICON_SIZES if s not in self.detected_images]
        logger.debug(f"Missing sizes: {missing}")
        return missing
    
    def remove_size(self, size: int) -> bool:
        """
        Remove a specific size from detected images.
        
        Args:
            size: Size to remove
            
        Returns:
            True if removed, False if didn't exist
            
        Example:
            >>> if processor.remove_size(16):
            ...     print("Removed 16x16")
        """
        if size in self.detected_images:
            del self.detected_images[size]
            logger.success(f"Removed {size}x{size}")
            return True
        logger.warning(f"Cannot remove {size}x{size} - does not exist")
        return False
    
    def get_summary(self) -> str:
        """
        Get summary of loaded images.
        
        Returns:
            Human-readable summary string
            
        Example:
            >>> print(processor.get_summary())
            "3 sizes: 256x256, 128x128, 64x64"
        """
        if not self.detected_images:
            summary: str = "No images loaded"
        else:
            sizes: list[int] = sorted(self.detected_images.keys(), reverse=True)
            size_str: str = ", ".join(f"{s}x{s}" for s in sizes)
            summary = f"{len(sizes)} sizes: {size_str}"
        
        logger.debug(f"Image summary: {summary}")
        return summary
    
    def get_statistics(self) -> dict[str, Any]:
        """
        Get detailed statistics about loaded images.
        
        Returns:
            Dictionary with statistics
            
        Example:
            >>> stats = processor.get_statistics()
            >>> print(f"Total: {stats['count']} images")
        """
        stats: dict[str, Any] = {
            'count': len(self.detected_images),
            'sizes': self.get_available_sizes(),
            'missing': self.get_missing_sizes(),
            'largest': self.get_largest_size(),
            'smallest': min(self.detected_images.keys()) if self.detected_images else None,
            'coverage': len(self.detected_images) / len(ICON_SIZES) * 100,
        }
        logger.debug(f"Statistics: {stats}")
        return stats
    
    def can_autofill(self, target_size: int) -> bool:
        """
        Check if a target size can be auto-filled from a larger image.
        
        Args:
            target_size: Size to check
            
        Returns:
            True if can be auto-filled
            
        Example:
            >>> if processor.can_autofill(32):
            ...     print("32x32 can be generated from larger image")
        """
        largest: int | None = self.get_largest_size()
        if largest is None:
            return False
        return target_size < largest and target_size not in self.detected_images
    
    def get_autofill_source(self, target_size: int) -> int | None:
        """
        Get the source size for auto-filling a target size.
        
        Args:
            target_size: Size to auto-fill
            
        Returns:
            Source size to use, or None if not possible
            
        Example:
            >>> source = processor.get_autofill_source(32)
            >>> if source:
            ...     print(f"Will resize from {source}x{source}")
        """
        if target_size in self.detected_images:
            return None  # Already have this size
        
        # Find smallest available size larger than target
        larger_sizes: list[int] = [s for s in self.detected_images.keys() if s > target_size]
        if larger_sizes:
            return min(larger_sizes)
        return None
    
    # ==================== Image Adjustment Methods ====================
    
    def _apply_to_all_images(
        self,
        transform_func: Callable[[Image.Image], Image.Image],
        operation_name: str,
        save_state: bool = True,
        check_modified: Callable[[Image.Image, Image.Image], bool] | None = None
    ) -> int:
        """
        Apply a transformation function to all loaded images.
        
        This helper consolidates the common pattern used by apply_* methods:
        1. Optionally save state for undo
        2. Iterate over all images
        3. Apply transformation
        4. Count modified images
        5. Log result
        
        Args:
            transform_func: Function that takes an image and returns transformed image
            operation_name: Human-readable name for logging
            save_state: Whether to save state for undo (default: True)
            check_modified: Optional function to check if image was actually modified.
                           Takes (original, transformed) and returns True if modified.
                           If None, all images are counted as modified.
        
        Returns:
            Number of images modified
            
        Example:
            >>> def grayscale(img): return img.convert('LA').convert('RGBA')
            >>> count = self._apply_to_all_images(grayscale, "grayscale conversion")
        """
        if not self.detected_images:
            logger.debug(f"No images to apply {operation_name}")
            return 0
        
        if save_state:
            self._save_state()
        
        modified = 0
        for size in list(self.detected_images.keys()):
            original_img = self.detected_images[size]
            transformed_img = transform_func(original_img)
            
            # Check if actually modified (if checker provided)
            if check_modified is not None:
                if check_modified(original_img, transformed_img):
                    self.detected_images[size] = transformed_img
                    modified += 1
            else:
                self.detected_images[size] = transformed_img
                modified += 1
        
        logger.info(f"{operation_name} applied to {modified} image(s)")
        return modified
    
    def apply_auto_crop(self) -> int:
        """
        Apply auto-crop to all loaded images.
        
        Removes transparent borders from each image.
        
        Returns:
            Number of images modified
        """
        from ui.image_adjustments import auto_crop
        
        return self._apply_to_all_images(
            transform_func=auto_crop,
            operation_name="Auto-crop",
            check_modified=lambda orig, cropped: cropped.size != orig.size
        )
    
    def apply_padding(self, padding: int) -> int:
        """
        Add padding to all loaded images.
        
        Args:
            padding: Pixels of padding to add
            
        Returns:
            Number of images modified
        """
        from ui.image_adjustments import add_padding
        
        return self._apply_to_all_images(
            transform_func=lambda img: add_padding(img, padding),
            operation_name=f"{padding}px padding"
        )
    
    def apply_center_resize(self, target_size: int, maintain_aspect: bool = True) -> int:
        """
        Center and resize all images to target size.
        
        Args:
            target_size: Target width and height
            maintain_aspect: If True, maintain aspect ratio
            
        Returns:
            Number of images modified
        """
        from ui.image_adjustments import center_content, resize_to_fit
        
        self._save_state()  # Save for undo
        
        modified = 0
        
        # Process each image and store in new dict
        new_images: dict[int, Image.Image] = {}
        
        for size in list(self.detected_images.keys()):
            img = self.detected_images[size]
            
            if maintain_aspect:
                # Center content in target size
                adjusted = center_content(img, target_size)
            else:
                # Resize to fit (stretch)
                adjusted = resize_to_fit(img, target_size, maintain_aspect=False)
            
            # Store with new size key
            new_images[target_size] = adjusted
            modified += 1
        
        # Replace all images with single resized image
        self.detected_images.clear()
        self.detected_images.update(new_images)
        
        logger.info(f"Center & resize to {target_size}x{target_size} applied")
        return modified
    
    def apply_rotate(self, degrees: int) -> int:
        """
        Rotate all loaded images by specified degrees.
        
        Args:
            degrees: Rotation angle (90, 180, 270, -90, -180, -270)
            
        Returns:
            Number of images modified
        """
        from ui.image_adjustments import rotate_image
        
        return self._apply_to_all_images(
            transform_func=lambda img: rotate_image(img, degrees),
            operation_name=f"Rotation by {degrees} degrees"
        )
    
    def apply_flip_horizontal(self) -> int:
        """
        Flip all loaded images horizontally (mirror).
        
        Returns:
            Number of images modified
        """
        from ui.image_adjustments import flip_horizontal
        
        return self._apply_to_all_images(
            transform_func=flip_horizontal,
            operation_name="Horizontal flip"
        )
    
    def apply_flip_vertical(self) -> int:
        """
        Flip all loaded images vertically.
        
        Returns:
            Number of images modified
        """
        from ui.image_adjustments import flip_vertical
        
        return self._apply_to_all_images(
            transform_func=flip_vertical,
            operation_name="Vertical flip"
        )
    
    def apply_fill_transparency(self, color: tuple[int, int, int, int]) -> int:
        """
        Fill transparent areas with a solid color in all loaded images.
        
        Args:
            color: RGBA color tuple (r, g, b, a)
            
        Returns:
            Number of images modified
        """
        from ui.image_adjustments import fill_transparency
        
        return self._apply_to_all_images(
            transform_func=lambda img: fill_transparency(img, color),
            operation_name=f"Fill transparency with color {color[:3]}"
        )
    
    def apply_add_border(self, width: int, color: tuple[int, int, int, int]) -> int:
        """
        Add a border around all loaded images.
        
        Args:
            width: Border width in pixels
            color: RGBA color tuple (r, g, b, a)
            
        Returns:
            Number of images modified
        """
        from ui.image_adjustments import add_border
        
        return self._apply_to_all_images(
            transform_func=lambda img: add_border(img, width, color),
            operation_name=f"{width}px border"
        )
    
    def apply_color_adjustments(self, brightness: int, contrast: int, saturation: int) -> int:
        """
        Apply brightness, contrast, and saturation adjustments to all loaded images.
        
        Uses the optimized single-pass combined adjustment function that splits
        the alpha channel once, applies all enhancers, and recombines once -
        reducing intermediate image allocations.
        
        Args:
            brightness: Brightness value (-100 to +100)
            contrast: Contrast value (-100 to +100)
            saturation: Saturation value (-100 to +100)
            
        Returns:
            Number of images modified
        """
        from ui.image_adjustments import apply_combined_adjustments
        
        # Only save state if at least one value is non-zero
        if brightness == 0 and contrast == 0 and saturation == 0:
            return 0
        
        self._save_state()  # Save for undo
        
        modified = 0
        for size in list(self.detected_images.keys()):
            img = self.detected_images[size]
            
            # Apply all adjustments in a single pass 
            img = apply_combined_adjustments(img, brightness, contrast, saturation)
            
            self.detected_images[size] = img
            modified += 1
        
        logger.info(f"Applied color adjustments (B:{brightness:+d}, C:{contrast:+d}, S:{saturation:+d}) to {modified} image(s)")
        return modified
    
    def apply_grayscale(self) -> int:
        """
        Convert all loaded images to grayscale while preserving alpha.
        
        Returns:
            Number of images modified
        """
        from ui.image_adjustments import convert_grayscale
        
        return self._apply_to_all_images(
            transform_func=convert_grayscale,
            operation_name="Grayscale conversion"
        )


# ==================== Module Exports ====================

__all__: list[str] = [
    'ImageProcessor',
]