---
type: "[[test]]"
id: TST-0018
aliases: ["TST-0018"]
title: "A scaffold offers every field the validator gates on, and declares no key twice"
status: active
owner: user:edwin
created: 2026-09-20
updated: 2026-09-20
source: ["[[ISS-0074-The-Feature-Template-Lacks-The-Acceptance-And-Design-Fields-The-Cockpit-Uses]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-note-templates.sh"
command: "bash ../project-os/tools/scripts/test-note-templates.sh"
covers: ["[[ISS-0074-The-Feature-Template-Lacks-The-Acceptance-And-Design-Fields-The-Cockpit-Uses]]"]
tasks: [TASK-0147]
issues: []
artifacts: []
evidence: []
adequacy: "Checked by breaking it, 2026-09-20, both ways. Restoring the previous feature.md fails 4 assertions (the two gate fields and the two comments that explain them). Putting project-os-cockpit's copy in its place fails the duplicate-key assertion, which is the real defect that copy carried: reviewed_by, review_date, review_verdict and review_round each declared twice. 9 assertions passing."
related: ["[[ISS-0076-The-Codex-Adapter-Note-Says-Two-Different-Things-In-Two-Repos]]"]
---

# A scaffold offers every field the validator gates on, and declares no key twice

## Purpose

A scaffold under `docs/__templates__/` is where a field is discovered. The validator warned on a feature's `acceptance:` and `design:` for months while `feature.md` offered neither, so the gates were unreachable for anyone who scaffolded a feature the normal way.

The test asserts three things. Every field the feature gates read exists in the scaffold. Every gate the scaffold advertises is one the validator actually runs, so the two cannot drift apart in the other direction. And no scaffold declares a frontmatter key twice — a silent defect, because YAML keeps one value and loses the other edit.

## Procedure

`bash tools/scripts/test-note-templates.sh` in `~/Dev/repos/project-os`. Cross-repo because every file it reads lives in the template, the same convention as [[TST-0015]].
