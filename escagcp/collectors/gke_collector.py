"""
Collector for GKE clusters and workload identity configurations
"""

from typing import Dict, Any, List, Optional
from googleapiclient.errors import HttpError
from .base import BaseCollector
from ..utils import get_logger


logger = get_logger(__name__)


class GKECollector(BaseCollector):
    """
    Collects GKE cluster configurations, workload identity bindings, and node pools
    
    This is critical for detecting:
    - Workload Identity Federation privilege escalation
    - Node pool service account abuse
    - Binary Authorization bypass
    - GKE metadata server exploitation
    
    Reference: https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity
    """
    
    def collect(
        self,
        project_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Collect GKE data
        
        Args:
            project_ids: List of project IDs to scan
            
        Returns:
            Dictionary containing GKE data
        """
        self._start_collection()
        
        # Initialize data structures
        self._collected_data = {
            'clusters': {},
            'node_pools': {},
            'workload_identity_pools': {},
            'k8s_service_accounts': {},  # K8s SAs with workload identity
            'binary_authorization': {},   # Binary auth policies
            'pod_security_policies': {}   # PSPs if enabled
        }
        
        if not project_ids:
            logger.warning("No project IDs provided for GKE collection")
            self._end_collection()
            return self.get_collected_data()
        
        try:
            for project_id in project_ids:
                self._collect_project_gke(project_id)
            
        except Exception as e:
            logger.error(f"Error during GKE collection: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'collection'
            })
        
        self._end_collection()
        return self.get_collected_data()
    
    def _collect_project_gke(self, project_id: str):
        """
        Collect GKE data for a project
        
        Args:
            project_id: Project ID
        """
        logger.info(f"Collecting GKE data for project {project_id}")
        
        # Collect clusters
        self._collect_clusters(project_id)
        
        # Collect binary authorization policies
        self._collect_binary_authorization(project_id)
    
    def _collect_clusters(self, project_id: str):
        """
        Collect GKE clusters
        
        Args:
            project_id: Project ID
        """
        try:
            service = self.auth_manager.build_service('container', 'v1')
            
            # List all clusters in all zones/regions
            parent = f"projects/{project_id}/locations/-"
            response = service.projects().locations().clusters().list(
                parent=parent
            ).execute()
            
            for cluster in response.get('clusters', []):
                cluster_name = cluster.get('name')
                cluster_id = f"{project_id}/{cluster.get('location')}/{cluster_name}"
                
                # Extract workload identity config
                workload_identity_config = cluster.get('workloadIdentityConfig', {})
                
                # Store cluster data
                self._collected_data['clusters'][cluster_id] = {
                    'name': cluster_name,
                    'project_id': project_id,
                    'location': cluster.get('location'),
                    'status': cluster.get('status'),
                    'workloadIdentityConfig': workload_identity_config,
                    'nodeConfig': self._extract_node_config(cluster.get('nodeConfig', {})),
                    'nodePools': [],  # Will be populated below
                    'masterAuth': cluster.get('masterAuth', {}),
                    'masterAuthorizedNetworksConfig': cluster.get('masterAuthorizedNetworksConfig', {}),
                    'privateClusterConfig': cluster.get('privateClusterConfig', {}),
                    'networkPolicy': cluster.get('networkPolicy', {}),
                    'binaryAuthorization': cluster.get('binaryAuthorization', {}),
                    'shieldedNodes': cluster.get('shieldedNodes', {}),
                    'releaseChannel': cluster.get('releaseChannel', {}),
                    'autopilot': cluster.get('autopilot', {})
                }
                
                # Collect node pools
                self._collect_node_pools(cluster_id, cluster)
                
                # If workload identity is enabled, collect K8s service accounts
                if workload_identity_config.get('workloadPool'):
                    self._collect_workload_identity_bindings(
                        cluster_id,
                        workload_identity_config['workloadPool']
                    )
                
                self._increment_stat('gke_clusters_collected')
            
        except HttpError as e:
            if e.resp.status != 403:
                logger.debug(f"Error collecting GKE clusters for {project_id}: {e}")
    
    def _collect_node_pools(self, cluster_id: str, cluster: Dict[str, Any]):
        """
        Collect node pools for a cluster
        
        Args:
            cluster_id: Cluster identifier
            cluster: Cluster data
        """
        for node_pool in cluster.get('nodePools', []):
            pool_name = node_pool.get('name')
            pool_id = f"{cluster_id}/nodePools/{pool_name}"
            
            # Extract node config
            node_config = node_pool.get('config', {})
            
            # Store node pool data
            self._collected_data['node_pools'][pool_id] = {
                'name': pool_name,
                'cluster_id': cluster_id,
                'status': node_pool.get('status'),
                'config': self._extract_node_config(node_config),
                'autoscaling': node_pool.get('autoscaling', {}),
                'management': node_pool.get('management', {}),
                'maxPodsConstraint': node_pool.get('maxPodsConstraint', {}),
                'conditions': node_pool.get('conditions', []),
                'upgradeSettings': node_pool.get('upgradeSettings', {})
            }
            
            # Add to cluster's node pool list
            self._collected_data['clusters'][cluster_id]['nodePools'].append(pool_id)
            
            self._increment_stat('node_pools_collected')
    
    def _extract_node_config(self, node_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant node configuration
        
        Args:
            node_config: Node configuration dict
            
        Returns:
            Extracted config
        """
        return {
            'serviceAccount': node_config.get('serviceAccount'),
            'oauthScopes': node_config.get('oauthScopes', []),
            'metadata': node_config.get('metadata', {}),
            'workloadMetadataConfig': node_config.get('workloadMetadataConfig', {}),
            'shieldedInstanceConfig': node_config.get('shieldedInstanceConfig', {}),
            'sandboxConfig': node_config.get('sandboxConfig', {}),
            'gcfsConfig': node_config.get('gcfsConfig', {}),
            'tags': node_config.get('tags', [])
        }
    
    def _collect_workload_identity_bindings(self, cluster_id: str, workload_pool: str):
        """
        Collect workload identity bindings
        
        Args:
            cluster_id: Cluster identifier
            workload_pool: Workload identity pool
        """
        # Store workload pool info
        self._collected_data['workload_identity_pools'][cluster_id] = {
            'cluster_id': cluster_id,
            'workload_pool': workload_pool,
            'k8s_service_accounts': []
        }
        
        # Note: To get actual K8s service accounts and their bindings,
        # we would need to connect to the K8s API directly.
        # For now, we'll mark this for manual inspection or integration
        # with a K8s collector.
        
        logger.info(f"Workload Identity enabled for cluster {cluster_id} with pool {workload_pool}")
        self._increment_stat('workload_identity_pools_collected')
    
    def _collect_binary_authorization(self, project_id: str):
        """
        Collect Binary Authorization policies
        
        Args:
            project_id: Project ID
        """
        try:
            service = self.auth_manager.build_service('binaryauthorization', 'v1')
            
            # Get the policy
            policy_name = f"projects/{project_id}/policy"
            policy = service.projects().getPolicy(name=policy_name).execute()
            
            # Store policy data
            self._collected_data['binary_authorization'][project_id] = {
                'name': policy.get('name'),
                'globalPolicyEvaluationMode': policy.get('globalPolicyEvaluationMode'),
                'admissionWhitelistPatterns': policy.get('admissionWhitelistPatterns', []),
                'clusterAdmissionRules': policy.get('clusterAdmissionRules', {}),
                'defaultAdmissionRule': policy.get('defaultAdmissionRule', {}),
                'updateTime': policy.get('updateTime')
            }
            
            self._increment_stat('binary_auth_policies_collected')
            
        except HttpError as e:
            if e.resp.status not in [403, 404]:
                logger.debug(f"Error collecting Binary Authorization for {project_id}: {e}")
    
    def get_clusters_with_workload_identity(self) -> List[str]:
        """
        Get list of clusters with Workload Identity enabled
        
        Returns:
            List of cluster IDs
        """
        clusters = []
        for cluster_id, cluster_data in self._collected_data['clusters'].items():
            if cluster_data.get('workloadIdentityConfig', {}).get('workloadPool'):
                clusters.append(cluster_id)
        return clusters
    
    def get_node_pools_by_service_account(self, service_account: str) -> List[str]:
        """
        Get node pools using a specific service account
        
        Args:
            service_account: Service account email
            
        Returns:
            List of node pool IDs
        """
        pools = []
        for pool_id, pool_data in self._collected_data['node_pools'].items():
            if pool_data.get('config', {}).get('serviceAccount') == service_account:
                pools.append(pool_id)
        return pools 