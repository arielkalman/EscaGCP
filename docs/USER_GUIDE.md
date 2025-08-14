# User Guide

Complete guide to using EscaGCP for GCP security analysis.

## Table of Contents

1. [Overview](#overview)
2. [Command Reference](#command-reference)
3. [Workflow Examples](#workflow-examples)
4. [Advanced Features](#advanced-features)
5. [Continuous Monitoring](#continuous-monitoring)
6. [Integration](#integration)
7. [Best Practices](#best-practices)

## Overview

EscaGCP follows a four-step workflow:
1. **Collect** - Gather data from GCP
2. **Build** - Create a graph from collected data
3. **Analyze** - Find attack paths and risks
4. **Visualize** - Create interactive reports

## Command Reference

### Global Options

```bash
escagcp [--config CONFIG_FILE] [--debug] COMMAND [OPTIONS]
```

- `--config`: Path to configuration file
- `--debug`: Enable debug logging

### Commands

#### `run` - Automatic Execution

```bash
escagcp run [--lazy] [--projects PROJECTS] [--open-browser]
```

Runs all operations automatically when `--lazy` is specified.

**Options**:
- `--lazy`: Run all steps automatically
- `--projects`: Comma-separated project IDs
- `--open-browser`: Open visualization after completion

**Example**:
```bash
escagcp run --lazy --projects prod-project,dev-project --open-browser
```

#### `collect` - Data Collection

```bash
escagcp collect [--organization ORG_ID] [--folders FOLDER_IDS] 
                [--projects PROJECT_IDS] [--output DIR]
                [--include-logs] [--log-days N]
```

Collects IAM and resource data from GCP.

**Options**:
- `--organization`: Organization ID to scan
- `--folders`: Comma-separated folder IDs
- `--projects`: Comma-separated project IDs
- `--output`: Output directory (default: data/)
- `--include-logs`: Include audit log collection
- `--log-days`: Days of logs to collect (default: 7)

**Examples**:
```bash
# Scan organization
escagcp collect --organization 123456789

# Scan specific projects with logs
escagcp collect --projects project1,project2 --include-logs --log-days 30

# Scan folders
escagcp collect --folders folder1,folder2 --output custom-data/
```

#### `build-graph` - Graph Construction

```bash
escagcp build-graph --input DIR --output DIR
```

Builds a graph from collected data.

**Options**:
- `--input`: Input directory with collected data
- `--output`: Output directory for graph files

**Example**:
```bash
escagcp build-graph --input data/ --output graph/
```

#### `analyze` - Attack Path Analysis

```bash
escagcp analyze --graph GRAPH_FILE [--output DIR] [--format FORMAT]
```

Analyzes the graph for attack paths and vulnerabilities.

**Options**:
- `--graph`: Path to graph file (supports wildcards)
- `--output`: Output directory
- `--format`: Output format (json, html, text)

**Example**:
```bash
escagcp analyze --graph graph/escagcp_graph_*.json --format html
```

#### `visualize` - Create visualizations

```bash
escagcp visualize --graph GRAPH_FILE [--output DIR] [--type TYPE]
```

Creates interactive visualizations.

**Options**:
- `--graph`: Path to graph file
- `--output`: Output directory
- `--type`: Visualization type (full, attack-paths, risk)

**Example**:
```bash
escagcp visualize --graph graph/escagcp_graph_*.json --type attack-paths
```

#### `query` - Query the Graph

```bash
escagcp query --graph GRAPH_FILE --from IDENTITY [--to TARGET] --type TYPE
```

Query the graph for specific information.

**Options**:
- `--graph`: Path to graph file
- `--from`: Source identity
- `--to`: Target resource (for path queries)
- `--type`: Query type (paths, permissions, access)

**Examples**:
```bash
# Find paths between identities
escagcp query --graph graph/*.json \
  --from "user:alice@example.com" \
  --to "projects/production" \
  --type paths

# Check what a user can access
escagcp query --graph graph/*.json \
  --from "user:bob@example.com" \
  --type access
```

#### `simulate` - What-If Analysis

```bash
escagcp simulate --graph GRAPH_FILE --action ACTION 
                 --member MEMBER --role ROLE --resource RESOURCE
                 [--new-role NEW_ROLE]
```

Simulate IAM changes to understand impact.

**Options**:
- `--action`: Action to simulate (add, remove, change)
- `--member`: Member identity
- `--role`: Role name
- `--resource`: Target resource
- `--new-role`: New role (for change action)

**Example**:
```bash
escagcp simulate --graph graph/*.json \
  --action add \
  --member "user:contractor@example.com" \
  --role "roles/compute.admin" \
  --resource "projects/production"
```

#### `export` - Export Reports

```bash
escagcp export --graph GRAPH_FILE --output FILE [--title TITLE]
```

Export a standalone HTML report.

**Options**:
- `--graph`: Path to graph file
- `--output`: Output file name

**Example** (Example output file):
```bash
escagcp export --graph graph/escagcp_graph_*.json --output security-report.html
```

#### `cleanup` - Clean Generated Files

```bash
escagcp cleanup [--force] [--dry-run]
```

Remove all generated files and data.

**Options**:
- `--force`: Skip confirmation
- `--dry-run`: Show what would be deleted

## Workflow Examples

### Example 1: Organization-Wide Security Audit

```bash
# 1. Collect data from entire organization
escagcp collect --organization 123456789 --include-logs

# 2. Build graph
escagcp build-graph --input data/ --output graph/

# 3. Analyze
escagcp analyze --graph graph/*.json --format html

# 4. Create visualizations
escagcp visualize --graph graph/*.json --type full

# 5. Export shareable report
escagcp export --graph graph/*.json \
  --output org-security-audit.html \
  --title "Organization Security Audit"
```

### Example 2: Project-Specific Investigation

```bash
# Quick scan of suspicious project
escagcp run --lazy --projects suspicious-project

# Query specific user access
escagcp query --graph graph/*.json \
  --from "user:suspicious@example.com" \
  --type access

# Simulate removing their access
escagcp simulate --graph graph/*.json \
  --action remove \
  --member "user:suspicious@example.com" \
  --role "roles/editor" \
  --resource "projects/suspicious-project"
```

### Example 3: Continuous Monitoring Setup

Create `monitor.sh`:
```bash
#!/bin/bash
set -e

# Configuration
ORG_ID="123456789"
ALERT_EMAIL="security@example.com"
THRESHOLD_CRITICAL=5

# Run collection
escagcp collect --organization $ORG_ID --include-logs --log-days 1

# Build and analyze
escagcp build-graph --input data/ --output graph/
escagcp analyze --graph graph/*.json --format json --output findings/

# Check for critical findings
CRITICAL_COUNT=$(jq '.statistics.critical_paths // 0' findings/escagcp_analysis_*.json)

if [ $CRITICAL_COUNT -gt $THRESHOLD_CRITICAL ]; then
    # Send alert
    escagcp export --graph graph/*.json --output alert-report.html
    echo "Critical security findings detected!" | \
      mail -s "EscaGCP Alert: $CRITICAL_COUNT Critical Paths" \
      -a alert-report.html $ALERT_EMAIL
fi

# Archive results
mkdir -p archive/$(date +%Y%m%d)
mv data/* graph/* findings/* visualizations/* archive/$(date +%Y%m%d)/
```

Schedule with cron:
```bash
# Run daily at 2 AM
0 2 * * * /path/to/monitor.sh >> /var/log/escagcp-monitor.log 2>&1
```

## Advanced Features

### Custom Configuration

Create `config.yaml`:
```yaml
authentication:
  method: adc
  impersonate_service_account: scanner@security.iam.gserviceaccount.com

collection:
  max_projects: 100
  page_size: 500
  resource_types:
    - buckets
    - compute_instances
    - functions
    - secrets
    - kms_keys
    - bigquery_datasets
  
  # Advanced collection options
  collect_tags: true
  collect_cloudbuild: true
  collect_gke: true
  collect_workload_identity: true
  
  # Performance tuning
  concurrent_requests: 10
  retry_attempts: 3
  timeout_seconds: 300

analysis:
  max_path_length: 8
  risk_thresholds:
    critical: 0.8
    high: 0.6
    medium: 0.4
  
  # Detection settings
  detect_privilege_escalation: true
  detect_lateral_movement: true
  detect_data_exfiltration: true
  detect_persistence: true
  
  # Custom dangerous roles
  dangerous_roles:
    - roles/owner
    - roles/editor
    - roles/iam.securityAdmin
    - roles/iam.serviceAccountTokenCreator
    - roles/cloudfunctions.admin
    - roles/compute.admin
    - roles/container.admin

visualization:
  node_limit: 5000
  edge_limit: 10000
  layout: hierarchical
  
  # Custom colors
  node_colors:
    user: "#4285F4"
    service_account: "#34A853"
    group: "#FBBC04"
    project: "#EA4335"

output:
  directory: ./escagcp-results
  timestamp_format: "%Y%m%d_%H%M%S"
  
  # Report settings
  include_recommendations: true
  include_evidence: true
  include_remediation_scripts: true
```

### Python API Usage

```python
from escagcp import (
    Config, AuthManager, CollectionOrchestrator,
    GraphBuilder, PathAnalyzer, HTMLVisualizer
)

# Initialize with config
config = Config.from_yaml('config.yaml')
auth = AuthManager(config)
auth.authenticate()

# Collect data
collector = CollectionOrchestrator(auth, config)
data = collector.collect_all(
    organization_id='123456789',
    include_folders=True
)

# Build graph
builder = GraphBuilder(config)
graph = builder.build_from_collected_data(data)

# Analyze
analyzer = PathAnalyzer(graph, config)
results = analyzer.analyze_all_paths()

# Find specific paths
paths = analyzer.find_privilege_escalation_paths(
    source='user:developer@example.com',
    target='projects/production'
)

# Create visualization
visualizer = HTMLVisualizer(graph, config)
visualizer.create_full_graph(
    'dashboard.html',
    risk_scores=results['risk_scores'],
    attack_paths=results['attack_paths']
)
```

### Integration with Other Tools

#### Export to Neo4j

```bash
# Export graph for Neo4j import
escagcp build-graph --input data/ --output neo4j_export/

# Import with neo4j-admin
neo4j-admin import \
  --nodes=neo4j_export/nodes.csv \
  --relationships=neo4j_export/edges.csv \
  --database=escagcp

# Query in Cypher
MATCH path = (u:User)-[:CAN_IMPERSONATE_SA*1..3]->(p:Project)
WHERE u.email = 'risky@example.com'
RETURN path
```

#### Integration with SIEM

```python
# Send findings to SIEM
import requests
from escagcp import PathAnalyzer

# Analyze
analyzer = PathAnalyzer(graph, config)
results = analyzer.analyze_all_paths()

# Send to SIEM
for category, paths in results['attack_paths'].items():
    for path in paths:
        if path.risk_score > 0.8:
            requests.post('https://siem.example.com/api/alerts', json={
                'severity': 'critical',
                'category': 'privilege_escalation',
                'source': 'escagcp',
                'details': {
                    'path': path.get_path_string(),
                    'risk_score': path.risk_score,
                    'technique': path.technique
                }
            })
```

## Continuous Monitoring

### Setting Up Automated Scans

1. **Create Service Account**:
```bash
# Create SA for scanning
gcloud iam service-accounts create escagcp-scanner \
  --display-name="EscaGCP Automated Scanner"

# Grant permissions
gcloud organizations add-iam-policy-binding ORG_ID \
  --member="serviceAccount:escagcp-scanner@PROJECT.iam.gserviceaccount.com" \
  --role="roles/viewer"

gcloud organizations add-iam-policy-binding ORG_ID \
  --member="serviceAccount:escagcp-scanner@PROJECT.iam.gserviceaccount.com" \
  --role="roles/iam.securityReviewer"
```

2. **Deploy to Cloud Run**:
```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["escagcp", "run", "--lazy", "--config", "/config/config.yaml"]
```

3. **Schedule with Cloud Scheduler**:
```bash
gcloud scheduler jobs create http escagcp-daily-scan \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri="https://escagcp-scanner-xxx.run.app/scan" \
  --http-method=POST
```

### Alerting on Findings

Create alert rules based on:
- New critical attack paths
- Changes in risk scores
- New external access
- Privilege escalations

Example alert configuration:
```yaml
alerts:
  - name: critical_paths
    condition: statistics.critical_paths > 0
    severity: critical
    notification:
      - email: security@example.com
      - slack: security-alerts
      
  - name: external_access
    condition: external_users.count > previous.external_users.count
    severity: high
    notification:
      - pagerduty: security-team
```

## Best Practices

### 1. Regular Scanning
- Daily scans for production environments
- Weekly scans for development
- Monthly full organization scans

### 2. Baseline Management
- Establish security baselines
- Track deviations over time
- Document approved exceptions

### 3. Remediation Workflow
1. Identify critical findings
2. Validate with stakeholders
3. Test remediation in dev
4. Apply fixes with change control
5. Re-scan to verify

### 4. Performance Optimization
- Use `--projects` to limit scope
- Enable caching for large environments
- Adjust concurrent requests in config
- Use incremental scanning

### 5. Security Considerations
- Store outputs securely
- Encrypt sensitive reports
- Limit access to findings
- Audit scanner access

## Troubleshooting

### Common Issues

**Large Environment Timeout**:
```yaml
# Increase timeouts in config
collection:
  timeout_seconds: 600
  max_retries: 5
```

**Memory Issues**:
```bash
# Increase memory for large graphs
export ESCAGCP_MAX_MEMORY=8G
escagcp analyze --graph large-graph.json
```

**API Rate Limits**:
```yaml
# Adjust rate limiting
performance:
  rate_limit:
    requests_per_second: 5
    burst_size: 10
```

### Debug Mode

Enable detailed logging:
```bash
# Set log level
export ESCAGCP_LOG_LEVEL=DEBUG

# Or use flag
escagcp --debug collect --projects my-project

# Save debug logs
escagcp --debug analyze --graph graph/*.json 2> debug.log
```

## Next Steps

- Review [Attack Techniques](ATTACK_TECHNIQUES.md) to understand findings
- Configure [continuous monitoring](#continuous-monitoring)
- Integrate with your security tools
- Customize detection rules in [Configuration](CONFIGURATION.md) 