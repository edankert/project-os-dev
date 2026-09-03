---
type: skill
id: SKILL-SNAPSHOT-SYNC
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-09-03
tags: [skills, snapshot]
---

# Skill: Snapshot sync

## When to use
- After any work that changes statuses/relationships.
- When you suspect drift between `../../../SNAPSHOT.yaml` and the notes.

## First: most of this is automatic now

`tools/scripts/sync-snapshot.py` syncs the **derived** snapshot fields (`../../instructions/LIFECYCLE.md`, "Mandatory Automated Documentation"). It runs at pre-commit (writing, and re-staging the file) and in CI with `--check`.

```bash
python3 tools/scripts/sync-snapshot.py            # sync derived fields
python3 tools/scripts/sync-snapshot.py --check    # report drift, write nothing
python3 tools/scripts/sync-snapshot.py --report-unregistered
```

**Run the script before doing anything by hand.** Hand-reconciling a status is now redundant work that the next commit would redo.

## What the script deliberately does NOT do

It is a *surgical updater*, not a generator. A snapshot is duplication **plus curation**, and the curated half has no home in frontmatter:

- hand-written comments (`# Pruned: FEAT-0001..0006 (all done)`),
- which items the snapshot carries at all (retention is a judgement),
- editorial `goal:` / `note:` prose.

A whole-file generator was built first and rejected on evidence: shadow-run against 10 repos it would have added 180 items, dropped 153, and destroyed ~80 comment lines. So membership, retention and prose stay yours.

## Checklist — what is left for a human or agent

1. Run the script. If it reports drift it has already fixed it; read what changed.
2. `--report-unregistered` lists notes with no snapshot entry. Decide, per item, whether it belongs in active context — **this is the curation call the script refuses to make**. Add or prune deliberately.
3. Reconcile anything the script cannot: notes that contradict *each other* (a task claiming a parent that does not list it back, two notes claiming one ID). That is semantic consistency — see `../docs-audit/SKILL.md`.
4. Update `focus` if the active work changed. `focus` is intent, not state, and stays hand-authored.
5. Run `bash tools/scripts/validate-docs.sh` and fix what it reports.

## Gates that still apply

- The gate on each terminal status is stated once in `../../instructions/STATUSES.md`, "The contract at a glance"; a sync never moves an item past a gate it does not meet.
