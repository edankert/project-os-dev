---
type: reference
id: TESTS-README
aliases: ["TESTS-README"]
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

## Where the walk order lives

`docs/tests/acceptance/WALK.md` is the one file that says in what order this project's acceptance checks are walked. It lists sittings — groups of checks sharing one setup state — and each sitting claims its checks **by surface**. `python3 tools/scripts/walk-sheet.py --release REL-#### --platform <platform>` reads it and prints the sheet for a release. Start from `../__templates__/walk.md`; the rules are stated once in `../../tools/instructions/TESTING.md`, "The walk".

## When to add a test note
- A change introduces or modifies behavior that needs verification.
- A workflow needs a repeatable validation checklist.
- You want durable coverage mapping (tests ↔ requirements/features/issues).

## Manual test feedback loop (LLM-friendly)
- An LLM can create a `[[test]]` note with a clear manual procedure and expected results.
- A human runs it and reports outcomes (pass/fail + observations).
- The LLM updates:
  - the test note (`status` and evidence for a manual test; a test with a `command:` records no verdict, ADR-0025)
  - `../../SNAPSHOT.yaml` (`items.tests.*.status` + links)
  - any gated items, at the terminal statuses `../../tools/instructions/STATUSES.md` allows
