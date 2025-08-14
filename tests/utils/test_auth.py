"""
Tests for authentication manager
"""

import pytest
from unittest.mock import patch, Mock, MagicMock, call
from google.auth.exceptions import DefaultCredentialsError, RefreshError
from googleapiclient.errors import HttpError
import google.auth

from escagcp.utils.auth import AuthManager
from escagcp.utils.config import Config


class TestAuthManager:
    """Test the AuthManager class"""
    
    @pytest.fixture
    def auth_config(self):
        """Create a test configuration"""
        config = Config()
        config.authentication_method = 'adc'
        config.authentication_service_account_key_file = None
        config.authentication_impersonate_service_account = None
        config.authentication_scopes = [
            'https://www.googleapis.com/auth/cloud-platform.read-only'
        ]
        return config
    
    def test_init_with_adc(self, auth_config):
        """Test initialization with Application Default Credentials"""
        auth_manager = AuthManager(auth_config)
        assert auth_manager.config == auth_config
        assert auth_manager.credentials is None
        assert auth_manager.impersonate_service_account is None
    
    def test_init_with_service_account(self, auth_config):
        """Test initialization with service account"""
        auth_config.authentication_method = 'service_account'
        auth_config.authentication_service_account_key_file = '/path/to/key.json'
        
        auth_manager = AuthManager(auth_config)
        assert auth_manager.config == auth_config
        assert auth_manager.credentials is None
    
    def test_init_with_impersonation(self, auth_config):
        """Test initialization with service account impersonation"""
        auth_config.authentication_impersonate_service_account = 'sa@project.iam.gserviceaccount.com'
        
        auth_manager = AuthManager(auth_config)
        assert auth_manager.impersonate_service_account == 'sa@project.iam.gserviceaccount.com'
    
    @patch('google.auth.default')
    def test_authenticate_with_adc_success(self, mock_default, auth_config):
        """Test successful authentication with ADC"""
        mock_creds = Mock()
        mock_project = 'test-project'
        mock_default.return_value = (mock_creds, mock_project)
        
        auth_manager = AuthManager(auth_config)
        auth_manager.authenticate()
        
        assert auth_manager.credentials == mock_creds
        mock_default.assert_called_once_with(scopes=auth_config.authentication_scopes)
    
    @patch('google.auth.default')
    def test_authenticate_with_adc_failure(self, mock_default, auth_config):
        """Test failed authentication with ADC"""
        mock_default.side_effect = DefaultCredentialsError("No credentials found")
        
        auth_manager = AuthManager(auth_config)
        with pytest.raises(DefaultCredentialsError):
            auth_manager.authenticate()
    
    @patch('google.auth.load_credentials_from_file')
    def test_authenticate_with_service_account_success(self, mock_load, auth_config):
        """Test successful authentication with service account key"""
        auth_config.authentication_method = 'service_account'
        auth_config.authentication_service_account_key_file = '/path/to/key.json'
        
        mock_creds = Mock()
        mock_project = 'test-project'
        mock_load.return_value = (mock_creds, mock_project)
        
        auth_manager = AuthManager(auth_config)
        auth_manager.authenticate()
        
        assert auth_manager.credentials == mock_creds
        mock_load.assert_called_once_with(
            '/path/to/key.json',
            scopes=auth_config.authentication_scopes
        )
    
    @patch('google.auth.load_credentials_from_file')
    def test_authenticate_with_service_account_file_not_found(self, mock_load, auth_config):
        """Test authentication with missing service account file"""
        auth_config.authentication_method = 'service_account'
        auth_config.authentication_service_account_key_file = '/path/to/missing.json'
        
        mock_load.side_effect = FileNotFoundError("File not found")
        
        auth_manager = AuthManager(auth_config)
        with pytest.raises(FileNotFoundError):
            auth_manager.authenticate()
    
    @patch('google.auth.impersonated_credentials.Credentials')
    @patch('google.auth.default')
    def test_authenticate_with_impersonation(self, mock_default, mock_impersonated, auth_config):
        """Test authentication with service account impersonation"""
        auth_config.authentication_impersonate_service_account = 'sa@project.iam.gserviceaccount.com'
        
        mock_source_creds = Mock()
        mock_project = 'test-project'
        mock_default.return_value = (mock_source_creds, mock_project)
        
        mock_impersonated_creds = Mock()
        mock_impersonated.return_value = mock_impersonated_creds
        
        auth_manager = AuthManager(auth_config)
        auth_manager.authenticate()
        
        assert auth_manager.credentials == mock_impersonated_creds
        mock_impersonated.assert_called_once_with(
            source_credentials=mock_source_creds,
            target_principal='sa@project.iam.gserviceaccount.com',
            target_scopes=auth_config.authentication_scopes,
            lifetime=3600
        )
    
    def test_authenticate_invalid_method(self, auth_config):
        """Test authentication with invalid method"""
        auth_config.authentication_method = 'invalid_method'
        
        auth_manager = AuthManager(auth_config)
        with pytest.raises(ValueError, match="Invalid authentication method"):
            auth_manager.authenticate()
    
    @patch('googleapiclient.discovery.build')
    def test_build_service_success(self, mock_build, auth_config):
        """Test successful service building"""
        mock_creds = Mock()
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        auth_manager = AuthManager(auth_config)
        auth_manager.credentials = mock_creds
        
        service = auth_manager.build_service('compute', 'v1')
        
        assert service == mock_service
        mock_build.assert_called_once_with(
            'compute',
            'v1',
            credentials=mock_creds,
            cache_discovery=False
        )
    
    def test_build_service_without_credentials(self, auth_config):
        """Test building service without authentication"""
        auth_manager = AuthManager(auth_config)
        
        with pytest.raises(ValueError, match="Not authenticated"):
            auth_manager.build_service('compute', 'v1')
    
    @patch('googleapiclient.discovery.build')
    def test_build_service_with_http_error(self, mock_build, auth_config):
        """Test service building with HTTP error"""
        mock_creds = Mock()
        mock_build.side_effect = HttpError(Mock(status=404), b'Not found')
        
        auth_manager = AuthManager(auth_config)
        auth_manager.credentials = mock_creds
        
        with pytest.raises(HttpError):
            auth_manager.build_service('invalid', 'v1')
    
    @patch('googleapiclient.discovery.build')
    def test_build_service_caching(self, mock_build, auth_config):
        """Test that services are cached"""
        mock_creds = Mock()
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        auth_manager = AuthManager(auth_config)
        auth_manager.credentials = mock_creds
        
        # Build same service twice
        service1 = auth_manager.build_service('compute', 'v1')
        service2 = auth_manager.build_service('compute', 'v1')
        
        # Should be the same instance (cached)
        assert service1 is service2
        # Should only be called once
        mock_build.assert_called_once()
    
    @patch('googleapiclient.discovery.build')
    def test_build_different_services(self, mock_build, auth_config):
        """Test building different services"""
        mock_creds = Mock()
        mock_service1 = Mock()
        mock_service2 = Mock()
        mock_build.side_effect = [mock_service1, mock_service2]
        
        auth_manager = AuthManager(auth_config)
        auth_manager.credentials = mock_creds
        
        service1 = auth_manager.build_service('compute', 'v1')
        service2 = auth_manager.build_service('storage', 'v1')
        
        assert service1 != service2
        assert mock_build.call_count == 2
    
    def test_refresh_credentials_success(self, auth_config):
        """Test successful credential refresh"""
        mock_creds = Mock()
        mock_creds.expired = True
        mock_creds.refresh = Mock()
        
        auth_manager = AuthManager(auth_config)
        auth_manager.credentials = mock_creds
        
        auth_manager.refresh_credentials()
        
        mock_creds.refresh.assert_called_once()
    
    def test_refresh_credentials_not_expired(self, auth_config):
        """Test refresh when credentials not expired"""
        mock_creds = Mock()
        mock_creds.expired = False
        mock_creds.refresh = Mock()
        
        auth_manager = AuthManager(auth_config)
        auth_manager.credentials = mock_creds
        
        auth_manager.refresh_credentials()
        
        # Should not refresh if not expired
        mock_creds.refresh.assert_not_called()
    
    def test_refresh_credentials_error(self, auth_config):
        """Test credential refresh error"""
        mock_creds = Mock()
        mock_creds.expired = True
        mock_creds.refresh.side_effect = RefreshError("Failed to refresh")
        
        auth_manager = AuthManager(auth_config)
        auth_manager.credentials = mock_creds
        
        with pytest.raises(RefreshError):
            auth_manager.refresh_credentials()
    
    def test_get_access_token(self, auth_config):
        """Test getting access token"""
        mock_creds = Mock()
        mock_creds.token = 'test-token-123'
        
        auth_manager = AuthManager(auth_config)
        auth_manager.credentials = mock_creds
        
        token = auth_manager.get_access_token()
        assert token == 'test-token-123'
    
    def test_get_access_token_without_credentials(self, auth_config):
        """Test getting access token without credentials"""
        auth_manager = AuthManager(auth_config)
        
        token = auth_manager.get_access_token()
        assert token is None
    
    def test_validate_scopes(self, auth_config):
        """Test scope validation"""
        auth_manager = AuthManager(auth_config)
        
        # Should not raise for valid scopes
        auth_manager._validate_scopes()
    
    def test_validate_scopes_empty(self):
        """Test scope validation with empty scopes"""
        config = Config()
        config.authentication_scopes = []
        
        auth_manager = AuthManager(config)
        with pytest.raises(ValueError, match="No authentication scopes"):
            auth_manager._validate_scopes()
    
    def test_validate_scopes_invalid(self):
        """Test scope validation with invalid scopes"""
        config = Config()
        config.authentication_scopes = ['invalid-scope']
        
        auth_manager = AuthManager(config)
        # Should log warning but not raise
        auth_manager._validate_scopes() 