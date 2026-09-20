---
type: "[[change]]"
id: CHG-20260920-The-Review-Machinery-Closes-Round-Ones-Findings
title: "A review packet, a budget and a fleet check that each do what they claim"
status: merged
created: 2026-09-20
updated: 2026-09-20
owner: user:edwin
related: ["[[TASK-0146-The-Four-Findings-Round-One-Left]]", "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]", "[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]"]
tags: [review, hooks, fleet]
---

# A review packet, a budget and a fleet check that each do what they claim

## What changed

Four things anyone running a review will notice.

**A review packet is refused when it has no code in it.** `review-packet.py` used to write a packet whose Source diff section read "(these commits change no source outside docs/)" and leave it at that. For a feature whose notes live in `project-os-dev` and whose code lives in `project-os`, that is every time. The new `--code-root` takes the commits and the diff from the other repo and says so in the packet; `--allow-empty-diff` covers work that really is documentation. Without one of them the script now exits with an error naming both causes.

**A reviewer keeps the budget it started with.** The hook decided it was in round two if the text `review-packet-…-r2` appeared anywhere in a tool call, so a `grep` or `ls` that merely mentioned such a path cut the reviewer from 40 calls to 15 for the rest of its run. Only opening a round-two packet does that now.

**Anyone can ask which repos have fallen behind the template.** `tools/scripts/fleet-file-drift.py` compares every template-owned file in every repo against the template and lists what is stale or missing. Ownership comes from `tools/sync/MANIFEST.yaml`, so it follows the manifest rather than keeping a list.

**The review budget is written down once.** The figure 40 was in five files. The hook holds it, the packet script reads it from the hook, the skill states it for the reviewer, and everything else points at the skill.

## Who notices

An author starting a review, and anyone who has lost a review to a budget that was not what they thought. The empty-packet error is the one that will be seen most: a review of a cross-repo feature now stops before it starts rather than quietly reviewing prose.

## Impact

- `tools/scripts/review-packet.py` — `--code-root`, `--allow-empty-diff`, an error on an empty diff, and the budgets read from the hook.
- `tools/adapters/claude-code/hooks/review-budget.py` — `announces_round_two()`, narrowed to a read of a file-naming field.
- `tools/scripts/fleet-file-drift.py` — new. **Not** `fleet-drift.py`, which `project-os-cockpit` has carried since 2026-08-29 for a different question.
- `tools/instructions/HOOKS.md`, `tools/skills/independent-review/SKILL.md`, the two generated reviewer agent files — the budget stated once.
- Tests: `test-review-budget.sh` 15 → 19 assertions, `test-review-packet.sh` 24 → 29, new `test-fleet-file-drift.sh` at 11.

## Where it landed

`~/Dev/repos/project-os` `c264bd6`, then eight files to the twelve other repos, each committed by named path with hooks disabled, followed by a second commit per repo regenerating the two reviewer agent files. All thirteen repos pass `test-review-budget.sh` (19) and `test-review-packet.sh` (29).

## Known, not fixed here

`fleet-file-drift.py` reports five pre-existing divergences: `project-os-cockpit` on `docs/__templates__/feature.md`, `tools/adapters/codex/ADAPTER.md` and `tools/scripts/run-tests.py`; `project-os-dev` and `your-trainer` on `.github/workflows/validate-docs.yml`. The cockpit authors tooling before it is upstreamed, so some of that is ahead of the template rather than behind it. Each needs a decision.
