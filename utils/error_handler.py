"""
RNV Icon Builder - Error Handler Module
Centralized error handling with safe execution wrappers and user-friendly dialogs.

Features:
- Safe execution wrappers for risky operations
- Automatic error logging with context
- User-friendly error dialogs
- Exception categorization
- Retry mechanisms
- Error recovery suggestions
"""

from __future__ import annotations

from typing import Callable, Any, TypeVar
from functools import wraps

from PyQt6.QtWidgets import QMessageBox, QWidget

from utils.logger import Logger, get_logger_instance
from utils.dialog_helper import DialogHelper

# Setup logger for this module
logger: Logger = get_logger_instance(__name__)

# Type variable for generic functions
T = TypeVar('T')


# ==================== Error Categories ====================

class ErrorCategory:
    """
    Error category classification for better error handling.
    
    Attributes:
        FILE_IO: File input/output errors
        IMAGE_PROCESSING: Image processing errors
        VALIDATION: Input validation errors
        PERMISSION: Permission/access errors
        NETWORK: Network-related errors
        UNKNOWN: Unclassified errors
        USER_CANCELLED: User cancelled operation
        RESOURCE: Resource exhaustion errors (memory, disk)
    """
    
    FILE_IO: str = "File I/O Error"
    IMAGE_PROCESSING: str = "Image Processing Error"
    VALIDATION: str = "Validation Error"
    PERMISSION: str = "Permission Error"
    NETWORK: str = "Network Error"
    UNKNOWN: str = "Unknown Error"
    USER_CANCELLED: str = "User Cancelled"
    RESOURCE: str = "Resource Error"


# ==================== Error Handler Class ====================

class ErrorHandler:
    """
    Centralized error handling with logging and user notifications.
    
    Provides static methods for safe execution, error dialogs,
    and user confirmations.
    
    Example:
        >>> success, result = ErrorHandler.safe_execute(
        ...     func=load_image,
        ...     operation_name="Loading image",
        ...     args=(file_path,),
        ...     show_error_dialog=True,
        ...     parent_widget=self
        ... )
    """
    
    @staticmethod
    def safe_execute(
        func: Callable[..., T],
        operation_name: str,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
        default_return: Any = None,
        show_error_dialog: bool = False,
        parent_widget: QWidget | None = None,
        error_category: str = ErrorCategory.UNKNOWN,
        critical: bool = False
    ) -> tuple[bool, Any]:
        """
        Execute a function safely with automatic error handling.
        
        Args:
            func: Function to execute
            operation_name: Human-readable operation name for logging
            args: Positional arguments for func
            kwargs: Keyword arguments for func
            default_return: Value to return on error
            show_error_dialog: Whether to show error dialog to user
            parent_widget: Parent widget for error dialog
            error_category: Category of error for better handling
            critical: Whether this is a critical error (affects app stability)
            
        Returns:
            Tuple of (success: bool, result or default_return)
            
        Example:
            >>> success, result = ErrorHandler.safe_execute(
            ...     func=load_image,
            ...     operation_name="Loading image file",
            ...     args=(file_path,),
            ...     show_error_dialog=True,
            ...     parent_widget=self
            ... )
        """
        if kwargs is None:
            kwargs = {}
        
        try:
            logger.debug(f"Executing: {operation_name}")
            result: T = func(*args, **kwargs)
            logger.debug(f"Success: {operation_name}")
            return True, result
            
        except FileNotFoundError as e:
            error_msg: str = f"File not found: {str(e)}"
            ErrorHandler._handle_error(
                error=e,
                operation_name=operation_name,
                error_msg=error_msg,
                error_category=ErrorCategory.FILE_IO,
                show_dialog=show_error_dialog,
                parent=parent_widget,
                critical=critical
            )
            return False, default_return
            
        except PermissionError as e:
            error_msg = f"Permission denied: {str(e)}"
            ErrorHandler._handle_error(
                error=e,
                operation_name=operation_name,
                error_msg=error_msg,
                error_category=ErrorCategory.PERMISSION,
                show_dialog=show_error_dialog,
                parent=parent_widget,
                critical=critical
            )
            return False, default_return
            
        except ValueError as e:
            error_msg = f"Invalid value: {str(e)}"
            ErrorHandler._handle_error(
                error=e,
                operation_name=operation_name,
                error_msg=error_msg,
                error_category=ErrorCategory.VALIDATION,
                show_dialog=show_error_dialog,
                parent=parent_widget,
                critical=critical
            )
            return False, default_return
            
        except MemoryError as e:
            error_msg = "Out of memory - file may be too large"
            ErrorHandler._handle_error(
                error=e,
                operation_name=operation_name,
                error_msg=error_msg,
                error_category=ErrorCategory.RESOURCE,
                show_dialog=show_error_dialog,
                parent=parent_widget,
                critical=True  # Memory errors are always critical
            )
            return False, default_return
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            ErrorHandler._handle_error(
                error=e,
                operation_name=operation_name,
                error_msg=error_msg,
                error_category=error_category,
                show_dialog=show_error_dialog,
                parent=parent_widget,
                critical=critical
            )
            return False, default_return
    
    @staticmethod
    def _handle_error(
        error: Exception,
        operation_name: str,
        error_msg: str,
        error_category: str,
        show_dialog: bool,
        parent: QWidget | None,
        critical: bool
    ) -> None:
        """
        Internal error handler - logs and optionally shows dialog.
        
        Args:
            error: The exception that occurred
            operation_name: Human-readable operation name
            error_msg: Error message to display
            error_category: Category of error
            show_dialog: Whether to show error dialog
            parent: Parent widget for dialog
            critical: Whether error is critical
        """
        # Log the error
        logger.error(f"{operation_name} failed: {error_msg}")
        logger.exception("Full stack trace:")
        
        # Log critical errors at CRITICAL level
        if critical:
            logger.critical(f"CRITICAL ERROR in {operation_name}: {error_msg}")
        
        # Show dialog if requested
        if show_dialog and parent:
            ErrorHandler.show_error_dialog(
                parent=parent,
                title=error_category,
                message=f"{operation_name} failed",
                details=error_msg,
                critical=critical
            )
    
    @staticmethod
    def show_error_dialog(
        parent: QWidget,
        title: str,
        message: str,
        details: str = "",
        critical: bool = False
    ) -> None:
        """
        Show a user-friendly error dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Main error message
            details: Detailed error information
            critical: Whether this is a critical error
            
        Example:
            >>> ErrorHandler.show_error_dialog(
            ...     parent=self,
            ...     title="Load Error",
            ...     message="Failed to load image",
            ...     details="File format not supported"
            ... )
        """
        logger.debug(f"Showing error dialog: {title}")
        
        msg_box = QMessageBox(parent)
        
        if critical:
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(f"Critical Error: {title}")
        else:
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(title)
        
        msg_box.setText(message)
        
        if details:
            msg_box.setInformativeText(details)
        
        # Add suggestion based on error type
        suggestion: str = ErrorHandler._get_error_suggestion(title, details)
        if suggestion:
            full_details: str = f"{details}\n\nSuggestion: {suggestion}"
            msg_box.setDetailedText(full_details)
        elif details:
            msg_box.setDetailedText(details)
        
        # Apply theme-aware styling
        msg_box.setStyleSheet(get_message_box_style(parent))
        
        msg_box.exec()
    
    @staticmethod
    def _get_error_suggestion(error_category: str, details: str) -> str:
        """
        Get helpful suggestion based on error type.
        
        Args:
            error_category: Category of error
            details: Error details
            
        Returns:
            Helpful suggestion for user
        """
        suggestions: dict[str, str] = {
            ErrorCategory.FILE_IO: (
                "Check that the file exists and is accessible. "
                "Verify the file path is correct."
            ),
            ErrorCategory.PERMISSION: (
                "Check that you have permission to access this file. "
                "Try running the application as administrator or check file permissions."
            ),
            ErrorCategory.IMAGE_PROCESSING: (
                "The image file may be corrupted or in an unsupported format. "
                "Try opening it in another program to verify it's valid."
            ),
            ErrorCategory.VALIDATION: (
                "Check that the input values are correct and within valid ranges. "
                "Ensure image dimensions match required sizes."
            ),
            ErrorCategory.RESOURCE: (
                "Close other applications to free up memory or disk space. "
                "Consider using smaller image files."
            ),
        }
        
        # Return category-specific suggestion
        for category, suggestion in suggestions.items():
            if category.lower() in error_category.lower():
                return suggestion
        
        # Check details for specific keywords
        details_lower: str = details.lower()
        if "disk" in details_lower or "space" in details_lower:
            return "Free up disk space and try again."
        
        if "memory" in details_lower:
            return "Close other applications and try again with smaller files."
        
        if "permission" in details_lower:
            return "Check file permissions and try running as administrator."
        
        return "Check the log files for more details."
    
    @staticmethod
    def confirm_action(
        parent: QWidget,
        title: str,
        message: str,
        details: str = "",
        default_yes: bool = False
    ) -> bool:
        """
        Show confirmation dialog for potentially destructive actions.
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Main message
            details: Additional details
            default_yes: Whether "Yes" is default button
            
        Returns:
            True if user confirmed, False otherwise
            
        Example:
            >>> if ErrorHandler.confirm_action(
            ...     parent=self,
            ...     title="Confirm Delete",
            ...     message="Delete all files?",
            ...     default_yes=False
            ... ):
            ...     delete_files()
        """
        logger.debug(f"Showing confirmation dialog: {title}")
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if details:
            msg_box.setInformativeText(details)
        
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if default_yes:
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        else:
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        # Apply theme-aware styling
        msg_box.setStyleSheet(get_message_box_style(parent))
        
        result: int = msg_box.exec()
        confirmed: bool = result == QMessageBox.StandardButton.Yes
        
        logger.debug(f"User {'confirmed' if confirmed else 'cancelled'} action: {title}")
        return confirmed


# ==================== Decorator for Safe Methods ====================

def safe_method(
    operation_name: str | None = None,
    show_error: bool = False,
    default_return: Any = None,
    critical: bool = False
) -> Callable[[Callable[..., T]], Callable[..., Any]]:
    """
    Decorator for class methods that need safe execution.
    
    Args:
        operation_name: Human-readable operation name
        show_error: Whether to show error dialog
        default_return: Value to return on error
        critical: Whether error is critical
        
    Returns:
        Decorated function with error handling
        
    Example:
        >>> @safe_method(operation_name="Loading configuration", show_error=True)
        ... def load_config(self):
        ...     # Code that might fail
        ...     pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Get operation name from function if not provided
            op_name: str = operation_name or f"{func.__name__}"
            
            # Determine parent widget (if self is a QWidget)
            parent: QWidget | None = self if isinstance(self, QWidget) else None
            
            success, result = ErrorHandler.safe_execute(
                func=lambda: func(self, *args, **kwargs),
                operation_name=op_name,
                show_error_dialog=show_error,
                parent_widget=parent,
                default_return=default_return,
                critical=critical
            )
            
            return result
        
        return wrapper
    return decorator


# ==================== File Operation Safety ====================

class SafeFileOperations:
    """
    Safe wrappers for common file operations.
    
    Provides static methods for safely opening, writing, and deleting files
    with proper error handling.
    """
    
    @staticmethod
    def safe_open_file(
        file_path: str,
        mode: str = 'r',
        encoding: str = 'utf-8',
        parent: QWidget | None = None
    ) -> tuple[bool, Any]:
        """
        Safely open a file with error handling.
        
        Args:
            file_path: Path to file
            mode: File open mode ('r', 'w', 'rb', etc.)
            encoding: File encoding (for text mode)
            parent: Parent widget for error dialogs
            
        Returns:
            Tuple of (success, file_handle or None)
            
        Example:
            >>> success, f = SafeFileOperations.safe_open_file("config.json")
            >>> if success:
            ...     data = f.read()
            ...     f.close()
        """
        def open_file() -> Any:
            if 'b' in mode:
                return open(file_path, mode)
            else:
                return open(file_path, mode, encoding=encoding)
        
        return ErrorHandler.safe_execute(
            func=open_file,
            operation_name=f"Opening file: {file_path}",
            show_error_dialog=parent is not None,
            parent_widget=parent,
            error_category=ErrorCategory.FILE_IO
        )
    
    @staticmethod
    def safe_write_file(
        file_path: str,
        content: str,
        parent: QWidget | None = None
    ) -> bool:
        """
        Safely write content to a file.
        
        Args:
            file_path: Path to file
            content: Content to write
            parent: Parent widget for error dialogs
            
        Returns:
            True if successful
            
        Example:
            >>> if SafeFileOperations.safe_write_file("output.txt", "Hello"):
            ...     print("File saved!")
        """
        def write_file() -> bool:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        success, _ = ErrorHandler.safe_execute(
            func=write_file,
            operation_name=f"Writing file: {file_path}",
            show_error_dialog=parent is not None,
            parent_widget=parent,
            error_category=ErrorCategory.FILE_IO
        )
        
        return success
    
    @staticmethod
    def safe_delete_file(
        file_path: str,
        confirm: bool = True,
        parent: QWidget | None = None
    ) -> bool:
        """
        Safely delete a file with optional confirmation.
        
        Args:
            file_path: Path to file
            confirm: Whether to confirm before deleting
            parent: Parent widget for dialogs
            
        Returns:
            True if successful
        """
        import os
        
        # Confirm deletion if requested
        if confirm and parent:
            confirmed: bool = ErrorHandler.confirm_action(
                parent=parent,
                title="Confirm Deletion",
                message="Are you sure you want to delete this file?",
                details=file_path,
                default_yes=False
            )
            
            if not confirmed:
                logger.info(f"File deletion cancelled by user: {file_path}")
                return False
        
        def delete_file() -> bool:
            os.remove(file_path)
            return True
        
        success, _ = ErrorHandler.safe_execute(
            func=delete_file,
            operation_name=f"Deleting file: {file_path}",
            show_error_dialog=parent is not None,
            parent_widget=parent,
            error_category=ErrorCategory.FILE_IO
        )
        
        return success


# ==================== Validation Helpers ====================

class ValidationHelper:
    """
    Helper functions for input validation with error handling.
    
    Provides static methods for validating file paths, image sizes,
    and other common inputs.
    """
    
    @staticmethod
    def validate_file_path(
        file_path: str,
        must_exist: bool = True,
        extensions: list[str] | None = None
    ) -> tuple[bool, str]:
        """
        Validate a file path.
        
        Args:
            file_path: Path to validate
            must_exist: Whether file must exist
            extensions: List of allowed extensions (e.g., ['.png', '.ico'])
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Example:
            >>> valid, error = ValidationHelper.validate_file_path(
            ...     "image.png",
            ...     must_exist=True,
            ...     extensions=['.png', '.ico']
            ... )
        """
        import os
        
        if not file_path:
            return False, "File path is empty"
        
        if must_exist and not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
        
        if extensions:
            file_ext: str = os.path.splitext(file_path)[1].lower()
            if file_ext not in extensions:
                valid_exts: str = ', '.join(extensions)
                return False, f"Invalid file type. Expected: {valid_exts}"
        
        return True, ""
    
    @staticmethod
    def validate_image_size(
        width: int,
        height: int,
        valid_sizes: list[int] | None = None,
        must_be_square: bool = True
    ) -> tuple[bool, str]:
        """
        Validate image dimensions.
        
        Args:
            width: Image width
            height: Image height
            valid_sizes: List of valid sizes
            must_be_square: Whether image must be square
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Example:
            >>> valid, error = ValidationHelper.validate_image_size(
            ...     256, 256,
            ...     valid_sizes=[16, 32, 64, 128, 256],
            ...     must_be_square=True
            ... )
        """
        if must_be_square and width != height:
            return False, f"Image must be square (got {width}x{height})"
        
        if valid_sizes and width not in valid_sizes:
            valid_str: str = ', '.join(str(s) for s in valid_sizes)
            return False, f"Invalid size {width}x{height}. Valid sizes: {valid_str}"
        
        if width <= 0 or height <= 0:
            return False, f"Invalid dimensions: {width}x{height}"
        
        return True, ""


# ==================== Exception Context Manager ====================

class exception_handler:
    """
    Context manager for safe code execution.
    
    Provides a clean way to wrap code blocks with automatic
    exception handling and logging.
    
    Example:
        >>> with exception_handler("Loading images", parent=self):
        ...     # Code that might fail
        ...     load_images()
    """
    
    def __init__(
        self,
        operation_name: str,
        parent: QWidget | None = None,
        show_error: bool = True,
        critical: bool = False
    ) -> None:
        """
        Initialize exception handler context.
        
        Args:
            operation_name: Human-readable operation name
            parent: Parent widget for error dialogs
            show_error: Whether to show error dialog
            critical: Whether error is critical
        """
        self.operation_name: str = operation_name
        self.parent: QWidget | None = parent
        self.show_error: bool = show_error
        self.critical: bool = critical
    
    def __enter__(self) -> exception_handler:
        """Enter context - log operation start."""
        logger.debug(f"Starting: {self.operation_name}")
        return self
    
    def __exit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: Any
    ) -> bool:
        """
        Exit context - handle any exceptions.
        
        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
            
        Returns:
            True to suppress exception, False to propagate
        """
        if exc_type is not None:
            # An exception occurred
            ErrorHandler._handle_error(
                error=exc_val if exc_val else Exception("Unknown error"),
                operation_name=self.operation_name,
                error_msg=str(exc_val) if exc_val else "Unknown error",
                error_category=ErrorCategory.UNKNOWN,
                show_dialog=self.show_error,
                parent=self.parent,
                critical=self.critical
            )
            
            # Suppress the exception (return True)
            return True
        
        # No exception - log success
        logger.debug(f"Completed: {self.operation_name}")
        return False


# ==================== Styled Message Box Helper ====================

# Theme stylesheets - delegated to DialogHelper for consistency
# These are kept for backwards compatibility
def _get_dark_style() -> str:
    """Get dark theme stylesheet (backwards compatibility wrapper)."""
    return DialogHelper._get_style_dark()

def _get_light_style() -> str:
    """Get light theme stylesheet (backwards compatibility wrapper)."""
    return DialogHelper._get_style_light()

# NOTE: MESSAGEBOX_STYLE_DARK, MESSAGEBOX_STYLE_LIGHT, and MESSAGEBOX_STYLE
# were previously evaluated eagerly at import time but were never imported by
# any other module. Use get_message_box_style(parent) instead for proper
# theme-aware styling.


def get_message_box_style(parent: QWidget | None = None) -> str:
    """
    Get the appropriate message box style for the current theme.
    
    Args:
        parent: Parent widget to detect theme from
        
    Returns:
        CSS stylesheet string
    """
    return DialogHelper._get_style(parent)


def styled_message_box(
    parent: QWidget,
    icon: QMessageBox.Icon,
    title: str,
    text: str,
    informative_text: str = "",
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok
) -> QMessageBox.StandardButton:
    """
    Create and show a styled QMessageBox that matches the current theme.
    
    Args:
        parent: Parent widget
        icon: Message box icon (Information, Warning, Critical, Question)
        title: Window title
        text: Main message text
        informative_text: Additional informative text
        buttons: Standard buttons to show
        
    Returns:
        The button that was clicked
        
    Example:
        >>> result = styled_message_box(
        ...     self,
        ...     QMessageBox.Icon.Warning,
        ...     "No Files",
        ...     "No PNG or ICO files found."
        ... )
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(icon)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    
    if informative_text:
        msg_box.setInformativeText(informative_text)
    
    msg_box.setStandardButtons(buttons)
    msg_box.setStyleSheet(get_message_box_style(parent))
    
    return msg_box.exec()


def styled_question_box(
    parent: QWidget,
    title: str,
    text: str,
    informative_text: str = "",
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes
) -> QMessageBox.StandardButton:
    """
    Create and show a styled Yes/No/Cancel question dialog.
    
    Args:
        parent: Parent widget
        title: Window title
        text: Main message text
        informative_text: Additional informative text
        buttons: Standard buttons to show (default: Yes | No)
        default_button: Which button is default (default: Yes)
        
    Returns:
        The button that was clicked
        
    Example:
        >>> result = styled_question_box(
        ...     self,
        ...     "Output Location",
        ...     "Save files to same folder?",
        ...     buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        ... )
        >>> if result == QMessageBox.StandardButton.Yes:
        ...     # User clicked Yes
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    
    if informative_text:
        msg_box.setInformativeText(informative_text)
    
    msg_box.setStandardButtons(buttons)
    msg_box.setDefaultButton(default_button)
    msg_box.setStyleSheet(get_message_box_style(parent))
    
    return msg_box.exec()


# ==================== Module Exports ====================

__all__: list[str] = [
    'ErrorCategory',
    'ErrorHandler',
    'safe_method',
    'SafeFileOperations',
    'ValidationHelper',
    'exception_handler',
    'styled_message_box',
    'styled_question_box',
    'get_message_box_style',
]