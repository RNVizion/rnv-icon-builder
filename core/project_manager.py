"""
RNV Icon Builder - Project Manager Module
Manages saving and loading project files (.rnvicon).

Features:
- Save/load complete project state
- Embed images or reference external files
- Track settings and adjustments
- Auto-save support
"""

from __future__ import annotations

import json
import base64
import io
import os
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime

from PIL import Image

from utils.config import ICON_SIZES, USER_DATA_DIR, AUTO_SAVE_PATH, LAST_SESSION_PATH
from utils.logger import Logger, get_logger_instance
from utils.file_utils import FileUtils

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)

# Project file extension
PROJECT_EXTENSION = ".rnvicon"


@dataclass
class ProjectSettings:
    """
    Project settings configuration.
    
    Attributes:
        selected_sizes: List of sizes to include
        autofill: Whether to autofill missing sizes
        png_compression: Whether to use PNG compression
        preset_name: Name of active preset (if any)
    """
    selected_sizes: list[int] = field(default_factory=lambda: ICON_SIZES.copy())
    autofill: bool = True
    png_compression: bool = True
    preset_name: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'selected_sizes': self.selected_sizes,
            'autofill': self.autofill,
            'png_compression': self.png_compression,
            'preset_name': self.preset_name
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectSettings:
        """Create from dictionary."""
        return cls(
            selected_sizes=data.get('selected_sizes', ICON_SIZES.copy()),
            autofill=data.get('autofill', True),
            png_compression=data.get('png_compression', True),
            preset_name=data.get('preset_name', '')
        )


@dataclass
class ProjectImage:
    """
    Represents an image in the project.
    
    Attributes:
        size: Image size (width and height)
        source_path: Original source file path (if available)
        embedded_data: Base64 encoded PNG data (if embedded)
        is_embedded: Whether image data is embedded
        is_autofilled: Whether this was auto-generated
    """
    size: int
    source_path: str = ""
    embedded_data: str = ""
    is_embedded: bool = True
    is_autofilled: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'size': self.size,
            'source_path': self.source_path,
            'embedded_data': self.embedded_data if self.is_embedded else "",
            'is_embedded': self.is_embedded,
            'is_autofilled': self.is_autofilled
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectImage:
        """Create from dictionary."""
        return cls(
            size=data.get('size', 0),
            source_path=data.get('source_path', ''),
            embedded_data=data.get('embedded_data', ''),
            is_embedded=data.get('is_embedded', True),
            is_autofilled=data.get('is_autofilled', False)
        )
    
    def to_pil_image(self) -> Image.Image | None:
        """
        Convert to PIL Image.
        
        Returns:
            PIL Image or None if unable to decode
        """
        if self.is_embedded and self.embedded_data:
            try:
                img_data = base64.b64decode(self.embedded_data)
                # BytesIO doesn't need cleanup, but load data into memory
                img = Image.open(io.BytesIO(img_data))
                img.load()
                return img
            except Exception as e:
                logger.error(f"Failed to decode embedded image: {e}")
                return None
        elif self.source_path and os.path.exists(self.source_path):
            try:
                # Use context manager and return copy to ensure file handle is closed
                with Image.open(self.source_path) as img:
                    img.load()  # Load image data into memory
                    return img.copy()  # Return copy so we can close file
            except Exception as e:
                logger.error(f"Failed to load source image: {e}")
                return None
        return None
    
    @classmethod
    def from_pil_image(
        cls,
        img: Image.Image,
        source_path: str = "",
        embed: bool = True
    ) -> ProjectImage:
        """
        Create from PIL Image.
        
        Args:
            img: PIL Image
            source_path: Optional source file path
            embed: Whether to embed image data
            
        Returns:
            ProjectImage instance
        """
        size = img.width
        
        embedded_data = ""
        if embed:
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            embedded_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return cls(
            size=size,
            source_path=source_path,
            embedded_data=embedded_data,
            is_embedded=embed
        )


@dataclass
class Project:
    """
    Represents a complete project state.
    
    Attributes:
        name: Project name
        file_path: Path to project file (if saved)
        settings: Project settings
        images: Dictionary of images by size
        created: Creation timestamp
        modified: Last modified timestamp
        version: Project file version
    """
    name: str = "Untitled Project"
    file_path: str = ""
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    images: dict[int, ProjectImage] = field(default_factory=dict)
    created: str = ""
    modified: str = ""
    version: str = "2.11"
    
    def __post_init__(self):
        if not self.created:
            self.created = datetime.now().isoformat()
        if not self.modified:
            self.modified = self.created
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'version': self.version,
            'settings': self.settings.to_dict(),
            'images': {str(k): v.to_dict() for k, v in self.images.items()},
            'created': self.created,
            'modified': datetime.now().isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        """Create from dictionary."""
        project = cls(
            name=data.get('name', 'Untitled Project'),
            version=data.get('version', '2.11'),
            settings=ProjectSettings.from_dict(data.get('settings', {})),
            created=data.get('created', ''),
            modified=data.get('modified', '')
        )
        
        # Load images
        images_data = data.get('images', {})
        for size_str, img_data in images_data.items():
            try:
                size = int(size_str)
                project.images[size] = ProjectImage.from_dict(img_data)
            except (ValueError, TypeError):
                logger.warning(f"Invalid image size key: {size_str}")
        
        return project
    
    def update_modified(self) -> None:
        """Update the modified timestamp."""
        self.modified = datetime.now().isoformat()
    
    def get_image_count(self) -> int:
        """Get number of images in project."""
        return len(self.images)
    
    def has_images(self) -> bool:
        """Check if project has any images."""
        return len(self.images) > 0
    
    def get_sizes(self) -> list[int]:
        """Get list of available sizes."""
        return sorted(self.images.keys(), reverse=True)


class ProjectManager:
    """
    Manages saving and loading project files.
    
    Handles project file I/O, auto-save, and session management.
    
    Example:
        >>> manager = ProjectManager()
        >>> project = manager.create_new_project()
        >>> manager.add_images_to_project(project, images_dict)
        >>> manager.save_project(project, "my_project.rnvicon")
        >>> loaded = manager.load_project("my_project.rnvicon")
    """
    
    def __init__(self) -> None:
        """Initialize the project manager."""
        self._current_project: Project | None = None
        self._is_modified: bool = False
        logger.debug("ProjectManager initialized")
    
    def create_new_project(self, name: str = "Untitled Project") -> Project:
        """
        Create a new empty project.
        
        Args:
            name: Project name
            
        Returns:
            New Project instance
        """
        project = Project(name=name)
        logger.success(f"Created new project: {name}")
        return project
    
    def add_images_to_project(
        self,
        project: Project,
        images: dict[int, Image.Image],
        source_paths: dict[int, str] | None = None,
        embed: bool = True
    ) -> None:
        """
        Add images to a project.
        
        Args:
            project: Project to add images to
            images: Dictionary of PIL Images by size
            source_paths: Optional source paths by size
            embed: Whether to embed image data
        """
        if source_paths is None:
            source_paths = {}
        
        for size, img in images.items():
            source = source_paths.get(size, "")
            project.images[size] = ProjectImage.from_pil_image(img, source, embed)
        
        project.update_modified()
        logger.debug(f"Added {len(images)} image(s) to project")
    
    def get_images_from_project(self, project: Project) -> dict[int, Image.Image]:
        """
        Extract PIL Images from a project.
        
        Args:
            project: Project to extract images from
            
        Returns:
            Dictionary of PIL Images by size
        """
        images = {}
        for size, proj_img in project.images.items():
            pil_img = proj_img.to_pil_image()
            if pil_img:
                images[size] = pil_img
            else:
                logger.warning(f"Could not load image for size {size}")
        
        return images
    
    def save_project(
        self,
        project: Project,
        file_path: str,
        embed_images: bool = True
    ) -> bool:
        """
        Save a project to file.
        
        Args:
            project: Project to save
            file_path: Output file path
            embed_images: Whether to embed image data
            
        Returns:
            True if save successful
        """
        try:
            # Ensure .rnvicon extension
            if not file_path.endswith(PROJECT_EXTENSION):
                file_path += PROJECT_EXTENSION
            
            # Update project file path
            project.file_path = file_path
            project.update_modified()
            
            # Re-embed images if requested and they weren't embedded
            if embed_images:
                for size, proj_img in project.images.items():
                    if not proj_img.is_embedded:
                        pil_img = proj_img.to_pil_image()
                        if pil_img:
                            buffer = io.BytesIO()
                            pil_img.save(buffer, format='PNG')
                            proj_img.embedded_data = base64.b64encode(
                                buffer.getvalue()
                            ).decode('utf-8')
                            proj_img.is_embedded = True
            
            # Serialize and save
            data = project.to_dict()
            
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.success(f"Saved project: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            return False
    
    def load_project(self, file_path: str) -> Project | None:
        """
        Load a project from file.
        
        Args:
            file_path: Path to project file
            
        Returns:
            Project instance or None if load failed
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Project file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            project = Project.from_dict(data)
            project.file_path = file_path
            
            logger.success(f"Loaded project: {file_path} ({project.get_image_count()} images)")
            return project
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid project file format: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            return None
    
    def auto_save(self, project: Project) -> bool:
        """
        Auto-save the project to a temporary location.
        
        Args:
            project: Project to auto-save
            
        Returns:
            True if save successful
        """
        return self.save_project(project, str(AUTO_SAVE_PATH))
    
    def load_auto_save(self) -> Project | None:
        """
        Load the auto-saved project if it exists.
        
        Returns:
            Project or None if no auto-save exists
        """
        if AUTO_SAVE_PATH.exists():
            return self.load_project(str(AUTO_SAVE_PATH))
        return None
    
    def clear_auto_save(self) -> None:
        """Delete the auto-save file if it exists."""
        if AUTO_SAVE_PATH.exists():
            try:
                AUTO_SAVE_PATH.unlink()
                logger.debug("Cleared auto-save file")
            except Exception as e:
                logger.warning(f"Failed to clear auto-save: {e}")
    
    def save_last_session(self, project: Project) -> bool:
        """
        Save the current session for restoration on startup.
        
        Args:
            project: Project to save as last session
            
        Returns:
            True if save successful
        """
        return self.save_project(project, str(LAST_SESSION_PATH))
    
    def load_last_session(self) -> Project | None:
        """
        Load the last session if it exists.
        
        Returns:
            Project or None if no last session exists
        """
        if LAST_SESSION_PATH.exists():
            return self.load_project(str(LAST_SESSION_PATH))
        return None
    
    def has_last_session(self) -> bool:
        """Check if a last session file exists."""
        return LAST_SESSION_PATH.exists()
    
    def clear_last_session(self) -> None:
        """Delete the last session file if it exists."""
        if LAST_SESSION_PATH.exists():
            try:
                LAST_SESSION_PATH.unlink()
                logger.debug("Cleared last session file")
            except Exception as e:
                logger.warning(f"Failed to clear last session: {e}")
    
    def get_project_info(self, file_path: str) -> dict[str, Any] | None:
        """
        Get basic info about a project file without fully loading it.
        
        Args:
            file_path: Path to project file
            
        Returns:
            Dictionary with project info or None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'name': data.get('name', 'Unknown'),
                'version': data.get('version', 'Unknown'),
                'created': data.get('created', ''),
                'modified': data.get('modified', ''),
                'image_count': len(data.get('images', {})),
                'file_size': os.path.getsize(file_path)
            }
        except Exception as e:
            logger.debug(f"Could not read project info from '{file_path}': {e}")
            return None
    
    def export_images(
        self,
        project: Project,
        output_folder: str,
        format: str = 'PNG'
    ) -> int:
        """
        Export all project images to a folder.
        
        Args:
            project: Project to export from
            output_folder: Output folder path
            format: Image format (PNG, etc.)
            
        Returns:
            Number of images exported
        """
        try:
            if not FileUtils.create_directory_if_not_exists(output_folder):
                logger.error(f"Cannot create output folder: {output_folder}")
                return 0
            
            exported = 0
            
            images = self.get_images_from_project(project)
            for size, img in images.items():
                output_path = os.path.join(output_folder, f"icon_{size}.{format.lower()}")
                img.save(output_path, format=format)
                exported += 1
            
            logger.success(f"Exported {exported} image(s) to {output_folder}")
            return exported
            
        except Exception as e:
            logger.error(f"Failed to export images: {e}")
            return 0


# Singleton instance
_project_manager: ProjectManager | None = None


def get_project_manager() -> ProjectManager:
    """
    Get the global project manager instance.
    
    Returns:
        ProjectManager singleton instance
    """
    global _project_manager
    if _project_manager is None:
        _project_manager = ProjectManager()
    return _project_manager


# ==================== Module Exports ====================

__all__: list[str] = [
    'ProjectSettings',
    'ProjectImage',
    'Project',
    'ProjectManager',
    'get_project_manager',
    'PROJECT_EXTENSION',
    'AUTO_SAVE_PATH',
    'LAST_SESSION_PATH',
]
