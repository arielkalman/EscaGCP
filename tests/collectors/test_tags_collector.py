"""
Tests for tags collector
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from googleapiclient.errors import HttpError

from gcphound.collectors.tags_collector import TagsCollector
from gcphound.collectors.base import BaseCollector


class TestTagsCollector:
    """Test the TagsCollector class"""
    
    @pytest.fixture
    def collector(self, mock_auth_manager, mock_config):
        """Create a TagsCollector instance for testing"""
        return TagsCollector(mock_auth_manager, mock_config)
    
    def test_paginate_list_basic(self, collector):
        """Test basic pagination functionality"""
        # Create a mock request
        request = Mock()
        request.execute.return_value = {
            'tagKeys': [
                {'name': 'tagKeys/1', 'shortName': 'key1'},
                {'name': 'tagKeys/2', 'shortName': 'key2'}
            ]
        }
        request.list_next = lambda req, resp: None
        
        # Test pagination
        items = list(collector._paginate_list(request, 'tagKeys'))
        
        assert len(items) == 2
        assert items[0]['name'] == 'tagKeys/1'
        assert items[1]['name'] == 'tagKeys/2'
    
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_tag_keys_simple(self, mock_paginate, collector):
        """Test _collect_tag_keys method directly"""
        # Mock the paginate_list to return our tag keys directly
        mock_paginate.return_value = iter([
            {
                'name': 'tagKeys/123456',
                'parent': 'organizations/123456789',
                'shortName': 'environment',
                'description': 'Environment tag',
                'createTime': '2023-01-01T00:00:00Z',
                'updateTime': '2023-01-02T00:00:00Z'
            }
        ])
        
        # Mock build_service
        mock_service = Mock()
        collector.auth_manager.build_service.return_value = mock_service
        
        # Initialize collected data
        collector._collected_data = {
            'tag_keys': {},
            'tag_values': {},
            'tag_bindings': {},
            'tag_holds': {},
            'iam_conditions_with_tags': []
        }
        
        # Call the method
        collector._collect_tag_keys('organizations/123456789')
        
        # Verify
        assert 'tagKeys/123456' in collector._collected_data['tag_keys']
        assert collector._collected_data['tag_keys']['tagKeys/123456']['shortName'] == 'environment'
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock Resource Manager service"""
        service = Mock()
        
        # Create service resource mocks
        tag_keys_resource = Mock()
        tag_values_resource = Mock()
        tag_bindings_resource = Mock()
        
        # Configure the service to return the resource mocks
        service.tagKeys.return_value = tag_keys_resource
        service.tagValues.return_value = tag_values_resource
        service.tagBindings.return_value = tag_bindings_resource
        
        return service
    
    @patch('gcphound.collectors.tags_collector.TagsCollector._collect_tag_values')
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    @patch('gcphound.collectors.tags_collector.TagsCollector._analyze_tag_usage_in_conditions')
    def test_collect_with_organization(self, mock_analyze, mock_paginate, mock_collect_tag_values, collector):
        """Test collecting tags for an organization"""
        # Mock build_service
        mock_service = Mock()
        collector.auth_manager.build_service.return_value = mock_service
        
        # Mock paginate_list to return tag keys
        tag_keys = [
            {
                'name': 'tagKeys/123456',
                'parent': 'organizations/123456789',
                'shortName': 'environment',
                'description': 'Environment tag',
                'createTime': '2023-01-01T00:00:00Z',
                'updateTime': '2023-01-02T00:00:00Z'
            }
        ]
        mock_paginate.return_value = iter(tag_keys)
        
        # Mock _collect_tag_values to populate tag values
        def mock_collect_values(tag_key):
            if tag_key == 'tagKeys/123456':
                collector._collected_data['tag_values']['tagValues/789012'] = {
                    'name': 'tagValues/789012',
                    'parent': 'tagKeys/123456',
                    'shortName': 'production',
                    'description': 'Production environment',
                    'createTime': '2023-01-01T00:00:00Z'
                }
        mock_collect_tag_values.side_effect = mock_collect_values
        
        # Collect
        result = collector.collect(organization_id='123456789')
        
        # Verify tag keys collected
        assert 'tagKeys/123456' in result['tag_keys']
        assert result['tag_keys']['tagKeys/123456']['shortName'] == 'environment'
        assert result['tag_keys']['tagKeys/123456']['parent'] == 'organizations/123456789'
        
        # Verify tag values collected
        assert 'tagValues/789012' in result['tag_values']
        assert result['tag_values']['tagValues/789012']['shortName'] == 'production'
        assert result['tag_values']['tagValues/789012']['parent'] == 'tagKeys/123456'
    
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_tag_bindings_for_projects(self, mock_paginate, collector, mock_service):
        """Test collecting tag bindings for projects"""
        collector.auth_manager.build_service.return_value = mock_service
        
        # Mock tag bindings
        tag_bindings = [
            {
                'name': 'tagBindings/binding1',
                'parent': '//cloudresourcemanager.googleapis.com/projects/test-project',
                'tagValue': 'tagValues/789012',
                'tagValueNamespacedName': '123456789/environment/production'
            }
        ]
        
        mock_paginate.return_value = iter(tag_bindings)
        
        # Collect bindings for a project
        collector._collected_data = {
            'tag_keys': {},
            'tag_values': {},
            'tag_bindings': {},
            'tag_usage_analysis': {}
        }
        
        collector._collect_tag_bindings('//cloudresourcemanager.googleapis.com/projects/test-project')
        
        # Verify bindings collected
        assert 'tagBindings/binding1' in collector._collected_data['tag_bindings']
        binding = collector._collected_data['tag_bindings']['tagBindings/binding1']
        assert binding['parent'] == '//cloudresourcemanager.googleapis.com/projects/test-project'
        assert binding['tagValue'] == 'tagValues/789012'
    
    def test_analyze_tag_usage_in_conditions(self, collector):
        """Test analyzing tag usage in IAM conditions"""
        # Setup test data with tag values and bindings
        collector._collected_data = {
            'tag_keys': {
                'tagKeys/123456': {'shortName': 'environment'}
            },
            'tag_values': {
                'tagValues/789012': {'shortName': 'production', 'parent': 'tagKeys/123456'},
                'tagValues/789013': {'shortName': 'staging', 'parent': 'tagKeys/123456'}
            },
            'tag_bindings': {
                'binding1': {
                    'tagValue': 'tagValues/789012',
                    'parent': '//cloudresourcemanager.googleapis.com/projects/test-project'
                }
            },
            'tag_usage_analysis': {}
        }
        
        # Call the analyze method
        collector._analyze_tag_usage_in_conditions()
        
        # Verify that tags with bindings are marked as potentially used
        assert collector._collected_data['tag_values']['tagValues/789012'].get('hasBindings') is True
        assert collector._collected_data['tag_values']['tagValues/789012'].get('potentiallyUsedInConditions') is True
        
        # Verify that tags without bindings are not marked
        assert collector._collected_data['tag_values']['tagValues/789013'].get('hasBindings') is None
        assert collector._collected_data['tag_values']['tagValues/789013'].get('potentiallyUsedInConditions') is None
    
    def test_get_tags_for_resource(self, collector):
        """Test getting tags for a specific resource"""
        # Setup test data
        collector._collected_data = {
            'tag_bindings': {
                'binding1': {
                    'parent': '//cloudresourcemanager.googleapis.com/projects/test-project',
                    'tagValue': 'tagValues/789012',
                    'tagValueNamespacedName': '123456789/environment/production',
                    'resource': '//cloudresourcemanager.googleapis.com/projects/test-project'
                },
                'binding2': {
                    'parent': '//cloudresourcemanager.googleapis.com/projects/test-project',
                    'tagValue': 'tagValues/789013',
                    'tagValueNamespacedName': '123456789/team/backend',
                    'resource': '//cloudresourcemanager.googleapis.com/projects/test-project'
                },
                'binding3': {
                    'parent': '//cloudresourcemanager.googleapis.com/projects/other-project',
                    'tagValue': 'tagValues/789014',
                    'tagValueNamespacedName': '123456789/environment/staging',
                    'resource': '//cloudresourcemanager.googleapis.com/projects/other-project'
                }
            }
        }
        
        # Get tags for test-project
        tags = collector.get_tags_for_resource('//cloudresourcemanager.googleapis.com/projects/test-project')
        
        # Verify results
        assert len(tags) == 2
        tag_values = [tag['tagValue'] for tag in tags]
        assert 'tagValues/789012' in tag_values
        assert 'tagValues/789013' in tag_values
        assert 'tagValues/789014' not in tag_values
    
    def test_get_resources_with_tag(self, collector):
        """Test getting resources that have a specific tag"""
        # Setup test data
        collector._collected_data = {
            'tag_bindings': {
                'binding1': {
                    'parent': '//cloudresourcemanager.googleapis.com/projects/project1',
                    'tagValue': 'tagValues/789012',
                    'resource': '//cloudresourcemanager.googleapis.com/projects/project1'
                },
                'binding2': {
                    'parent': '//cloudresourcemanager.googleapis.com/projects/project2',
                    'tagValue': 'tagValues/789012',
                    'resource': '//cloudresourcemanager.googleapis.com/projects/project2'
                },
                'binding3': {
                    'parent': '//cloudresourcemanager.googleapis.com/projects/project3',
                    'tagValue': 'tagValues/789013',
                    'resource': '//cloudresourcemanager.googleapis.com/projects/project3'
                }
            }
        }
        
        # Get resources with tag
        resources = collector.get_resources_with_tag('tagValues/789012')
        
        # Verify results
        assert len(resources) == 2
        assert '//cloudresourcemanager.googleapis.com/projects/project1' in resources
        assert '//cloudresourcemanager.googleapis.com/projects/project2' in resources
        assert '//cloudresourcemanager.googleapis.com/projects/project3' not in resources
    
    def test_collect_handles_permission_errors(self, collector, mock_service):
        """Test handling permission errors gracefully"""
        collector.auth_manager.build_service.return_value = mock_service
        
        # Mock 403 error
        mock_resp = Mock(status=403)
        mock_service.tagKeys().list.return_value.execute.side_effect = HttpError(
            mock_resp, b'Permission denied'
        )
        
        # Collect
        result = collector.collect(organization_id='123456789')
        
        # Should handle error gracefully
        assert len(result['tag_keys']) == 0
        assert len(collector._metadata['errors']) > 0
    
    @patch('gcphound.collectors.tags_collector.TagsCollector._collect_tag_values')
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_with_pagination(self, mock_paginate, mock_collect_tag_values, collector, mock_service):
        """Test collecting with pagination"""
        collector.auth_manager.build_service.return_value = mock_service
        
        # Mock paginated tag keys
        tag_keys = [
            {
                'name': f'tagKeys/{i}',
                'parent': 'organizations/123456789',
                'shortName': f'tag{i}'
            }
            for i in range(25)
        ]
        
        mock_paginate.return_value = iter(tag_keys)
        
        # Mock _collect_tag_values to do nothing
        mock_collect_tag_values.return_value = None
        
        # Initialize collected data
        collector._collected_data = {
            'tag_keys': {},
            'tag_values': {},
            'tag_bindings': {},
            'tag_usage_analysis': {}
        }
        
        # Collect tag keys
        collector._collect_tag_keys('organizations/123456789')
        
        # Verify all collected
        assert len(collector._collected_data['tag_keys']) == 25
        assert 'tagKeys/0' in collector._collected_data['tag_keys']
        assert 'tagKeys/24' in collector._collected_data['tag_keys']
    
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_empty_collection(self, mock_paginate, collector):
        """Test collection when no tags exist"""
        # Mock build_service
        mock_service = Mock()
        collector.auth_manager.build_service.return_value = mock_service
        
        # Mock paginate_list to return empty iterators
        mock_paginate.return_value = iter([])
        
        # Collect
        result = collector.collect(organization_id='123456789')
        
        # Verify empty but valid structure
        assert result['tag_keys'] == {}
        assert result['tag_values'] == {}
        assert result['tag_bindings'] == {}
        assert 'tag_holds' in result
        assert 'iam_conditions_with_tags' in result 