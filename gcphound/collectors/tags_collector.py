"""
Collector for GCP Resource Manager Tags and Tag Bindings
"""

from typing import Dict, Any, List, Optional, Set
from googleapiclient.errors import HttpError
from .base import BaseCollector
from ..utils import get_logger, ProgressLogger


logger = get_logger(__name__)


class TagsCollector(BaseCollector):
    """
    Collects GCP Resource Manager Tags, Tag Values, and Tag Bindings
    
    This is critical for detecting tag-based privilege escalation paths where
    IAM conditions use resource.matchTag() and users have tagUser permissions.
    
    Reference: https://cloud.google.com/iam/docs/conditions-resource-tags
    """
    
    def collect(
        self,
        organization_id: Optional[str] = None,
        project_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Collect tags, tag values, and tag bindings
        
        Args:
            organization_id: Organization ID to scan for tags
            project_ids: List of project IDs to check tag bindings
            
        Returns:
            Dictionary containing tag data
        """
        self._start_collection()
        
        # Initialize data structures
        self._collected_data = {
            'tag_keys': {},
            'tag_values': {},
            'tag_bindings': {},
            'tag_holds': {},
            'iam_conditions_with_tags': []  # IAM conditions that reference tags
        }
        
        try:
            if organization_id:
                # Collect tag keys at organization level
                self._collect_tag_keys(f'organizations/{organization_id}')
            
            # Collect tag bindings for projects
            if project_ids:
                for project_id in project_ids:
                    self._collect_tag_bindings(f'//cloudresourcemanager.googleapis.com/projects/{project_id}')
            
            # Analyze which tags are used in IAM conditions
            self._analyze_tag_usage_in_conditions()
            
        except Exception as e:
            logger.error(f"Error during tags collection: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'collection'
            })
        
        self._end_collection()
        return self.get_collected_data()
    
    def _collect_tag_keys(self, parent: str):
        """
        Collect tag keys under a parent (organization)
        
        Args:
            parent: Parent resource (e.g., organizations/123456)
        """
        logger.info(f"Collecting tag keys for {parent}")
        
        try:
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            
            # List tag keys
            request = service.tagKeys().list(
                parent=parent,
                pageSize=self.config.collection_page_size
            )
            
            for tag_key in self._paginate_list(request, 'tagKeys'):
                key_name = tag_key.get('name')
                
                # Store tag key data
                self._collected_data['tag_keys'][key_name] = {
                    'name': key_name,
                    'namespacedName': tag_key.get('namespacedName'),
                    'shortName': tag_key.get('shortName'),
                    'parent': tag_key.get('parent'),
                    'description': tag_key.get('description'),
                    'createTime': tag_key.get('createTime'),
                    'updateTime': tag_key.get('updateTime'),
                    'etag': tag_key.get('etag')
                }
                
                # Collect tag values for this key
                self._collect_tag_values(key_name)
                
                self._increment_stat('tag_keys_collected')
            
        except HttpError as e:
            logger.error(f"Error collecting tag keys: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'parent': parent
            })
    
    def _collect_tag_values(self, tag_key: str):
        """
        Collect tag values for a tag key
        
        Args:
            tag_key: Tag key name (e.g., tagKeys/123456)
        """
        try:
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            
            # List tag values
            request = service.tagValues().list(
                parent=tag_key,
                pageSize=self.config.collection_page_size
            )
            
            for tag_value in self._paginate_list(request, 'tagValues'):
                value_name = tag_value.get('name')
                
                # Store tag value data
                self._collected_data['tag_values'][value_name] = {
                    'name': value_name,
                    'namespacedName': tag_value.get('namespacedName'),
                    'shortName': tag_value.get('shortName'),
                    'parent': tag_value.get('parent'),
                    'description': tag_value.get('description'),
                    'createTime': tag_value.get('createTime'),
                    'updateTime': tag_value.get('updateTime'),
                    'etag': tag_value.get('etag')
                }
                
                self._increment_stat('tag_values_collected')
            
        except HttpError as e:
            logger.debug(f"Error collecting tag values for {tag_key}: {e}")
    
    def _collect_tag_bindings(self, resource: str):
        """
        Collect tag bindings for a resource
        
        Args:
            resource: Full resource name (e.g., //cloudresourcemanager.googleapis.com/projects/123)
        """
        try:
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            
            # List tag bindings
            request = service.tagBindings().list(
                parent=resource,
                pageSize=self.config.collection_page_size
            )
            
            for binding in self._paginate_list(request, 'tagBindings'):
                binding_name = binding.get('name')
                
                # Store tag binding data
                self._collected_data['tag_bindings'][binding_name] = {
                    'name': binding_name,
                    'parent': binding.get('parent'),
                    'tagValue': binding.get('tagValue'),
                    'tagValueNamespacedName': binding.get('tagValueNamespacedName'),
                    'resource': resource
                }
                
                self._increment_stat('tag_bindings_collected')
            
        except HttpError as e:
            logger.debug(f"Error collecting tag bindings for {resource}: {e}")
    
    def _analyze_tag_usage_in_conditions(self):
        """
        Analyze which tags are referenced in IAM conditions
        
        This helps identify potential privilege escalation paths where
        a user with tagUser permission can satisfy an IAM condition.
        """
        # This would need to be populated from IAM policy analysis
        # Looking for conditions like:
        # - resource.matchTag('tagKeys/123', 'tagValues/456')
        # - resource.hasTagKey('tagKeys/123')
        
        # For now, we'll mark tags that have bindings as potentially used
        for tag_value_name in self._collected_data['tag_values']:
            # Check if this tag value has any bindings
            has_bindings = any(
                binding['tagValue'] == tag_value_name
                for binding in self._collected_data['tag_bindings'].values()
            )
            
            if has_bindings:
                tag_value = self._collected_data['tag_values'][tag_value_name]
                tag_value['hasBindings'] = True
                tag_value['potentiallyUsedInConditions'] = True
    
    def get_tags_for_resource(self, resource: str) -> List[Dict[str, Any]]:
        """
        Get all tags bound to a specific resource
        
        Args:
            resource: Resource name
            
        Returns:
            List of tag bindings
        """
        tags = []
        for binding in self._collected_data['tag_bindings'].values():
            if binding['resource'] == resource:
                tags.append(binding)
        return tags
    
    def get_resources_with_tag(self, tag_value: str) -> List[str]:
        """
        Get all resources that have a specific tag value
        
        Args:
            tag_value: Tag value name
            
        Returns:
            List of resource names
        """
        resources = []
        for binding in self._collected_data['tag_bindings'].values():
            if binding['tagValue'] == tag_value:
                resources.append(binding['resource'])
        return resources 