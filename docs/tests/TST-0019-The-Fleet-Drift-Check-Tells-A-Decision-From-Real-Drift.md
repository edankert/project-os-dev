---
type: "[[test]]"
id: TST-0019
aliases: ["TST-0019"]
title: "The fleet drift check finds a stale or missing template-owned file, and does not cry wolf over a recorded decision"
status: active
owner: user:edwin
created: 2026-09-20
updated: 2026-09-20
source: ["[[TASK-0146-The-Four-Findings-Round-One-Left]]", "The FEAT-0034 round-two review, 2026-09-20"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-fleet-file-drift.sh"
command: "bash ../project-os/tools/scripts/test-fleet-file-drift.sh"
covers: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
tasks: [TASK-0146]
issues: []
artifacts: []
evidence: []
adequacy: "Checked by breaking it, 2026-09-20. Disabling the content comparison fails 4 assertions; ignoring keep_local fails 5, including 'only the real one is called stale'; counting a missing keep_local file as kept fails the two added after round two. 20 assertions passing."
related: ["[[TST-0018]]"]
---

# The fleet drift check tells a decision from real drift

## Purpose

`fleet-file-drift.py` compares every template-owned file in every repo against the template, taking ownership from `tools/sync/MANIFEST.yaml`. It must find a file that is stale or missing, stay quiet about one a repo keeps different on purpose under `keep_local:`, and say so when such an exception has nothing left to protect.

## Why it has a note

**It had none until the round-two review of 2026-09-20 pointed that out**, and the observation was sharp: a checker written because nothing noticed a stale file across eleven repos had itself been left where nothing would run it. No `TST-*` note carried its command, so `run-tests.py` never called it and CI never called it. The failure it exists to catch would have gone unnoticed again, for the same reason.

That is [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]]'s shape exactly, reappearing in new code on the same day the rest of it was being closed.

## Procedure

`bash tools/scripts/test-fleet-file-drift.sh` in `~/Dev/repos/project-os`. Cross-repo because the script and its fixtures live in the template, the same convention as [[TST-0015]] and [[TST-0018]].
