---
type: "[[test]]"
id: TST-0025
aliases: ["TST-0025"]
title: "A misspelt link field, an incomplete index, an undocumented field and a dead citation are each reported"
status: active
owner: user:edwin
created: 2026-09-25
updated: 2026-09-25
source: ["[[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks]]", "[[ISS-0053-A-Note-With-Unparseable-Frontmatter-Passes-Silently]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-drift-checks.sh"
command: "bash ../project-os/tools/scripts/test-drift-checks.sh"
covers: ["[[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks]]", "[[ISS-0053-A-Note-With-Unparseable-Frontmatter-Passes-Silently]]"]
tasks: ["[[TASK-0163]]", "[[TASK-0164]]", "[[TASK-0165]]", "[[TASK-0166]]"]
issues: ["[[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks]]", "[[ISS-0053-A-Note-With-Unparseable-Frontmatter-Passes-Silently]]"]
artifacts: []
evidence: []
adequacy: "2026-09-25, 10 assertions. Seven mutations in a full copy of the template: D1 typo check removed, 2 failures; D2 plural not excused, 1; D3 index check removed, 3; D4 field derivation misses field tables (fixes:), 1; D5 cited paths unchecked, 2; D6 cited sections unchecked, 2; D7 placeholders not skipped, 1 (it survived until a placeholder outside docs/ was added to the fixture). Pristine 10 of 10."
related: ["[[TST-0001]]", "[[TST-0022]]"]
---

# A misspelt link field, an incomplete index, an undocumented field and a dead citation are each reported

## Purpose

Four validator checks replace drift-sweep findings: FRONTMATTER-TYPO (ISS-0053), INDEX-COVERAGE, FIELD-UNDOCUMENTED and CITATION (ISS-0052). The harness copies the template, checks the copy is clean, then puts one defect in at a time.

## Procedure

`bash tools/scripts/test-drift-checks.sh` in `~/Dev/repos/project-os`.

1. A clean template trips none of the four.
2. `elated:` is an error naming `related:`; a singular `feature:` and a project field `review_note:` are not reported.
3. `docs/INDEX.md` without OBSIDIAN.md, and a skill no README lists, are reported, as warnings until 2026-12-24.
4. SCHEMAS.md without `fixes:` makes FIELD-UNDOCUMENTED name it: the field is read only through a table, which the syntax-tree derivation must follow.
5. A cited path and a cited section that resolve nowhere are reported; a `YYYY` placeholder, a `docs/` path, a context-relative `plan/PLAN.md` and a real section are not.

## Expected results

- Exit 0: 10 of 10, 2026-09-25.
