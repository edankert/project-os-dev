---
type: "[[issue]]"
id: ISS-0041
aliases: ["ISS-0041"]
title: "Four files still require a different model family for review"
status: fixed
phase: "[[PHASE-0003]]"
severity: medium
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
component: docs
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 1.1", "https://claude.ai/code/artifact/4d82b4ff-73ed-42ab-97c0-9a2d0f98fcfc"]
related: ["[[ADR-0013-Independence-Is-Clean-Context]]", "[[ISS-0006-Status-Transition-Test-Gates-Requirements]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]"]
tasks: []
tests: []
---

# Four files still require a different model family for review

## Problem

ADR-0013 decided that what makes a reviewer independent is a clean context, not a different model family. QUALITY.md and rule 1 of the review skill say so. Four other files still instruct the old rule, so an agent reading the review skill's checklist is told to find a different model two paragraphs after being told it does not need one.

The four, in the template repo:

| File and line | What it says |
|---|---|
| `tools/skills/independent-review/SKILL.md:45` | "Launch the review with a different model" |
| `tools/skills/docs-audit/SKILL.md:46` | "Run the audit with a different model ... a fresh model family" |
| `tools/adapters/claude-code/ADAPTER.md:158` | "`QUALITY.md` ... require a *different model family* or a human" |
| `tools/instructions/HOOKS.md:92` | HC-008's rule line: "independent review must not be performed by the authoring model" |

The ADAPTER.md paragraph is the most costly of the four, because it tells the reader the pinned reviewer subagent cannot satisfy the gate. Under ADR-0013 it can.

## Repro

```bash
cd ~/Dev/repos/project-os
grep -rn "different model" tools/skills/independent-review/SKILL.md tools/skills/docs-audit/SKILL.md tools/adapters/claude-code/ADAPTER.md
grep -n "authoring model" tools/instructions/HOOKS.md
grep -n "Model family is \*\*not\*\* the gate" tools/instructions/QUALITY.md
```

## Expected

Every statement of the review-independence rule either matches ADR-0013 — a clean context that is not the authoring session — or links to QUALITY.md instead of restating it.

## Actual

Four statements name model family. HC-008 is still called the "model routing hint", which names the thing it no longer routes on.

## Evidence

- Verified in the template on 2026-09-03 at the four lines above.
- The generated reviewer prompt in `tools/scripts/generate-adapters.py` already has the ADR-0013 wording; copy from it.

## Next Actions

- [x] Rewrite the four statements to the ADR-0013 rule, or replace them with a link to QUALITY.md "Independent review (clean-context)".
- [x] Rename HC-008 from "model routing hint" to "delegation hint" in HOOKS.md, the hook filename reference, and ADAPTER.md.
- [x] Sequence this before [[TASK-0103]], which rewrites the same HC-008 contract for a different reason.

## Resolution

Fixed in the template by commit `1b5956e` on 2026-09-03 (CHG-20260903-Prompting-Guide-Contradictions there). The four statements now link to QUALITY.md "Independent review (clean-context)"; HC-008 is named "delegation hint" in HOOKS.md, ADAPTER.md and the hook's own header, and the script keeps its filename. The hook's status lists were brought back to the current taxonomy in the same commit. Landed before [[TASK-0103]], which is still backlog. The validator and the generator check passed at the commit; CI has not run because the commit is not pushed.

## Sibling search

Siblings found: [[ISS-0006-Status-Transition-Test-Gates-Requirements]] (a gate restated in four files, corrected in three) and this issue's own family, ISS-0042 and ISS-0043, filed the same day. Searched `docs/issues/` for: restate, contradict, drift, model family. Per the intake harvest rule the family gets a proposed rule-ADR: [[ADR-0024-A-Normative-Rule-Is-Stated-Once]].

## Risk scan

Run against the LIFECYCLE.md triggers. No new risks: no dependency, env var, path, runtime or credential change. Prose only.
