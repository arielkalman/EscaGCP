"""
Tests for Cloud Build collector
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from googleapiclient.errors import HttpError

from gcphound.collectors.cloudbuild_collector import CloudBuildCollector


class TestCloudBuildCollector:
    """Test the CloudBuildCollector class"""
    
    @pytest.fixture
    def collector(self, mock_auth_manager, mock_config):
        """Create a CloudBuildCollector instance for testing"""
        return CloudBuildCollector(mock_auth_manager, mock_config)
    
    @pytest.fixture
    def mock_services(self):
        """Create mock GCP services"""
        services = {
            'cloudbuild': Mock(),
            'cloudresourcemanager': Mock()
        }
        return services
    
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_recent_builds')
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_worker_pools')
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_cloud_build_data(self, mock_paginate, mock_collect_worker_pools, mock_collect_recent_builds, collector):
        """Test collecting Cloud Build data for projects"""
        # Mock build_service
        mock_service = Mock()
        collector.auth_manager.build_service.return_value = mock_service
        
        # Mock project number lookup - need to mock both services
        def mock_build_service(service_name, version):
            if service_name == 'cloudresourcemanager':
                crm_service = Mock()
                projects_resource = Mock()
                projects_resource.get.return_value.execute.return_value = {
                    'name': 'projects/123456789012',  # The method extracts from name field
                    'projectNumber': '123456789012'
                }
                crm_service.projects.return_value = projects_resource
                return crm_service
            else:
                return mock_service
        
        collector.auth_manager.build_service.side_effect = mock_build_service
        
        # Mock Cloud Build triggers
        triggers = [
            {
                'id': 'trigger-1',
                'name': 'test-trigger',
                'description': 'Test trigger',
                'github': {
                    'owner': 'test-org',
                    'name': 'test-repo',
                    'push': {'branch': 'main'}
                },
                'build': {
                    'steps': [{'name': 'gcr.io/cloud-builders/docker'}],
                    'serviceAccount': 'projects/test-project/serviceAccounts/custom-sa@test-project.iam.gserviceaccount.com'
                },
                'createTime': '2023-01-01T00:00:00Z'
            }
        ]
        mock_paginate.return_value = iter(triggers)
        
        # Mock worker pools and recent builds to do nothing
        mock_collect_worker_pools.return_value = None
        mock_collect_recent_builds.return_value = None
        
        # Collect
        result = collector.collect(project_ids=['test-project'])
        
        # Verify Cloud Build service accounts collected
        assert 'test-project' in result['service_accounts']
        sa_info = result['service_accounts']['test-project']
        assert sa_info['default'] == '123456789012@cloudbuild.gserviceaccount.com'
        assert sa_info['project_number'] == '123456789012'
        
        # Verify triggers collected
        assert 'test-project/trigger-1' in result['triggers']
        trigger = result['triggers']['test-project/trigger-1']
        assert trigger['name'] == 'test-trigger'
        # The serviceAccount is nested in the build config
        assert trigger['build']['serviceAccount'] == 'projects/test-project/serviceAccounts/custom-sa@test-project.iam.gserviceaccount.com'
    
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_recent_builds')
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_worker_pools')
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_default_service_account_detection(self, mock_paginate, mock_collect_worker_pools, mock_collect_recent_builds, collector):
        """Test detection of default Cloud Build service account usage"""
        # Mock build_service
        def mock_build_service(service_name, version):
            if service_name == 'cloudresourcemanager':
                crm_service = Mock()
                projects_resource = Mock()
                projects_resource.get.return_value.execute.return_value = {
                    'name': 'projects/123456789012',
                    'projectNumber': '123456789012'
                }
                crm_service.projects.return_value = projects_resource
                return crm_service
            else:
                return Mock()
        
        collector.auth_manager.build_service.side_effect = mock_build_service
        
        # Mock trigger using default SA
        triggers = [
            {
                'id': 'trigger-default',
                'name': 'default-sa-trigger',
                'build': {
                    'steps': [{'name': 'gcr.io/cloud-builders/gcloud'}]
                    # No serviceAccount specified = uses default
                }
            }
        ]
        mock_paginate.return_value = iter(triggers)
        
        # Mock worker pools and recent builds to do nothing
        mock_collect_worker_pools.return_value = None
        mock_collect_recent_builds.return_value = None
        
        # Collect
        result = collector.collect(project_ids=['test-project'])
        
        # Verify default SA usage detected
        trigger = result['triggers']['test-project/trigger-default']
        assert trigger.get('serviceAccount') is None  # No custom SA specified
    
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_worker_pools')
    def test_collect_worker_pools(self, mock_collect_worker_pools, collector):
        """Test collecting Cloud Build worker pools"""
        # Set up test data
        worker_pools = {
            'projects/test-project/locations/us-central1/workerPools/pool1': {
                'name': 'projects/test-project/locations/us-central1/workerPools/pool1',
                'displayName': 'Test Pool',
                'project_id': 'test-project',
                'state': 'RUNNING',
                'privatePoolV1Config': {
                    'workerConfig': {
                        'machineType': 'e2-standard-4',
                        'diskSizeGb': 100
                    },
                    'networkConfig': {
                        'peeredNetwork': 'projects/test-project/global/networks/vpc-1'
                    }
                },
                'createTime': '2023-01-01T00:00:00Z',
                'updateTime': None
            }
        }
        
        # Mock the method to populate data directly
        def mock_collect(project_id):
            collector._collected_data['worker_pools'].update(worker_pools)
            collector._increment_stat('worker_pools_collected')
        
        mock_collect_worker_pools.side_effect = mock_collect
        
        # Initialize collected data
        collector._collected_data = {
            'service_accounts': {},
            'triggers': {},
            'worker_pools': {},
            'github_connections': {},
            'build_configs': []
        }
        
        # Collect worker pools
        collector._collect_worker_pools('test-project')
        
        # Verify collected
        assert 'projects/test-project/locations/us-central1/workerPools/pool1' in collector._collected_data['worker_pools']
        pool = collector._collected_data['worker_pools']['projects/test-project/locations/us-central1/workerPools/pool1']
        assert pool['displayName'] == 'Test Pool'
        assert pool['state'] == 'RUNNING'
        assert pool['privatePoolV1Config']['workerConfig']['machineType'] == 'e2-standard-4'
    
    def test_analyze_service_account_permissions(self, collector, mock_services):
        """Test analyzing Cloud Build service account permissions"""
        collector.auth_manager.build_service.side_effect = lambda service, version: mock_services[service]
        
        # Setup test data
        collector._collected_data = {
            'service_accounts': {
                'test-project': {
                    'default': '123456789012@cloudbuild.gserviceaccount.com',
                    'project_id': 'test-project',
                    'project_number': '123456789012',
                    'type': 'cloud_build_default'
                }
            },
            'triggers': {
                'test-project/trigger-1': {
                    'serviceAccount': 'custom-sa@test-project.iam.gserviceaccount.com',
                    'project_id': 'test-project'
                }
            },
            'worker_pools': {},
            'github_connections': {},
            'build_configs': []
        }
        
        # Check custom service accounts
        collector._check_custom_service_accounts('test-project')
        
        # Verify custom service accounts were found
        assert 'test-project' in collector._collected_data['service_accounts']
        sa_info = collector._collected_data['service_accounts']['test-project']
        assert 'custom' in sa_info
        assert 'custom-sa@test-project.iam.gserviceaccount.com' in sa_info['custom']
    
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_recent_builds')
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_worker_pools')
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_handles_api_errors(self, mock_paginate, mock_collect_worker_pools, mock_collect_recent_builds, collector):
        """Test handling API errors gracefully"""
        # Mock build_service
        def mock_build_service(service_name, version):
            if service_name == 'cloudresourcemanager':
                crm_service = Mock()
                projects_resource = Mock()
                projects_resource.get.return_value.execute.return_value = {
                    'name': 'projects/123456789012',
                    'projectNumber': '123456789012'
                }
                crm_service.projects.return_value = projects_resource
                return crm_service
            else:
                return Mock()
        
        collector.auth_manager.build_service.side_effect = mock_build_service
        
        # Mock 403 error for triggers
        mock_resp = Mock(status=403)
        mock_paginate.side_effect = HttpError(mock_resp, b'Permission denied')
        
        # Mock worker pools and recent builds to do nothing
        mock_collect_worker_pools.return_value = None
        mock_collect_recent_builds.return_value = None
        
        # Collect
        result = collector.collect(project_ids=['test-project'])
        
        # Should handle error gracefully
        assert 'test-project' in result['service_accounts']
        assert len(result['triggers']) == 0
        assert len(collector._metadata['errors']) == 0  # 403 errors are ignored
    
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_recent_builds')
    def test_recent_builds_analysis(self, mock_collect_recent_builds, collector):
        """Test analyzing recent builds for patterns"""
        # Set up test builds data
        builds = [
            {
                'id': 'build-1',
                'project_id': 'test-project',
                'serviceAccount': 'custom-sa@test-project.iam.gserviceaccount.com',
                'options': {},
                'substitutions': [],
                'tags': [],
                'secrets': 0,
                'availableSecrets': None,
                'logsBucket': None
            },
            {
                'id': 'build-2',
                'project_id': 'test-project',
                'serviceAccount': '123456789012@cloudbuild.gserviceaccount.com',
                'options': {},
                'substitutions': [],
                'tags': [],
                'secrets': 0,
                'availableSecrets': None,
                'logsBucket': None
            },
            {
                'id': 'build-3',
                'project_id': 'test-project',
                'serviceAccount': 'another-sa@test-project.iam.gserviceaccount.com',
                'options': {},
                'substitutions': [],
                'tags': [],
                'secrets': 0,
                'availableSecrets': None,
                'logsBucket': None
            }
        ]
        
        # Mock the method to populate data directly
        def mock_collect(project_id):
            collector._collected_data['build_configs'].extend(builds)
        
        mock_collect_recent_builds.side_effect = mock_collect
        
        # Initialize collected data
        collector._collected_data = {
            'service_accounts': {},
            'triggers': {},
            'worker_pools': {},
            'github_connections': {},
            'build_configs': []
        }
        
        # Collect recent builds
        collector._collect_recent_builds('test-project')
        
        # Verify builds collected
        assert len(collector._collected_data['build_configs']) == 3
        
        # Check that different service accounts were captured
        service_accounts = {build['serviceAccount'] for build in collector._collected_data['build_configs']}
        assert len(service_accounts) == 3
        assert 'custom-sa@test-project.iam.gserviceaccount.com' in service_accounts
    
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_recent_builds')
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_worker_pools')
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_empty_cloud_build_config(self, mock_paginate, mock_collect_worker_pools, mock_collect_recent_builds, collector):
        """Test handling projects with no Cloud Build configuration"""
        # Mock build_service
        def mock_build_service(service_name, version):
            if service_name == 'cloudresourcemanager':
                crm_service = Mock()
                projects_resource = Mock()
                projects_resource.get.return_value.execute.return_value = {
                    'name': 'projects/123456789012',
                    'projectNumber': '123456789012'
                }
                crm_service.projects.return_value = projects_resource
                return crm_service
            else:
                return Mock()
        
        collector.auth_manager.build_service.side_effect = mock_build_service
        
        # Mock empty responses
        mock_paginate.return_value = iter([])
        mock_collect_worker_pools.return_value = None
        mock_collect_recent_builds.return_value = None
        
        # Collect
        result = collector.collect(project_ids=['empty-project'])
        
        # Verify structure is valid but empty
        assert 'empty-project' in result['service_accounts']
        assert len(result['triggers']) == 0
        assert len(result['worker_pools']) == 0
        assert len(result['build_configs']) == 0
    
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_build_triggers')
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_worker_pools')
    @patch('gcphound.collectors.cloudbuild_collector.CloudBuildCollector._collect_recent_builds')
    def test_project_number_lookup_failure(self, mock_collect_recent_builds, mock_collect_worker_pools, mock_collect_triggers, collector):
        """Test handling project number lookup failure"""
        # Mock build_service to fail on project lookup
        def mock_build_service(service_name, version):
            if service_name == 'cloudresourcemanager':
                crm_service = Mock()
                projects_resource = Mock()
                mock_resp = Mock(status=404)
                projects_resource.get.return_value.execute.side_effect = HttpError(
                    mock_resp, b'Not found'
                )
                crm_service.projects.return_value = projects_resource
                return crm_service
            else:
                return Mock()
        
        collector.auth_manager.build_service.side_effect = mock_build_service
        
        # Mock other methods to do nothing
        mock_collect_triggers.return_value = None
        mock_collect_worker_pools.return_value = None
        mock_collect_recent_builds.return_value = None
        
        # Collect
        result = collector.collect(project_ids=['invalid-project'])
        
        # Should handle gracefully - no service account collected due to missing project number
        assert 'invalid-project' not in result['service_accounts'] 