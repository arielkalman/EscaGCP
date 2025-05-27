# Frequently Asked Questions (FAQ)

## General Questions

### What is EscaGCP?

EscaGCP is a graph-based security analysis tool for Google Cloud Platform (GCP) that maps IAM relationships and permissions to identify attack paths and privilege escalation opportunities. It's similar to BloodHound for Active Directory but designed specifically for GCP environments.

### How is EscaGCP different from other GCP security tools?

EscaGCP focuses on:
- **Graph-based analysis**: Visualizes relationships between identities and resources
- **Attack path detection**: Finds multi-step privilege escalation chains
- **Comprehensive coverage**: Detects all known GCP escalation techniques
- **Interactive visualization**: Provides an intuitive dashboard for exploration

### Is EscaGCP safe to run in production?

Yes, EscaGCP is read-only and makes no modifications to your GCP environment. It only:
- Reads IAM policies and configurations
- Queries resource metadata
- Optionally reads audit logs (if enabled)

### What GCP permissions does EscaGCP need?

Minimum permissions:
- `roles/viewer` on target projects
- `roles/iam.securityReviewer` for detailed IAM analysis

For organization-wide scans:
- `roles/resourcemanager.organizationViewer`
- `roles/browser` on folders

## Installation & Setup

### How do I install EscaGCP?

```bash
# Clone and install
git clone https://github.com/arielkalman/EscaGCP.git
cd EscaGCP
pip install -e .
```

### What Python version is required?

Python 3.8 or higher is required. Check your version:
```bash
python --version
```

### How do I authenticate to GCP?

Three methods are supported:

1. **Application Default Credentials** (recommended):
```bash
gcloud auth application-default login
```

2. **Service Account Key**:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

3. **Workload Identity** (for GKE/Cloud Run)

### What APIs need to be enabled?

Required APIs:
- Cloud Resource Manager API
- Identity and Access Management (IAM) API

Optional APIs:
- Cloud Identity API (for groups)
- Cloud Logging API (for audit logs)
- Cloud Asset API (for inventory)

Enable them with:
```bash
gcloud services enable cloudresourcemanager.googleapis.com iam.googleapis.com
```

## Usage Questions

### How do I run a quick scan?

Use lazy mode for automatic scanning:
```bash
escagcp run --lazy
```

### How do I scan multiple projects?

```bash
escagcp collect --projects project1,project2,project3
```

### How do I scan an entire organization?

```bash
escagcp collect --organization YOUR_ORG_ID
```

### Can I scan specific folders?

Yes:
```bash
escagcp collect --folders folder1,folder2
```

### How do I include audit logs in the analysis?

```bash
escagcp collect --projects PROJECT_ID --include-logs --log-days 30
```

### How long does a scan take?

Typical scan times:
- Single project: 1-2 minutes
- 10 projects: 5-10 minutes
- Organization (50 projects): 20-30 minutes

Factors affecting speed:
- Number of resources
- API rate limits
- Network latency
- Audit log collection

## Analysis Questions

### What attack techniques does EscaGCP detect?

EscaGCP detects all known GCP privilege escalation techniques including:
- Service Account Impersonation
- Service Account Key Creation
- VM/Function/Cloud Run deployment abuse
- Cloud Build exploitation
- Workload Identity abuse
- Tag-based escalation
- And more...

See [Attack Techniques](ATTACK_TECHNIQUES.md) for details.

### What do the risk scores mean?

Risk scores range from 0-100%:
- **Critical (80-100%)**: Immediate action required
- **High (60-80%)**: Should be addressed soon
- **Medium (40-60%)**: Review and plan remediation
- **Low (0-40%)**: Monitor

### How are risk scores calculated?

Risk scores consider:
1. **Technique severity** (40%): How dangerous the attack is
2. **Path length** (20%): Number of steps required
3. **Target sensitivity** (30%): What can be compromised
4. **Required effort** (10%): Difficulty of exploitation

### Can I customize risk scoring?

Yes, in your configuration file:
```yaml
analysis:
  scoring_weights:
    technique_severity: 0.5  # Increase weight
    path_length: 0.1        # Decrease weight
    target_sensitivity: 0.3
    required_effort: 0.1
```

## Visualization Questions

### How do I open the visualization?

After running analysis:
```bash
# Open the latest visualization
open visualizations/escagcp_attack_paths_*.html

# Or use --open-browser flag
escagcp run --lazy --open-browser
```

### What do the different node colors mean?

- 🔵 **Blue**: Users
- 🟢 **Green**: Service Accounts
- 🟡 **Yellow**: Groups
- 🔴 **Red**: Projects/Resources
- 🟣 **Purple**: Organizations
- ⚫ **Gray**: Roles

### How do I filter the graph?

Use the search box in the dashboard to filter by:
- Node name
- Node type
- Risk level
- Specific permissions

### Can I export the visualization?

Yes, use the export command:
```bash
escagcp export --graph graph/*.json --output report.html
```

### How do I share reports safely?

Reports contain sensitive information. Before sharing:
1. Review the [Security Checklist](SECURITY_CHECKLIST.md)
2. Use the export command to create standalone reports
3. Consider redacting sensitive project IDs/emails

## Troubleshooting

### I get "Permission Denied" errors

Check your permissions:
```bash
# View current authentication
gcloud auth list

# Check project permissions
gcloud projects get-iam-policy PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:user:YOUR_EMAIL"
```

### The scan is taking too long

Try:
1. Limit scope: `--projects specific-project`
2. Increase timeout in config
3. Check API quotas
4. Use concurrent requests

### I get API rate limit errors

Adjust rate limiting in config:
```yaml
performance:
  rate_limit:
    requests_per_second: 5  # Reduce rate
    burst_size: 10
```

### The graph is too large to visualize

Options:
1. Filter by risk level
2. Limit to attack paths only
3. Increase node/edge limits in config
4. Use graph database (Neo4j)

### How do I debug issues?

Enable debug logging:
```bash
# Set environment variable
export ESCAGCP_LOG_LEVEL=DEBUG

# Or use flag
escagcp --debug collect --projects PROJECT_ID
```

## Security Questions

### Is my data stored anywhere?

EscaGCP stores data locally only:
- `data/`: Collected GCP data
- `graph/`: Built graphs
- `findings/`: Analysis results
- `visualizations/`: HTML reports

No data is sent to external services.

### How do I clean up sensitive data?

Use the cleanup command:
```bash
# Preview what will be deleted
escagcp cleanup --dry-run

# Delete all data
escagcp cleanup --force
```

### Can I run EscaGCP in a restricted environment?

Yes, you can:
1. Use a dedicated service account
2. Run in a secured VM/container
3. Restrict output directory access
4. Enable audit logging

### How do I audit EscaGCP usage?

Monitor these Cloud Logging queries:
```
# Service account token generation
protoPayload.methodName="GenerateAccessToken"

# IAM policy reads
protoPayload.methodName="GetIamPolicy"
```

## Advanced Questions

### Can I integrate EscaGCP with my SIEM?

Yes, see the [User Guide](USER_GUIDE.md#integration-with-other-tools) for examples of:
- Sending alerts to SIEM
- Exporting to JSON for parsing
- Webhook notifications

### How do I run EscaGCP in CI/CD?

Example GitHub Actions workflow:
```yaml
- name: Run EscaGCP
  run: |
    pip install escagcp
    escagcp run --lazy --projects ${{ secrets.PROJECT_ID }}
    
- name: Check for critical findings
  run: |
    CRITICAL=$(jq '.statistics.critical_paths' findings/escagcp_analysis_*.json)
    if [ $CRITICAL -gt 0 ]; then
      echo "Critical security findings detected!"
      exit 1
    fi
```

### Can I extend EscaGCP with custom checks?

Yes, EscaGCP is designed to be extensible. You can:
1. Add custom analyzers
2. Define new edge types
3. Create custom visualizations

See the API documentation for details.

### How do I contribute to EscaGCP?

We welcome contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Development setup
- Coding standards
- Pull request process
- Issue reporting

## Getting Help

### Where can I get more help?

1. Check the [User Guide](USER_GUIDE.md)
2. Review [example workflows](USER_GUIDE.md#workflow-examples)
3. Search [GitHub issues](https://github.com/arielkalman/EscaGCP/issues)
4. Open a new issue with details

### How do I report a bug?

Open an issue with:
- EscaGCP version
- Python version
- Error messages
- Steps to reproduce
- Expected vs actual behavior

### How do I request a feature?

Open an issue describing:
- Use case
- Expected behavior
- Why it would be valuable
- Any implementation ideas 