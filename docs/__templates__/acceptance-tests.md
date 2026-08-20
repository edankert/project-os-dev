---
type: "[[reference]]"
# A placeholder, like every other template's id. It carried the REAL id
# `ACCEPTANCE-TESTS` until 2026-08-17, which made it squat on the record's
# own id: `[[ACCEPTANCE-TESTS]]` resolved to this template rather than to
# the suite, in every repo, for as long as both existed.
id: ACCEPTANCE-TESTS-TEMPLATE
title: "Acceptance test suite"
status: active
owner: unassigned
created: YYYY-MM-DD
updated: YYYY-MM-DD
scope: tests
related: []
---

> **This is the older single-document form of the acceptance suite.** The current form is **one note per check** — `check.md`, `type: [[check]]`, id `CHK-*`, at `docs/tests/acceptance/`. Both are read; a repo stores its suite one way or the other and never both. See `../../tools/instructions/TESTING.md`, "Where the acceptance suite lives".

# Acceptance Test Suite: <Project> v<version>

## Sections

A check is not filed into a section; its section is derived from `covers:` and `command:`.

- **Feature tests:** verify core user-facing capabilities; `covers:` names a `FEAT-*`; never removed, and re-checked when a change overlaps.
- **Regression tests:** guard previously-broken behavior; `covers:` names the `ISS-*` that created it; completed once and not re-opened by a later change.
- **Automated tests:** carry a `command:`; executed by CI; no verdict and no checkbox.

Full tier rules: `tools/instructions/TESTING.md`.

## Rules

1. New feature implemented → add a feature test under the feature's area heading, naming the `FEAT-*`.
2. Bug fixed → add a regression test naming the `ISS-*`.
3. Any code change invalidates overlapping feature tests (mark for re-check). A regression test is not re-opened.
4. A release is blocked while any manual check is unsettled (exceptions must be documented in the release note).
5. A check a machine executes carries a `command:`. Nothing removes a check.

---

# Feature tests

## 1.1 <Area> (<FEAT-IDs>)

- [ ] **<Test name>:** <Procedure and expected result.>

---

# Regression tests

## 2.1 <Bug area> (<ISS-ID>)

- [ ] **<Test name>:** <Procedure and expected result.>

---

# Automated tests

<!-- Temporary tests. Remove or promote after a verified release. -->

---

# Test Execution Notes

<!-- Prerequisites, environment setup, devices/accounts needed. -->

# Release History

<!-- One line per verified release: version, date, exceptions granted. -->
