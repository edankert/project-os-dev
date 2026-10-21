---
type: "[[task]]"
id: TASK-0208
aliases: ["TASK-0208"]
title: "test-stop-sync.sh's sample issue names who reported it, so the test passes after ISSUE-REPORTER became an error on 2026-10-19"
status: done
phase: ""
owner: user:edwin
created: 2026-10-21
updated: 2026-10-21
source: ["Found 2026-10-21 by the session fixing ISS-0107, running every tools/scripts/test-*.sh in the template"]
parent: "[[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed]]"
effort: "XS"
due: ""
depends: []
blocks: []
related: ["[[ISS-0107]]", "[[ADR-0047]]"]
tests: []
---

# The stop hook test's sample issue names its reporter

`tools/scripts/test-stop-sync.sh` fails in the template on a clean checkout of project-os `742fbe9`, with 2 of its 7 checks failing. Both stop hooks it drives, Claude Code's and Codex's, block the stop with `ERROR [ISSUE-REPORTER] ISS-0001 has no valid reported_by:`. The test expects them to let the stop through.

The test builds a copy of the template with one issue note, ISS-0001, created 2026-09-26 and with no `reported_by:`. ADR-0047's rule that an open issue names its reporter was a warning until 2026-10-19 and is an error since. The test passed on 2026-10-16 and started failing on that date, with no change to the code.

The fix is the test's sample note: it gains `reported_by: agent`. The rule is right; the sample was written before it applied.

## Definition of Done

- [x] ISS-0001 in `test-stop-sync.sh`'s sample repo carries `reported_by: agent`.
- [x] `test-stop-sync.sh` passes in the template, and every other `tools/scripts/test-*.sh` passes with it.

## Result

Fixed in project-os 8bac993. `test-stop-sync.sh` passes (7 assertions, 0 failures), and all 34 `tools/scripts/test-*.sh` in the template pass together with ISS-0107's fix in 2bb7976. Synced here.
