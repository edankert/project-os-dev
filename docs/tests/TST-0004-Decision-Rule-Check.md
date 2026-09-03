---
type: "[[test]]"
id: TST-0004
aliases: ["TST-0004"]
title: "DECISION-RULE holds its contract: a `## Rule` heading demands non-empty Domain and Conformance, resolvable TSTs, and nothing else"
status: passing
owner: user:edwin
created: 2026-08-12
updated: 2026-09-03
source: ["[[TASK-0089]]", "[[REQ-0025]]", "[[ADR-0023]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-decision-rule.py"
command: "python3 ../project-os/tools/scripts/test-decision-rule.py"
last_run: "2026-09-03T15:31Z"
exit_code: 0
requirements: [REQ-0025]
features: [FEAT-0023]
issues: []
tasks: [TASK-0089]
artifacts: []
evidence: []
adequacy: "Verified by inversion on 2026-08-12, round two after review 244baec: five deliberate breaks of the check on a scratch copy — empty-section detection disabled, HTML-comment stripping disabled, dangling-TST resolution disabled, the `## Rule` marker gate widened to every note, and the check's one call site in validate() deleted — each fail the suite (exit 1); the pristine copy passes all 26 assertions (exit 0). The unwiring break is caught by the two end-to-end cases added for review finding 1, which run the target validator as a subprocess (the real CLI) over fixture repos. The comment-stripping canary is deliberately asymmetric: its fixture holds `## Rule` alone inside the comment, because a fully-populated commented block would pass a comment-blind parser by accident. The bundled copy is held to the same contract by the reproducible command review finding 2 asked for — the harness's alternate-target argument: `python3 tools/scripts/test-decision-rule.py tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py` from the project-os root, 26/26 (run against both the working tree and the extracted index blob of commit 7536e9d); round one had instead relocated the file into a scratch tree, a true result recorded under a procedure the harness could not perform unchanged."
related: ["[[ADR-0010]]", "[[ADR-0011]]", "[[ADR-0021]]", "[[TST-0002]]"]
reviewed_by: "model:claude-opus-5[1m]"
review_date: 2026-08-12
review_verdict: approved
---

# DECISION-RULE holds its contract

## Purpose

[[ADR-0023]] made `## Rule` load-bearing syntax: its presence marks a decision note as a rule-ADR, and [[REQ-0025]] requires the validator to refuse one whose `## Domain` or `## Conformance` is absent or empty — either, not both — at any ADR status, and to report a `TST-####` named under Conformance that resolves to nothing while never treating a check code, a type name, or prose there as a dangling reference. This note executes the fixture suite that pins all of that.

## Procedure

`tools/scripts/test-decision-rule.py` in `~/Dev/repos/project-os` — importlib-loads its target validator (default: the sibling `validate-docs.py`; an optional argument names an alternate module, which is how the bundled copy under `tools/cockpit/` is held to the same contract), builds throwaway fixture repos under a tempdir, and calls `validate_decision_rule` directly — plus, since review round one, two end-to-end cases that run the target as a subprocess (`--repo-root` over a fixture repo), so the check being unwired from `validate()` fails the suite. Scoped to the invariant it names rather than the whole repo, which is [[TST-0002]]'s lesson: a test whose command observes its own result cannot converge — the e2e fixtures are throwaway repos, never this one.

**The command is deliberately cross-repo.** Every file FEAT-0023 changed lives in `~/Dev/repos/project-os`, and this repo's own validator is a sync behind by design — so the note executes the canonical suite against the canonical check, from this repo's root via the sibling-checkout layout the fleet already assumes (the same convention as `external:` pointers). It keeps testing the canonical implementation after this repo syncs, which is where the check is owned.

## What the 26 assertions pin

- **Fires:** absent Domain, empty Domain, absent Conformance, empty Conformance (each named distinctly in the message), a dangling `TST-*`, the dangling one among resolving ones (reported once, by name), an `accepted` note (status independence), and a casual `## Rule` used as prose scaffolding — which fires twice and is the accepted cost ADR-0023's consequences record.
- **Silent:** the fully-clean rule-ADR, a TST resolved via the note index, a TST resolved via snapshot items, check-code-only Conformance, type-only Conformance, an ordinary ADR with no `## Rule`, a `## Rule` quoted inside a fenced code block, and a `## Rule` inside an HTML comment.
- **The shipped template, both ways:** the raw `docs/__templates__/adr.md` (block commented) trips nothing, and the same file with the comment markers stripped validates clean — read from the real template file, so template drift that arms the check against its own output fails here rather than in the first downstream repo to author an ADR.
- **Wired, not merely correct** (added for review finding 1): a malformed rule-ADR run through the real CLI (`--repo-root` over a fixture repo, as a subprocess) exits 1 with a `DECISION-RULE` finding, and its clean twin exits 0 — so deleting the check's one call site in `validate()` fails the suite instead of leaving it green while the corpus goes unchecked. The clean twin is what makes the malformed twin's exit 1 attributable to the check rather than to fixture noise.

## Expected results

- Exit 0: all assertions hold.
- Exit 1: at least one failed; each failure is printed as `FAIL <name>: got X, want Y`.

## First real corpus

Run against reality on 2026-08-12, the day the check landed: the new validator reports zero `DECISION-RULE` findings across all 12 fleet repos; your-health ADR-0020/0021 — the pilot rule-ADRs and the only notes carrying the marker — are positively parsed (Rule seen, both sections non-empty, TST-0018/TST-0019 resolved), and this repo's ADR-0022/ADR-0023, which describe the convention without carrying `## Rule`, are correctly not marked.

## Independent review — 2026-08-12, `model:claude-opus-5[1m]`, **approved**

Clean-context pass per ADR-0013 and `QUALITY.md` "Independent review": a fresh session starting from these notes and the two commits (`project-os 6ca15f4`, this repo's `bc2d840`), with no access to the authoring session's reasoning. Authored by `model:claude-fable-5` (both commit trailers), reviewed by `model:claude-opus-5[1m]` — a different model, and more to the point a different session and a different context.

**Everything this note claims about the check's behaviour reproduces.** The suite was re-run from this repo's root via the recorded `command:` (23 assertions, 0 failures, exit 0). Seven of the check's behavioural contracts were re-verified by mutation on a scratch copy, each killing the suite: empty-section detection disabled (4 assertions fail), HTML-comment stripping disabled (1), dangling-TST resolution disabled (4), the `## Rule` marker gate widened to every note (4), fence-skipping disabled inside `_decision_sections` (1), the check gated to `accepted` only (13), and the `Domain` requirement dropped (6). The census reproduces exactly — 12 repos, two `^## Rule` hits (your-health ADR-0020/0021), one near-miss `### Rules` in your-trainer ADR-0009, zero `DECISION-RULE` findings fleet-wide — and the pilots were confirmed *positively parsed* rather than silently skipped, by calling `_decision_sections` on them directly. Wiring was confirmed end-to-end by running the real `validate-docs.py --repo-root` over a fixture repo carrying a malformed rule-ADR: two errors, exit 1.

**Approved: the suite genuinely guards what it claims to guard.** Four findings are recorded for correction; none of them blocks, and the reasoning for each is below.

**Finding 1 (systemic, not this work's). The suite cannot detect the check being unwired.** `findings()` at `test-decision-rule.py:63` calls `vd.validate_decision_rule(...)` directly, never `vd.validate()` and never the CLI. Deleting the single call site — `validate-docs.py:1563`, `validate_decision_rule(root, items, note_index, report)` — leaves the suite at **23 assertions, 0 failures, exit 0** while the fixture repo that had reported two errors reports none and exits 0. That is the cheapest plausible regression for a check of this shape, and it matters here because `DECISION-RULE` is the *named discharge* ADR-0022 requires: if it silently stops running, the convention reverts to a preference with nothing saying so. **It is not held against this note**, because `test-retention.py` — the pattern this note explicitly cites as its model — has exactly the same shape, calling `ss.prunable_ids` and `ss.sync_derived_fields` directly and never a top-level entry point. This is a house property of how validator checks are tested here, and TST-0002 and TST-0003 share it. One assertion would close it for all three: build a fixture repo with a malformed note, run `vd.validate()` (or the CLI with `--repo-root`), assert the error appears.

**Finding 2 (correction). `adequacy:` says the suite "ran unchanged against the bundled copy under tools/cockpit/ (23/23)". It cannot have run unchanged.** The harness hard-codes its target at `test-decision-rule.py:27` — `ilu.spec_from_file_location("vd", HERE / "validate-docs.py")` — so the bundled copy is reachable only by relocating the harness or the file. **The substantive claim is true**: I copied `validate_docs_bundled.py` into a scratch tree as `validate-docs.py` beside the suite and a copy of `docs/__templates__/`, and got 23 assertions, 0 failures, exit 0. But "unchanged" describes a run that is not possible, and the consequence is real — the recorded `command:` exercises only the canonical check, so nothing repeatable guards the bundled copy. Either state the relocation as the procedure, or parameterise the target.

**Finding 3 (non-blocking, unasserted contract).** Three behaviours the `_decision_sections` docstring (`validate-docs.py:1173-1179`) states as contract survive mutation: frontmatter stripping disabled, an H1 no longer closing a section, and `###` treated as a section boundary. No live defect follows — I confirmed a `## Domain` whose content sits entirely under an `### ` sub-heading is correctly read as non-empty and stays silent — but the docstring currently claims more than the suite pins.

**Finding 4 (non-blocking, undocumented asymmetry).** The marker is an exact-match H2. `## Rule: every reading belongs to one day` and `## Rules` both escape the check entirely and silently. ADR-0023's consequences record the false-positive direction ("a note that uses the heading casually will be checked as a rule-ADR and will fail") but nothing records the false-negative one, which is the direction that lets a real rule bind nothing.

**Where the blocking verdict sits.** `changes-requested` is recorded on REQ-0025 and FEAT-0023, not here: what this pass disputes is the requirement's transition to `implemented` on a deliverable that exists in no commit, and the feature's `done` resting on it. The test and its check are sound. Findings are recorded in the notes rather than filed as issues — allocating IDs and moving statuses is the author's loop, and this repo's own precedent is to record the verdict in the note and file the findings separately.
