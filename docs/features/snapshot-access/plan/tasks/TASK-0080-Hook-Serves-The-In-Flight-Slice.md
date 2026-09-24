---
type: "[[task]]"
id: TASK-0080
aliases: ["TASK-0080"]
title: "SessionStart emits the in-flight slice instead of a reminder to read the file"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-08-03
updated: 2026-09-24
source: ["ISS-0031"]
parent: "[[FEAT-0021]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ISS-0031]]", "[[ADR-0002]]", "[[ADR-0017]]"]
tests: ["[[TST-0007]]"]
---

# The hook serves orientation

## What changes

`snapshot-freshness.sh` currently ends:

```bash
echo "REMINDER: Read SNAPSHOT.yaml to understand current project state, focus, and active work before proceeding."
```

It emits the orientation content instead: `focus`, `metrics.counts`, and items whose status is in-flight (`doing`, `review`, `open`, `triage`), with fields trimmed to title / status / file / parent / phase.

Contract **HC-002** changes with it — its check logic today is *"Required context files exist and `SNAPSHOT.yaml` can be read"*, and the failure mode it guards (missing files) must survive the rewrite rather than being replaced by the new behaviour.

## The token budget is the design constraint

Measured 2026-08-03: 513 (project-os-cockpit), 778 (your-applications.com), 1,294 (your-sudoku), 1,663 (project-os-dev), 3,418 (your-health) — and **11,573 in your-trainer**, for 58 items where your-health fits 67 in 3,418.

The difference is title length, not item count. Decide the rule before implementing:

- truncate titles to a fixed width (simplest; loses the tail of long titles, which in `your-trainer` is where the substance often is), or
- cap total output and drop the least relevant items when over budget (needs a relevance order, which is a judgement the hook should probably not be making), or
- emit IDs and statuses only above a threshold, with titles below it.

**A hook that injects 11.5k tokens into every session has re-created the cost this line of work was checking for.** State the budget in the note, and make exceeding it a failure of this task rather than a discovered surprise.

## Constraints

- **Fail open.** A hook that errors must not block the session; the current one exits 0 unconditionally and that property is load-bearing.
- **Cheap.** It runs on every session start. Parsing a 386 KB YAML must stay fast enough to be unnoticeable, and must not require a Python import chain that may be absent.
- **Per-tool implementations move together** (ADR-0002): Claude Code's `snapshot-freshness.sh` and the Codex/generic `tools/agents/bootstrap.sh`. Regenerate adapters and run `generate-adapters.py --check`.
- **The startup instruction surface must stop telling agents to read the whole file** once the hook serves it, or the two disagree and ISS-0031 reappears with the roles reversed. That means `CLAUDE.md`, the user-level `CLAUDE.md`, `CONTEXT.md` and HC-002 — stated once per REQ-0018, referenced from the rest.

## Definition of Done
- [x] Hook emits focus, counts and in-flight items; the reminder string is gone — evidence: `snapshot-freshness.sh` prints `tools/scripts/snapshot-slice.py`'s output; the reminder is printed only when the slice prints nothing
- [x] HC-002's existing guard (required files present, snapshot readable) still fires, with its failure path unchanged — evidence: a missing `AGENTS.md`, `CONTEXT.md` or `docs/INDEX.md` is named in the output (TST-0007 assertion); an unreadable snapshot or a missing script prints the old reminder (TST-0007 assertion)
- [x] Stated token budget, met in all twelve repos including `your-trainer`, with the truncation rule recorded — evidence: the budget is 6,000 characters, about 1,500 tokens; measured 2026-09-24 over every repo under `~/Dev/repos` with a snapshot, largest your-trainer 5,928 and your-health 4,954, this repo 2,734, smallest yourtrainer-mcp 710; TST-0007 asserts 400 in-flight items stay under it
- [x] Codex/generic implementation updated in step; `generate-adapters.py --check` clean — evidence: Codex `dispatch.py` SessionStart and `tools/agents/bootstrap.sh` call the same script; `test_session_start_serves_the_slice`; "all 65 artifacts current"
- [x] Startup instructions reconciled so nothing still directs a whole-file read — evidence: `AGENTS.md` step 3, the template's `CLAUDE.md`, `ADAPTER.md`'s CLAUDE.md template, `HANDOFF.md` recovery step 1, HC-002, and this repo's `CLAUDE.md`. Not changed: the user-level `~/.claude/CLAUDE.md`, which is Edwin's (see Notes), and the other fleet repos' own `CLAUDE.md` files, which are project-owned and change when each repo next syncs and edits it
- [x] Verified by running a session in a large repo and a small one and confirming what actually lands in context — evidence: a headless Claude Code session started in this repo on 2026-09-24 (`claude -p`, plan mode) quoted its context's first lines as `SessionStart:startup hook success: project-os orientation from SNAPSHOT.yaml ...` followed by `focus.phase: PHASE-0003 (active) ...` and `focus.feature: FEAT-0039 (doing) ...`. The large and small repos (your-trainer 5,928 characters, yourtrainer-mcp 710) were checked by running the script, because they have not synced yet; a session there lands the same output once they do

## Decisions taken at implementation (2026-09-24)

- **Truncation rule: titles are left out, not cut.** Each item is ID, status and note path; the path carries the slug. Of the three options above this is none of them exactly: it is cheaper than truncating titles and needs no relevance order. Past the 6,000-character cap, items are counted, not listed.
- **Order:** focus items first, then tasks, features, issues and phases as the snapshot lists them. In your-trainer, 75 items are in flight and the tail of the issues list is counted rather than shown.
- **The focus note is cut to 400 characters.** It is the one free-text field in the slice, and in this repo it had grown to 1,900 characters.
- **Python, standard library only**, with the reminder as the fallback: every other hook that parses already uses `python3`, and a parser in awk for both YAML styles would be harder to keep correct.
- **The measurement FEAT-0021 said this could wait for (bench TASK-0008) was not run.** Edwin's instruction on 2026-09-24 was to implement.

## Notes

- The user-level `~/.claude/CLAUDE.md` also says "Read SNAPSHOT.yaml at session start". It covers every repo and is Edwin's file, so the change is proposed to him rather than made.
