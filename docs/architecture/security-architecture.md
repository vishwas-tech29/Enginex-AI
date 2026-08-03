# Security architecture

## Authentication and authorization

- JWT access tokens and refresh tokens with rotation.
- OAuth providers for Google and GitHub.
- Role-based access control with organization, team, and project scopes.
- Project actions require explicit permission checks before execution.

## Secrets and encryption

- API keys and provider secrets are stored encrypted at rest.
- Secret material is managed by a KMS-backed secret provider in production.
- Signed URLs protect object storage downloads and uploads.

## Network and edge protections

- TLS everywhere.
- Rate limiting and WAF rules on public entry points.
- CORS configured per origin and environment.
- CSRF protections for browser-facing state-changing operations.

## Auditing and observability

- Every mutating operation emits an audit entry.
- Audit records capture user, action, resource, details, and source IP.
- Logs carry correlation IDs for cross-service debugging.
- Alerts are generated on unusual authentication, permission, or token activity.
