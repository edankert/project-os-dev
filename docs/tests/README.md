---
type: reference
id: TESTS-README
status: active
owner: team:docs
created: 2026-01-27
updated: 2026-01-27
tags: [tests]
---

# `docs/tests/` (system-wide tests)

Test notes are the canonical place to describe **how to verify behavior**, whether verification is automated or manual.

This directory is for **system-wide** or **cross-feature** tests.
Feature-scoped tests live under `docs/features/<feature-slug>/plan/tests/`.

## What goes here
- `TST-####-*.md` created from `../__templates__/test.md`.

## When to add a test note
- A change introduces or modifies behavior that needs verification.
- A workflow needs a repeatable validation checklist.
- You want durable coverage mapping (tests ↔ requirements/features/issues).

## Manual test feedback loop (LLM-friendly)
- An LLM can create a `[[test]]` note with a clear manual procedure and expected results.
- A human runs it and reports outcomes (pass/fail + observations).
- The LLM updates:
  - the test note (`status`, evidence, `last_run`)
  - `../../SNAPSHOT.yaml` (`items.tests.*.status` + links)
  - any gated items (task done / issue closed / requirement verified)
