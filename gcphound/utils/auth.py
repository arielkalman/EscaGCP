"""
Authentication manager for GCP
"""

import os
from typing import Optional, Dict, Any
import google.auth
from google.auth import impersonated_credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from .logger import get_logger
from .config import Config


logger = get_logger(__name__)


class AuthManager:
    """
    Manages authentication for GCP APIs
    """
    
    def __init__(self, config: Config):
        """
        Initialize authentication manager
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.credentials = None
        self.impersonate_service_account = config.authentication_impersonate_service_account
        self._service_cache = {}
    
    def authenticate(self):
        """
        Authenticate based on configured method
        """
        self._validate_scopes()
        
        if self.config.authentication_method == 'adc':
            self._authenticate_adc()
        elif self.config.authentication_method == 'service_account':
            self._authenticate_service_account()
        else:
            raise ValueError(f"Invalid authentication method: {self.config.authentication_method}")
        
        # Apply impersonation if configured
        if self.impersonate_service_account:
            self._apply_impersonation()
    
    def _authenticate_adc(self):
        """Authenticate using Application Default Credentials"""
        logger.info("Authenticating with Application Default Credentials")
        credentials, project = google.auth.default(scopes=self.config.authentication_scopes)
        self.credentials = credentials
    
    def _authenticate_service_account(self):
        """Authenticate using service account key file"""
        if not self.config.authentication_service_account_key_file:
            raise ValueError("Service account key file not specified")
        
        logger.info(f"Authenticating with service account key: {self.config.authentication_service_account_key_file}")
        credentials, project = google.auth.load_credentials_from_file(
            self.config.authentication_service_account_key_file,
            scopes=self.config.authentication_scopes
        )
        self.credentials = credentials
    
    def _apply_impersonation(self):
        """Apply service account impersonation"""
        logger.info(f"Impersonating service account: {self.impersonate_service_account}")
        self.credentials = impersonated_credentials.Credentials(
            source_credentials=self.credentials,
            target_principal=self.impersonate_service_account,
            target_scopes=self.config.authentication_scopes,
            lifetime=3600
        )
    
    def build_service(self, service_name: str, version: str = 'v1'):
        """
        Build a GCP API service client
        
        Args:
            service_name: Name of the service (e.g., 'compute')
            version: API version
            
        Returns:
            Service client
        """
        if not self.credentials:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        cache_key = f"{service_name}:{version}"
        if cache_key in self._service_cache:
            return self._service_cache[cache_key]
        
        logger.debug(f"Building service: {service_name} {version}")
        service = discovery.build(
            service_name,
            version,
            credentials=self.credentials,
            cache_discovery=False
        )
        
        self._service_cache[cache_key] = service
        return service
    
    def refresh_credentials(self):
        """Refresh credentials if expired"""
        if self.credentials and hasattr(self.credentials, 'expired') and self.credentials.expired:
            logger.info("Refreshing expired credentials")
            self.credentials.refresh(Request())
    
    def get_access_token(self) -> Optional[str]:
        """Get current access token"""
        if self.credentials and hasattr(self.credentials, 'token'):
            return self.credentials.token
        return None
    
    def _validate_scopes(self):
        """Validate authentication scopes"""
        if not self.config.authentication_scopes:
            raise ValueError("No authentication scopes configured")
        
        # Check for common invalid scopes
        for scope in self.config.authentication_scopes:
            if not scope.startswith('https://'):
                logger.warning(f"Invalid scope format: {scope}") 