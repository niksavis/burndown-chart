---
applyTo: "callbacks/**/*.py,data/**/*.py,ui/**/*.py,visualization/**/*.py,**/*.sql,assets/**/*.js"
description: "Enforce security, data safety, and no-secrets policy"
---

# Security and Data Safety

Apply these rules for any code/data handling changes:

- Use parameterized SQL only.
- Validate all user input and external API responses.
- Never commit or log real customer identifiers, credentials, tokens, or secrets.
- Use safe placeholders: `Acme Corp`, `example.com`, `customfield_10001`.
- Avoid adding diagnostics that print full payloads containing IDs or sensitive fields.
- Keep warning/error messages informative but sanitized.

Before completion:

1. Confirm no secret-like literals were added.
2. Confirm SQL execution paths are parameterized.
3. Confirm logs avoid customer-identifying data.
