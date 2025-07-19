# EscaGCP Project Structure

## Overview
This document describes the organization and structure of the EscaGCP project.

## Directory Structure

### Core Package (`escagcp/`)
The main Python package containing all the core functionality:

- **`cli.py`** - Command-line interface implementation
- **`__init__.py`** - Package initialization

#### Submodules:
- **`analyzers/`** - Attack path analysis and security assessment
  - `paths.py` - PathAnalyzer class for finding privilege escalation paths
  
- **`collectors/`** - GCP API data collectors
  - `base.py` - Base collector class with common functionality
  - `orchestrator.py` - Orchestrates all collectors
  - `iam.py` - IAM policies and roles collector
  - `hierarchy.py` - Organization/folder/project hierarchy collector
  - `identity.py` - Users, groups, and service accounts collector
  - `resources.py` - GCP resources collector
  - `logs_collector.py` - Audit logs collector
  - `tags_collector.py` - Resource tags collector
  - `cloudbuild_collector.py` - Cloud Build configurations collector
  - `gke_collector.py` - GKE clusters and workloads collector
  
- **`config/`** - Configuration files
  - `default.yaml` - Default configuration settings
  - `permissions.yaml` - GCP permissions mapping
  
- **`graph/`** - Graph construction and manipulation
  - `builder.py` - Builds NetworkX graph from collected data
  - `exporter.py` - Exports graph to various formats
  - `models.py` - Node and Edge type definitions
  - `query.py` - Graph querying functionality
  
- **`utils/`** - Utility modules
  - `auth.py` - GCP authentication handling
  - `config.py` - Configuration management
  - `logger.py` - Logging utilities
  - `retry.py` - Retry logic for API calls
  
- **`visualizers/`** - Visualization generators
  - `html.py` - Interactive HTML visualization
  - `graphml.py` - GraphML format export

### Tests (`tests/`)
Comprehensive test suite organized by module:
- Unit tests for each component
- Integration tests
- Test fixtures and utilities

### Documentation (`docs/`)
Project documentation:
- `examples/` - Example reports and outputs
- Various markdown files documenting features

### Configuration Files
- **`setup.py`** - Package setup and metadata
- **`requirements.txt`** - Python dependencies
- **`pytest.ini`** - Test configuration
- **`.gitignore`** - Git ignore rules
- **`MANIFEST.in`** - Package manifest
- **`LICENSE`** - MIT license

### Runtime Directories (git-ignored)
These directories are created during execution:
- **`data/`** - Collected GCP data (JSON files)
- **`graph/`** - Generated graph files
- **`findings/`** - Analysis results
- **`visualizations/`** - HTML visualization outputs

### Temporary Directories (to be cleaned)
- **`temp_test_files/`** - Temporary test files (can be deleted)
- **`test_output/`** - Test execution outputs

## Key Design Principles

1. **Modular Architecture** - Each component has a single responsibility
2. **Extensibility** - Easy to add new collectors or analyzers
3. **Configuration-Driven** - Behavior controlled via YAML configs
4. **Type Safety** - Uses enums and dataclasses for type safety
5. **Error Handling** - Graceful degradation with comprehensive logging

## Data Flow

1. **Collection** - Collectors gather data from GCP APIs
2. **Graph Building** - Data is transformed into a directed graph
3. **Analysis** - Graph is analyzed for attack paths
4. **Visualization** - Results are presented in interactive formats

## Adding New Features

### Adding a New Collector
1. Create a new file in `escagcp/collectors/`
2. Inherit from `BaseCollector`
3. Implement the `collect()` method
4. Register in `orchestrator.py`

### Adding a New Attack Path
1. Add new `EdgeType` in `graph/models.py`
2. Update `ESCALATION_EDGE_TYPES` in `analyzers/paths.py`
3. Implement edge creation logic in relevant collector
4. Add description in `cli.py` `list_attack_types` command

## Development Workflow

1. Install in development mode: `pip install -e .`
2. Run tests: `pytest`
3. Check coverage: `pytest --cov=escagcp`
4. Format code: Follow PEP 8 guidelines

## Maintenance Notes

- Keep `data/`, `graph/`, `findings/`, and `visualizations/` directories in `.gitignore`
- Regularly clean up old data files to save space
- Update `requirements.txt` when adding new dependencies
- Document new features in README.md 