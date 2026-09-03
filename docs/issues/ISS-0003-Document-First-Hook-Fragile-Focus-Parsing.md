---
type: "[[issue]]"
id: ISS-0003
aliases: ["ISS-0003"]
title: "Stale vendored hooks in project-os-dev: fragile focus parsing and wrong-repo gating already fixed upstream, plus an unfixed non-repo path case"
status: fixed
phase: "[[PHASE-0003]]"
severity: low
owner: user:edwin
created: 2026-07-21
updated: 2026-09-03
component: adapters-hooks
source: ["Prompting-guide review 2026-09-03, finding 2.4: https://claude.ai/code/artifact/4d82b4ff-73ed-42ab-97c0-9a2d0f98fcfc"]
related: ["[[FEAT-0002-Hook-Contracts]]", "[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]", "[[TST-0007]]"]
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

## Re-observed 2026-09-03

Point 3 blocked a write again today, this time to the Claude Code session scratchpad under `/private/tmp/claude-502/…/scratchpad/`, while the template was being reviewed against the Claude 5 prompting guides (finding 2.4 in the linked review). The workaround was to write the file through the shell. That is the bypass the pre-commit hook's own comment warns about: a gate that blocks legitimate work teaches the model to route around it.

Points 1 and 2 are fixed here as well now. The vendored hooks are byte-identical to the template's.

The hook was run directly against four paths, with this repo as `CLAUDE_PROJECT_DIR` and both `focus.task` and `focus.issue` empty. All four were denied. Only the last two should have been.

| Target | Should be | Was |
|---|---|---|
| `/private/tmp/claude-502/x/scratchpad/report.html` (no repo above it) | allowed | denied |
| `/Users/Edwin/Dev/repos/some-other-repo/src/main.py` (a repo with no `SNAPSHOT.yaml`) | allowed | denied |
| `src/main.py` (relative, resolves inside this repo) | denied | denied |
| `/Users/Edwin/Dev/repos/project-os-dev/src/main.py` (absolute, inside this repo) | denied | denied |

Repro, from the repo root:

```bash
printf '{"tool_input":{"file_path":"<path>"}}' | CLAUDE_PROJECT_DIR="$PWD" bash tools/adapters/claude-code/hooks/document-first-gate.sh
```

## Resolution

Fixed in the template by commit `7b6890f` on 2026-09-03 (CHG-20260903-Hooks-Serve-State there): when the walk finds no `SNAPSHOT.yaml`, the gate falls back to the session repo only for a relative path or a path under it, and allows anything else. HC-001 in HOOKS.md says so. The four-path table above is assertions 31 to 34 of [[TST-0007]] (22 to 25 before the review round added nine), passing; reverting the fix fails the first two. Points 1 and 2 were already fixed upstream. This repo picks the fix up at the next template sync.

## Remaining work (as planned before the fix; every item below landed in `7b6890f`)

The earlier proposal (exit 0 whenever the walk finds nothing) is too broad. The fallback has one legitimate job: a relative path such as `src/main.py`, where the walk cannot find anything and the session repo is the right guess. The fix keeps that case and drops the rest.

- Template, `tools/adapters/claude-code/hooks/document-first-gate.sh` line 43: when the walk finds no `SNAPSHOT.yaml`, fall back to `CLAUDE_PROJECT_DIR` only if the target path is relative or lies under `CLAUDE_PROJECT_DIR`. Otherwise allow. About four lines.
- `verification-gate.py` has the same fallback shape but only fires on `docs/` and `SNAPSHOT.yaml` paths, so it cannot misfire this way. No change needed.
- `tools/instructions/HOOKS.md`, HC-001: add one sentence saying a file outside every project-os repo is not gated.
- Verification: the four-path table above is the test. After the fix the first two rows are allowed and the last two stay denied. It is assertions 31 to 34 of [[TST-0007]] (22 to 25 before the harness grew), whose harness is written by [[TASK-0102]], so this fix and the two hook rewrites in [[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]] share one test run.
- project-os-dev picks the fix up through the normal template sync; the pending `tools/` sync mentioned in [[CHG-20260721-Requirement-Lifecycle-Closure]] has since landed for the hooks.
