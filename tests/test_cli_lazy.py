"""Test the lazy mode CLI functionality"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from gcphound.cli import cli
from pathlib import Path


class TestLazyMode:
    """Test the --lazy mode functionality"""
    
    def test_run_command_exists(self):
        """Test that the run command exists"""
        runner = CliRunner()
        result = runner.invoke(cli, ['run', '--help'])
        assert result.exit_code == 0
        assert '--lazy' in result.output
        assert 'Run all operations automatically' in result.output
    
    def test_run_without_lazy_shows_help(self):
        """Test that run without --lazy shows help"""
        runner = CliRunner()
        with patch('gcphound.cli.Config.from_yaml', return_value=Mock()):
            result = runner.invoke(cli, ['run'])
            assert result.exit_code == 0
            assert 'Manual execution steps:' in result.output
            assert 'gcphound collect' in result.output
            assert 'gcphound run --lazy' in result.output
    
    @patch('subprocess.run')
    @patch('click.get_current_context')
    @patch('pathlib.Path.glob')
    @patch('webbrowser.open')
    @patch('platform.system')
    def test_lazy_mode_with_current_project(self, mock_platform, mock_browser, mock_glob, mock_ctx, mock_subprocess):
        """Test lazy mode using current project from gcloud"""
        # Mock platform to return something other than Darwin/Linux/Windows
        # This will force it to use webbrowser.open
        mock_platform.return_value = 'Other'
        
        # Mock gcloud command to return a project
        mock_subprocess.return_value = Mock(
            stdout='test-project-123',
            returncode=0
        )
        
        # Mock context and command invocations
        mock_context = Mock()
        mock_ctx.return_value = mock_context
        
        # Mock visualization files
        mock_viz_file = Mock()
        mock_viz_file.stat.return_value.st_mtime = 123456
        mock_viz_file.absolute.return_value = Path('/path/to/viz.html')
        mock_glob.return_value = [mock_viz_file]
        
        runner = CliRunner()
        with patch('gcphound.cli.Config.from_yaml', return_value=Mock()):
            result = runner.invoke(cli, ['run', '--lazy'])
            
            # Check that gcloud was called to get current project
            # The first call should be to get the current project
            assert mock_subprocess.call_count >= 1
            first_call = mock_subprocess.call_args_list[0]
            assert first_call[0][0] == ['gcloud', 'config', 'get-value', 'project']
            assert first_call[1]['capture_output'] == True
            assert first_call[1]['text'] == True
            assert first_call[1]['check'] == True
            
            # Check that all commands were invoked
            assert mock_context.invoke.call_count == 4  # collect, build, analyze, visualize
            
            # Check browser was opened
            mock_browser.assert_called_once()
    
    @patch('click.get_current_context')
    @patch('pathlib.Path.glob')
    @patch('webbrowser.open')
    def test_lazy_mode_with_specified_projects(self, mock_browser, mock_glob, mock_ctx):
        """Test lazy mode with explicitly specified projects"""
        # Mock context and command invocations
        mock_context = Mock()
        mock_ctx.return_value = mock_context
        
        # Mock visualization files
        mock_viz_file = Mock()
        mock_viz_file.stat.return_value.st_mtime = 123456
        mock_viz_file.absolute.return_value = Path('/path/to/viz.html')
        mock_glob.return_value = [mock_viz_file]
        
        runner = CliRunner()
        with patch('gcphound.cli.Config.from_yaml', return_value=Mock()):
            result = runner.invoke(cli, ['run', '--lazy', '-p', 'project1', '-p', 'project2'])
            
            # Check that all commands were invoked with the right projects
            calls = mock_context.invoke.call_args_list
            assert len(calls) == 4
            
            # Check collect was called with projects
            collect_call = calls[0]
            assert collect_call[1]['projects'] == ('project1', 'project2')
    
    @patch('subprocess.run')
    @patch('click.get_current_context')
    def test_lazy_mode_handles_no_current_project(self, mock_ctx, mock_subprocess):
        """Test lazy mode handles case when no current project is set"""
        # Mock gcloud command to return empty
        mock_subprocess.return_value = Mock(
            stdout='',
            returncode=0
        )
        
        runner = CliRunner()
        with patch('gcphound.cli.Config.from_yaml', return_value=Mock()):
            result = runner.invoke(cli, ['run', '--lazy'])
            
            assert result.exit_code == 1
            assert 'No project specified' in result.output
    
    @patch('subprocess.run')
    @patch('click.get_current_context')
    @patch('pathlib.Path.glob')
    @patch('platform.system')
    def test_lazy_mode_chrome_opening_macos(self, mock_platform, mock_glob, mock_ctx, mock_subprocess):
        """Test Chrome opening on macOS"""
        mock_platform.return_value = 'Darwin'
        
        # Mock gcloud and context
        mock_subprocess.side_effect = [
            Mock(stdout='test-project', returncode=0),  # gcloud config
            Mock(returncode=0)  # open command
        ]
        mock_context = Mock()
        mock_ctx.return_value = mock_context
        
        # Mock visualization files
        mock_viz_file = Mock()
        mock_viz_file.stat.return_value.st_mtime = 123456
        mock_viz_file.absolute.return_value = Path('/path/to/viz.html')
        mock_glob.return_value = [mock_viz_file]
        
        runner = CliRunner()
        with patch('gcphound.cli.Config.from_yaml', return_value=Mock()):
            result = runner.invoke(cli, ['run', '--lazy'])
            
            # Check that open command was called for macOS
            open_call = mock_subprocess.call_args_list[-1]
            assert open_call[0][0] == ['open', '-a', 'Google Chrome', 'file:///path/to/viz.html']
    
    @patch('click.get_current_context')
    @patch('pathlib.Path.glob')
    def test_lazy_mode_no_browser_option(self, mock_glob, mock_ctx):
        """Test lazy mode with --no-open-browser option"""
        # Mock context and command invocations
        mock_context = Mock()
        mock_ctx.return_value = mock_context
        
        # Mock visualization files
        mock_viz_file = Mock()
        mock_viz_file.stat.return_value.st_mtime = 123456
        mock_glob.return_value = [mock_viz_file]
        
        runner = CliRunner()
        with patch('gcphound.cli.Config.from_yaml', return_value=Mock()):
            with patch('webbrowser.open') as mock_browser:
                result = runner.invoke(cli, ['run', '--lazy', '-p', 'test-project', '--no-open-browser'])
                
                # Browser should not be opened
                mock_browser.assert_not_called() 