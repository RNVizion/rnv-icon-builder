"""
RNV Icon Builder - Preset Manager Module
Manages custom size presets for ICO generation.

Features:
- Save/load custom size presets
- Built-in presets (All, Favicon, Windows, macOS)
- Persist presets to JSON file
- Import/export presets
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime

from utils.config import ICON_SIZES, USER_DATA_DIR
from utils.logger import Logger, get_logger_instance

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)

# Presets file location
PRESETS_FILE: Path = USER_DATA_DIR / "presets.json"


@dataclass
class SizePreset:
    """
    Represents a size preset configuration.
    
    Attributes:
        name: Preset name (unique identifier)
        sizes: List of sizes to include
        autofill: Whether to autofill missing sizes
        png_compression: Whether to use PNG compression
        description: Optional description
        is_builtin: Whether this is a built-in preset (cannot be deleted)
        created: Creation timestamp
        modified: Last modified timestamp
    """
    name: str
    sizes: list[int] = field(default_factory=list)
    autofill: bool = True
    png_compression: bool = True
    description: str = ""
    is_builtin: bool = False
    created: str = ""
    modified: str = ""
    
    def __post_init__(self):
        if not self.created:
            self.created = datetime.now().isoformat()
        if not self.modified:
            self.modified = self.created
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'sizes': self.sizes,
            'autofill': self.autofill,
            'png_compression': self.png_compression,
            'description': self.description,
            'is_builtin': self.is_builtin,
            'created': self.created,
            'modified': self.modified
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SizePreset:
        """Create preset from dictionary."""
        return cls(
            name=data.get('name', 'Unnamed'),
            sizes=data.get('sizes', ICON_SIZES.copy()),
            autofill=data.get('autofill', True),
            png_compression=data.get('png_compression', True),
            description=data.get('description', ''),
            is_builtin=data.get('is_builtin', False),
            created=data.get('created', ''),
            modified=data.get('modified', '')
        )
    
    def update_modified(self) -> None:
        """Update the modified timestamp."""
        self.modified = datetime.now().isoformat()


# Built-in presets that cannot be deleted
BUILTIN_PRESETS: list[SizePreset] = [
    SizePreset(
        name="All Sizes",
        sizes=[256, 128, 64, 48, 32, 16],
        autofill=True,
        png_compression=True,
        description="All 6 standard icon sizes",
        is_builtin=True
    ),
    SizePreset(
        name="Favicon",
        sizes=[48, 32, 16],
        autofill=True,
        png_compression=True,
        description="Web favicon sizes (16, 32, 48)",
        is_builtin=True
    ),
    SizePreset(
        name="Windows",
        sizes=[256, 48, 32, 16],
        autofill=True,
        png_compression=True,
        description="Windows application icon sizes",
        is_builtin=True
    ),
    SizePreset(
        name="macOS",
        sizes=[256, 128, 32, 16],
        autofill=True,
        png_compression=True,
        description="macOS application icon sizes",
        is_builtin=True
    ),
    SizePreset(
        name="Large Only",
        sizes=[256, 128],
        autofill=False,
        png_compression=True,
        description="Large sizes only (256, 128)",
        is_builtin=True
    ),
    SizePreset(
        name="Small Only",
        sizes=[48, 32, 16],
        autofill=False,
        png_compression=False,
        description="Small sizes only (48, 32, 16)",
        is_builtin=True
    ),
]


class PresetManager:
    """
    Manages custom size presets for ICO generation.
    
    Provides methods to save, load, and manage presets. Built-in
    presets cannot be modified or deleted.
    
    Example:
        >>> manager = PresetManager()
        >>> manager.save_preset("My Preset", [256, 64, 32])
        >>> preset = manager.get_preset("My Preset")
        >>> all_presets = manager.list_presets()
    """
    
    def __init__(self) -> None:
        """Initialize the preset manager and load presets."""
        self._presets: dict[str, SizePreset] = {}
        self._load_presets()
        logger.debug("PresetManager initialized")
    
    def _load_presets(self) -> None:
        """Load presets from disk, including built-in presets."""
        # Start with built-in presets
        for preset in BUILTIN_PRESETS:
            self._presets[preset.name] = preset
        
        # Load custom presets from file
        if PRESETS_FILE.exists():
            try:
                with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    custom_presets = data.get('presets', [])
                    
                    for preset_data in custom_presets:
                        preset = SizePreset.from_dict(preset_data)
                        # Don't override built-in presets
                        if not preset.is_builtin:
                            self._presets[preset.name] = preset
                
                custom_count = len([p for p in self._presets.values() if not p.is_builtin])
                logger.debug(f"Loaded {custom_count} custom preset(s)")
                
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid presets file: {e}")
            except Exception as e:
                logger.warning(f"Failed to load presets: {e}")
        else:
            logger.debug("No presets file found, using built-in presets only")
    
    def _save_presets(self) -> bool:
        """
        Save custom presets to disk.
        
        Returns:
            True if save successful
        """
        try:
            # Ensure directory exists
            PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Only save custom presets (not built-in)
            custom_presets = [
                p.to_dict() for p in self._presets.values() 
                if not p.is_builtin
            ]
            
            data = {
                'version': '2.11',
                'presets': custom_presets,
                'last_modified': datetime.now().isoformat()
            }
            
            with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(custom_presets)} custom preset(s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save presets: {e}")
            return False
    
    def save_preset(
        self,
        name: str,
        sizes: list[int],
        autofill: bool = True,
        png_compression: bool = True,
        description: str = ""
    ) -> bool:
        """
        Save a new preset or update existing one.
        
        Args:
            name: Preset name
            sizes: List of sizes to include
            autofill: Whether to autofill missing sizes
            png_compression: Whether to use PNG compression
            description: Optional description
            
        Returns:
            True if save successful
            
        Note:
            Cannot overwrite built-in presets.
        """
        # Check for built-in preset
        if name in self._presets and self._presets[name].is_builtin:
            logger.warning(f"Cannot overwrite built-in preset: {name}")
            return False
        
        # Validate sizes
        valid_sizes = [s for s in sizes if s in ICON_SIZES]
        if not valid_sizes:
            logger.warning("No valid sizes provided")
            return False
        
        # Sort sizes descending
        valid_sizes = sorted(valid_sizes, reverse=True)
        
        # Create or update preset
        if name in self._presets:
            preset = self._presets[name]
            preset.sizes = valid_sizes
            preset.autofill = autofill
            preset.png_compression = png_compression
            preset.description = description
            preset.update_modified()
            logger.success(f"Updated preset: {name}")
        else:
            preset = SizePreset(
                name=name,
                sizes=valid_sizes,
                autofill=autofill,
                png_compression=png_compression,
                description=description
            )
            self._presets[name] = preset
            logger.success(f"Created preset: {name}")
        
        return self._save_presets()
    
    def get_preset(self, name: str) -> SizePreset | None:
        """
        Get a preset by name.
        
        Args:
            name: Preset name
            
        Returns:
            SizePreset or None if not found
        """
        return self._presets.get(name)
    
    def delete_preset(self, name: str) -> bool:
        """
        Delete a preset.
        
        Args:
            name: Preset name to delete
            
        Returns:
            True if deleted successfully
            
        Note:
            Cannot delete built-in presets.
        """
        if name not in self._presets:
            logger.warning(f"Preset not found: {name}")
            return False
        
        if self._presets[name].is_builtin:
            logger.warning(f"Cannot delete built-in preset: {name}")
            return False
        
        del self._presets[name]
        logger.success(f"Deleted preset: {name}")
        return self._save_presets()
    
    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """
        Rename a preset.
        
        Args:
            old_name: Current preset name
            new_name: New preset name
            
        Returns:
            True if renamed successfully
        """
        if old_name not in self._presets:
            logger.warning(f"Preset not found: {old_name}")
            return False
        
        if self._presets[old_name].is_builtin:
            logger.warning(f"Cannot rename built-in preset: {old_name}")
            return False
        
        if new_name in self._presets:
            logger.warning(f"Preset already exists: {new_name}")
            return False
        
        preset = self._presets.pop(old_name)
        preset.name = new_name
        preset.update_modified()
        self._presets[new_name] = preset
        
        logger.success(f"Renamed preset: {old_name} -> {new_name}")
        return self._save_presets()
    
    def list_presets(self, include_builtin: bool = True) -> list[SizePreset]:
        """
        Get list of all presets.
        
        Args:
            include_builtin: Whether to include built-in presets
            
        Returns:
            List of SizePreset objects
        """
        if include_builtin:
            return list(self._presets.values())
        else:
            return [p for p in self._presets.values() if not p.is_builtin]
    
    def list_preset_names(self, include_builtin: bool = True) -> list[str]:
        """
        Get list of preset names.
        
        Args:
            include_builtin: Whether to include built-in presets
            
        Returns:
            List of preset names
        """
        presets = self.list_presets(include_builtin)
        # Sort with built-in first, then custom alphabetically
        builtin = sorted([p.name for p in presets if p.is_builtin])
        custom = sorted([p.name for p in presets if not p.is_builtin])
        return builtin + custom
    
    def preset_exists(self, name: str) -> bool:
        """Check if a preset exists."""
        return name in self._presets
    
    def is_builtin(self, name: str) -> bool:
        """Check if a preset is built-in."""
        return name in self._presets and self._presets[name].is_builtin
    
    def get_custom_count(self) -> int:
        """Get number of custom presets."""
        return len([p for p in self._presets.values() if not p.is_builtin])
    
    def get_builtin_count(self) -> int:
        """Get number of built-in presets."""
        return len([p for p in self._presets.values() if p.is_builtin])
    
    def export_presets(self, file_path: str) -> bool:
        """
        Export custom presets to a file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if export successful
        """
        try:
            custom_presets = [p.to_dict() for p in self._presets.values() if not p.is_builtin]
            
            data = {
                'version': '2.11',
                'export_date': datetime.now().isoformat(),
                'presets': custom_presets
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.success(f"Exported {len(custom_presets)} preset(s) to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export presets: {e}")
            return False
    
    def import_presets(self, file_path: str, overwrite: bool = False) -> int:
        """
        Import presets from a file.
        
        Args:
            file_path: Path to import file
            overwrite: Whether to overwrite existing presets
            
        Returns:
            Number of presets imported
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            presets_data = data.get('presets', [])
            imported = 0
            
            for preset_data in presets_data:
                preset = SizePreset.from_dict(preset_data)
                preset.is_builtin = False  # Imported presets are never built-in
                
                if preset.name in self._presets:
                    if self._presets[preset.name].is_builtin:
                        logger.warning(f"Skipping import, conflicts with built-in: {preset.name}")
                        continue
                    if not overwrite:
                        logger.warning(f"Skipping existing preset: {preset.name}")
                        continue
                
                self._presets[preset.name] = preset
                imported += 1
            
            if imported > 0:
                self._save_presets()
                logger.success(f"Imported {imported} preset(s)")
            
            return imported
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid preset file format: {e}")
            return 0
        except Exception as e:
            logger.error(f"Failed to import presets: {e}")
            return 0
    
    def duplicate_preset(self, name: str) -> str | None:
        """
        Create a copy of an existing preset.
        
        Args:
            name: Name of preset to duplicate
            
        Returns:
            Name of new preset, or None if failed
        """
        if name not in self._presets:
            return None
        
        source = self._presets[name]
        
        # Generate unique name
        new_name = f"{name} (Copy)"
        counter = 1
        while new_name in self._presets:
            counter += 1
            new_name = f"{name} (Copy {counter})"
        
        # Create copy
        success = self.save_preset(
            name=new_name,
            sizes=source.sizes.copy(),
            autofill=source.autofill,
            png_compression=source.png_compression,
            description=f"Copy of {name}"
        )
        
        return new_name if success else None


# Singleton instance
_preset_manager: PresetManager | None = None


def get_preset_manager() -> PresetManager:
    """
    Get the global preset manager instance.
    
    Returns:
        PresetManager singleton instance
    """
    global _preset_manager
    if _preset_manager is None:
        _preset_manager = PresetManager()
    return _preset_manager


# ==================== Module Exports ====================

__all__: list[str] = [
    'SizePreset',
    'PresetManager',
    'get_preset_manager',
    'BUILTIN_PRESETS',
]
