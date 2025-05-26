"""Tests for the identity collector"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError
from gcphound.collectors.identity import IdentityCollector
from gcphound.utils.auth import AuthManager
from gcphound.utils.config import Config


@pytest.fixture
def auth_manager():
    """Mock auth manager"""
    mock_auth = Mock(spec=AuthManager)
    mock_auth.project_id = 'test-project'
    return mock_auth


@pytest.fixture
def config():
    """Test configuration"""
    return Config({
        'collection': {
            'page_size': 10,
            'collect_groups': True
        }
    })


@pytest.fixture
def collector(auth_manager, config):
    """Create an IdentityCollector instance"""
    return IdentityCollector(auth_manager, config)


class TestIdentityCollector:
    """Test the IdentityCollector class"""
    
    def test_init(self, collector):
        """Test collector initialization"""
        assert collector.__class__.__name__ == "IdentityCollector"
        assert hasattr(collector, '_collected_data')
        assert hasattr(collector, 'auth_manager')
        assert hasattr(collector, 'config')
    
    def test_collect_service_accounts(self, collector):
        """Test service account collection"""
        # Mock IAM service
        mock_service = Mock()
        
        # Mock service accounts response
        mock_sa_response = {
            'accounts': [
                {
                    'name': 'projects/test-project/serviceAccounts/sa1@test-project.iam.gserviceaccount.com',
                    'projectId': 'test-project',
                    'uniqueId': '123456789',
                    'email': 'sa1@test-project.iam.gserviceaccount.com',
                    'displayName': 'Service Account 1',
                    'etag': 'etag1',
                    'description': 'Test service account',
                    'oauth2ClientId': 'client123',
                    'disabled': False
                },
                {
                    'name': 'projects/test-project/serviceAccounts/sa2@test-project.iam.gserviceaccount.com',
                    'projectId': 'test-project',
                    'uniqueId': '987654321',
                    'email': 'sa2@test-project.iam.gserviceaccount.com',
                    'displayName': 'Service Account 2',
                    'etag': 'etag2',
                    'disabled': True
                }
            ]
        }
        
        # Mock keys response
        mock_keys_response = {
            'keys': [
                {
                    'name': 'projects/test-project/serviceAccounts/sa1@test-project.iam.gserviceaccount.com/keys/key1',
                    'validAfterTime': '2023-01-01T00:00:00Z',
                    'validBeforeTime': '2024-01-01T00:00:00Z',
                    'keyAlgorithm': 'KEY_ALG_RSA_2048',
                    'keyOrigin': 'GOOGLE_PROVIDED',
                    'keyType': 'USER_MANAGED'
                }
            ]
        }
        
        # Set up mocks
        list_mock = mock_service.projects().serviceAccounts().list
        list_mock.return_value.execute.return_value = mock_sa_response
        
        keys_list_mock = mock_service.projects().serviceAccounts().keys().list
        keys_list_mock.return_value.execute.return_value = mock_keys_response
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        collector._paginate_list = Mock(return_value=mock_sa_response['accounts'])
        
        # Initialize collected data
        collector._collected_data = {
            'service_accounts': {},
            'users': {},
            'groups': {},
            'external_identities': set()
        }
        
        # Call the method
        collector._collect_service_accounts(['test-project'])
        
        # Verify results
        assert len(collector._collected_data['service_accounts']) == 2
        
        # Check SA1
        sa1_key = 'sa1@test-project.iam.gserviceaccount.com'
        assert sa1_key in collector._collected_data['service_accounts']
        sa1 = collector._collected_data['service_accounts'][sa1_key]
        assert sa1['email'] == 'sa1@test-project.iam.gserviceaccount.com'
        assert sa1['displayName'] == 'Service Account 1'
        assert sa1['disabled'] == False
        assert len(sa1['keys']) == 1
        assert sa1['keys'][0]['keyType'] == 'USER_MANAGED'
        
        # Check SA2
        sa2_key = 'sa2@test-project.iam.gserviceaccount.com'
        assert sa2_key in collector._collected_data['service_accounts']
        sa2 = collector._collected_data['service_accounts'][sa2_key]
        assert sa2['disabled'] == True
        
    def test_collect_groups(self, collector):
        """Test group collection"""
        # Mock Cloud Identity service
        mock_service = Mock()
        
        # Mock groups response
        mock_groups_response = {
            'groups': [
                {
                    'name': 'groups/123456',
                    'groupKey': {'id': 'admins@example.com'},
                    'displayName': 'Admins Group',
                    'description': 'Admin users',
                    'createTime': '2023-01-01T00:00:00Z',
                    'updateTime': '2023-01-02T00:00:00Z',
                    'labels': {'type': 'security'},
                    'parent': 'customers/C12345'
                },
                {
                    'name': 'groups/789012',
                    'groupKey': {'id': 'developers@example.com'},
                    'displayName': 'Developers Group',
                    'description': 'Dev team',
                    'createTime': '2023-01-01T00:00:00Z',
                    'updateTime': '2023-01-02T00:00:00Z',
                    'labels': {},
                    'parent': 'customers/C12345'
                }
            ]
        }
        
        # Mock members response
        mock_members_response = {
            'memberships': [
                {
                    'preferredMemberKey': {'id': 'alice@example.com'},
                    'type': 'USER',
                    'roles': [{'name': 'MEMBER'}],
                    'createTime': '2023-01-01T00:00:00Z',
                    'updateTime': '2023-01-02T00:00:00Z'
                }
            ]
        }
        
        # Set up mocks
        list_mock = mock_service.groups().list
        list_mock.return_value.execute.return_value = mock_groups_response
        
        memberships_list_mock = mock_service.groups().memberships().list
        memberships_list_mock.return_value.execute.return_value = mock_members_response
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        collector._paginate_list = Mock(side_effect=[
            mock_groups_response['groups'],
            mock_members_response['memberships'],
            mock_members_response['memberships']
        ])
        
        # Initialize collected data
        collector._collected_data = {
            'service_accounts': {},
            'groups': {},
            'group_memberships': {},
            'users': {},
            'identity_summary': {
                'by_type': {
                    'users': set(),
                    'service_accounts': set(),
                    'groups': set()
                }
            }
        }
        
        # Call the method
        collector._collect_groups('C12345')
        
        # Verify results
        assert len(collector._collected_data['groups']) == 2
        assert 'admins@example.com' in collector._collected_data['groups']
        assert 'developers@example.com' in collector._collected_data['groups']
        
        # Check group details
        admins_group = collector._collected_data['groups']['admins@example.com']
        assert admins_group['displayName'] == 'Admins Group'
        assert admins_group['description'] == 'Admin users'
        
        # Check group memberships were collected
        assert 'admins@example.com' in collector._collected_data['group_memberships']
        assert len(collector._collected_data['group_memberships']['admins@example.com']) == 1
        

        
    def test_collect_group_members(self, collector):
        """Test group member collection"""
        # Mock Cloud Identity service
        mock_service = Mock()
        
        # Mock members response
        mock_members_response = {
            'memberships': [
                {
                    'preferredMemberKey': {'id': 'alice@example.com'},
                    'type': 'USER',
                    'roles': [{'name': 'MEMBER'}],
                    'createTime': '2023-01-01T00:00:00Z',
                    'updateTime': '2023-01-02T00:00:00Z'
                },
                {
                    'preferredMemberKey': {'id': 'bob@example.com'},
                    'type': 'USER',
                    'roles': [{'name': 'OWNER'}],
                    'createTime': '2023-01-01T00:00:00Z',
                    'updateTime': '2023-01-02T00:00:00Z'
                }
            ]
        }
        
        # Set up mocks
        list_mock = mock_service.groups().memberships().list
        list_mock.return_value.execute.return_value = mock_members_response
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        collector._paginate_list = Mock(return_value=mock_members_response['memberships'])
        
        # Initialize data
        collector._collected_data = {
            'group_memberships': {},
            'users': {}
        }
        
        # Call the method
        collector._collect_group_members('admins@example.com')
        
        # Verify results
        assert 'admins@example.com' in collector._collected_data['group_memberships']
        members = collector._collected_data['group_memberships']['admins@example.com']
        assert len(members) == 2
        assert members[0]['id'] == 'alice@example.com'
        assert members[1]['id'] == 'bob@example.com'
        
        # Check that users were discovered
        assert 'alice@example.com' in collector._collected_data['users']
        assert 'bob@example.com' in collector._collected_data['users']
        
    def test_collect_all_identities(self, collector):
        """Test collecting all identity types"""
        # Mock methods
        collector._collect_service_accounts = Mock()
        collector._collect_groups = Mock()
        collector._build_identity_summary = Mock()
        
        # Call collect
        result = collector.collect(
            project_ids=['test-project'],
            organization_id='C12345',
            collect_groups=True,
            collect_service_accounts=True
        )
        
        # Verify all collectors were called
        collector._collect_service_accounts.assert_called_once_with(['test-project'])
        collector._collect_groups.assert_called_once_with('C12345')
        collector._build_identity_summary.assert_called_once()
        
        # Verify result structure
        assert 'service_accounts' in result
        assert 'groups' in result
        assert 'group_memberships' in result
        assert 'users' in result
        assert 'identity_summary' in result
        
    def test_error_handling_service_accounts(self, collector):
        """Test error handling in service account collection"""
        # Mock service that raises HttpError
        mock_service = Mock()
        mock_error = HttpError(Mock(status=403), b'Access Denied')
        mock_service.projects().serviceAccounts().list().execute.side_effect = mock_error
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        
        # Initialize collected data
        collector._collected_data = {
            'service_accounts': {},
            'users': {},
            'groups': {},
            'external_identities': set()
        }
        
        # Should not raise exception
        collector._collect_service_accounts(['test-project'])
        
        # Data should be empty due to error
        assert collector._collected_data['service_accounts'] == {}
        
    def test_error_handling_group_members(self, collector):
        """Test error handling in group member collection"""
        # Mock service that raises HttpError
        mock_service = Mock()
        mock_error = HttpError(Mock(status=404), b'Group not found')
        mock_service.groups().memberships().list().execute.side_effect = mock_error
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        
        # Initialize data
        collector._collected_data = {
            'group_memberships': {},
            'users': {}
        }
        
        # Should not raise exception
        collector._collect_group_members('admins@example.com')
        
        # Group memberships should be empty due to error
        assert 'admins@example.com' in collector._collected_data['group_memberships']
        assert collector._collected_data['group_memberships']['admins@example.com'] == []
        
    def test_build_identity_summary(self, collector):
        """Test building identity summary"""
        # Initialize collected data
        collector._collected_data = {
            'service_accounts': {
                'sa1@test-project.iam.gserviceaccount.com': {'email': 'sa1@test-project.iam.gserviceaccount.com'},
                'sa2@test-project.iam.gserviceaccount.com': {'email': 'sa2@test-project.iam.gserviceaccount.com'}
            },
            'groups': {
                'admins@example.com': {'groupKey': {'id': 'admins@example.com'}},
                'developers@example.com': {'groupKey': {'id': 'developers@example.com'}}
            },
            'users': {
                'alice@example.com': {'email': 'alice@example.com'},
                'bob@example.com': {'email': 'bob@example.com'}
            },
            'identity_summary': {
                'by_type': {
                    'users': set(),
                    'service_accounts': set(),
                    'groups': set()
                }
            }
        }
        
        # Call the method
        collector._build_identity_summary()
        
        # Verify summary was built correctly
        summary = collector._collected_data['identity_summary']['by_type']
        
        # Check service accounts
        assert len(summary['service_accounts']) == 2
        assert 'serviceAccount:sa1@test-project.iam.gserviceaccount.com' in summary['service_accounts']
        assert 'serviceAccount:sa2@test-project.iam.gserviceaccount.com' in summary['service_accounts']
        
        # Check groups
        assert len(summary['groups']) == 2
        assert 'group:admins@example.com' in summary['groups']
        assert 'group:developers@example.com' in summary['groups']
        
        # Check users
        assert len(summary['users']) == 2
        assert 'user:alice@example.com' in summary['users']
        assert 'user:bob@example.com' in summary['users'] 