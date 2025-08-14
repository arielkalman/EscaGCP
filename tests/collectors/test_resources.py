"""Tests for the resources collector"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError
from escagcp.collectors.resources import ResourceCollector
from escagcp.utils.auth import AuthManager
from escagcp.utils.config import Config


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
            'resource_types': ['buckets', 'compute_instances', 'functions', 'secrets', 'kms_keys'],
            'page_size': 10
        }
    })


@pytest.fixture
def collector(auth_manager, config):
    """Create a ResourceCollector instance"""
    return ResourceCollector(auth_manager, config)


class TestResourceCollector:
    """Test the ResourceCollector class"""
    
    def test_init(self, collector):
        """Test collector initialization"""
        assert collector.__class__.__name__ == "ResourceCollector"
        assert hasattr(collector, '_collected_data')
        assert hasattr(collector, 'auth_manager')
        assert hasattr(collector, 'config')
    
    def test_collect_buckets(self, collector):
        """Test bucket collection"""
        # Mock storage service
        mock_service = Mock()
        mock_buckets = Mock()
        
        # Mock bucket list response
        mock_response = {
            'items': [
                {
                    'name': 'test-bucket-1',
                    'id': 'bucket-id-1',
                    'projectNumber': '123456',
                    'location': 'us-central1',
                    'storageClass': 'STANDARD',
                    'timeCreated': '2023-01-01T00:00:00Z',
                    'updated': '2023-01-02T00:00:00Z',
                    'labels': {'env': 'test'},
                    'iamConfiguration': {'uniformBucketLevelAccess': {'enabled': False}},
                    'lifecycle': None,
                    'versioning': {'enabled': True},
                    'encryption': None
                },
                {
                    'name': 'test-bucket-2',
                    'id': 'bucket-id-2',
                    'projectNumber': '123456',
                    'location': 'us-east1',
                    'storageClass': 'NEARLINE',
                    'timeCreated': '2023-01-01T00:00:00Z',
                    'updated': '2023-01-02T00:00:00Z',
                    'labels': {},
                    'iamConfiguration': {'uniformBucketLevelAccess': {'enabled': True}},
                    'lifecycle': None,
                    'versioning': None,
                    'encryption': None
                }
            ]
        }
        
        # Mock IAM policy response
        mock_iam_policy = {
            'bindings': [
                {
                    'role': 'roles/storage.admin',
                    'members': ['user:admin@example.com']
                }
            ],
            'etag': 'etag123',
            'version': 1
        }
        
        # Set up mocks
        mock_buckets.list.return_value.execute.return_value = mock_response
        mock_buckets.getIamPolicy.return_value.execute.return_value = mock_iam_policy
        mock_service.buckets.return_value = mock_buckets
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        collector._paginate_list = Mock(return_value=mock_response['items'])
        
        # Initialize collected data structure
        collector._collected_data = {
            'resources': {
                'buckets': {},
                'compute_instances': {},
                'functions': {},
                'pubsub_topics': {},
                'bigquery_datasets': {},
                'kms_keys': {},
                'secrets': {}
            },
            'resource_iam_policies': {},
            'resource_summary': {
                'by_type': {},
                'by_project': {}
            }
        }
        
        # Call the method
        collector._collect_buckets(['test-project'])
        
        # Verify results
        assert len(collector._collected_data['resources']['buckets']) == 2
        assert 'test-bucket-1' in collector._collected_data['resources']['buckets']
        assert collector._collected_data['resources']['buckets']['test-bucket-1']['name'] == 'test-bucket-1'
        assert collector._collected_data['resources']['buckets']['test-bucket-1']['location'] == 'us-central1'
        
        # Check IAM policies were collected
        assert 'storage.googleapis.com/buckets/test-bucket-1' in collector._collected_data['resource_iam_policies']
        
    def test_collect_compute_instances(self, collector):
        """Test compute instance collection"""
        # Mock compute service
        mock_service = Mock()
        mock_zones = Mock()
        mock_instances = Mock()
        
        # Mock zones response
        mock_zones_response = {
            'items': [
                {'name': 'us-central1-a'},
                {'name': 'us-east1-b'}
            ]
        }
        
        # Mock instances response
        mock_instances_response = {
            'items': [
                {
                    'name': 'instance-1',
                    'id': '123456789',
                    'machineType': 'zones/us-central1-a/machineTypes/n1-standard-1',
                    'status': 'RUNNING',
                    'creationTimestamp': '2023-01-01T00:00:00Z',
                    'labels': {'app': 'web'},
                    'serviceAccounts': [
                        {
                            'email': 'sa1@test-project.iam.gserviceaccount.com',
                            'scopes': ['https://www.googleapis.com/auth/cloud-platform']
                        }
                    ],
                    'networkInterfaces': [],
                    'disks': [],
                    'metadata': {
                        'items': [
                            {'key': 'enable-oslogin', 'value': 'TRUE'}
                        ]
                    },
                    'tags': {'items': ['web', 'prod']}
                }
            ]
        }
        
        # Set up mocks
        mock_zones.list.return_value.execute.return_value = mock_zones_response
        mock_instances.list.return_value.execute.return_value = mock_instances_response
        mock_service.zones.return_value = mock_zones
        mock_service.instances.return_value = mock_instances
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        collector._paginate_list = Mock(side_effect=[
            mock_zones_response['items'],  # For zones
            mock_instances_response['items']  # For instances
        ])
        
        # Initialize collected data
        collector._collected_data = {
            'resources': {
                'buckets': {},
                'compute_instances': {},
                'functions': {},
                'pubsub_topics': {},
                'bigquery_datasets': {},
                'kms_keys': {},
                'secrets': {}
            },
            'resource_iam_policies': {},
            'resource_summary': {
                'by_type': {},
                'by_project': {}
            }
        }
        
        # Call the method
        collector._collect_compute_instances(['test-project'])
        
        # Verify results
        assert len(collector._collected_data['resources']['compute_instances']) == 1
        instance_key = 'test-project/us-central1-a/instance-1'
        assert instance_key in collector._collected_data['resources']['compute_instances']
        instance = collector._collected_data['resources']['compute_instances'][instance_key]
        assert instance['name'] == 'instance-1'
        assert instance['status'] == 'RUNNING'
        assert len(instance['serviceAccounts']) == 1
        
    def test_collect_cloud_functions(self, collector):
        """Test Cloud Functions collection"""
        # Mock functions service
        mock_service = Mock()
        
        # Mock functions response
        mock_functions_response = {
            'functions': [
                {
                    'name': 'projects/test-project/locations/us-central1/functions/function-1',
                    'description': 'Test function',
                    'entryPoint': 'main',
                    'runtime': 'python39',
                    'timeout': '60s',
                    'availableMemoryMb': 256,
                    'serviceAccountEmail': 'sa-function@test-project.iam.gserviceaccount.com',
                    'updateTime': '2023-01-01T00:00:00Z',
                    'versionId': '1',
                    'labels': {'env': 'prod'},
                    'environmentVariables': {'API_KEY': 'hidden'},
                    'httpsTrigger': {'url': 'https://function-url'},
                    'eventTrigger': None,
                    'status': 'ACTIVE'
                }
            ]
        }
        
        # Mock IAM policy
        mock_iam_policy = {
            'bindings': [
                {
                    'role': 'roles/cloudfunctions.invoker',
                    'members': ['allUsers']
                }
            ],
            'etag': 'etag123',
            'version': 1
        }
        
        # Set up mocks
        list_mock = mock_service.projects().locations().functions().list
        list_mock.return_value.execute.return_value = mock_functions_response
        
        getIamPolicy_mock = mock_service.projects().locations().functions().getIamPolicy
        getIamPolicy_mock.return_value.execute.return_value = mock_iam_policy
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        collector._paginate_list = Mock(return_value=mock_functions_response['functions'])
        
        # Initialize collected data
        collector._collected_data = {
            'resources': {
                'buckets': {},
                'compute_instances': {},
                'functions': {},
                'pubsub_topics': {},
                'bigquery_datasets': {},
                'kms_keys': {},
                'secrets': {}
            },
            'resource_iam_policies': {},
            'resource_summary': {
                'by_type': {},
                'by_project': {}
            }
        }
        
        # Call the method
        collector._collect_cloud_functions(['test-project'])
        
        # Verify results
        assert len(collector._collected_data['resources']['functions']) == 1
        func_key = 'projects/test-project/locations/us-central1/functions/function-1'
        assert func_key in collector._collected_data['resources']['functions']
        func = collector._collected_data['resources']['functions'][func_key]
        assert func['runtime'] == 'python39'
        assert func['serviceAccountEmail'] == 'sa-function@test-project.iam.gserviceaccount.com'
        
    def test_collect_secrets(self, collector):
        """Test Secret Manager secrets collection"""
        # Mock secrets service
        mock_service = Mock()
        
        # Mock secrets response
        mock_secrets_response = {
            'secrets': [
                {
                    'name': 'projects/test-project/secrets/api-key',
                    'createTime': '2023-01-01T00:00:00Z',
                    'labels': {'type': 'api'},
                    'replication': {
                        'automatic': {}
                    }
                },
                {
                    'name': 'projects/test-project/secrets/db-password',
                    'createTime': '2023-01-02T00:00:00Z',
                    'labels': {},
                    'replication': {
                        'userManaged': {
                            'replicas': [
                                {'location': 'us-central1'},
                                {'location': 'us-east1'}
                            ]
                        }
                    }
                }
            ]
        }
        
        # Mock IAM policy
        mock_iam_policy = {
            'bindings': [
                {
                    'role': 'roles/secretmanager.secretAccessor',
                    'members': ['serviceAccount:app@test-project.iam.gserviceaccount.com']
                }
            ],
            'etag': 'etag123',
            'version': 1
        }
        
        # Set up mocks
        list_mock = mock_service.projects().secrets().list
        list_mock.return_value.execute.return_value = mock_secrets_response
        
        getIamPolicy_mock = mock_service.projects().secrets().getIamPolicy
        getIamPolicy_mock.return_value.execute.return_value = mock_iam_policy
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        collector._paginate_list = Mock(return_value=mock_secrets_response['secrets'])
        
        # Initialize collected data
        collector._collected_data = {
            'resources': {
                'buckets': {},
                'compute_instances': {},
                'functions': {},
                'pubsub_topics': {},
                'bigquery_datasets': {},
                'kms_keys': {},
                'secrets': {}
            },
            'resource_iam_policies': {},
            'resource_summary': {
                'by_type': {},
                'by_project': {}
            }
        }
        
        # Call the method
        collector._collect_secrets(['test-project'])
        
        # Verify results
        assert len(collector._collected_data['resources']['secrets']) == 2
        
        secret1_key = 'projects/test-project/secrets/api-key'
        assert secret1_key in collector._collected_data['resources']['secrets']
        secret1 = collector._collected_data['resources']['secrets'][secret1_key]
        assert secret1['name'] == 'projects/test-project/secrets/api-key'
        
    def test_collect_kms_keys(self, collector):
        """Test KMS keys collection"""
        # Mock KMS service
        mock_service = Mock()
        
        # Mock keyrings response
        mock_keyrings_response = {
            'keyRings': [
                {'name': 'projects/test-project/locations/us-central1/keyRings/keyring-1'}
            ]
        }
        
        # Mock keys response
        mock_keys_response = {
            'cryptoKeys': [
                {
                    'name': 'projects/test-project/locations/us-central1/keyRings/keyring-1/cryptoKeys/key-1',
                    'purpose': 'ENCRYPT_DECRYPT',
                    'createTime': '2023-01-01T00:00:00Z',
                    'nextRotationTime': '2024-01-01T00:00:00Z',
                    'rotationPeriod': '7776000s',
                    'versionTemplate': {'algorithm': 'GOOGLE_SYMMETRIC_ENCRYPTION'},
                    'labels': {'env': 'prod'},
                    'importOnly': False
                }
            ]
        }
        
        # Mock IAM policy
        mock_iam_policy = {
            'bindings': [
                {
                    'role': 'roles/cloudkms.cryptoKeyEncrypterDecrypter',
                    'members': ['serviceAccount:app@test-project.iam.gserviceaccount.com']
                }
            ],
            'etag': 'etag123',
            'version': 1
        }
        
        # Set up mocks
        keyRings_list_mock = mock_service.projects().locations().keyRings().list
        keyRings_list_mock.return_value.execute.return_value = mock_keyrings_response
        
        cryptoKeys_list_mock = mock_service.projects().locations().keyRings().cryptoKeys().list
        cryptoKeys_list_mock.return_value.execute.return_value = mock_keys_response
        
        getIamPolicy_mock = mock_service.projects().locations().keyRings().cryptoKeys().getIamPolicy
        getIamPolicy_mock.return_value.execute.return_value = mock_iam_policy
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        collector._paginate_list = Mock(side_effect=[
            mock_keyrings_response['keyRings'],
            mock_keys_response['cryptoKeys']
        ])
        
        # Initialize collected data
        collector._collected_data = {
            'resources': {
                'buckets': {},
                'compute_instances': {},
                'functions': {},
                'pubsub_topics': {},
                'bigquery_datasets': {},
                'kms_keys': {},
                'secrets': {}
            },
            'resource_iam_policies': {},
            'resource_summary': {
                'by_type': {},
                'by_project': {}
            }
        }
        
        # Call the method
        collector._collect_kms_keys(['test-project'])
        
        # Verify results
        assert len(collector._collected_data['resources']['kms_keys']) == 1
        
        key1_key = 'projects/test-project/locations/us-central1/keyRings/keyring-1/cryptoKeys/key-1'
        assert key1_key in collector._collected_data['resources']['kms_keys']
        key1 = collector._collected_data['resources']['kms_keys'][key1_key]
        assert key1['purpose'] == 'ENCRYPT_DECRYPT'
        
    def test_collect_all_resources(self, collector):
        """Test collecting all resource types"""
        # Mock all collection methods
        collector._collect_buckets = Mock()
        collector._collect_compute_instances = Mock()
        collector._collect_cloud_functions = Mock()
        collector._collect_secrets = Mock()
        collector._collect_kms_keys = Mock()
        collector._collect_pubsub_topics = Mock()
        collector._collect_bigquery_datasets = Mock()
        collector._build_resource_summary = Mock()
        
        # Call collect with specific resource types
        result = collector.collect(
            project_ids=['test-project'],
            resource_types=['buckets', 'compute_instances', 'functions', 'secrets', 'kms_keys']
        )
        
        # Verify collectors were called
        collector._collect_buckets.assert_called_once_with(['test-project'])
        collector._collect_compute_instances.assert_called_once_with(['test-project'])
        collector._collect_cloud_functions.assert_called_once_with(['test-project'])
        collector._collect_secrets.assert_called_once_with(['test-project'])
        collector._collect_kms_keys.assert_called_once_with(['test-project'])
        
        # Verify collectors not in resource_types were not called
        collector._collect_pubsub_topics.assert_not_called()
        collector._collect_bigquery_datasets.assert_not_called()
        
        # Verify summary was built
        collector._build_resource_summary.assert_called_once()
        
    def test_error_handling_in_collectors(self, collector):
        """Test error handling in individual collectors"""
        # Mock service that raises HttpError
        mock_service = Mock()
        mock_error = HttpError(Mock(status=500), b'Internal Server Error')
        mock_service.buckets().list().execute.side_effect = mock_error
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        
        # Initialize collected data
        collector._collected_data = {
            'resources': {
                'buckets': {},
                'compute_instances': {},
                'functions': {},
                'pubsub_topics': {},
                'bigquery_datasets': {},
                'kms_keys': {},
                'secrets': {}
            },
            'resource_iam_policies': {},
            'resource_summary': {
                'by_type': {},
                'by_project': {}
            }
        }
        
        # Should not raise exception
        collector._collect_buckets(['test-project'])
        
        # Data should be empty due to error
        assert collector._collected_data['resources']['buckets'] == {}
        
    def test_collect_with_no_resource_types(self, collector):
        """Test collection uses config defaults when no resource types specified"""
        # Set config defaults
        collector.config.collection_resource_types = ['buckets', 'functions']
        
        # Mock collection methods
        collector._collect_buckets = Mock()
        collector._collect_compute_instances = Mock()
        collector._collect_cloud_functions = Mock()
        collector._collect_secrets = Mock()
        collector._collect_kms_keys = Mock()
        collector._collect_pubsub_topics = Mock()
        collector._collect_bigquery_datasets = Mock()
        collector._build_resource_summary = Mock()
        
        # Call collect without resource_types
        result = collector.collect(project_ids=['test-project'])
        
        # Only configured collectors should be called
        collector._collect_buckets.assert_called_once()
        collector._collect_cloud_functions.assert_called_once()
        
        # Others should not be called
        collector._collect_compute_instances.assert_not_called()
        collector._collect_secrets.assert_not_called()
        collector._collect_kms_keys.assert_not_called() 