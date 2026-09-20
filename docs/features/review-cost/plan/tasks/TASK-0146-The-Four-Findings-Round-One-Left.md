---
type: "[[task]]"
id: TASK-0146
aliases: ["TASK-0146"]
title: "The four findings round one left on the review machinery"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-20
updated: 2026-09-20
source: ["The FEAT-0034 independent review, round 1, 2026-09-20", "Edwin, 2026-09-20: 'Finish the FEAT-0034 as suggested'"]
parent: "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"
effort: "Medium"
due: ""
depends: [TASK-0145]
blocks: []
related: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]", "[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]"]
tests: ["[[TST-0013]]", "[[TST-0014]]"]
---

# The four findings round one left on the review machinery

## Problem

Round one of FEAT-0034's review left four defects in the feature's own code. Each is fixed here, before the feature closes, as ADR-0047 requires.

## Definition of Done

- [x] **Fleet file drift is checkable.** `fleet-file-drift.py` reports which template-owned files in each repo no longer match the template.
- [x] **A round-one reviewer keeps its budget** unless it actually reads a round-two packet.
- [x] **A packet with no source diff is refused**, and a feature whose notes and code are in different repos can be reviewed.
- [x] **The budget is stated once** (REQ-0027), and nothing can quietly restate it.
- [x] Every fix has a test that fails without it, verified both ways.
- [x] The template and all twelve other repos carry the result.

## What each one was

**1. Nothing compared the fleet's files to the template.** On 2026-09-20 an adapter hook was fixed in the template, reached two repos, and sat stale in eleven — while a reviewer had just declared the fleet identical on the strength of one `md5` of `independent-review/SKILL.md`, a file the sync always carries. The file that enforced the budget was never compared.

`tools/scripts/fleet-file-drift.py` takes ownership from `tools/sync/MANIFEST.yaml`, so it needs no list of its own and follows the manifest when that changes. It reports stale and missing files per repo and exits 1 on drift. `merge`, `seed` and `project` paths are expected to diverge and are not reported.

**It is deliberately not called `fleet-drift.py`.** `project-os-cockpit` has carried a script of that name since 2026-08-29, for a different question: which validator *rules* each repo runs. `tools/scripts/` is template-owned, so a file named `fleet-drift.py` in the template would have overwritten the cockpit's tool at the next sync. The name collision was caught by reading the cockpit's copy before shipping.

**2. A round-one reviewer could be silently demoted to a 15-call budget.** `ROUND_TWO_PACKET` was matched against the whole `tool_input` JSON of every call, so a `Bash` command that merely mentioned a path like `review-packet-FEAT-0001-r2.md` flipped the hook into round two, and the flip never flips back. Now only a read, through a field that names a file (`file_path`, `path`, `notebook_path`), announces round two.

**3. A packet with no source diff arrived as a blank section.** For a feature whose notes are here and whose code is in `project-os`, the diff filter strips everything the commits touched. `review-packet.py` gains `--code-root`, which takes the commits and the diff from the other repo and says so in the packet, and `--allow-empty-diff` for work that really is documentation. Without either, an empty diff is now an error naming both causes.

A cross-repo review still needs `--range`, because `commits_for` matches the feature id on the subject line only, and upstream commit subjects name the downstream feature in their body. That matching is deliberate and recorded (it once doubled a diff), so it was left alone and the error message says to pass `--range`.

**4. The budget was stated at five sites.** `40` appeared in the skill, `HOOKS.md` twice, `review-packet.py`, the agent file and `generate-adapters.py`, against [[REQ-0027-Every-Normative-Rule-Is-Stated-Once|REQ-0027]]. Now the hook holds the numbers, `review-packet.py` reads them from the hook (honouring the per-repo env overrides as a side effect), the skill states them once in prose, and `HOOKS.md` and the agent file point at the skill.

Two numbers still exist — the hook's default and the skill's prose — because a reviewer has to read the figure somewhere. Two assertions stop them drifting: the skill must state the budget the hook enforces, and no other file may restate it.

## Verification

Each fix was verified both ways: the test passes with it and fails without it.

| Harness | Before | After | Reverted |
|---|---|---|---|
| `test-review-budget.sh` | 15 assertions | **19, 0 failures** | 2 fail on whole-input matching; 1 fails when a file restates the budget |
| `test-review-packet.sh` | 24 assertions | **29, 0 failures** | — |
| `test-fleet-file-drift.sh` | new | **11, 0 failures** | 4 fail when the content comparison is disabled |

`test-hooks.sh` 80 assertions, the validator clean, all 65 adapter artifacts current.

## The fleet

Template `c264bd6`, then eight files to twelve repos, each committed by named path with hooks disabled and checked to hold eight files.

**A failing assertion reached all twelve first.** The new "no other file restates the budget" check reads the two generated reviewer agent files, which still carried the old wording because `generate-adapters.py` was synced but not run. Caught by running the harness in each repo straight after the copy; a second commit per repo regenerated them. Both artifacts, nothing else: `--check` reported exactly two stale in every repo before and none after.

**The first sync attempt was a no-op and looked like a success.** The loop used `for f in $FILES` under zsh, which does not word-split an unquoted variable, so every `cp` failed on one bogus path and every `git commit` found nothing staged. The per-repo test still printed a pass, because the old file was still there. It was caught by the commit hashes not moving. The rewrite uses a shell array.

## What the new checker found

Run across the fleet after the sync: **3 repos drifted, 5 files**, none of them from this work.

- `project-os-cockpit`: `docs/__templates__/feature.md`, `tools/adapters/codex/ADAPTER.md`, `tools/scripts/run-tests.py`
- `project-os-dev` and `your-trainer`: `.github/workflows/validate-docs.yml`

The cockpit is where validator and tooling work is authored before it is upstreamed, so some of its divergence is expected to be *ahead* rather than behind. Deciding each one is separate work and is in the close-out summary, not done here.
