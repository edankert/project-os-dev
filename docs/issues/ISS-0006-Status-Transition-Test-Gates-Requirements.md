---
type: "[[issue]]"
id: ISS-0006
aliases: ["ISS-0006"]
title: "status-transition/SKILL.md test-gates requirements, contradicting QUALITY.md and ADR-0007 — in all 10 fleet repos"
status: fixed
phase: "[[PHASE-0002-State-Model-Simplification]]"
severity: medium
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
component: lifecycle-rules
source: ["review:2026-07-25-fleet-state-audit"]
related: [ADR-0007, FEAT-0014, REQ-0018]
tasks: []
tests: []
---

# status-transition contradicts QUALITY.md on requirement test-gating

## Problem

`tools/skills/status-transition/SKILL.md` step 2 instructs an agent to check linked tests before advancing a requirement:

> Verification gate: before transitioning a task to `done`, issue to `closed`, requirement to `implemented`, feature to `done`, or phase to `done`, verify linked `TST-*` notes are passing …

`tools/instructions/QUALITY.md` says the opposite, in bold, on the same subject:

> **A requirement is never gated on linked tests.** It needs no `[[test]]` note to reach `implemented`, and a linked test that is `blocked`/`failing`/`draft` does not block it either.

`ADR-0007`'s 2026-07-24 amendment is the authority, and is emphatic: applying the test gate to `implemented` "reintroduced it through the back door", "penalised the one behaviour the system wants to encourage", and was explicitly reverted in `validate-docs.py` (`if coll_name == "requirements": terminal = None`).

So the validator is correct, `QUALITY.md` is correct, and the skill an agent reads *while performing the transition* tells it to do the thing the ADR reverted.

## Repro

```bash
grep -n "requirement to \`implemented\`" tools/skills/status-transition/SKILL.md
grep -n "never gated on linked tests" tools/instructions/QUALITY.md
```

## Expected

The skill either restates the rule correctly, or does not restate it at all and links to the normative source.

## Actual

It restates it incorrectly, and has done since 2026-07-21 — the same day `QUALITY.md` was updated with the opposing text. The ADR-0007 amendment on 2026-07-24 corrected the validator, `QUALITY.md`, `STATUSES.md`, and `close-out`, and missed this file.

## Evidence

Present in **all 10 fleet repos** (the file is template-synced):

```
edankert.com  obsidian-supernote-sync  project-os  project-os-dev  project-os-cockpit
your-applications.com  your-trainer  your-health  your-sudoku  yourtrainer-mcp
```

The same step also gates `phase` to `done` on linked tests, which no validator check implements — a second, quieter divergence in the same sentence.

## Impact

Requirement advancement is stated in **four** places: `QUALITY.md`, `STATUSES.md`, `close-out/SKILL.md`, and `status-transition/SKILL.md`. Four copies is why a three-file correction could leave the fourth wrong and nothing detect it — no check compares prose to prose.

The practical effect is an agent following the skill will refuse a legitimate `implemented` transition, or demand a test note that ADR-0007 explicitly says is not required. That is precisely the your-sudoku REQ-0086/REQ-0087 failure the amendment was written to stop, re-entering through the skill instead of the validator.

## Next Actions

- [ ] Correct the sentence (immediate, low-risk, independent of everything else).
- [ ] Remove the restatement entirely once [[FEAT-0014-Single-State-Contract|FEAT-0014]] gives the rule one normative home — this issue is the concrete evidence for that feature.
- [ ] Re-sync the corrected skill to all 10 repos.
