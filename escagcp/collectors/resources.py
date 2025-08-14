"""
Collector for GCP resources (buckets, instances, functions, etc.)
"""

from typing import Dict, Any, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from googleapiclient.errors import HttpError
from .base import BaseCollector
from ..utils import get_logger, ProgressLogger


logger = get_logger(__name__)


class ResourceCollector(BaseCollector):
    """
    Collects various GCP resources and their IAM policies
    """
    
    def collect(
        self,
        project_ids: List[str],
        resource_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Collect resource data
        
        Args:
            project_ids: List of project IDs to collect resources from
            resource_types: List of resource types to collect (None for all configured)
            
        Returns:
            Dictionary containing resource data
        """
        self._start_collection()
        
        # Use configured resource types if not specified
        if resource_types is None:
            resource_types = self.config.collection_resource_types
        
        # Initialize data structures
        self._collected_data = {
            'resources': {
                'buckets': {},
                'compute_instances': {},
                'functions': {},
                'pubsub_topics': {},
                'bigquery_datasets': {},
                'kms_keys': {},
                'secrets': {}
            },
            'resource_iam_policies': {},  # resource_uri -> IAM policy
            'resource_summary': {
                'by_type': {},
                'by_project': {}
            }
        }
        
        try:
            # Collect resources based on types
            collectors = {
                'buckets': self._collect_buckets,
                'compute_instances': self._collect_compute_instances,
                'functions': self._collect_cloud_functions,
                'pubsub_topics': self._collect_pubsub_topics,
                'bigquery_datasets': self._collect_bigquery_datasets,
                'kms_keys': self._collect_kms_keys,
                'secrets': self._collect_secrets
            }
            
            for resource_type in resource_types:
                if resource_type in collectors:
                    logger.info(f"Collecting {resource_type}")
                    collectors[resource_type](project_ids)
            
            # Build resource summary
            self._build_resource_summary()
            
        except Exception as e:
            logger.error(f"Error during resource collection: {e}")
            self._metadata['errors'].append({
                'error': str(e),
                'phase': 'collection'
            })
        
        self._end_collection()
        return self.get_collected_data()
    
    def _collect_buckets(self, project_ids: List[str]):
        """
        Collect Cloud Storage buckets
        """
        try:
            service = self.auth_manager.build_service('storage', 'v1')
            
            bucket_count = 0
            for project_id in project_ids:
                try:
                    request = service.buckets().list(
                        project=project_id,
                        maxResults=self.config.collection_page_size
                    )
                    
                    for bucket in self._paginate_list(request, 'items'):
                        bucket_name = bucket.get('name')
                        
                        # Store bucket data
                        self._collected_data['resources']['buckets'][bucket_name] = {
                            'name': bucket_name,
                            'id': bucket.get('id'),
                            'projectNumber': bucket.get('projectNumber'),
                            'location': bucket.get('location'),
                            'storageClass': bucket.get('storageClass'),
                            'timeCreated': bucket.get('timeCreated'),
                            'updated': bucket.get('updated'),
                            'labels': bucket.get('labels', {}),
                            'iamConfiguration': bucket.get('iamConfiguration', {}),
                            'lifecycle': bucket.get('lifecycle'),
                            'versioning': bucket.get('versioning'),
                            'encryption': bucket.get('encryption'),
                            'projectId': project_id
                        }
                        
                        # Collect bucket IAM policy
                        self._collect_bucket_iam_policy(bucket_name)
                        
                        bucket_count += 1
                    
                except HttpError as e:
                    if e.resp.status != 403:
                        logger.error(f"Error listing buckets in project {project_id}: {e}")
            
            self._update_stats('buckets_collected', bucket_count)
            
        except Exception as e:
            logger.error(f"Error collecting buckets: {e}")
    
    def _collect_bucket_iam_policy(self, bucket_name: str):
        """
        Collect IAM policy for a bucket
        """
        try:
            service = self.auth_manager.build_service('storage', 'v1')
            
            request = service.buckets().getIamPolicy(bucket=bucket_name)
            
            with self.rate_limiter:
                policy = self._execute_request(request)
            
            # Store IAM policy
            resource_uri = f"storage.googleapis.com/buckets/{bucket_name}"
            self._collected_data['resource_iam_policies'][resource_uri] = {
                'bindings': policy.get('bindings', []),
                'etag': policy.get('etag'),
                'version': policy.get('version', 1),
                'resourceType': 'bucket',
                'resourceName': bucket_name
            }
            
        except HttpError as e:
            logger.debug(f"Error getting IAM policy for bucket {bucket_name}: {e}")
    
    def _collect_compute_instances(self, project_ids: List[str]):
        """
        Collect Compute Engine instances
        """
        try:
            service = self.auth_manager.build_service('compute', 'v1')
            
            instance_count = 0
            for project_id in project_ids:
                try:
                    # Get all zones first
                    zones_request = service.zones().list(project=project_id)
                    zones = []
                    
                    for zone in self._paginate_list(zones_request, 'items'):
                        zones.append(zone['name'])
                    
                    # Collect instances from each zone
                    for zone in zones:
                        request = service.instances().list(
                            project=project_id,
                            zone=zone,
                            maxResults=self.config.collection_page_size
                        )
                        
                        for instance in self._paginate_list(request, 'items'):
                            instance_name = instance.get('name')
                            instance_id = f"{project_id}/{zone}/{instance_name}"
                            
                            # Store instance data
                            self._collected_data['resources']['compute_instances'][instance_id] = {
                                'name': instance_name,
                                'id': instance.get('id'),
                                'machineType': instance.get('machineType'),
                                'status': instance.get('status'),
                                'zone': zone,
                                'creationTimestamp': instance.get('creationTimestamp'),
                                'labels': instance.get('labels', {}),
                                'serviceAccounts': instance.get('serviceAccounts', []),
                                'networkInterfaces': instance.get('networkInterfaces', []),
                                'disks': instance.get('disks', []),
                                'metadata': instance.get('metadata', {}),
                                'tags': instance.get('tags', {}),
                                'projectId': project_id
                            }
                            
                            instance_count += 1
                    
                except HttpError as e:
                    if e.resp.status != 403:
                        logger.error(f"Error listing instances in project {project_id}: {e}")
            
            self._update_stats('compute_instances_collected', instance_count)
            
        except Exception as e:
            logger.error(f"Error collecting compute instances: {e}")
    
    def _collect_cloud_functions(self, project_ids: List[str]):
        """
        Collect Cloud Functions
        """
        try:
            service = self.auth_manager.build_service('cloudfunctions', 'v1')
            
            function_count = 0
            for project_id in project_ids:
                try:
                    # List all locations first
                    locations = ['us-central1', 'us-east1', 'us-east4', 'us-west1', 
                               'europe-west1', 'europe-west2', 'asia-east1', 'asia-northeast1']
                    
                    for location in locations:
                        parent = f"projects/{project_id}/locations/{location}"
                        request = service.projects().locations().functions().list(
                            parent=parent,
                            pageSize=self.config.collection_page_size
                        )
                        
                        try:
                            for function in self._paginate_list(request, 'functions'):
                                function_name = function.get('name')
                                
                                # Store function data
                                self._collected_data['resources']['functions'][function_name] = {
                                    'name': function_name,
                                    'description': function.get('description'),
                                    'sourceArchiveUrl': function.get('sourceArchiveUrl'),
                                    'sourceRepository': function.get('sourceRepository'),
                                    'entryPoint': function.get('entryPoint'),
                                    'runtime': function.get('runtime'),
                                    'timeout': function.get('timeout'),
                                    'availableMemoryMb': function.get('availableMemoryMb'),
                                    'serviceAccountEmail': function.get('serviceAccountEmail'),
                                    'updateTime': function.get('updateTime'),
                                    'versionId': function.get('versionId'),
                                    'labels': function.get('labels', {}),
                                    'environmentVariables': function.get('environmentVariables', {}),
                                    'httpsTrigger': function.get('httpsTrigger'),
                                    'eventTrigger': function.get('eventTrigger'),
                                    'status': function.get('status'),
                                    'projectId': project_id,
                                    'location': location
                                }
                                
                                # Collect function IAM policy
                                self._collect_function_iam_policy(function_name)
                                
                                function_count += 1
                        except HttpError:
                            # Location might not be available
                            continue
                    
                except HttpError as e:
                    if e.resp.status != 403:
                        logger.error(f"Error listing functions in project {project_id}: {e}")
            
            self._update_stats('functions_collected', function_count)
            
        except Exception as e:
            logger.error(f"Error collecting cloud functions: {e}")
    
    def _collect_function_iam_policy(self, function_name: str):
        """
        Collect IAM policy for a Cloud Function
        """
        try:
            service = self.auth_manager.build_service('cloudfunctions', 'v1')
            
            request = service.projects().locations().functions().getIamPolicy(
                resource=function_name
            )
            
            with self.rate_limiter:
                policy = self._execute_request(request)
            
            # Store IAM policy
            self._collected_data['resource_iam_policies'][function_name] = {
                'bindings': policy.get('bindings', []),
                'etag': policy.get('etag'),
                'version': policy.get('version', 1),
                'resourceType': 'function',
                'resourceName': function_name
            }
            
        except HttpError as e:
            logger.debug(f"Error getting IAM policy for function {function_name}: {e}")
    
    def _collect_pubsub_topics(self, project_ids: List[str]):
        """
        Collect Pub/Sub topics
        """
        try:
            service = self.auth_manager.build_service('pubsub', 'v1')
            
            topic_count = 0
            for project_id in project_ids:
                try:
                    project = f"projects/{project_id}"
                    request = service.projects().topics().list(
                        project=project,
                        pageSize=self.config.collection_page_size
                    )
                    
                    for topic in self._paginate_list(request, 'topics'):
                        topic_name = topic.get('name')
                        
                        # Store topic data
                        self._collected_data['resources']['pubsub_topics'][topic_name] = {
                            'name': topic_name,
                            'labels': topic.get('labels', {}),
                            'messageStoragePolicy': topic.get('messageStoragePolicy'),
                            'kmsKeyName': topic.get('kmsKeyName'),
                            'schemaSettings': topic.get('schemaSettings'),
                            'satisfiesPzs': topic.get('satisfiesPzs'),
                            'messageRetentionDuration': topic.get('messageRetentionDuration'),
                            'projectId': project_id
                        }
                        
                        # Collect topic IAM policy
                        self._collect_pubsub_topic_iam_policy(topic_name)
                        
                        topic_count += 1
                    
                except HttpError as e:
                    if e.resp.status != 403:
                        logger.error(f"Error listing topics in project {project_id}: {e}")
            
            self._update_stats('pubsub_topics_collected', topic_count)
            
        except Exception as e:
            logger.error(f"Error collecting Pub/Sub topics: {e}")
    
    def _collect_pubsub_topic_iam_policy(self, topic_name: str):
        """
        Collect IAM policy for a Pub/Sub topic
        """
        try:
            service = self.auth_manager.build_service('pubsub', 'v1')
            
            request = service.projects().topics().getIamPolicy(resource=topic_name)
            
            with self.rate_limiter:
                policy = self._execute_request(request)
            
            # Store IAM policy
            self._collected_data['resource_iam_policies'][topic_name] = {
                'bindings': policy.get('bindings', []),
                'etag': policy.get('etag'),
                'version': policy.get('version', 1),
                'resourceType': 'pubsub_topic',
                'resourceName': topic_name
            }
            
        except HttpError as e:
            logger.debug(f"Error getting IAM policy for topic {topic_name}: {e}")
    
    def _collect_bigquery_datasets(self, project_ids: List[str]):
        """
        Collect BigQuery datasets
        """
        try:
            service = self.auth_manager.build_service('bigquery', 'v2')
            
            dataset_count = 0
            for project_id in project_ids:
                try:
                    request = service.datasets().list(
                        projectId=project_id,
                        maxResults=self.config.collection_page_size
                    )
                    
                    for dataset in self._paginate_list(request, 'datasets'):
                        dataset_ref = dataset.get('datasetReference', {})
                        dataset_id = dataset_ref.get('datasetId')
                        
                        if dataset_id:
                            # Get full dataset details
                            detail_request = service.datasets().get(
                                projectId=project_id,
                                datasetId=dataset_id
                            )
                            
                            with self.rate_limiter:
                                dataset_details = self._execute_request(detail_request)
                            
                            # Store dataset data
                            full_dataset_id = f"{project_id}.{dataset_id}"
                            self._collected_data['resources']['bigquery_datasets'][full_dataset_id] = {
                                'id': dataset_id,
                                'projectId': project_id,
                                'friendlyName': dataset_details.get('friendlyName'),
                                'description': dataset_details.get('description'),
                                'location': dataset_details.get('location'),
                                'creationTime': dataset_details.get('creationTime'),
                                'lastModifiedTime': dataset_details.get('lastModifiedTime'),
                                'labels': dataset_details.get('labels', {}),
                                'access': dataset_details.get('access', []),
                                'defaultTableExpirationMs': dataset_details.get('defaultTableExpirationMs'),
                                'defaultPartitionExpirationMs': dataset_details.get('defaultPartitionExpirationMs'),
                                'defaultEncryptionConfiguration': dataset_details.get('defaultEncryptionConfiguration')
                            }
                            
                            dataset_count += 1
                    
                except HttpError as e:
                    if e.resp.status != 403:
                        logger.error(f"Error listing datasets in project {project_id}: {e}")
            
            self._update_stats('bigquery_datasets_collected', dataset_count)
            
        except Exception as e:
            logger.error(f"Error collecting BigQuery datasets: {e}")
    
    def _collect_kms_keys(self, project_ids: List[str]):
        """
        Collect Cloud KMS crypto keys
        """
        try:
            service = self.auth_manager.build_service('cloudkms', 'v1')
            
            key_count = 0
            for project_id in project_ids:
                try:
                    # List all locations
                    locations = ['global', 'us', 'europe', 'asia', 'us-central1', 
                               'us-east1', 'europe-west1', 'asia-east1']
                    
                    for location in locations:
                        parent = f"projects/{project_id}/locations/{location}"
                        
                        # List key rings
                        try:
                            keyring_request = service.projects().locations().keyRings().list(
                                parent=parent,
                                pageSize=self.config.collection_page_size
                            )
                            
                            for keyring in self._paginate_list(keyring_request, 'keyRings'):
                                keyring_name = keyring.get('name')
                                
                                # List crypto keys in the key ring
                                keys_request = service.projects().locations().keyRings().cryptoKeys().list(
                                    parent=keyring_name,
                                    pageSize=self.config.collection_page_size
                                )
                                
                                for key in self._paginate_list(keys_request, 'cryptoKeys'):
                                    key_name = key.get('name')
                                    
                                    # Store key data
                                    self._collected_data['resources']['kms_keys'][key_name] = {
                                        'name': key_name,
                                        'purpose': key.get('purpose'),
                                        'createTime': key.get('createTime'),
                                        'nextRotationTime': key.get('nextRotationTime'),
                                        'rotationPeriod': key.get('rotationPeriod'),
                                        'versionTemplate': key.get('versionTemplate'),
                                        'labels': key.get('labels', {}),
                                        'importOnly': key.get('importOnly'),
                                        'destroyScheduledDuration': key.get('destroyScheduledDuration'),
                                        'projectId': project_id,
                                        'location': location,
                                        'keyRing': keyring_name
                                    }
                                    
                                    # Collect key IAM policy
                                    self._collect_kms_key_iam_policy(key_name)
                                    
                                    key_count += 1
                        except HttpError:
                            # Location might not be available
                            continue
                    
                except HttpError as e:
                    if e.resp.status != 403:
                        logger.error(f"Error listing KMS keys in project {project_id}: {e}")
            
            self._update_stats('kms_keys_collected', key_count)
            
        except Exception as e:
            logger.error(f"Error collecting KMS keys: {e}")
    
    def _collect_kms_key_iam_policy(self, key_name: str):
        """
        Collect IAM policy for a KMS crypto key
        """
        try:
            service = self.auth_manager.build_service('cloudkms', 'v1')
            
            request = service.projects().locations().keyRings().cryptoKeys().getIamPolicy(
                resource=key_name
            )
            
            with self.rate_limiter:
                policy = self._execute_request(request)
            
            # Store IAM policy
            self._collected_data['resource_iam_policies'][key_name] = {
                'bindings': policy.get('bindings', []),
                'etag': policy.get('etag'),
                'version': policy.get('version', 1),
                'resourceType': 'kms_key',
                'resourceName': key_name
            }
            
        except HttpError as e:
            logger.debug(f"Error getting IAM policy for KMS key {key_name}: {e}")
    
    def _collect_secrets(self, project_ids: List[str]):
        """
        Collect Secret Manager secrets
        """
        try:
            service = self.auth_manager.build_service('secretmanager', 'v1')
            
            secret_count = 0
            for project_id in project_ids:
                try:
                    parent = f"projects/{project_id}"
                    request = service.projects().secrets().list(
                        parent=parent,
                        pageSize=self.config.collection_page_size
                    )
                    
                    for secret in self._paginate_list(request, 'secrets'):
                        secret_name = secret.get('name')
                        
                        # Store secret data (metadata only, not the actual secret value)
                        self._collected_data['resources']['secrets'][secret_name] = {
                            'name': secret_name,
                            'createTime': secret.get('createTime'),
                            'labels': secret.get('labels', {}),
                            'replication': secret.get('replication'),
                            'etag': secret.get('etag'),
                            'topics': secret.get('topics', []),
                            'expireTime': secret.get('expireTime'),
                            'ttl': secret.get('ttl'),
                            'rotation': secret.get('rotation'),
                            'versionAliases': secret.get('versionAliases', {}),
                            'annotations': secret.get('annotations', {}),
                            'projectId': project_id
                        }
                        
                        # Collect secret IAM policy
                        self._collect_secret_iam_policy(secret_name)
                        
                        secret_count += 1
                    
                except HttpError as e:
                    if e.resp.status != 403:
                        logger.error(f"Error listing secrets in project {project_id}: {e}")
            
            self._update_stats('secrets_collected', secret_count)
            
        except Exception as e:
            logger.error(f"Error collecting secrets: {e}")
    
    def _collect_secret_iam_policy(self, secret_name: str):
        """
        Collect IAM policy for a secret
        """
        try:
            service = self.auth_manager.build_service('secretmanager', 'v1')
            
            request = service.projects().secrets().getIamPolicy(resource=secret_name)
            
            with self.rate_limiter:
                policy = self._execute_request(request)
            
            # Store IAM policy
            self._collected_data['resource_iam_policies'][secret_name] = {
                'bindings': policy.get('bindings', []),
                'etag': policy.get('etag'),
                'version': policy.get('version', 1),
                'resourceType': 'secret',
                'resourceName': secret_name
            }
            
        except HttpError as e:
            logger.debug(f"Error getting IAM policy for secret {secret_name}: {e}")
    
    def _build_resource_summary(self):
        """
        Build summary of collected resources
        """
        logger.info("Building resource summary")
        
        # Count resources by type
        for resource_type, resources in self._collected_data['resources'].items():
            self._collected_data['resource_summary']['by_type'][resource_type] = len(resources)
        
        # Count resources by project
        for resource_type, resources in self._collected_data['resources'].items():
            for resource_id, resource_data in resources.items():
                project_id = resource_data.get('projectId')
                if project_id:
                    if project_id not in self._collected_data['resource_summary']['by_project']:
                        self._collected_data['resource_summary']['by_project'][project_id] = {}
                    
                    if resource_type not in self._collected_data['resource_summary']['by_project'][project_id]:
                        self._collected_data['resource_summary']['by_project'][project_id][resource_type] = 0
                    
                    self._collected_data['resource_summary']['by_project'][project_id][resource_type] += 1
        
        # Update total stats
        total_resources = sum(self._collected_data['resource_summary']['by_type'].values())
        self._update_stats('total_resources_collected', total_resources)
        self._update_stats('resource_iam_policies_collected', len(self._collected_data['resource_iam_policies'])) 