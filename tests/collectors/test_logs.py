"""Tests for the logs collector"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
from gcphound.collectors.logs_collector import LogsCollector
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
            'log_days_back': 30
        },
        'performance': {
            'max_concurrent_requests': 5
        }
    })


@pytest.fixture
def collector(auth_manager, config):
    """Create a LogsCollector instance"""
    return LogsCollector(auth_manager, config)


class TestLogsCollector:
    """Test the LogsCollector class"""
    
    def test_init(self, collector):
        """Test collector initialization"""
        assert collector.__class__.__name__ == "LogsCollector"
        assert hasattr(collector, '_collected_data')
        assert hasattr(collector, 'auth_manager')
        assert hasattr(collector, 'config')
        assert hasattr(collector, 'IMPERSONATION_METHODS')
        assert hasattr(collector, 'PRIVILEGE_ESCALATION_METHODS')
    
    def test_build_log_filters(self, collector):
        """Test log filter building"""
        filters = collector._build_log_filters(
            days_back=7,
            custom_filter=None,
            collect_impersonation=True,
            collect_privilege_escalation=True,
            collect_sensitive_access=True
        )
        
        # Check that filters were created
        assert 'impersonation' in filters
        assert 'privilege_escalation' in filters
        assert 'sensitive_access' in filters
        
        # Check filter content
        assert 'GenerateAccessToken' in filters['impersonation']
        assert 'SetIamPolicy' in filters['privilege_escalation']
        assert 'secretmanager.googleapis.com' in filters['sensitive_access']
        
    def test_parse_log_entry(self, collector):
        """Test log entry parsing"""
        # Mock log entry
        entry = {
            'timestamp': '2023-01-01T00:00:00Z',
            'severity': 'INFO',
            'protoPayload': {
                'authenticationInfo': {
                    'principalEmail': 'user@example.com',
                    'principalSubject': 'user:user@example.com'
                },
                'serviceName': 'iam.googleapis.com',
                'methodName': 'GenerateAccessToken',
                'resourceName': 'projects/-/serviceAccounts/sa@test-project.iam.gserviceaccount.com',
                'requestMetadata': {
                    'callerIp': '1.2.3.4',
                    'userAgent': 'gcloud'
                },
                'authorizationInfo': [
                    {
                        'permission': 'iam.serviceAccounts.getAccessToken',
                        'granted': True
                    }
                ],
                'request': {
                    'scope': ['https://www.googleapis.com/auth/cloud-platform']
                },
                'response': {},
                'status': {}
            }
        }
        
        # Parse the entry
        event = collector._parse_log_entry(entry)
        
        # Verify parsing
        assert event is not None
        assert event['principal'] == 'user@example.com'
        assert event['methodName'] == 'GenerateAccessToken'
        assert event['serviceName'] == 'iam.googleapis.com'
        assert 'impersonationDetails' in event
        assert event['impersonationDetails']['targetServiceAccount'] == 'sa@test-project.iam.gserviceaccount.com'
        
    def test_extract_impersonation_details(self, collector):
        """Test impersonation detail extraction"""
        proto_payload = {
            'resourceName': 'projects/-/serviceAccounts/admin@test-project.iam.gserviceaccount.com',
            'request': {
                'delegates': ['sa1@test-project.iam.gserviceaccount.com'],
                'scope': ['https://www.googleapis.com/auth/cloud-platform'],
                'audience': 'https://example.com'
            }
        }
        
        details = collector._extract_impersonation_details(proto_payload)
        
        assert details['targetServiceAccount'] == 'admin@test-project.iam.gserviceaccount.com'
        assert details['delegationChain'] == ['sa1@test-project.iam.gserviceaccount.com']
        assert details['scope'] == ['https://www.googleapis.com/auth/cloud-platform']
        assert details['audience'] == 'https://example.com'
        
    def test_extract_escalation_details(self, collector):
        """Test privilege escalation detail extraction"""
        proto_payload = {
            'resourceName': 'projects/test-project',
            'request': {
                'policy': {
                    'bindings': [
                        {
                            'role': 'roles/owner',
                            'members': ['user:attacker@example.com']
                        }
                    ]
                },
                'role': {
                    'name': 'roles/custom',
                    'includedPermissions': ['iam.serviceAccounts.actAs', 'compute.instances.create']
                }
            }
        }
        
        details = collector._extract_escalation_details(proto_payload)
        
        assert details['targetResource'] == 'projects/test-project'
        assert len(details['newBindings']) == 1
        assert details['newBindings'][0]['role'] == 'roles/owner'
        assert details['role']['name'] == 'roles/custom'
        assert len(details['permissions']) == 2
        
    def test_process_log_events(self, collector):
        """Test log event processing"""
        # Initialize collected data
        collector._collected_data = {
            'impersonation_events': [],
            'privilege_escalation_events': [],
            'sensitive_access_events': [],
            'suspicious_patterns': [],
            'activity_summary': {
                'by_principal': {},
                'by_resource': {},
                'by_method': {}
            }
        }
        
        # Mock events
        events = [
            {
                'timestamp': '2023-01-01T00:00:00Z',
                'principal': 'user@example.com',
                'methodName': 'GenerateAccessToken',
                'status': {'code': 0}
            },
            {
                'timestamp': '2023-01-02T00:00:00Z',
                'principal': 'admin@example.com',
                'methodName': 'SetIamPolicy',
                'status': {}
            },
            {
                'timestamp': '2023-01-03T00:00:00Z',
                'principal': 'user@example.com',
                'methodName': 'AccessSecretVersion',
                'status': {'code': 403}  # Failed
            }
        ]
        
        # Process events
        collector._process_log_events(events[:1], 'impersonation')
        collector._process_log_events(events[1:2], 'privilege_escalation')
        collector._process_log_events(events[2:], 'sensitive_access')
        
        # Verify processing
        assert len(collector._collected_data['impersonation_events']) == 1
        assert len(collector._collected_data['privilege_escalation_events']) == 1
        assert len(collector._collected_data['sensitive_access_events']) == 0  # Failed event excluded
        
    def test_analyze_suspicious_patterns(self, collector):
        """Test suspicious pattern analysis"""
        # Set up test data with suspicious patterns
        collector._collected_data = {
            'impersonation_events': [
                {
                    'timestamp': f'2023-01-01T{i:02d}:00:00Z',
                    'principal': 'suspicious@example.com',
                    'methodName': 'GenerateAccessToken',
                    'impersonationDetails': {
                        'targetServiceAccount': f'sa{i}@test-project.iam.gserviceaccount.com'
                    }
                }
                for i in range(6)  # 6 impersonations to different SAs
            ],
            'privilege_escalation_events': [
                {
                    'timestamp': '2023-01-01T00:00:00Z',
                    'principal': 'attacker@example.com',
                    'methodName': 'SetIamPolicy',
                    'failed': False
                }
            ],
            'sensitive_access_events': [
                {
                    'timestamp': '2023-01-01T00:30:00Z',  # 30 minutes after escalation
                    'principal': 'attacker@example.com',
                    'methodName': 'AccessSecretVersion',
                    'resourceName': 'projects/test-project/secrets/api-key'
                }
            ],
            'suspicious_patterns': [],
            'activity_summary': {
                'by_principal': {},
                'by_resource': {},
                'by_method': {}
            }
        }
        
        # Analyze patterns
        collector._analyze_suspicious_patterns()
        
        # Check patterns were detected
        patterns = collector._collected_data['suspicious_patterns']
        assert len(patterns) >= 2
        
        # Check for rapid impersonation chain
        impersonation_pattern = next(
            (p for p in patterns if p['type'] == 'rapid_impersonation_chain'),
            None
        )
        assert impersonation_pattern is not None
        assert impersonation_pattern['principal'] == 'suspicious@example.com'
        assert impersonation_pattern['unique_targets'] == 6
        
        # Check for escalation then access pattern
        escalation_pattern = next(
            (p for p in patterns if p['type'] == 'escalation_then_access'),
            None
        )
        assert escalation_pattern is not None
        assert escalation_pattern['principal'] == 'attacker@example.com'
        
    def test_build_activity_summary(self, collector):
        """Test activity summary building"""
        # Set up test data
        collector._collected_data = {
            'impersonation_events': [
                {
                    'principal': 'user1@example.com',
                    'methodName': 'GenerateAccessToken',
                    'resourceName': 'projects/-/serviceAccounts/sa1@test.iam'
                },
                {
                    'principal': 'user1@example.com',
                    'methodName': 'GenerateIdToken',
                    'resourceName': 'projects/-/serviceAccounts/sa2@test.iam'
                }
            ],
            'privilege_escalation_events': [
                {
                    'principal': 'admin@example.com',
                    'methodName': 'SetIamPolicy',
                    'resourceName': 'projects/test-project'
                }
            ],
            'sensitive_access_events': [
                {
                    'principal': 'user1@example.com',
                    'methodName': 'AccessSecretVersion',
                    'resourceName': 'projects/test-project/secrets/api-key'
                }
            ],
            'suspicious_patterns': [],
            'activity_summary': {
                'by_principal': {},
                'by_resource': {},
                'by_method': {}
            }
        }
        
        # Build summary
        collector._build_activity_summary()
        
        # Verify summary
        summary = collector._collected_data['activity_summary']
        
        # Check by_principal
        assert 'user1@example.com' in summary['by_principal']
        assert summary['by_principal']['user1@example.com']['impersonations'] == 2
        assert summary['by_principal']['user1@example.com']['sensitive_accesses'] == 1
        assert 'admin@example.com' in summary['by_principal']
        assert summary['by_principal']['admin@example.com']['escalations'] == 1
        
        # Check by_method
        assert 'GenerateAccessToken' in summary['by_method']
        assert summary['by_method']['GenerateAccessToken'] == 1
        assert 'SetIamPolicy' in summary['by_method']
        
    def test_collect_with_all_options(self, collector):
        """Test the main collect method"""
        # Mock the internal methods
        collector._build_log_filters = Mock(return_value={
            'impersonation': 'filter1',
            'privilege_escalation': 'filter2'
        })
        collector._collect_project_logs = Mock(return_value=[
            {'event': 'test1'},
            {'event': 'test2'}
        ])
        collector._process_log_events = Mock()
        collector._analyze_suspicious_patterns = Mock()
        collector._build_activity_summary = Mock()
        
        # Call collect
        result = collector.collect(
            project_ids=['test-project'],
            days_back=7,
            collect_impersonation=True,
            collect_privilege_escalation=True,
            collect_sensitive_access=False
        )
        
        # Verify methods were called
        collector._build_log_filters.assert_called_once()
        assert collector._collect_project_logs.call_count == 2  # 2 filters
        collector._analyze_suspicious_patterns.assert_called_once()
        collector._build_activity_summary.assert_called_once()
        
        # Verify result structure
        assert 'impersonation_events' in result
        assert 'privilege_escalation_events' in result
        assert 'sensitive_access_events' in result
        assert 'suspicious_patterns' in result
        assert 'activity_summary' in result
        
    def test_error_handling(self, collector):
        """Test error handling in log collection"""
        # Mock service that raises HttpError
        mock_service = Mock()
        mock_error = HttpError(Mock(status=403), b'Access Denied')
        mock_service.entries().list().execute.side_effect = mock_error
        
        collector.auth_manager.build_service = Mock(return_value=mock_service)
        
        # Should not raise exception, returns empty list
        events = collector._collect_project_logs('test-project', 'filter', 'test')
        assert events == []
        
    def test_within_time_window(self, collector):
        """Test time window checking"""
        timestamp1 = '2023-01-01T12:00:00Z'
        timestamp2 = '2023-01-01T12:30:00Z'
        timestamp3 = '2023-01-01T14:00:00Z'
        
        # Within 1 hour
        assert collector._within_time_window(timestamp1, timestamp2, hours=1) == True
        
        # Not within 1 hour
        assert collector._within_time_window(timestamp1, timestamp3, hours=1) == False 