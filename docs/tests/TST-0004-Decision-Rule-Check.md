---
type: "[[test]]"
id: TST-0004
aliases: ["TST-0004"]
title: "DECISION-RULE holds its contract: a `## Rule` heading demands non-empty Domain and Conformance, resolvable TSTs, and nothing else"
status: passing
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["[[TASK-0089]]", "[[REQ-0025]]", "[[ADR-0023]]"]
scope: system
kind: automated
level: unit
entrypoint: "../project-os/tools/scripts/test-decision-rule.py"
command: "python3 ../project-os/tools/scripts/test-decision-rule.py"
last_run: "2026-08-12T16:23Z"
exit_code: 0
requirements: [REQ-0025]
features: [FEAT-0023]
issues: []
tasks: [TASK-0089]
artifacts: []
evidence: []
adequacy: "Verified by inversion on 2026-08-12: four deliberate breaks of the check on a scratch copy — empty-section detection disabled, HTML-comment stripping disabled, dangling-TST resolution disabled, and the `## Rule` marker gate widened to every note — each fail the suite (exit 1); the pristine copy passes all 23 assertions (exit 0). The comment-stripping canary is deliberately asymmetric: its fixture holds `## Rule` alone inside the comment, because a fully-populated commented block would pass a comment-blind parser by accident. The suite also ran unchanged against the bundled copy under tools/cockpit/ (23/23)."
related: ["[[ADR-0010]]", "[[ADR-0011]]", "[[ADR-0021]]", "[[TST-0002]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
---

# DECISION-RULE holds its contract

## Purpose

[[ADR-0023]] made `## Rule` load-bearing syntax: its presence marks a decision note as a rule-ADR, and [[REQ-0025]] requires the validator to refuse one whose `## Domain` or `## Conformance` is absent or empty — either, not both — at any ADR status, and to report a `TST-####` named under Conformance that resolves to nothing while never treating a check code, a type name, or prose there as a dangling reference. This note executes the fixture suite that pins all of that.

## Procedure

`tools/scripts/test-decision-rule.py` in `~/Dev/repos/project-os` — importlib-loads the sibling `validate-docs.py` (the same pattern as `test-retention.py`), builds throwaway fixture repos under a tempdir, and calls `validate_decision_rule` directly. Scoped to the invariant it names rather than the whole validator, which is [[TST-0002]]'s lesson: a test whose command observes its own result cannot converge.

**The command is deliberately cross-repo.** Every file FEAT-0023 changed lives in `~/Dev/repos/project-os`, and this repo's own validator is a sync behind by design — so the note executes the canonical suite against the canonical check, from this repo's root via the sibling-checkout layout the fleet already assumes (the same convention as `external:` pointers). It keeps testing the canonical implementation after this repo syncs, which is where the check is owned.

## What the 23 assertions pin

- **Fires:** absent Domain, empty Domain, absent Conformance, empty Conformance (each named distinctly in the message), a dangling `TST-*`, the dangling one among resolving ones (reported once, by name), an `accepted` note (status independence), and a casual `## Rule` used as prose scaffolding — which fires twice and is the accepted cost ADR-0023's consequences record.
- **Silent:** the fully-clean rule-ADR, a TST resolved via the note index, a TST resolved via snapshot items, check-code-only Conformance, type-only Conformance, an ordinary ADR with no `## Rule`, a `## Rule` quoted inside a fenced code block, and a `## Rule` inside an HTML comment.
- **The shipped template, both ways:** the raw `docs/__templates__/adr.md` (block commented) trips nothing, and the same file with the comment markers stripped validates clean — read from the real template file, so template drift that arms the check against its own output fails here rather than in the first downstream repo to author an ADR.

## Expected results

- Exit 0: all assertions hold.
- Exit 1: at least one failed; each failure is printed as `FAIL <name>: got X, want Y`.

## First real corpus

Run against reality on 2026-08-12, the day the check landed: the new validator reports zero `DECISION-RULE` findings across all 12 fleet repos; your-health ADR-0020/0021 — the pilot rule-ADRs and the only notes carrying the marker — are positively parsed (Rule seen, both sections non-empty, TST-0018/TST-0019 resolved), and this repo's ADR-0022/ADR-0023, which describe the convention without carrying `## Rule`, are correctly not marked.
