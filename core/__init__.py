"""
RNV Icon Builder - Core Package
Contains core business logic modules for icon building.

Modules:
    icon_builder_core: ICO file generation, PNG compression, format exports
    image_processor: Load PNG/ICO/SVG, validate sizes, undo/redo stack
    batch_processor: Process multiple files with job queue
    folder_watcher: Monitor folders for auto-processing
    preset_manager: Save/load custom size presets
    project_manager: .rnvicon project file format
    recent_files: Track recently opened files/folders
    session_manager: Auto-save sessions, crash recovery
    export_history: Log of all exports with timestamps
"""

from .icon_builder_core import IconBuilderCore
from .image_processor import ImageProcessor
from .recent_files import RecentFilesManager
from .batch_processor import BatchProcessor, BatchJob, JobStatus
from .folder_watcher import FolderWatcher, WatchSettings
from .preset_manager import PresetManager, SizePreset
from .project_manager import ProjectManager, Project
from .export_history import ExportHistory, ExportEntry
from .session_manager import SessionManager, SessionState

__all__: list[str] = [
    'IconBuilderCore',
    'ImageProcessor',
    'RecentFilesManager',
    'BatchProcessor',
    'BatchJob',
    'JobStatus',
    'FolderWatcher',
    'WatchSettings',
    'PresetManager',
    'SizePreset',
    'ProjectManager',
    'Project',
    'ExportHistory',
    'ExportEntry',
    'SessionManager',
    'SessionState',
]
