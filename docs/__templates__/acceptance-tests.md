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

> **This is the older single-document form of the acceptance suite.** The current form is **one note per check** — `test.md` with `level: acceptance`, id `TST-*`, stored per `tools/instructions/LIFECYCLE.md` "Test storage". Both are read; a repo stores its suite one way or the other and never both. See `../../tools/instructions/TESTING.md`, "Where the acceptance suite lives".

# Acceptance Test Suite: <Project> v<version>

## Sections and rules

The three sections, when a check is created, invalidated or retired, and release gating are stated once in `tools/instructions/TESTING.md`. A check is not filed into a section; its section is derived from `covers:` and `command:`.

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

<!-- Checks carrying a `command:`; see TESTING.md "Automated tests". -->

---

# Test Execution Notes

<!-- Prerequisites, environment setup, devices/accounts needed. -->

# Release History

<!-- One line per verified release: version, date, exceptions granted. -->
