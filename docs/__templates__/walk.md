---
type: "[[reference]]"
title: "Walk order — the sittings this project's releases are walked in"
status: active
owner: unassigned
created: 2026-01-26
updated: 2026-01-26
gallery: ""          # optional: a command that regenerates the screen gallery; the walk sheet prints it at the top of the survey
---

# Walk order

Copy this file to `docs/tests/acceptance/WALK.md` and rewrite the sittings for your product. It is the only place the order of a release walk is written down, and `python3 tools/scripts/walk-sheet.py` reads it to build every sheet. What the sheet does with it — which sitting claims a check, what happens to a check no sitting claims, why nothing here may carry a duration — is stated once in `tools/instructions/TESTING.md`, "The walk".

**What to write down.** The order is a state machine over the product, not a priority list. Put the sittings in the order a person can actually reach the states: fresh install before an account with data, free tier before the upgrade that cannot be undone, everything that needs the hardware on the bench together, and the wipe that ends the session last. That sequencing is the knowledge this file exists to keep, and it is the part that gets thrown away every release when the plan is written by hand.

**One `### ` heading per sitting, one fenced `yaml` block under it.** The heading is the sitting's name as the sheet prints it. The keys are below; `surfaces` and `checks` say what the sitting claims, `state` and `bench` say what it needs. A sitting with neither `surfaces` nor `checks` can claim nothing and is reported when the sheet is generated.

### Fresh install and first rider

```yaml
surfaces: ["Riders & profiles", "App shell & UX"]   # area: strings, or SUR-* ids whose title is the area string
state: "Fresh install, no rider yet. Cheapest: Settings > Developer > Clear data, then force-stop."
bench: ["Tablet with the candidate build"]
```

### Hardware on the bench

```yaml
surfaces: ["Hardware"]
checks: ["TST-0044"]                                 # optional: ids pulled into this sitting whatever their area
state: "A rider exists and one ride has been completed, so the ride screen has history to show."
bench: ["Smart trainer, powered and awake", "Heart-rate strap, charged", "A second trainer for the mid-ride swap row"]
```

**The four keys** — `surfaces`, `checks`, `state`, `bench` — are documented once in `SCHEMAS.md`, "Walk order (`WALK.md`)". **No durations, anywhere**: not in `state`, not in a heading, not in a comment. The sheet counts rows and prints no minutes, and the reason is in "The walk", rule 8.

**A sitting's procedure is found by name, and nothing here points at it.** A sitting may be walked from a written script instead of from each check in turn: one file under `docs/tests/acceptance/walk/`, from `docs/__templates__/procedure.md`, whose `sitting:` repeats this file's `### ` heading word for word. That single field is the whole link — a pointer written in both files is a pointer that can disagree, and renaming a heading here would then leave two files disagreeing instead of one reporting it. The sheet prints the path of the procedure it used, and `walk-sheet.py --check` names any procedure whose `sitting:` matches no heading in this file. What a procedure contains is "The walk", rule 9.
