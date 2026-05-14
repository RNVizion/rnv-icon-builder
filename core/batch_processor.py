"""
RNV Icon Builder - Batch Processor Module
Handles batch processing of multiple image files to ICO format.

Features:
- Queue multiple jobs for processing
- Process all jobs with progress tracking
- Background thread processing
- Error handling per job (one failure doesn't stop batch)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
import threading

from PyQt6.QtCore import QObject, pyqtSignal

from utils.config import ICON_SIZES, SUPPORTED_EXTENSIONS
from utils.logger import Logger, get_logger_instance
from utils.file_utils import FileUtils

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)


class JobStatus(Enum):
    """Status values for batch jobs."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    """
    Represents a single batch processing job.
    
    Attributes:
        source_path: Path to source image file
        output_path: Path for output ICO file
        settings: Dictionary of processing settings
        status: Current job status
        error_message: Error message if job failed
        result: Result dictionary from processing
    """
    source_path: str
    output_path: str
    settings: dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    error_message: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary for serialization."""
        return {
            'source_path': self.source_path,
            'output_path': self.output_path,
            'settings': self.settings,
            'status': self.status.value,
            'error_message': self.error_message,
            'result': self.result
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchJob:
        """Create job from dictionary."""
        job = cls(
            source_path=data.get('source_path', ''),
            output_path=data.get('output_path', ''),
            settings=data.get('settings', {})
        )
        job.status = JobStatus(data.get('status', 'pending'))
        job.error_message = data.get('error_message', '')
        job.result = data.get('result', {})
        return job


class BatchProcessor(QObject):
    """
    Handles batch processing of multiple image files.
    
    Processes multiple source images into ICO files with progress tracking
    and error handling. Each job is independent - one failure doesn't
    stop the batch.
    
    Signals:
        job_started: Emitted when a job starts (job_index)
        job_completed: Emitted when a job completes (job_index, success)
        job_progress: Emitted for progress updates (job_index, progress_percent)
        batch_started: Emitted when batch processing starts (total_jobs)
        batch_completed: Emitted when all jobs are done (completed, failed, cancelled)
        batch_progress: Emitted for overall progress (completed_count, total_count)
        
    Example:
        >>> processor = BatchProcessor()
        >>> processor.add_job("icon.png", "icon.ico", {"sizes": [256, 48, 32, 16]})
        >>> processor.add_job("logo.png", "logo.ico")
        >>> processor.batch_completed.connect(on_complete)
        >>> processor.process_all()
    """
    
    # Signals
    job_started = pyqtSignal(int)           # job_index
    job_completed = pyqtSignal(int, bool)    # job_index, success
    job_progress = pyqtSignal(int, int)      # job_index, progress_percent
    batch_started = pyqtSignal(int)          # total_jobs
    batch_completed = pyqtSignal(int, int, int)  # completed, failed, cancelled
    batch_progress = pyqtSignal(int, int)    # completed_count, total_count
    
    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the batch processor."""
        super().__init__(parent)
        
        self._jobs: list[BatchJob] = []
        self._is_processing: bool = False
        self._cancel_requested: bool = False
        self._executor: ThreadPoolExecutor | None = None
        self._current_future: Future | None = None
        self._lock = threading.Lock()
        
        logger.debug("BatchProcessor initialized")
    
    def add_job(
        self,
        source_path: str,
        output_path: str,
        settings: dict[str, Any] | None = None
    ) -> int:
        """
        Add a job to the batch queue.
        
        Args:
            source_path: Path to source image (PNG, ICO, or SVG)
            output_path: Path for output ICO file
            settings: Optional processing settings dict:
                - sizes: List of sizes to include
                - autofill: Whether to autofill missing sizes
                - png_compression: Whether to use PNG compression
                
        Returns:
            Index of the added job
            
        Example:
            >>> idx = processor.add_job("icon.png", "icon.ico")
        """
        if settings is None:
            settings = {
                'sizes': ICON_SIZES.copy(),
                'autofill': True,
                'png_compression': True
            }
        
        job = BatchJob(
            source_path=source_path,
            output_path=output_path,
            settings=settings
        )
        
        with self._lock:
            self._jobs.append(job)
            job_index = len(self._jobs) - 1
        
        logger.debug(f"Added batch job {job_index}: {source_path} -> {output_path}")
        return job_index
    
    def add_jobs_from_folder(
        self,
        folder_path: str,
        output_folder: str,
        settings: dict[str, Any] | None = None,
        recursive: bool = False
    ) -> int:
        """
        Add jobs for all valid images in a folder.
        
        Args:
            folder_path: Source folder containing images
            output_folder: Output folder for ICO files
            settings: Processing settings for all jobs
            recursive: Whether to scan subfolders
            
        Returns:
            Number of jobs added
        """
        folder = Path(folder_path)
        output = Path(output_folder)
        output.mkdir(parents=True, exist_ok=True)
        
        added_count = 0
        
        if recursive:
            files = folder.rglob('*')
        else:
            files = folder.glob('*')
        
        for file_path in files:
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                # Generate output path
                output_name = file_path.stem + '.ico'
                output_path = output / output_name
                
                self.add_job(str(file_path), str(output_path), settings)
                added_count += 1
        
        logger.info(f"Added {added_count} jobs from folder: {folder_path}")
        return added_count
    
    def remove_job(self, index: int) -> bool:
        """
        Remove a job from the queue (only if pending).
        
        Args:
            index: Job index to remove
            
        Returns:
            True if removed successfully
        """
        with self._lock:
            if 0 <= index < len(self._jobs):
                if self._jobs[index].status == JobStatus.PENDING:
                    del self._jobs[index]
                    logger.debug(f"Removed batch job {index}")
                    return True
                else:
                    logger.warning(f"Cannot remove job {index}: not pending")
        return False
    
    def clear_jobs(self) -> None:
        """Clear all pending jobs from the queue."""
        with self._lock:
            pending_count = len([j for j in self._jobs if j.status == JobStatus.PENDING])
            self._jobs = [j for j in self._jobs if j.status != JobStatus.PENDING]
        logger.info(f"Cleared {pending_count} pending job(s)")
    
    def clear_all(self) -> None:
        """Clear all jobs regardless of status."""
        with self._lock:
            count = len(self._jobs)
            self._jobs.clear()
        logger.info(f"Cleared all {count} job(s)")
    
    def get_jobs(self) -> list[BatchJob]:
        """Get a copy of all jobs."""
        with self._lock:
            return self._jobs.copy()
    
    def get_job(self, index: int) -> BatchJob | None:
        """Get a specific job by index."""
        with self._lock:
            if 0 <= index < len(self._jobs):
                return self._jobs[index]
        return None
    
    def get_job_count(self) -> int:
        """Get total number of jobs."""
        with self._lock:
            return len(self._jobs)
    
    def get_pending_count(self) -> int:
        """Get number of pending jobs."""
        with self._lock:
            return len([j for j in self._jobs if j.status == JobStatus.PENDING])
    
    def is_processing(self) -> bool:
        """Check if batch is currently processing."""
        return self._is_processing
    
    def process_all(self) -> None:
        """
        Start processing all pending jobs.
        
        Processing runs in a background thread. Connect to signals
        to track progress and completion.
        """
        if self._is_processing:
            logger.warning("Batch processing already in progress")
            return
        
        pending_jobs = [j for j in self._jobs if j.status == JobStatus.PENDING]
        if not pending_jobs:
            logger.warning("No pending jobs to process")
            return
        
        logger.info(f"Starting batch processing: {len(pending_jobs)} job(s)")
        self._is_processing = True
        self._cancel_requested = False
        
        # Start processing in background thread
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._current_future = self._executor.submit(self._process_jobs)
    
    def cancel(self) -> None:
        """Request cancellation of batch processing."""
        if self._is_processing:
            logger.info("Batch cancellation requested")
            self._cancel_requested = True
    
    def _process_jobs(self) -> None:
        """Internal method to process all pending jobs (runs in thread)."""
        from core.image_processor import ImageProcessor
        from core.icon_builder_core import IconBuilderCore
        
        # Get pending jobs
        with self._lock:
            pending_indices = [
                i for i, j in enumerate(self._jobs) 
                if j.status == JobStatus.PENDING
            ]
        
        total = len(pending_indices)
        completed = 0
        failed = 0
        cancelled = 0
        
        self.batch_started.emit(total)
        
        for job_index in pending_indices:
            # Check for cancellation
            if self._cancel_requested:
                with self._lock:
                    self._jobs[job_index].status = JobStatus.CANCELLED
                cancelled += 1
                continue
            
            # Process this job
            with self._lock:
                job = self._jobs[job_index]
                job.status = JobStatus.PROCESSING
            
            self.job_started.emit(job_index)
            
            try:
                success = self._process_single_job(job_index)
                if success:
                    completed += 1
                else:
                    failed += 1
            except Exception as e:
                with self._lock:
                    self._jobs[job_index].status = JobStatus.FAILED
                    self._jobs[job_index].error_message = str(e)
                failed += 1
                logger.error(f"Job {job_index} exception: {e}")
            
            self.job_completed.emit(job_index, job.status == JobStatus.COMPLETED)
            self.batch_progress.emit(completed + failed + cancelled, total)
        
        # Mark any remaining pending as cancelled
        if self._cancel_requested:
            with self._lock:
                for job in self._jobs:
                    if job.status == JobStatus.PENDING:
                        job.status = JobStatus.CANCELLED
                        cancelled += 1
        
        self._is_processing = False
        self.batch_completed.emit(completed, failed, cancelled)
        
        logger.info(f"Batch complete: {completed} completed, {failed} failed, {cancelled} cancelled")
        
        # Cleanup executor
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
    
    def _process_single_job(self, job_index: int) -> bool:
        """
        Process a single job.
        
        Args:
            job_index: Index of job to process
            
        Returns:
            True if successful
        """
        from core.image_processor import ImageProcessor
        from core.icon_builder_core import IconBuilderCore
        
        with self._lock:
            job = self._jobs[job_index]
        
        source_path = job.source_path
        output_path = job.output_path
        settings = job.settings
        
        # Validate source exists
        if not os.path.exists(source_path):
            job.status = JobStatus.FAILED
            job.error_message = f"Source file not found: {source_path}"
            return False
        
        # Create image processor and load source
        processor = ImageProcessor()
        ext = os.path.splitext(source_path)[1].lower()
        
        try:
            if ext == '.png':
                processor.load_png(source_path)
            elif ext == '.ico':
                processor.load_ico(source_path)
            elif ext == '.svg':
                processor.load_svg(source_path)
            else:
                job.status = JobStatus.FAILED
                job.error_message = f"Unsupported file type: {ext}"
                return False
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = f"Failed to load source: {e}"
            return False
        
        images = processor.get_detected_images()
        if not images:
            job.status = JobStatus.FAILED
            job.error_message = "No valid images loaded from source"
            return False
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            FileUtils.create_directory_if_not_exists(output_dir)
        
        # Get settings
        sizes = settings.get('sizes', ICON_SIZES)
        autofill = settings.get('autofill', True)
        png_compression = settings.get('png_compression', True)
        
        # Build ICO
        try:
            success, message, info = IconBuilderCore.build_ico_file(
                images_dict=images,
                output_path=output_path,
                autofill=autofill,
                selected_sizes=sizes,
                use_png_compression=png_compression
            )
            
            with self._lock:
                if success:
                    self._jobs[job_index].status = JobStatus.COMPLETED
                    self._jobs[job_index].result = info
                    logger.success(f"Job {job_index} completed: {output_path}")
                else:
                    self._jobs[job_index].status = JobStatus.FAILED
                    self._jobs[job_index].error_message = message
                    logger.error(f"Job {job_index} failed: {message}")
            
            return success
            
        except Exception as e:
            with self._lock:
                self._jobs[job_index].status = JobStatus.FAILED
                self._jobs[job_index].error_message = str(e)
            logger.error(f"Job {job_index} build error: {e}")
            return False
    
    def get_summary(self) -> dict[str, int]:
        """
        Get summary of job statuses.
        
        Returns:
            Dictionary with counts by status
        """
        with self._lock:
            summary = {
                'total': len(self._jobs),
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0
            }
            for job in self._jobs:
                summary[job.status.value] += 1
        return summary
    
    def get_progress(self) -> float:
        """
        Get overall progress as percentage.
        
        Returns:
            Progress from 0.0 to 100.0
        """
        with self._lock:
            total = len(self._jobs)
            if total == 0:
                return 100.0
            
            done = len([j for j in self._jobs 
                       if j.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)])
            return (done / total) * 100.0


# ==================== Module Exports ====================

__all__: list[str] = [
    'JobStatus',
    'BatchJob',
    'BatchProcessor',
]