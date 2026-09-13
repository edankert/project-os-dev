---
type: "[[change]]"
id: CHG-20260910-A-Review-Gate-Runs-Two-Rounds
aliases: ["CHG-20260910-A-Review-Gate-Runs-Two-Rounds"]
title: "A review gate runs two rounds, and only a behavioural finding blocks it"
status: merged
owner: user:edwin
created: 2026-09-10
updated: "2026-09-10"
source: ["[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]], accepted by user:edwin 2026-09-10"]
commit: ""
pr: ""
impacts: ["tools/instructions/QUALITY.md", "tools/skills/independent-review/SKILL.md", ".cursor/rules/quality.mdc"]
issues: ["[[ISS-0061-A-Review-Gate-Has-No-Round-Cap-And-No-Severity-Bar]]", "[[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]]", "[[ADR-0026-When-A-Drift-Sweep-Stops]]", "[[ADR-0013-Independence-Is-Clean-Context]]"]
---

# A review gate runs two rounds, and only a behavioural finding blocks it

## Summary

The independent-review gate used to loop until a reviewer stopped finding things, and any true finding was a blocker. It now runs at most two rounds, and a finding holds a terminal status shut only when it refutes a claim about behaviour or an acceptance criterion. The change is three bullets in `QUALITY.md` and a rewritten step 5 in `independent-review/SKILL.md`.

## Impact

**What an agent closing a review does differently.** Round one reviews the work. Round two verifies the fixes to round one's blocking findings and nothing else — it is not a fresh sweep. There is no round three: a second `changes-requested` goes to one adjudicated exchange between the reviewer and a separate critic, where each disagreement cites specific code and both positions reach the adjudicator side by side, and its output is a decision for the owner.

**What stops blocking.** A true finding that does not refute a behavioural claim or an acceptance criterion is now filed as an `ISS-*` at `triage` and the item closes over it. Applied to the eight-round review on [[CHG-20260804-Retention-And-Field-Derivation]], rounds four to seven produce three issues and no delay: each found no code defect and blocked on a stale figure in a note.

**What does not change.** `independent-review/SKILL.md` step 3 still asks the reviewer for every finding, labelled reproduced or not. Telling a reviewer to be conservative makes it drop the plausible findings itself, which is the failure that instruction exists to prevent. The severity bar sits at transcription, beside the reproduction filter that was already there.

**The author never answers the reviewer in turns.** This is the rule most likely to be broken by accident, because a conversational back-and-forth is the obvious thing to reach for. A reviewer facing a follow-up rebuttal abandons true findings, and does so more readily when the rebuttal reasons at length and is wrong; ADR-0028 records the evidence.

**Where the rules live.** All three are in `QUALITY.md`, "Independent review (clean-context)". The skill links them and restates none of them (REQ-0027).

## Verification

- `bash tools/scripts/validate-docs.sh` — OK in the template and in this repo.
- The template's five test scripts, after the edit: `test-hooks` 74 assertions, `test-pause-rule` 15, `test-verdict-model` 31, `test-decision-rule` 26, `test-retention` 23, `test-word-budgets` 3 — 0 failures each.
- `generate-adapters.py --check` exits 0 in both repos; `.cursor/rules/quality.mdc` was regenerated in both, which is the only generated artifact this touches.
- No test guards the new rules. They are prose about a human-and-agent process, with no observable output a script can read — the same gap `FEAT-0025` recorded for its writing rules. [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]] is what would make the round cap checkable.

## Documentation Coverage (All Types Considered)

- features: not-applicable
- requirements: not-applicable
- tasks: not-applicable
- issues: new — [[ISS-0061-A-Review-Gate-Has-No-Round-Cap-And-No-Severity-Bar|ISS-0061]] (`fixed`), [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]] (`triage`)
- tests: not-applicable — see Verification; no command distinguishes a process rule that is stated from one that is followed
- workflows: not-applicable
- decisions: new — [[ADR-0028-A-Review-Gate-Runs-Two-Rounds|ADR-0028]], accepted with three of four acceptance criteria open
- risks: not-applicable — risk scan run, no trigger applies (no dependency, env var, artifact path, long-running step or credential surface). The one hazard, a gate closing over true findings, is stated in ADR-0028's consequences
- changes: new — this note
- snapshot: updated — focus moved to ISS-0061; ADR-0028, ISS-0061 and ISS-0062 registered

## Follow-ups

- [ ] **The cap is unchecked.** A ninth round would pass every check in the system. [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]] carries it, and it is also ADR-0028's route to becoming a rule-ADR.
- [ ] **The adjudicated exchange has never run.** Record what happens the first time it does: whether the citation constraint held, whether the critic capitulated, and whether the owner got a decision or another list.
- [ ] **Nine unrelated template files are behind.** `sync-project-os.sh --dry-run` reports `HOOKS.md`, `SNAPSHOT.md`, `STATUSES.md`, `install-git-hooks.sh`, `run-tests.py`, `test-verdict-model.sh`, `validate-docs.py`, `MANIFEST.yaml` and `hooks/pre-push` as updated upstream, plus a `CONFLICT` on `.github/workflows/validate-docs.yml` and `LOCAL-CONTENT` on `docs/__templates__/test.md`. This change copied only its own two files rather than widening the diff. The backlog predates it and needs its own sync pass.
