"""
Tests for IAM collector
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from googleapiclient.errors import HttpError

from gcphound.collectors.iam import IAMCollector


class TestIAMCollector:
    """Test the IAMCollector class"""
    
    @pytest.fixture
    def collector(self, mock_auth_manager, mock_config):
        """Create an IAMCollector instance for testing"""
        return IAMCollector(mock_auth_manager, mock_config)
    
    @pytest.fixture
    def mock_services(self):
        """Create mock GCP services"""
        services = {
            'cloudresourcemanager': Mock(),
            'iam': Mock()
        }
        return services
    
    def test_collect_project_iam_policies(self, collector, mock_services):
        """Test collecting IAM policies for projects"""
        collector.auth_manager.build_service.side_effect = lambda service, version: mock_services[service]
        
        # Mock project IAM policy
        mock_services['cloudresourcemanager'].projects().getIamPolicy.return_value.execute.return_value = {
            'bindings': [
                {
                    'role': 'roles/owner',
                    'members': ['user:alice@example.com', 'group:admins@example.com']
                },
                {
                    'role': 'roles/editor',
                    'members': ['serviceAccount:sa1@project.iam.gserviceaccount.com'],
                    'condition': {
                        'expression': 'request.time < timestamp("2024-12-31T00:00:00Z")',
                        'title': 'Expires end of 2024'
                    }
                }
            ],
            'etag': 'BwXXXXXXXXX='
        }
        
        # Collect
        result = collector.collect(project_ids=['test-project'])
        
        # Verify project policies collected
        assert 'test-project' in result['policies']['projects']
        policy = result['policies']['projects']['test-project']
        assert len(policy['bindings']) == 2
        
        # Check bindings
        owner_binding = policy['bindings'][0]
        assert owner_binding['role'] == 'roles/owner'
        assert 'user:alice@example.com' in owner_binding['members']
        
        # Check conditional binding
        editor_binding = policy['bindings'][1]
        assert 'condition' in editor_binding
        assert editor_binding['condition']['title'] == 'Expires end of 2024'
    
    def test_collect_organization_iam_policy(self, collector, mock_services):
        """Test collecting IAM policy for organization"""
        collector.auth_manager.build_service.side_effect = lambda service, version: mock_services[service]
        collector.config.collection_include_organization = True
        
        # Mock org IAM policy
        mock_services['cloudresourcemanager'].organizations().getIamPolicy.return_value.execute.return_value = {
            'bindings': [
                {
                    'role': 'roles/resourcemanager.organizationAdmin',
                    'members': ['user:admin@example.com']
                }
            ]
        }
        
        # Collect
        result = collector.collect(organization_id='123456789', project_ids=[])
        
        # Verify org policy collected
        assert '123456789' in result['policies']['organizations']
        policy = result['policies']['organizations']['123456789']
        assert len(policy['bindings']) == 1
        assert policy['bindings'][0]['role'] == 'roles/resourcemanager.organizationAdmin'
    
    def test_collect_folder_iam_policies(self, collector, mock_services):
        """Test collecting IAM policies for folders"""
        collector.auth_manager.build_service.side_effect = lambda service, version: mock_services[service]
        collector.config.collection_include_folders = True
        
        # Mock folder IAM policy
        mock_services['cloudresourcemanager'].folders().getIamPolicy.return_value.execute.return_value = {
            'bindings': [
                {
                    'role': 'roles/resourcemanager.folderAdmin',
                    'members': ['user:folder-admin@example.com']
                }
            ]
        }
        
        # Collect
        result = collector.collect(folder_ids=['987654321'], project_ids=[])
        
        # Verify folder policy collected
        assert '987654321' in result['policies']['folders']
        policy = result['policies']['folders']['987654321']
        assert policy['bindings'][0]['role'] == 'roles/resourcemanager.folderAdmin'
    
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_predefined_roles(self, mock_paginate, collector, mock_services):
        """Test collecting predefined role definitions"""
        collector.auth_manager.build_service.side_effect = lambda service, version: mock_services[service]
        
        # Setup test data with roles in bindings
        collector._collected_data = {
            'policies': {
                'projects': {
                    'test-project': {
                        'bindings': [
                            {'role': 'roles/owner', 'members': ['user:test@example.com']},
                            {'role': 'roles/viewer', 'members': ['user:test2@example.com']}
                        ]
                    }
                }
            },
            'roles': {'predefined': {}, 'custom': {}},
            'bindings_summary': {}
        }
        
        # Mock role get responses
        def get_role_side_effect(name):
            roles = {
                'roles/owner': {
                    'name': 'roles/owner',
                    'title': 'Owner',
                    'description': 'Full access to all resources',
                    'includedPermissions': ['*'],
                    'stage': 'GA'
                },
                'roles/viewer': {
                    'name': 'roles/viewer',
                    'title': 'Viewer',
                    'description': 'Read access to all resources',
                    'includedPermissions': ['*.get', '*.list'],
                    'stage': 'GA'
                }
            }
            mock_response = Mock()
            mock_response.execute.return_value = roles.get(name, {})
            return mock_response
        
        mock_services['iam'].roles().get.side_effect = get_role_side_effect
        
        # Collect roles
        collector._collect_predefined_roles()
        
        # Verify roles collected
        assert 'roles/owner' in collector._collected_data['roles']['predefined']
        assert 'roles/viewer' in collector._collected_data['roles']['predefined']
        
        owner_role = collector._collected_data['roles']['predefined']['roles/owner']
        assert owner_role['title'] == 'Owner'
        assert '*' in owner_role['includedPermissions']
    
    @patch('gcphound.collectors.base.BaseCollector._paginate_list')
    def test_collect_custom_roles(self, mock_paginate, collector, mock_services):
        """Test collecting custom role definitions"""
        collector.auth_manager.build_service.side_effect = lambda service, version: mock_services[service]
        
        # Initialize the _collected_data structure
        collector._collected_data = {
            'roles': {'predefined': {}, 'custom': {}},
            'policies': {},
            'bindings_summary': {}
        }
        
        # Mock custom role list
        custom_roles = [
            {
                'name': 'projects/test-project/roles/customDeveloper',
                'title': 'Custom Developer',
                'description': 'Custom role for developers',
                'includedPermissions': [
                    'compute.instances.get',
                    'compute.instances.list',
                    'iam.serviceAccounts.actAs'
                ],
                'stage': 'GA',
                'deleted': False
            }
        ]
        mock_paginate.return_value = iter(custom_roles)
        
        # Mock role get for details - need to mock the projects().roles().get() chain
        mock_services['iam'].projects().roles().get.return_value.execute.return_value = custom_roles[0]
        
        # Collect
        collector._collect_custom_roles('projects/test-project')
        
        # Verify custom role collected
        custom_role_name = 'projects/test-project/roles/customDeveloper'
        assert custom_role_name in collector._collected_data['roles']['custom']
        
        custom_role = collector._collected_data['roles']['custom'][custom_role_name]
        assert custom_role['title'] == 'Custom Developer'
        assert 'iam.serviceAccounts.actAs' in custom_role['includedPermissions']
    
    def test_build_binding_summaries(self, collector):
        """Test building IAM binding summaries"""
        # Setup test data
        collector._collected_data = {
            'policies': {
                'projects': {
                    'project-a': {
                        'resource': 'projects/project-a',
                        'bindings': [
                            {
                                'role': 'roles/owner',
                                'members': ['user:alice@example.com', 'serviceAccount:sa@project.iam.gserviceaccount.com']
                            }
                        ]
                    }
                },
                'organizations': {},
                'folders': {}
            },
            'bindings_summary': {}
        }
        
        # Build summaries
        collector._build_binding_summaries()
        
        # Verify summaries built
        summaries = collector._collected_data['bindings_summary']
        
        # Check by_member
        assert 'user:alice@example.com' in summaries['by_member']
        alice_bindings = summaries['by_member']['user:alice@example.com']
        assert len(alice_bindings) == 1
        assert alice_bindings[0]['role'] == 'roles/owner'
        assert alice_bindings[0]['resource'] == 'projects/project-a'
        
        # Check by_role
        assert 'roles/owner' in summaries['by_role']
        owner_bindings = summaries['by_role']['roles/owner']
        assert len(owner_bindings) == 1
        assert 'user:alice@example.com' in owner_bindings[0]['members']
        
        # Check by_resource
        assert 'projects/project-a' in summaries['by_resource']
        resource_bindings = summaries['by_resource']['projects/project-a']
        assert len(resource_bindings) == 1
        assert resource_bindings[0]['role'] == 'roles/owner'
    
    def test_analyze_impersonation(self, collector):
        """Test analyzing service account impersonation permissions"""
        # Setup test data with roles that grant impersonation
        collector._collected_data = {
            'roles': {
                'predefined': {
                    'roles/iam.serviceAccountTokenCreator': {
                        'includedPermissions': ['iam.serviceAccounts.getAccessToken']
                    },
                    'roles/iam.serviceAccountUser': {
                        'includedPermissions': ['iam.serviceAccounts.actAs']
                    }
                },
                'custom': {}
            },
            'bindings_summary': {
                'by_role': {
                    'roles/iam.serviceAccountTokenCreator': [
                        {
                            'resource': 'projects/test/serviceAccounts/sa1@test.iam.gserviceaccount.com',
                            'members': ['user:bob@example.com']
                        }
                    ]
                },
                'by_member': {},
                'by_resource': {}
            }
        }
        
        # Analyze
        collector._analyze_impersonation()
        
        # Verify impersonation analysis
        assert 'impersonation_analysis' in collector._collected_data
        impersonation = collector._collected_data['impersonation_analysis']
        
        assert 'can_impersonate' in impersonation
        sa_email = 'sa1@test.iam.gserviceaccount.com'
        assert sa_email in impersonation['can_impersonate']
        assert any(
            entry['member'] == 'user:bob@example.com' 
            for entry in impersonation['can_impersonate'][sa_email]
        )
    
    def test_get_members_with_role(self, collector):
        """Test getting all members with a specific role"""
        # Setup test data
        collector._collected_data = {
            'bindings_summary': {
                'by_role': {
                    'roles/owner': [
                        {
                            'members': ['user:alice@example.com', 'user:bob@example.com']
                        },
                        {
                            'members': ['user:charlie@example.com']
                        }
                    ]
                }
            }
        }
        
        # Get members
        members = collector.get_members_with_role('roles/owner')
        
        # Verify all members returned
        assert len(members) == 3
        assert 'user:alice@example.com' in members
        assert 'user:bob@example.com' in members
        assert 'user:charlie@example.com' in members
    
    def test_get_roles_for_member(self, collector):
        """Test getting all roles for a member"""
        # Setup test data
        collector._collected_data = {
            'bindings_summary': {
                'by_member': {
                    'user:alice@example.com': [
                        {
                            'role': 'roles/owner',
                            'resource': 'projects/project-a'
                        },
                        {
                            'role': 'roles/editor',
                            'resource': 'projects/project-b'
                        }
                    ]
                }
            }
        }
        
        # Get roles
        roles = collector.get_roles_for_member('alice@example.com')  # Should normalize
        
        # Verify roles returned
        assert len(roles) == 2
        assert any(r['role'] == 'roles/owner' for r in roles)
        assert any(r['role'] == 'roles/editor' for r in roles)
    
    def test_collect_handles_403_errors(self, collector, mock_services):
        """Test handling 403 permission errors gracefully"""
        collector.auth_manager.build_service.side_effect = lambda service, version: mock_services[service]
        
        # Mock 403 error
        mock_resp = Mock(status=403)
        mock_services['cloudresourcemanager'].projects().getIamPolicy.return_value.execute.side_effect = HttpError(
            mock_resp, b'Permission denied'
        )
        
        # Collect
        result = collector.collect(project_ids=['forbidden-project'])
        
        # Should handle error gracefully
        assert 'forbidden-project' not in result['policies']['projects']
        assert len(collector._metadata['errors']) > 0
    
    def test_concurrent_collection(self, collector, mock_services):
        """Test concurrent collection of IAM policies"""
        collector.auth_manager.build_service.side_effect = lambda service, version: mock_services[service]
        collector.config.performance_max_concurrent_requests = 3
        
        # Mock multiple project policies
        def get_iam_policy_side_effect(resource, body):
            project_id = resource.split('/')[-1]
            return Mock(execute=lambda: {
                'bindings': [{
                    'role': 'roles/viewer',
                    'members': [f'user:{project_id}@example.com']
                }]
            })
        
        mock_services['cloudresourcemanager'].projects().getIamPolicy.side_effect = get_iam_policy_side_effect
        
        # Collect multiple projects
        project_ids = [f'project-{i}' for i in range(5)]
        result = collector.collect(project_ids=project_ids)
        
        # Verify all collected
        for project_id in project_ids:
            assert project_id in result['policies']['projects']




