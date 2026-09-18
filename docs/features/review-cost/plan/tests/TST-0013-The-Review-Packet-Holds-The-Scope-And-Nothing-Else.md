---
type: "[[test]]"
id: TST-0013
aliases: ["TST-0013"]
title: "The review packet holds the feature's scope and nothing else"
status: active
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-review-packet.sh"
command: "bash ../project-os/tools/scripts/test-review-packet.sh"
covers: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
tasks: [TASK-0126, TASK-0129]
issues: []
artifacts: []
evidence: []
adequacy: "Checked by breaking the script on 2026-09-18: with notes no longer excluded, with commits matched on the message body instead of the subject, and with generated files no longer excluded, each break fails exactly the assertion meant for it; the unbroken script passes all 23."
related: []
---

# The review packet holds the feature's scope and nothing else

## Purpose
A throwaway git repo with known answers: the packet must carry the acceptance criteria word for word, the author's claims, tests linked by task and by `covers:`, the full-run result and the task's source diff. It must leave out notes, generated files and a commit that names the feature only in its body. A large diff goes to an indexed companion file. Round two carries round one's findings and the fixes only.

## Procedure
`bash tools/scripts/test-review-packet.sh` in `~/Dev/repos/project-os`. The command is cross-repo because every file this work changed lives in the template, the same convention as [[TST-0004]].
