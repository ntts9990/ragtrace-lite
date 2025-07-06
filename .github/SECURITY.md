# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within RAGTrace Lite, please send an email to security@ragtrace-lite.com. All security vulnerabilities will be promptly addressed.

Please do not publicly disclose the issue until it has been addressed by the team.

### What to Include

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Initial Response**: Within 24 hours
- **Assessment**: Within 72 hours
- **Fix Development**: Depends on severity (Critical: 7 days, High: 14 days, Medium: 30 days)
- **Public Disclosure**: After fix is released and users have had time to update

## Security Best Practices

When using RAGTrace Lite:

1. **Keep API Keys Secure**
   - Never commit API keys to version control
   - Use environment variables or secure vaults
   - Rotate keys regularly

2. **Update Dependencies**
   - Regularly update to the latest version
   - Monitor security advisories
   - Use `pip audit` to check for vulnerabilities

3. **Network Security**
   - Use HTTPS for all API communications
   - Implement proper firewall rules
   - Monitor for unusual activity

4. **Data Protection**
   - Encrypt sensitive data at rest
   - Use secure connections for database
   - Implement access controls