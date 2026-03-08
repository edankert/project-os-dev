---
type: security
id: SECURITY
status: draft
owner: group:maintainers
created: 2026-01-26
updated: 2026-01-26
tags: [security]
---

# Security

> REPLACE ME (template): Replace these notes with your project’s security guidance.

Guidelines:
- Do not commit secrets, credentials, or proprietary tool binaries.
- Treat build outputs and logs as generated artifacts; keep them out of version control.
- Avoid embedding absolute internal paths into documentation; prefer environment variables or repo-relative paths.
