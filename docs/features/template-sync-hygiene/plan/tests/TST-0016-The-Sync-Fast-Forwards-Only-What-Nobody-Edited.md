---
type: "[[test]]"
id: TST-0016
aliases: ["TST-0016"]
title: "The sync fast-forwards only what nobody edited"
status: active
owner: user:edwin
created: 2026-09-18
updated: 2026-09-19
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
adequacy: "Checked by disabling each behaviour. 2026-09-18: no stale fast-forward, stale fast-forward on merge paths, keep_local ignored. 2026-09-19: the merge-path restriction restored (1 failure), build-output exclusion removed (2), the old GONE rule restored (3). The project-workflow assertion can now fail, because the fixture template ships its own own-ci.yml. 24 assertions, all passing."
related: []
---

# The sync fast-forwards only what nobody edited

## Procedure
`bash tools/scripts/test-sync-stale.sh` in `~/Dev/repos/project-os`. The command runs across repos, the same convention as [[TST-0004]].
