# Configuration Reference

This guide covers all configuration options available in EscaGCP.

## Configuration File

EscaGCP uses YAML configuration files to customize its behavior. You can specify a configuration file using:

```bash
escagcp --config config.yaml [command]
```

## Default Configuration

If no configuration file is specified, EscaGCP uses in-code defaults. The example below shows a representative baseline; actual defaults are defined in `escagcp/config/default.yaml` and `escagcp/utils/config.py`.

```yaml
# Default configuration
authentication:
  method: adc  # Application Default Credentials

collection:
  max_projects: 50
  page_size: 100
  timeout_seconds: 300
  retry_attempts: 3

analysis:
  max_path_length: 6
  risk_thresholds:
    critical: 0.8
    high: 0.6
    medium: 0.4
    low: 0.2

output:
  directory: ./
  timestamp_format: "%Y%m%d_%H%M%S"
```

## Configuration Sections

### Authentication

Configure how EscaGCP authenticates to GCP:

```yaml
authentication:
  # Authentication method: 'adc' or 'service_account'
  method: adc
  
  # For service account authentication
  service_account_key_file: /path/to/key.json
  
  # Impersonate a service account (optional)
  impersonate_service_account: scanner@project.iam.gserviceaccount.com
  
  # Scopes (defaults primarily read-only; see default.yaml)
  scopes:
    - https://www.googleapis.com/auth/cloud-platform
```

### Collection

Control data collection behavior:

```yaml
collection:
  # Maximum number of projects to scan
  max_projects: 100
  
  # API pagination size
  page_size: 500
  
  # Request timeout in seconds
  timeout_seconds: 60  # default.yaml
  
  # Number of retry attempts
  retry_attempts: 3
  
  # Concurrent API requests
  concurrent_requests: 10
  
  # Resource types to collect
  resource_types:
    - buckets
    - compute_instances
    - functions
    - secrets
    - kms_keys
    - bigquery_datasets
    - pubsub_topics
    - spanner_instances
    - sql_instances
  
  # Feature flags
  collect_tags: true
  collect_cloudbuild: true
  collect_gke: true
  collect_workload_identity: true
  collect_audit_logs: false
  
  # Audit log settings
  log_days_back: 7
  log_filter: |
    protoPayload.methodName:(
      "SetIamPolicy" OR
      "google.iam.admin.v1.CreateServiceAccountKey" OR
      "GenerateAccessToken"
    )
```

### Analysis

Configure attack path analysis:

```yaml
analysis:
  # Maximum path length to search
  max_path_length: 8
  
  # Risk score thresholds (code defaults)
  risk_thresholds:
    critical: 0.8
    high: 0.6
    medium: 0.4
    low: 0.2
  
  # Detection settings
  detect_privilege_escalation: true
  detect_lateral_movement: true
  detect_data_exfiltration: true
  detect_persistence: true
  detect_defense_evasion: true
  
  # Roles considered dangerous
  dangerous_roles:
    - roles/owner
    - roles/editor
    - roles/iam.securityAdmin
    - roles/iam.serviceAccountAdmin
    - roles/iam.serviceAccountTokenCreator
    - roles/iam.serviceAccountKeyAdmin
    - roles/resourcemanager.organizationAdmin
    - roles/resourcemanager.folderAdmin
    - roles/resourcemanager.projectIamAdmin
    - roles/compute.admin
    - roles/cloudfunctions.admin
    - roles/run.admin
    - roles/container.admin
    - roles/cloudbuild.builds.editor
  
  # Permissions considered dangerous
  dangerous_permissions:
    - iam.serviceAccounts.getAccessToken
    - iam.serviceAccountKeys.create
    - iam.serviceAccounts.actAs
    - resourcemanager.projects.setIamPolicy
    - compute.instances.create
    - cloudfunctions.functions.create
    - run.services.create
    - cloudbuild.builds.create
  
  # External domains to flag
  external_domains:
    - gmail.com
    - yahoo.com
    - hotmail.com
    - outlook.com
  
  # Scoring weights
  scoring_weights:
    technique_severity: 0.4
    path_length: 0.2
    target_sensitivity: 0.3
    required_effort: 0.1
```

### Visualization

Control visualization output:

```yaml
visualization:
  # Maximum nodes/edges to display
  node_limit: 5000
  edge_limit: 10000
  
  # Graph layout algorithm
  layout: hierarchical  # or 'force-directed', 'circular'
  
  # Node colors by type
  node_colors:
    user: "#4285F4"
    service_account: "#34A853"
    group: "#FBBC04"
    project: "#EA4335"
    folder: "#FF6D00"
    organization: "#9C27B0"
    role: "#757575"
    resource: "#00ACC1"
  
  # Edge colors by type
  edge_colors:
    has_role: "#757575"
    can_impersonate: "#F44336"
    can_admin: "#FF5722"
    member_of: "#9E9E9E"
    can_access: "#2196F3"
  
  # HTML dashboard settings
  dashboard:
    show_legend: true
    show_stats: true
    show_search: true
    enable_zoom: true
    enable_pan: true
    
  # Attack path visualization
  attack_paths:
    show_risk_scores: true
    show_techniques: true
    show_remediation: true
    max_paths_per_category: 50
```

### Output

Configure output settings:

```yaml
output:
  # Base output directory
  directory: ./escagcp-results
  
  # Timestamp format for filenames
  timestamp_format: "%Y%m%d_%H%M%S"
  
  # File naming patterns
  file_patterns:
    collection: "escagcp_complete_{timestamp}.json"
    graph: "escagcp_graph_{timestamp}"
    analysis: "escagcp_analysis_{timestamp}"
    visualization: "escagcp_{type}_{timestamp}.html"
  
  # Report settings
  reports:
    include_executive_summary: true
    include_technical_details: true
    include_recommendations: true
    include_evidence: true
    include_remediation_scripts: true
    
  # Export formats (supported by exporter)
  export_formats:
    - json
    - graphml
    - neo4j_csv
    - cypher
```

### Performance

Tune performance settings:

```yaml
performance:
  # Rate limiting
  rate_limit:
    requests_per_second: 10
    burst_size: 20
    
  # Caching
  cache:
    enabled: true
    directory: .cache/escagcp
    ttl_seconds: 3600
    
  # Memory management
  memory:
    max_graph_size_mb: 4096
    gc_threshold_mb: 1024
    
  # Threading
  threading:
    max_workers: 10
    queue_size: 1000
```

### Logging

Configure logging behavior:

```yaml
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: INFO
  
  # Log format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # Log destinations
  handlers:
    - type: console
      level: INFO
    - type: file
      level: DEBUG
      filename: escagcp.log
      max_bytes: 10485760  # 10MB
      backup_count: 5
      
  # Sensitive data masking
  mask_sensitive_data: true
  masked_fields:
    - email
    - serviceAccountEmail
    - projectId
```

## Environment Variables

You can override configuration using environment variables:

```bash
# Authentication
export ESCAGCP_AUTH_METHOD=service_account
export ESCAGCP_SERVICE_ACCOUNT_KEY=/path/to/key.json

# Collection
export ESCAGCP_MAX_PROJECTS=100
export ESCAGCP_CONCURRENT_REQUESTS=20

# Analysis
export ESCAGCP_MAX_PATH_LENGTH=10

# Output
export ESCAGCP_OUTPUT_DIR=/custom/output

# Logging
export ESCAGCP_LOG_LEVEL=DEBUG
```

## Configuration Examples

### Minimal Configuration

```yaml
# minimal.yaml
authentication:
  method: adc

collection:
  max_projects: 10
```

### Security-Focused Configuration

```yaml
# security.yaml
authentication:
  method: service_account
  service_account_key_file: /secure/path/key.json

collection:
  collect_audit_logs: true
  log_days_back: 30
  
analysis:
  max_path_length: 10
  detect_privilege_escalation: true
  detect_lateral_movement: true
  detect_data_exfiltration: true
  
output:
  directory: /secure/output
  reports:
    include_remediation_scripts: true
    
logging:
  mask_sensitive_data: true
```

### Performance-Optimized Configuration

```yaml
# performance.yaml
collection:
  concurrent_requests: 20
  page_size: 1000
  
performance:
  rate_limit:
    requests_per_second: 20
    burst_size: 50
  cache:
    enabled: true
    ttl_seconds: 7200
  threading:
    max_workers: 20
    
visualization:
  node_limit: 10000
  edge_limit: 20000
```

### CI/CD Configuration

```yaml
# cicd.yaml
authentication:
  method: service_account
  service_account_key_file: ${SA_KEY_PATH}

collection:
  max_projects: ${MAX_PROJECTS:-50}
  
analysis:
  risk_thresholds:
    critical: ${CRITICAL_THRESHOLD:-0.8}
    
output:
  directory: ${OUTPUT_DIR:-./results}
  export_formats:
    - json  # For parsing in CI
```

## Validation

Configuration keys not recognized by the current release are ignored at load time. Prefer keys present in `escagcp/config/default.yaml` and the fields in `escagcp/utils/config.py`.

## Best Practices

1. **Use separate configs for different environments**:
   ```bash
   escagcp --config config.prod.yaml collect --organization PROD_ORG
   escagcp --config config.dev.yaml collect --organization DEV_ORG
   ```

2. **Store sensitive values in environment variables**:
   ```yaml
   authentication:
     service_account_key_file: ${ESCAGCP_SA_KEY}
   ```

3. **Version control your configurations** (exclude sensitive data):
   ```bash
   git add config.yaml
   echo "config.prod.yaml" >> .gitignore
   ```

4. **Start with defaults and customize as needed**:
   - Begin with minimal configuration
   - Add sections as you need them
   - Document why you changed defaults

5. **Regular configuration reviews**:
   - Review dangerous roles list quarterly
   - Update external domains list
   - Adjust thresholds based on findings 