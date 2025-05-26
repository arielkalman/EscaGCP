"""
Tests for logger utility
"""

import pytest
import logging
from unittest.mock import patch, Mock, MagicMock
from gcphound.utils.logger import get_logger, ProgressLogger


class TestGetLogger:
    """Test the get_logger function"""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logging.Logger instance"""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_get_logger_with_rich_handler(self):
        """Test that logger has RichHandler when available"""
        with patch('gcphound.utils.logger.RichHandler') as mock_rich_handler:
            logger = get_logger("test_rich")
            # Check that RichHandler was used
            assert mock_rich_handler.called
    
    def test_get_logger_fallback_to_stream_handler(self):
        """Test fallback to StreamHandler when RichHandler not available"""
        with patch('gcphound.utils.logger.RICH_AVAILABLE', False):
            logger = get_logger("test_fallback")
            # Should have at least one handler
            assert len(logger.handlers) > 0
            # Should be StreamHandler
            assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    
    def test_get_logger_singleton(self):
        """Test that same logger instance is returned for same name"""
        logger1 = get_logger("test_singleton")
        logger2 = get_logger("test_singleton")
        assert logger1 is logger2
    
    def test_get_logger_different_names(self):
        """Test that different names return different loggers"""
        logger1 = get_logger("test_module1")
        logger2 = get_logger("test_module2")
        assert logger1 is not logger2
        assert logger1.name == "test_module1"
        assert logger2.name == "test_module2"


class TestProgressLogger:
    """Test the ProgressLogger context manager"""
    
    def test_progress_logger_initialization(self):
        """Test ProgressLogger initialization with various parameters"""
        # Test with total
        progress = ProgressLogger(total=100, description="Test")
        assert progress.total == 100
        assert progress.description == "Test"
        
        # Test without total
        progress = ProgressLogger(description="No total")
        assert progress.total is None
        assert progress.description == "No total"
    
    @patch('gcphound.utils.logger.Progress')
    def test_progress_logger_context_manager(self, mock_progress_class):
        """Test ProgressLogger as context manager"""
        # Create a mock progress instance with context manager support
        mock_progress = MagicMock()
        mock_progress.__enter__ = MagicMock(return_value=mock_progress)
        mock_progress.__exit__ = MagicMock(return_value=None)
        mock_progress_class.return_value = mock_progress
        
        with ProgressLogger(total=50, description="Test") as progress:
            assert progress is not None
            assert progress._progress is mock_progress
        
        # Verify context manager methods were called
        mock_progress.__enter__.assert_called_once()
        mock_progress.__exit__.assert_called_once()
    
    @patch('gcphound.utils.logger.Progress')
    def test_progress_logger_update(self, mock_progress_class):
        """Test updating progress"""
        # Create a mock progress instance with context manager support
        mock_progress = MagicMock()
        mock_progress.__enter__ = MagicMock(return_value=mock_progress)
        mock_progress.__exit__ = MagicMock(return_value=None)
        mock_task = MagicMock()
        mock_progress.add_task = MagicMock(return_value=mock_task)
        mock_progress.update = MagicMock()
        mock_progress_class.return_value = mock_progress
        
        with ProgressLogger(total=100, description="Test") as progress:
            progress.update(10)
            mock_progress.update.assert_called_with(mock_task, advance=10)
            
            progress.update(5)
            mock_progress.update.assert_called_with(mock_task, advance=5)
    
    @patch('gcphound.utils.logger.Progress')
    def test_progress_logger_update_without_total(self, mock_progress_class):
        """Test updating progress without total"""
        # Create a mock progress instance with context manager support
        mock_progress = MagicMock()
        mock_progress.__enter__ = MagicMock(return_value=mock_progress)
        mock_progress.__exit__ = MagicMock(return_value=None)
        mock_task = MagicMock()
        mock_progress.add_task = MagicMock(return_value=mock_task)
        mock_progress.update = MagicMock()
        mock_progress_class.return_value = mock_progress
        
        with ProgressLogger(description="No total") as progress:
            progress.update(1)
            mock_progress.update.assert_called_with(mock_task, advance=1)
    
    @patch('gcphound.utils.logger.RICH_AVAILABLE', False)
    @patch('gcphound.utils.logger.TQDM_AVAILABLE', True)
    @patch('gcphound.utils.logger.tqdm')
    def test_progress_logger_fallback_to_tqdm(self, mock_tqdm):
        """Test fallback to tqdm when rich is not available"""
        # Create a mock tqdm instance with context manager support
        mock_tqdm_instance = MagicMock()
        mock_tqdm_instance.__enter__ = MagicMock(return_value=mock_tqdm_instance)
        mock_tqdm_instance.__exit__ = MagicMock(return_value=None)
        mock_tqdm_instance.close = MagicMock()
        mock_tqdm.return_value = mock_tqdm_instance
        
        with ProgressLogger(total=100, description="Test") as progress:
            assert progress._progress is mock_tqdm_instance
        
        mock_tqdm.assert_called_once_with(total=100, desc="Test")
        mock_tqdm_instance.close.assert_called_once()
    
    @patch('gcphound.utils.logger.RICH_AVAILABLE', False)
    @patch('gcphound.utils.logger.TQDM_AVAILABLE', False)
    def test_progress_logger_no_progress_library(self):
        """Test when no progress library is available"""
        with ProgressLogger(total=100, description="Test") as progress:
            # Should work without error
            progress.update(10)
            assert progress._progress is None
    
    @patch('gcphound.utils.logger.Progress')
    def test_progress_logger_with_exception(self, mock_progress_class):
        """Test progress logger handles exceptions properly"""
        # Create a mock progress instance with context manager support
        mock_progress = MagicMock()
        mock_progress.__enter__ = MagicMock(return_value=mock_progress)
        mock_progress.__exit__ = MagicMock(return_value=None)
        mock_progress_class.return_value = mock_progress
        
        try:
            with ProgressLogger(total=100, description="Test") as progress:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Verify __exit__ was still called
        mock_progress.__exit__.assert_called_once()
    
    def test_progress_logger_custom_columns(self):
        """Test progress logger with custom columns"""
        with patch('gcphound.utils.logger.Progress') as mock_progress_class:
            with patch('gcphound.utils.logger.SpinnerColumn') as mock_spinner:
                with patch('gcphound.utils.logger.TextColumn') as mock_text:
                    with patch('gcphound.utils.logger.BarColumn') as mock_bar:
                        with patch('gcphound.utils.logger.TimeRemainingColumn') as mock_time:
                            with ProgressLogger(total=100, description="Test"):
                                # Check that columns were created
                                mock_spinner.assert_called_once()
                                mock_text.assert_called_once()
                                mock_bar.assert_called_once()
                                mock_time.assert_called_once() 