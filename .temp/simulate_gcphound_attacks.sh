#!/bin/bash
# simulate_gcphound_attacks.sh - Simulate GCPHound attack paths for testing
# WARNING: FOR TEST PROJECTS ONLY - DO NOT RUN IN PRODUCTION

set -uo pipefail  # Remove -e to allow continuing on errors

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT:-$(gcloud config get-value project)}"
REGION="${GCP_REGION:-us-central1}"
ZONE="${GCP_ZONE:-us-central1-a}"
ATTACKER_EMAIL="${ATTACKER_EMAIL:-}"  # Will be set after creating attacker SA
VICTIM_EMAIL="${VICTIM_EMAIL:-victim@example.com}"
RESOURCE_PREFIX="gcphound"
LABEL_KEY="gcphound"
LABEL_VALUE="true"
ATTACKER_SA_NAME="${RESOURCE_PREFIX}-attacker-sa"

# Error handler
handle_error() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log WARNING "Command failed with exit code $exit_code. Continuing..."
    fi
    return 0
}

# Cleanup function
cleanup_on_exit() {
    if [ $? -ne 0 ]; then
        log ERROR "Script failed. You may need to run cleanup manually."
    fi
}

# Trap for cleanup on exit
trap cleanup_on_exit EXIT

# Function to print colored output
log() {
    local level=$1
    shift
    case $level in
        INFO) echo -e "${BLUE}[INFO]${NC} $*" ;;
        SUCCESS) echo -e "${GREEN}[SUCCESS]${NC} $*" ;;
        WARNING) echo -e "${YELLOW}[WARNING]${NC} $*" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} $*" ;;
        STEP) echo -e "${PURPLE}[STEP]${NC} ${BOLD}$*${NC}" ;;
    esac
}

# Function to show usage
usage() {
    cat << EOF
${BOLD}GCPHound Attack Path Simulator${NC}

${RED}WARNING: FOR TEST PROJECTS ONLY - DO NOT RUN IN PRODUCTION${NC}

Usage: $0 [OPTIONS]

Options:
    --cleanup       Remove all resources created by this script
    --project       GCP project ID (default: current project)
    --region        GCP region (default: us-central1)
    --zone          GCP zone (default: us-central1-a)
    --attacker      Attacker email (default: attacker@example.com)
    --victim        Victim email (default: victim@example.com)
    --help          Show this help message

Examples:
    $0                          # Run all simulations
    $0 --cleanup                # Clean up all resources
    $0 --project test-project   # Run in specific project

This script simulates all 10 GCPHound attack paths:
1. Service Account Impersonation
2. Service Account Key Creation
3. ActAs Privilege Escalation via VM
4. Cloud Function Deployment
5. Cloud Build Exploitation
6. VM Token Theft
7. Tag-Based Privilege Escalation
8. Workload Identity Federation
9. Organization Policy Bypass
10. Custom Role Creation

Plus 2 multi-step chained attacks (5+ steps each)
EOF
}

# Parse command line arguments
CLEANUP_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --cleanup)
            CLEANUP_MODE=true
            shift
            ;;
        --project)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --zone)
            ZONE="$2"
            shift 2
            ;;
        --attacker)
            ATTACKER_EMAIL="$2"
            shift 2
            ;;
        --victim)
            VICTIM_EMAIL="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            log ERROR "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Verify project
if [ -z "$PROJECT_ID" ]; then
    log ERROR "No project ID specified. Set GCP_PROJECT or use --project"
    exit 1
fi

log INFO "Using project: $PROJECT_ID"
gcloud config set project "$PROJECT_ID" >/dev/null

# Setup attacker identity
setup_attacker() {
    log STEP "Setting up attacker identity..."
    
    # If no attacker email provided, create a service account
    if [ -z "$ATTACKER_EMAIL" ]; then
        ATTACKER_EMAIL=$(create_service_account "$ATTACKER_SA_NAME" "GCPHound Attacker Service Account")
        log SUCCESS "Created attacker service account: $ATTACKER_EMAIL"
        
        # Grant basic permissions to the attacker SA so it can be used
        grant_iam_role "serviceAccount:$ATTACKER_EMAIL" "roles/viewer"
    else
        log INFO "Using provided attacker email: $ATTACKER_EMAIL"
    fi
}

# Enable required APIs
enable_apis() {
    log STEP "Enabling required APIs..."
    
    local apis=(
        "iam.googleapis.com"
        "cloudresourcemanager.googleapis.com"
        "compute.googleapis.com"
        "storage.googleapis.com"
        "cloudfunctions.googleapis.com"
        "cloudbuild.googleapis.com"
        "container.googleapis.com"
        "cloudkms.googleapis.com"
        "secretmanager.googleapis.com"
        "orgpolicy.googleapis.com"
        "cloudidentity.googleapis.com"
        "iap.googleapis.com"
        "oslogin.googleapis.com"
        "run.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        if ! gcloud services list --enabled --filter="name:$api" --format="value(name)" 2>/dev/null | grep -q "$api"; then
            log INFO "Enabling $api..."
            gcloud services enable "$api" --quiet
        else
            log SUCCESS "$api already enabled"
        fi
    done
}

# Get member format for IAM bindings
get_member_format() {
    local email=$1
    if [[ "$email" == *".gserviceaccount.com" ]]; then
        echo "serviceAccount:$email"
    else
        echo "user:$email"
    fi
}

# Create service account helper
create_service_account() {
    local sa_name=$1
    local display_name=$2
    local sa_email="${sa_name}@${PROJECT_ID}.iam.gserviceaccount.com"
    
    if ! gcloud iam service-accounts describe "$sa_email" &>/dev/null; then
        log INFO "Creating service account: $sa_name" >&2
        gcloud iam service-accounts create "$sa_name" \
            --display-name="$display_name" \
            --description="GCPHound test SA" \
            --quiet
        
        # Wait for service account to be fully created
        log INFO "Waiting for service account to be ready..." >&2
        local retries=0
        while ! gcloud iam service-accounts describe "$sa_email" &>/dev/null; do
            sleep 2
            retries=$((retries + 1))
            if [ $retries -gt 10 ]; then
                log ERROR "Service account creation timed out" >&2
                return 1
            fi
        done
        sleep 2  # Extra wait for IAM propagation
    else
        log SUCCESS "Service account already exists: $sa_name" >&2
    fi
    
    echo "$sa_email"
}

# Grant IAM role helper
grant_iam_role() {
    local member=$1
    local role=$2
    local resource=${3:-"projects/$PROJECT_ID"}
    local condition=${4:-""}
    
    log INFO "Granting $role to $member on $resource"
    
    # Handle service account resources differently
    if [[ "$resource" == *"/serviceAccounts/"* ]]; then
        if [ -n "$condition" ]; then
            gcloud iam service-accounts add-iam-policy-binding "${resource#*/serviceAccounts/}" \
                --member="$member" \
                --role="$role" \
                --condition="$condition" \
                --quiet >/dev/null
        else
            gcloud iam service-accounts add-iam-policy-binding "${resource#*/serviceAccounts/}" \
                --member="$member" \
                --role="$role" \
                --condition=None \
                --quiet >/dev/null
        fi
    else
        # Handle project/folder/organization resources
        if [ -n "$condition" ]; then
            # Parse condition string and build proper format
            local expression=""
            local title=""
            local description=""
            
            # Debug logging
            log INFO "DEBUG: Raw condition string: $condition" >&2
            
            # Extract parts from condition string
            if [[ "$condition" =~ expression=([^,]+) ]]; then
                expression="${BASH_REMATCH[1]}"
            fi
            if [[ "$condition" =~ title=([^,]+) ]]; then
                title="${BASH_REMATCH[1]}"
            fi
            if [[ "$condition" =~ description=(.+)$ ]]; then
                description="${BASH_REMATCH[1]}"
            fi
            
            # Debug logging
            log INFO "DEBUG: Parsed expression: $expression" >&2
            log INFO "DEBUG: Parsed title: $title" >&2
            log INFO "DEBUG: Parsed description: $description" >&2
            
            # Build condition argument
            local condition_arg=""
            if [ -n "$expression" ]; then
                # Use a different delimiter (^) since expression contains commas
                # Format: --condition=^:^expression=EXPR:title=TITLE:description=DESC
                condition_arg="^:^expression=${expression}:title=${title}"
                if [ -n "$description" ]; then
                    condition_arg="${condition_arg}:description=${description}"
                fi
            else
                log ERROR "No expression found in condition"
                return 1
            fi
            
            gcloud "${resource%%/*}" add-iam-policy-binding "${resource#*/}" \
                --member="$member" \
                --role="$role" \
                --condition="${condition_arg}" \
                --quiet >/dev/null
        else
            # Explicitly specify no condition to handle policies with existing conditions
            gcloud "${resource%%/*}" add-iam-policy-binding "${resource#*/}" \
                --member="$member" \
                --role="$role" \
                --condition=None \
                --quiet >/dev/null
        fi
    fi
}

# 1. Simulate Service Account Impersonation
simulate_sa_impersonation() {
    log STEP "1. Simulating Service Account Impersonation Attack"
    
    # Create victim SA with editor role
    local victim_sa=$(create_service_account "${RESOURCE_PREFIX}-victim-sa-1" "Victim SA for Impersonation")
    grant_iam_role "serviceAccount:$victim_sa" "roles/editor"
    
    # Grant attacker token creator role
    local attacker_member=$(get_member_format "$ATTACKER_EMAIL")
    grant_iam_role "$attacker_member" "roles/iam.serviceAccountTokenCreator" "projects/$PROJECT_ID/serviceAccounts/$victim_sa"
    
    log SUCCESS "Attack path created: $ATTACKER_EMAIL -> [CAN_IMPERSONATE_SA] -> $victim_sa"
}

# 2. Simulate Service Account Key Creation
simulate_sa_key_creation() {
    log STEP "2. Simulating Service Account Key Creation Attack"
    
    # Create high-privilege SA
    local priv_sa=$(create_service_account "${RESOURCE_PREFIX}-priv-sa-2" "Privileged SA for Key Creation")
    grant_iam_role "serviceAccount:$priv_sa" "roles/owner"
    
    # Grant attacker key admin role
    local attacker_member=$(get_member_format "$ATTACKER_EMAIL")
    grant_iam_role "$attacker_member" "roles/iam.serviceAccountKeyAdmin" "projects/$PROJECT_ID/serviceAccounts/$priv_sa"
    
    log SUCCESS "Attack path created: $ATTACKER_EMAIL -> [CAN_CREATE_KEY] -> $priv_sa"
}

# 3. Simulate ActAs Privilege Escalation via VM
simulate_actas_vm() {
    log STEP "3. Simulating ActAs Privilege Escalation via VM"
    
    # Create privileged SA
    local vm_sa=$(create_service_account "${RESOURCE_PREFIX}-vm-sa-3" "VM Service Account")
    grant_iam_role "serviceAccount:$vm_sa" "roles/editor"
    
    # Grant attacker necessary permissions
    grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/iam.serviceAccountUser" "projects/$PROJECT_ID/serviceAccounts/$vm_sa"
    grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/compute.instanceAdmin.v1"
    
    # Create VM instance
    local vm_name="${RESOURCE_PREFIX}-vm-3"
    if ! gcloud compute instances describe "$vm_name" --zone="$ZONE" &>/dev/null; then
        log INFO "Creating VM instance: $vm_name"
        gcloud compute instances create "$vm_name" \
            --zone="$ZONE" \
            --machine-type="e2-micro" \
            --service-account="$vm_sa" \
            --scopes="cloud-platform" \
            --labels="${LABEL_KEY}=${LABEL_VALUE}" \
            --quiet
    else
        log SUCCESS "VM already exists: $vm_name"
    fi
    
    log SUCCESS "Attack path created: $ATTACKER_EMAIL -> [CAN_ACT_AS_VIA_VM] -> $vm_sa"
}

# 4. Simulate Cloud Function Deployment
simulate_function_deployment() {
    log STEP "4. Simulating Cloud Function Deployment Attack"
    
    # Ensure Cloud Functions service account has necessary permissions
    local project_number=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
    local gcf_sa="${PROJECT_ID}@appspot.gserviceaccount.com"
    local cloud_run_sa="${project_number}-compute@developer.gserviceaccount.com"
    
    # Grant storage permissions to Cloud Functions SA if needed
    grant_iam_role "serviceAccount:$gcf_sa" "roles/storage.objectAdmin" || true
    
    # Grant Cloud Run permissions
    grant_iam_role "serviceAccount:$cloud_run_sa" "roles/run.admin" || true
    
    # Create function SA
    local func_sa=$(create_service_account "${RESOURCE_PREFIX}-func-sa-4" "Function Service Account")
    grant_iam_role "serviceAccount:$func_sa" "roles/editor"
    
    # Grant attacker permissions
    grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/cloudfunctions.developer"
    grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/iam.serviceAccountUser" "projects/$PROJECT_ID/serviceAccounts/$func_sa"
    
    # Create a simple function
    local func_name="${RESOURCE_PREFIX}-func-4"
    local func_dir="/tmp/${func_name}"
    
    if ! gcloud functions describe "$func_name" --region="$REGION" &>/dev/null; then
        log INFO "Creating Cloud Function: $func_name"
        
        # Create function code
        mkdir -p "$func_dir"
        cat > "$func_dir/main.py" << 'EOF'
def hello_world(request):
    return 'GCPHound test function'
EOF
        
        cat > "$func_dir/requirements.txt" << 'EOF'
functions-framework==3.*
EOF
        
        # Deploy function (use 1st gen for simplicity)
        if gcloud functions deploy "$func_name" \
            --runtime="python39" \
            --trigger-http \
            --allow-unauthenticated \
            --entry-point="hello_world" \
            --source="$func_dir" \
            --service-account="$func_sa" \
            --region="$REGION" \
            --no-gen2 \
            --quiet 2>&1 | tee /tmp/function_deploy.log; then
            log SUCCESS "Function deployed successfully"
        else
            log WARNING "Failed to deploy function. This may be due to project restrictions."
            if grep -q "Failed to get Cloud run service" /tmp/function_deploy.log; then
                log WARNING "Cloud Run service creation failed - this is a common restriction in test projects"
            fi
            log INFO "Continuing with attack path demonstration..."
            rm -f /tmp/function_deploy.log
        fi
        
        rm -rf "$func_dir"
    else
        log SUCCESS "Function already exists: $func_name"
    fi
    
    log SUCCESS "Attack path created: $ATTACKER_EMAIL -> [CAN_DEPLOY_FUNCTION_AS] -> $func_sa"
}

# 5. Simulate Cloud Build Exploitation
simulate_cloudbuild() {
    log STEP "5. Simulating Cloud Build Exploitation Attack"
    
    # Get Cloud Build service account
    local project_number=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
    local cloudbuild_sa="${project_number}@cloudbuild.gserviceaccount.com"
    
    # Grant Cloud Build SA editor role (common misconfiguration)
    grant_iam_role "serviceAccount:$cloudbuild_sa" "roles/editor"
    
    # Grant attacker build permissions
    grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/cloudbuild.builds.editor"
    
    # Create a build config file
    local build_config="/tmp/${RESOURCE_PREFIX}-build.yaml"
    cat > "$build_config" << 'EOF'
steps:
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['config', 'list']
EOF
    
    log INFO "Build config created at $build_config"
    log SUCCESS "Attack path created: $ATTACKER_EMAIL -> [CAN_TRIGGER_BUILD_AS] -> $cloudbuild_sa"
    
    rm -f "$build_config"
}

# 6. Simulate VM Token Theft
simulate_vm_token_theft() {
    log STEP "6. Simulating VM Token Theft Attack"
    
    # Create powerful SA
    local powerful_sa=$(create_service_account "${RESOURCE_PREFIX}-powerful-sa-6" "Powerful SA for VM")
    grant_iam_role "serviceAccount:$powerful_sa" "roles/owner"
    
    # Create VM with powerful SA
    local vm_name="${RESOURCE_PREFIX}-vm-6"
    if ! gcloud compute instances describe "$vm_name" --zone="$ZONE" &>/dev/null; then
        log INFO "Creating VM instance: $vm_name"
        gcloud compute instances create "$vm_name" \
            --zone="$ZONE" \
            --machine-type="e2-micro" \
            --service-account="$powerful_sa" \
            --scopes="cloud-platform" \
            --labels="${LABEL_KEY}=${LABEL_VALUE}" \
            --metadata="enable-oslogin=TRUE" \
            --quiet
    else
        log SUCCESS "VM already exists: $vm_name"
    fi
    
    # Grant attacker OS Login access
    grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/compute.osLogin"
    grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/iap.tunnelResourceAccessor"
    
    log SUCCESS "Attack path created: $ATTACKER_EMAIL -> [CAN_LOGIN_TO_VM] -> VM -> [RUNS_AS] -> $powerful_sa"
}

# 7. Simulate Tag-Based Privilege Escalation
simulate_tag_escalation() {
    log STEP "7. Simulating Tag-Based Privilege Escalation Attack"
    
    # Create tag key and value
    local tag_key="${RESOURCE_PREFIX}-env"
    local tag_value="${RESOURCE_PREFIX}-prod"
    local tag_key_id=""
    local tag_value_id=""
    
    # Get organization ID (if available)
    local org_id=$(gcloud organizations list --format="value(name)" 2>/dev/null | head -1 | cut -d'/' -f2)
    
    if [ -n "$org_id" ]; then
        # Create tag key
        if ! gcloud resource-manager tags keys describe "$tag_key" --parent="organizations/$org_id" &>/dev/null; then
            log INFO "Creating tag key: $tag_key"
            gcloud resource-manager tags keys create "$tag_key" \
                --parent="organizations/$org_id" \
                --description="GCPHound test tag key" \
                --quiet
        fi
        
        tag_key_id=$(gcloud resource-manager tags keys list --parent="organizations/$org_id" --filter="shortName:$tag_key" --format="value(name)" | head -1)
        
        # Create tag value
        if ! gcloud resource-manager tags values describe "$tag_value" --parent="$tag_key_id" &>/dev/null; then
            log INFO "Creating tag value: $tag_value"
            gcloud resource-manager tags values create "$tag_value" \
                --parent="$tag_key_id" \
                --description="GCPHound test tag value" \
                --quiet
        fi
        
        tag_value_id=$(gcloud resource-manager tags values list --parent="$tag_key_id" --filter="shortName:$tag_value" --format="value(name)" | head -1)
        
        # Grant attacker tag user role
        grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/resourcemanager.tagUser"
        
        # Create conditional IAM binding
        if [ -n "$tag_key_id" ] && [ -n "$tag_value_id" ]; then
            log INFO "Tag key ID: $tag_key_id"
            log INFO "Tag value ID: $tag_value_id"
            # Use proper escaping for the condition
            local expression="resource.matchTag('${tag_key_id}', '${tag_value_id}')"
            local title="GCPHound Tag Condition"
            local description="Grant storage admin if tag matches"
            local condition="expression=${expression},title=${title},description=${description}"
            log INFO "Condition: $condition"
            # Use a non-basic role for conditional binding
            grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/storage.admin" "projects/$PROJECT_ID" "$condition"
        else
            log WARNING "Tag IDs not available, skipping conditional binding"
        fi
        
        log SUCCESS "Attack path created: $ATTACKER_EMAIL -> [CAN_MODIFY_TAG] -> Apply Tag -> [SATISFIES_CONDITION] -> roles/storage.admin"
    else
        log WARNING "No organization found, skipping tag-based escalation (requires org-level permissions)"
    fi
}

# 8. Simulate Workload Identity Federation
simulate_workload_identity() {
    log STEP "8. Simulating Workload Identity Federation Attack"
    
    # Grant network permissions to the current user for GKE creation
    local current_user=$(gcloud config get-value account)
    if [ -n "$current_user" ]; then
        log INFO "Granting network permissions to $current_user for GKE creation"
        # Try to grant at project level first
        grant_iam_role "user:$current_user" "roles/compute.networkUser" || true
        
        # Also grant viewer role which includes compute.networks.get
        grant_iam_role "user:$current_user" "roles/compute.viewer" || true
    fi
    
    # Create a service account for GKE operations if user permissions fail
    local gke_admin_sa=$(create_service_account "${RESOURCE_PREFIX}-gke-admin" "GKE Admin SA")
    grant_iam_role "serviceAccount:$gke_admin_sa" "roles/container.clusterAdmin"
    grant_iam_role "serviceAccount:$gke_admin_sa" "roles/compute.networkAdmin"
    grant_iam_role "serviceAccount:$gke_admin_sa" "roles/iam.serviceAccountUser"
    
    # Create GKE cluster
    local cluster_name="${RESOURCE_PREFIX}-cluster-8"
    
    if ! gcloud container clusters describe "$cluster_name" --zone="$ZONE" &>/dev/null; then
        log INFO "Creating GKE cluster: $cluster_name (this may take several minutes)"
        
        # First check if default network exists
        if ! gcloud compute networks describe default &>/dev/null; then
            log WARNING "Default network not found. Creating minimal network for GKE..."
            if gcloud compute networks create default --subnet-mode=auto --quiet 2>/dev/null; then
                log SUCCESS "Created default network"
                sleep 5  # Wait for network to be ready
            else
                log WARNING "Could not create default network. GKE creation will likely fail."
            fi
        fi
        
        # Check if we have permissions and quota
        if ! gcloud compute regions describe "${REGION}" &>/dev/null; then
            log WARNING "Cannot access compute regions. GKE cluster creation may fail due to permissions."
        fi
        
        if gcloud container clusters create "$cluster_name" \
            --zone="$ZONE" \
            --num-nodes=1 \
            --machine-type="e2-micro" \
            --workload-pool="${PROJECT_ID}.svc.id.goog" \
            --labels="${LABEL_KEY}=${LABEL_VALUE}" \
            --network="default" \
            --no-enable-cloud-logging \
            --no-enable-cloud-monitoring \
            --quiet 2>&1 | tee /tmp/gke_create.log; then
            log SUCCESS "GKE cluster created successfully"
        else
            log WARNING "Failed to create GKE cluster. This may be due to missing permissions or quota limits."
            if grep -q "Insufficient regional quota" /tmp/gke_create.log; then
                log WARNING "Insufficient quota for GKE cluster creation"
            fi
            rm -f /tmp/gke_create.log
            # Create a mock cluster for demonstration
            echo "Note: GKE cluster creation failed, but the attack path concept is still valid"
        fi
    else
        log SUCCESS "GKE cluster already exists: $cluster_name"
    fi
    
    # Create GCP SA for workload identity
    local wi_sa=$(create_service_account "${RESOURCE_PREFIX}-wi-sa-8" "Workload Identity SA")
    grant_iam_role "serviceAccount:$wi_sa" "roles/editor"
    
    # Create Kubernetes namespace and service account
    local k8s_namespace="${RESOURCE_PREFIX}-ns"
    local k8s_sa="${RESOURCE_PREFIX}-ksa"
    
    # Get cluster credentials if cluster exists
    if gcloud container clusters describe "$cluster_name" --zone="$ZONE" &>/dev/null; then
        gcloud container clusters get-credentials "$cluster_name" --zone="$ZONE" --quiet
        
        # Create namespace
        kubectl create namespace "$k8s_namespace" --dry-run=client -o yaml | kubectl apply -f -
        
        # Create Kubernetes service account
        kubectl create serviceaccount "$k8s_sa" -n "$k8s_namespace" --dry-run=client -o yaml | kubectl apply -f -
        
        # Annotate Kubernetes SA
        kubectl annotate serviceaccount "$k8s_sa" \
            -n "$k8s_namespace" \
            "iam.gke.io/gcp-service-account=$wi_sa" \
            --overwrite
    else
        log WARNING "GKE cluster not available, skipping Kubernetes operations"
    fi
    
    # Bind Kubernetes SA to GCP SA
    grant_iam_role "serviceAccount:${PROJECT_ID}.svc.id.goog[${k8s_namespace}/${k8s_sa}]" \
        "roles/iam.workloadIdentityUser" \
        "projects/$PROJECT_ID/serviceAccounts/$wi_sa"
    
    # Grant attacker Kubernetes permissions
    grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/container.developer"
    
    log SUCCESS "Attack path created: $ATTACKER_EMAIL -> [CAN_DEPLOY_GKE_POD_AS] -> KSA -> [WORKLOAD_IDENTITY] -> $wi_sa"
}

# 9. Simulate Organization Policy Bypass
simulate_org_policy_bypass() {
    log STEP "9. Simulating Organization Policy Bypass Attack"
    
    # Check if we have org access
    local org_id=$(gcloud organizations list --format="value(name)" 2>/dev/null | head -1 | cut -d'/' -f2)
    
    if [ -n "$org_id" ]; then
        # Grant attacker org policy admin
        grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/orgpolicy.policyAdmin" "organizations/$org_id"
        
        # Create a test constraint override
        local constraint="iam.disableServiceAccountKeyCreation"
        
        log INFO "Creating org policy to demonstrate bypass capability"
        cat > /tmp/policy.yaml << EOF
name: organizations/$org_id/policies/$constraint
spec:
  inheritFromParent: false
  reset: false
  rules:
  - enforce: false
EOF
        
        gcloud org-policies set-policy /tmp/policy.yaml --quiet || true
        rm -f /tmp/policy.yaml
        
        log SUCCESS "Attack path created: $ATTACKER_EMAIL -> [CAN_BYPASS_ORG_POLICY] -> Disable constraints"
    else
        log WARNING "No organization found, simulating project-level policy admin"
        grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/orgpolicy.policyAdmin"
        log SUCCESS "Attack path created: $ATTACKER_EMAIL -> [CAN_BYPASS_ORG_POLICY] -> Project policies"
    fi
}

# 10. Simulate Custom Role Creation
simulate_custom_role() {
    log STEP "10. Simulating Custom Role Creation Attack"
    
    # Grant attacker role admin
    grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/iam.roleAdmin"
    
    # Create a custom role
    local role_id="${RESOURCE_PREFIX}_custom_role_10"
    
    if ! gcloud iam roles describe "$role_id" --project="$PROJECT_ID" &>/dev/null; then
        log INFO "Creating custom role: $role_id"
        gcloud iam roles create "$role_id" \
            --project="$PROJECT_ID" \
            --title="GCPHound Custom Role" \
            --description="Custom role for privilege escalation demo" \
            --permissions="resourcemanager.projects.setIamPolicy,iam.serviceAccounts.getAccessToken" \
            --quiet
    else
        log SUCCESS "Custom role already exists: $role_id"
    fi
    
    # Grant the custom role to attacker
    grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "projects/$PROJECT_ID/roles/$role_id"
    
    log SUCCESS "Attack path created: $ATTACKER_EMAIL -> [CAN_CREATE_CUSTOM_ROLE] -> Create role with setIamPolicy -> Bind to self"
}

# Multi-step chained attack 1: Workload Identity → Tag Manipulation → Conditional IAM
simulate_chain_attack_1() {
    log STEP "CHAINED ATTACK 1: Workload Identity → Tag Manipulation → Conditional IAM (5+ steps)"
    
    # Grant network permissions to the current user for GKE creation
    local current_user=$(gcloud config get-value account)
    if [ -n "$current_user" ]; then
        log INFO "[Chain1] Granting network permissions to $current_user for GKE creation"
        grant_iam_role "user:$current_user" "roles/compute.networkUser" || true
        grant_iam_role "user:$current_user" "roles/compute.viewer" || true
    fi
    
    # Create a service account for GKE operations
    local gke_admin_sa=$(create_service_account "${RESOURCE_PREFIX}-chain1-gke-admin" "Chain1 GKE Admin SA")
    grant_iam_role "serviceAccount:$gke_admin_sa" "roles/container.clusterAdmin"
    grant_iam_role "serviceAccount:$gke_admin_sa" "roles/compute.networkAdmin"
    grant_iam_role "serviceAccount:$gke_admin_sa" "roles/iam.serviceAccountUser"
    
    # Step 1: Create GKE cluster with workload identity
    local cluster_name="${RESOURCE_PREFIX}-chain1-cluster"
    
    if ! gcloud container clusters describe "$cluster_name" --zone="$ZONE" &>/dev/null; then
        log INFO "[Chain1 Step 1] Creating GKE cluster with workload identity"
        
        # Check for default network
        if ! gcloud compute networks describe default &>/dev/null; then
            log WARNING "[Chain1] Default network not found. Creating minimal network for GKE..."
            if gcloud compute networks create default --subnet-mode=auto --quiet 2>/dev/null; then
                log SUCCESS "[Chain1] Created default network"
                sleep 5  # Wait for network to be ready
            else
                log WARNING "[Chain1] Could not create default network. GKE creation will likely fail."
            fi
        fi
        
        if ! gcloud container clusters create "$cluster_name" \
            --zone="$ZONE" \
            --num-nodes=1 \
            --machine-type="e2-micro" \
            --workload-pool="${PROJECT_ID}.svc.id.goog" \
            --labels="${LABEL_KEY}=${LABEL_VALUE}" \
            --network="default" \
            --no-enable-cloud-logging \
            --no-enable-cloud-monitoring \
            --quiet 2>&1 | tee /tmp/gke_chain1.log; then
            log WARNING "[Chain1] GKE cluster creation failed. Continuing with conceptual demonstration..."
            rm -f /tmp/gke_chain1.log
        fi
    fi
    
    # Step 2: Create intermediate SA with tag permissions
    log INFO "[Chain1 Step 2] Creating intermediate SA with tag permissions"
    local tag_sa=$(create_service_account "${RESOURCE_PREFIX}-chain1-tag-sa" "Chain1 Tag SA")
    grant_iam_role "serviceAccount:$tag_sa" "roles/resourcemanager.tagUser"
    
    # Step 3: Bind Kubernetes SA to GCP SA
    log INFO "[Chain1 Step 3] Creating and binding Kubernetes SA"
    
    local k8s_namespace="${RESOURCE_PREFIX}-chain1-ns"
    local k8s_sa="${RESOURCE_PREFIX}-chain1-ksa"
    
    if gcloud container clusters describe "$cluster_name" --zone="$ZONE" &>/dev/null; then
        gcloud container clusters get-credentials "$cluster_name" --zone="$ZONE" --quiet
        kubectl create namespace "$k8s_namespace" --dry-run=client -o yaml | kubectl apply -f -
        kubectl create serviceaccount "$k8s_sa" -n "$k8s_namespace" --dry-run=client -o yaml | kubectl apply -f -
        kubectl annotate serviceaccount "$k8s_sa" \
            -n "$k8s_namespace" \
            "iam.gke.io/gcp-service-account=$tag_sa" \
            --overwrite
    else
        log WARNING "[Chain1] GKE cluster not available, skipping Kubernetes operations"
    fi
    
    grant_iam_role "serviceAccount:${PROJECT_ID}.svc.id.goog[${k8s_namespace}/${k8s_sa}]" \
        "roles/iam.workloadIdentityUser" \
        "projects/$PROJECT_ID/serviceAccounts/$tag_sa"
    
    # Step 4: Create tag-based conditional binding
    log INFO "[Chain1 Step 4] Creating tag-based conditional IAM binding"
    local org_id=$(gcloud organizations list --format="value(name)" 2>/dev/null | head -1 | cut -d'/' -f2)
    
    if [ -n "$org_id" ]; then
        local tag_key="${RESOURCE_PREFIX}-chain1-key"
        local tag_value="${RESOURCE_PREFIX}-chain1-value"
        
        if ! gcloud resource-manager tags keys describe "$tag_key" --parent="organizations/$org_id" &>/dev/null; then
            gcloud resource-manager tags keys create "$tag_key" \
                --parent="organizations/$org_id" \
                --description="Chain1 tag key" \
                --quiet
        fi
        
        local tag_key_id=$(gcloud resource-manager tags keys list --parent="organizations/$org_id" --filter="shortName:$tag_key" --format="value(name)" | head -1)
        
        if ! gcloud resource-manager tags values describe "$tag_value" --parent="$tag_key_id" &>/dev/null; then
            gcloud resource-manager tags values create "$tag_value" \
                --parent="$tag_key_id" \
                --description="Chain1 tag value" \
                --quiet
        fi
        
        local tag_value_id=$(gcloud resource-manager tags values list --parent="$tag_key_id" --filter="shortName:$tag_value" --format="value(name)" | head -1)
        
        # Step 5: Create final SA with conditional editor access
        log INFO "[Chain1 Step 5] Creating final privileged SA with conditional access"
        local final_sa=$(create_service_account "${RESOURCE_PREFIX}-chain1-final-sa" "Chain1 Final SA")
        
        if [ -n "$tag_key_id" ] && [ -n "$tag_value_id" ]; then
            log INFO "[Chain1] Tag key ID: $tag_key_id"
            log INFO "[Chain1] Tag value ID: $tag_value_id"
            # Use proper escaping for the condition
            local expression="resource.matchTag('${tag_key_id}', '${tag_value_id}')"
            local title="Chain1 Condition"
            local description="Grant compute admin if tag matches"
            local condition="expression=${expression},title=${title},description=${description}"
            log INFO "[Chain1] Condition: $condition"
            # Use a non-basic role for conditional binding
            grant_iam_role "serviceAccount:$final_sa" "roles/compute.admin" "projects/$PROJECT_ID" "$condition"
        else
            log WARNING "Tag IDs not available, using unconditional binding for demonstration"
            grant_iam_role "serviceAccount:$final_sa" "roles/compute.admin" "projects/$PROJECT_ID"
        fi
        
        # Step 6: Grant tag SA ability to impersonate final SA
        log INFO "[Chain1 Step 6] Granting impersonation permissions"
        grant_iam_role "serviceAccount:$tag_sa" "roles/iam.serviceAccountTokenCreator" "projects/$PROJECT_ID/serviceAccounts/$final_sa"
        
        # Grant attacker Kubernetes access
        grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/container.developer"
        
        log SUCCESS "Chain Attack 1 created: Attacker -> Deploy Pod -> KSA -> Tag SA -> Apply Tags -> Conditional Binding -> Final SA (Compute Admin)"
    else
        log WARNING "No organization found, chain attack 1 requires org-level permissions"
    fi
}

# Multi-step chained attack 2: Cloud Build → Impersonate SA → Modify Custom Role
simulate_chain_attack_2() {
    log STEP "CHAINED ATTACK 2: Cloud Build → Impersonate SA → Modify Custom Role (5+ steps)"
    
    # Step 1: Create initial custom role with limited permissions
    log INFO "[Chain2 Step 1] Creating initial custom role"
    local initial_role="${RESOURCE_PREFIX}_chain2_initial_role"
    
    if ! gcloud iam roles describe "$initial_role" --project="$PROJECT_ID" &>/dev/null; then
        gcloud iam roles create "$initial_role" \
            --project="$PROJECT_ID" \
            --title="Chain2 Initial Role" \
            --description="Initial role for chain attack 2" \
            --permissions="storage.buckets.list" \
            --quiet
    fi
    
    # Step 2: Create intermediate SA with role admin permissions
    log INFO "[Chain2 Step 2] Creating intermediate SA with role admin"
    local role_admin_sa=$(create_service_account "${RESOURCE_PREFIX}-chain2-roleadmin-sa" "Chain2 Role Admin SA")
    grant_iam_role "serviceAccount:$role_admin_sa" "roles/iam.roleAdmin"
    grant_iam_role "serviceAccount:$role_admin_sa" "projects/$PROJECT_ID/roles/$initial_role"
    
    # Step 3: Configure Cloud Build SA
    log INFO "[Chain2 Step 3] Configuring Cloud Build SA"
    local project_number=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
    local cloudbuild_sa="${project_number}@cloudbuild.gserviceaccount.com"
    
    # Grant Cloud Build SA ability to impersonate role admin SA
    grant_iam_role "serviceAccount:$cloudbuild_sa" "roles/iam.serviceAccountTokenCreator" \
        "projects/$PROJECT_ID/serviceAccounts/$role_admin_sa"
    
    # Step 4: Create another SA that will get elevated permissions
    log INFO "[Chain2 Step 4] Creating target SA for privilege escalation"
    local target_sa=$(create_service_account "${RESOURCE_PREFIX}-chain2-target-sa" "Chain2 Target SA")
    
    # Step 5: Create build trigger that can be exploited
    log INFO "[Chain2 Step 5] Creating exploitable Cloud Build configuration"
    
    # Create a build config that demonstrates the attack chain
    local build_config="/tmp/${RESOURCE_PREFIX}-chain2-build.yaml"
    cat > "$build_config" << EOF
steps:
# Step 1: Impersonate role admin SA
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['auth', 'print-access-token', '--impersonate-service-account=$role_admin_sa']
  
# Step 2: Modify custom role to add dangerous permissions
- name: 'gcr.io/cloud-builders/gcloud'
  args: 
  - 'iam'
  - 'roles'
  - 'update'
  - '$initial_role'
  - '--project=$PROJECT_ID'
  - '--add-permissions=resourcemanager.projects.setIamPolicy,iam.serviceAccounts.getAccessToken'
  
# Step 3: Grant modified role to target SA
- name: 'gcr.io/cloud-builders/gcloud'
  args:
  - 'projects'
  - 'add-iam-policy-binding'
  - '$PROJECT_ID'
  - '--member=serviceAccount:$target_sa'
  - '--role=projects/$PROJECT_ID/roles/$initial_role'
EOF
    
    # Grant attacker Cloud Build permissions
    grant_iam_role "$(get_member_format "$ATTACKER_EMAIL")" "roles/cloudbuild.builds.editor"
    
    log INFO "Attack chain build config created at $build_config"
    log SUCCESS "Chain Attack 2 created: Attacker -> Submit Build -> Cloud Build SA -> Impersonate Role Admin SA -> Modify Custom Role -> Grant to Target SA"
    
    rm -f "$build_config"
}

# Cleanup function
cleanup_resources() {
    log STEP "Cleaning up all GCPHound test resources"
    
    # Set attacker email if not already set (for cleanup mode)
    if [ -z "$ATTACKER_EMAIL" ]; then
        # Try to find the attacker SA
        ATTACKER_EMAIL="${ATTACKER_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
        if ! gcloud iam service-accounts describe "$ATTACKER_EMAIL" &>/dev/null; then
            log WARNING "Attacker service account not found, skipping IAM cleanup for attacker"
            ATTACKER_EMAIL=""
        fi
    fi
    
    # Delete VMs
    log INFO "Deleting VMs..."
    # List VMs with proper formatting
    local vm_list=$(gcloud compute instances list --filter="labels.${LABEL_KEY}=${LABEL_VALUE}" --format="csv[no-heading](name,zone)" 2>/dev/null)
    if [ -n "$vm_list" ]; then
        echo "$vm_list" | while IFS=',' read -r name zone; do
            if [ -n "$name" ] && [ -n "$zone" ]; then
                log INFO "Deleting VM: $name in zone $zone"
                gcloud compute instances delete "$name" --zone="$zone" --quiet
            fi
        done
    else
        log INFO "No VMs found to delete"
    fi
    
    # Delete Cloud Functions
    log INFO "Deleting Cloud Functions..."
    for func in $(gcloud functions list --filter="labels.${LABEL_KEY}=${LABEL_VALUE}" --format="value(name,location)"); do
        local name=$(echo "$func" | awk '{print $1}')
        local location=$(echo "$func" | awk '{print $2}')
        log INFO "Deleting function: $name"
        gcloud functions delete "$name" --region="$location" --quiet
    done
    
    # Delete GKE clusters
    log INFO "Deleting GKE clusters..."
    for cluster in $(gcloud container clusters list --filter="resourceLabels.${LABEL_KEY}=${LABEL_VALUE}" --format="value(name,zone)"); do
        local name=$(echo "$cluster" | awk '{print $1}')
        local zone=$(echo "$cluster" | awk '{print $2}')
        log INFO "Deleting GKE cluster: $name (this may take several minutes)"
        gcloud container clusters delete "$name" --zone="$zone" --quiet
    done
    
    # Delete custom roles
    log INFO "Deleting custom roles..."
    for role in $(gcloud iam roles list --project="$PROJECT_ID" --filter="name:${RESOURCE_PREFIX}" --format="value(name)"); do
        # Extract just the role ID from the full name (projects/PROJECT_ID/roles/ROLE_ID)
        local role_id=$(echo "$role" | sed 's|^projects/.*/roles/||')
        log INFO "Deleting custom role: $role_id"
        gcloud iam roles delete "$role_id" --project="$PROJECT_ID" --quiet
    done
    
    # Delete service accounts
    log INFO "Deleting service accounts..."
    for sa in $(gcloud iam service-accounts list --filter="email:${RESOURCE_PREFIX}" --format="value(email)"); do
        log INFO "Deleting service account: $sa"
        # First delete all keys
        for key in $(gcloud iam service-accounts keys list --iam-account="$sa" --filter="keyType:USER_MANAGED" --format="value(name)"); do
            gcloud iam service-accounts keys delete "$key" --iam-account="$sa" --quiet
        done
        # Then delete the SA
        gcloud iam service-accounts delete "$sa" --quiet
    done
    
    # Remove IAM bindings for attacker
    if [ -n "$ATTACKER_EMAIL" ]; then
        log INFO "Removing IAM bindings for attacker: $ATTACKER_EMAIL"
        local member=$(get_member_format "$ATTACKER_EMAIL")
        local bindings=$(gcloud projects get-iam-policy "$PROJECT_ID" --format=json | \
            jq -r ".bindings[] | select(.members[] | contains(\"$ATTACKER_EMAIL\")) | .role")
        
        for role in $bindings; do
            log INFO "Removing $role from $ATTACKER_EMAIL"
            gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
                --member="$member" \
                --role="$role" \
                --quiet >/dev/null 2>&1 || true
        done
    else
        log INFO "Skipping IAM binding cleanup (no attacker email found)"
    fi
    
    # Clean up tags (if we have org access)
    local org_id=$(gcloud organizations list --format="value(name)" 2>/dev/null | head -1 | cut -d'/' -f2)
    if [ -n "$org_id" ]; then
        log INFO "Cleaning up tags..."
        for tag_key in $(gcloud resource-manager tags keys list --parent="organizations/$org_id" --filter="shortName:${RESOURCE_PREFIX}" --format="value(name)"); do
            # First delete tag values
            for tag_value in $(gcloud resource-manager tags values list --parent="$tag_key" --format="value(name)"); do
                # Remove bindings first
                for binding in $(gcloud resource-manager tags bindings list --filter="tagValue:$tag_value" --format="value(name)" 2>/dev/null); do
                    gcloud resource-manager tags bindings delete "$binding" --quiet 2>/dev/null || true
                done
                log INFO "Deleting tag value: $tag_value"
                gcloud resource-manager tags values delete "$tag_value" --quiet
            done
            log INFO "Deleting tag key: $tag_key"
            gcloud resource-manager tags keys delete "$tag_key" --quiet
        done
    fi
    
    log SUCCESS "Cleanup completed!"
}

# Main execution
main() {
    echo -e "${BOLD}${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           GCPHound Attack Path Simulator v1.0                ║"
    echo "║                                                              ║"
    echo "║  ${RED}WARNING: FOR TEST PROJECTS ONLY - DO NOT RUN IN PRODUCTION${CYAN} ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    if [ "$CLEANUP_MODE" = true ]; then
        cleanup_resources
        exit 0
    fi
    
    # Confirm before proceeding
    echo -e "${YELLOW}This script will create resources in project: ${BOLD}$PROJECT_ID${NC}"
    if [ -z "$ATTACKER_EMAIL" ]; then
        echo -e "${YELLOW}Attacker identity: ${BOLD}Will create service account${NC}"
    else
        echo -e "${YELLOW}Attacker email: ${BOLD}$ATTACKER_EMAIL${NC}"
    fi
    echo -e "${YELLOW}Region: ${BOLD}$REGION${NC}"
    echo -e "${YELLOW}Zone: ${BOLD}$ZONE${NC}"
    echo ""
    read -p "Do you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log INFO "Aborted by user"
        exit 0
    fi
    
    # Enable APIs
    enable_apis
    
    # Setup attacker identity
    setup_attacker
    
    # Run all attack simulations
    simulate_sa_impersonation || handle_error
    simulate_sa_key_creation || handle_error
    simulate_actas_vm || handle_error
    simulate_function_deployment || handle_error
    simulate_cloudbuild || handle_error
    simulate_vm_token_theft || handle_error
    simulate_tag_escalation || handle_error
    simulate_workload_identity || handle_error
    simulate_org_policy_bypass || handle_error
    simulate_custom_role || handle_error
    
    # Run chained attacks
    simulate_chain_attack_1 || handle_error
    simulate_chain_attack_2 || handle_error
    
    echo ""
    log SUCCESS "All attack paths have been simulated!"
    echo ""
    echo -e "${BOLD}Next steps:${NC}"
    echo "1. Run GCPHound to collect and analyze the attack paths:"
    echo "   gcphound collect --projects $PROJECT_ID"
    echo "   gcphound build-graph --input data/ --output graph/"
    echo "   gcphound analyze --graph graph/*.json --output findings/"
    echo "   gcphound visualize --graph graph/*.json --output visualizations/"
    echo ""
    echo "2. To clean up all resources:"
    echo "   $0 --cleanup"
    echo ""
    log WARNING "Remember to clean up resources when done to avoid charges!"
}

# Run main function
main 