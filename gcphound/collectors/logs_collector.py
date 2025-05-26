"""
Collector for Cloud Audit Logs to enrich graph with actual activity
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from googleapiclient.errors import HttpError
from .base import BaseCollector
from ..utils import get_logger, ProgressLogger
import re


logger = get_logger(__name__)


class LogsCollector(BaseCollector):
    """
    Collects and analyzes Cloud Audit Logs for security-relevant activities
    """
    
    # Audit log methods that indicate privilege escalation or impersonation
    IMPERSONATION_METHODS = {
        'GenerateAccessToken',
        'GenerateIdToken',
        'SignBlob',
        'SignJwt',
        'ImpersonateServiceAccount'
    }
    
    PRIVILEGE_ESCALATION_METHODS = {
        'SetIamPolicy',
        'UpdatePolicy',
        'CreateRole',
        'UpdateRole',
        'CreateServiceAccount',
        'CreateServiceAccountKey',
        'AttachServiceAccount',
        'UpdateMetadata',
        'Deploy',  # Cloud Functions/Run
        'Create',  # Various resources
        'Update',  # Various resources
        'BindTag',
        'CreateTagBinding'
    }
    
    SENSITIVE_ACCESS_METHODS = {
        'Get',
        'List',
        'Read',
        'Download',
        'Decrypt',
        'AccessSecretVersion'
    }
    
    def collect(
        self,
        project_ids: List[str],
        days_back: int = 7,
        log_filter: Optional[str] = None,
        collect_impersonation: bool = True,
        collect_privilege_escalation: bool = True,
        collect_sensitive_access: bool = True
    ) -> Dict[str, Any]:
        """
        Collect audit logs from Cloud Logging
        
        Args:
            project_ids: List of project IDs to collect logs from
            days_back: Number of days to look back
            log_filter: Additional log filter to apply
            collect_impersonation: Collect service account impersonation events
            collect_privilege_escalation: Collect privilege escalation events
            collect_sensitive_access: Collect sensitive resource access events
            
        Returns:
            Dictionary containing audit log data
        """
        self._start_collection()
        
        # Initialize data structures
        self._collected_data = {
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
        
        try:
            # Build log filters
            filters = self._build_log_filters(
                days_back,
                log_filter,
                collect_impersonation,
                collect_privilege_escalation,
                collect_sensitive_access
            )
            
            # Collect logs from each project
            with ThreadPoolExecutor(
                max_workers=self.config.performance_max_concurrent_requests
            ) as executor:
                futures = []
                
                for project_id in project_ids:
                    for filter_name, filter_str in filters.items():
                        future = executor.submit(
                            self._collect_project_logs,
                            project_id,
                            filter_str,
                            filter_name
                        )
                        futures.append((project_id, filter_name, future))
                
                # Process results
                with ProgressLogger(
                    total=len(futures),
                    description="Collecting audit logs"
                ) as progress:
                    for project_id, filter_name, future in futures:
                        try:
                            events = future.result()
                            self._process_log_events(events, filter_name)
                            progress.update(1)
                        except Exception as e:
                            logger.error(f"Error collecting {filter_name} logs from {project_id}: {e}")
                            self._metadata['errors'].append({
                                'error': str(e),
                                'project_id': project_id,
                                'filter_name': filter_name
                            })
            
            # Analyze patterns
            self._analyze_suspicious_patterns()
            
            # Build activity summary
            self._build_activity_summary()
            
        except Exception as e:
            logger.error(f"Error during audit log collection: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'collection'
            })
        
        self._end_collection()
        return self.get_collected_data()
    
    def _build_log_filters(
        self,
        days_back: int,
        custom_filter: Optional[str],
        collect_impersonation: bool,
        collect_privilege_escalation: bool,
        collect_sensitive_access: bool
    ) -> Dict[str, str]:
        """Build Cloud Logging filters for different event types"""
        filters = {}
        
        # Base timestamp filter
        timestamp = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + 'Z'
        base_filter = f'timestamp>="{timestamp}"'
        
        if custom_filter:
            base_filter = f'{base_filter} AND ({custom_filter})'
        
        # Impersonation filter
        if collect_impersonation:
            impersonation_methods = ' OR '.join([
                f'protoPayload.methodName="{method}"'
                for method in self.IMPERSONATION_METHODS
            ])
            filters['impersonation'] = (
                f'{base_filter} AND '
                f'protoPayload.@type="type.googleapis.com/google.cloud.audit.AuditLog" AND '
                f'({impersonation_methods})'
            )
        
        # Privilege escalation filter
        if collect_privilege_escalation:
            escalation_methods = ' OR '.join([
                f'protoPayload.methodName=~".*{method}.*"'
                for method in self.PRIVILEGE_ESCALATION_METHODS
            ])
            filters['privilege_escalation'] = (
                f'{base_filter} AND '
                f'protoPayload.@type="type.googleapis.com/google.cloud.audit.AuditLog" AND '
                f'({escalation_methods})'
            )
        
        # Sensitive access filter
        if collect_sensitive_access:
            # Focus on specific sensitive services
            sensitive_services = [
                'secretmanager.googleapis.com',
                'cloudkms.googleapis.com',
                'storage.googleapis.com',
                'bigquery.googleapis.com'
            ]
            service_filter = ' OR '.join([
                f'protoPayload.serviceName="{service}"'
                for service in sensitive_services
            ])
            filters['sensitive_access'] = (
                f'{base_filter} AND '
                f'protoPayload.@type="type.googleapis.com/google.cloud.audit.AuditLog" AND '
                f'({service_filter}) AND '
                f'severity!="ERROR"'
            )
        
        return filters
    
    def _collect_project_logs(
        self,
        project_id: str,
        filter_str: str,
        filter_name: str
    ) -> List[Dict[str, Any]]:
        """Collect logs from a single project"""
        try:
            service = self.auth_manager.build_service('logging', 'v2')
            
            # List log entries
            request = service.entries().list(
                body={
                    'resourceNames': [f'projects/{project_id}'],
                    'filter': filter_str,
                    'orderBy': 'timestamp desc',
                    'pageSize': self.config.collection_page_size
                }
            )
            
            events = []
            page_count = 0
            max_pages = 10  # Limit pages for performance
            
            while request is not None and page_count < max_pages:
                with self.rate_limiter:
                    response = self._execute_request(request)
                
                entries = response.get('entries', [])
                for entry in entries:
                    event = self._parse_log_entry(entry)
                    if event:
                        events.append(event)
                
                # Get next page
                request = service.entries().list_next(request, response)
                page_count += 1
            
            logger.info(f"Collected {len(events)} {filter_name} events from {project_id}")
            return events
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"No permission to read logs in project {project_id}")
            else:
                logger.error(f"Error collecting logs from {project_id}: {e}")
            return []
    
    def _parse_log_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a log entry into a structured event"""
        try:
            proto_payload = entry.get('protoPayload', {})
            
            # Extract key fields
            event = {
                'timestamp': entry.get('timestamp'),
                'severity': entry.get('severity'),
                'principal': proto_payload.get('authenticationInfo', {}).get('principalEmail'),
                'principalSubject': proto_payload.get('authenticationInfo', {}).get('principalSubject'),
                'serviceName': proto_payload.get('serviceName'),
                'methodName': proto_payload.get('methodName'),
                'resourceName': proto_payload.get('resourceName'),
                'requestMetadata': proto_payload.get('requestMetadata', {}),
                'authorizationInfo': proto_payload.get('authorizationInfo', []),
                'response': proto_payload.get('response', {}),
                'request': proto_payload.get('request', {}),
                'status': proto_payload.get('status', {})
            }
            
            # Extract specific details based on method
            if event['methodName'] in self.IMPERSONATION_METHODS:
                event['impersonationDetails'] = self._extract_impersonation_details(proto_payload)
            
            if any(method in event['methodName'] for method in self.PRIVILEGE_ESCALATION_METHODS):
                event['escalationDetails'] = self._extract_escalation_details(proto_payload)
            
            return event
            
        except Exception as e:
            logger.debug(f"Error parsing log entry: {e}")
            return None
    
    def _extract_impersonation_details(self, proto_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract details specific to impersonation events"""
        details = {}
        
        # Get the target service account
        resource_name = proto_payload.get('resourceName', '')
        if '/serviceAccounts/' in resource_name:
            details['targetServiceAccount'] = resource_name.split('/serviceAccounts/')[-1]
        
        # Get delegation chain if present
        request = proto_payload.get('request', {})
        if 'delegates' in request:
            details['delegationChain'] = request['delegates']
        
        # Get scope/audience
        if 'scope' in request:
            details['scope'] = request['scope']
        if 'audience' in request:
            details['audience'] = request['audience']
        
        return details
    
    def _extract_escalation_details(self, proto_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract details specific to privilege escalation events"""
        details = {}
        
        # Get the policy changes
        request = proto_payload.get('request', {})
        if 'policy' in request:
            policy = request['policy']
            if 'bindings' in policy:
                details['newBindings'] = policy['bindings']
        
        # Get role details
        if 'role' in request:
            details['role'] = request['role']
            if 'includedPermissions' in request['role']:
                details['permissions'] = request['role']['includedPermissions']
        
        # Get resource details
        resource_name = proto_payload.get('resourceName', '')
        details['targetResource'] = resource_name
        
        return details
    
    def _process_log_events(self, events: List[Dict[str, Any]], event_type: str):
        """Process and categorize log events"""
        for event in events:
            # Skip failed operations unless they're attempts
            if event.get('status', {}).get('code') and event['status']['code'] != 0:
                # Still track failed privilege escalation attempts
                if event_type == 'privilege_escalation':
                    event['failed'] = True
                else:
                    continue
            
            # Categorize event
            if event_type == 'impersonation':
                self._collected_data['impersonation_events'].append(event)
            elif event_type == 'privilege_escalation':
                self._collected_data['privilege_escalation_events'].append(event)
            elif event_type == 'sensitive_access':
                self._collected_data['sensitive_access_events'].append(event)
            
            # Update stats
            self._increment_stat(f'{event_type}_events')
    
    def _analyze_suspicious_patterns(self):
        """Analyze collected events for suspicious patterns"""
        patterns = []
        
        # Pattern 1: Rapid impersonation chain
        impersonation_by_principal = {}
        for event in self._collected_data['impersonation_events']:
            principal = event.get('principal')
            if principal:
                if principal not in impersonation_by_principal:
                    impersonation_by_principal[principal] = []
                impersonation_by_principal[principal].append(event)
        
        for principal, events in impersonation_by_principal.items():
            if len(events) > 5:  # More than 5 impersonations
                unique_targets = set()
                for event in events:
                    details = event.get('impersonationDetails', {})
                    target = details.get('targetServiceAccount')
                    if target:
                        unique_targets.add(target)
                
                if len(unique_targets) > 3:  # Multiple different targets
                    patterns.append({
                        'type': 'rapid_impersonation_chain',
                        'principal': principal,
                        'event_count': len(events),
                        'unique_targets': len(unique_targets),
                        'risk_score': min(1.0, len(unique_targets) * 0.2)
                    })
        
        # Pattern 2: Privilege escalation followed by sensitive access
        escalation_principals = set()
        for event in self._collected_data['privilege_escalation_events']:
            principal = event.get('principal')
            if principal and not event.get('failed'):
                escalation_principals.add(principal)
                timestamp = event.get('timestamp')
                
                # Check for sensitive access within 1 hour
                for access_event in self._collected_data['sensitive_access_events']:
                    if (access_event.get('principal') == principal and
                        self._within_time_window(timestamp, access_event.get('timestamp'), hours=1)):
                        patterns.append({
                            'type': 'escalation_then_access',
                            'principal': principal,
                            'escalation_method': event.get('methodName'),
                            'access_resource': access_event.get('resourceName'),
                            'risk_score': 0.9
                        })
        
        # Pattern 3: Service account key creation followed by usage
        key_creations = {}
        for event in self._collected_data['privilege_escalation_events']:
            if 'CreateServiceAccountKey' in event.get('methodName', ''):
                sa = event.get('escalationDetails', {}).get('targetResource', '')
                if sa:
                    key_creations[sa] = event
        
        # Check for subsequent usage
        for sa, creation_event in key_creations.items():
            sa_email = sa.split('/')[-1] if '/' in sa else sa
            for event in self._collected_data['impersonation_events']:
                if event.get('principal') == sa_email:
                    patterns.append({
                        'type': 'key_creation_and_usage',
                        'service_account': sa_email,
                        'created_by': creation_event.get('principal'),
                        'risk_score': 0.95
                    })
        
        self._collected_data['suspicious_patterns'] = patterns
    
    def _build_activity_summary(self):
        """Build summary of all activities"""
        summary = self._collected_data['activity_summary']
        
        # Summarize by principal
        all_events = (
            self._collected_data['impersonation_events'] +
            self._collected_data['privilege_escalation_events'] +
            self._collected_data['sensitive_access_events']
        )
        
        for event in all_events:
            principal = event.get('principal')
            if principal:
                if principal not in summary['by_principal']:
                    summary['by_principal'][principal] = {
                        'impersonations': 0,
                        'escalations': 0,
                        'sensitive_accesses': 0,
                        'methods': set(),
                        'resources': set()
                    }
                
                if event in self._collected_data['impersonation_events']:
                    summary['by_principal'][principal]['impersonations'] += 1
                elif event in self._collected_data['privilege_escalation_events']:
                    summary['by_principal'][principal]['escalations'] += 1
                elif event in self._collected_data['sensitive_access_events']:
                    summary['by_principal'][principal]['sensitive_accesses'] += 1
                
                method = event.get('methodName')
                if method:
                    summary['by_principal'][principal]['methods'].add(method)
                
                resource = event.get('resourceName')
                if resource:
                    summary['by_principal'][principal]['resources'].add(resource)
        
        # Convert sets to lists for JSON serialization
        for principal_data in summary['by_principal'].values():
            principal_data['methods'] = list(principal_data['methods'])
            principal_data['resources'] = list(principal_data['resources'])
        
        # Summarize by method
        for event in all_events:
            method = event.get('methodName')
            if method:
                if method not in summary['by_method']:
                    summary['by_method'][method] = 0
                summary['by_method'][method] += 1
    
    def _within_time_window(
        self,
        timestamp1: str,
        timestamp2: str,
        hours: int
    ) -> bool:
        """Check if two timestamps are within a time window"""
        try:
            t1 = datetime.fromisoformat(timestamp1.replace('Z', '+00:00'))
            t2 = datetime.fromisoformat(timestamp2.replace('Z', '+00:00'))
            return abs((t1 - t2).total_seconds()) <= hours * 3600
        except:
            return False
    
    def get_graph_enrichment_data(self) -> List[Dict[str, Any]]:
        """
        Get data formatted for graph enrichment
        
        Returns:
            List of edges to add to the graph based on audit logs
        """
        enrichment_edges = []
        
        # Add confirmed impersonation edges
        for event in self._collected_data['impersonation_events']:
            if event.get('status', {}).get('code', 0) == 0:  # Successful
                principal = event.get('principal')
                details = event.get('impersonationDetails', {})
                target = details.get('targetServiceAccount')
                
                if principal and target:
                    enrichment_edges.append({
                        'source': principal,
                        'target': target,
                        'type': 'HAS_IMPERSONATED',
                        'properties': {
                            'timestamp': event.get('timestamp'),
                            'method': event.get('methodName'),
                            'confirmedByAudit': True
                        }
                    })
        
        # Add confirmed privilege escalation edges
        for event in self._collected_data['privilege_escalation_events']:
            if event.get('status', {}).get('code', 0) == 0:  # Successful
                principal = event.get('principal')
                details = event.get('escalationDetails', {})
                target = details.get('targetResource')
                
                if principal and target:
                    enrichment_edges.append({
                        'source': principal,
                        'target': target,
                        'type': 'HAS_ESCALATED_PRIVILEGE',
                        'properties': {
                            'timestamp': event.get('timestamp'),
                            'method': event.get('methodName'),
                            'newBindings': details.get('newBindings', []),
                            'confirmedByAudit': True
                        }
                    })
        
        # Add confirmed sensitive access edges
        for event in self._collected_data['sensitive_access_events']:
            principal = event.get('principal')
            resource = event.get('resourceName')
            
            if principal and resource:
                enrichment_edges.append({
                    'source': principal,
                    'target': resource,
                    'type': 'HAS_ACCESSED',
                    'properties': {
                        'timestamp': event.get('timestamp'),
                        'method': event.get('methodName'),
                        'service': event.get('serviceName'),
                        'confirmedByAudit': True
                    }
                })
        
        return enrichment_edges 