"""Tests for the GKE collector"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError
from gcphound.collectors.gke_collector import GKECollector
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
            'collect_gke_workloads': True
        }
    })


@pytest.fixture
def collector(auth_manager, config):
    """Create a GKECollector instance"""
    return GKECollector(auth_manager, config)


class TestGKECollector:
    """Test the GKECollector class"""
    
    def test_init(self, collector):
        """Test collector initialization"""
        assert collector.__class__.__name__ == "GKECollector"
        assert hasattr(collector, '_collected_data')
        assert hasattr(collector, 'auth_manager')
        assert hasattr(collector, 'config')
    
    def test_collect_clusters(self, collector):
        """Test GKE cluster collection"""
        # Mock container service
        mock_service = Mock()
        
        # Mock clusters response
        mock_clusters_response = {
            'clusters': [
                {
                    'name': 'test-cluster',
                    'location': 'us-central1-a',
                    'endpoint': '10.0.0.1',
                    'status': 'RUNNING',
                    'currentMasterVersion': '1.27.3-gke.100',
                    'currentNodeVersion': '1.27.3-gke.100',
                    'nodeConfig': {
                        'serviceAccount': 'default',
                        'oauthScopes': [
                            'https://www.googleapis.com/auth/cloud-platform'
                        ]
                    },
                    'workloadIdentityConfig': {
                        'workloadPool': 'test-project.svc.id.goog'
                    },
                    'addonsConfig': {
                        'gcePersistentDiskCsiDriverConfig': {'enabled': True},
                        'workloadIdentityConfig': {'enabled': True}
                    },
                    'nodePools': [
                        {
                            'name': 'default-pool',
                            'config': {
                                'serviceAccount': 'gke-node-sa@test-project.iam.gserviceaccount.com',
                                'oauthScopes': ['https://www.googleapis.com/auth/cloud-platform']
                            },
                            'autoscaling': {
                                'enabled': True,
                                'minNodeCount': 1,
                                'maxNodeCount': 10
                            }
                        }
                    ]
                },
                {
                    'name': 'prod-cluster',
                    'location': 'us-east1',
                    'endpoint': '10.0.0.2',
                    'status': 'RUNNING',
                    'currentMasterVersion': '1.27.3-gke.100',
                    'workloadIdentityConfig': {
                        'workloadPool': 'test-project.svc.id.goog'
                    }
                }
            ]
        }
        
        # Set up mocks
        mock_service.projects().locations().clusters().list.return_value.execute.return_value = mock_clusters_response
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        collector._paginate_list = Mock(return_value=mock_clusters_response['clusters'])
        
        # Initialize collected data
        collector._collected_data = {
            'clusters': {},
            'node_pools': {},
            'workload_identity_pools': {},
            'k8s_service_accounts': {},
            'binary_authorization': {},
            'pod_security_policies': {}
        }
        
        # Call the method
        collector._collect_clusters('test-project')
        
        # Verify results
        assert len(collector._collected_data['clusters']) == 2
        assert 'test-project/us-central1-a/test-cluster' in collector._collected_data['clusters']
        assert 'test-project/us-east1/prod-cluster' in collector._collected_data['clusters']
        
        # Check cluster details
        cluster_id = 'test-project/us-central1-a/test-cluster'
        test_cluster = collector._collected_data['clusters'][cluster_id]
        assert test_cluster['location'] == 'us-central1-a'
        assert test_cluster['status'] == 'RUNNING'
        assert test_cluster['workloadIdentityConfig']['workloadPool'] == 'test-project.svc.id.goog'
        
        # Check node pools were collected
        assert len(collector._collected_data['node_pools']) > 0
        
    def test_collect_workload_identity_bindings(self, collector):
        """Test workload identity collection"""
        # Initialize collected data
        collector._collected_data = {
            'clusters': {},
            'node_pools': {},
            'workload_identity_pools': {},
            'k8s_service_accounts': {},
            'binary_authorization': {},
            'pod_security_policies': {}
        }
        
        # Call the method
        cluster_id = 'test-project/us-central1-a/test-cluster'
        workload_pool = 'test-project.svc.id.goog'
        collector._collect_workload_identity_bindings(cluster_id, workload_pool)
        
        # Verify results
        assert cluster_id in collector._collected_data['workload_identity_pools']
        pool_data = collector._collected_data['workload_identity_pools'][cluster_id]
        
        assert pool_data['cluster_id'] == cluster_id
        assert pool_data['workload_pool'] == workload_pool
        assert pool_data['k8s_service_accounts'] == []
                
    def test_collect_all(self, collector):
        """Test the main collect method"""
        # Mock methods
        collector._collect_project_gke = Mock()
        
        # Call collect
        result = collector.collect(
            project_ids=['test-project']
        )
        
        # Verify all collectors were called
        collector._collect_project_gke.assert_called_once_with('test-project')
        
        # Verify result structure
        assert 'clusters' in result
        assert 'node_pools' in result
        assert 'workload_identity_pools' in result
        assert 'k8s_service_accounts' in result
        assert 'binary_authorization' in result
        assert 'pod_security_policies' in result
        
    def test_error_handling_clusters(self, collector):
        """Test error handling in cluster collection"""
        # Mock service that raises HttpError
        mock_service = Mock()
        mock_error = HttpError(Mock(status=403), b'Access Denied')
        mock_service.projects().locations().clusters().list().execute.side_effect = mock_error
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        
        # Initialize collected data
        collector._collected_data = {
            'clusters': {},
            'node_pools': {},
            'workload_identity_pools': {},
            'k8s_service_accounts': {},
            'binary_authorization': {},
            'pod_security_policies': {}
        }
        
        # Should not raise exception
        collector._collect_clusters('test-project')
        
        # Data should be empty due to error
        assert collector._collected_data['clusters'] == {}
        
    def test_binary_authorization_collection(self, collector):
        """Test binary authorization policy collection"""
        # Mock binary authorization service
        mock_service = Mock()
        
        # Mock policy response
        mock_policy = {
            'name': 'projects/test-project/policy',
            'globalPolicyEvaluationMode': 'ENABLE',
            'admissionWhitelistPatterns': [
                {'namePattern': 'gcr.io/test-project/*'}
            ],
            'defaultAdmissionRule': {
                'evaluationMode': 'REQUIRE_ATTESTATION',
                'enforcementMode': 'ENFORCED_BLOCK_AND_AUDIT_LOG'
            },
            'updateTime': '2023-01-01T00:00:00Z'
        }
        
        # Set up mocks
        mock_service.projects().getPolicy().execute.return_value = mock_policy
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        
        # Initialize collected data
        collector._collected_data = {
            'clusters': {},
            'node_pools': {},
            'workload_identity_pools': {},
            'k8s_service_accounts': {},
            'binary_authorization': {},
            'pod_security_policies': {}
        }
        
        # Call the method
        collector._collect_binary_authorization('test-project')
        
        # Verify results
        assert 'test-project' in collector._collected_data['binary_authorization']
        policy_data = collector._collected_data['binary_authorization']['test-project']
        
        assert policy_data['name'] == 'projects/test-project/policy'
        assert policy_data['globalPolicyEvaluationMode'] == 'ENABLE'
        assert len(policy_data['admissionWhitelistPatterns']) == 1 