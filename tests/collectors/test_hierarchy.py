"""
Tests for hierarchy collector
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from googleapiclient.errors import HttpError

from gcphound.collectors.hierarchy import HierarchyCollector


class TestHierarchyCollector:
    """Test the HierarchyCollector class"""
    
    @pytest.fixture
    def collector(self, mock_auth_manager, mock_config):
        """Create a HierarchyCollector instance for testing"""
        return HierarchyCollector(mock_auth_manager, mock_config)
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock GCP service"""
        service = Mock()
        
        # Create service mocks that will be reused
        org_service = Mock()
        folder_service = Mock()
        project_service = Mock()
        
        # Configure the service to always return the same mock objects
        service.organizations = Mock(return_value=org_service)
        service.folders = Mock(return_value=folder_service)
        service.projects = Mock(return_value=project_service)
        
        return service
    
    def test_collect_specific_projects(self, collector, mock_service):
        """Test collecting specific projects only"""
        collector.auth_manager.build_service.return_value = mock_service
        
        # Mock project responses
        def get_project_side_effect(name):
            project_id = name.split('/')[-1]
            mock_response = Mock()
            mock_response.execute.return_value = {
                'name': name,
                'projectId': project_id,
                'displayName': f'Project {project_id}',
                'state': 'ACTIVE'
            }
            return mock_response
        
        mock_service.projects().get.side_effect = get_project_side_effect
        
        # Collect specific projects
        result = collector.collect(project_ids=['project-1', 'project-2'])
        
        # Verify only specified projects collected
        assert 'project-1' in result['projects']
        assert 'project-2' in result['projects']
        assert len(result['projects']) == 2
        
        # Should not have collected organization or folders
        assert len(result['organizations']) == 0
        assert len(result['folders']) == 0
    
    @patch('gcphound.collectors.base.BaseCollector._execute_request')
    def test_collect_with_folders(self, mock_execute, collector, mock_service):
        """Test collecting specific folders"""
        collector.auth_manager.build_service.return_value = mock_service
        collector.config.collection_include_folders = True
        
        # Create the folder data that will be returned
        folder_data = {
            'name': 'folders/123',
            'displayName': 'Test Folder',
            'parent': 'organizations/456',
            'state': 'ACTIVE',
            'createTime': '2020-01-01T00:00:00Z',
            'updateTime': '2020-01-02T00:00:00Z',
            'etag': 'test-etag'
        }
        
        # Mock _execute_request to return the folder data directly
        mock_execute.return_value = folder_data
        
        # Collect - pass empty project_ids to avoid project discovery
        result = collector.collect(folder_ids=['123'], project_ids=[])
        
        # Verify folder collected
        assert '123' in result['folders']
        assert result['folders']['123']['displayName'] == 'Test Folder'
        assert result['folders']['123']['parent'] == 'organizations/456'
    
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_all_projects(self, mock_paginate, collector, mock_service):
        """Test discovering all accessible projects"""
        collector.auth_manager.build_service.return_value = mock_service
        
        # Mock the paginated results
        projects = [
            {'projectId': 'project-1', 'state': 'ACTIVE', 'name': 'projects/project-1'},
            {'projectId': 'project-2', 'state': 'ACTIVE', 'name': 'projects/project-2'},
            {'projectId': 'project-3', 'state': 'ACTIVE', 'name': 'projects/project-3'},
            {'projectId': 'project-4', 'state': 'DELETE_REQUESTED', 'name': 'projects/project-4'}  # Should be skipped
        ]
        
        # Configure mock_paginate to return the projects
        mock_paginate.return_value = iter(projects)
        
        # Collect all projects
        result = collector.collect()
        
        # Verify active projects collected
        assert 'project-1' in result['projects']
        assert 'project-2' in result['projects']
        assert 'project-3' in result['projects']
        assert 'project-4' not in result['projects']  # Deleted project skipped
    
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_with_max_projects_limit(self, mock_paginate, collector, mock_service):
        """Test project collection with max limit"""
        collector.auth_manager.build_service.return_value = mock_service
        collector.config.collection_max_projects = 2
        
        # Mock many projects
        projects = [
            {'projectId': f'project-{i}', 'state': 'ACTIVE', 'name': f'projects/project-{i}'}
            for i in range(10)
        ]
        
        # Configure mock_paginate to return the projects
        mock_paginate.return_value = iter(projects)
        
        # Collect
        result = collector.collect()
        
        # Should only collect max_projects
        assert len(result['projects']) == 2
    
    @patch('gcphound.collectors.base.BaseCollector._execute_request')
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_handles_permission_errors(self, mock_paginate, mock_execute, collector, mock_service):
        """Test handling permission errors gracefully"""
        collector.auth_manager.build_service.return_value = mock_service
        collector.config.collection_include_folders = False  # Disable folder collection
        
        # Mock 403 error for organization
        mock_resp = Mock(status=403)
        
        def execute_side_effect(request):
            # Check if this is an organization request
            if hasattr(request, 'uri') and 'organizations' in str(request.uri):
                raise HttpError(mock_resp, b'Forbidden')
            # For other requests, return a mock response
            return Mock()
        
        mock_execute.side_effect = execute_side_effect
        
        # Mock successful project list
        projects = [{'projectId': 'project-1', 'state': 'ACTIVE', 'name': 'projects/project-1'}]
        mock_paginate.return_value = iter(projects)
        
        # Collect
        result = collector.collect(organization_id='123456789')
        
        # Should continue despite organization error
        assert 'project-1' in result['projects']
        assert len(collector._metadata['errors']) > 0
        assert '403' in str(collector._metadata['errors'][0])
    
    def test_build_hierarchy_relationships(self, collector, mock_service):
        """Test building parent-child hierarchy relationships"""
        # Prepare test data
        collector._collected_data = {
            'organizations': {
                '123': {'name': 'organizations/123'}
            },
            'folders': {
                '456': {'parent': 'organizations/123'},
                '789': {'parent': 'folders/456'}
            },
            'projects': {
                'project-1': {'parent': 'organizations/123'},
                'project-2': {'parent': 'folders/456'},
                'project-3': {'parent': 'folders/789'}
            },
            'hierarchy': {}
        }
        
        # Build hierarchy
        collector._build_hierarchy()
        
        hierarchy = collector._collected_data['hierarchy']
        
        # Verify organization hierarchy
        assert '456' in hierarchy['organizations']['123']['folders']
        assert 'project-1' in hierarchy['organizations']['123']['projects']
        
        # Verify folder hierarchy
        assert hierarchy['folders']['456']['parent'] == 'organizations/123'
        assert '789' in hierarchy['folders']['456']['folders']
        assert 'project-2' in hierarchy['folders']['456']['projects']
        
        assert hierarchy['folders']['789']['parent'] == 'folders/456'
        assert 'project-3' in hierarchy['folders']['789']['projects']
        
        # Verify project hierarchy
        assert hierarchy['projects']['project-1']['parent'] == 'organizations/123'
        assert hierarchy['projects']['project-2']['parent'] == 'folders/456'
        assert hierarchy['projects']['project-3']['parent'] == 'folders/789'
    
    def test_get_project_ancestors(self, collector):
        """Test getting all ancestors of a project"""
        # Setup hierarchy data
        collector._collected_data = {
            'projects': {
                'project-1': {'parent': 'folders/789'}
            },
            'folders': {
                '789': {'parent': 'folders/456'},
                '456': {'parent': 'organizations/123'}
            },
            'organizations': {
                '123': {}
            }
        }
        
        # Get ancestors
        ancestors = collector.get_project_ancestors('project-1')
        
        # Should return all ancestors in order
        assert ancestors == ['folders/789', 'folders/456', 'organizations/123']
    
    def test_get_project_ancestors_no_parent(self, collector):
        """Test getting ancestors for project with no parent"""
        collector._collected_data = {
            'projects': {
                'orphan-project': {}
            }
        }
        
        ancestors = collector.get_project_ancestors('orphan-project')
        assert ancestors == []
    
    def test_get_project_ancestors_unknown_project(self, collector):
        """Test getting ancestors for unknown project"""
        collector._collected_data = {'projects': {}}
        
        ancestors = collector.get_project_ancestors('unknown-project')
        assert ancestors == []
    
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_all_folders_recursive(self, mock_paginate, collector, mock_service):
        """Test recursive folder collection"""
        collector.auth_manager.build_service.return_value = mock_service
        
        # Initialize the collected data structure
        collector._collected_data = {
            'organizations': {},
            'folders': {},
            'projects': {},
            'hierarchy': {}
        }
        
        # Track which parent is being queried
        call_count = 0
        
        def paginate_side_effect(request, response_field, max_pages):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:  # First call for organizations/123
                return iter([{
                    'name': 'folders/folder1',
                    'displayName': 'Folder 1',
                    'parent': 'organizations/123',
                    'state': 'ACTIVE'
                }])
            elif call_count == 2:  # Second call for folders/folder1
                return iter([{
                    'name': 'folders/folder2',
                    'displayName': 'Folder 2',
                    'parent': 'folders/folder1',
                    'state': 'ACTIVE'
                }])
            else:
                return iter([])
        
        mock_paginate.side_effect = paginate_side_effect
        
        # Collect all folders under org
        collector._collect_all_folders('organizations/123')
        
        # Verify both folders collected
        assert 'folder1' in collector._collected_data['folders']
        assert 'folder2' in collector._collected_data['folders']
        assert collector._collected_data['folders']['folder2']['parent'] == 'folders/folder1'
    
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_handles_api_errors(self, mock_paginate, collector, mock_service):
        """Test handling various API errors"""
        collector.auth_manager.build_service.return_value = mock_service
        
        # Mock 500 error during pagination
        mock_resp = Mock(status=500)
        mock_paginate.side_effect = HttpError(mock_resp, b'Internal Server Error')
        
        # Collect
        result = collector.collect()
        
        # Should handle error gracefully
        assert len(result['projects']) == 0
        assert len(collector._metadata['errors']) > 0
        # Check that the error message contains information about the error
        error_str = str(collector._metadata['errors'][0])
        assert '500' in error_str or 'Error' in error_str or 'HttpError' in error_str
    
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    @patch('gcphound.collectors.hierarchy.ProgressLogger')
    def test_progress_logging(self, mock_progress, mock_paginate, collector, mock_service):
        """Test that progress logging is used"""
        collector.auth_manager.build_service.return_value = mock_service
        
        # Mock project list
        projects = [{'projectId': 'project-1', 'state': 'ACTIVE', 'name': 'projects/project-1'}]
        mock_paginate.return_value = iter(projects)
        
        # Create a mock progress context manager
        mock_progress_instance = Mock()
        mock_progress_instance.__enter__ = Mock(return_value=mock_progress_instance)
        mock_progress_instance.__exit__ = Mock(return_value=None)
        mock_progress_instance.update = Mock()
        mock_progress.return_value = mock_progress_instance
        
        # Collect
        collector.collect()
        
        # Verify progress logger was used
        mock_progress.assert_called()
        mock_progress_instance.update.assert_called()
    
    def test_collect_with_folders_debug(self, collector, mock_service):
        """Debug test for folder collection"""
        collector.auth_manager.build_service.return_value = mock_service
        collector.config.collection_include_folders = True
        
        # Create a proper mock that returns the actual data
        folder_data = {
            'name': 'folders/123',
            'displayName': 'Test Folder',
            'parent': 'organizations/456',
            'state': 'ACTIVE',
            'createTime': '2020-01-01T00:00:00Z',
            'updateTime': '2020-01-02T00:00:00Z',
            'etag': 'test-etag'
        }
        
        # Configure the mock to return the folder data when execute() is called
        mock_request = Mock()
        mock_request.execute = Mock(return_value=folder_data)
        
        # Configure the service mock
        mock_service.folders().get.return_value = mock_request
        
        # Add debugging to see what's happening
        original_execute = collector._execute_request
        def debug_execute(request):
            result = original_execute(request)
            print(f"Execute result type: {type(result)}")
            print(f"Execute result: {result}")
            return result
        collector._execute_request = debug_execute
        
        # Collect - pass empty project_ids to avoid project discovery
        try:
            result = collector.collect(folder_ids=['123'], project_ids=[])
            print("Result:", result)
            print("Folders:", result.get('folders', {}))
            print("Folder 123:", result.get('folders', {}).get('123', {}))
        except Exception as e:
            print("Exception:", e)
            import traceback
            traceback.print_exc()
            raise 