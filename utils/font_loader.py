"""
RNV Icon Builder - Font Loader Module
Handles loading custom fonts with fallback support.

Features:
- Load fonts from embedded base64 data
- Load fonts from external files
- Fallback to system fonts
- Bold and regular font variants
"""

from __future__ import annotations

from PyQt6.QtCore import QByteArray
from PyQt6.QtGui import QFont, QFontDatabase

from utils.config import FONT_PATH
from utils.logger import Logger, get_logger_instance

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)

# Cache for loaded font family name (avoids repeated addApplicationFont calls)
_cached_font_family: str | None = None


# ==================== Embedded Font (Base64) ====================
# Replace this with actual base64 encoded font data if needed
MONT_FONT: str = """
<BASE64 FONT STRING HERE>
"""


# ==================== Font Loading ====================

def load_embedded_font() -> QFont:
    """
    Load Montserrat font from embedded base64 or file, with fallback to system font.
    
    Uses a module-level cache to avoid repeated font registration with Qt.
    After the first successful load, subsequent calls return a new QFont
    from the cached family name without re-registering.
    
    Priority:
        1. Cached font family (if previously loaded)
        2. Embedded base64 font (if available)
        3. External font file (resources/fonts/Montserrat-Black.ttf)
        4. System fallback (Arial)
    
    Returns:
        QFont object ready to use
        
    Example:
        >>> font = load_embedded_font()
        >>> app.setFont(font)
    """
    global _cached_font_family
    
    # Return cached font if already loaded
    if _cached_font_family is not None:
        logger.debug(f"Using cached font family: {_cached_font_family}")
        return QFont(_cached_font_family, 10)
    
    # Try embedded font first
    if MONT_FONT.strip() and "<BASE64 FONT STRING" not in MONT_FONT:
        logger.debug("Attempting to load embedded base64 font")
        try:
            font_id: int = QFontDatabase.addApplicationFontFromData(
                QByteArray.fromBase64(MONT_FONT.encode("utf-8"))
            )
            if font_id != -1:
                families: list[str] = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    _cached_font_family = families[0]
                    logger.success("Loaded Montserrat-Black  (embedded)")
                    return QFont(families[0], 10)
            else:
                logger.warning("Failed to load embedded font (invalid font_id)")
        except Exception as e:
            logger.warning(f"Failed to load embedded font: {e}")
    else:
        logger.debug("No embedded font available (placeholder detected)")
    
    # Try file-based font
    if FONT_PATH.exists():
        logger.debug(f"Attempting to load font from file: {FONT_PATH}")
        try:
            font_id = QFontDatabase.addApplicationFont(str(FONT_PATH))
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    _cached_font_family = families[0]
                    logger.success("Loaded Montserrat-Black  (file)")
                    return QFont(families[0], 10)
                else:
                    logger.warning("Font file loaded but no families found")
            else:
                logger.warning("Failed to load font file (invalid font_id)")
        except Exception as e:
            logger.warning(f"Failed to load font file: {e}")
    else:
        logger.warning(f"Font file not found: {FONT_PATH}")
    
    # Fallback to system font (also cache so we don't retry every time)
    _cached_font_family = "Arial"
    logger.warning("Using fallback font (Arial)")
    return QFont("Arial", 10)


def get_bold_font(size: int = 10) -> QFont:
    """
    Get a bold version of the application font.
    
    Args:
        size: Font size in points
        
    Returns:
        Bold QFont object
        
    Example:
        >>> title_font = get_bold_font(14)
        >>> label.setFont(title_font)
    """
    logger.debug(f"Creating bold font with size {size}")
    font: QFont = load_embedded_font()
    font.setPointSize(size)
    font.setBold(True)
    return font


def get_regular_font(size: int = 10) -> QFont:
    """
    Get regular version of the application font.
    
    Args:
        size: Font size in points
        
    Returns:
        Regular QFont object
        
    Example:
        >>> body_font = get_regular_font(11)
        >>> text_edit.setFont(body_font)
    """
    logger.debug(f"Creating regular font with size {size}")
    font: QFont = load_embedded_font()
    font.setPointSize(size)
    return font


def get_monospace_font(size: int = 10) -> QFont:
    """
    Get a monospace font for code or fixed-width content.
    
    Args:
        size: Font size in points
        
    Returns:
        Monospace QFont object
        
    Example:
        >>> code_font = get_monospace_font(9)
        >>> code_editor.setFont(code_font)
    """
    logger.debug(f"Creating monospace font with size {size}")
    # Try common monospace fonts in order of preference
    monospace_families: list[str] = [
        "Consolas",
        "Monaco", 
        "Courier New",
        "DejaVu Sans Mono",
        "monospace"
    ]
    
    for family in monospace_families:
        font = QFont(family, size)
        if font.exactMatch() or family == "monospace":
            font.setStyleHint(QFont.StyleHint.Monospace)
            return font
    
    # Fallback
    font = QFont("Courier", size)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font


# ==================== Module Exports ====================

__all__: list[str] = [
    'load_embedded_font',
    'get_bold_font',
    'get_regular_font',
    'get_monospace_font',
]