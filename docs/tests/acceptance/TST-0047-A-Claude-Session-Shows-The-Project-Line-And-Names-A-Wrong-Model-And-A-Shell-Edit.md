---
type: "[[test]]"
id: TST-0047
aliases: ["TST-0047"]
title: "A Claude session in a synced repo shows the project line above the prompt, names a wrong model, and treats a shell edit as a write at close-out"
status: active
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["[[FEAT-0041-Project-Os-Mod]]"]
scope: feature
level: acceptance
entrypoint: "A terminal in a project-os repo that has taken the template sync, running claude"
command: ""
last_verified: ""
covers: ["[[FEAT-0041-Project-Os-Mod]]"]
issues: ["[[ISS-0106-Project-Os-As-A-Plugin]]"]
tasks: ["[[TASK-0199-The-Mod-Reaches-Every-Repo-Through-The-Template-Sync]]", "[[TASK-0200-A-File-Changed-From-The-Shell-Counts-As-A-Write-At-Close-Out]]", "[[TASK-0201-A-Session-On-The-Wrong-Model-Is-Named-At-Start]]", "[[TASK-0202-The-Project-Line-Above-The-Prompt]]"]
artifacts: []
adequacy: ""
mutation_score: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
review_round: ""
related: ["[[project-os-cockpit#TST-0097-The-Cockpits-Counts-And-Open-Button-Sit-On-The-Project-Line]]", "[[REFERENCE-PROJECT-LINE-CONTRACT]]"]
area: "Claude Code adapter"
after: []
---

# A Claude session shows the project line, names a wrong model, and treats a shell edit as a write

## Purpose

Confirms what FEAT-0041 promises a person, in an ordinary terminal and not a cockpit one: the line appears in a synced repo with no install step to remember, its facts match the repo, a wrong model is named, and a file changed through the shell triggers the close-out check.

## Setup

project-os-cockpit after TASK-0203's sync, opened in macOS Terminal (not a cockpit terminal), so the cockpit's plugin is not loaded. Claude Code 2.1.300 or the version `plugin.json` names.

## Steps

1. Start `claude` in the repo. **Expect:** one line above the prompt with the focus item, its status and phase, a validator error count, a review-stale count and a route. No segment after it. No install prompt other than the one ADAPTER.md describes.
2. In another terminal, read `focus:` in `SNAPSHOT.yaml` (or look the item up with `python3 tools/scripts/snapshot-query.py <ID>`) and run `bash tools/scripts/validate-docs.sh 2>&1 | grep -c '^ERROR'` and `... | grep -c REVIEW-STALE`. **Expect:** the focus item, status and phase on the line match the snapshot; the two counts match the two greps. The route matches the bracketed kind of work in the hint the session received at its last prompt.
3. Change the focus item in `SNAPSHOT.yaml` from the session (ask Claude to do it), and let the turn end. **Expect:** the line shows the new focus item within a few seconds, without restarting.
4. With a focus task set, ask Claude to change one line of a tracked file with `sed -i` through Bash and nothing else. **Expect:** when the turn ends, the close-out check blocks once, as it would after an Edit.
5. Ask a question that changes no file. **Expect:** no close-out block.
6. Quit, then resume the session with `claude --resume --model <a model other than the pin>`, or start one with `--model`. **Expect:** a warning row above the line naming the session's model and the pin. Ask Claude to quote any note about its model from its context. **Expect:** it quotes the same sentence.
7. Narrow the terminal to 60 columns. **Expect:** the line is cut from the right; the focus item stays visible.

## Expected result

Every step's **Expect** holds.
