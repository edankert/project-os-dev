---
type: glossary
id: GLOSSARY
aliases: ["GLOSSARY"]
status: active
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
tags: [glossary]
---

# Glossary

- **adapter**: A tool-specific module that maps project-os rules to a target tool's native instruction format (e.g., CLAUDE.md for Claude Code, AGENTS.md for Codex).
- **hook contract**: A tool-agnostic specification of an enforcement point — what to check, when to check it, and what to do on failure.
- **hook implementation**: A tool-specific script or configuration that enforces a hook contract (e.g., a Claude Code shell hook).
- **team model**: A lightweight schema in SNAPSHOT.yaml identifying team members and their tool adapters, without real-time coordination.
- **orchestration delegation**: The principle that project-os provides project context but delegates agent coordination to native tool mechanisms (Agent Teams, Codex parallel, etc.).
- **feature**: A work package (goal + scope + acceptance) tracked under `features/`.
- **requirement**: An acceptance criteria spec that features must satisfy, tracked under `requirements/`.
- **ADR**: Architecture Decision Record — captures why a decision was made, with alternatives and consequences.
- **task**: An actionable unit of work with a parent feature or issue.
- **change note**: A "what changed and why" record under `changes/`.
