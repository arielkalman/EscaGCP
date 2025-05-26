"""
Base collector class for GCPHound
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Iterator
from pathlib import Path
from datetime import datetime
from googleapiclient.errors import HttpError
from ..utils import get_logger, AuthManager, retry_with_backoff, RateLimiter, Config


logger = get_logger(__name__)


class BaseCollector(ABC):
    """
    Abstract base class for all collectors
    """
    
    def __init__(self, auth_manager: AuthManager, config: Config):
        """
        Initialize base collector
        
        Args:
            auth_manager: Authentication manager instance
            config: Configuration instance
        """
        self.auth_manager = auth_manager
        self.config = config
        self.rate_limiter = RateLimiter(
            requests_per_second=config.performance_rate_limit_requests_per_second,
            burst_size=config.performance_rate_limit_burst_size
        )
        self._collected_data = {}
        self._metadata = {
            'collector': self.__class__.__name__,
            'start_time': None,
            'end_time': None,
            'errors': [],
            'stats': {}
        }
    
    @abstractmethod
    def collect(self, **kwargs) -> Dict[str, Any]:
        """
        Collect data from GCP APIs
        
        Returns:
            Dictionary of collected data
        """
        pass
    
    def save_to_file(self, output_dir: str, filename: Optional[str] = None) -> str:
        """
        Save collected data to file
        
        Args:
            output_dir: Output directory path
            filename: Optional filename (defaults to collector name + timestamp)
            
        Returns:
            Path to saved file
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.__class__.__name__.lower()}_{timestamp}.json"
        
        # Full file path
        file_path = output_path / filename
        
        # Prepare data with metadata
        output_data = {
            'metadata': self._metadata,
            'data': self._collected_data
        }
        
        # Save to file
        logger.info(f"Saving collected data to: {file_path}")
        with open(file_path, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        return str(file_path)
    
    def _paginate_list(
        self,
        request,
        response_field: str,
        max_pages: Optional[int] = None
    ) -> Iterator[Any]:
        """
        Paginate through API list responses
        
        Args:
            request: Initial request object
            response_field: Field name containing items in response
            max_pages: Maximum number of pages to fetch
            
        Yields:
            Items from all pages
        """
        page_count = 0
        
        while request is not None:
            # Rate limit the request
            with self.rate_limiter:
                try:
                    response = self._execute_request(request)
                except HttpError as e:
                    logger.error(f"Error during pagination: {e}")
                    self._metadata['errors'].append({
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    break
            
            # Yield items from this page
            items = response.get(response_field, [])
            for item in items:
                yield item
            
            # Check page limit
            page_count += 1
            if max_pages and page_count >= max_pages:
                logger.info(f"Reached maximum page limit: {max_pages}")
                break
            
            # Get next page
            request = getattr(request, 'list_next', lambda x, y: None)(request, response)
    
    def _execute_request(self, request) -> Dict[str, Any]:
        """
        Execute an API request with retry logic
        
        Args:
            request: API request object
            
        Returns:
            Response dictionary
        """
        @retry_with_backoff(max_retries=3)
        def _do_execute():
            return request.execute()
        
        return _do_execute()
    
    def _start_collection(self):
        """Mark the start of collection"""
        self._metadata['start_time'] = datetime.now().isoformat()
        logger.info(f"Starting {self.__class__.__name__} collection")
    
    def _end_collection(self):
        """Mark the end of collection"""
        self._metadata['end_time'] = datetime.now().isoformat()
        duration = (
            datetime.fromisoformat(self._metadata['end_time']) -
            datetime.fromisoformat(self._metadata['start_time'])
        ).total_seconds()
        self._metadata['duration_seconds'] = duration
        logger.info(
            f"Completed {self.__class__.__name__} collection in {duration:.2f} seconds"
        )
    
    def _update_stats(self, key: str, value: Any):
        """
        Update collection statistics
        
        Args:
            key: Statistic key
            value: Statistic value
        """
        self._metadata['stats'][key] = value
    
    def _increment_stat(self, key: str, increment: int = 1):
        """
        Increment a collection statistic
        
        Args:
            key: Statistic key
            increment: Amount to increment
        """
        current = self._metadata['stats'].get(key, 0)
        self._metadata['stats'][key] = current + increment
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get collection metadata
        
        Returns:
            Metadata dictionary
        """
        return self._metadata.copy()
    
    def get_collected_data(self) -> Dict[str, Any]:
        """
        Get collected data
        
        Returns:
            Collected data dictionary
        """
        return self._collected_data.copy()
    
    def _normalize_identity(self, identity: str) -> str:
        """
        Normalize an identity string to a consistent format
        
        Args:
            identity: Identity string (e.g., user:alice@example.com)
            
        Returns:
            Normalized identity string
        """
        # Already normalized if it has a prefix
        if ':' in identity:
            return identity
        
        # Determine type and add prefix
        if '@' in identity:
            if identity.endswith('.iam.gserviceaccount.com'):
                return f"serviceAccount:{identity}"
            elif identity.startswith('group:'):
                return identity
            else:
                return f"user:{identity}"
        
        # Assume it's a special identity
        return identity
    
    def _extract_project_id(self, resource_name: str) -> Optional[str]:
        """
        Extract project ID from a resource name
        
        Args:
            resource_name: Full resource name
            
        Returns:
            Project ID or None
        """
        # Common patterns for project extraction
        if 'projects/' in resource_name:
            # Handle both /projects/ and projects/ at the start
            if resource_name.startswith('projects/'):
                parts = resource_name.split('/')
                if len(parts) > 1:
                    return parts[1]
            elif '/projects/' in resource_name:
                parts = resource_name.split('/projects/')
                if len(parts) > 1:
                    project_part = parts[1].split('/')[0]
                    return project_part
        
        return None 