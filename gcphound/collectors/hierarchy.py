"""
Collector for GCP resource hierarchy (Organizations, Folders, Projects)
"""

from typing import Dict, Any, List, Optional, Set
from googleapiclient.errors import HttpError
from .base import BaseCollector
from ..utils import get_logger, ProgressLogger


logger = get_logger(__name__)


class HierarchyCollector(BaseCollector):
    """
    Collects GCP resource hierarchy information
    """
    
    def collect(
        self,
        organization_id: Optional[str] = None,
        folder_ids: Optional[List[str]] = None,
        project_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Collect hierarchy data
        
        Args:
            organization_id: Organization ID to scan (e.g., '123456789')
            folder_ids: List of folder IDs to scan
            project_ids: List of project IDs to scan (if None, discovers all)
            
        Returns:
            Dictionary containing hierarchy data
        """
        self._start_collection()
        
        # Initialize data structures
        self._collected_data = {
            'organizations': {},
            'folders': {},
            'projects': {},
            'hierarchy': {}  # parent-child relationships
        }
        
        try:
            # Collect organization if specified
            if organization_id and self.config.collection_include_organization:
                self._collect_organization(organization_id)
            
            # Collect folders
            if self.config.collection_include_folders:
                if folder_ids:
                    for folder_id in folder_ids:
                        self._collect_folder(folder_id)
                elif organization_id:
                    # Discover all folders in organization
                    self._collect_all_folders(f'organizations/{organization_id}')
            
            # Collect projects
            if project_ids is not None:
                # Collect specific projects
                for project_id in project_ids:
                    self._collect_project(project_id)
            else:
                # Discover all accessible projects
                self._collect_all_projects()
            
            # Build hierarchy relationships
            self._build_hierarchy()
            
        except Exception as e:
            logger.error(f"Error during hierarchy collection: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'collection'
            })
        
        self._end_collection()
        return self.get_collected_data()
    
    def _collect_organization(self, org_id: str):
        """
        Collect organization information
        
        Args:
            org_id: Organization ID
        """
        logger.info(f"Collecting organization: {org_id}")
        
        try:
            # Build service
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            
            # Get organization details
            org_name = f"organizations/{org_id}"
            request = service.organizations().get(name=org_name)
            
            with self.rate_limiter:
                org = self._execute_request(request)
            
            # Store organization data
            self._collected_data['organizations'][org_id] = {
                'name': org.get('name'),
                'displayName': org.get('displayName'),
                'state': org.get('state'),
                'createTime': org.get('createTime'),
                'updateTime': org.get('updateTime'),
                'etag': org.get('etag')
            }
            
            self._increment_stat('organizations_collected')
            logger.info(f"Collected organization: {org.get('displayName', org_id)}")
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"No permission to access organization {org_id}")
            else:
                logger.error(f"Error collecting organization {org_id}: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'organization_id': org_id
            })
    
    def _collect_folder(self, folder_id: str):
        """
        Collect folder information
        
        Args:
            folder_id: Folder ID
        """
        try:
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            
            # Get folder details
            folder_name = f"folders/{folder_id}"
            request = service.folders().get(name=folder_name)
            
            with self.rate_limiter:
                folder = self._execute_request(request)
            
            # Store folder data
            self._collected_data['folders'][folder_id] = {
                'name': folder.get('name'),
                'displayName': folder.get('displayName'),
                'parent': folder.get('parent'),
                'state': folder.get('state'),
                'createTime': folder.get('createTime'),
                'updateTime': folder.get('updateTime'),
                'etag': folder.get('etag')
            }
            
            self._increment_stat('folders_collected')
            
        except HttpError as e:
            logger.error(f"Error collecting folder {folder_id}: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'folder_id': folder_id
            })
    
    def _collect_all_folders(self, parent: str):
        """
        Recursively collect all folders under a parent
        
        Args:
            parent: Parent resource (organizations/123 or folders/456)
        """
        logger.info(f"Discovering folders under: {parent}")
        
        try:
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            
            # List folders
            request = service.folders().list(
                parent=parent,
                pageSize=self.config.collection_page_size
            )
            
            # Collect all folders
            folder_count = 0
            for folder in self._paginate_list(request, 'folders', self.config.collection_max_pages):
                folder_id = folder['name'].split('/')[-1]
                
                # Store folder data
                self._collected_data['folders'][folder_id] = {
                    'name': folder.get('name'),
                    'displayName': folder.get('displayName'),
                    'parent': folder.get('parent'),
                    'state': folder.get('state'),
                    'createTime': folder.get('createTime'),
                    'updateTime': folder.get('updateTime'),
                    'etag': folder.get('etag')
                }
                
                folder_count += 1
                
                # Recursively collect subfolders
                if folder.get('state') == 'ACTIVE':
                    self._collect_all_folders(folder['name'])
            
            self._increment_stat('folders_collected', folder_count)
            logger.info(f"Collected {folder_count} folders under {parent}")
            
        except HttpError as e:
            logger.error(f"Error listing folders under {parent}: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'parent': parent
            })
    
    def _collect_project(self, project_id: str):
        """
        Collect project information
        
        Args:
            project_id: Project ID
        """
        try:
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            
            # Get project details
            project_name = f"projects/{project_id}"
            request = service.projects().get(name=project_name)
            
            with self.rate_limiter:
                project = self._execute_request(request)
            
            # Store project data
            self._collected_data['projects'][project_id] = {
                'name': project.get('name'),
                'projectId': project.get('projectId'),
                'displayName': project.get('displayName'),
                'parent': project.get('parent'),
                'state': project.get('state'),
                'createTime': project.get('createTime'),
                'updateTime': project.get('updateTime'),
                'deleteTime': project.get('deleteTime'),
                'etag': project.get('etag'),
                'labels': project.get('labels', {})
            }
            
            self._increment_stat('projects_collected')
            
        except HttpError as e:
            logger.error(f"Error collecting project {project_id}: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'project_id': project_id
            })
    
    def _collect_all_projects(self):
        """
        Collect all accessible projects
        """
        logger.info("Discovering all accessible projects")
        
        try:
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            
            # List all projects
            request = service.projects().list(
                pageSize=self.config.collection_page_size
            )
            
            # Track progress
            project_count = 0
            max_projects = self.config.collection_max_projects
            
            with ProgressLogger(
                total=max_projects or 100,
                description="Collecting projects"
            ) as progress:
                
                for project in self._paginate_list(
                    request,
                    'projects',
                    self.config.collection_max_pages
                ):
                    # Skip deleted projects
                    if project.get('state') != 'ACTIVE':
                        continue
                    
                    project_id = project.get('projectId')
                    
                    # Store project data
                    self._collected_data['projects'][project_id] = {
                        'name': project.get('name'),
                        'projectId': project_id,
                        'displayName': project.get('displayName'),
                        'parent': project.get('parent'),
                        'state': project.get('state'),
                        'createTime': project.get('createTime'),
                        'updateTime': project.get('updateTime'),
                        'deleteTime': project.get('deleteTime'),
                        'etag': project.get('etag'),
                        'labels': project.get('labels', {})
                    }
                    
                    project_count += 1
                    progress.update(1)
                    
                    # Check project limit
                    if max_projects and project_count >= max_projects:
                        logger.info(f"Reached project limit: {max_projects}")
                        break
            
            self._update_stats('projects_collected', project_count)
            logger.info(f"Collected {project_count} projects")
            
        except HttpError as e:
            logger.error(f"Error listing projects: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'project_discovery'
            })
    
    def _build_hierarchy(self):
        """
        Build parent-child relationships in the hierarchy
        """
        logger.info("Building hierarchy relationships")
        
        hierarchy = {
            'organizations': {},
            'folders': {},
            'projects': {}
        }
        
        # Build organization hierarchy
        for org_id, org_data in self._collected_data['organizations'].items():
            hierarchy['organizations'][org_id] = {
                'folders': [],
                'projects': []
            }
        
        # Build folder hierarchy
        for folder_id, folder_data in self._collected_data['folders'].items():
            parent = folder_data.get('parent', '')
            
            # Initialize folder entry
            if folder_id not in hierarchy['folders']:
                hierarchy['folders'][folder_id] = {
                    'parent': parent,
                    'folders': [],
                    'projects': []
                }
            else:
                hierarchy['folders'][folder_id]['parent'] = parent
            
            # Add to parent's children
            if parent and parent.startswith('organizations/'):
                org_id = parent.split('/')[-1]
                if org_id in hierarchy['organizations']:
                    hierarchy['organizations'][org_id]['folders'].append(folder_id)
            elif parent and parent.startswith('folders/'):
                parent_folder_id = parent.split('/')[-1]
                if parent_folder_id not in hierarchy['folders']:
                    hierarchy['folders'][parent_folder_id] = {
                        'parent': None,
                        'folders': [],
                        'projects': []
                    }
                hierarchy['folders'][parent_folder_id]['folders'].append(folder_id)
        
        # Build project hierarchy
        for project_id, project_data in self._collected_data['projects'].items():
            parent = project_data.get('parent', '')
            
            # Add to parent's children
            if parent and parent.startswith('organizations/'):
                org_id = parent.split('/')[-1]
                if org_id in hierarchy['organizations']:
                    hierarchy['organizations'][org_id]['projects'].append(project_id)
            elif parent and parent.startswith('folders/'):
                folder_id = parent.split('/')[-1]
                if folder_id not in hierarchy['folders']:
                    hierarchy['folders'][folder_id] = {
                        'parent': None,
                        'folders': [],
                        'projects': []
                    }
                hierarchy['folders'][folder_id]['projects'].append(project_id)
            
            # Store project parent
            hierarchy['projects'][project_id] = {
                'parent': parent
            }
        
        self._collected_data['hierarchy'] = hierarchy
        logger.info("Hierarchy relationships built")
    
    def get_project_ancestors(self, project_id: str) -> List[str]:
        """
        Get all ancestors of a project (folders and organization)
        
        Args:
            project_id: Project ID
            
        Returns:
            List of ancestor resource names
        """
        ancestors = []
        
        if project_id not in self._collected_data['projects']:
            return ancestors
        
        current = self._collected_data['projects'][project_id].get('parent')
        
        while current:
            ancestors.append(current)
            
            if current.startswith('folders/'):
                folder_id = current.split('/')[-1]
                if folder_id in self._collected_data['folders']:
                    current = self._collected_data['folders'][folder_id].get('parent')
                else:
                    break
            else:
                break
        
        return ancestors 