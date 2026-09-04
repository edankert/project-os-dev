---
type: "[[change]]"
id: CHG-20260904-Hooks-Ship-Executable
aliases: ["CHG-20260904-Hooks-Ship-Executable"]
title: "The hook scripts carry the executable bit, the installer sets it on every run, and the harness asserts it"
status: merged
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
source: ["user:edwin, a your-trainer session, 2026-09-04"]
commit: "e1c46bf, 2faa90f (template)"
pr: ""
impacts: ["tools/adapters/claude-code/hooks/", "tools/scripts/generate-adapters.py", "tools/scripts/test-hooks.sh", "tools/adapters/claude-code/ADAPTER.md"]
issues: ["[[ISS-0055-The-Delegation-Hint-Is-Not-Executable-In-Any-Repo]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[TST-0007-The-Hooks-Emit-What-The-Contracts-Say]]", "[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]"]
---

# The hooks ship executable

## Summary

Every prompt in every project-os repo printed `Permission denied` where the delegation hint should have been. `.claude/settings.json` registers each hook by bare path with no interpreter in front, and `model-routing-hint.sh` was mode `644` in all twelve repos under `~/Dev/repos/`. The hint never blocks, so nothing stopped working; the focus line it exists to print was simply absent, replaced by a warning, on every turn since the hook shipped.

The executable bit was never travelling with the file. The template recorded all eight hook scripts as `100644` and sets `core.fileMode = false`, so a `chmod +x` there was invisible to git. The seven older hooks worked downstream only because `ADAPTER.md` gave `chmod +x .../hooks/*.sh` as an install step and it was run once — before this hook existed. Any hook the template adds after an install arrives the same way.

Fixed in the template at `e1c46bf` and `2faa90f`: the eight scripts are `100755` in the index, `generate-adapters.py --install-hooks` sets the bit on every file in `hooks/` including on the path that leaves an existing `hooks` key alone, `test-hooks.sh` asserts each hook is executable, and `ADAPTER.md` drops the manual `chmod` from the preferred install.

## Impact

- **The sync does not carry this fix.** `sync_file` returns early on `current == new`, comparing bytes only, so a mode-only change never reaches a repo whose copy of the script is already identical. `python3 tools/scripts/generate-adapters.py --install-hooks` is what repairs an existing repo, and `SYNCING.md` step 5 already calls for it after every sync.
- **A repo with `core.fileMode = false` needs one more step.** Git ignores the bit the installer just set, so the next clone is broken again. `git update-index --chmod=+x tools/adapters/claude-code/hooks/*` then commit, once per repo. Six repos carry all eight hooks as `100644` and are one clean clone away from every hook failing, not just this one.
- [[TST-0007-The-Hooks-Emit-What-The-Contracts-Say]] goes from 37 to 45 assertions. The eight run last, so the ordinals its note documents do not shift.
- No hook logic changed. The hint prints what it printed before, where it now runs.

## Documentation Coverage (All Types Considered)
Set each item to one of: `updated`, `new`, `not-applicable`, `deferred`.

- features: not-applicable
- requirements: not-applicable
- tasks: not-applicable
- issues: new
- tests: updated
- workflows: not-applicable
- decisions: not-applicable
- risks: not-applicable
- changes: new
- snapshot: updated

## Follow-ups

- [ ] Record the mode in the ten repos that still have it unstaged or untracked, so a clone is not broken again.
