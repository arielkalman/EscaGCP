"""
Collector for IAM policies, bindings, and roles
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from googleapiclient.errors import HttpError
from .base import BaseCollector
from ..utils import get_logger, ProgressLogger


logger = get_logger(__name__)


class IAMCollector(BaseCollector):
    """
    Collects IAM policies, bindings, and role definitions
    """
    
    def collect(
        self,
        project_ids: List[str] = None,
        organization_id: Optional[str] = None,
        folder_ids: Optional[List[str]] = None,
        collect_custom_roles: bool = True,
        collect_predefined_roles: bool = True
    ) -> Dict[str, Any]:
        """
        Collect IAM data
        
        Args:
            project_ids: List of project IDs to collect IAM policies for
            organization_id: Organization ID for org-level policies
            folder_ids: List of folder IDs for folder-level policies
            collect_custom_roles: Whether to collect custom role definitions
            collect_predefined_roles: Whether to collect predefined role definitions
            
        Returns:
            Dictionary containing IAM data
        """
        self._start_collection()
        
        # Initialize data structures
        self._collected_data = {
            'policies': {
                'organizations': {},
                'folders': {},
                'projects': {}
            },
            'roles': {
                'predefined': {},
                'custom': {}
            },
            'bindings_summary': {
                'by_member': {},  # member -> list of bindings
                'by_role': {},    # role -> list of bindings
                'by_resource': {} # resource -> list of bindings
            }
        }
        
        try:
            # Collect IAM policies
            if project_ids:
                self._collect_iam_policies(project_ids, organization_id, folder_ids)
            elif organization_id or folder_ids:
                self._collect_iam_policies([], organization_id, folder_ids)
            
            # Collect role definitions
            if collect_predefined_roles or collect_custom_roles:
                self._collect_roles(
                    project_ids,
                    organization_id,
                    collect_custom_roles,
                    collect_predefined_roles
                )
            
            # Build binding summaries
            self._build_binding_summaries()
            
            # Analyze service account impersonation
            self._analyze_impersonation()
            
        except Exception as e:
            logger.error(f"Error during IAM collection: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'collection'
            })
        
        self._end_collection()
        return self.get_collected_data()
    
    def _collect_iam_policies(
        self,
        project_ids: List[str],
        organization_id: Optional[str],
        folder_ids: Optional[List[str]]
    ):
        """
        Collect IAM policies for all resources
        """
        logger.info("Collecting IAM policies")
        
        # Use thread pool for concurrent collection
        with ThreadPoolExecutor(
            max_workers=self.config.performance_max_concurrent_requests
        ) as executor:
            futures = []
            
            # Submit organization policy collection
            if organization_id and self.config.collection_include_organization:
                future = executor.submit(
                    self._collect_organization_iam_policy,
                    organization_id
                )
                futures.append(('organization', organization_id, future))
            
            # Submit folder policy collection
            if folder_ids and self.config.collection_include_folders:
                for folder_id in folder_ids:
                    future = executor.submit(
                        self._collect_folder_iam_policy,
                        folder_id
                    )
                    futures.append(('folder', folder_id, future))
            
            # Submit project policy collection
            for project_id in project_ids:
                future = executor.submit(
                    self._collect_project_iam_policy,
                    project_id
                )
                futures.append(('project', project_id, future))
            
            # Process results
            with ProgressLogger(
                total=len(futures),
                description="Collecting IAM policies"
            ) as progress:
                for resource_type, resource_id, future in futures:
                    try:
                        future.result()
                        progress.update(1)
                    except Exception as e:
                        logger.error(
                            f"Error collecting {resource_type} {resource_id} policy: {e}"
                        )
                        self._metadata['errors'].append({
                            'error': str(e),
                            'resource_type': resource_type,
                            'resource_id': resource_id
                        })
    
    def _collect_organization_iam_policy(self, org_id: str):
        """
        Collect organization-level IAM policy
        """
        try:
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            
            resource = f"organizations/{org_id}"
            request = service.organizations().getIamPolicy(
                resource=resource,
                body={'options': {'requestedPolicyVersion': 3}}
            )
            
            with self.rate_limiter:
                policy = self._execute_request(request)
            
            # Store policy
            self._collected_data['policies']['organizations'][org_id] = {
                'resource': resource,
                'bindings': policy.get('bindings', []),
                'etag': policy.get('etag'),
                'version': policy.get('version', 1),
                'auditConfigs': policy.get('auditConfigs', [])
            }
            
            self._increment_stat('organization_policies_collected')
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"No permission to access organization {org_id} IAM policy")
            else:
                raise
    
    def _collect_folder_iam_policy(self, folder_id: str):
        """
        Collect folder-level IAM policy
        """
        try:
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            
            resource = f"folders/{folder_id}"
            request = service.folders().getIamPolicy(
                resource=resource,
                body={'options': {'requestedPolicyVersion': 3}}
            )
            
            with self.rate_limiter:
                policy = self._execute_request(request)
            
            # Store policy
            self._collected_data['policies']['folders'][folder_id] = {
                'resource': resource,
                'bindings': policy.get('bindings', []),
                'etag': policy.get('etag'),
                'version': policy.get('version', 1),
                'auditConfigs': policy.get('auditConfigs', [])
            }
            
            self._increment_stat('folder_policies_collected')
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"No permission to access folder {folder_id} IAM policy")
            else:
                raise
    
    def _collect_project_iam_policy(self, project_id: str):
        """
        Collect project-level IAM policy
        """
        try:
            service = self.auth_manager.build_service('cloudresourcemanager', 'v3')
            
            resource = f"projects/{project_id}"
            request = service.projects().getIamPolicy(
                resource=resource,
                body={'options': {'requestedPolicyVersion': 3}}
            )
            
            with self.rate_limiter:
                policy = self._execute_request(request)
            
            # Store policy
            self._collected_data['policies']['projects'][project_id] = {
                'resource': resource,
                'bindings': policy.get('bindings', []),
                'etag': policy.get('etag'),
                'version': policy.get('version', 1),
                'auditConfigs': policy.get('auditConfigs', [])
            }
            
            self._increment_stat('project_policies_collected')
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"No permission to access project {project_id} IAM policy")
            else:
                raise
    
    def _collect_roles(
        self,
        project_ids: List[str],
        organization_id: Optional[str],
        collect_custom: bool,
        collect_predefined: bool
    ):
        """
        Collect role definitions
        """
        logger.info("Collecting role definitions")
        
        # Collect predefined roles
        if collect_predefined:
            self._collect_predefined_roles()
        
        # Collect custom roles
        if collect_custom:
            # Organization-level custom roles
            if organization_id:
                self._collect_custom_roles(f"organizations/{organization_id}")
            
            # Project-level custom roles
            for project_id in project_ids:
                self._collect_custom_roles(f"projects/{project_id}")
    
    def _collect_predefined_roles(self):
        """
        Collect predefined role definitions
        """
        logger.info("Collecting predefined roles")
        
        try:
            service = self.auth_manager.build_service('iam', 'v1')
            
            # Get list of roles we've seen in bindings
            roles_to_fetch = set()
            for resource_type in self._collected_data['policies']:
                for resource_id, policy in self._collected_data['policies'][resource_type].items():
                    for binding in policy.get('bindings', []):
                        role = binding.get('role', '')
                        if role.startswith('roles/'):
                            roles_to_fetch.add(role)
            
            # Fetch role definitions
            with ProgressLogger(
                total=len(roles_to_fetch),
                description="Fetching predefined roles"
            ) as progress:
                for role_name in roles_to_fetch:
                    try:
                        request = service.roles().get(name=role_name)
                        
                        with self.rate_limiter:
                            role = self._execute_request(request)
                        
                        # Store role definition
                        self._collected_data['roles']['predefined'][role_name] = {
                            'name': role.get('name'),
                            'title': role.get('title'),
                            'description': role.get('description'),
                            'includedPermissions': role.get('includedPermissions', []),
                            'stage': role.get('stage'),
                            'etag': role.get('etag')
                        }
                        
                        progress.update(1)
                        
                    except HttpError as e:
                        logger.warning(f"Error fetching role {role_name}: {e}")
            
            self._update_stats('predefined_roles_collected', len(roles_to_fetch))
            
        except Exception as e:
            logger.error(f"Error collecting predefined roles: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'predefined_roles'
            })
    
    def _collect_custom_roles(self, parent: str):
        """
        Collect custom roles for a parent resource
        """
        logger.info(f"Collecting custom roles for {parent}")
        
        try:
            service = self.auth_manager.build_service('iam', 'v1')
            
            request = service.roles().list(
                parent=parent,
                pageSize=self.config.collection_page_size,
                showDeleted=False
            )
            
            role_count = 0
            for role in self._paginate_list(request, 'roles'):
                role_name = role.get('name')
                
                try:
                    # Get full role details
                    # For custom roles, we need to use the full resource name
                    detail_request = service.projects().roles().get(name=role_name) if parent.startswith('projects/') else service.organizations().roles().get(name=role_name)
                    
                    with self.rate_limiter:
                        role_details = self._execute_request(detail_request)
                    
                    # Store custom role
                    self._collected_data['roles']['custom'][role_name] = {
                        'name': role_details.get('name'),
                        'title': role_details.get('title'),
                        'description': role_details.get('description'),
                        'includedPermissions': role_details.get('includedPermissions', []),
                        'stage': role_details.get('stage'),
                        'deleted': role_details.get('deleted', False),
                        'etag': role_details.get('etag')
                    }
                    
                    role_count += 1
                    
                except HttpError as e:
                    logger.warning(f"Error fetching custom role {role_name}: {e}")
                    # Continue with next role instead of failing completely
                    continue
            
            self._increment_stat('custom_roles_collected', role_count)
            
        except HttpError as e:
            logger.warning(f"Error collecting custom roles for {parent}: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'custom_roles',
                'parent': parent
            })
        except Exception as e:
            logger.error(f"Unexpected error collecting custom roles for {parent}: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'custom_roles',
                'parent': parent
            })
    
    def _build_binding_summaries(self):
        """
        Build summaries of IAM bindings by member, role, and resource
        """
        logger.info("Building IAM binding summaries")
        
        by_member = {}
        by_role = {}
        by_resource = {}
        
        # Process all policies
        for resource_type in self._collected_data['policies']:
            for resource_id, policy in self._collected_data['policies'][resource_type].items():
                resource = policy['resource']
                
                for binding in policy.get('bindings', []):
                    role = binding.get('role')
                    members = binding.get('members', [])
                    condition = binding.get('condition')
                    
                    # Create binding info
                    binding_info = {
                        'resource': resource,
                        'resource_type': resource_type.rstrip('s'),  # Remove plural
                        'resource_id': resource_id,
                        'role': role,
                        'condition': condition
                    }
                    
                    # Index by member
                    for member in members:
                        normalized_member = self._normalize_identity(member)
                        if normalized_member not in by_member:
                            by_member[normalized_member] = []
                        by_member[normalized_member].append({
                            **binding_info,
                            'member': normalized_member
                        })
                    
                    # Index by role
                    if role not in by_role:
                        by_role[role] = []
                    by_role[role].append({
                        **binding_info,
                        'members': [self._normalize_identity(m) for m in members]
                    })
                    
                    # Index by resource
                    if resource not in by_resource:
                        by_resource[resource] = []
                    by_resource[resource].append({
                        'role': role,
                        'members': [self._normalize_identity(m) for m in members],
                        'condition': condition
                    })
        
        # Store summaries
        self._collected_data['bindings_summary'] = {
            'by_member': by_member,
            'by_role': by_role,
            'by_resource': by_resource
        }
        
        # Update stats
        self._update_stats('unique_members', len(by_member))
        self._update_stats('unique_roles', len(by_role))
        self._update_stats('total_bindings', sum(len(b) for b in by_member.values()))
    
    def _analyze_impersonation(self):
        """
        Analyze service account impersonation permissions
        """
        logger.info("Analyzing service account impersonation")
        
        impersonation_data = {
            'can_impersonate': {},  # SA -> list of who can impersonate it
            'impersonation_chains': []  # Potential impersonation chains
        }
        
        # Dangerous impersonation permissions
        impersonation_permissions = {
            'iam.serviceAccounts.actAs',
            'iam.serviceAccounts.getAccessToken',
            'iam.serviceAccounts.implicitDelegation',
            'iam.serviceAccountKeys.create'
        }
        
        # Check all role bindings for impersonation permissions
        for role_name, role_data in self._collected_data['roles']['predefined'].items():
            permissions = set(role_data.get('includedPermissions', []))
            
            if permissions & impersonation_permissions:
                # This role grants impersonation abilities
                role_bindings = self._collected_data['bindings_summary']['by_role'].get(role_name, [])
                
                for binding in role_bindings:
                    resource = binding['resource']
                    
                    # Check if this is a service account resource
                    if '/serviceAccounts/' in resource:
                        sa_email = self._extract_service_account_email(resource)
                        if sa_email:
                            if sa_email not in impersonation_data['can_impersonate']:
                                impersonation_data['can_impersonate'][sa_email] = []
                            
                            for member in binding['members']:
                                impersonation_data['can_impersonate'][sa_email].append({
                                    'member': member,
                                    'role': role_name,
                                    'permissions': list(permissions & impersonation_permissions),
                                    'resource': resource,
                                    'condition': binding.get('condition')
                                })
        
        # Check custom roles too
        for role_name, role_data in self._collected_data['roles']['custom'].items():
            permissions = set(role_data.get('includedPermissions', []))
            
            if permissions & impersonation_permissions:
                role_bindings = self._collected_data['bindings_summary']['by_role'].get(role_name, [])
                
                for binding in role_bindings:
                    resource = binding['resource']
                    
                    if '/serviceAccounts/' in resource:
                        sa_email = self._extract_service_account_email(resource)
                        if sa_email:
                            if sa_email not in impersonation_data['can_impersonate']:
                                impersonation_data['can_impersonate'][sa_email] = []
                            
                            for member in binding['members']:
                                impersonation_data['can_impersonate'][sa_email].append({
                                    'member': member,
                                    'role': role_name,
                                    'permissions': list(permissions & impersonation_permissions),
                                    'resource': resource,
                                    'condition': binding.get('condition')
                                })
        
        # Store impersonation analysis
        self._collected_data['impersonation_analysis'] = impersonation_data
        self._update_stats('service_accounts_impersonatable', len(impersonation_data['can_impersonate']))
    
    def _extract_service_account_email(self, resource: str) -> Optional[str]:
        """
        Extract service account email from resource name
        """
        # Pattern: projects/{project}/serviceAccounts/{email}
        if '/serviceAccounts/' in resource:
            parts = resource.split('/serviceAccounts/')
            if len(parts) > 1:
                return parts[1]
        return None
    
    def get_members_with_role(self, role: str) -> List[str]:
        """
        Get all members that have a specific role
        
        Args:
            role: Role name (e.g., 'roles/owner')
            
        Returns:
            List of member identities
        """
        members = set()
        
        role_bindings = self._collected_data['bindings_summary']['by_role'].get(role, [])
        for binding in role_bindings:
            members.update(binding['members'])
        
        return list(members)
    
    def get_roles_for_member(self, member: str) -> List[Dict[str, Any]]:
        """
        Get all roles assigned to a member
        
        Args:
            member: Member identity
            
        Returns:
            List of role assignments
        """
        normalized_member = self._normalize_identity(member)
        return self._collected_data['bindings_summary']['by_member'].get(
            normalized_member, []
        ) 