# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

1. **DO NOT** create a public GitHub issue
2. Email security report to: <nesterov.alexander@outlook.com>
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 5 business days
- **Resolution Target**: 30 days for critical, 90 days for low severity

## Security Best Practices

### For Users

1. **Secrets Management**
   - Never commit credentials to git
   - Use environment variables for sensitive data
   - Rotate credentials regularly

2. **Device Security**
   - Use secure connections (USB debugging, SSH keys)
   - Limit device access to authorized users
   - Keep Android Debug Bridge (ADB) updated

3. **Model Security**
   - Verify model sources
   - Check model checksums
   - Don't use untrusted models

### For Contributors

1. **Code Security**
   - Sanitize all inputs
   - Use parameterized commands
   - Avoid shell injection vulnerabilities
   - No hardcoded credentials

2. **Dependencies**
   - Keep dependencies updated
   - Review dependency licenses
   - Monitor for CVEs

3. **CI/CD Security**
   - Use secrets management
   - Limit runner permissions
   - Review workflow changes

## Known Security Considerations

### ADB Security

- ADB runs with elevated privileges
- Ensure devices are trusted
- Use ADB authorization

### SSH Security

- Use key-based authentication
- Verify host keys
- Limit SSH access scope

### Model Execution

- Models run with benchmark_app privileges
- Potential for malicious models
- Validate model sources

## Security Features

### Current

- Input validation in configuration
- Parameterized shell commands
- Secrets excluded from logs

### Planned

- Model signature verification
- Encrypted credential storage
- Audit logging

## Vulnerability Disclosure

After a security issue is resolved:

1. Security advisory will be published
2. CVE will be requested if applicable
3. Users will be notified via GitHub

## Contact

Security Team: <nesterov.alexander@outlook.com>
PGP Key: [Link to public key]

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who:

- Follow responsible disclosure practices
- Allow reasonable time for fixes
- Don't exploit vulnerabilities

Thank you for helping keep OVMobileBench secure!
