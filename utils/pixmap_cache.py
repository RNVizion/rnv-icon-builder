"""
RNV Icon Builder - QPixmap Cache
LRU cache for faster image/pixmap operations.

Features:
- LRU (Least Recently Used) eviction policy
- Configurable cache size
- Statistics tracking for performance monitoring
- Specialized ImagePixmapCache for preview operations

Usage Examples:
    # In a class that handles images:
    self.pixmap_cache = QPixmapCache(max_size=15)
    
    # Get cached pixmap or create new:
    pixmap = self.pixmap_cache.get_or_create(
        cache_key=(self.image_path, zoom_level),
        creator=lambda: self._create_pixmap(zoom_level)
    )
    
    # Clear cache when loading new image:
    self.pixmap_cache.clear()
    
    # View statistics:
    self.pixmap_cache.print_stats()
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Callable, Any

from PyQt6.QtGui import QPixmap

# Import logger
from utils.logger import Logger, get_logger_instance
logger: Logger = get_logger_instance(__name__)


class QPixmapCache:
    """
    LRU (Least Recently Used) cache for QPixmap objects.
    
    Benefits:
    - Faster zoom/preview operations (reuses cached pixmaps)
    - Reduced memory allocation
    - Better performance on repeated operations
    - Automatic size limiting with LRU eviction
    
    The cache uses an OrderedDict to maintain insertion order
    and implements LRU eviction when size limit is reached.
    
    Example:
        cache = QPixmapCache(max_size=15)
        
        # Get or create pixmap
        pixmap = cache.get_or_create(
            cache_key=("image.png", 1.5, (256, 256)),
            creator=lambda: create_scaled_pixmap(1.5)
        )
        
        # Check stats
        cache.print_stats()
    """
    
    def __init__(self, max_size: int = 15):
        """
        Initialize pixmap cache.
        
        Args:
            max_size: Maximum number of pixmaps to cache.
                     Typical values: 10-20 depending on memory.
                     Each cached pixmap can be 1-10MB depending on size.
                     Default: 15 for good balance of memory and performance.
        """
        self._cache: OrderedDict[tuple, QPixmap] = OrderedDict()
        self._max_size = max_size
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: tuple) -> QPixmap | None:
        """
        Get pixmap from cache.
        
        Args:
            key: Cache key (typically tuple of identifying info)
                 Example: (image_path, zoom_level, width, height)
        
        Returns:
            Cached QPixmap if found, None otherwise
        
        Example:
            cache_key = (self.image_path, 1.5, 800, 600)
            pixmap = cache.get(cache_key)
        """
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        
        self._misses += 1
        return None
    
    def put(self, key: tuple, pixmap: QPixmap) -> None:
        """
        Add pixmap to cache.
        
        Args:
            key: Cache key
            pixmap: QPixmap to cache
        
        Example:
            cache_key = (self.image_path, 2.0, 1600, 1200)
            cache.put(cache_key, pixmap)
        """
        # Remove if already exists (will re-add at end)
        if key in self._cache:
            del self._cache[key]
        
        # Add to cache
        self._cache[key] = pixmap
        self._cache.move_to_end(key)
        
        # Enforce size limit (LRU eviction)
        while len(self._cache) > self._max_size:
            # Remove oldest (first item)
            evicted_key = next(iter(self._cache))
            del self._cache[evicted_key]
            self._evictions += 1
    
    def get_or_create(
        self, 
        cache_key: tuple, 
        creator: Callable[[], QPixmap]
    ) -> QPixmap:
        """
        Get from cache or create if not found (recommended method).
        
        This is the most convenient method for typical usage.
        It handles cache lookup and creation in one call.
        
        Args:
            cache_key: Cache key (tuple)
            creator: Function to create pixmap if not in cache
        
        Returns:
            Cached or newly created QPixmap
        
        Example:
            pixmap = cache.get_or_create(
                cache_key=(path, zoom, size),
                creator=lambda: self._create_pixmap(zoom)
            )
        """
        # Try to get from cache
        pixmap = self.get(cache_key)
        
        if pixmap is not None:
            return pixmap
        
        # Create new pixmap
        pixmap = creator()
        
        # Cache it (if valid)
        if pixmap is not None and not pixmap.isNull():
            self.put(cache_key, pixmap)
        
        return pixmap
    
    def clear(self) -> int:
        """
        Clear all cached pixmaps.
        
        Returns:
            Number of pixmaps cleared
        
        Example:
            # When loading new image:
            cleared = self.pixmap_cache.clear()
            logger.debug(f"Cleared {cleared} cached pixmaps")
        """
        count = len(self._cache)
        self._cache.clear()
        return count
    
    def remove(self, key: tuple) -> bool:
        """
        Remove specific pixmap from cache.
        
        Args:
            key: Cache key to remove
        
        Returns:
            True if removed, False if not in cache
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def resize(self, new_max_size: int) -> None:
        """
        Change cache size limit.
        
        Args:
            new_max_size: New maximum number of cached pixmaps
        
        If new size is smaller, oldest entries are evicted.
        """
        self._max_size = new_max_size
        
        # Evict oldest entries if needed
        while len(self._cache) > self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._evictions += 1
    
    def get_size(self) -> int:
        """Get current number of cached pixmaps."""
        return len(self._cache)
    
    def get_max_size(self) -> int:
        """Get maximum cache size."""
        return self._max_size
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with:
            - size: Current number of cached pixmaps
            - max_size: Maximum cache size
            - hits: Number of cache hits
            - misses: Number of cache misses
            - hit_rate: Cache hit rate (0-100%)
            - evictions: Number of evicted entries
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        
        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate,
            'evictions': self._evictions
        }
    
    def print_stats(self) -> None:
        """Print cache statistics to console (via logger)."""
        stats = self.get_stats()
        
        logger.debug("=" * 50)
        logger.debug("QPixmap Cache Statistics:")
        logger.debug("=" * 50)
        logger.debug(f"  Cache Size:     {stats['size']}/{stats['max_size']}")
        logger.debug(f"  Cache Hits:     {stats['hits']}")
        logger.debug(f"  Cache Misses:   {stats['misses']}")
        logger.debug(f"  Hit Rate:       {stats['hit_rate']:.1f}%")
        logger.debug(f"  Evictions:      {stats['evictions']}")
        logger.debug("=" * 50)
    
    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get_keys(self) -> list[tuple]:
        """
        Get list of all cache keys (for debugging).
        
        Returns:
            List of cache keys in LRU order (oldest first)
        """
        return list(self._cache.keys())
    
    def contains(self, key: tuple) -> bool:
        """Check if key is in cache without affecting LRU order."""
        return key in self._cache


class ImagePixmapCache(QPixmapCache):
    """
    Specialized QPixmap cache for image display with helper methods.
    
    Extends QPixmapCache with image-specific functionality like
    tracking current image and zoom-level caching.
    
    Example:
        cache = ImagePixmapCache(max_size=15)
        
        # Set current image (clears old cache)
        cache.set_current_image("/path/to/image.png")
        
        # Get pixmap for zoom level
        pixmap = cache.get_for_zoom(
            image_path,
            zoom_level=1.5,
            image_size=(800, 600),
            creator=lambda: create_pixmap(1.5)
        )
    """
    
    def __init__(self, max_size: int = 15):
        """
        Initialize image pixmap cache.
        
        Args:
            max_size: Maximum number of cached pixmaps (default: 15)
        """
        super().__init__(max_size)
        self.current_image_path: str | None = None
    
    def set_current_image(self, image_path: str) -> int:
        """
        Set current image and clear cache for previous image.
        
        Call this when loading a new image to invalidate
        all cached pixmaps from the previous image.
        
        Args:
            image_path: Path to current image
        
        Returns:
            Number of pixmaps cleared
        """
        if self.current_image_path != image_path:
            cleared = self.clear()
            self.current_image_path = image_path
            return cleared
        return 0
    
    def get_for_zoom(
        self, 
        image_path: str, 
        zoom_level: float,
        image_size: tuple[int, int],
        creator: Callable[[], QPixmap]
    ) -> QPixmap:
        """
        Get or create pixmap for specific zoom level.
        
        Args:
            image_path: Path to image
            zoom_level: Zoom level (e.g., 1.0, 1.5, 2.0)
            image_size: Original image size (width, height)
            creator: Function to create pixmap if not cached
        
        Returns:
            QPixmap for the zoom level
        
        Example:
            pixmap = cache.get_for_zoom(
                self.image_path,
                1.5,
                (800, 600),
                lambda: self._create_scaled_pixmap(1.5)
            )
        """
        # Create cache key
        cache_key = (image_path, zoom_level, image_size)
        
        # Get or create
        return self.get_or_create(cache_key, creator)
    
    def get_for_size(
        self,
        image_path: str,
        target_size: int,
        creator: Callable[[], QPixmap]
    ) -> QPixmap:
        """
        Get or create pixmap for specific target size (e.g., icon size).
        
        Args:
            image_path: Path to image
            target_size: Target size in pixels (e.g., 256, 128, 64)
            creator: Function to create pixmap if not cached
        
        Returns:
            QPixmap for the target size
        
        Example:
            pixmap = cache.get_for_size(
                self.image_path,
                64,
                lambda: self._create_thumbnail(64)
            )
        """
        cache_key = (image_path, "size", target_size)
        return self.get_or_create(cache_key, creator)
    
    def invalidate_image(self, image_path: str) -> int:
        """
        Remove all cached pixmaps for a specific image.
        
        Args:
            image_path: Path to image to invalidate
        
        Returns:
            Number of pixmaps removed
        """
        keys_to_remove = [
            key for key in self.get_keys() 
            if len(key) > 0 and key[0] == image_path
        ]
        
        for key in keys_to_remove:
            self.remove(key)
        
        return len(keys_to_remove)


class ThumbnailCache(QPixmapCache):
    """
    Specialized cache for preview thumbnails.
    
    Optimized for the icon builder's preview grid where
    multiple sizes need to be cached per image.
    
    Example:
        cache = ThumbnailCache(max_size=50)  # More items, smaller pixmaps
        
        thumb = cache.get_thumbnail(
            source_path="/path/to/icon.png",
            size=64,
            creator=lambda: generate_thumbnail(64)
        )
    """
    
    def __init__(self, max_size: int = 50):
        """
        Initialize thumbnail cache.
        
        Args:
            max_size: Maximum thumbnails to cache (default: 50)
                     Higher than regular cache since thumbnails are smaller.
        """
        super().__init__(max_size)
    
    def get_thumbnail(
        self,
        source_path: str,
        size: int,
        creator: Callable[[], QPixmap],
        variant: str = "default"
    ) -> QPixmap:
        """
        Get or create thumbnail for an image at specific size.
        
        Args:
            source_path: Path to source image
            size: Thumbnail size in pixels
            creator: Function to create thumbnail if not cached
            variant: Optional variant identifier (e.g., "hover", "selected")
        
        Returns:
            Thumbnail QPixmap
        
        Example:
            thumb = cache.get_thumbnail(
                "/path/to/icon.png",
                64,
                lambda: create_thumb(64),
                variant="hover"
            )
        """
        cache_key = (source_path, size, variant)
        return self.get_or_create(cache_key, creator)
    
    def invalidate_source(self, source_path: str) -> int:
        """
        Remove all cached thumbnails for a source image.
        
        Args:
            source_path: Path to source image
        
        Returns:
            Number of thumbnails removed
        """
        keys_to_remove = [
            key for key in self.get_keys()
            if len(key) > 0 and key[0] == source_path
        ]
        
        for key in keys_to_remove:
            self.remove(key)
        
        return len(keys_to_remove)


# ==================== Helper Functions ====================

def create_cache_key(
    identifier: str,
    *args,
    **kwargs
) -> tuple:
    """
    Create standardized cache key from various parameters.
    
    Args:
        identifier: Primary identifier (e.g., file path)
        *args: Additional positional identifiers
        **kwargs: Additional keyword identifiers (converted to sorted tuple)
    
    Returns:
        Tuple that can be used as cache key
    
    Example:
        key = create_cache_key(
            '/path/to/image.jpg',
            1.5,  # zoom
            (800, 600),  # size
            quality='high'
        )
    """
    key_parts = [identifier] + list(args)
    
    if kwargs:
        # Convert dict to sorted tuple for hashability
        params_tuple = tuple(sorted(kwargs.items()))
        key_parts.append(params_tuple)
    
    return tuple(key_parts)


# ==================== Module Exports ====================

__all__: list[str] = [
    'QPixmapCache',
    'ImagePixmapCache',
    'ThumbnailCache',
    'create_cache_key',
]
