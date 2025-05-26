"""
Shared fixtures and mocks for GCPHound tests
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import tempfile
import json
from datetime import datetime
import networkx as nx

from gcphound.utils import Config, AuthManager
from gcphound.graph.models import Node, Edge, NodeType, EdgeType


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config():
    """Create a mock configuration object"""
    config = Config()
    # Set test-specific values
    config.collection_page_size = 10
    config.collection_max_pages = 5
    config.collection_max_projects = 10
    config.collection_resource_types = ['buckets', 'compute_instances', 'functions']
    config.collection_include_organization = True
    config.collection_include_folders = True
    config.performance_max_concurrent_requests = 2
    config.performance_rate_limit_requests_per_second = 10
    config.performance_rate_limit_burst_size = 20
    config.analysis_max_path_length = 5
    config.analysis_dangerous_roles = ['roles/owner', 'roles/editor']
    config.visualization_html_physics = True
    config.visualization_html_node_colors = {
        NodeType.USER.value: "#4285F4",
        NodeType.SERVICE_ACCOUNT.value: "#34A853",
        NodeType.GROUP.value: "#FBBC04",
        NodeType.PROJECT.value: "#EA4335"
    }
    config.visualization_html_edge_colors = {
        EdgeType.HAS_ROLE.value: "#757575",
        EdgeType.CAN_IMPERSONATE.value: "#F44336"
    }
    config.visualization_html_attack_path_color = "#FF0000"
    return config


@pytest.fixture
def mock_auth_manager(mock_config):
    """Create a mock authentication manager"""
    auth_manager = Mock(spec=AuthManager)
    auth_manager.config = mock_config
    auth_manager.credentials = Mock()
    auth_manager.impersonate_service_account = None
    
    # Mock build_service method
    def build_service(service_name, version):
        service = Mock()
        return service
    
    auth_manager.build_service = Mock(side_effect=build_service)
    return auth_manager


@pytest.fixture
def sample_hierarchy_data():
    """Sample hierarchy data for testing"""
    return {
        'organizations': {
            '123456789': {
                'name': 'organizations/123456789',
                'displayName': 'Test Organization',
                'state': 'ACTIVE',
                'createTime': '2020-01-01T00:00:00Z'
            }
        },
        'folders': {
            '987654321': {
                'name': 'folders/987654321',
                'displayName': 'Test Folder',
                'parent': 'organizations/123456789',
                'state': 'ACTIVE',
                'createTime': '2020-01-02T00:00:00Z'
            }
        },
        'projects': {
            'test-project-1': {
                'name': 'projects/test-project-1',
                'projectId': 'test-project-1',
                'displayName': 'Test Project 1',
                'parent': 'folders/987654321',
                'state': 'ACTIVE',
                'createTime': '2020-01-03T00:00:00Z',
                'labels': {'env': 'test'}
            },
            'test-project-2': {
                'name': 'projects/test-project-2',
                'projectId': 'test-project-2',
                'displayName': 'Test Project 2',
                'parent': 'organizations/123456789',
                'state': 'ACTIVE',
                'createTime': '2020-01-04T00:00:00Z',
                'labels': {}
            }
        },
        'hierarchy': {
            'organizations': {
                '123456789': {
                    'folders': ['987654321'],
                    'projects': ['test-project-2']
                }
            },
            'folders': {
                '987654321': {
                    'parent': 'organizations/123456789',
                    'folders': [],
                    'projects': ['test-project-1']
                }
            },
            'projects': {
                'test-project-1': {'parent': 'folders/987654321'},
                'test-project-2': {'parent': 'organizations/123456789'}
            }
        }
    }


@pytest.fixture
def sample_iam_data():
    """Sample IAM data for testing"""
    return {
        'policies': {
            'organizations': {
                '123456789': {
                    'resource': 'organizations/123456789',
                    'bindings': [
                        {
                            'role': 'roles/resourcemanager.organizationAdmin',
                            'members': ['user:admin@example.com']
                        }
                    ],
                    'etag': 'BwX1234567',
                    'version': 3
                }
            },
            'folders': {},
            'projects': {
                'test-project-1': {
                    'resource': 'projects/test-project-1',
                    'bindings': [
                        {
                            'role': 'roles/owner',
                            'members': ['user:alice@example.com', 'serviceAccount:sa1@test-project-1.iam.gserviceaccount.com']
                        },
                        {
                            'role': 'roles/iam.serviceAccountTokenCreator',
                            'members': ['user:bob@example.com'],
                            'condition': {
                                'title': 'Expires in 2024',
                                'expression': 'request.time < timestamp("2024-12-31T00:00:00Z")'
                            }
                        }
                    ],
                    'etag': 'BwX7654321',
                    'version': 3
                }
            }
        },
        'roles': {
            'predefined': {
                'roles/owner': {
                    'name': 'roles/owner',
                    'title': 'Owner',
                    'description': 'Full access to all resources',
                    'includedPermissions': ['*'],
                    'stage': 'GA'
                },
                'roles/iam.serviceAccountTokenCreator': {
                    'name': 'roles/iam.serviceAccountTokenCreator',
                    'title': 'Service Account Token Creator',
                    'description': 'Create OAuth2 access tokens for service accounts',
                    'includedPermissions': [
                        'iam.serviceAccounts.getAccessToken',
                        'iam.serviceAccounts.getOpenIdToken',
                        'iam.serviceAccounts.implicitDelegation'
                    ],
                    'stage': 'GA'
                }
            },
            'custom': {}
        },
        'bindings_summary': {
            'by_member': {
                'user:alice@example.com': [
                    {
                        'resource': 'projects/test-project-1',
                        'resource_type': 'project',
                        'resource_id': 'test-project-1',
                        'role': 'roles/owner',
                        'member': 'user:alice@example.com'
                    }
                ],
                'user:bob@example.com': [
                    {
                        'resource': 'projects/test-project-1',
                        'resource_type': 'project',
                        'resource_id': 'test-project-1',
                        'role': 'roles/iam.serviceAccountTokenCreator',
                        'member': 'user:bob@example.com',
                        'condition': {
                            'title': 'Expires in 2024',
                            'expression': 'request.time < timestamp("2024-12-31T00:00:00Z")'
                        }
                    }
                ]
            },
            'by_role': {},
            'by_resource': {}
        },
        'impersonation_analysis': {
            'can_impersonate': {
                'sa1@test-project-1.iam.gserviceaccount.com': [
                    {
                        'member': 'user:bob@example.com',
                        'role': 'roles/iam.serviceAccountTokenCreator',
                        'permissions': ['iam.serviceAccounts.getAccessToken'],
                        'resource': 'projects/test-project-1',
                        'condition': {
                            'title': 'Expires in 2024',
                            'expression': 'request.time < timestamp("2024-12-31T00:00:00Z")'
                        }
                    }
                ]
            },
            'impersonation_chains': []
        }
    }


@pytest.fixture
def sample_identity_data():
    """Sample identity data for testing"""
    return {
        'service_accounts': {
            'sa1@test-project-1.iam.gserviceaccount.com': {
                'name': 'projects/test-project-1/serviceAccounts/sa1@test-project-1.iam.gserviceaccount.com',
                'email': 'sa1@test-project-1.iam.gserviceaccount.com',
                'displayName': 'Test Service Account 1',
                'description': 'Service account for testing',
                'projectId': 'test-project-1',
                'uniqueId': '111111111111111111111',
                'disabled': False,
                'keys': []
            }
        },
        'groups': {
            'test-group@example.com': {
                'name': 'groups/test-group@example.com',
                'groupKey': {'id': 'test-group@example.com'},
                'displayName': 'Test Group',
                'description': 'Test group for testing',
                'createTime': '2020-01-01T00:00:00Z'
            }
        },
        'group_memberships': {
            'test-group@example.com': [
                {
                    'id': 'alice@example.com',
                    'type': 'USER',
                    'roles': ['MEMBER']
                }
            ]
        },
        'users': {
            'alice@example.com': {
                'email': 'alice@example.com',
                'discovered_from': 'group_membership',
                'groups': ['test-group@example.com']
            }
        },
        'identity_summary': {
            'by_type': {
                'users': ['user:alice@example.com', 'user:bob@example.com'],
                'service_accounts': ['serviceAccount:sa1@test-project-1.iam.gserviceaccount.com'],
                'groups': ['group:test-group@example.com']
            }
        }
    }


@pytest.fixture
def sample_resource_data():
    """Sample resource data for testing"""
    return {
        'resources': {
            'buckets': {
                'test-bucket-1': {
                    'name': 'test-bucket-1',
                    'id': 'test-bucket-1',
                    'projectNumber': '123456789012',
                    'location': 'US',
                    'storageClass': 'STANDARD',
                    'timeCreated': '2020-01-01T00:00:00Z',
                    'projectId': 'test-project-1'
                }
            },
            'compute_instances': {
                'test-project-1/us-central1-a/instance-1': {
                    'name': 'instance-1',
                    'id': '1234567890123456789',
                    'machineType': 'n1-standard-1',
                    'status': 'RUNNING',
                    'zone': 'us-central1-a',
                    'serviceAccounts': [
                        {
                            'email': 'sa1@test-project-1.iam.gserviceaccount.com',
                            'scopes': ['https://www.googleapis.com/auth/cloud-platform']
                        }
                    ],
                    'projectId': 'test-project-1'
                }
            },
            'functions': {
                'projects/test-project-1/locations/us-central1/functions/function-1': {
                    'name': 'projects/test-project-1/locations/us-central1/functions/function-1',
                    'runtime': 'python39',
                    'entryPoint': 'main',
                    'serviceAccountEmail': 'sa1@test-project-1.iam.gserviceaccount.com',
                    'projectId': 'test-project-1',
                    'location': 'us-central1'
                }
            }
        },
        'resource_iam_policies': {},
        'resource_summary': {
            'by_type': {
                'buckets': 1,
                'compute_instances': 1,
                'functions': 1
            },
            'by_project': {
                'test-project-1': {
                    'buckets': 1,
                    'compute_instances': 1,
                    'functions': 1
                }
            }
        }
    }


@pytest.fixture
def sample_logs_data():
    """Sample audit logs data for testing"""
    return {
        'impersonation_events': [
            {
                'timestamp': '2023-12-01T10:00:00Z',
                'severity': 'INFO',
                'principal': 'bob@example.com',
                'serviceName': 'iamcredentials.googleapis.com',
                'methodName': 'GenerateAccessToken',
                'resourceName': 'projects/-/serviceAccounts/sa1@test-project-1.iam.gserviceaccount.com',
                'status': {'code': 0},
                'impersonationDetails': {
                    'targetServiceAccount': 'sa1@test-project-1.iam.gserviceaccount.com'
                }
            }
        ],
        'privilege_escalation_events': [],
        'sensitive_access_events': [],
        'suspicious_patterns': [],
        'activity_summary': {
            'by_principal': {
                'bob@example.com': {
                    'impersonations': 1,
                    'escalations': 0,
                    'sensitive_accesses': 0,
                    'methods': ['GenerateAccessToken'],
                    'resources': ['projects/-/serviceAccounts/sa1@test-project-1.iam.gserviceaccount.com']
                }
            },
            'by_method': {
                'GenerateAccessToken': 1
            }
        }
    }


@pytest.fixture
def sample_graph():
    """Create a sample NetworkX graph for testing"""
    graph = nx.DiGraph()
    
    # Add nodes
    graph.add_node('user:alice@example.com', type=NodeType.USER.value, name='alice@example.com', email='alice@example.com')
    graph.add_node('user:bob@example.com', type=NodeType.USER.value, name='bob@example.com', email='bob@example.com')
    graph.add_node('sa:sa1@test-project-1.iam.gserviceaccount.com', type=NodeType.SERVICE_ACCOUNT.value, 
                   name='sa1@test-project-1.iam.gserviceaccount.com', email='sa1@test-project-1.iam.gserviceaccount.com')
    graph.add_node('project:test-project-1', type=NodeType.PROJECT.value, name='projects/test-project-1', projectId='test-project-1')
    graph.add_node('role:roles/owner', type=NodeType.ROLE.value, name='roles/owner', title='Owner')
    graph.add_node('role:roles/iam.serviceAccountTokenCreator', type=NodeType.ROLE.value, 
                   name='roles/iam.serviceAccountTokenCreator', title='Service Account Token Creator')
    
    # Add edges
    graph.add_edge('user:alice@example.com', 'role:roles/owner', type=EdgeType.HAS_ROLE.value, 
                   resource='projects/test-project-1', role='roles/owner')
    graph.add_edge('user:bob@example.com', 'role:roles/iam.serviceAccountTokenCreator', 
                   type=EdgeType.HAS_ROLE.value, resource='projects/test-project-1')
    graph.add_edge('user:bob@example.com', 'sa:sa1@test-project-1.iam.gserviceaccount.com', 
                   type=EdgeType.CAN_IMPERSONATE.value)
    
    return graph


@pytest.fixture
def sample_nodes():
    """Create sample Node objects for testing"""
    nodes = {
        'user:alice@example.com': Node(
            id='user:alice@example.com',
            type=NodeType.USER,
            name='alice@example.com',
            properties={'email': 'alice@example.com'}
        ),
        'user:bob@example.com': Node(
            id='user:bob@example.com',
            type=NodeType.USER,
            name='bob@example.com',
            properties={'email': 'bob@example.com'}
        ),
        'sa:sa1@test-project-1.iam.gserviceaccount.com': Node(
            id='sa:sa1@test-project-1.iam.gserviceaccount.com',
            type=NodeType.SERVICE_ACCOUNT,
            name='sa1@test-project-1.iam.gserviceaccount.com',
            properties={'email': 'sa1@test-project-1.iam.gserviceaccount.com', 'projectId': 'test-project-1'}
        ),
        'project:test-project-1': Node(
            id='project:test-project-1',
            type=NodeType.PROJECT,
            name='projects/test-project-1',
            properties={'projectId': 'test-project-1'}
        ),
        'role:roles/owner': Node(
            id='role:roles/owner',
            type=NodeType.ROLE,
            name='roles/owner',
            properties={'title': 'Owner', 'permissions': ['*']}
        )
    }
    return nodes


@pytest.fixture
def mock_gcp_service():
    """Create a mock GCP service with common methods"""
    service = Mock()
    
    # Mock common service patterns
    service.organizations.return_value = Mock()
    service.folders.return_value = Mock()
    service.projects.return_value = Mock()
    
    return service


@pytest.fixture
def collected_data(sample_hierarchy_data, sample_iam_data, sample_identity_data, sample_resource_data):
    """Complete collected data structure"""
    return {
        'metadata': {
            'start_time': '2023-12-01T00:00:00Z',
            'end_time': '2023-12-01T01:00:00Z',
            'collectors_run': ['hierarchy', 'iam', 'identity', 'resources'],
            'errors': [],
            'stats': {
                'total_projects': 2,
                'total_errors': 0
            }
        },
        'data': {
            'hierarchy': {
                'data': sample_hierarchy_data,
                'metadata': {
                    'collector': 'HierarchyCollector',
                    'errors': [],
                    'stats': {'projects_collected': 2}
                }
            },
            'iam': {
                'data': sample_iam_data,
                'metadata': {
                    'collector': 'IAMCollector',
                    'errors': [],
                    'stats': {'policies_collected': 2}
                }
            },
            'identity': {
                'data': sample_identity_data,
                'metadata': {
                    'collector': 'IdentityCollector',
                    'errors': [],
                    'stats': {'service_accounts_collected': 1}
                }
            },
            'resources': {
                'data': sample_resource_data,
                'metadata': {
                    'collector': 'ResourceCollector',
                    'errors': [],
                    'stats': {'total_resources_collected': 3}
                }
            }
        }
    } 