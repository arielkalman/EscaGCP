"""
Orchestrator for coordinating all data collectors
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from .hierarchy import HierarchyCollector
from .iam import IAMCollector
from .identity import IdentityCollector
from .resources import ResourceCollector
from .logs_collector import LogsCollector
from .tags_collector import TagsCollector
from .cloudbuild_collector import CloudBuildCollector
from .gke_collector import GKECollector
from ..utils import get_logger, AuthManager, Config, ProgressLogger


logger = get_logger(__name__)


class CollectionOrchestrator:
    """
    Orchestrates the collection of all GCP data
    """
    
    def __init__(self, auth_manager: AuthManager, config: Config):
        """
        Initialize the orchestrator
        
        Args:
            auth_manager: Authentication manager instance
            config: Configuration instance
        """
        self.auth_manager = auth_manager
        self.config = config
        self._collected_data = {}
        self._metadata = {
            'start_time': None,
            'end_time': None,
            'collectors_run': [],
            'errors': [],
            'stats': {}
        }
    
    def collect_all(
        self,
        organization_id: Optional[str] = None,
        folder_ids: Optional[List[str]] = None,
        project_ids: Optional[List[str]] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Collect all data from GCP
        
        Args:
            organization_id: Organization ID to scan
            folder_ids: List of folder IDs to scan
            project_ids: List of project IDs to scan (None to discover all)
            output_dir: Directory to save collected data
            
        Returns:
            Dictionary containing all collected data
        """
        self._metadata['start_time'] = datetime.now().isoformat()
        logger.info("Starting GCPHound data collection")
        
        try:
            # Step 1: Collect hierarchy to discover projects
            logger.info("Step 1: Collecting resource hierarchy")
            hierarchy_collector = HierarchyCollector(self.auth_manager, self.config)
            hierarchy_data = hierarchy_collector.collect(
                organization_id=organization_id,
                folder_ids=folder_ids,
                project_ids=project_ids
            )
            self._collected_data['hierarchy'] = hierarchy_data
            self._metadata['collectors_run'].append('hierarchy')
            
            # Extract discovered project IDs if not specified
            if project_ids is None:
                project_ids = list(hierarchy_data['data']['projects'].keys())
                logger.info(f"Discovered {len(project_ids)} projects")
            
            # Extract folder IDs if organization is specified but folders aren't
            if organization_id and folder_ids is None:
                folder_ids = list(hierarchy_data['data']['folders'].keys())
                logger.info(f"Discovered {len(folder_ids)} folders")
            
            # Step 2: Collect IAM policies and roles
            logger.info("Step 2: Collecting IAM policies and roles")
            iam_collector = IAMCollector(self.auth_manager, self.config)
            iam_data = iam_collector.collect(
                project_ids=project_ids,
                organization_id=organization_id,
                folder_ids=folder_ids
            )
            self._collected_data['iam'] = iam_data
            self._metadata['collectors_run'].append('iam')
            
            # Step 3: Collect identity information
            logger.info("Step 3: Collecting identity information")
            identity_collector = IdentityCollector(self.auth_manager, self.config)
            identity_data = identity_collector.collect(
                project_ids=project_ids,
                organization_id=organization_id
            )
            self._collected_data['identity'] = identity_data
            self._metadata['collectors_run'].append('identity')
            
            # Step 4: Collect resources
            logger.info("Step 4: Collecting GCP resources")
            resource_collector = ResourceCollector(self.auth_manager, self.config)
            resource_data = resource_collector.collect(
                project_ids=project_ids
            )
            self._collected_data['resources'] = resource_data
            self._metadata['collectors_run'].append('resources')
            
            # Step 5: Collect logs
            logger.info("Step 5: Collecting logs")
            logs_collector = LogsCollector(self.auth_manager, self.config)
            logs_data = logs_collector.collect(
                project_ids=project_ids
            )
            self._collected_data['logs'] = logs_data
            self._metadata['collectors_run'].append('logs')
            
            # Step 6: Collect tags
            logger.info("Step 6: Collecting tags")
            tags_collector = TagsCollector(self.auth_manager, self.config)
            tags_data = tags_collector.collect(
                organization_id=organization_id,
                project_ids=project_ids
            )
            self._collected_data['tags'] = tags_data
            self._metadata['collectors_run'].append('tags')
            
            # Step 7: Collect Cloud Build data
            logger.info("Step 7: Collecting Cloud Build data")
            cloudbuild_collector = CloudBuildCollector(self.auth_manager, self.config)
            cloudbuild_data = cloudbuild_collector.collect(
                project_ids=project_ids
            )
            self._collected_data['cloudbuild'] = cloudbuild_data
            self._metadata['collectors_run'].append('cloudbuild')
            
            # Step 8: Collect GKE data
            logger.info("Step 8: Collecting GKE data")
            gke_collector = GKECollector(self.auth_manager, self.config)
            gke_data = gke_collector.collect(
                project_ids=project_ids
            )
            self._collected_data['gke'] = gke_data
            self._metadata['collectors_run'].append('gke')
            
            # Merge all metadata
            self._merge_metadata()
            
            # Save collected data if output directory specified
            if output_dir:
                self._save_all_data(output_dir)
            
        except Exception as e:
            logger.error(f"Error during orchestrated collection: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'orchestration'
            })
        
        self._metadata['end_time'] = datetime.now().isoformat()
        duration = (
            datetime.fromisoformat(self._metadata['end_time']) -
            datetime.fromisoformat(self._metadata['start_time'])
        ).total_seconds()
        self._metadata['duration_seconds'] = duration
        
        logger.info(f"Completed GCPHound data collection in {duration:.2f} seconds")
        
        return {
            'metadata': self._metadata,
            'data': self._collected_data
        }
    
    def collect_incremental(
        self,
        previous_data_path: str,
        organization_id: Optional[str] = None,
        folder_ids: Optional[List[str]] = None,
        project_ids: Optional[List[str]] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Collect data incrementally, comparing with previous collection
        
        Args:
            previous_data_path: Path to previous collection data
            organization_id: Organization ID to scan
            folder_ids: List of folder IDs to scan
            project_ids: List of project IDs to scan
            output_dir: Directory to save collected data
            
        Returns:
            Dictionary containing collected data and changes
        """
        logger.info("Starting incremental GCPHound data collection")
        
        # Load previous data
        previous_data = self._load_previous_data(previous_data_path)
        
        # Collect current data
        current_data = self.collect_all(
            organization_id=organization_id,
            folder_ids=folder_ids,
            project_ids=project_ids
        )
        
        # Compare and find changes
        changes = self._compare_collections(previous_data, current_data)
        
        # Add changes to metadata
        current_data['metadata']['changes'] = changes
        
        # Save if output directory specified
        if output_dir:
            self._save_all_data(output_dir, current_data)
            self._save_changes(output_dir, changes)
        
        return current_data
    
    def _merge_metadata(self):
        """
        Merge metadata from all collectors
        """
        total_errors = []
        combined_stats = {}
        
        for collector_name, collector_data in self._collected_data.items():
            if 'metadata' in collector_data:
                metadata = collector_data['metadata']
                
                # Merge errors
                total_errors.extend(metadata.get('errors', []))
                
                # Merge stats
                stats = metadata.get('stats', {})
                for key, value in stats.items():
                    combined_stats[f"{collector_name}_{key}"] = value
        
        self._metadata['errors'].extend(total_errors)
        self._metadata['stats'] = combined_stats
        
        # Calculate totals
        self._metadata['stats']['total_projects'] = len(
            self._collected_data.get('hierarchy', {}).get('data', {}).get('projects', {})
        )
        self._metadata['stats']['total_errors'] = len(self._metadata['errors'])
    
    def _save_all_data(self, output_dir: str, data: Optional[Dict[str, Any]] = None):
        """
        Save all collected data to files
        
        Args:
            output_dir: Output directory path
            data: Data to save (uses self._collected_data if None)
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if data is None:
            data = {
                'metadata': self._metadata,
                'data': self._collected_data
            }
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save complete data
        complete_file = output_path / f"gcphound_complete_{timestamp}.json"
        logger.info(f"Saving complete data to: {complete_file}")
        with open(complete_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        # Save individual collector outputs
        for collector_name, collector_data in self._collected_data.items():
            collector_file = output_path / f"gcphound_{collector_name}_{timestamp}.json"
            logger.info(f"Saving {collector_name} data to: {collector_file}")
            with open(collector_file, 'w') as f:
                json.dump(collector_data, f, indent=2, default=str)
        
        # Save metadata separately
        metadata_file = output_path / f"gcphound_metadata_{timestamp}.json"
        with open(metadata_file, 'w') as f:
            json.dump(self._metadata, f, indent=2, default=str)
        
        logger.info(f"All data saved to: {output_path}")
    
    def _load_previous_data(self, data_path: str) -> Dict[str, Any]:
        """
        Load previous collection data
        
        Args:
            data_path: Path to previous data file
            
        Returns:
            Previous collection data
        """
        logger.info(f"Loading previous data from: {data_path}")
        
        try:
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading previous data: {e}")
            return {}
    
    def _compare_collections(
        self,
        previous: Dict[str, Any],
        current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two collections and identify changes
        
        Args:
            previous: Previous collection data
            current: Current collection data
            
        Returns:
            Dictionary of changes
        """
        logger.info("Comparing collections to identify changes")
        
        changes = {
            'summary': {
                'new_resources': 0,
                'removed_resources': 0,
                'modified_resources': 0,
                'new_bindings': 0,
                'removed_bindings': 0,
                'new_identities': 0,
                'removed_identities': 0
            },
            'details': {
                'new_resources': [],
                'removed_resources': [],
                'modified_resources': [],
                'new_bindings': [],
                'removed_bindings': [],
                'new_identities': [],
                'removed_identities': []
            }
        }
        
        # Compare projects
        prev_projects = set(previous.get('data', {}).get('hierarchy', {}).get('data', {}).get('projects', {}).keys())
        curr_projects = set(current.get('data', {}).get('hierarchy', {}).get('data', {}).get('projects', {}).keys())
        
        new_projects = curr_projects - prev_projects
        removed_projects = prev_projects - curr_projects
        
        for project in new_projects:
            changes['details']['new_resources'].append({
                'type': 'project',
                'id': project
            })
            changes['summary']['new_resources'] += 1
        
        for project in removed_projects:
            changes['details']['removed_resources'].append({
                'type': 'project',
                'id': project
            })
            changes['summary']['removed_resources'] += 1
        
        # Compare IAM bindings
        prev_bindings = self._extract_all_bindings(previous.get('data', {}).get('iam', {}))
        curr_bindings = self._extract_all_bindings(current.get('data', {}).get('iam', {}))
        
        new_bindings = curr_bindings - prev_bindings
        removed_bindings = prev_bindings - curr_bindings
        
        changes['summary']['new_bindings'] = len(new_bindings)
        changes['summary']['removed_bindings'] = len(removed_bindings)
        
        # Add more detailed comparison logic as needed
        
        return changes
    
    def _extract_all_bindings(self, iam_data: Dict[str, Any]) -> set:
        """
        Extract all IAM bindings as a set for comparison
        
        Args:
            iam_data: IAM collector data
            
        Returns:
            Set of binding tuples
        """
        bindings = set()
        
        if 'data' not in iam_data:
            return bindings
        
        policies = iam_data['data'].get('policies', {})
        
        for resource_type in policies:
            for resource_id, policy in policies[resource_type].items():
                for binding in policy.get('bindings', []):
                    role = binding.get('role')
                    for member in binding.get('members', []):
                        bindings.add((resource_type, resource_id, role, member))
        
        return bindings
    
    def _save_changes(self, output_dir: str, changes: Dict[str, Any]):
        """
        Save changes to a separate file
        
        Args:
            output_dir: Output directory
            changes: Changes dictionary
        """
        output_path = Path(output_dir)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        changes_file = output_path / f"gcphound_changes_{timestamp}.json"
        logger.info(f"Saving changes to: {changes_file}")
        
        with open(changes_file, 'w') as f:
            json.dump(changes, f, indent=2, default=str)
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the collection
        
        Returns:
            Summary dictionary
        """
        summary = {
            'duration_seconds': self._metadata.get('duration_seconds', 0),
            'collectors_run': self._metadata.get('collectors_run', []),
            'total_errors': len(self._metadata.get('errors', [])),
            'stats': self._metadata.get('stats', {})
        }
        
        return summary 