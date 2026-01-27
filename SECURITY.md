# Security Policy

## ⚠️ Important Notice

**This repository contains DEMONSTRATION CODE for educational purposes only.**

The code in this repository is designed to illustrate multi-tenant security patterns for agentic AI applications. It is NOT intended for production use without significant security hardening.

## Known Security Considerations

### Demo-Only Features

The following features are intentionally simplified for demonstration purposes:

1. **JWT Token Verification**: The demo code decodes JWT tokens without full signature verification for local development convenience. Production deployments MUST implement proper JWT validation using JWKS from Amazon Cognito.

2. **Demo Credentials**: Sample users use simplified passwords for demonstration. Production systems should use strong password policies and consider passwordless authentication.

3. **Flask Development Server**: The backend uses Flask's built-in development server. Production deployments should use a production WSGI server (gunicorn, uWSGI) behind a reverse proxy.

4. **Debug Mode**: Debug settings are controlled via environment variables. Ensure `FLASK_DEBUG=false` in production.

5. **Resource Polling**: The `time.sleep()` calls in `aws_resources.py` are used for AWS resource creation/deletion polling. These are necessary for waiting on asynchronous AWS operations and are not debug code.

### Required Security Hardening for Production

Before deploying to production, you MUST:

1. **Enable JWT Signature Verification**
   - Implement proper JWKS-based token validation
   - Verify token expiration, issuer, and audience claims

2. **Use Secure Credential Management**
   - Store credentials in AWS Secrets Manager
   - Implement credential rotation policies
   - Remove all hardcoded credentials

3. **Configure Network Security**
   - Use VPC endpoints for AWS service access
   - Implement security groups with least-privilege access
   - Enable TLS/HTTPS for all communications

4. **Enable Encryption**
   - Enable encryption at rest for all data stores (S3, RDS, OpenSearch)
   - Use AWS KMS for key management
   - Implement encryption in transit

5. **Implement Logging and Monitoring**
   - Enable CloudTrail for API auditing
   - Configure application-level audit logging
   - Set up CloudWatch alarms for security events

6. **AI/ML Security Controls**
   - Implement input validation for prompt injection prevention
   - Configure AWS Bedrock Guardrails for content filtering
   - Enable rate limiting for AI endpoints

## AI/ML Security Considerations

### Input Validation
- All user queries should be validated before being sent to AI agents
- Implement prompt injection detection and filtering
- Use AWS Bedrock Guardrails for content moderation

### Output Filtering
- AI responses should be sanitized before display
- Implement PII detection and redaction where appropriate
- Log all AI interactions for audit purposes

### Bias and Fairness
- This demo uses synthetic insurance data for illustration
- Production systems should implement bias testing for AI models
- Regular fairness audits should be conducted for AI-driven decisions
- Document any known limitations or biases in AI model behavior

### Model Access Controls
- Use IAM policies to restrict Bedrock model access
- Enable CloudWatch logging for model invocations
- Implement rate limiting to prevent abuse

## Data Classification

| Data Type | Classification | Handling Requirements |
|-----------|---------------|----------------------|
| User credentials | Confidential | Encrypt at rest, never log |
| JWT tokens | Confidential | Short expiration, secure transmission |
| Insurance claims | Confidential/PII | Encrypt, access logging, retention policy |
| Policy documents | Internal | Tenant isolation, access controls |
| System logs | Internal | Retention policy, no PII |

## Key Management Strategy

For production deployments:

1. **AWS KMS Integration**
   - Create customer-managed keys (CMKs) for each data classification
   - Enable automatic key rotation
   - Implement least-privilege key policies

2. **Secrets Management**
   - Use AWS Secrets Manager for all credentials
   - Enable automatic rotation where supported
   - Audit secret access via CloudTrail

## Security Architecture

This sample demonstrates defense-in-depth security patterns:

| Layer | Component | Security Control |
|-------|-----------|------------------|
| Authentication | Amazon Cognito | JWT issuance with tenant claims |
| Runtime | AgentCore | JWT validation, identity propagation |
| Agent | Strands Agent | Tenant context extraction |
| Data (Structured) | PostgreSQL RLS | Row-level filtering by tenant |
| Data (Unstructured) | Knowledge Base | Metadata filtering by tenant |

## Third-Party Dependencies

This project uses the following third-party components:

| Component | License | Security Review |
|-----------|---------|-----------------|
| AWS Bedrock (Claude) | AWS Service Agreement | Pre-approved via AWS Marketplace |
| Strands Agents SDK | Apache 2.0 | Open source, community reviewed |
| React/Cloudscape | Apache 2.0 | AWS maintained |
| Flask | BSD | Widely used, community reviewed |

## Reporting Security Issues

If you discover a security vulnerability in this sample code, please report it by:

1. Opening a GitHub issue (for non-sensitive issues)
2. Contacting the AWS Security team at aws-security@amazon.com (for sensitive issues)

Please do NOT create public GitHub issues for security vulnerabilities that could be exploited.

## Compliance Notes

- This sample code is provided under the MIT-0 license
- No customer data or PII is included in this repository
- Sample data is synthetic and for demonstration only
- See [THREAT_MODEL.md](THREAT_MODEL.md) for detailed threat analysis
