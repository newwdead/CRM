# GitHub Actions Workflows

This directory contains automated CI/CD and security workflows for the BizCard CRM project.

## Available Workflows

### 1. Security Scan (`security.yml`)

**Purpose:** Core security scanning for dependencies and code vulnerabilities.

**Jobs:**
- **python-security**: Safety check + Bandit scan
- **npm-security**: NPM audit for Node.js dependencies
- **docker-security**: Trivy scan for Docker images
- **security-summary**: Aggregated results summary

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Schedule: Every Monday at 9:00 AM UTC
- Manual dispatch

**Features:**
- ✅ All scans use `continue-on-error: true` (won't fail on warnings)
- ✅ No special permissions required
- ✅ Results displayed in GitHub Step Summary
- ✅ Fast execution (~5-10 minutes)

**Status:** ✅ Production Ready


### 2. CodeQL Analysis (`codeql.yml`)

**Purpose:** Advanced code analysis for security vulnerabilities and code quality.

**Jobs:**
- **analyze**: Python and JavaScript analysis

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`
- Schedule: Every Monday at 9:30 AM UTC
- Manual dispatch

**Requirements:**
- Permissions: `security-events: write`
- GitHub Advanced Security (may require enterprise plan)

**Features:**
- ✅ Deep static analysis
- ✅ Results in Security tab
- ✅ Integration with GitHub Security Advisories
- ✅ Supports multiple languages

**Status:** ⚠️ Requires GitHub Advanced Security


### 3. CI/CD Pipeline (`ci-cd.yml`)

**Purpose:** Continuous integration and deployment for the application.

**Jobs:**
- Backend tests
- Frontend tests
- Docker build and push
- Deployment (optional)

**Triggers:**
- Push to any branch
- Pull requests

**Status:** ✅ Active


### 4. Dependabot (`dependabot.yml`)

**Purpose:** Automated dependency updates for security patches.

**Ecosystems:**
- Python (pip)
- JavaScript (npm)
- Docker
- GitHub Actions

**Schedule:** Weekly

**Status:** ✅ Active

---

## Configuration

### Enabling GitHub Security Features

1. **Go to:** Repository → Settings → Security → Code security and analysis

2. **Enable:**
   - ✅ Dependabot alerts
   - ✅ Dependabot security updates
   - ✅ CodeQL analysis (if available)
   - ✅ Secret scanning (if available)
   - ✅ Push protection (optional)

3. **Configure Actions Permissions:**
   - Settings → Actions → General
   - ✅ Allow all actions and reusable workflows
   - ✅ Read and write permissions
   - ✅ Allow GitHub Actions to create and approve pull requests

---

## Monitoring

### Check Workflow Status

**URL:** https://github.com/newwdead/CRM/actions

Expected status:
- ✅ Security Scan: Should pass (continue-on-error prevents failures)
- ✅ CI/CD Pipeline: Should pass
- ⚠️ CodeQL Analysis: May require setup

### View Security Findings

**URL:** https://github.com/newwdead/CRM/security

Available tabs:
- **Security advisories**: CVE reports and advisories
- **Dependabot alerts**: Dependency vulnerabilities
- **Code scanning alerts**: CodeQL findings (if enabled)
- **Secret scanning alerts**: Exposed secrets (if enabled)

---

## Troubleshooting

### Security Scan Failing

**Common Issues:**

1. **Permission Errors:**
   - Check: Settings → Actions → General → Permissions
   - Set to: Read and write permissions

2. **Docker Build Errors:**
   - Ensure `backend/Dockerfile` and `frontend/Dockerfile` are valid
   - Check Docker Hub rate limits

3. **Dependency Install Errors:**
   - Verify `backend/requirements.txt` is valid
   - Verify `frontend/package.json` is valid

**Solution:** All scans use `continue-on-error: true`, so they should pass even with warnings.

### CodeQL Not Running

**Possible Causes:**

1. **No Permission:**
   - CodeQL requires `security-events: write` permission
   - May require GitHub Advanced Security

2. **Large Repository:**
   - CodeQL may timeout on very large repos
   - Consider excluding test files or generated code

**Solution:** CodeQL is optional. If not available, the basic security scan still provides good coverage.

---

## Best Practices

1. **Regular Monitoring:**
   - Check GitHub Actions weekly
   - Review security alerts immediately

2. **Update Dependencies:**
   - Merge Dependabot PRs regularly
   - Test updates in staging before production

3. **Fix Critical Issues:**
   - High/Critical severity: Fix within 7 days
   - Medium severity: Fix within 30 days
   - Low severity: Fix when convenient

4. **Custom Scans:**
   - Add project-specific security checks
   - Integrate with external security tools

---

## Version History

- **v3.4.1** (2025-10-24): Simplified security workflows, separated CodeQL
- **v3.4.0** (2025-10-23): Added comprehensive security scanning
- **v3.0.0** (2025-10-20): Initial workflows setup

---

## Support

For issues or questions about workflows:
1. Check logs: https://github.com/newwdead/CRM/actions
2. Review this documentation
3. Contact repository maintainers

