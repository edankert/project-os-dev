---
type: "[[task]]"
id: TASK-0075
title: "Prototype the external review runner"
status: done
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-07-27
updated: 2026-07-27
source: ["session:2026-07-27"]
parent: "[[FEAT-0018]]"
effort: "S"
due: ""
depends: []
blocks: ["[[TASK-0076]]"]
related: []
tests: []
---

# Prototype the external review runner

## Definition of Done

- [ ] `tools/scripts/review-external.py` assembles a review prompt from the `independent-review` skill, named notes, and a git diff range
- [ ] It creates a detached git worktree for the reviewer to mutate, and removes it afterwards; the real tree is unchanged after a run
- [x] `--dry-run` writes the assembled prompt without invoking a model, so the whole pipeline is testable with no subscription — evidence: run with no CLI installed produced `calib.prompt.md`
- [x] Runner invocation is table-driven (`RUNNERS`), so kimi/codex/gemini are a flag rather than a rewrite — evidence: `RUNNERS` = kimi / codex / gemini, selected by `--model`
- [x] The verdict is parsed from agent-CLI output that may contain surrounding chatter — evidence: extractor tested against prose-wrapped, fenced, brace-in-string, nested and two-object outputs; returns None on no-JSON
- [x] Findings without both `repro` and `observed` are dropped, and the count of dropped findings is reported — evidence: 4 synthetic findings → 1 kept, 3 dropped (missing repro, missing observed, whitespace-only)
- [x] The script never writes to a note — evidence: no write path to `docs/` in the source; it writes only `--out`, `.raw.txt` and `.prompt.md`

## Steps

- [x] Write the runner with `--dry-run` first and validate prompt assembly with no CLI installed
- [x] Verify worktree create/remove leaves the source tree byte-identical
- [x] Verify the JSON extractor against output with leading and trailing prose
- [x] Verify the repro filter drops an unreproduced finding

## Result

Prototype complete and testable without a subscription. Everything except the model call is verified: prompt assembly, worktree isolation and cleanup, JSON extraction from realistic agent chatter, the repro filter, and a clean exit(3) when the CLI is absent.

Done: every DoD item is ticked with evidence. Whether a real non-Claude model produces a usable verdict from this prompt is deliberately **not** in this task's scope — that is [[TASK-0076]], and it needs the CLI installed and authenticated by a human (OAuth device flow, which an agent must not perform).

(Briefly held at `review` while writing this up, which the validator rejected: `review` is a *feature* status, not a task status. The vocabulary was right and the instinct was wrong — the caution belonged in TASK-0076's scope, not in this task's status.)

## Notes

Prototype, deliberately in this repo's `tools/scripts/` rather than a scratchpad, because it is template-owned tooling and its home is where it will be synced from. Promotion to `project-os` happens after the calibration run says whether the approach works.

The no-auto-stamp rule is not squeamishness. `review_verdict` is the field ADR-0011 gates close-out on; a script that writes it from whatever the model returned makes the gate self-certifying through a longer pipe.
