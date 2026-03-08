---
type: reference
id: WORKFLOWS-README
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-01-29
tags: [workflows]
---

# `docs/workflows/`

> REPLACE ME (template): Update the workflow list and the referenced entrypoints to match your project.

Workflow notes describe the **canonical entrypoints** for common activities in this repo (what to run, what inputs are needed, what artifacts/logs to expect).

## What goes here
- `WF-####-*.md` notes, one per workflow, kept short and command-oriented.

## When to add a workflow note
- A developer needs a repeatable “front door” to accomplish something (build, test, run, deploy, troubleshoot).
- There is more than one valid path and you want to standardize on the recommended one.

## How workflows relate to other docs
- `../issues/`: file an issue when a workflow is broken or unclear.
- `../changes/`: add a change note when a workflow materially changes (scripts, paths, required env vars).

## Index
- `[[WF-0001-Existing-Project-Init]]` (existing project derive/import)
- `[[WF-0002-Template-Sync]]` (sync template updates into a repo)
- `[[WF-0003-Recovery-Resume]]` (resume work after failure / multi-agent)
- REPLACE ME: add links to your `WF-####-*.md` notes as you create them.
