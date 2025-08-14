# Getting Started with EscaGCP

This guide will walk you through your first scan with EscaGCP in under 5 minutes.

## Prerequisites

Before starting, ensure you have:
- ✅ EscaGCP installed ([Installation Guide](INSTALLATION.md))
- ✅ GCP authentication configured
- ✅ At least `roles/viewer` permission on a GCP project

## Quick Start - Lazy Mode 🚀

The fastest way to get started is using lazy mode, which runs all operations automatically:

```bash
# Scan current project and open visualization
escagcp run --lazy

# Or scan specific projects
escagcp run --lazy --projects project1,project2
```

This command will:
1. Collect data from GCP
2. Build the graph
3. Analyze for attack paths
4. Create visualizations
5. Open the dashboard in your browser

## Step-by-Step Tutorial

If you prefer to understand each step, follow this tutorial:

### Step 1: Collect Data

First, collect IAM and resource data from your GCP project:

```bash
# Collect from current project
escagcp collect --projects $(gcloud config get-value project)

# Or specify a project
escagcp collect --projects my-project-id
```

You should see output like:
```
Starting data collection...
Collecting from project: my-project-id
  ✓ Hierarchy data
  ✓ IAM policies
  ✓ Service accounts
  ✓ Resources
Collection completed in 45.2 seconds
```

### Step 2: Build the Graph

Convert the collected data into a graph:

```bash
escagcp build-graph --input data/ --output graph/
```

Example output:
```
Loading data from: data/escagcp_complete_20240315_120000.json
Building graph...
Graph built successfully:
  Nodes: 156
  Edges: 423
  Projects: 1
```

### Step 3: Analyze for Attack Paths

Find privilege escalation paths and security issues:

```bash
escagcp analyze --graph graph/escagcp_graph_*.json
```

Example output:
```
Analysis completed:
  Total attack paths: 12
  Critical nodes: 3
  High-risk nodes: 7
```

### Step 4: Visualize Results

Create an interactive dashboard:

```bash
escagcp visualize --graph graph/escagcp_graph_*.json
```

This creates an HTML file in the `visualizations/` directory. Open it in your browser to explore:
- Interactive graph visualization
- Attack path details
- Risk scores
- Dangerous role assignments

## Understanding the Dashboard

![Dashboard Overview](screenshots/dashboard-overview.png)

The dashboard has several sections:

1. **Header Stats**: Quick overview of findings
2. **Graph View**: Interactive network visualization
3. **Sidebar Tabs**:
   - **Dictionary**: Legend for node/edge types
   - **Attack Paths**: Detected privilege escalation paths
   - **Found Paths**: Detailed path listings

### Interpreting Results

**Risk Levels**:
- 🔴 **Critical (>80%)**: Immediate action required
- 🟠 **High (>60%)**: Should be addressed soon
- 🟡 **Medium (>40%)**: Review and plan remediation
- 🟢 **Low (<40%)**: Monitor

**Common Attack Paths**:
1. **Service Account Impersonation**: User can generate tokens for privileged SA
2. **Key Creation**: User can create and download SA keys
3. **Deployment Abuse**: User can deploy code with SA permissions

## Your First Remediation

Based on findings, here's a common first fix:

```bash
# Remove dangerous permission
gcloud projects remove-iam-policy-binding PROJECT_ID \
    --member="user:risky@example.com" \
    --role="roles/iam.serviceAccountTokenCreator"

# Re-run analysis to verify
escagcp run --lazy --projects PROJECT_ID
```

## Next Steps

Now that you've completed your first scan:

1. **Scan More Projects**: Add `--projects project1,project2,project3`
2. **Scan Organization**: Use `--organization ORG_ID`
3. **Include Audit Logs**: Add `--include-logs --log-days 30`
4. **Automate Scans**: Set up [continuous monitoring](USER_GUIDE.md#continuous-monitoring)

## Common Questions

**Q: How long does a scan take?**
A: Typically 1-5 minutes per project, depending on size.

**Q: Can I scan production safely?**
A: Yes, EscaGCP only reads data, it makes no modifications.

**Q: What if I get permission errors?**
A: Ensure you have at least `roles/viewer` on the project. See [troubleshooting](INSTALLATION.md#troubleshooting).

## Getting Help

- 📖 [User Guide](USER_GUIDE.md) - Complete documentation
- 🔧 [Configuration](CONFIGURATION.md) - Advanced settings
- ❓ [FAQ](FAQ.md) - Frequently asked questions
- 🐛 [Issues](https://github.com/arielkalman/EscaGCP/issues) - Report problems 