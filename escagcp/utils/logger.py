"""
Logging utilities for EscaGCP
"""

import logging
import sys
from typing import Optional

# Try to import rich for better logging
try:
    from rich.logging import RichHandler
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Try to import tqdm as fallback
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handler if logger doesn't have one
    if not logger.handlers:
        if RICH_AVAILABLE:
            handler = RichHandler(rich_tracebacks=True)
        else:
            handler = logging.StreamHandler(sys.stdout)
        
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


def setup_logging(level: str = 'INFO', log_file: Optional[str] = None):
    """
    Setup logging configuration
    
    Args:
        level: Logging level
        log_file: Optional log file path
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    if RICH_AVAILABLE:
        console_handler = RichHandler(rich_tracebacks=True)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
    
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        root_logger.addHandler(file_handler)


class ProgressLogger:
    """
    Progress logger that uses rich or tqdm if available
    """
    
    def __init__(self, total: Optional[int] = None, description: str = "Processing"):
        """
        Initialize progress logger
        
        Args:
            total: Total number of items (None for indeterminate)
            description: Description of the task
        """
        self.total = total
        self.description = description
        self._progress = None
        self._task = None
    
    def __enter__(self):
        """Enter context manager"""
        if RICH_AVAILABLE:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeRemainingColumn(),
            )
            self._progress.__enter__()
            self._task = self._progress.add_task(self.description, total=self.total)
        elif TQDM_AVAILABLE:
            self._progress = tqdm(total=self.total, desc=self.description)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        if self._progress:
            if RICH_AVAILABLE:
                self._progress.__exit__(exc_type, exc_val, exc_tb)
            elif TQDM_AVAILABLE:
                self._progress.close()
    
    def update(self, advance: int = 1):
        """
        Update progress
        
        Args:
            advance: Number of items completed
        """
        if self._progress:
            if RICH_AVAILABLE and self._task is not None:
                self._progress.update(self._task, advance=advance)
            elif TQDM_AVAILABLE:
                self._progress.update(advance) 