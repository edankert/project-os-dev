---
type: "[[test]]"
id: TST-0016
aliases: ["TST-0016"]
title: "The sync fast-forwards only what nobody edited"
status: active
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-sync-stale.sh"
command: "bash ../project-os/tools/scripts/test-sync-stale.sh"
covers: ["[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"]
tasks: [TASK-0134]
issues: []
artifacts: []
evidence: []
adequacy: "Checked on 2026-09-18 by disabling each behaviour: with no stale fast-forward, with stale fast-forward applied to merge paths, with keep_local ignored, and with the keep_local block dropped on rewrite, each breaks exactly its own assertions. The unbroken script passes 12 of 12."
related: []
---

# The sync fast-forwards only what nobody edited

## Procedure
`bash tools/scripts/test-sync-stale.sh` in `~/Dev/repos/project-os`. The command runs across repos, the same convention as [[TST-0004]].
