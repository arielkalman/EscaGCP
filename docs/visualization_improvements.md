# EscaGCP Visualization Improvements

## Overview
Enhanced the HTML visualization to create a comprehensive security dashboard with multiple informative components beyond just the graph.

## Key Features Added

### 1. Dashboard Layout
- **Main Graph Area**: Interactive network visualization with risk-based coloring
- **Header with Statistics**: Real-time metrics showing:
  - Total Nodes
  - Total Edges  
  - Attack Paths Found
  - High Risk Nodes
  - Dangerous Roles Count
- **Sidebar with Tabs**: Multiple information panels

### 2. Legend Tab
Comprehensive legend explaining:
- **Node Types**: Color coding for Users, Service Accounts, Groups, Projects, Folders, Organizations, and Roles
- **Edge Types**: Different relationship types (Has Role, Can Impersonate, Can Admin, Member Of)
- **Risk Levels**: Color gradients for Critical (>0.8), High (>0.6), Medium (>0.4), and Low (>0.2) risk scores

### 3. Attack Paths Tab
Detailed explanations of attack techniques:
- **Service Account Impersonation**: How to exploit and prevent
- **Service Account Key Creation**: Attack methods and mitigations
- **VM Service Account Abuse**: Exploitation techniques
- **Cloud Function Deployment**: Security risks
- **Cloud Run Deployment**: Attack vectors

Each attack type includes:
- Description of the vulnerability
- Exploitation commands/techniques
- Prevention recommendations

### 4. Dangerous Roles Tab
Lists all dangerous roles found in the environment:
- Role name and description
- Which identities have each dangerous role
- Why each role is considered dangerous

Dangerous roles tracked include:
- `roles/owner`
- `roles/editor`
- `roles/iam.securityAdmin`
- `roles/iam.serviceAccountAdmin`
- `roles/iam.serviceAccountTokenCreator`
- `roles/compute.admin`
- `roles/cloudfunctions.admin`
- `roles/run.admin`
- And more...

### 5. Found Paths Tab
Displays actual attack paths discovered:
- Grouped by category (privilege escalation, lateral movement, etc.)
- Risk score for each path
- Path visualization showing the attack chain

### 6. Visual Enhancements
- **Dark Theme**: Professional dark background with high contrast
- **Risk-Based Node Coloring**: Nodes colored based on their risk score
- **Highlighted Critical Nodes**: Gold highlighting for most critical nodes
- **Edge Thickness**: Dangerous edges (like impersonation) are thicker
- **Interactive Tooltips**: Detailed information on hover
- **Responsive Design**: Adapts to different screen sizes

### 7. Graph Improvements
- **Smart Node Labels**: Service accounts and roles have shortened labels for clarity
- **Risk Score Integration**: Nodes sized and colored based on risk
- **Attack Path Highlighting**: Critical paths are visually emphasized
- **Better Physics**: Improved graph layout for readability

## Usage

### Generate Full Dashboard
```bash
escagcp visualize --graph graph/escagcp_graph_*.json --output visualizations/ --type full
```

### Generate Attack Path Focused View
```bash
escagcp visualize --graph graph/escagcp_graph_*.json --output visualizations/ --type attack-paths
```

### Generate Risk Focused View
```bash
escagcp visualize --graph graph/escagcp_graph_*.json --output visualizations/ --type risk
```

## Benefits
1. **Better Context**: Security teams can understand not just what the risks are, but how to exploit and prevent them
2. **Actionable Intelligence**: Specific commands and prevention steps for each attack type
3. **Risk Prioritization**: Clear visual indicators of the most critical issues
4. **Educational Value**: Helps teams understand GCP-specific attack techniques
5. **Executive Friendly**: Statistics and high-level metrics for reporting

## Technical Implementation
- Extended `HTMLVisualizer` class with dashboard generation
- Added attack path explanations dictionary
- Implemented dangerous roles detection
- Created tabbed interface with JavaScript
- Enhanced CSS for professional appearance
- Integrated with existing PathAnalyzer for real-time analysis 