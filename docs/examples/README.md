# GCPHound Example Reports

This directory contains example report outputs from GCPHound.

## Important Note

When running GCPHound on your own GCP environment, the generated reports will contain sensitive information including:
- Project IDs and names
- Service account emails
- User emails
- Resource names
- IAM bindings and permissions

**Always review reports before sharing them** to ensure no sensitive data is exposed.

## Generating Example Reports

To generate example reports for your environment:

```bash
# Generate a full interactive report
gcphound visualize --graph graph/gcphound_graph_*.json --output example_report.html

# Generate a simple standalone report
gcphound simple-export --graph graph/gcphound_graph_*.json --output simple_report.html

# Generate a shareable report
gcphound export --graph graph/gcphound_graph_*.json --output shareable_report.html
```

## Report Types

1. **Interactive Report** - Full dashboard with graph visualization
2. **Simple Report** - Basic HTML tables, no JavaScript required
3. **Shareable Report** - Self-contained HTML with embedded data 