---
type: "[[issue]]"
id: ISS-0055
title: "The HC-008 delegation hint has no executable bit in any of the twelve repos, so every prompt submission prints a Permission denied warning instead of the hint"
status: fixed
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-04
updated: 2026-09-04
source: ["user:edwin"]
severity: medium
component: adapters-hooks
parent: ""
related: ["[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]", "[[TST-0007-The-Hooks-Emit-What-The-Contracts-Say]]", "[[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]]"]
tests: ["[[TST-0007-The-Hooks-Emit-What-The-Contracts-Say]]"]
---

# The delegation hint is not executable in any repo

## Problem

Every prompt Edwin submits in any project-os repo prints a hook error and no hint. `tools/adapters/claude-code/hooks/model-routing-hint.sh` is mode `644` on disk in all twelve repos under `~/Dev/repos/`, and `.claude/settings.json` runs it by bare path, so the shell refuses to execute it. The HC-008 contract says the hint informs and never blocks, and that holds — the prompt still goes through — but the focus line it exists to emit is lost on every turn, and a warning takes its place.

The executable bit does not travel. The template repo records all eight hook scripts as `100644` in git and sets `core.fileMode = false`, so a `chmod +x` there is invisible to git and never reaches a downstream repo. `sync-project-os.py` copies with `shutil.copy2`, which carries the source file's mode, and the source file's mode is `644`. The seven older hooks are executable on disk only because someone once ran the `chmod +x tools/adapters/claude-code/hooks/*.sh` line that `ADAPTER.md:123` gives as an install step. That line runs once at install; `model-routing-hint.sh` arrived later, by sync, and nobody re-ran it.

> [!quote] As reported — 2026-09-04 (user:edwin)
> I am getting this error now:
> UserPromptSubmit hook error
> Failed with non-blocking status code: /bin/sh: /Users/Edwin/Dev/repos/your-trainer/tools/adapters/claude-code/hooks/model-routing-hint.sh: Permission denied
> Can you check why this is and if we should have this and how to fix?

## Repro

```bash
cd ~/Dev/repos/your-trainer
ls -l tools/adapters/claude-code/hooks/model-routing-hint.sh   # -rw-r--r--
printf '{"prompt":"x"}' | ./tools/adapters/claude-code/hooks/model-routing-hint.sh
# /bin/sh: .../model-routing-hint.sh: Permission denied
```

Submitting any prompt in that repo reproduces it through the harness, because `.claude/settings.json` registers the hook as `"$CLAUDE_PROJECT_DIR/tools/adapters/claude-code/hooks/model-routing-hint.sh"` with no interpreter in front of it.

The fleet-wide shape:

```bash
cd ~/Dev/repos && for d in */; do f="$d/tools/adapters/claude-code/hooks/model-routing-hint.sh"; [ -f "$f" ] && { [ -x "$f" ] && echo "EXEC     ${d%/}" || echo "NOT-EXEC ${d%/}"; }; done
```

## Expected

The hook runs and prints its one advisory line, in every repo, straight after a sync or a fresh clone, with no manual `chmod`.

## Actual

Before the fix, twelve of twelve repos printed `Permission denied` on every prompt submission. The bit is missing on disk in all twelve and missing in git in all twelve.

Six of those repos — the template `project-os`, plus `edankert.com`, `your-applications.com`, `your-health`, `your-sudoku` and `your-trainer` — record **all eight** hooks as `100644`; a seventh, `obsidian-supernote-sync`, records five of the eight that way. Those repos are one clean `git clone` away from every hook failing, not just this one. They work today only because the on-disk bits were set by hand at install time and `core.fileMode = false` hides the divergence from git.

## Evidence

- `tools/adapters/claude-code/hooks/model-routing-hint.sh` — `100644` in this repo's index; the other seven hooks are `100755`.
- `/Users/Edwin/Dev/repos/project-os` — all eight hooks `100644` in the index, `core.fileMode = false`.
- `tools/scripts/sync-project-os.py:194,206,217` — `shutil.copy2`, which preserves the source mode; and `:199`, `if current == new: uptodate; return`, which compares bytes only. So a sync carries the mode of a script whose content changed, and never carries a mode-only change. Fixing the modes upstream therefore does not reach a downstream repo on its own.
- `tools/sync/MANIFEST.yaml:17` — `"tools/adapters/": template`, so the upstream copy is authoritative and a sync overwrites downstream.
- `tools/adapters/claude-code/ADAPTER.md:123` — `chmod +x tools/adapters/claude-code/hooks/*.sh`, the one-time install step.
- `tools/scripts/test-hooks.sh:58-60` — every hook is invoked as `bash "$HOOKS/<name>"`, which succeeds whatever the mode is. This is why thirty-seven green assertions never saw the defect.
- `tools/scripts/generate-adapters.py:228-243` — `install_hooks()` writes `.claude/settings.json` and never touches the mode of the scripts it registers.

Sibling search: no sibling found (searched `docs/issues/` for chmod, executable, permission denied, exec bit, file mode, 100644 — the "executable" hits are all `TST-*` notes carrying a `command:`, a different sense of the word).

## Next Actions

- [x] Record all eight hook scripts as `100755` in the template's git index, so a clone carries the bit (template `e1c46bf`). This alone does not reach the existing repos: their scripts are byte-identical, so the sync skips them.
- [x] Make `generate-adapters.py --install-hooks` set the executable bit on every file in `hooks/`, including on the path that leaves an existing `hooks` key alone. This is the repair path for the existing repos, and `SYNCING.md` step 5 already calls for it after every sync.
- [x] Assert in `test-hooks.sh` that every file in `hooks/` is executable: 37 assertions to 45, and verified to fail when the bit is removed.
- [x] Drop the manual `chmod` line from `ADAPTER.md`, and say there what to do in a repo with `core.fileMode = false`.
- [x] `chmod +x` on disk across the ten repos still unfixed, to unblock them now.
- [x] Record the mode in each of those repos' indexes. Done 2026-09-04, one commit per repo, each containing nothing but mode changes: `articles` 8ce40f2, `edankert.com` 3a38552, `obsidian-supernote-sync` 80226d3, `project-os-bench` e1e4711, `project-os-cockpit` f45db59, `your-applications.com` 9479b78, `your-health` e99eb27, `your-sudoku` 61922ee, `your-trainer` e847d253, `yourtrainer-mcp` 4f07369. All 96 hook entries across the twelve repos are now `100755`. Verified by cloning `your-trainer` fresh: all eight arrive executable and the hint runs.
