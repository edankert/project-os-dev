---
type: instruction
id: INSTR-MARKDOWN
status: active
owner: group:maintainers
created: 2026-05-07
updated: 2026-05-07
tags: [instructions, markdown, formatting]
---

# Markdown authoring rules

These rules define how agents and maintainers should format Markdown prose in repositories that use project-os.

## Rules
- Do not hard-wrap prose to a fixed column width in `.md` files.
- Prefer one paragraph, bullet, checklist item, table row, or heading per physical line.
- Only introduce manual line breaks when Markdown syntax or readability requires them, such as YAML frontmatter lists, fenced code blocks, tables, deliberate hard breaks, long nested lists, or generated content that already has a required shape.
- Do not reflow existing Markdown solely to change wrapping style; apply this policy to new or materially edited prose.
- Preserve existing line breaks when they carry semantic meaning, command formatting, quoted output, or list hierarchy.

## Formatter policy
- Prettier, if used, should run with `proseWrap: "never"`.
- Markdown linting, if used, should not enforce a prose line-length limit.
