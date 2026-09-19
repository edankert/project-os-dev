---
type: "[[test]]"
id: TST-0017
aliases: ["TST-0017"]
title: "The ledger and frontmatter checks hold their rules"
status: active
owner: user:edwin
created: 2026-09-18
updated: 2026-09-19
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
adequacy: "Checked by disabling each rule on 2026-09-18 (the reason rule, the real-date check, the moved-field level filter); a reviewer broke four more ledger rules on 2026-09-19 and each failed. After that review, two end-to-end cases run the whole validator: removing the call to validate_frontmatter_parses or to validate_ledgers fails them. 36 unit assertions and 2 end-to-end, all passing."
related: []
---

# The ledger and frontmatter checks hold their rules

## Procedure
`bash tools/scripts/test-ledger-checks.sh` in `~/Dev/repos/project-os`. The command runs across repos, the same convention as [[TST-0004]].
