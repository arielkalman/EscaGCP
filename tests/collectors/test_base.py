"""
Tests for base collector
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError

from escagcp.collectors.base import BaseCollector
from escagcp.utils import AuthManager, Config


class ConcreteCollector(BaseCollector):
    """Concrete implementation for testing"""
    
    def collect(self, **kwargs):
        self._start_collection()
        self._collected_data = {"test": "data"}
        self._increment_stat('items_collected', 5)
        self._end_collection()
        return self.get_collected_data()


class TestBaseCollector:
    """Test the BaseCollector abstract class"""
    
    @pytest.fixture
    def collector(self, mock_auth_manager, mock_config):
        """Create a concrete collector instance for testing"""
        return ConcreteCollector(mock_auth_manager, mock_config)
    
    def test_initialization(self, mock_auth_manager, mock_config):
        """Test BaseCollector initialization"""
        collector = ConcreteCollector(mock_auth_manager, mock_config)
        
        assert collector.auth_manager == mock_auth_manager
        assert collector.config == mock_config
        assert collector.rate_limiter is not None
        assert collector._collected_data == {}
        assert collector._metadata['collector'] == 'ConcreteCollector'
        assert collector._metadata['start_time'] is None
        assert collector._metadata['end_time'] is None
        assert collector._metadata['errors'] == []
        assert collector._metadata['stats'] == {}
    
    def test_abstract_collect_method(self, mock_auth_manager, mock_config):
        """Test that BaseCollector.collect is abstract"""
        with pytest.raises(TypeError):
            # Cannot instantiate abstract class
            BaseCollector(mock_auth_manager, mock_config)
    
    def test_save_to_file(self, collector, temp_dir):
        """Test saving collected data to file"""
        # Collect some data
        collector.collect()
        
        # Save to file
        output_file = collector.save_to_file(str(temp_dir))
        
        # Verify file exists
        assert Path(output_file).exists()
        
        # Verify content
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        assert 'metadata' in saved_data
        assert 'data' in saved_data
        assert saved_data['data'] == {"test": "data"}
        assert saved_data['metadata']['collector'] == 'ConcreteCollector'
    
    def test_save_to_file_custom_filename(self, collector, temp_dir):
        """Test saving with custom filename"""
        collector.collect()
        
        output_file = collector.save_to_file(str(temp_dir), "custom_name.json")
        
        assert output_file == str(temp_dir / "custom_name.json")
        assert Path(output_file).exists()
    
    def test_save_to_file_creates_directory(self, collector, temp_dir):
        """Test that save_to_file creates output directory if needed"""
        collector.collect()
        
        # Use non-existent subdirectory
        output_dir = temp_dir / "subdir" / "another"
        output_file = collector.save_to_file(str(output_dir))
        
        assert Path(output_file).exists()
        assert output_dir.exists()
    
    def test_paginate_list_single_page(self, collector):
        """Test pagination with single page of results"""
        # Mock request and response
        mock_request = Mock()
        mock_request.execute.return_value = {
            'items': [{'id': 1}, {'id': 2}, {'id': 3}],
            'nextPageToken': None
        }
        mock_request.list_next.return_value = None
        
        # Collect items
        items = list(collector._paginate_list(mock_request, 'items'))
        
        assert len(items) == 3
        assert items[0]['id'] == 1
        assert items[2]['id'] == 3
    
    def test_paginate_list_multiple_pages(self, collector):
        """Test pagination with multiple pages"""
        # Mock requests for multiple pages
        mock_request1 = Mock()
        mock_request2 = Mock()
        mock_request3 = Mock()
        
        mock_request1.execute.return_value = {
            'items': [{'id': 1}, {'id': 2}],
            'nextPageToken': 'token1'
        }
        mock_request2.execute.return_value = {
            'items': [{'id': 3}, {'id': 4}],
            'nextPageToken': 'token2'
        }
        mock_request3.execute.return_value = {
            'items': [{'id': 5}],
            'nextPageToken': None
        }
        
        mock_request1.list_next.return_value = mock_request2
        mock_request2.list_next.return_value = mock_request3
        mock_request3.list_next.return_value = None
        
        # Collect all items
        items = list(collector._paginate_list(mock_request1, 'items'))
        
        assert len(items) == 5
        assert [item['id'] for item in items] == [1, 2, 3, 4, 5]
    
    def test_paginate_list_max_pages(self, collector):
        """Test pagination with max_pages limit"""
        # Mock endless pagination
        mock_request = Mock()
        mock_request.execute.return_value = {
            'items': [{'id': i} for i in range(10)],
            'nextPageToken': 'token'
        }
        mock_request.list_next.return_value = mock_request  # Always returns itself
        
        # Collect with max_pages=3
        items = list(collector._paginate_list(mock_request, 'items', max_pages=3))
        
        # Should have 3 pages * 10 items = 30 items
        assert len(items) == 30
    
    def test_paginate_list_with_error(self, collector):
        """Test pagination handling errors"""
        mock_request = Mock()
        mock_resp = Mock(status=500)
        mock_request.execute.side_effect = HttpError(mock_resp, b'Server Error')
        
        # Should handle error and return empty
        items = list(collector._paginate_list(mock_request, 'items'))
        
        assert len(items) == 0
        assert len(collector._metadata['errors']) == 1
        assert 'Server Error' in str(collector._metadata['errors'][0]['error'])
    
    def test_execute_request_success(self, collector):
        """Test successful request execution"""
        mock_request = Mock()
        mock_request.execute.return_value = {'result': 'success'}
        
        result = collector._execute_request(mock_request)
        
        assert result == {'result': 'success'}
        mock_request.execute.assert_called_once()
    
    @patch('escagcp.collectors.base.retry_with_backoff')
    def test_execute_request_with_retry(self, mock_retry, collector):
        """Test request execution uses retry decorator"""
        # Mock the decorator to return the original function
        mock_retry.return_value = lambda func: func
        
        mock_request = Mock()
        mock_request.execute.return_value = {'result': 'success'}
        
        result = collector._execute_request(mock_request)
        
        assert result == {'result': 'success'}
        mock_retry.assert_called_once_with(max_retries=3)
    
    def test_start_collection(self, collector):
        """Test _start_collection sets metadata"""
        collector._start_collection()
        
        assert collector._metadata['start_time'] is not None
        # Should be ISO format timestamp
        datetime.fromisoformat(collector._metadata['start_time'])
    
    def test_end_collection(self, collector):
        """Test _end_collection sets metadata and calculates duration"""
        collector._start_collection()
        collector._end_collection()
        
        assert collector._metadata['end_time'] is not None
        assert 'duration_seconds' in collector._metadata
        assert collector._metadata['duration_seconds'] >= 0
    
    def test_update_stats(self, collector):
        """Test updating collection statistics"""
        collector._update_stats('test_stat', 42)
        collector._update_stats('another_stat', 'value')
        
        assert collector._metadata['stats']['test_stat'] == 42
        assert collector._metadata['stats']['another_stat'] == 'value'
    
    def test_increment_stat(self, collector):
        """Test incrementing statistics"""
        # First increment
        collector._increment_stat('counter')
        assert collector._metadata['stats']['counter'] == 1
        
        # Second increment
        collector._increment_stat('counter')
        assert collector._metadata['stats']['counter'] == 2
        
        # Increment by custom amount
        collector._increment_stat('counter', 5)
        assert collector._metadata['stats']['counter'] == 7
    
    def test_get_metadata(self, collector):
        """Test getting metadata returns a copy"""
        collector._metadata['test'] = 'value'
        
        metadata = collector.get_metadata()
        
        # Should be a copy
        metadata['test'] = 'modified'
        assert collector._metadata['test'] == 'value'
    
    def test_get_collected_data(self, collector):
        """Test getting collected data returns a copy"""
        collector._collected_data['test'] = 'value'
        
        data = collector.get_collected_data()
        
        # Should be a copy
        data['test'] = 'modified'
        assert collector._collected_data['test'] == 'value'
    
    def test_normalize_identity_user(self, collector):
        """Test normalizing user identities"""
        assert collector._normalize_identity('user:alice@example.com') == 'user:alice@example.com'
        assert collector._normalize_identity('alice@example.com') == 'user:alice@example.com'
    
    def test_normalize_identity_service_account(self, collector):
        """Test normalizing service account identities"""
        sa_email = 'sa@project.iam.gserviceaccount.com'
        assert collector._normalize_identity(f'serviceAccount:{sa_email}') == f'serviceAccount:{sa_email}'
        assert collector._normalize_identity(sa_email) == f'serviceAccount:{sa_email}'
    
    def test_normalize_identity_group(self, collector):
        """Test normalizing group identities"""
        assert collector._normalize_identity('group:admins@example.com') == 'group:admins@example.com'
        # Groups without prefix but with group: prefix stay as-is
        assert collector._normalize_identity('group:admins') == 'group:admins'
    
    def test_normalize_identity_special(self, collector):
        """Test normalizing special identities"""
        assert collector._normalize_identity('allUsers') == 'allUsers'
        assert collector._normalize_identity('allAuthenticatedUsers') == 'allAuthenticatedUsers'
    
    def test_extract_project_id_from_resource_name(self, collector):
        """Test extracting project ID from resource names"""
        # Standard resource name
        assert collector._extract_project_id('projects/my-project/buckets/my-bucket') == 'my-project'
        
        # Nested resource
        assert collector._extract_project_id('projects/test-123/zones/us-central1-a/instances/vm1') == 'test-123'
        
        # No project in name
        assert collector._extract_project_id('organizations/123456/folders/789') is None
        
        # Invalid format
        assert collector._extract_project_id('invalid-resource-name') is None
    
    def test_rate_limiter_integration(self, collector):
        """Test that rate limiter is used during pagination"""
        mock_request = Mock()
        mock_request.execute.return_value = {'items': [{'id': 1}]}
        mock_request.list_next.return_value = None
        
        # Check initial tokens
        initial_tokens = collector.rate_limiter.tokens
        
        # Make request
        list(collector._paginate_list(mock_request, 'items'))
        
        # Token should be consumed
        assert collector.rate_limiter.tokens < initial_tokens
    
    def test_collection_workflow(self, collector):
        """Test complete collection workflow"""
        # Run collection
        data = collector.collect()
        
        # Check metadata is properly set
        metadata = collector.get_metadata()
        assert metadata['start_time'] is not None
        assert metadata['end_time'] is not None
        assert metadata['duration_seconds'] >= 0
        assert metadata['stats']['items_collected'] == 5
        
        # Check data
        assert data == {"test": "data"} 