---
type: "[[test]]"
id: TST-0042
aliases: ["TST-0042"]
title: "An Expect line marked [android] or [ios] prints only on that platform, a tag pairs per platform, and a quoted procedure line is a warning"
status: active
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0188-Expect-Lines-Can-Be-Marked-Per-Platform]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-release-test.sh"
command: "bash ../project-os/tools/scripts/test-release-test.sh"
covers: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
tasks: ["[[TASK-0188]]"]
requirements: ["[[REQ-0034-A-Check-Writes-Its-Expected-Result-Once-Per-Platform]]"]
issues: []
artifacts: []
evidence: []
adequacy: "2026-09-27, the block headed 'Expect lines marked for one platform' in test-release-test.sh (25 assertions; the harness has 204). Twelve mutations in a scratch copy of the template, each failing the harness: the platform filter always true, 5 failures; pairing counted over every platform's lines, 14; per-check rows printing the whole Expect section, 3; the unknown-platform refusal not added to --check, 1; the quoted-line warning removed, 4; QUOTED_EXPECTATIONS_REFUSED ignored, 1; the --quiet count off, 1; release-test-tags.py comparing only the last platform, 1; ignoring the step's own platforms, 1; not comparing per platform at all, 2; --all ignored, 2; --all leaving tags on an action line, 2. One more, comparing only the first platform, survived until the fixture gained a step that runs on one platform alone. Pristine 204 of 204."
related: ["[[TST-0033]]", "[[TST-0009]]"]
---

# An Expect line marked for a platform prints only there

## Purpose

REQ-0034 lets a check write one Expect line per platform where the platforms differ, so the Android page stops printing iOS wording. This test shows the page prints only the current platform's lines, that a tag's `.N` counts the lines that apply on that platform, that a platform name with no ledger is refused, and that a procedure line quoting an expectation is reported as a warning.

## Procedure

`bash ../project-os/tools/scripts/test-release-test.sh`. The fixture gives the procedure fixture a second ledger, `bench`, and marks one of TST-0401's four Expect lines `[testbed]` and another `[bench]`, so each platform has three lines for three steps.

## Expected results

- On testbed the page prints the `[testbed]` line without its brackets, never the `[bench]` line, and tag `.3` prints only the third applicable line. On bench the reverse holds.
- A per-check row prints only the lines for its platform.
- `--check` refuses `[andriod]`, naming TST-0405 and the line.
- `--check` warns about each quoted line and still exits 0; `--quiet` prints one line with the count; with `QUOTED_EXPECTATIONS_REFUSED` on, the same lines are problems.
- `release-test-tags.py --all --apply` leaves no quoted line and no tagged action line, and `--check` then passes on both platforms. Without `--all` it keeps a quote that one platform would print differently.
