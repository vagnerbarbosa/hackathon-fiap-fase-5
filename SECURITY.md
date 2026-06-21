# Security Policy

## Supported Versions

This project is currently in active development for the Hackathon FIAP Fase 5 (FIAP Software Security).

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security seriously — after all, this project is about automated threat modeling. If you discover a security vulnerability in our system, please follow these steps:

### 1. Do Not Create a Public Issue
Please **do not** open a public issue or pull request that discloses the vulnerability, as this could allow malicious actors to exploit it before a fix is available.

### 2. Report via Email
Send an email to the project maintainers at:

- **contato@vagnerbarbosa.com**

Include the following information:
- **Description**: A clear description of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Impact**: What could happen if exploited
- **Suggested Fix**: If you have a suggestion for fixing the issue
- **Your Contact**: How we can reach you for follow-up questions

### 3. Response Timeline

We will acknowledge receipt of your report within **48 hours** and provide a detailed response within **7 days**.

### 4. Disclosure Policy

Once a vulnerability is confirmed:
1. We will work on a fix and release it as soon as possible
2. We will credit you in the security advisory (unless you prefer to remain anonymous)
3. We will request a CVE if appropriate

## Security Measures

This project implements the following security measures:

### Code Security
- **Dependency Scanning**: GitHub Dependabot alerts enabled
- **Code Scanning**: CodeQL analysis for Python and GitHub Actions
- **Secret Scanning**: Enabled to prevent accidental secret commits

### Application Security (OWASP API Top 10)
- **Input Validation**: All user inputs are validated with Pydantic v2 before processing
- **Rate Limiting**: API endpoints have rate limits (Redis-backed) to prevent abuse
- **Security Headers**: CSP, HSTS, X-Content-Type-Options, X-Frame-Options
- **File Upload Validation**: Magic bytes verification for PNG/JPG uploads
- **LGPD Compliance**: Personal/organizational data is anonymized before logging
- **No Hardcoded Secrets**: All credentials use environment variables

### Threat Modeling Approach
- **STRIDE Methodology**: Every component detected is analyzed against Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege
- **CVE/CWE Mapping**: Known vulnerabilities are mapped per component type
- **Countermeasures**: OWASP Cheat Sheet-based recommendations

### Infrastructure Security
- **Docker**: Non-root containers with minimal privileges
- **GitHub Actions**: Minimal required permissions for each workflow
- **PostgreSQL**: Secure connections with SSL in production

## Security Best Practices for Users

1. **Environment Variables**: Never commit `.env` files or expose API credentials
2. **File Uploads**: The API validates file types (PNG, JPG, JPEG) and sizes (max 50MB)
3. **Model Files**: YOLOv11n model files (`best.pt`) should be stored securely; verify checksums
4. **Cache Management**: Redis cache contains processed results; configure TTL appropriately
5. **Report Data**: Generated threat model reports may contain sensitive architecture details; handle with care

## Known Security Considerations

### ML Models (YOLOv11n)
- Model files are trained locally using trusted sources (Ultralytics)
- Local inference prevents data exposure to external APIs
- Model artifacts should be scanned for supply chain risks

### Dataset
- Diagrams used for training may contain proprietary architecture details
- Ensure you have permission to use any uploaded diagrams

### STRIDE Engine
- The threat model engine uses YAML-based mappings; validate all mapping files
- Inferred data flows (heuristic-based) may miss some attack vectors

## Security Updates

Security updates will be released as patch versions and announced in:
1. Release notes
2. Security advisories (when applicable)

---

**Last Updated**: June 2026

This security policy is subject to change. Please review periodically for updates.
