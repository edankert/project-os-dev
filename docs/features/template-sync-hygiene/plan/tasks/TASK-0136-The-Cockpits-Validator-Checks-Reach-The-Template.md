---
type: "[[task]]"
id: TASK-0136
aliases: ["TASK-0136"]
title: "The cockpit's validator checks reach the template"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-19
source: ["[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"]
parent: "[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"
effort: "Large"
due: ""
depends: [TASK-0135]
blocks: []
related: []
tests: [TST-0017]
---

# The cockpit's validator checks reach the template

## Definition of Done
- [x] The template's `validate-docs.py` gains the cockpit's four checks: frontmatter that does not parse ([[ISS-0053-A-Note-With-Unparseable-Frontmatter-Passes-Silently|ISS-0053]]), ledgers, moved verdict fields and vouched ledgers. Each keeps the test that guards it in the cockpit, or gets one.
- [x] The whole fleet validates with them.
- [x] project-os-cockpit takes the template's validator.

## Outcome, 2026-09-18
project-os `d2f78bc`, test-ledger-checks.sh (16 assertions). The template's validator gained the cockpit's `validate_ledgers`, `validate_moved_verdict_fields`, `validate_vouched_ledgers` and `validate_frontmatter_parses` ([[ISS-0053-A-Note-With-Unparseable-Frontmatter-Passes-Silently|ISS-0053]] is covered by the last). The fleet had debt against three codes: LEDGER-FIELD (your-trainer 649), LEDGER-SEALED (your-trainer 1) and NOTE-FRONTMATTER (18 across five repos). Those three warn until 2026-12-17. **The cockpit did not take the template's validator:** its own carries more rules, and 41 of its tests failed on the template's. That work is filed as [[ISS-0068-The-Cockpits-Validator-Carries-Rules-The-Template-Lacks|ISS-0068]].

## Later, 2026-09-18 and 2026-09-19

The Outcome above was true when written. The cockpit took the template's validator later the same day, through [[ISS-0068-The-Cockpits-Validator-Carries-Rules-The-Template-Lacks|ISS-0068]] (project-os `4b5fa83`, cockpit `b546625`), and today it is byte-identical to the template's. The ticked box is right; the Outcome sentence records the state before ISS-0068. Noted after the FEAT-0037 review of 2026-09-19.
