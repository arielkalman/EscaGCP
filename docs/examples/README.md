# EscaGCP Example Reports

This directory contains example report outputs from EscaGCP.

## Important Note

When running EscaGCP on your own GCP environment, the generated reports will contain sensitive information including:
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
escagcp visualize --graph graph/escagcp_graph_*.json --output example_report.html

# Generate a simple standalone report
escagcp simple-export --graph graph/escagcp_graph_*.json --output simple_report.html

# Generate a shareable report
escagcp export --graph graph/escagcp_graph_*.json --output shareable_report.html
```

## Report Types

1. **Interactive Report** - Full dashboard with graph visualization
2. **Simple Report** - Basic HTML tables, no JavaScript required
3. **Shareable Report** - Self-contained HTML with embedded data 