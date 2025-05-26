# EscaGCP 🔍

EscaGCP (formerly GCPHound) is a comprehensive graph-based analysis tool for Google Cloud Platform (GCP) that maps IAM relationships and permissions to reveal potential attack paths, similar to BloodHound for Active Directory environments.

## 🚀 Features

### Core Capabilities
- **Comprehensive Data Collection**: Collects IAM policies, resource configurations, and identity relationships across GCP
- **Graph-Based Analysis**: Builds a directed graph of all relationships and permissions
- **Attack Path Discovery**: Identifies privilege escalation and lateral movement opportunities
- **Risk Scoring**: Calculates risk scores for nodes and paths based on permissions and centrality
- **What-If Analysis**: Simulates IAM changes to understand security impact

### Attack Path Detection

GCPHound detects all known GCP privilege escalation and lateral movement techniques:

#### 1. **Service Account Impersonation** (`CAN_IMPERSONATE_SA`)
- Detects `roles/iam.serviceAccountTokenCreator` permissions
- Identifies impersonation chains
- Maps Workload Identity Federation paths

#### 2. **Service Account Key Creation** (`CAN_CREATE_KEY`)
- Finds `roles/iam.serviceAccountKeyAdmin` permissions
- Identifies paths to create and exfiltrate SA keys

#### 3. **ActAs Privilege Escalation** (`CAN_ACT_AS_VIA_VM`)
- Detects combinations of `roles/iam.serviceAccountUser` with deployment permissions
- Maps VM, Cloud Function, and Cloud Run deployment paths

#### 4. **Cloud Function Deployment** (`CAN_DEPLOY_FUNCTION_AS`)
- Identifies `roles/cloudfunctions.developer` with SA access
- Detects backdoor deployment opportunities

#### 5. **Cloud Build Exploitation** (`CAN_TRIGGER_BUILD_AS`)
- Maps access to Cloud Build service accounts
- Detects `cloudbuild.builds.create` permissions
- Identifies default Cloud Build SA with Editor role

#### 6. **VM Token Theft** (`CAN_LOGIN_TO_VM` + `RUNS_AS`)
- Detects OS Login and IAP tunnel access
- Maps VMs to their service accounts
- Identifies metadata server exploitation paths

#### 7. **Tag-Based Privilege Escalation** (`CAN_MODIFY_TAG`)
- Finds `roles/resourcemanager.tagUser` permissions
- Detects IAM conditions using `resource.matchTag()`
- Maps tag manipulation paths

#### 8. **Workload Identity Federation** (`CAN_CONFIGURE_WORKLOAD_IDENTITY`)
- Maps GKE clusters with Workload Identity
- Detects K8s SA to GCP SA bindings
- Identifies federation abuse paths

#### 9. **Organization Policy Bypass** (`CAN_BYPASS_ORG_POLICY`)
- Detects `roles/orgpolicy.policyAdmin` access
- Maps policy modification capabilities

#### 10. **Custom Role Creation** (`CAN_CREATE_CUSTOM_ROLE`)
- Finds `roles/iam.roleAdmin` permissions
- Detects arbitrary permission granting

### Additional Features
- **Cross-Project Access Analysis**: Maps permissions across project boundaries
- **External Access Detection**: Identifies access from external domains
- **Lateral Movement Mapping**: Finds multi-hop paths between resources
- **Data Exfiltration Risk**: Identifies paths to sensitive data
- **Blast Radius Analysis**: Calculates impact of node compromise

## 📋 Requirements

- Python 3.8+
- GCP credentials with appropriate permissions
- Required APIs enabled in target projects

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/arielkalman/EscaGCP.git
cd EscaGCP

# Install the package
pip install -e .

# Or install from PyPI (when published)
pip install gcphound
```

## 🚀 Getting Started

### 1. Prerequisites

Before running GCPHound, ensure you have:

1. **GCP Authentication**: You need to be authenticated to GCP with appropriate permissions
2. **Required APIs**: Enable the following APIs in your GCP projects:
   - Cloud Resource Manager API
   - Identity and Access Management (IAM) API
   - Cloud Identity API (for group enumeration)
   - Admin SDK API (optional, for advanced group features)
   - Cloud Asset API (optional, for asset inventory)

### 2. Authentication Setup

GCPHound supports multiple authentication methods:

#### Option A: Application Default Credentials (Recommended)
```bash
# Login with your Google account
gcloud auth login

# Set application default credentials
gcloud auth application-default login

# Set your default project (optional)
gcloud config set project YOUR_PROJECT_ID
```

#### Option B: Service Account Key
```bash
# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Or specify in config file (see Configuration section)
```

### 3. Basic Usage

#### Quick Start - Scan Current Project

##### Option A: Automatic (Lazy) Mode 🚀
```bash
# Run all operations automatically and open visualization in Chrome
gcphound run --lazy

# Or specify projects explicitly
gcphound run --lazy --projects project1,project2
```

##### Option B: Manual Steps
```bash
# Scan the current project
gcphound collect --projects $(gcloud config get-value project)

# Build and analyze the graph
gcphound build-graph --input data/ --output graph/
gcphound analyze --graph graph/gcphound_graph_*.json --output findings/

# Create visualization
gcphound visualize --graph graph/gcphound_graph_*.json --output visualizations/
```

#### Scan Entire Organization
```bash
# Get your organization ID
ORG_ID=$(gcloud organizations list --format="value(name)" | cut -d'/' -f2)

# Scan the organization
gcphound collect --organization $ORG_ID --output data/

# Analyze with all features
gcphound analyze --graph graph/gcphound_graph_*.json --format html --output findings/
```

#### Scan Specific Projects
```bash
# Scan multiple projects
gcphound collect --projects project1,project2,project3 --output data/

# Include audit logs (requires logging permissions)
gcphound collect --projects project1,project2 --include-logs --log-days 30
```

### 4. Step-by-Step Workflow

#### Step 1: Data Collection
Collect IAM and resource data from GCP:

```bash
# Basic collection
gcphound collect --projects YOUR_PROJECT_ID

# With organization hierarchy
gcphound collect --organization YOUR_ORG_ID --include-folders

# With specific configuration
gcphound --config config.yaml collect --projects YOUR_PROJECT_ID
```

#### Step 2: Build Graph
Convert collected data into a graph:

```bash
# Build graph from latest collection
gcphound build-graph --input data/ --output graph/

# The graph will be saved in multiple formats:
# - GraphML (for Gephi, yEd)
# - JSON (for custom processing)
# - Neo4j CSV (for Neo4j import)
```

#### Step 3: Analyze
Find attack paths and vulnerabilities:

```bash
# Basic analysis
gcphound analyze --graph graph/gcphound_graph_*.json

# Generate HTML report
gcphound analyze --graph graph/gcphound_graph_*.json --format html

# Generate text report
gcphound analyze --graph graph/gcphound_graph_*.json --format text
```

#### Step 4: Visualize
Create interactive visualizations:

```bash
# Full graph visualization
gcphound visualize --graph graph/gcphound_graph_*.json --type full

# Attack paths only
gcphound visualize --graph graph/gcphound_graph_*.json --type attack-paths

# Risk-based visualization
gcphound visualize --graph graph/gcphound_graph_*.json --type risk
```

#### Step 5: Query and Simulate
Query the graph and simulate changes:

```bash
# Find paths between identities
gcphound query --graph graph/gcphound_graph_*.json \
  --from "user:alice@example.com" \
  --to "projects/production" \
  --type paths

# Check what a user can access
gcphound query --graph graph/gcphound_graph_*.json \
  --from "user:bob@example.com" \
  --type access

# Simulate adding a binding
gcphound simulate --graph graph/gcphound_graph_*.json \
  --action add \
  --member "user:eve@example.com" \
  --role "roles/iam.serviceAccountTokenCreator" \
  --resource "projects/production"
```

### 5. Advanced Usage

#### Custom Configuration
Create a `config.yaml` file for advanced settings:

```yaml
# config.yaml
authentication:
  method: adc  # or 'service_account'
  # service_account_key_file: /path/to/key.json
  # impersonate_service_account: automation@project.iam.gserviceaccount.com

collection:
  max_projects: 50  # Limit number of projects
  page_size: 100
  resource_types:
    - buckets
    - compute_instances
    - functions
    - secrets
    - kms_keys
  include_logs: true
  log_days_back: 30

analysis:
  max_path_length: 6
  detect_privilege_escalation: true
  detect_lateral_movement: true
  dangerous_roles:
    - roles/owner
    - roles/editor
    - roles/iam.securityAdmin
    - roles/iam.serviceAccountTokenCreator
    - roles/cloudfunctions.admin

output:
  directory: ./gcphound-results
  formats:
    - json
    - graphml
    - html
```

Run with configuration:
```bash
gcphound --config config.yaml collect --organization YOUR_ORG_ID
```

#### Continuous Monitoring
Set up a cron job for regular scans:

```bash
# Create a script
cat > /path/to/gcphound-scan.sh << 'EOF'
#!/bin/bash
cd /path/to/gcphound
source venv/bin/activate

# Run collection
gcphound --config config.yaml collect --organization YOUR_ORG_ID

# Analyze
LATEST_GRAPH=$(ls -t graph/gcphound_graph_*.json | head -1)
gcphound analyze --graph "$LATEST_GRAPH" --format html

# Send alerts if critical findings
# ... add your alerting logic here
EOF

chmod +x /path/to/gcphound-scan.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/gcphound-scan.sh") | crontab -
```

#### Import to Neo4j
```bash
# Export for Neo4j
gcphound build-graph --input data/ --output neo4j_import/

# Import using neo4j-admin
neo4j-admin import \
  --nodes=neo4j_import/nodes.csv \
  --relationships=neo4j_import/edges.csv \
  --database=gcphound

# Or use Cypher import
gcphound export --graph graph/gcphound_graph_*.json --format cypher --output import.cypher
cypher-shell -f import.cypher
```

### 6. Troubleshooting

#### Common Issues

1. **Authentication Errors**
   ```bash
   # Check current authentication
   gcloud auth list
   gcloud auth application-default print-access-token
   
   # Re-authenticate if needed
   gcloud auth application-default login
   ```

2. **API Not Enabled**
   ```bash
   # Enable required APIs
   gcloud services enable cloudresourcemanager.googleapis.com
   gcloud services enable iam.googleapis.com
   gcloud services enable cloudidentity.googleapis.com
   ```

3. **Permission Denied**
   - Ensure your account has at least these roles:
     - `roles/viewer` on target projects
     - `roles/iam.securityReviewer` for detailed IAM analysis
     - `roles/resourcemanager.organizationViewer` for org-level scan

4. **Rate Limiting**
   - Adjust rate limits in config:
     ```yaml
     performance:
       rate_limit:
         requests_per_second: 5
         burst_size: 10
     ```

#### Debug Mode
Run with debug logging:
```bash
# Set log level
export GCPHOUND_LOG_LEVEL=DEBUG

# Or use --debug flag
gcphound --debug collect --projects YOUR_PROJECT_ID
```

### 7. Output Files

GCPHound generates several output files:

- **Collection Phase**:
  - `data/gcphound_complete_TIMESTAMP.json` - All collected data
  - `data/gcphound_hierarchy_TIMESTAMP.json` - Organization/folder/project structure
  - `data/gcphound_iam_TIMESTAMP.json` - IAM policies and bindings
  - `data/gcphound_identity_TIMESTAMP.json` - Users, groups, service accounts

- **Graph Phase**:
  - `graph/gcphound_graph_TIMESTAMP.graphml` - Graph in GraphML format
  - `graph/gcphound_graph_TIMESTAMP.json` - Graph in JSON format

- **Analysis Phase**:
  - `findings/gcphound_analysis_TIMESTAMP.json` - Analysis results
  - `findings/gcphound_analysis_TIMESTAMP.html` - HTML report
  - `findings/gcphound_analysis_TIMESTAMP.txt` - Text report

- **Visualization Phase**:
  - `visualizations/gcphound_graph_TIMESTAMP.html` - Interactive graph
  - `visualizations/gcphound_attack_paths_TIMESTAMP.html` - Attack paths only
  - `visualizations/gcphound_risk_TIMESTAMP.graphml` - Risk-colored graph

### 8. Cleaning Up

To remove all generated files and start fresh:

```bash
# Preview what will be deleted
gcphound cleanup --dry-run

# Clean up with confirmation prompt
gcphound cleanup

# Force cleanup without confirmation
gcphound cleanup --force
```

The cleanup command will remove:
- All collected data (`data/` directory)
- Generated graphs (`graph/` directory)
- Analysis findings (`findings/` directory)
- Visualizations (`visualizations/` directory)
- Test outputs and temporary files
- Python cache files and coverage reports

⚠️ **Warning**: This action cannot be undone! All collected data and analysis results will be permanently deleted.

## 🔧 Configuration

Create a configuration file (optional):

```yaml
# config.yaml
authentication:
  method: adc  # or 'service_account'
  service_account_file: /path/to/key.json

collection:
  collect_tags: true
  collect_cloudbuild: true
  collect_gke: true

analysis:
  detect_privilege_escalation: true
  detect_lateral_movement: true
  detect_tag_escalation: true
  max_path_length: 6

export:
  formats:
    - graphml
    - json
    - neo4j_csv
```

## 🚀 Usage

### Command Line Interface

```bash
# Basic scan of an organization
gcphound collect --organization YOUR_ORG_ID

# Scan specific projects
gcphound collect --projects project1,project2,project3

# Full analysis with all features
gcphound analyze --config config.yaml --output results/

# What-if analysis
gcphound simulate --add-binding "user:alice@example.com,roles/owner,projects/prod"

# Export to Neo4j
gcphound export --format neo4j --output neo4j_import/

# Clean up all generated files and data
gcphound cleanup  # Interactive confirmation
gcphound cleanup --force  # Skip confirmation
gcphound cleanup --dry-run  # Preview what will be deleted
```

### Python API

```python
from gcphound import GCPHound

# Initialize
hound = GCPHound(config_file='config.yaml')

# Collect data
data = hound.collect(
    organization_id='123456789',
    include_folders=['folder1', 'folder2']
)

# Build graph
graph = hound.build_graph(data)

# Analyze
results = hound.analyze(graph)

# Find specific attack paths
paths = hound.find_privilege_escalation_paths('user:alice@example.com')

# Simulate IAM changes
impact = hound.simulate_binding_addition(
    member='user:bob@example.com',
    role='roles/iam.serviceAccountTokenCreator',
    resource='projects/prod'
)
```

## 📊 Output Formats

### GraphML
- Compatible with Gephi, yEd, and other graph visualization tools
- Includes all node and edge attributes
- Preserves risk scores and attack paths

### Neo4j
- CSV files for `neo4j-admin import`
- Cypher scripts for direct import
- Includes indexes and constraints

### JSON
- Complete graph data with metadata
- Attack paths and risk scores
- Recommendations and vulnerabilities

### HTML Visualization
- Interactive graph visualization
- Risk score heat maps
- Attack path highlighting
- Search and filter capabilities

## 🔍 Example Findings

### Service Account Impersonation Chain
```
user:alice@example.com 
  → [CAN_IMPERSONATE_SA] → serviceAccount:dev-sa@project.iam
    → [CAN_IMPERSONATE_SA] → serviceAccount:prod-sa@project.iam
      → [CAN_ADMIN] → projects/production
```

### Cloud Build Privilege Escalation
```
user:developer@example.com
  → [CAN_TRIGGER_BUILD_AS] → serviceAccount:123@cloudbuild.gserviceaccount.com
    → [HAS_ROLE: roles/editor] → projects/production
```

### Tag-Based Condition Bypass
```
user:bob@example.com
  → [CAN_MODIFY_TAG] → tagValue:environment/prod
    → [SATISFIES_CONDITION] → conditional_binding
      → [CAN_ADMIN] → bucket:sensitive-data
```

## 🛡️ Security Best Practices

Based on GCPHound findings, we recommend:

1. **Disable Service Account Key Creation**
   ```bash
   gcloud resource-manager org-policies enable-enforce \
     constraints/iam.disableServiceAccountKeyCreation \
     --organization=ORG_ID
   ```

2. **Use Workload Identity Instead of Keys**
   - For GKE workloads
   - For external applications via Workload Identity Federation

3. **Restrict Service Account Impersonation**
   - Limit `iam.serviceAccountTokenCreator` grants
   - Use short-lived tokens

4. **Secure Cloud Build**
   - Use custom service accounts with minimal permissions
   - Enable Binary Authorization
   - Audit build configurations

5. **Implement Tag Governance**
   - Restrict `resourcemanager.tagUser` permissions
   - Audit IAM conditions using tags
   - Use tag holds for critical tags

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repo
git clone https://github.com/arielkalman/EscaGCP.git
cd EscaGCP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 gcphound/
black gcphound/
```

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [BloodHound](https://github.com/BloodHoundAD/BloodHound)
- Built on research from:
  - [GCP Privilege Escalation](https://rhinosecuritylabs.com/gcp/privilege-escalation-google-cloud-platform-part-1/)
  - [GCP IAM Security](https://cloud.google.com/iam/docs/best-practices)
  - [Cloud Security Research](https://github.com/carlospolop/hacktricks-cloud)

## ⚠️ Disclaimer

This tool is for authorized security assessments only. Users are responsible for complying with all applicable laws and regulations.

## 📧 Contact

- Issues: [GitHub Issues](https://github.com/arielkalman/EscaGCP/issues)
- Security: security@example.com

---

**Note**: GCPHound requires appropriate IAM permissions to collect data. Ensure you have the necessary access before running scans.

## Project Structure

```
GCPHound/
├── gcphound/                 # Main package directory
│   ├── __init__.py
│   ├── cli.py               # Command-line interface
│   ├── analyzers/           # Attack path analysis
│   │   ├── __init__.py
│   │   └── paths.py
│   ├── collectors/          # GCP data collectors
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── iam.py
│   │   ├── hierarchy.py
│   │   ├── identity.py
│   │   ├── resources.py
│   │   ├── logs_collector.py
│   │   ├── tags_collector.py
│   │   ├── cloudbuild_collector.py
│   │   ├── gke_collector.py
│   │   └── orchestrator.py
│   ├── config/              # Configuration files
│   │   ├── default.yaml
│   │   └── permissions.yaml
│   ├── graph/               # Graph building and querying
│   │   ├── __init__.py
│   │   ├── builder.py
│   │   ├── exporter.py
│   │   ├── models.py
│   │   └── query.py
│   ├── utils/               # Utility modules
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── retry.py
│   └── visualizers/         # Visualization modules
│       ├── __init__.py
│       ├── html.py
│       └── graphml.py
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── analyzers/
│   ├── collectors/
│   ├── graph/
│   ├── utils/
│   └── visualizers/
├── docs/                    # Documentation
│   ├── examples/           # Example reports
│   ├── LAZY_MODE_DEMO.md
│   ├── SHARING_REPORTS.md
│   └── ...
├── setup.py                # Package setup
├── requirements.txt        # Dependencies
├── pytest.ini             # Test configuration
├── README.md              # This file
└── .gitignore            # Git ignore rules
```

### Output Directories (created at runtime)
- `data/` - Collected GCP data
- `graph/` - Built graph files
- `findings/` - Analysis results
- `visualizations/` - HTML visualizations

## 🔒 Security Notice

⚠️ **Important**: GCPHound collects sensitive information about your GCP environment including project IDs, service account emails, user identities, and IAM permissions. 

**Before sharing any outputs or publishing code modifications**, please review the [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) file to ensure no sensitive data is exposed.

Use the cleanup command to remove all collected data:
```bash
gcphound cleanup --force
``` 