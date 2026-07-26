---
type: "[[issue]]"
id: ISS-0003
aliases: ["ISS-0003"]
title: "Stale vendored hooks in project-os-dev: fragile focus parsing and wrong-repo gating already fixed upstream, plus an unfixed non-repo path case"
status: open
phase: "[[PHASE-999-Parking-Lot]]"
severity: low
owner: user:edwin
created: 2026-07-21
updated: 2026-07-22
component: adapters-hooks
source: []
related: []
tasks: []
---

# Stale vendored hooks (and one real remaining gap)

## Correction (2026-07-22)

As originally filed this issue was **wrong about where the defect lives**. It described `tools/adapters/claude-code/hooks/document-first-gate.sh` as broken "template and downstream copies". In fact the template fixed points 1 and 2 on 2026-07-18 — template commit `a296fe1` "hooks: gate against the target file's repo, not the session repo" with `docs/changes/CHG-20260718-Cross-Repo-Hook-Root.md`. The symptoms were observed against **project-os-dev's stale vendored copy** (55 lines) rather than the template's current one (76 lines).

The filing error is instructive: it is the same root cause as the validator gap noted in [[CHG-20260721-Requirement-Lifecycle-Closure]] — this repo runs vendored `tools/` that is behind the template, so defects appear to exist that were fixed upstream.

## Status of each original point

1. **Key-order dependence** — **fixed upstream.** The template now extracts the whole `focus:` block (`sed -n '/^focus:/,/^[^[:space:]]/p'`) and greps for the key within it, so key order is irrelevant. The workaround applied here (reordering `focus:` so `task:` came first) is no longer needed once the sync lands. project-os-dev still runs the `grep -A1`/`grep -A3` version.
2. **Wrong-repo resolution on cross-repo edits** — **fixed upstream.** The template walks up from the target file's directory to find the governing `SNAPSHOT.yaml`, falling back to `CLAUDE_PROJECT_DIR` only when none is found. project-os-dev still reads the session repo's snapshot.
3. **Over-broad path gating for non-repo paths** — **still open, in the template too.** When the target file is outside any project-os repo (e.g. Claude's memory directory under `~/.claude/projects/...`), the upward walk finds no `SNAPSHOT.yaml` and the hook falls back to `CLAUDE_PROJECT_DIR`, so the edit is still gated on the *session* repo's focus. Observed twice in this session: writing a memory file was denied while `focus` was empty. A path that resolves to no project-os repo should be allowed unconditionally rather than falling back.

## Remaining work

- Template: in `document-first-gate.sh`, when the upward walk finds no `SNAPSHOT.yaml`, exit 0 instead of falling back to `CLAUDE_PROJECT_DIR`. The fallback is what makes non-repo paths gateable.
- project-os-dev: pick up the 2026-07-18 hook fixes as part of the pending `tools/` sync (see [[CHG-20260721-Requirement-Lifecycle-Closure]] "Known follow-up"), which also brings the REQ-*/DEFER-* validator checks.
