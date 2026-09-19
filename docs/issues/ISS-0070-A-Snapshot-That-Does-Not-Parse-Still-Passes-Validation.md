---
type: "[[issue]]"
id: ISS-0070
aliases: ["ISS-0070"]
title: "A SNAPSHOT.yaml that does not parse still passes the validator and the snapshot check, in every repo"
status: "open"
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: "2026-09-19"
source: ["your-health ISS-0112, confirmed in the template during the issue review of 2026-09-18 (FEAT-0036, TASK-0139)"]
reported_by: review
question: ""
severity: high
component: "validator"
parent: ""
related: ["[[ISS-0053-A-Note-With-Unparseable-Frontmatter-Passes-Silently]]"]
tests: []
---

# A SNAPSHOT.yaml that does not parse still passes validation, in every repo

## Problem

Anyone can commit a `SNAPSHOT.yaml` that PyYAML cannot parse, and `validate-docs.sh` and `sync-snapshot.py --check` both report success. The gates that exist to catch a broken snapshot pass it.

`load_yaml` in `tools/scripts/validate-docs.py` catches every exception from `yaml.safe_load`, including a syntax error, and falls back to the lenient `parse_yaml_subset`. `sync-snapshot.py` reuses the same function. The fallback was meant for a machine without PyYAML, but it also swallows a real parse error. Every fleet repo carries the same code. Found as your-health [[your-health#ISS-0112]], confirmed here on 2026-09-18.

## Next Actions
- [ ] Fall back to `parse_yaml_subset` only on `ImportError`. On a parse error, report the parser's message and fail.
- [ ] A fixture test with a snapshot that does not parse, which must fail both the validator and `sync-snapshot --check`.
- [ ] Sync to the fleet, and close your-health ISS-0112.
