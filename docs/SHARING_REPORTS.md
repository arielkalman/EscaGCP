# Sharing EscaGCP Reports

## Overview
EscaGCP now includes a powerful export feature that creates completely self-contained HTML reports that can be easily shared with colleagues, security teams, or management without requiring any additional software or dependencies.

## Creating a Standalone Report

Use the `export` command to generate a shareable report:

```bash
# Export using the latest graph
escagcp export --output my_report.html

# Export a specific graph file
escagcp export --graph graph/escagcp_graph_20250526_134123.json --output report.html

# Export a report
escagcp export --output security_audit.html
```

## What's Included

The standalone report contains:

1. **Interactive Graph Visualization**
   - Fully interactive network graph with zoom, pan, and node selection
   - Risk-based color coding for nodes and edges
   - Hover tooltips with detailed information

2. **Comprehensive Dashboard**
   - Statistics panel with key metrics
   - Legend explaining node types, edge types, and risk levels
   - Attack paths analysis with risk scores
   - Dangerous roles breakdown
   - Complete node and edge listings

3. **All Dependencies Embedded**
   - vis.js library for graph visualization
   - Inter font from Google Fonts
   - All CSS styles
   - Complete graph data in JSON format

## Sharing the Report

The generated HTML file (typically ~130KB) can be:

- **Emailed** as an attachment
- **Uploaded** to file sharing services (Google Drive, Dropbox, etc.)
- **Transferred** via USB or network drives
- **Hosted** on internal wikis or documentation sites
- **Opened** on any computer with a modern web browser

## Security Considerations

When sharing reports, keep in mind:

1. **Sensitive Information**: The report contains detailed IAM relationships and potential attack paths
2. **Access Control**: Share only with authorized personnel
3. **Data Classification**: Follow your organization's data handling policies
4. **Redaction**: Consider removing sensitive project names or identities if needed

## Example Use Cases

### 1. Security Audit Reports
```bash
escagcp export --output "gcp_security_audit_$(date +%Y%m%d).html"
```

### 2. Incident Response
```bash
escagcp export --graph graph/incident_*.json \
  --output incident_report.html
```

### 3. Compliance Documentation
```bash
escagcp export --output compliance_iam_review.html
```

## Technical Details

- **File Size**: Typically 100-200KB depending on graph complexity
- **Browser Support**: Works in Chrome, Firefox, Safari, Edge (all modern versions)
- **No Internet Required**: All resources are embedded
- **Performance**: Handles graphs with thousands of nodes smoothly

## Tips

1. **Regular Exports**: Create reports after each scan for historical comparison
2. **Naming Convention**: Use descriptive filenames with dates
3. **Archive Reports**: Keep historical reports for trend analysis
4. **Version Control**: Consider storing reports in git for change tracking

## Troubleshooting

If the report doesn't display correctly:

1. Ensure you're using a modern browser (Chrome/Firefox/Safari/Edge)
2. Check that JavaScript is enabled
3. Try opening in an incognito/private window to rule out extensions
4. Verify the file wasn't corrupted during transfer

## Future Enhancements

Planned improvements for the export feature:
- PDF export option
- Report templates for different audiences
- Automated report generation via CI/CD
- Differential reports showing changes between scans 