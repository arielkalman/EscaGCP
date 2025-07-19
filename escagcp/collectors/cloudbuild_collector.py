"""
Collector for Cloud Build configurations and service accounts
"""

from typing import Dict, Any, List, Optional
from googleapiclient.errors import HttpError
from .base import BaseCollector
from ..utils import get_logger


logger = get_logger(__name__)


class CloudBuildCollector(BaseCollector):
    """
    Collects Cloud Build configurations, triggers, and service accounts
    
    This is critical for detecting Cloud Build-based privilege escalation where
    users with cloudbuild.builds.create can execute code as the Cloud Build SA.
    
    Reference: https://cloud.google.com/build/docs/securing-builds/configure-access-control
    """
    
    def collect(
        self,
        project_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Collect Cloud Build data
        
        Args:
            project_ids: List of project IDs to scan
            
        Returns:
            Dictionary containing Cloud Build data
        """
        self._start_collection()
        
        # Initialize data structures
        self._collected_data = {
            'service_accounts': {},  # Cloud Build service accounts per project
            'triggers': {},          # Build triggers
            'worker_pools': {},      # Private worker pools
            'github_connections': {},# GitHub app connections
            'build_configs': []      # Sample build configurations
        }
        
        if not project_ids:
            logger.warning("No project IDs provided for Cloud Build collection")
            self._end_collection()
            return self.get_collected_data()
        
        try:
            for project_id in project_ids:
                self._collect_project_cloud_build(project_id)
            
        except Exception as e:
            logger.error(f"Error during Cloud Build collection: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'collection'
            })
        
        self._end_collection()
        return self.get_collected_data()
    
    def _collect_project_cloud_build(self, project_id: str):
        """
        Collect Cloud Build data for a project
        
        Args:
            project_id: Project ID
        """
        logger.info(f"Collecting Cloud Build data for project {project_id}")
        
        # Get Cloud Build service account
        self._collect_cloud_build_sa(project_id)
        
        # Collect build triggers
        self._collect_build_triggers(project_id)
        
        # Collect worker pools
        self._collect_worker_pools(project_id)
        
        # Collect recent builds to understand patterns
        self._collect_recent_builds(project_id)
    
    def _collect_cloud_build_sa(self, project_id: str):
        """
        Identify the Cloud Build service account for a project
        
        Args:
            project_id: Project ID
        """
        try:
            # Cloud Build uses a default service account
            project_number = self._get_project_number(project_id)
            if project_number:
                default_sa = f"{project_number}@cloudbuild.gserviceaccount.com"
                
                self._collected_data['service_accounts'][project_id] = {
                    'default': default_sa,
                    'project_id': project_id,
                    'project_number': project_number,
                    'type': 'cloud_build_default'
                }
                
                # Try to get custom service accounts from build configs
                self._check_custom_service_accounts(project_id)
                
                self._increment_stat('cloud_build_sas_collected')
            
        except Exception as e:
            logger.debug(f"Error collecting Cloud Build SA for {project_id}: {e}")
    
    def _collect_build_triggers(self, project_id: str):
        """
        Collect Cloud Build triggers
        
        Args:
            project_id: Project ID
        """
        try:
            service = self.auth_manager.build_service('cloudbuild', 'v1')
            
            # List build triggers
            request = service.projects().triggers().list(
                projectId=project_id,
                pageSize=self.config.collection_page_size
            )
            
            for trigger in self._paginate_list(request, 'triggers'):
                trigger_id = trigger.get('id')
                
                # Store trigger data
                self._collected_data['triggers'][f"{project_id}/{trigger_id}"] = {
                    'id': trigger_id,
                    'name': trigger.get('name'),
                    'description': trigger.get('description'),
                    'project_id': project_id,
                    'disabled': trigger.get('disabled', False),
                    'github': trigger.get('github'),
                    'pubsubConfig': trigger.get('pubsubConfig'),
                    'webhookConfig': trigger.get('webhookConfig'),
                    'build': trigger.get('build', {}),
                    'serviceAccount': trigger.get('serviceAccount'),  # Custom SA if specified
                    'createTime': trigger.get('createTime')
                }
                
                self._increment_stat('build_triggers_collected')
            
        except HttpError as e:
            if e.resp.status != 403:  # Ignore permission errors
                logger.debug(f"Error collecting build triggers for {project_id}: {e}")
    
    def _collect_worker_pools(self, project_id: str):
        """
        Collect private worker pools
        
        Args:
            project_id: Project ID
        """
        try:
            service = self.auth_manager.build_service('cloudbuild', 'v1')
            
            # List worker pools
            parent = f"projects/{project_id}/locations/-"
            request = service.projects().locations().workerPools().list(
                parent=parent,
                pageSize=self.config.collection_page_size
            )
            
            response = request.execute()
            for pool in response.get('workerPools', []):
                pool_name = pool.get('name')
                
                # Store worker pool data
                self._collected_data['worker_pools'][pool_name] = {
                    'name': pool_name,
                    'displayName': pool.get('displayName'),
                    'project_id': project_id,
                    'state': pool.get('state'),
                    'privatePoolV1Config': pool.get('privatePoolV1Config', {}),
                    'createTime': pool.get('createTime'),
                    'updateTime': pool.get('updateTime')
                }
                
                self._increment_stat('worker_pools_collected')
            
        except HttpError as e:
            if e.resp.status != 403:
                logger.debug(f"Error collecting worker pools for {project_id}: {e}")
    
    def _collect_recent_builds(self, project_id: str):
        """
        Collect recent builds to understand patterns
        
        Args:
            project_id: Project ID
        """
        try:
            service = self.auth_manager.build_service('cloudbuild', 'v1')
            
            # List recent builds (last 10)
            request = service.projects().builds().list(
                projectId=project_id,
                pageSize=10
            )
            
            response = request.execute()
            for build in response.get('builds', []):
                # Extract relevant build configuration
                build_config = {
                    'id': build.get('id'),
                    'project_id': project_id,
                    'serviceAccount': build.get('serviceAccount'),
                    'options': build.get('options', {}),
                    'substitutions': list(build.get('substitutions', {}).keys()),
                    'tags': build.get('tags', []),
                    'secrets': len(build.get('secrets', [])),
                    'availableSecrets': build.get('availableSecrets'),
                    'logsBucket': build.get('logsBucket')
                }
                
                self._collected_data['build_configs'].append(build_config)
            
        except HttpError as e:
            if e.resp.status != 403:
                logger.debug(f"Error collecting recent builds for {project_id}: {e}")
    
    def _check_custom_service_accounts(self, project_id: str):
        """
        Check for custom service accounts used in builds
        
        Args:
            project_id: Project ID
        """
        # Look through triggers and builds for custom service accounts
        custom_sas = set()
        
        # From triggers
        for trigger in self._collected_data['triggers'].values():
            if trigger.get('project_id') == project_id:
                sa = trigger.get('serviceAccount')
                if sa:
                    custom_sas.add(sa)
        
        # From recent builds
        for build in self._collected_data['build_configs']:
            if build.get('project_id') == project_id:
                sa = build.get('serviceAccount')
                if sa:
                    custom_sas.add(sa)
        
        if custom_sas:
            if project_id not in self._collected_data['service_accounts']:
                self._collected_data['service_accounts'][project_id] = {}
            
            self._collected_data['service_accounts'][project_id]['custom'] = list(custom_sas)
    
    def _get_project_number(self, project_id: str) -> Optional[str]:
        """
        Get project number from project ID
        
        Args:
            project_id: Project ID
            
        Returns:
            Project number or None
        """
        try:
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            project = service.projects().get(name=f"projects/{project_id}").execute()
            return project.get('name', '').split('/')[-1]  # projects/NUMBER
        except Exception as e:
            logger.debug(f"Could not get project number for {project_id}: {e}")
            return None 