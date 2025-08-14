# Secret Rotation Playbook for EscaGCP

## Overview

This playbook provides step-by-step instructions for rotating and revoking various types of secrets that could potentially be exposed in the repository. While no active secrets were found in the current audit, this playbook serves as a reference for incident response.

## Table of Contents

1. [Google Cloud Platform (GCP) Secrets](#google-cloud-platform-gcp-secrets)
2. [GitHub Secrets](#github-secrets)
3. [AWS Secrets](#aws-secrets)
4. [API Keys and Tokens](#api-keys-and-tokens)
5. [Database Credentials](#database-credentials)
6. [SSH Keys](#ssh-keys)
7. [Certificates](#certificates)
8. [General Best Practices](#general-best-practices)

---

## Google Cloud Platform (GCP) Secrets

### Service Account Keys

**Detection Pattern:** Files containing `"type": "service_account"` and `"private_key"`

**Rotation Steps:**

1. **Identify the compromised service account:**
   ```bash
   gcloud iam service-accounts list --project=PROJECT_ID
   ```

2. **Create a new key:**
   ```bash
   gcloud iam service-accounts keys create NEW_KEY.json \
     --iam-account=SERVICE_ACCOUNT_EMAIL \
     --project=PROJECT_ID
   ```

3. **Update applications to use the new key**

4. **Delete the compromised key:**
   ```bash
   gcloud iam service-accounts keys delete KEY_ID \
     --iam-account=SERVICE_ACCOUNT_EMAIL \
     --project=PROJECT_ID
   ```

5. **Audit recent usage:**
   ```bash
   gcloud logging read "protoPayload.authenticationInfo.principalEmail=\"SERVICE_ACCOUNT_EMAIL\"" \
     --limit=50 \
     --project=PROJECT_ID \
     --format=json
   ```

**References:**
- [GCP Service Account Key Management](https://cloud.google.com/iam/docs/keys-create-delete)
- [GCP Security Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)

### GCP API Keys

**Detection Pattern:** `AIza[0-9A-Za-z\-_]{35}`

**Rotation Steps:**

1. **List existing API keys:**
   ```bash
   gcloud services api-keys list --project=PROJECT_ID
   ```

2. **Create a new API key:**
   ```bash
   gcloud services api-keys create --display-name="NEW_KEY_NAME" \
     --project=PROJECT_ID
   ```

3. **Update applications with the new key**

4. **Delete the compromised key:**
   ```bash
   gcloud services api-keys delete KEY_ID --project=PROJECT_ID
   ```

5. **Add API key restrictions:**
   ```bash
   gcloud services api-keys update KEY_ID \
     --allowed-referrers="*.example.com/*" \
     --project=PROJECT_ID
   ```

### OAuth 2.0 Tokens

**Detection Pattern:** `ya29\.[0-9A-Za-z\-_]+`

**Rotation Steps:**

1. **Revoke the token immediately:**
   ```bash
   curl -X POST https://oauth2.googleapis.com/revoke \
     -d "token=TOKEN_VALUE"
   ```

2. **Review authorized applications:**
   - Visit: https://myaccount.google.com/permissions
   - Remove suspicious applications

3. **Generate new credentials:**
   - Visit: https://console.cloud.google.com/apis/credentials
   - Create new OAuth 2.0 credentials

---

## GitHub Secrets

### Personal Access Tokens (PAT)

**Detection Pattern:** `(ghp|gho|ghu|ghs|ghr)_[0-9A-Za-z]{36,}`

**Rotation Steps:**

1. **Revoke immediately via GitHub UI:**
   - Go to: https://github.com/settings/tokens
   - Click "Delete" next to the compromised token

2. **Create a new token:**
   - Click "Generate new token"
   - Use minimal required scopes
   - Set expiration date

3. **Update all systems using the token:**
   - CI/CD pipelines
   - Local development environments
   - Third-party integrations

4. **Audit recent usage:**
   - Review: https://github.com/settings/security-log

### GitHub Actions Secrets

**Rotation Steps:**

1. **Update repository secrets:**
   ```bash
   gh secret set SECRET_NAME --body "NEW_SECRET_VALUE" \
     --repo OWNER/REPO
   ```

2. **Update organization secrets (if applicable):**
   ```bash
   gh secret set SECRET_NAME --body "NEW_SECRET_VALUE" \
     --org ORGANIZATION
   ```

---

## AWS Secrets

### AWS Access Keys

**Detection Pattern:** `AKIA[0-9A-Z]{16}` or `ASIA[0-9A-Z]{16}`

**Rotation Steps:**

1. **Create new access keys:**
   ```bash
   aws iam create-access-key --user-name USERNAME
   ```

2. **Update all systems with new keys**

3. **Deactivate old keys:**
   ```bash
   aws iam update-access-key --access-key-id OLD_KEY_ID \
     --status Inactive --user-name USERNAME
   ```

4. **Delete old keys (after verification):**
   ```bash
   aws iam delete-access-key --access-key-id OLD_KEY_ID \
     --user-name USERNAME
   ```

5. **Review CloudTrail logs:**
   ```bash
   aws cloudtrail lookup-events --lookup-attributes \
     AttributeKey=AccessKeyId,AttributeValue=OLD_KEY_ID
   ```

---

## API Keys and Tokens

### Slack Tokens

**Detection Pattern:** `xox[baprs]-[0-9A-Za-z\-]+`

**Rotation Steps:**

1. **Revoke via Slack API:**
   ```bash
   curl -X POST https://slack.com/api/auth.revoke \
     -H "Authorization: Bearer TOKEN"
   ```

2. **Regenerate in Slack App settings:**
   - Visit: https://api.slack.com/apps
   - Select your app → OAuth & Permissions
   - Regenerate tokens

### Stripe API Keys

**Detection Pattern:** `(sk|pk)_(live|test)_[0-9A-Za-z]{20,}`

**Rotation Steps:**

1. **Roll API keys in Stripe Dashboard:**
   - Visit: https://dashboard.stripe.com/apikeys
   - Click "Roll key" for the compromised key

2. **Update webhook endpoints:**
   - Visit: https://dashboard.stripe.com/webhooks
   - Update endpoint secrets

---

## Database Credentials

### Connection Strings

**Detection Pattern:** Database URLs with embedded credentials

**Rotation Steps:**

1. **PostgreSQL:**
   ```sql
   ALTER USER username WITH PASSWORD 'new_password';
   ```

2. **MySQL:**
   ```sql
   ALTER USER 'username'@'host' IDENTIFIED BY 'new_password';
   ```

3. **MongoDB:**
   ```javascript
   db.changeUserPassword("username", "new_password")
   ```

4. **Update all connection strings in:**
   - Application configuration
   - Environment variables
   - CI/CD systems
   - Database clients

---

## SSH Keys

### Private Keys

**Detection Pattern:** `-----BEGIN (RSA|EC|OPENSSH|DSA|ED25519) PRIVATE KEY-----`

**Rotation Steps:**

1. **Generate new SSH key pair:**
   ```bash
   ssh-keygen -t ed25519 -C "email@example.com" -f ~/.ssh/new_key
   ```

2. **Add new public key to authorized systems:**
   ```bash
   ssh-copy-id -i ~/.ssh/new_key.pub user@host
   ```

3. **Remove old public key from authorized_keys:**
   ```bash
   ssh user@host
   sed -i '/OLD_KEY_IDENTIFIER/d' ~/.ssh/authorized_keys
   ```

4. **Update SSH configs and CI/CD systems**

---

## Certificates

### SSL/TLS Certificates

**Rotation Steps:**

1. **Generate new certificate:**
   - Use Let's Encrypt: `certbot certonly --webroot`
   - Or request from CA

2. **Install new certificate:**
   ```bash
   sudo cp new_cert.pem /etc/ssl/certs/
   sudo cp new_key.pem /etc/ssl/private/
   ```

3. **Restart services:**
   ```bash
   sudo systemctl restart nginx  # or apache2, etc.
   ```

4. **Revoke old certificate (if CA-signed):**
   - Contact your Certificate Authority

---

## General Best Practices

### Immediate Response Checklist

1. **[ ] Revoke/rotate the exposed secret immediately**
2. **[ ] Audit logs for unauthorized access**
3. **[ ] Update all systems using the secret**
4. **[ ] Document the incident**
5. **[ ] Review and update security policies**

### Prevention Measures

1. **Use secret management systems:**
   - Google Secret Manager
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault

2. **Enable pre-commit hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   pre-commit run --all-files
   ```

3. **Regular security audits:**
   ```bash
   # Run gitleaks
   gitleaks detect --source . --verbose
   
   # Run detect-secrets
   detect-secrets scan --baseline .secrets.baseline
   
   # Check git history
   git log --all -p | grep -E "(password|secret|token|key)"
   ```

4. **Use environment variables:**
   ```python
   import os
   api_key = os.environ.get('API_KEY')
   ```

5. **Implement least privilege access:**
   - Use service accounts with minimal permissions
   - Regular access reviews
   - Time-bound credentials

### Incident Response Contacts

- **Security Team:** security@yourcompany.com
- **GCP Support:** https://cloud.google.com/support
- **GitHub Security:** https://github.com/contact/security
- **AWS Security:** https://aws.amazon.com/security/vulnerability-reporting/

### References

- [OWASP Secret Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security/getting-started/best-practices-for-preventing-data-leaks)
- [NIST Incident Response Guide](https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-61r2.pdf)

---

## Automation Scripts

### Quick Rotation Script

Create a file `rotate_secrets.sh`:

```bash
#!/bin/bash

# EscaGCP Secret Rotation Script
# Usage: ./rotate_secrets.sh [secret_type]

set -e

SECRET_TYPE=${1:-all}

rotate_gcp_keys() {
    echo "Rotating GCP service account keys..."
    # Add your GCP key rotation logic here
}

rotate_github_tokens() {
    echo "Rotating GitHub tokens..."
    # Add your GitHub token rotation logic here
}

rotate_database_passwords() {
    echo "Rotating database passwords..."
    # Add your database password rotation logic here
}

case $SECRET_TYPE in
    gcp)
        rotate_gcp_keys
        ;;
    github)
        rotate_github_tokens
        ;;
    database)
        rotate_database_passwords
        ;;
    all)
        rotate_gcp_keys
        rotate_github_tokens
        rotate_database_passwords
        ;;
    *)
        echo "Usage: $0 [gcp|github|database|all]"
        exit 1
        ;;
esac

echo "Secret rotation completed!"
```

Make it executable:
```bash
chmod +x rotate_secrets.sh
```

---

**Last Updated:** December 2024
**Version:** 1.0
**Review Schedule:** Quarterly
