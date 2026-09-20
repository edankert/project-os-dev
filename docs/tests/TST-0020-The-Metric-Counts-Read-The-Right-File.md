---
type: "[[test]]"
id: TST-0020
aliases: ["TST-0020"]
title: "A metric count reads the file that claims the id, counts an executable test as executable, and never counts an acceptance check"
status: active
owner: user:edwin
created: 2026-09-20
updated: 2026-09-20
source: ["[[ISS-0073-A-Validator-Test-Can-Run-Against-Code-That-Is-Not-The-Source]]", "[[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-metric-counts.sh"
command: "bash ../project-os/tools/scripts/test-metric-counts.sh"
covers: ["[[ISS-0073-A-Validator-Test-Can-Run-Against-Code-That-Is-Not-The-Source]]"]
tasks: [TASK-0149]
issues: ["[[ISS-0020]]", "[[ISS-0021]]", "[[ISS-0035]]"]
artifacts: []
evidence: []
adequacy: "The harness was written for ISS-0020, ISS-0021 and ISS-0035 and already fails when the count reads the index's impostor instead of the file that claims the id. 6 assertions passing 2026-09-20 on a cleared bytecode cache. Its adequacy was never in doubt; what was missing was anything running it."
related: ["[[TST-0018]]", "[[TST-0019]]"]
---

# A metric count reads the file that claims the id

## Purpose

`compute_metric_counts` decides what the snapshot's `metrics.counts` say. The harness runs it over made-up notes and checks that a test carrying a `command:` counts as executable, one without counts as manual, an acceptance check is in neither, a waiver is counted once per item, and the status comes from the file that actually claims the id rather than from a filename that merely contains it.

## Why it has a note

**It had none until 2026-09-20, and that is how it came to report a failure nobody could explain.** A round-two reviewer ran it by hand and got two failures; the same assertions passed on the source. The harness had executed a 14 September compile of `validate-docs.py` from a bytecode cache Apple's Python keeps outside the repository, so clearing `tools/scripts/__pycache__` changed nothing ([[ISS-0073-A-Validator-Test-Can-Run-Against-Code-That-Is-Not-The-Source|ISS-0073]]).

Because no `TST-*` note carried its command, `run-tests.py` never ran it and the recorded "17 passing, 0 failing" never covered it in either direction. That is [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]]'s shape.

## Procedure

`bash tools/scripts/test-metric-counts.sh` in `~/Dev/repos/project-os`. Cross-repo, like [[TST-0015]], [[TST-0018]] and [[TST-0019]].
