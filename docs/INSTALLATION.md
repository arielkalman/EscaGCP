# Installation Guide

This guide covers the installation and setup of EscaGCP.

## Requirements

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Memory**: At least 4GB RAM (8GB+ recommended for large environments)
- **Disk Space**: At least 1GB free space

### GCP Requirements
- **GCP Account**: With appropriate permissions
- **APIs**: The following APIs must be enabled in your GCP projects:
  - Cloud Resource Manager API
  - Identity and Access Management (IAM) API
  - Cloud Identity API (for group enumeration)
  - Admin SDK API (optional, for advanced group features)
  - Cloud Asset API (optional, for asset inventory)
  - Cloud Logging API (optional, for audit log analysis)

### Required Permissions
Your GCP account needs at least these roles:
- `roles/viewer` on target projects
- `roles/iam.securityReviewer` for detailed IAM analysis
- `roles/resourcemanager.organizationViewer` for organization-level scans
- `roles/logging.viewer` for audit log collection (optional)

## Installation Methods

### Method 1: Install from Source (Recommended)

```bash
# Clone the repository
git clone https://github.com/arielkalman/EscaGCP.git
cd EscaGCP

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Method 2: Install from PyPI

```bash
# When published to PyPI
pip install escagcp
```

### Method 3: Docker Installation

```bash
# Pull the Docker image (when available)
docker pull escagcp/escagcp:latest

# Run with Docker
docker run -v ~/.config/gcloud:/root/.config/gcloud escagcp/escagcp --help
```

## Authentication Setup

### Option 1: Application Default Credentials (Recommended)

This is the simplest method for local development:

```bash
# Login with your Google account
gcloud auth login

# Set application default credentials
gcloud auth application-default login

# Set your default project (optional)
gcloud config set project YOUR_PROJECT_ID
```

### Option 2: Service Account Key

For automated environments or CI/CD:

```bash
# Create a service account
gcloud iam service-accounts create escagcp-scanner \
    --display-name="EscaGCP Scanner"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:escagcp-scanner@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/viewer"

# Create and download key
gcloud iam service-accounts keys create key.json \
    --iam-account=escagcp-scanner@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### Option 3: Workload Identity (GKE)

For running in GKE:

```bash
# Create service account
kubectl create serviceaccount escagcp-scanner

# Bind to GCP service account
kubectl annotate serviceaccount escagcp-scanner \
    iam.gke.io/gcp-service-account=escagcp-scanner@PROJECT_ID.iam.gserviceaccount.com

# Grant workload identity binding
gcloud iam service-accounts add-iam-policy-binding \
    escagcp-scanner@PROJECT_ID.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/escagcp-scanner]"
```

## Enabling Required APIs

Enable all required APIs with this script:

```bash
# Set your project ID
PROJECT_ID="your-project-id"

# Enable required APIs
gcloud services enable cloudresourcemanager.googleapis.com --project=$PROJECT_ID
gcloud services enable iam.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudidentity.googleapis.com --project=$PROJECT_ID
gcloud services enable admin.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudasset.googleapis.com --project=$PROJECT_ID
gcloud services enable logging.googleapis.com --project=$PROJECT_ID
```

## Verifying Installation

After installation, verify everything is working:

```bash
# Check EscaGCP is installed
escagcp --version

# Verify GCP authentication
gcloud auth list
gcloud auth application-default print-access-token

# Test basic functionality
escagcp collect --projects $(gcloud config get-value project) --dry-run
```

## Troubleshooting Installation

### Common Issues

1. **Python Version Error**
   ```
   ERROR: Python 3.8 or higher is required
   ```
   Solution: Install Python 3.8+ from [python.org](https://www.python.org/)

2. **Permission Denied**
   ```
   ERROR: Permission denied accessing project
   ```
   Solution: Ensure your account has the required roles (see Requirements)

3. **API Not Enabled**
   ```
   ERROR: Cloud Resource Manager API has not been used in project
   ```
   Solution: Enable the required APIs (see Enabling Required APIs)

4. **Authentication Failed**
   ```
   ERROR: Could not automatically determine credentials
   ```
   Solution: Run `gcloud auth application-default login`

### Getting Help

If you encounter issues:
1. Check the [FAQ](FAQ.md)
2. Search [existing issues](https://github.com/arielkalman/EscaGCP/issues)
3. Open a new issue with:
   - Your OS and Python version
   - Complete error message
   - Steps to reproduce

## Next Steps

Once installed, proceed to:
- [Getting Started](GETTING_STARTED.md) - Quick tutorial
- [User Guide](USER_GUIDE.md) - Complete feature guide
- [Configuration](CONFIGURATION.md) - Advanced settings 