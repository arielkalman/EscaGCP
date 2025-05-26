"""
Collector for identity information (users, groups, service accounts)
"""

from typing import Dict, Any, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.errors import HttpError
from .base import BaseCollector
from ..utils import get_logger, ProgressLogger


logger = get_logger(__name__)


class IdentityCollector(BaseCollector):
    """
    Collects identity information including users, groups, and service accounts
    """
    
    def collect(
        self,
        project_ids: List[str],
        organization_id: Optional[str] = None,
        collect_groups: bool = True,
        collect_service_accounts: bool = True
    ) -> Dict[str, Any]:
        """
        Collect identity data
        
        Args:
            project_ids: List of project IDs to collect service accounts from
            organization_id: Organization ID for group collection
            collect_groups: Whether to collect group information
            collect_service_accounts: Whether to collect service account information
            
        Returns:
            Dictionary containing identity data
        """
        self._start_collection()
        
        # Initialize data structures
        self._collected_data = {
            'service_accounts': {},
            'groups': {},
            'group_memberships': {},  # group -> members
            'users': {},  # Discovered users
            'identity_summary': {
                'by_type': {
                    'users': set(),
                    'service_accounts': set(),
                    'groups': set()
                }
            }
        }
        
        try:
            # Collect service accounts
            if collect_service_accounts:
                self._collect_service_accounts(project_ids)
            
            # Collect groups (requires Cloud Identity API)
            if collect_groups and organization_id:
                self._collect_groups(organization_id)
            
            # Build identity summary
            self._build_identity_summary()
            
        except Exception as e:
            logger.error(f"Error during identity collection: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'collection'
            })
        
        self._end_collection()
        return self.get_collected_data()
    
    def _collect_service_accounts(self, project_ids: List[str]):
        """
        Collect service accounts from all projects
        """
        logger.info(f"Collecting service accounts from {len(project_ids)} projects")
        
        # Use thread pool for concurrent collection
        with ThreadPoolExecutor(
            max_workers=self.config.performance_max_concurrent_requests
        ) as executor:
            futures = {
                executor.submit(self._collect_project_service_accounts, project_id): project_id
                for project_id in project_ids
            }
            
            with ProgressLogger(
                total=len(futures),
                description="Collecting service accounts"
            ) as progress:
                for future in futures:
                    project_id = futures[future]
                    try:
                        future.result()
                        progress.update(1)
                    except Exception as e:
                        logger.error(f"Error collecting service accounts from {project_id}: {e}")
                        self._metadata['errors'].append({
                            'error': str(e),
                            'project_id': project_id
                        })
    
    def _collect_project_service_accounts(self, project_id: str):
        """
        Collect service accounts from a single project
        """
        try:
            service = self.auth_manager.build_service('iam', 'v1')
            
            # List service accounts
            request = service.projects().serviceAccounts().list(
                name=f"projects/{project_id}",
                pageSize=self.config.collection_page_size
            )
            
            sa_count = 0
            for sa in self._paginate_list(request, 'accounts'):
                sa_email = sa.get('email')
                
                # Store service account data
                self._collected_data['service_accounts'][sa_email] = {
                    'name': sa.get('name'),
                    'email': sa_email,
                    'displayName': sa.get('displayName'),
                    'description': sa.get('description'),
                    'projectId': project_id,
                    'uniqueId': sa.get('uniqueId'),
                    'oauth2ClientId': sa.get('oauth2ClientId'),
                    'disabled': sa.get('disabled', False),
                    'etag': sa.get('etag')
                }
                
                # Also collect service account keys
                self._collect_service_account_keys(project_id, sa_email)
                
                sa_count += 1
            
            self._increment_stat('service_accounts_collected', sa_count)
            logger.debug(f"Collected {sa_count} service accounts from project {project_id}")
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"No permission to list service accounts in project {project_id}")
            else:
                raise
    
    def _collect_service_account_keys(self, project_id: str, sa_email: str):
        """
        Collect keys for a service account
        """
        try:
            service = self.auth_manager.build_service('iam', 'v1')
            
            # List keys
            request = service.projects().serviceAccounts().keys().list(
                name=f"projects/{project_id}/serviceAccounts/{sa_email}"
            )
            
            with self.rate_limiter:
                response = self._execute_request(request)
            
            keys = response.get('keys', [])
            
            # Store key information (without the actual key data for security)
            if sa_email in self._collected_data['service_accounts']:
                self._collected_data['service_accounts'][sa_email]['keys'] = [
                    {
                        'name': key.get('name'),
                        'keyAlgorithm': key.get('keyAlgorithm'),
                        'keyOrigin': key.get('keyOrigin'),
                        'keyType': key.get('keyType'),
                        'validAfterTime': key.get('validAfterTime'),
                        'validBeforeTime': key.get('validBeforeTime'),
                        'disabled': key.get('disabled', False)
                    }
                    for key in keys
                ]
            
        except HttpError as e:
            logger.debug(f"Error collecting keys for service account {sa_email}: {e}")
    
    def _collect_groups(self, organization_id: str):
        """
        Collect groups using Cloud Identity API
        """
        logger.info(f"Collecting groups for organization {organization_id}")
        
        try:
            # Build Cloud Identity service
            service = self.auth_manager.build_service('cloudidentity', 'v1')
            
            # List groups
            parent = f"customers/{organization_id}"
            request = service.groups().list(
                parent=parent,
                pageSize=self.config.collection_page_size
            )
            
            group_count = 0
            with ProgressLogger(
                total=100,  # Estimate
                description="Collecting groups"
            ) as progress:
                
                for group in self._paginate_list(request, 'groups'):
                    group_key = group.get('groupKey', {})
                    group_id = group_key.get('id')
                    
                    if not group_id:
                        continue
                    
                    # Store group data
                    self._collected_data['groups'][group_id] = {
                        'name': group.get('name'),
                        'groupKey': group_key,
                        'displayName': group.get('displayName'),
                        'description': group.get('description'),
                        'createTime': group.get('createTime'),
                        'updateTime': group.get('updateTime'),
                        'labels': group.get('labels', {}),
                        'parent': group.get('parent')
                    }
                    
                    # Collect group members
                    self._collect_group_members(group_id)
                    
                    group_count += 1
                    progress.update(1)
            
            self._update_stats('groups_collected', group_count)
            logger.info(f"Collected {group_count} groups")
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"No permission to access Cloud Identity API for org {organization_id}")
            else:
                logger.error(f"Error collecting groups: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'group_collection'
            })
    
    def _collect_group_members(self, group_id: str):
        """
        Collect members of a group
        """
        try:
            service = self.auth_manager.build_service('cloudidentity', 'v1')
            
            # List group members
            request = service.groups().memberships().list(
                parent=f"groups/{group_id}",
                pageSize=self.config.collection_page_size
            )
            
            members = []
            for membership in self._paginate_list(request, 'memberships'):
                member_key = membership.get('preferredMemberKey', {})
                member_id = member_key.get('id')
                
                if member_id:
                    member_info = {
                        'id': member_id,
                        'type': membership.get('type'),
                        'roles': [role.get('name') for role in membership.get('roles', [])],
                        'createTime': membership.get('createTime'),
                        'updateTime': membership.get('updateTime')
                    }
                    members.append(member_info)
                    
                    # Track discovered users
                    if '@' in member_id and not member_id.endswith('.gserviceaccount.com'):
                        self._collected_data['users'][member_id] = {
                            'email': member_id,
                            'discovered_from': 'group_membership',
                            'groups': [group_id]
                        }
            
            # Store group membership
            self._collected_data['group_memberships'][group_id] = members
            
        except HttpError as e:
            logger.debug(f"Error collecting members for group {group_id}: {e}")
    
    def _build_identity_summary(self):
        """
        Build summary of all discovered identities
        """
        logger.info("Building identity summary")
        
        # Collect all service accounts
        for sa_email in self._collected_data['service_accounts']:
            self._collected_data['identity_summary']['by_type']['service_accounts'].add(
                f"serviceAccount:{sa_email}"
            )
        
        # Collect all groups
        for group_id in self._collected_data['groups']:
            self._collected_data['identity_summary']['by_type']['groups'].add(
                f"group:{group_id}"
            )
        
        # Collect all users
        for user_email in self._collected_data['users']:
            self._collected_data['identity_summary']['by_type']['users'].add(
                f"user:{user_email}"
            )
        
        # Convert sets to lists for JSON serialization
        for identity_type in self._collected_data['identity_summary']['by_type']:
            self._collected_data['identity_summary']['by_type'][identity_type] = list(
                self._collected_data['identity_summary']['by_type'][identity_type]
            )
        
        # Update stats
        self._update_stats('total_identities', sum(
            len(identities) 
            for identities in self._collected_data['identity_summary']['by_type'].values()
        ))
    
    def get_service_account_details(self, sa_email: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific service account
        
        Args:
            sa_email: Service account email
            
        Returns:
            Service account details or None
        """
        return self._collected_data['service_accounts'].get(sa_email)
    
    def get_group_members(self, group_id: str) -> List[Dict[str, Any]]:
        """
        Get members of a specific group
        
        Args:
            group_id: Group ID
            
        Returns:
            List of group members
        """
        return self._collected_data['group_memberships'].get(group_id, []) 