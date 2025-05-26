# EscaGCP Lazy Mode Demo

The new `--lazy` mode allows you to run all EscaGCP operations with a single command!

## Quick Start

### 1. Using Current GCP Project

If you have a GCP project set in your gcloud config:

```bash
# This will automatically:
# 1. Collect data from your current GCP project
# 2. Build the graph
# 3. Analyze for attack paths
# 4. Create visualization
# 5. Open the results in Chrome
escagcp run --lazy
```

### 2. Specifying Projects

You can also specify which projects to scan:

```bash
# Scan specific projects
escagcp run --lazy -p project1 -p project2 -p project3
```

### 3. Without Opening Browser

If you don't want to automatically open the browser:

```bash
escagcp run --lazy --no-open-browser
```

## What Happens Behind the Scenes

When you run `escagcp run --lazy`, it executes these commands in sequence:

1. **Data Collection**
   ```bash
   escagcp collect --projects $(gcloud config get-value project)
   ```

2. **Graph Building**
   ```bash
   escagcp build-graph --input data/ --output graph/
   ```

3. **Analysis**
   ```bash
   escagcp analyze --graph graph/escagcp_graph_*.json --output findings/
   ```

4. **Visualization**
   ```bash
   escagcp visualize --graph graph/escagcp_graph_*.json --output visualizations/
   ```

5. **Browser Launch**
   - Opens the visualization in Chrome (or default browser if Chrome is not available)

## Output

After running, you'll find:
- **Data files** in `data/`
- **Graph files** in `graph/`
- **Analysis results** in `findings/`
- **Interactive visualization** in `visualizations/`

## Example Output

```
$ escagcp run --lazy
Step 1/4: Collecting data from GCP...
Using current project: my-gcp-project
[Progress bars and collection logs...]

Step 2/4: Building graph from collected data...
Graph built successfully:
  Nodes: 57
  Edges: 63
  Projects: 1

Step 3/4: Analyzing graph for attack paths...
Analysis completed:
  Total attack paths: 47
  Critical nodes: 5
  Vulnerabilities: 12
  High-risk nodes: 11

Step 4/4: Creating visualization...
Visualization created: visualizations/escagcp_attack_paths_20250526_151200.html

✅ All operations completed successfully!
Opening visualization in browser...
```

## Manual Mode

If you prefer to run commands manually or need more control:

```bash
escagcp run
```

This will show you the manual steps you can run individually. 