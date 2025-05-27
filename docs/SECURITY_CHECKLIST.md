# Security Checklist

⚠️ **Important**: EscaGCP collects sensitive information about your GCP environment. Review this checklist before sharing any outputs.

## Pre-Sharing Checklist

### 1. Sensitive Data Review

Before sharing any EscaGCP output, check for:

- [ ] **Project IDs**: May reveal internal naming conventions
- [ ] **Service Account Emails**: Contains project IDs and SA names
- [ ] **User Emails**: May expose employee information
- [ ] **Group Names**: Could reveal team structures
- [ ] **Resource Names**: May contain sensitive business information
- [ ] **Custom Role Names**: Could expose security practices
- [ ] **API Keys/Secrets**: Should never be in outputs (but verify)

### 2. Data Sanitization

#### Option A: Use Built-in Redaction
```bash
# Export with redaction enabled
escagcp export --graph graph/*.json \
  --output sanitized-report.html \
  --redact-sensitive
```

#### Option B: Manual Redaction
Replace sensitive values with generic ones:
- Project IDs → `project-1`, `project-2`
- Emails → `user1@example.com`, `sa1@project.iam`
- Resource names → `bucket-1`, `instance-1`

### 3. Scope Limitation

Limit what data is included:

```bash
# Exclude specific projects
escagcp collect --projects public-project --exclude sensitive-project

# Limit visualization to specific risk levels
escagcp visualize --min-risk 0.6 --exclude-low-risk

# Export only summary statistics
escagcp export --summary-only
```

## Sharing Guidelines

### Internal Sharing

When sharing within your organization:

1. **Use Secure Channels**
   - Company file sharing systems
   - Encrypted email
   - Access-controlled repositories

2. **Set Appropriate Permissions**
   - Limit access to security team
   - Use view-only permissions
   - Set expiration dates

3. **Document Recipients**
   - Track who has access
   - Note sharing purpose
   - Set review reminders

### External Sharing

When sharing with vendors/consultants:

1. **Legal Requirements**
   - [ ] NDA in place
   - [ ] Data handling agreement signed
   - [ ] Compliance requirements met

2. **Data Minimization**
   - Share only necessary information
   - Remove unrelated projects/resources
   - Aggregate statistics when possible

3. **Secure Transfer**
   - Use encrypted file transfer
   - Password protect files
   - Verify recipient identity

## Specific File Types

### JSON Files

High risk - contains all raw data:
```bash
# DON'T share these directly:
data/escagcp_complete_*.json
graph/escagcp_graph_*.json
findings/escagcp_analysis_*.json

# Instead, create sanitized versions:
escagcp sanitize --input findings/*.json --output sanitized/
```

### HTML Visualizations

Medium risk - contains processed data:
- Review all visible text
- Check JavaScript console for embedded data
- Verify no API keys in source

### GraphML Files

Medium risk - contains graph structure:
- Node labels may contain sensitive names
- Edge properties might reveal permissions
- Consider using pseudonyms

## Redaction Script

Use this script to automatically redact sensitive data:

```python
#!/usr/bin/env python3
import json
import re
import sys

def redact_email(email):
    """Redact email while preserving type"""
    if email.endswith('.gserviceaccount.com'):
        return f"sa-REDACTED@project-REDACTED.iam.gserviceaccount.com"
    elif '@' in email:
        domain = email.split('@')[1]
        return f"user-REDACTED@{domain}"
    return email

def redact_project_id(text):
    """Redact project IDs"""
    # Common patterns for project IDs
    return re.sub(r'projects/[a-z][-a-z0-9]{4,28}[a-z0-9]', 
                  'projects/PROJECT-REDACTED', text)

def redact_json(data):
    """Recursively redact sensitive data"""
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            if key in ['email', 'member', 'serviceAccountEmail']:
                redacted[key] = redact_email(value) if isinstance(value, str) else value
            elif key in ['projectId', 'project']:
                redacted[key] = 'PROJECT-REDACTED'
            elif key == 'name' and isinstance(value, str):
                redacted[key] = redact_project_id(value)
            else:
                redacted[key] = redact_json(value)
        return redacted
    elif isinstance(data, list):
        return [redact_json(item) for item in data]
    elif isinstance(data, str):
        return redact_project_id(data)
    return data

if __name__ == '__main__':
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    redacted = redact_json(data)
    
    with open(output_file, 'w') as f:
        json.dump(redacted, f, indent=2)
    
    print(f"Redacted data written to {output_file}")
```

## Post-Sharing Actions

After sharing EscaGCP outputs:

1. **Document the Sharing**
   - Record what was shared
   - Note with whom and when
   - Document business justification

2. **Set Reminders**
   - Review access after 30 days
   - Revoke when no longer needed
   - Update if scope changes

3. **Monitor Usage**
   - Check access logs if available
   - Verify data handling compliance
   - Address any concerns promptly

## Emergency Response

If sensitive data is accidentally shared:

1. **Immediate Actions**
   - Revoke access immediately
   - Contact recipients to delete
   - Document the incident

2. **Assess Impact**
   - Identify what was exposed
   - Determine potential risks
   - Check for any misuse

3. **Remediation**
   - Rotate any exposed credentials
   - Update access controls
   - Review and improve processes

## Best Practices

1. **Principle of Least Privilege**
   - Share minimum necessary data
   - Limit access duration
   - Use role-based access

2. **Defense in Depth**
   - Encrypt sensitive files
   - Use secure channels
   - Implement access logging

3. **Regular Reviews**
   - Audit shared data quarterly
   - Update redaction rules
   - Train team on procedures

## Compliance Considerations

Ensure sharing complies with:
- [ ] GDPR (if EU data involved)
- [ ] SOC 2 requirements
- [ ] Industry regulations
- [ ] Company policies
- [ ] Customer agreements

## Questions?

If unsure about sharing:
1. Consult your security team
2. Review company data policies
3. When in doubt, don't share

Remember: It's easier to prevent a leak than to contain one. 