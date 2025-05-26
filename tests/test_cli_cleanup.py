"""Tests for the cleanup command"""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, Mock
from gcphound.cli import cli


class TestCleanupCommand:
    """Test the cleanup command functionality"""
    
    def test_cleanup_command_exists(self):
        """Test that cleanup command is available"""
        runner = CliRunner()
        result = runner.invoke(cli, ['cleanup', '--help'])
        assert result.exit_code == 0
        assert 'Clean up all generated files' in result.output
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.rglob')
    def test_cleanup_dry_run(self, mock_rglob, mock_glob, mock_is_file, mock_is_dir, mock_exists):
        """Test cleanup with --dry-run flag"""
        # Mock file system
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_is_file.return_value = False
        mock_glob.return_value = []
        mock_rglob.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['cleanup', '--dry-run'])
        
        assert result.exit_code == 0
        assert 'DRY RUN: No files were actually deleted' in result.output
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.rglob')
    def test_cleanup_no_files(self, mock_rglob, mock_glob, mock_is_file, mock_is_dir, mock_exists):
        """Test cleanup when no files to delete"""
        # Mock no files exist
        mock_exists.return_value = False
        mock_is_dir.return_value = False
        mock_is_file.return_value = False
        mock_glob.return_value = []
        mock_rglob.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['cleanup', '--force'])
        
        assert result.exit_code == 0
        assert 'No files to clean up' in result.output
        assert 'workspace is already clean' in result.output
    
    @patch('shutil.rmtree')
    @patch('pathlib.Path.unlink')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.stat')
    def test_cleanup_with_force(self, mock_stat, mock_rglob, mock_glob, mock_is_file, 
                               mock_is_dir, mock_exists, mock_unlink, mock_rmtree):
        """Test cleanup with --force flag"""
        # Mock file system
        mock_exists.return_value = True
        mock_is_dir.side_effect = lambda: True  # First call returns True
        mock_is_file.return_value = False
        mock_glob.return_value = []
        mock_rglob.return_value = []
        
        # Mock stat for size calculation
        mock_stat_obj = Mock()
        mock_stat_obj.st_size = 1024 * 1024  # 1MB
        mock_stat.return_value = mock_stat_obj
        
        runner = CliRunner()
        result = runner.invoke(cli, ['cleanup', '--force'])
        
        assert result.exit_code == 0
        assert 'Cleanup completed!' in result.output
        assert 'EscaGCP is now clean and ready for a fresh start!' in result.output
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.rglob')
    def test_cleanup_cancelled(self, mock_rglob, mock_glob, mock_is_file, mock_is_dir, mock_exists):
        """Test cleanup cancelled by user"""
        # Mock file system
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_is_file.return_value = False
        mock_glob.return_value = []
        mock_rglob.return_value = []
        
        runner = CliRunner()
        # Simulate user entering 'n' for no
        result = runner.invoke(cli, ['cleanup'], input='n\n')
        
        assert result.exit_code == 0
        assert 'WARNING: This action cannot be undone!' in result.output
        assert 'Cleanup cancelled' in result.output
    
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.rglob')
    def test_cleanup_with_errors(self, mock_rglob, mock_glob, mock_is_file, 
                                mock_is_dir, mock_exists, mock_rmtree):
        """Test cleanup handles errors gracefully"""
        # Mock file system
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_is_file.return_value = False
        mock_glob.return_value = []
        mock_rglob.return_value = []
        
        # Mock deletion error
        mock_rmtree.side_effect = PermissionError("Permission denied")
        
        runner = CliRunner()
        with patch('gcphound.utils.logger.get_logger') as mock_logger:
            result = runner.invoke(cli, ['cleanup', '--force'])
            
            assert result.exit_code == 0
            assert 'Errors:' in result.output or 'Deleted: 0 items' in result.output 