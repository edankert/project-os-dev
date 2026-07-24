---
type: "[[reference]]"
id: ACCEPTANCE-TESTS
title: "Acceptance test suite"
status: active
owner: unassigned
created: YYYY-MM-DD
updated: YYYY-MM-DD
scope: tests
related: []
---

# Acceptance Test Suite: <Project> v<version>

## Test Tiers

- **Tier 1 — Feature Tests (permanent):** verify core user-facing capabilities; one or more per feature; never removed.
- **Tier 2 — Regression Tests (permanent):** guard previously-broken behavior; each references the `ISS-*` that created it.
- **Tier 3 — Verification Tests (temporary):** one-time checks for a specific build or fix; promoted to Tier 2 or removed after a verified release.

Full tier rules: `tools/instructions/TESTING.md`.

## Rules

1. New feature implemented → add Tier 1 test(s) under the feature's area heading.
2. Bug fixed → add a Tier 2 test referencing the `ISS-*`.
3. Any code change unchecks overlapping Tier 1/Tier 2 tests (mark for re-run).
4. A release is blocked while any Tier 1/Tier 2 test is unchecked (exceptions must be documented in the release note).
5. Tier 3 tests are removed or promoted after each verified release.

---

# Tier 1 — Feature Tests

## 1.1 <Area> (<FEAT-IDs>)

- [ ] **<Test name>:** <Procedure and expected result.>

---

# Tier 2 — Regression Tests

## 2.1 <Bug area> (<ISS-ID>)

- [ ] **<Test name>:** <Procedure and expected result.>

---

# Tier 3 — Verification Tests (current build)

<!-- Temporary tests. Remove or promote after a verified release. -->

---

# Test Execution Notes

<!-- Prerequisites, environment setup, devices/accounts needed. -->

# Release History

<!-- One line per verified release: version, date, exceptions granted. -->
