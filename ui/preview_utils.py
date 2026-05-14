"""
RNV Icon Builder - Preview Utilities Module
Provides image preview enhancements including transparency visualization,
zoom functionality, and comparison views.

Features:
- Transparency checkerboard pattern generation
- Background preview options (white/black/custom color)
- Hover-to-zoom thumbnails
- Full-size preview popup
- Side-by-side original vs resized comparison
- Color palette extraction
- Zoom controls
"""

from __future__ import annotations

import io
from typing import Any
from collections import Counter

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QWidget, QSizePolicy, QToolTip, QApplication,
    QSlider, QPushButton, QComboBox, QColorDialog, QGridLayout
)
from PyQt6.QtCore import Qt, QPoint, QTimer, QEvent, QSize, QRect, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QCursor, QClipboard

from PIL import Image

from utils.config import (
    THUMBNAIL_SIZE, TRANSPARENCY_CHECKERBOARD_SIZE,
    PREVIEW_BG_CHECKERBOARD, PREVIEW_BG_WHITE, PREVIEW_BG_BLACK, PREVIEW_BG_CUSTOM,
    PREVIEW_BACKGROUND_OPTIONS, DEFAULT_PREVIEW_BACKGROUND,
    ZOOM_MIN, ZOOM_MAX, ZOOM_DEFAULT, ZOOM_STEP, COLOR_PALETTE_SIZE, COLOR_SWATCH_SIZE,
    THUMBNAIL_CACHE_MAX_SIZE, DEBUG_MODE
)
from utils.logger import Logger, get_logger_instance
from utils.pixmap_cache import ThumbnailCache
from ui.base_dialog import BaseDialog
from ui.colors import (
    BRAND_GOLD, BRAND_GOLD_DARK, get_theme_colors,
    CONTRAST_ON_LIGHT, CONTRAST_ON_DARK, DARK_THEME_COLORS,
    DEFAULT_CUSTOM_BG_COLOR,
)

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)

# Global thumbnail cache for performance optimization
# Caches generated thumbnails to avoid repeated processing
# Size configured via THUMBNAIL_CACHE_MAX_SIZE in config.py
_thumbnail_cache: ThumbnailCache = ThumbnailCache(max_size=THUMBNAIL_CACHE_MAX_SIZE)


# ==================== Checkerboard Pattern ====================

def create_checkerboard_pattern(
    width: int,
    height: int,
    square_size: int = TRANSPARENCY_CHECKERBOARD_SIZE,
    color1: tuple[int, int, int] = (255, 255, 255),
    color2: tuple[int, int, int] = (204, 204, 204)
) -> Image.Image:
    """
    Create a checkerboard pattern image for transparency visualization.
    
    Args:
        width: Pattern width in pixels
        height: Pattern height in pixels
        square_size: Size of each checker square
        color1: First checker color (default: white)
        color2: Second checker color (default: light gray)
        
    Returns:
        PIL Image with checkerboard pattern
        
    Example:
        >>> pattern = create_checkerboard_pattern(256, 256)
        >>> pattern.size
        (256, 256)
    """
    # Create RGB image (no alpha needed for background)
    pattern = Image.new('RGB', (width, height))
    
    for y in range(0, height, square_size):
        for x in range(0, width, square_size):
            # Determine color based on position
            is_even_row = (y // square_size) % 2 == 0
            is_even_col = (x // square_size) % 2 == 0
            
            color = color1 if (is_even_row == is_even_col) else color2
            
            # Fill the square
            for dy in range(min(square_size, height - y)):
                for dx in range(min(square_size, width - x)):
                    pattern.putpixel((x + dx, y + dy), color)
    
    return pattern


def composite_on_checkerboard(
    image: Image.Image,
    square_size: int = TRANSPARENCY_CHECKERBOARD_SIZE,
    color1: tuple[int, int, int] = (255, 255, 255),
    color2: tuple[int, int, int] = (204, 204, 204)
) -> Image.Image:
    """
    Composite an image with alpha channel onto a checkerboard pattern.
    
    This makes transparent and semi-transparent areas visible.
    
    Args:
        image: Input image (should have alpha channel)
        square_size: Size of checker squares
        color1: First checker color
        color2: Second checker color
        
    Returns:
        RGB image with transparency visualized on checkerboard
        
    Example:
        >>> img = Image.open("icon.png")
        >>> preview = composite_on_checkerboard(img)
        >>> preview.mode
        'RGB'
    """
    # Ensure image has alpha channel
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Create checkerboard pattern
    checkerboard = create_checkerboard_pattern(
        image.width, image.height, square_size, color1, color2
    )
    
    # Convert checkerboard to RGBA for compositing
    checkerboard = checkerboard.convert('RGBA')
    
    # Composite the image onto the checkerboard
    result = Image.alpha_composite(checkerboard, image)
    
    # Convert back to RGB (no alpha needed for display)
    return result.convert('RGB')


# ==================== Background Options ====================

def composite_on_color(
    image: Image.Image,
    color: tuple[int, int, int] = (255, 255, 255)
) -> Image.Image:
    """
    Composite an image with alpha channel onto a solid color background.
    
    Args:
        image: Input image (should have alpha channel)
        color: RGB color tuple for background
        
    Returns:
        RGB image with transparency replaced by solid color
    """
    # Ensure image has alpha channel
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Create solid color background
    background = Image.new('RGBA', image.size, (*color, 255))
    
    # Composite the image onto the background
    result = Image.alpha_composite(background, image)
    
    return result.convert('RGB')


def composite_with_background(
    image: Image.Image,
    background_type: str = PREVIEW_BG_CHECKERBOARD,
    custom_color: tuple[int, int, int] | None = None
) -> Image.Image:
    """
    Composite an image with the specified background type.
    
    Args:
        image: Input image (should have alpha channel)
        background_type: One of 'checkerboard', 'white', 'black', 'custom'
        custom_color: RGB color tuple for custom background
        
    Returns:
        RGB image with appropriate background
    """
    if background_type == PREVIEW_BG_CHECKERBOARD:
        return composite_on_checkerboard(image)
    elif background_type == PREVIEW_BG_WHITE:
        return composite_on_color(image, (255, 255, 255))
    elif background_type == PREVIEW_BG_BLACK:
        return composite_on_color(image, (0, 0, 0))
    elif background_type == PREVIEW_BG_CUSTOM and custom_color:
        return composite_on_color(image, custom_color)
    else:
        # Default to checkerboard
        return composite_on_checkerboard(image)


# ==================== Color Palette Extraction ====================

def extract_dominant_colors(
    image: Image.Image,
    count: int = COLOR_PALETTE_SIZE,
    ignore_transparent: bool = True
) -> list[tuple[tuple[int, int, int], int]]:
    """
    Extract dominant colors from an image using color quantization.
    
    Uses k-means style quantization via PIL's built-in method.
    
    Args:
        image: PIL Image to analyze
        count: Number of colors to extract
        ignore_transparent: If True, ignore fully transparent pixels
        
    Returns:
        List of tuples: ((r, g, b), pixel_count) sorted by frequency
    """
    # Convert to RGBA if needed
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Get pixel data
    pixels = list(image.getdata())
    
    # Filter out transparent pixels if requested
    if ignore_transparent:
        pixels = [p for p in pixels if p[3] > 0]  # Alpha > 0
    
    if not pixels:
        return []
    
    # Convert to RGB for color counting
    rgb_pixels = [(p[0], p[1], p[2]) for p in pixels]
    
    # Use quantization for better color grouping
    # Create a smaller image for faster processing
    thumb = image.copy()
    thumb.thumbnail((100, 100))
    
    # Convert to P mode (palette) with limited colors
    try:
        quantized = thumb.convert('P', palette=Image.Palette.ADAPTIVE, colors=count * 2)
        palette = quantized.getpalette()
        
        if palette:
            # Get color counts from the quantized image
            color_counts: Counter = Counter()
            for p in quantized.getdata():
                idx = p * 3
                if idx + 2 < len(palette):
                    color = (palette[idx], palette[idx + 1], palette[idx + 2])
                    color_counts[color] += 1
            
            # Get top colors
            top_colors = color_counts.most_common(count)
            return top_colors
    except Exception as e:
        logger.debug(f"Quantization failed, using direct counting: {e}")
    
    # Fallback: direct color counting with color binning
    # Bin colors to reduce noise (group similar colors)
    bin_size = 16
    binned_counts: Counter = Counter()
    
    for r, g, b in rgb_pixels:
        # Bin to nearest multiple of bin_size
        binned = (
            (r // bin_size) * bin_size,
            (g // bin_size) * bin_size,
            (b // bin_size) * bin_size
        )
        binned_counts[binned] += 1
    
    return binned_counts.most_common(count)


def color_to_hex(color: tuple[int, int, int]) -> str:
    """
    Convert RGB color tuple to hex string.
    
    Args:
        color: RGB tuple (r, g, b)
        
    Returns:
        Hex color string like '#FF0000'
    """
    return f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"


def hex_to_color(hex_str: str) -> tuple[int, int, int]:
    """
    Convert hex color string to RGB tuple.
    
    Args:
        hex_str: Hex color string like '#FF0000' or 'FF0000'
        
    Returns:
        RGB tuple (r, g, b)
    """
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


def pil_to_qpixmap(image: Image.Image) -> QPixmap:
    """
    Convert PIL Image to QPixmap.
    
    Args:
        image: PIL Image object
        
    Returns:
        QPixmap object
    """
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    
    pixmap = QPixmap()
    pixmap.loadFromData(buffer.getvalue())
    return pixmap


def get_cached_thumbnail(
    source_path: str,
    image: Image.Image,
    size: int,
    show_checkerboard: bool = True,
    variant: str = "default"
) -> QPixmap:
    """
    Get or create a cached thumbnail pixmap.
    
    Uses the global thumbnail cache to avoid repeatedly generating
    the same thumbnails, improving performance when scrolling
    or switching between views.
    
    Args:
        source_path: Path to source image (for cache key)
        image: PIL Image to create thumbnail from
        size: Target thumbnail size
        show_checkerboard: Whether to composite on checkerboard
        variant: Optional variant name (e.g., "hover", "selected")
        
    Returns:
        Cached or newly created QPixmap
        
    Example:
        pixmap = get_cached_thumbnail(
            "/path/to/icon.png",
            my_image,
            64,
            show_checkerboard=True
        )
    """
    cache_variant = f"{variant}_checker" if show_checkerboard else variant
    
    # Check if we have a cache hit before creating (for debug logging)
    cache_key = (source_path, size, cache_variant)
    is_cached = _thumbnail_cache.contains(cache_key)
    
    def create_thumbnail() -> QPixmap:
        """Create the thumbnail pixmap."""
        thumb = image.resize((size, size), Image.Resampling.LANCZOS)
        
        if show_checkerboard:
            display_image = composite_on_checkerboard(thumb)
        else:
            display_image = thumb.convert('RGB') if thumb.mode != 'RGB' else thumb
        
        return pil_to_qpixmap(display_image)
    
    result = _thumbnail_cache.get_thumbnail(
        source_path,
        size,
        create_thumbnail,
        variant=cache_variant
    )
    
    # Log cache activity in debug mode
    if DEBUG_MODE and not is_cached:
        stats = _thumbnail_cache.get_stats()
        logger.debug(
            f"Thumbnail cache miss: {size}x{size} [{cache_variant}] "
            f"(cache: {stats['size']}/{stats['max_size']}, "
            f"hit rate: {stats['hit_rate']:.0f}%)"
        )
    
    return result


def clear_thumbnail_cache() -> int:
    """
    Clear the thumbnail cache.
    
    Call this when loading new images or when memory is needed.
    
    Returns:
        Number of thumbnails cleared
    """
    # Log final stats before clearing in debug mode
    if DEBUG_MODE:
        stats = _thumbnail_cache.get_stats()
        if stats['size'] > 0:
            logger.debug(
                f"Thumbnail cache stats before clear: "
                f"{stats['size']}/{stats['max_size']} entries, "
                f"hits={stats['hits']}, misses={stats['misses']}, "
                f"hit rate={stats['hit_rate']:.0f}%, "
                f"evictions={stats['evictions']}"
            )
    
    count = _thumbnail_cache.clear()
    logger.debug(f"Cleared {count} cached thumbnails")
    return count


def get_thumbnail_cache_stats() -> dict:
    """
    Get thumbnail cache statistics.
    
    Returns:
        Dictionary with cache stats (size, hits, misses, hit_rate, etc.)
    """
    return _thumbnail_cache.get_stats()


# ==================== Zoom Preview Widget ====================

class ZoomPreviewWidget(QLabel):
    """
    A widget that shows a zoomed preview on hover.
    
    When the mouse hovers over a thumbnail, this widget displays
    a larger version near the cursor.
    
    Attributes:
        original_image: The full-size PIL Image
        zoom_factor: Multiplier for zoom size
        show_checkerboard: Whether to show transparency checkerboard
        
    Example:
        >>> label = ZoomPreviewWidget()
        >>> label.set_image(my_pil_image, show_checkerboard=True)
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the zoom preview widget."""
        super().__init__(parent)
        
        self.original_image: Image.Image | None = None
        self.original_size: int = 0
        self.zoom_factor: float = 2.0
        self.show_checkerboard: bool = True
        self.hover_timer: QTimer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._show_zoom_preview)
        self.hover_delay_ms: int = 300  # Delay before showing zoom
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Store image data for tag
        self.tag: str = ""
        self.size_value: int = 0
    
    def set_image(
        self,
        image: Image.Image,
        size: int,
        tag: str,
        show_checkerboard: bool = True
    ) -> None:
        """
        Set the image to display with zoom capability.
        
        Args:
            image: PIL Image to display
            size: Original icon size
            tag: Status tag (provided/autofill/missing)
            show_checkerboard: Whether to show checkerboard for transparency
        """
        self.original_image = image.copy()
        self.original_size = image.width
        self.size_value = size
        self.tag = tag
        self.show_checkerboard = show_checkerboard
        
        # Create thumbnail with checkerboard
        thumb = image.resize((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
        
        if show_checkerboard:
            display_image = composite_on_checkerboard(thumb)
        else:
            display_image = thumb.convert('RGB')
        
        # Set the pixmap
        pixmap = pil_to_qpixmap(display_image)
        self.setPixmap(pixmap)
        self.setFixedSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
    
    def enterEvent(self, event) -> None:
        """Handle mouse enter - start hover timer."""
        super().enterEvent(event)
        if self.original_image:
            self.hover_timer.start(self.hover_delay_ms)
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave - cancel hover timer and hide tooltip."""
        super().leaveEvent(event)
        self.hover_timer.stop()
        QToolTip.hideText()
    
    def _show_zoom_preview(self) -> None:
        """Show zoomed preview as tooltip."""
        if not self.original_image:
            return
        
        # Calculate zoom size (cap at reasonable maximum)
        zoom_size = min(int(self.original_size * self.zoom_factor), 256)
        
        # Create zoomed image
        zoomed = self.original_image.resize(
            (zoom_size, zoom_size),
            Image.Resampling.LANCZOS
        )
        
        if self.show_checkerboard:
            zoomed = composite_on_checkerboard(zoomed)
        else:
            zoomed = zoomed.convert('RGB')
        
        # Convert to QPixmap and show as rich tooltip
        pixmap = pil_to_qpixmap(zoomed)
        
        # Save to buffer for base64 tooltip image
        buffer = io.BytesIO()
        zoomed.save(buffer, format='PNG')
        import base64
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        tooltip_html = f'''
        <div style="padding: 5px;">
            <img src="data:image/png;base64,{img_data}" width="{zoom_size}" height="{zoom_size}">
            <br>
            <center><b>{self.size_value}x{self.size_value}</b> {self.tag}</center>
        </div>
        '''
        
        # Show tooltip at cursor position
        QToolTip.showText(QCursor.pos(), tooltip_html, self)
    
    def mouseDoubleClickEvent(self, event) -> None:
        """Handle double-click to show full preview dialog."""
        super().mouseDoubleClickEvent(event)
        if self.original_image:
            self._show_full_preview()
    
    def _show_full_preview(self) -> None:
        """Show full-size preview in a dialog."""
        if not self.original_image:
            return
        
        dialog = ImagePreviewDialog(
            self.original_image,
            self.size_value,
            self.tag,
            self.show_checkerboard,
            parent=self.window()
        )
        dialog.exec()


# ==================== Full Preview Dialog ====================

class ImagePreviewDialog(BaseDialog):
    """
    Dialog for full-size image preview with comparison view.
    
    Shows the image at actual size with transparency checkerboard.
    Includes side-by-side comparison option.
    
    Attributes:
        image: The PIL Image being previewed
        size: Original icon size
        tag: Status tag
        
    Example:
        >>> dialog = ImagePreviewDialog(image, 256, "(provided)")
        >>> dialog.exec()
    """
    
    def __init__(
        self,
        image: Image.Image,
        size: int,
        tag: str,
        show_checkerboard: bool = True,
        comparison_image: Image.Image | None = None,
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize the preview dialog.
        
        Args:
            image: Image to preview
            size: Icon size
            tag: Status tag
            show_checkerboard: Show transparency pattern
            comparison_image: Optional second image for comparison
            parent: Parent widget
        """
        # Calculate dialog size based on image before super().__init__
        dialog_width = max(300, size + 40)
        if comparison_image:
            dialog_width = max(500, size * 2 + 60)
        dialog_height = max(200, size + 100)
        
        super().__init__(
            parent=parent,
            title=f"Preview: {size}x{size} {tag}",
            modal=True,
            min_size=(dialog_width, dialog_height)
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self.image = image
        self.size = size
        self.tag = tag
        self.show_checkerboard = show_checkerboard
        self.comparison_image = comparison_image
        
        self._setup_ui()
        self._apply_theme(is_dark=self._is_dark_theme())
        
        logger.debug(f"Opened preview dialog for {size}x{size} {tag}")
    
    def closeEvent(self, event) -> None:
        """Clean up image references on close."""
        self.image = None
        self.comparison_image = None
        super().closeEvent(event)
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Create preview image
        preview_frame = self._create_preview_frame(
            self.image,
            f"Current ({self.size}x{self.size})"
        )
        content_layout.addWidget(preview_frame)
        
        # Add comparison if available
        if self.comparison_image:
            comparison_frame = self._create_preview_frame(
                self.comparison_image,
                f"Original ({self.comparison_image.width}x{self.comparison_image.height})"
            )
            content_layout.addWidget(comparison_frame)
        
        layout.addLayout(content_layout)
        
        # Info label
        info_text = f"Size: {self.size}x{self.size} pixels | Status: {self.tag}"
        if self.image.mode == 'RGBA':
            info_text += " | Has transparency"
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setObjectName("info_label")
        layout.addWidget(info_label)
    
    def _create_preview_frame(self, image: Image.Image, title: str) -> QFrame:
        """
        Create a framed preview for an image.
        
        Args:
            image: Image to display
            title: Title for the frame
            
        Returns:
            QFrame containing the preview
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setObjectName("preview_frame")
        
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("frame_title")
        frame_layout.addWidget(title_label)
        
        # Image display
        if self.show_checkerboard:
            display_image = composite_on_checkerboard(image)
        else:
            display_image = image.convert('RGB')
        
        pixmap = pil_to_qpixmap(display_image)
        
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("background-color: transparent;")
        frame_layout.addWidget(image_label)
        
        return frame
    
    def _apply_theme(self, is_dark: bool = True) -> None:
        """Apply theme styling to dialog."""
        colors = get_theme_colors(is_dark=is_dark)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['dialog_bg']};
            }}
            QFrame[objectName="preview_frame"] {{
                background-color: {colors['tab_bg']};
                border: 1px solid {colors['border_hover']};
                border-radius: 4px;
            }}
            QLabel[objectName="frame_title"] {{
                color: {colors['text_primary']};
                font-weight: bold;
                font-size: 12px;
            }}
            QLabel[objectName="info_label"] {{
                color: {colors['text_muted']};
                font-size: 11px;
                padding: 5px;
            }}
        """)
    
    def apply_theme_from_manager(self, theme_name: str) -> None:
        """Apply theme from theme manager."""
        self._apply_theme(is_dark=theme_name != 'light')


# ==================== Comparison Dialog ====================

class ComparisonDialog(BaseDialog):
    """
    Dialog showing side-by-side comparison of original vs resized images.
    
    Useful for seeing quality differences when downscaling.
    
    Example:
        >>> dialog = ComparisonDialog(original_256, resized_64, 64)
        >>> dialog.exec()
    """
    
    def __init__(
        self,
        original_image: Image.Image,
        resized_image: Image.Image,
        target_size: int,
        parent: QWidget | None = None
    ) -> None:
        """
        Initialize comparison dialog.
        
        Args:
            original_image: Source image (larger)
            resized_image: Resized image (smaller)
            target_size: Target size for the resized image
            parent: Parent widget
        """
        super().__init__(
            parent=parent,
            title=f"Comparison: Original vs {target_size}x{target_size}",
            modal=True,
            min_size=(400, 250)
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self.original = original_image
        self.resized = resized_image
        self.target_size = target_size
        
        self._setup_ui()
        self._apply_theme(is_dark=self._is_dark_theme())
    
    def closeEvent(self, event) -> None:
        """Clean up image references on close."""
        self.original = None
        self.resized = None
        super().closeEvent(event)
    
    def _setup_ui(self) -> None:
        """Setup the comparison UI."""
        layout = QVBoxLayout(self)
        
        # Side-by-side comparison
        comparison_layout = QHBoxLayout()
        
        # Original (scaled to match display size)
        original_frame = self._create_comparison_frame(
            self.original,
            f"Original ({self.original.width}x{self.original.height})",
            display_size=128
        )
        comparison_layout.addWidget(original_frame)
        
        # Arrow label
        arrow_label = QLabel("→")
        arrow_label.setObjectName("arrow_label")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comparison_layout.addWidget(arrow_label)
        
        # Resized (actual size and scaled up for comparison)
        resized_frame = self._create_comparison_frame(
            self.resized,
            f"Resized ({self.target_size}x{self.target_size})",
            display_size=128
        )
        comparison_layout.addWidget(resized_frame)
        
        layout.addLayout(comparison_layout)
        
        # Quality info
        info_label = QLabel(
            f"Scaling: {self.original.width}x{self.original.height} → "
            f"{self.target_size}x{self.target_size} "
            f"({100 * self.target_size / self.original.width:.1f}%)"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setObjectName("info_label")
        layout.addWidget(info_label)
    
    def _create_comparison_frame(
        self,
        image: Image.Image,
        title: str,
        display_size: int = 128
    ) -> QFrame:
        """Create a frame for comparison display."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setObjectName("preview_frame")
        
        frame_layout = QVBoxLayout(frame)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("frame_title")
        frame_layout.addWidget(title_label)
        
        # Scale image to display size for comparison
        scaled = image.resize((display_size, display_size), Image.Resampling.NEAREST)
        display_image = composite_on_checkerboard(scaled)
        
        pixmap = pil_to_qpixmap(display_image)
        
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(image_label)
        
        return frame
    
    def _apply_theme(self, is_dark: bool = True) -> None:
        """Apply theme styling to dialog."""
        colors = get_theme_colors(is_dark=is_dark)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['dialog_bg']};
            }}
            QFrame[objectName="preview_frame"] {{
                background-color: {colors['tab_bg']};
                border: 1px solid {colors['border_hover']};
                border-radius: 4px;
                padding: 5px;
            }}
            QLabel[objectName="frame_title"] {{
                color: {colors['text_primary']};
                font-weight: bold;
            }}
            QLabel[objectName="arrow_label"] {{
                font-size: 24px;
                color: {colors['text_muted']};
            }}
            QLabel[objectName="info_label"] {{
                color: {colors['text_muted']};
                padding: 10px;
            }}
        """)
    
    def apply_theme_from_manager(self, theme_name: str) -> None:
        """Apply theme from theme manager."""
        self._apply_theme(is_dark=theme_name != 'light')


# ==================== Color Palette Widget ====================

class ColorPaletteWidget(QFrame):
    """
    Widget displaying the dominant colors from an image.
    
    Shows color swatches with hex values that can be clicked to copy.
    
    Signals:
        color_clicked: Emitted with hex color string when swatch is clicked
    """
    
    color_clicked = pyqtSignal(str)
    
    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the color palette widget."""
        super().__init__(parent)
        
        self.colors: list[tuple[tuple[int, int, int], int]] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setObjectName("palette_widget")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        
        # Title
        title = QLabel("Dominant Colors")
        title.setObjectName("widget_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)
        
        # Swatches container
        self.swatches_layout = QHBoxLayout()
        self.swatches_layout.setSpacing(3)
        self.layout.addLayout(self.swatches_layout)
        
        # Info label
        self.info_label = QLabel("Load an image to see colors")
        self.info_label.setObjectName("widget_info")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.info_label)
        
        # Apply default theme
        self.apply_theme(is_dark=True)
    
    def apply_theme(self, is_dark: bool = True) -> None:
        """Apply theme styling to widget."""
        colors = get_theme_colors(is_dark=is_dark)
        self.setStyleSheet(f"""
            QFrame[objectName="palette_widget"] {{
                background-color: {colors['tab_bg']};
                border: 1px solid {colors['border_hover']};
                border-radius: 4px;
                padding: 5px;
            }}
            QLabel[objectName="widget_title"] {{
                color: {colors['text_primary']};
                font-weight: bold;
                font-size: 11px;
            }}
            QLabel[objectName="widget_info"] {{
                color: {colors['text_muted']};
                font-size: 10px;
            }}
        """)
    
    def set_image(self, image: Image.Image | None) -> None:
        """
        Set the image to extract colors from.
        
        Args:
            image: PIL Image or None to clear
        """
        # Clear existing swatches
        while self.swatches_layout.count():
            item = self.swatches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if image is None:
            self.colors = []
            self.info_label.setText("Load an image to see colors")
            return
        
        # Extract colors
        self.colors = extract_dominant_colors(image)
        
        if not self.colors:
            self.info_label.setText("No colors found")
            return
        
        # Create swatches
        for color, count in self.colors:
            swatch = self._create_swatch(color, count)
            self.swatches_layout.addWidget(swatch)
        
        # Add stretch to keep swatches together
        self.swatches_layout.addStretch()
        
        # Update info
        total_pixels = sum(c[1] for c in self.colors)
        self.info_label.setText(f"Click to copy hex • {total_pixels} pixels analyzed")
    
    def _create_swatch(self, color: tuple[int, int, int], count: int) -> QFrame:
        """Create a color swatch widget."""
        swatch = QFrame()
        swatch.setFixedSize(COLOR_SWATCH_SIZE, COLOR_SWATCH_SIZE)
        hex_color = color_to_hex(color)
        
        # Calculate contrast text color
        brightness = (color[0] * 299 + color[1] * 587 + color[2] * 114) / 1000
        text_color = CONTRAST_ON_LIGHT if brightness > 128 else CONTRAST_ON_DARK
        
        swatch.setStyleSheet(f"""
            QFrame {{
                background-color: {hex_color};
                border: 1px solid {DARK_THEME_COLORS['text_disabled']};
                border-radius: 3px;
            }}
            QFrame:hover {{
                border: 2px solid {BRAND_GOLD};
            }}
        """)
        
        swatch.setToolTip(f"{hex_color}\nClick to copy")
        swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Store color data
        swatch.setProperty("hex_color", hex_color)
        
        # Make clickable
        swatch.mousePressEvent = lambda e: self._on_swatch_clicked(hex_color)
        
        return swatch
    
    def _on_swatch_clicked(self, hex_color: str) -> None:
        """Handle swatch click - copy to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(hex_color)
        self.color_clicked.emit(hex_color)
        
        # Show brief feedback
        self.info_label.setText(f"Copied: {hex_color}")
        QTimer.singleShot(1500, lambda: self.info_label.setText("Click to copy hex"))
        
        logger.debug(f"Copied color to clipboard: {hex_color}")


# ==================== Zoom Controls Widget ====================

class ZoomControlsWidget(QFrame):
    """
    Widget with zoom slider and controls.
    
    Signals:
        zoom_changed: Emitted with zoom percentage (50-400)
    """
    
    zoom_changed = pyqtSignal(int)
    
    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the zoom controls widget."""
        super().__init__(parent)
        
        self.current_zoom = ZOOM_DEFAULT
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # Zoom out button
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(24, 24)
        self.zoom_out_btn.setToolTip("Zoom out")
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        layout.addWidget(self.zoom_out_btn)
        
        # Zoom slider
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(ZOOM_MIN)
        self.zoom_slider.setMaximum(ZOOM_MAX)
        self.zoom_slider.setValue(ZOOM_DEFAULT)
        self.zoom_slider.setTickInterval(ZOOM_STEP)
        self.zoom_slider.setSingleStep(ZOOM_STEP)
        self.zoom_slider.setToolTip("Zoom level")
        self.zoom_slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.zoom_slider, 1)  # Stretch
        
        # Zoom in button
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(24, 24)
        self.zoom_in_btn.setToolTip("Zoom in")
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        layout.addWidget(self.zoom_in_btn)
        
        # Zoom percentage label
        self.zoom_label = QLabel(f"{ZOOM_DEFAULT}%")
        self.zoom_label.setFixedWidth(45)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.zoom_label)
        
        # Fit to view button
        self.fit_btn = QPushButton("Fit")
        self.fit_btn.setFixedSize(32, 24)
        self.fit_btn.setToolTip("Fit to view")
        self.fit_btn.clicked.connect(self._fit_to_view)
        layout.addWidget(self.fit_btn)
        
        # 100% button
        self.actual_btn = QPushButton("1:1")
        self.actual_btn.setFixedSize(32, 24)
        self.actual_btn.setToolTip("Actual size (100%)")
        self.actual_btn.clicked.connect(self._actual_size)
        layout.addWidget(self.actual_btn)
        
        self.apply_theme(is_dark=True)
    
    def apply_theme(self, is_dark: bool = True) -> None:
        """Apply theme styling to zoom controls."""
        colors = get_theme_colors(is_dark=is_dark)
        accent = BRAND_GOLD if is_dark else BRAND_GOLD_DARK
        accent_hover = BRAND_GOLD_DARK if is_dark else BRAND_GOLD
        
        button_style = f"""
            QPushButton {{
                background-color: {colors['button_bg']};
                color: {colors['button_text']};
                border: 1px solid {colors['button_border']};
                border-radius: 3px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover_bg']};
                color: {colors['button_hover_text']};
                border-color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {accent};
                color: {colors['button_pressed_text']};
            }}
        """
        for btn in [self.zoom_out_btn, self.zoom_in_btn, self.fit_btn, self.actual_btn]:
            btn.setStyleSheet(button_style)
        
        self.zoom_label.setStyleSheet(f"color: {colors['text_primary']}; font-weight: bold;")
        
        self.zoom_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {colors['button_border']};
                height: 6px;
                background: {colors['button_bg']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: 1px solid {accent_hover};
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {accent_hover};
            }}
        """)
    
    def _on_slider_changed(self, value: int) -> None:
        """Handle slider value change."""
        # Snap to nearest step
        snapped = round(value / ZOOM_STEP) * ZOOM_STEP
        if snapped != value:
            self.zoom_slider.blockSignals(True)
            self.zoom_slider.setValue(snapped)
            self.zoom_slider.blockSignals(False)
            value = snapped
        
        self.current_zoom = value
        self.zoom_label.setText(f"{value}%")
        self.zoom_changed.emit(value)
    
    def _zoom_in(self) -> None:
        """Zoom in by one step."""
        new_value = min(self.current_zoom + ZOOM_STEP, ZOOM_MAX)
        self.zoom_slider.setValue(new_value)
    
    def _zoom_out(self) -> None:
        """Zoom out by one step."""
        new_value = max(self.current_zoom - ZOOM_STEP, ZOOM_MIN)
        self.zoom_slider.setValue(new_value)
    
    def _fit_to_view(self) -> None:
        """Reset to fit view (typically 100% or calculated)."""
        self.zoom_slider.setValue(ZOOM_DEFAULT)
    
    def _actual_size(self) -> None:
        """Set to 100% zoom."""
        self.zoom_slider.setValue(100)
    
    def set_zoom(self, value: int) -> None:
        """
        Set zoom value programmatically.
        
        Args:
            value: Zoom percentage (50-400)
        """
        value = max(ZOOM_MIN, min(ZOOM_MAX, value))
        self.zoom_slider.setValue(value)
    
    def get_zoom(self) -> int:
        """Get current zoom value."""
        return self.current_zoom


# ==================== Background Selector Widget ====================

class BackgroundSelectorWidget(QFrame):
    """
    Widget for selecting preview background type.
    
    Signals:
        background_changed: Emitted with (background_type, custom_color)
    """
    
    background_changed = pyqtSignal(str, object)  # type, color or None
    
    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the background selector widget."""
        super().__init__(parent)
        
        self.current_bg = DEFAULT_PREVIEW_BACKGROUND
        self.custom_color: tuple[int, int, int] = (128, 128, 128)  # Gray default
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # Label
        self.bg_label = QLabel("Background:")
        self.bg_label.setObjectName("bg_label")
        layout.addWidget(self.bg_label)
        
        # Dropdown
        self.bg_combo = QComboBox()
        self.bg_combo.setToolTip("Choose how transparency is displayed behind previews")
        self.bg_combo.addItem("Checkerboard", PREVIEW_BG_CHECKERBOARD)
        self.bg_combo.addItem("White", PREVIEW_BG_WHITE)
        self.bg_combo.addItem("Black", PREVIEW_BG_BLACK)
        self.bg_combo.addItem("Custom...", PREVIEW_BG_CUSTOM)
        self.bg_combo.setCurrentIndex(0)
        self.bg_combo.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(self.bg_combo)
        
        # Custom color button (hidden initially)
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(24, 24)
        self.color_btn.setToolTip("Choose custom color")
        self.color_btn.clicked.connect(self._choose_color)
        self.color_btn.setVisible(False)
        self._update_color_button()
        layout.addWidget(self.color_btn)
        
        layout.addStretch()
        
        self.apply_theme(is_dark=True)
    
    def apply_theme(self, is_dark: bool = True) -> None:
        """Apply theme styling to background selector."""
        colors = get_theme_colors(is_dark=is_dark)
        accent = BRAND_GOLD if is_dark else BRAND_GOLD_DARK
        accent_dark = BRAND_GOLD_DARK if is_dark else BRAND_GOLD
        
        self.bg_label.setStyleSheet(f"color: {colors['text_primary']};")
        
        self.bg_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors['button_bg']};
                color: {colors['button_text']};
                border: 1px solid {colors['button_border']};
                border-radius: 3px;
                padding: 3px 8px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                border-color: {accent};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {colors['text_primary']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['button_bg']};
                color: {colors['button_text']};
                selection-background-color: {accent_dark};
                selection-color: {colors['text_on_accent']};
                border: 1px solid {colors['button_border']};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px 8px;
                min-height: 20px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {accent_dark};
                color: {colors['text_on_accent']};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {accent};
                color: {colors['text_on_accent']};
            }}
        """)
    
    def _update_color_button(self) -> None:
        """Update the color button appearance."""
        hex_color = color_to_hex(self.custom_color)
        self.color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                border: 2px solid {DARK_THEME_COLORS['text_disabled']};
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border-color: {BRAND_GOLD};
            }}
        """)
    
    def _on_combo_changed(self, index: int) -> None:
        """Handle combo box selection change."""
        bg_type = self.bg_combo.currentData()
        self.current_bg = bg_type
        
        # Show/hide custom color button
        self.color_btn.setVisible(bg_type == PREVIEW_BG_CUSTOM)
        
        if bg_type == PREVIEW_BG_CUSTOM:
            self.background_changed.emit(bg_type, self.custom_color)
        else:
            self.background_changed.emit(bg_type, None)
    
    def _choose_color(self) -> None:
        """Open color picker for custom background."""
        initial_color = QColor(*self.custom_color)
        color = QColorDialog.getColor(initial_color, self, "Choose Background Color")
        
        if color.isValid():
            self.custom_color = (color.red(), color.green(), color.blue())
            self._update_color_button()
            self.background_changed.emit(PREVIEW_BG_CUSTOM, self.custom_color)
    
    def get_background_settings(self) -> tuple[str, tuple[int, int, int] | None]:
        """
        Get current background settings.
        
        Returns:
            Tuple of (background_type, custom_color or None)
        """
        if self.current_bg == PREVIEW_BG_CUSTOM:
            return (self.current_bg, self.custom_color)
        return (self.current_bg, None)


# ==================== Module Exports ====================

__all__: list[str] = [
    # Checkerboard functions
    'create_checkerboard_pattern',
    'composite_on_checkerboard',
    'pil_to_qpixmap',
    # Background options
    'composite_on_color',
    'composite_with_background',
    # Color palette
    'extract_dominant_colors',
    'color_to_hex',
    'hex_to_color',
    # Widgets
    'ZoomPreviewWidget',
    'ImagePreviewDialog',
    'ComparisonDialog',
    # New widgets
    'ColorPaletteWidget',
    'ZoomControlsWidget',
    'BackgroundSelectorWidget',
]