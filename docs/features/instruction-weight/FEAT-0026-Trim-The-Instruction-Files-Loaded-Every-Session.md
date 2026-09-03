---
type: "[[feature]]"
id: FEAT-0026
aliases: ["FEAT-0026"]
title: "Trim the instruction files an agent loads every session"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] findings 4.1, 4.3, 4.4"]
goal: "Cut LIFECYCLE.md to under its budget and give the other four over-long normative files a fixed shape: the rule, one line of reason, the ADR link. The stories move to the ADR Context sections they came from."
requirements: ["[[REQ-0026-Instruction-Files-Carry-Rules-Not-History]]"]
tasks: ["[[TASK-0098]]", "[[TASK-0099]]", "[[TASK-0100]]", "[[TASK-0101]]"]
release: ""
related: ["[[ADR-0016-Ceremony-Proportionate-To-The-Change]]", "[[ADR-0004-Mandatory-Skill-Steps]]", "[[ISS-0031-Instruction-Prescribes-A-Method-For-Two-Different-Needs]]"]
tests: ["[[TST-0006]]"]
---

# Trim the instruction files an agent loads every session

## Goal

LIFECYCLE.md is 1,343 words and every Claude Code and Cursor session loads all of it. The Cursor always-on bundle is 5,711 words of the same four files inlined. None of the rules should go; what should go is the history — "a local pass is not a CI pass" carries two anecdotes under a rule that is two lines, and STATUSES.md still explains the retired `check` type at length.

`tools/instructions/README.md:17` already asks for this: "Use a short title and explicit Rules bullets; avoid narrative prose where possible."

Measured on 2026-09-03, in words: STATUSES 2,772 · TESTING 1,608 · QUALITY 1,408 · DECISIONS 1,381 · LIFECYCLE 1,343 · the four always-on Cursor rules 5,711.

## Scope

| Task | Finding | Files |
|---|---|---|
| [[TASK-0098]] | 4.1 (the always-loaded one) | `LIFECYCLE.md`, and the ADRs the anecdotes move into |
| [[TASK-0099]] | 4.1 (the rest) | `STATUSES.md`, `TESTING.md`, `QUALITY.md`, `DECISIONS.md` |
| [[TASK-0100]] | 4.3 | `docs/__templates__/feature.md`, `test.md` |
| [[TASK-0101]] | 4.4 | `tools/scripts/generate-adapters.py` |

## Out of scope

- **Deleting a rule, or the reason for one.** The guides are explicit that a model follows a rule better when it knows why. What moves is the third paragraph, not the second.
- **A validator check on file length.** [[TST-0006]] is the check; making it a build failure over twelve repos is a separate decision under [[ADR-0011-No-Permanent-Warning-Tier]].
- **The word budgets for the other five files.** Only LIFECYCLE.md has a number the review states. The others are shaped, not counted, until the owner sets budgets — see the open question in the plan.

## Acceptance

- [x] `wc -w tools/instructions/LIFECYCLE.md` is under 1,000 (the 800 was amended on [[REQ-0026]]; measured 966) — evidence: [[TST-0006]] passing 2026-09-03
- [x] `.cursor/rules/lifecycle.mdc` was regenerated and tracks it (1,005 words) — evidence: [[TST-0006]] passing 2026-09-03, second assertion inverted
- [x] Every anecdote removed lands in an ADR Context section or a change note, listed row by row — evidence: the moved-text table in the template's CHG-20260903-Instruction-Weight, sixteen rows
- [x] A scaffolded feature and test note no longer inherit eight and nine lines of frontmatter commentary — evidence: template commit `74753d1`, one line each
- [x] A generated skill body is the pointer plus when-to-use, and the three close-out steps appear in the close-out skill only — evidence: template commit `2025f32`, `.claude/skills/inbox-triage/SKILL.md` and `.claude/skills/close-out/SKILL.md` read after regeneration

## Risk scan

Run against the LIFECYCLE.md triggers. One fires: LIFECYCLE.md, STATUSES.md, QUALITY.md and the templates are synced wholesale into eleven downstream repos, so a deletion here deletes there. No `RISK-*` note — the sync is the normal path for every instruction change and nothing about this one is unusual. Recorded as the negative result the scan asks for, with one caution carried into [[TASK-0099]]: a downstream repo that edited its own copy loses that edit at the next sync, which is true today and not made worse here.

## Links

- Requirement: [[REQ-0026-Instruction-Files-Carry-Rules-Not-History]]
- Review: [[Prompting-Guide-Review-2026-09-03]]
- Implementation target: `~/Dev/repos/project-os`.
