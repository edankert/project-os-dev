---
type: "[[change]]"
id: CHG-20260904-A-Docs-Audit-Is-One-Bounded-Round
aliases: ["CHG-20260904-A-Docs-Audit-Is-One-Bounded-Round"]
title: "A docs audit is one bounded round, and the first drift class became a check"
status: merged
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
source: ["[[ADR-0026-When-A-Drift-Sweep-Stops]], accepted by user:edwin 2026-09-04"]
commit: "17edc84"
pr: ""
impacts: ["tools/skills/docs-audit/SKILL.md", "tools/skills/release-prep/SKILL.md", "tools/scripts/validate-docs.py"]
issues: ["[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]", "[[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[ADR-0026-When-A-Drift-Sweep-Stops]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]"]
---

# A docs audit is one bounded round, and the first drift class became a check

## Summary

A docs audit used to end only when two consecutive passes found nothing. It now runs once: three clean-context passes in parallel at one commit, findings unioned, each verified against its reproduction, fixed, residue recorded, stop. The old rule never terminated — twelve passes over the template produced counts of 36, 26, 2, 3, 2, 2, 0, 21, 2, 5, 25, 25, and pass 12 found 25 defects pass 11 had never raised after all 25 of pass 11's were fixed.

## Impact

**What an agent running the audit does differently.** Three passes instead of one, in parallel instead of in sequence, and then it stops. Three rules in the skill each replace something that failed:

- *Each pass is briefed with the domain and the rule, never with what an earlier pass found.* A primed pass confirms its priming. That is why pass 7 looked clean and pass 8, reading the same corpus without the table, found 21.
- *Findings are unioned, not filtered by agreement.* This is an amendment to the option as accepted, recorded in ADR-0026's decision record. Passes 11 and 12 ran at adjacent commits, found 25 each, and shared almost nothing; a two-of-three rule would have discarded both severe defects — the Obsidian views filtering on retired statuses, and the hook denying `done` to every feature with an acceptance check.
- *Each finding is verified against a reproduction before it is fixed.* This is what controls false positives, since agreement cannot. Done by hand across passes 11 and 12 it held 17 of 17.

**What reaches a person.** The skill now says a sweep hands back two lists — what was fixed, and what decisions are owed as `ISS-*` notes — and that only the second is a human queue. A reviewer reporting 25 items a pass exhausts the reader long before the corpus.

**A new error-level check, `BASE-STATUS`.** Every status literal in a shipped Obsidian view must be a status `STATUSES.md` allows. It reproduces the defect that shipped for seven weeks — "Features (Open)" empty in every repo because the view filtered on `in-progress` and `in-review` — in milliseconds at pre-commit and CI. It lands erroring rather than warning because both repos measured zero violations after the fix (`STATUSES.md`, "Grandfathering").

**Where the quiescence rule came from**, worth recording since it is now gone: it entered from a research summary that borrowed it from another system, and was never tested against a corpus this size.

## Documentation Coverage (All Types Considered)

- features: not-applicable
- requirements: updated — REQ-0027 `implemented`, criteria 1 and 3 reworded off the clean-pair test
- tasks: not-applicable
- issues: updated — ISS-0048 `fixed` on a 14-row recorded residue; new — ISS-0052
- tests: not-applicable — `BASE-STATUS` was negative-tested by reintroducing the original filter, which is recorded on ADR-0026 rather than as a `TST-*`
- workflows: not-applicable
- decisions: updated — ADR-0026 accepted with one amendment; ADR-0024's `RULE-ONCE` box gains the reconsideration it asked for
- risks: not-applicable — the one hazard, a new check erroring across the fleet, is carried by ISS-0052's risk scan
- changes: new — this note
- snapshot: updated — focus cleared, ISS-0052 added

## Follow-ups

- [ ] ISS-0052: the other three checks. Two need a fleet measurement before they error rather than warn.
- [ ] The 14-row residue on ISS-0048. Rows 1, 3, 6, 7, 8 and 12 are documents describing behaviour the code does not have.
- [ ] Re-measure whether the drift dimension still earns a cadence slot once the checks exist. That is ADR-0026's real acceptance test.
