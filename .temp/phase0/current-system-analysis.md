# GCPHound Current System Analysis & Feature Inventory

## Overview

This document provides a comprehensive analysis of the current GCPHound HTML/CSS/Python frontend system, serving as the foundation for the React refactoring project.

## Current System Architecture

### Technology Stack
- **Backend**: Python with NetworkX for graph processing
- **Frontend**: Server-side rendered HTML with embedded JavaScript
- **Visualization**: vis.js network library (v9.1.2)
- **Styling**: Embedded CSS with Inter font
- **Data Flow**: JSON data embedded directly in HTML templates

### Core Workflow
The current system follows a linear pipeline:
1. **collect**: Gather GCP IAM data, resources, and metadata
2. **build-graph**: Convert collected data into NetworkX graph
3. **analyze**: Find attack paths and calculate risk scores  
4. **visualize**: Generate interactive HTML dashboard
5. **export**: Create standalone reports

## Detailed Feature Inventory

### 1. Main Dashboard Layout

#### Header Section
- **Logo**: EscaGCP branding with purple theme (#6b46c1)
- **Title**: "EscaGCP Security Dashboard"
- **Statistics Bar**: 5 key metrics displayed as clickable cards
  - Total Nodes (count of all graph nodes)
  - Total Edges (count of all relationships)
  - Attack Paths (number of detected privilege escalation paths)
  - High Risk Nodes (nodes with risk score > 0.6)
  - Dangerous Roles (count of roles like owner/editor assigned to identities)
- **Share Button**: Export/share functionality with modal popup

#### Main Content Area
- **Graph Visualization**: Interactive network diagram using vis.js
  - Physics-enabled layout with hierarchical arrangement
  - Zoom and pan capabilities
  - Node selection and highlighting
  - Risk-based color coding
  - Hover tooltips with node/edge details
  - Click handlers for detailed information

#### Sidebar (Right Panel)
- **Resizable**: 400px default width, drag-to-resize functionality
- **Three Tab System**:
  1. **Dictionary Tab**: Legend and reference information
  2. **Attack Paths Tab**: Educational content about attack techniques
  3. **Found Paths Tab**: Actual detected attack paths in the environment

### 2. Interactive Elements

#### Statistics Cards
- **Hover Effects**: Transform and shadow changes
- **Click Handlers**: Open modals with detailed information
- **Visual States**: Different colors for different metric types

#### Graph Interactions
- **Node Selection**: Click to select, show details in tooltip
- **Edge Highlighting**: Hover to highlight path connections
- **Zoom Controls**: Mouse wheel and button controls
- **Pan Navigation**: Click and drag to navigate large graphs
- **Physics Toggle**: Enable/disable automatic layout

#### Modal System
- **Node Details Modal**: Shows comprehensive node information
- **Edge Details Modal**: Shows relationship details and permissions
- **Path Exploration Modal**: Interactive path visualization
- **Share Modal**: Export options and instructions

### 3. Sidebar Content Detail

#### Dictionary Tab
**Node Types Legend:**
- User (👤, Blue #4285F4)
- Service Account (🤖, Green #34A853) 
- Group (👥, Yellow #FBBC04)
- Project (📁, Red #EA4335)
- Folder (📂, Orange #FF6D00)
- Organization (🏢, Purple #9C27B0)
- Role (🎭, Gray #757575)
- Resource (📦, Teal #00ACC1)

**Edge Types Legend:**
- Has Role (Gray #757575)
- Can Impersonate (Red #F44336)
- Can Admin (Orange #FF5722)
- Member Of (Light Gray #9E9E9E)
- Can Access (Blue #2196F3)

**Risk Levels:**
- Critical (>80%, Dark Red)
- High (>60%, Red)
- Medium (>40%, Orange)
- Low (>20%, Yellow)
- Info (<20%, Green)

#### Attack Paths Tab
Educational content covering 25+ attack techniques:

**Critical Risk Techniques:**
- Service Account Impersonation (Risk: 90-100%)
- Service Account Key Creation (Risk: 85-95%)
- VM-based Service Account Abuse (Risk: 70-85%)
- Cloud Function Deployment (Risk: 75-85%)
- Cloud Run Deployment (Risk: 75-85%)

**Each technique includes:**
- Description of the vulnerability
- Required permissions
- Exploitation commands/techniques
- Prevention recommendations
- Common roles that enable the attack

#### Found Paths Tab
**Path Display Features:**
- Grouped by category (critical, high, medium, low)
- Sorted by risk score (descending)
- Path visualization with source → target format
- Risk percentage badges
- Length indicators (number of steps)
- Expandable details with full path information

**Path Categories:**
- Critical Multi-Step (2+ escalation steps)
- Privilege Escalation (single step to higher privilege)
- Lateral Movement (cross-project access)
- Service Account Impersonation
- Resource Access

### 4. Visual Design System

#### Color Palette
- **Primary**: Purple (#6b46c1)
- **Secondary**: Various node-type specific colors
- **Background**: Light gray (#f8f9fa)
- **Cards**: White (#ffffff)
- **Text**: Dark gray (#1a1f36)
- **Accent**: Purple variants for interactive elements

#### Typography
- **Font Family**: Inter (with fallbacks)
- **Sizes**: 
  - Headers: 24px (h1), 16px (h2)
  - Body: 14px
  - Small: 11-13px
  - Statistics: 18px (values)

#### Layout
- **Responsive Design**: Adapts to different screen sizes
- **Grid System**: Flexbox-based layout
- **Spacing**: Consistent 8px grid system
- **Shadows**: Subtle box-shadows for depth
- **Borders**: 1px solid borders with rounded corners (8px)

## Current User Workflows

### 1. Initial Dashboard View
1. User runs `gcphound run --lazy`
2. System collects data, builds graph, analyzes, and opens dashboard
3. Dashboard loads with header statistics and main graph
4. User sees overview metrics and visual representation

### 2. Graph Exploration
1. User interacts with graph (zoom, pan, click nodes)
2. Hover tooltips show basic node/edge information
3. Click events show detailed information modals
4. Users can follow paths visually through the network

### 3. Attack Path Investigation
1. User clicks on "Attack Paths" statistic or sidebar tab
2. Detailed list of found attack paths appears
3. User can click on specific paths to highlight in graph
4. Each path shows risk score, technique, and remediation

### 4. Risk Assessment
1. User reviews high-risk nodes highlighted in red/orange
2. Dangerous roles section shows privileged assignments
3. Attack explanations provide context for each risk
4. Users can drill down into specific vulnerabilities

### 5. Report Generation
1. User clicks "Share" button
2. System generates standalone HTML report
3. Report can be saved/shared with stakeholders
4. All data and interactivity preserved in single file

## Data Dependencies

### From Python Backend
The frontend requires these data structures from the Python analysis:

1. **Graph Data** (`graph/*.json`):
   - Nodes array with id, type, name, properties
   - Edges array with source, target, type, properties
   - Metadata with counts and collection info

2. **Analysis Results** (`findings/*.json`):
   - Attack paths by category
   - Risk scores by node
   - Vulnerability details
   - Statistics summary

3. **Risk Scoring**:
   - Node risk scores (0-1 float)
   - Edge risk scores (0-1 float)
   - Path risk scores (0-1 float)
   - Aggregated statistics

### Embedded Data Format
Currently data is embedded directly in HTML via JavaScript variables:
```javascript
window.graphData = { /* NetworkX graph converted to vis.js format */ };
window.attackPaths = [ /* Array of attack path objects */ ];
window.riskScores = { /* Node ID to risk score mapping */ };
```

## Current Limitations & Pain Points

### Technical Limitations
1. **Single File Output**: All data embedded in HTML (100-200KB files)
2. **No Real-time Updates**: Static analysis output only
3. **Limited Customization**: No user preferences or filters
4. **Performance**: Large graphs (>1000 nodes) can be slow
5. **Mobile Experience**: Not optimized for mobile devices

### User Experience Issues
1. **Learning Curve**: Complex interface requires explanation
2. **Information Overload**: Too much data displayed at once
3. **Navigation**: Difficult to find specific information quickly
4. **Context Switching**: No side-by-side comparison views
5. **Export Options**: Limited sharing and export formats

### Maintenance Challenges
1. **Mixed Code**: HTML, CSS, JS all in Python strings
2. **No Component Reuse**: Duplicated UI patterns
3. **Testing**: Difficult to test frontend independently
4. **Styling**: Hard to maintain consistent design system
5. **Responsive Design**: Manual media queries throughout

## Integration Points for React Frontend

### Data Loading Strategy
The new React frontend will need to:
1. Load graph data from JSON files or API endpoints
2. Parse and validate data structures
3. Handle loading states and error conditions
4. Support incremental data updates

### State Management Requirements
1. **Graph State**: Nodes, edges, layout positions
2. **UI State**: Selected nodes, active tabs, modal states
3. **Filter State**: Search queries, type filters, risk thresholds
4. **Analysis State**: Attack paths, risk scores, statistics

### Performance Considerations
1. **Large Graph Rendering**: Virtualization for >1000 nodes
2. **Search and Filtering**: Efficient client-side search
3. **Layout Calculations**: Web Workers for complex computations
4. **Memory Management**: Proper cleanup of vis.js instances

This analysis provides the foundation for defining the API contracts and data structures needed for the React frontend implementation. 