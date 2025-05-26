# EscaGCP Security Checklist

Before sharing or publishing any EscaGCP outputs, please review this checklist:

## Pre-Publication Checklist

### 1. Remove Sensitive Files
- [ ] Delete all files in `data/` directory
- [ ] Delete all files in `graph/` directory  
- [ ] Delete all files in `findings/` directory
- [ ] Delete all files in `visualizations/` directory
- [ ] Delete any `.html` report files in the root directory
- [ ] Delete any `.json` files containing GCP data

### 2. Review Code for Hardcoded Values
- [ ] No hardcoded project IDs
- [ ] No hardcoded service account emails
- [ ] No hardcoded user emails
- [ ] No API keys or credentials
- [ ] No internal domain names

### 3. Clean Test Data
- [ ] Test files use only generic domains (example.com)
- [ ] Test files use only generic project names (test-project)
- [ ] No real GCP resource names in tests

### 4. Use the Cleanup Command
Run the cleanup command to remove all generated data:
```bash
escagcp cleanup --force
```

### 5. Git Repository Check
Before committing:
```bash
# Check what files will be committed
git status

# Ensure .gitignore is properly configured
cat .gitignore

# Check for sensitive patterns
git grep -i "your-domain.com"
git grep -i "your-project-id"
git grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
```

### 6. Report Sanitization
If you must share reports:
1. Use the `--title` option to set a generic title
2. Review the HTML file for any sensitive data
3. Consider creating a demo environment with non-sensitive data

## What Gets Collected

EscaGCP collects and stores:
- Project IDs and numbers
- Organization and folder IDs
- Service account emails
- User and group emails
- Resource names (VMs, functions, buckets, etc.)
- IAM roles and permissions
- Network configurations
- API keys metadata (not the keys themselves)

## Safe Sharing Practices

1. **Never share raw data files** from the `data/` directory
2. **Review all HTML reports** before sharing
3. **Use demo/test projects** for public demonstrations
4. **Anonymize data** if needed for bug reports
5. **Use private repositories** for internal use

## If You Find Sensitive Data

If you accidentally commit sensitive data:
1. Remove it from the repository immediately
2. Use `git filter-branch` or BFG Repo-Cleaner to remove from history
3. Rotate any exposed credentials
4. Review access logs for any unauthorized access 