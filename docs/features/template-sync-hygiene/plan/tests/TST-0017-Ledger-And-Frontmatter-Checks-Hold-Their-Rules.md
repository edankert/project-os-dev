---
type: "[[test]]"
id: TST-0017
aliases: ["TST-0017"]
title: "The ledger and frontmatter checks hold their rules"
status: active
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-ledger-checks.sh"
command: "bash ../project-os/tools/scripts/test-ledger-checks.sh"
covers: ["[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"]
tasks: [TASK-0136]
issues: []
artifacts: []
evidence: []
adequacy: "Checked on 2026-09-18 by disabling each rule: the reason rule, the real-date check, and the moved-field check's level filter (in the right function; an earlier break hit a same-text line elsewhere) each break their assertion. The unbroken validator passes 16 of 16."
related: []
---

# The ledger and frontmatter checks hold their rules

## Procedure
`bash tools/scripts/test-ledger-checks.sh` in `~/Dev/repos/project-os`. The command runs across repos, the same convention as [[TST-0004]].
