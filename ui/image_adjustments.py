"""
RNV Icon Builder - Image Adjustments Module
Functions for quick image adjustments.

Features:
- Add padding around images
- Auto-crop transparent borders
- Center image content
- Resize to fit standard icon sizes
- Rotate images (90, 180, 270 degrees)
- Flip images (horizontal/vertical)
- Fill transparency with solid color
- Add border/outline around content
- Brightness/Contrast/Saturation adjustments
- Grayscale conversion

Note: The adjustment dialog is now integrated into the Settings dialog.
      This module contains only the adjustment functions used by ImageProcessor.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageEnhance

from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)


# ==================== Image Adjustment Functions ====================

def get_content_bounds(img: Image.Image) -> tuple[int, int, int, int] | None:
    """
    Find the bounding box of non-transparent content.
    
    Args:
        img: PIL Image with alpha channel
        
    Returns:
        Tuple (left, top, right, bottom) or None if image is fully transparent
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Get alpha channel
    alpha = img.split()[3]
    bbox = alpha.getbbox()
    
    return bbox


def auto_crop(img: Image.Image) -> Image.Image:
    """
    Remove transparent borders from image.
    
    Args:
        img: PIL Image to crop
        
    Returns:
        Cropped image with transparent borders removed
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    bbox = get_content_bounds(img)
    
    if bbox is None:
        # Fully transparent image, return as-is
        logger.warning("Image is fully transparent, cannot crop")
        return img
    
    cropped = img.crop(bbox)
    logger.success(f"Cropped from {img.size} to {cropped.size}")
    return cropped


def add_padding(img: Image.Image, padding: int, color: tuple = (0, 0, 0, 0)) -> Image.Image:
    """
    Add padding around image.
    
    Args:
        img: PIL Image
        padding: Pixels of padding to add on each side
        color: RGBA color for padding (default: transparent)
        
    Returns:
        New image with padding added
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    new_width = img.width + (padding * 2)
    new_height = img.height + (padding * 2)
    
    # Create new image with padding
    new_img = Image.new('RGBA', (new_width, new_height), color)
    new_img.paste(img, (padding, padding))
    
    logger.success(f"Added {padding}px padding: {img.size} -> {new_img.size}")
    return new_img


def center_content(img: Image.Image, target_size: int | None = None) -> Image.Image:
    """
    Center the non-transparent content within the canvas.
    
    Args:
        img: PIL Image
        target_size: Target canvas size (if None, uses current size)
        
    Returns:
        New image with content centered
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Get content bounds
    bbox = get_content_bounds(img)
    
    if bbox is None:
        logger.warning("Image is fully transparent, cannot center")
        return img
    
    # Crop to content
    content = img.crop(bbox)
    content_w, content_h = content.size
    
    # Determine target size
    if target_size is None:
        target_size = max(img.width, img.height)
    
    # Check if content fits
    if content_w > target_size or content_h > target_size:
        # Scale down to fit
        scale = min(target_size / content_w, target_size / content_h)
        new_w = int(content_w * scale)
        new_h = int(content_h * scale)
        content = content.resize((new_w, new_h), Image.Resampling.LANCZOS)
        content_w, content_h = content.size
    
    # Create new canvas and paste centered
    new_img = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
    paste_x = (target_size - content_w) // 2
    paste_y = (target_size - content_h) // 2
    new_img.paste(content, (paste_x, paste_y))
    
    logger.success(f"Centered content in {target_size}x{target_size} canvas")
    return new_img


def resize_to_fit(img: Image.Image, target_size: int, maintain_aspect: bool = True) -> Image.Image:
    """
    Resize image to fit within target size.
    
    Args:
        img: PIL Image
        target_size: Target width and height
        maintain_aspect: If True, maintain aspect ratio and center
        
    Returns:
        Resized image
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    if maintain_aspect:
        # Calculate scale to fit
        scale = min(target_size / img.width, target_size / img.height)
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        
        # Resize content
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Center in target canvas
        new_img = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
        paste_x = (target_size - new_w) // 2
        paste_y = (target_size - new_h) // 2
        new_img.paste(resized, (paste_x, paste_y))
        
        logger.success(f"Resized to fit {target_size}x{target_size} (aspect preserved)")
        return new_img
    else:
        # Stretch to fill
        resized = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
        logger.success(f"Resized to {target_size}x{target_size} (stretched)")
        return resized


def make_square(img: Image.Image, fill_color: tuple = (0, 0, 0, 0)) -> Image.Image:
    """
    Make image square by adding padding to shorter dimension.
    
    Args:
        img: PIL Image
        fill_color: RGBA color for padding
        
    Returns:
        Square image
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    if img.width == img.height:
        return img
    
    # Determine new size (largest dimension)
    new_size = max(img.width, img.height)
    
    # Create square canvas
    new_img = Image.new('RGBA', (new_size, new_size), fill_color)
    
    # Center original image
    paste_x = (new_size - img.width) // 2
    paste_y = (new_size - img.height) // 2
    new_img.paste(img, (paste_x, paste_y))
    
    logger.success(f"Made square: {img.size} -> {new_img.size}")
    return new_img


# ==================== Transform Functions  ====================

def rotate_image(img: Image.Image, degrees: int) -> Image.Image:
    """
    Rotate image by specified degrees.
    
    Args:
        img: PIL Image
        degrees: Rotation angle (90, 180, 270, or -90 for CCW)
        
    Returns:
        Rotated image
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Normalize degrees to positive values
    degrees = degrees % 360
    
    if degrees == 0:
        return img
    
    # Use PIL's rotate with expand=True to handle non-square images
    # For 90/270 rotations, dimensions swap
    rotated = img.rotate(-degrees, expand=True, resample=Image.Resampling.BICUBIC)
    
    logger.success(f"Rotated image {degrees} degrees clockwise")
    return rotated


def flip_horizontal(img: Image.Image) -> Image.Image:
    """
    Flip image horizontally (mirror).
    
    Args:
        img: PIL Image
        
    Returns:
        Horizontally flipped image
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    flipped = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    logger.success("Flipped image horizontally")
    return flipped


def flip_vertical(img: Image.Image) -> Image.Image:
    """
    Flip image vertically.
    
    Args:
        img: PIL Image
        
    Returns:
        Vertically flipped image
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    flipped = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    logger.success("Flipped image vertically")
    return flipped


# ==================== Color Functions  ====================

def fill_transparency(img: Image.Image, color: tuple) -> Image.Image:
    """
    Replace transparent areas with a solid color.
    
    Args:
        img: PIL Image with alpha channel
        color: RGBA or RGB color tuple to fill with
        
    Returns:
        Image with transparency replaced by solid color
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Ensure color is RGBA
    if len(color) == 3:
        color = (*color, 255)
    
    # Create solid background
    background = Image.new('RGBA', img.size, color)
    
    # Composite the original image onto the background
    result = Image.alpha_composite(background, img)
    
    logger.success(f"Filled transparency with color {color[:3]}")
    return result


def add_border(img: Image.Image, width: int, color: tuple) -> Image.Image:
    """
    Add a colored border around the image content.
    
    The border is added around the non-transparent content, not the entire canvas.
    
    Args:
        img: PIL Image
        width: Border width in pixels
        color: RGBA or RGB color tuple for border
        
    Returns:
        Image with border added (canvas size increases by 2*width)
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    if width <= 0:
        return img
    
    # Ensure color is RGBA
    if len(color) == 3:
        color = (*color, 255)
    
    # Get content bounds
    bbox = get_content_bounds(img)
    
    if bbox is None:
        logger.warning("Image is fully transparent, cannot add border")
        return img
    
    # Crop to content
    content = img.crop(bbox)
    content_w, content_h = content.size
    
    # New canvas size (content + border on all sides)
    new_w = content_w + (width * 2)
    new_h = content_h + (width * 2)
    
    # Create new canvas with transparent background
    result = Image.new('RGBA', (new_w, new_h), (0, 0, 0, 0))
    
    # Draw border rectangle
    draw = ImageDraw.Draw(result)
    # Outer rectangle (full border area)
    draw.rectangle([0, 0, new_w - 1, new_h - 1], fill=color)
    
    # Paste content on top (centered, leaving border visible)
    result.paste(content, (width, width), content)
    
    logger.success(f"Added {width}px border with color {color[:3]}")
    return result


# ==================== Color Adjustment Functions  ====================

def adjust_brightness(img: Image.Image, value: int) -> Image.Image:
    """
    Adjust image brightness.
    
    Args:
        img: PIL Image
        value: Brightness adjustment (-100 to +100)
               0 = no change, negative = darker, positive = brighter
        
    Returns:
        Brightness-adjusted image
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    if value == 0:
        return img
    
    # Convert value from -100..+100 to enhancement factor
    # -100 -> 0.0 (black), 0 -> 1.0 (no change), +100 -> 2.0 (double bright)
    factor = 1.0 + (value / 100.0)
    factor = max(0.0, min(2.0, factor))  # Clamp to 0..2
    
    # Separate alpha channel to preserve it
    r, g, b, a = img.split()
    rgb_img = Image.merge('RGB', (r, g, b))
    
    # Apply brightness enhancement
    enhancer = ImageEnhance.Brightness(rgb_img)
    enhanced = enhancer.enhance(factor)
    
    # Recombine with alpha
    r2, g2, b2 = enhanced.split()
    result = Image.merge('RGBA', (r2, g2, b2, a))
    
    logger.success(f"Adjusted brightness by {value:+d}")
    return result


def adjust_contrast(img: Image.Image, value: int) -> Image.Image:
    """
    Adjust image contrast.
    
    Args:
        img: PIL Image
        value: Contrast adjustment (-100 to +100)
               0 = no change, negative = less contrast, positive = more contrast
        
    Returns:
        Contrast-adjusted image
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    if value == 0:
        return img
    
    # Convert value from -100..+100 to enhancement factor
    # -100 -> 0.0 (gray), 0 -> 1.0 (no change), +100 -> 2.0 (high contrast)
    factor = 1.0 + (value / 100.0)
    factor = max(0.0, min(2.0, factor))  # Clamp to 0..2
    
    # Separate alpha channel to preserve it
    r, g, b, a = img.split()
    rgb_img = Image.merge('RGB', (r, g, b))
    
    # Apply contrast enhancement
    enhancer = ImageEnhance.Contrast(rgb_img)
    enhanced = enhancer.enhance(factor)
    
    # Recombine with alpha
    r2, g2, b2 = enhanced.split()
    result = Image.merge('RGBA', (r2, g2, b2, a))
    
    logger.success(f"Adjusted contrast by {value:+d}")
    return result


def adjust_saturation(img: Image.Image, value: int) -> Image.Image:
    """
    Adjust image color saturation.
    
    Args:
        img: PIL Image
        value: Saturation adjustment (-100 to +100)
               -100 = grayscale, 0 = no change, +100 = highly saturated
        
    Returns:
        Saturation-adjusted image
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    if value == 0:
        return img
    
    # Convert value from -100..+100 to enhancement factor
    # -100 -> 0.0 (grayscale), 0 -> 1.0 (no change), +100 -> 2.0 (vivid)
    factor = 1.0 + (value / 100.0)
    factor = max(0.0, min(2.0, factor))  # Clamp to 0..2
    
    # Separate alpha channel to preserve it
    r, g, b, a = img.split()
    rgb_img = Image.merge('RGB', (r, g, b))
    
    # Apply color (saturation) enhancement
    enhancer = ImageEnhance.Color(rgb_img)
    enhanced = enhancer.enhance(factor)
    
    # Recombine with alpha
    r2, g2, b2 = enhanced.split()
    result = Image.merge('RGBA', (r2, g2, b2, a))
    
    logger.success(f"Adjusted saturation by {value:+d}")
    return result


def convert_grayscale(img: Image.Image) -> Image.Image:
    """
    Convert image to grayscale while preserving alpha channel.
    
    Args:
        img: PIL Image
        
    Returns:
        Grayscale image with original alpha channel preserved
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Separate alpha channel
    r, g, b, a = img.split()
    rgb_img = Image.merge('RGB', (r, g, b))
    
    # Convert to grayscale
    gray = rgb_img.convert('L')
    
    # Convert back to RGB (grayscale values in all channels)
    gray_rgb = gray.convert('RGB')
    
    # Recombine with original alpha
    r2, g2, b2 = gray_rgb.split()
    result = Image.merge('RGBA', (r2, g2, b2, a))
    
    logger.success("Converted to grayscale")
    return result


# ==================== Combined Adjustment  ====================

def _value_to_factor(value: int) -> float:
    """
    Convert a -100..+100 adjustment value to a 0.0..2.0 enhancement factor.
    
    Args:
        value: Adjustment value (-100 to +100)
        
    Returns:
        Enhancement factor (0.0 to 2.0), where 1.0 = no change
    """
    factor = 1.0 + (value / 100.0)
    return max(0.0, min(2.0, factor))


def apply_combined_adjustments(
    img: Image.Image,
    brightness: int = 0,
    contrast: int = 0,
    saturation: int = 0
) -> Image.Image:
    """
    Apply brightness, contrast, and saturation adjustments in a single pass.
    
    Optimized version that splits the alpha channel once, applies all
    three enhancers sequentially on the same RGB intermediate, then
    recombines with alpha once. This avoids creating multiple intermediate
    RGBA images and redundant split/merge cycles.
    
    When all three adjustments are applied individually, each function:
    1. Converts to RGBA
    2. Splits into r, g, b, a
    3. Creates RGB image
    4. Applies enhancer
    5. Splits result back
    6. Merges to RGBA
    
    This combined version performs steps 1-3 once, applies all enhancers
    in sequence, then performs steps 5-6 once - reducing intermediate
    image allocations from 6 to 2.
    
    Args:
        img: PIL Image (any mode, will be converted to RGBA)
        brightness: Brightness adjustment (-100 to +100), 0 = no change
        contrast: Contrast adjustment (-100 to +100), 0 = no change
        saturation: Saturation adjustment (-100 to +100), 0 = no change
        
    Returns:
        Adjusted image with original alpha channel preserved
        
    Example:
        >>> adjusted = apply_combined_adjustments(img, brightness=20, contrast=-10, saturation=30)
    """
    # Skip if no adjustments needed
    if brightness == 0 and contrast == 0 and saturation == 0:
        return img
    
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Single split: separate alpha channel once
    r, g, b, a = img.split()
    rgb_img = Image.merge('RGB', (r, g, b))
    
    # Apply each non-zero adjustment in sequence on same RGB intermediate
    if brightness != 0:
        factor = _value_to_factor(brightness)
        rgb_img = ImageEnhance.Brightness(rgb_img).enhance(factor)
    
    if contrast != 0:
        factor = _value_to_factor(contrast)
        rgb_img = ImageEnhance.Contrast(rgb_img).enhance(factor)
    
    if saturation != 0:
        factor = _value_to_factor(saturation)
        rgb_img = ImageEnhance.Color(rgb_img).enhance(factor)
    
    # Single merge: recombine with original alpha once
    r2, g2, b2 = rgb_img.split()
    result = Image.merge('RGBA', (r2, g2, b2, a))
    
    # Build log message showing only non-zero adjustments
    parts = []
    if brightness != 0:
        parts.append(f"B:{brightness:+d}")
    if contrast != 0:
        parts.append(f"C:{contrast:+d}")
    if saturation != 0:
        parts.append(f"S:{saturation:+d}")
    logger.success(f"Applied combined adjustments ({', '.join(parts)})")
    
    return result


# ==================== Module Exports ====================

__all__: list[str] = [
    'get_content_bounds',
    'auto_crop',
    'add_padding',
    'center_content',
    'resize_to_fit',
    'make_square',
    # Transform
    'rotate_image',
    'flip_horizontal',
    'flip_vertical',
    # Color
    'fill_transparency',
    'add_border',
    # Color Adjustments
    'adjust_brightness',
    'adjust_contrast',
    'adjust_saturation',
    'convert_grayscale',
    # Combined Optimization
    'apply_combined_adjustments',
]