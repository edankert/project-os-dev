---
type: "[[reference]]"
title: "Section order — the sections this project's releases are tested in"
status: active
owner: unassigned
created: 2026-01-26
updated: 2026-01-26
gallery: ""          # optional: a command that regenerates the screen gallery; the release test sheet prints it at the top of what changed
# length_limits: {action: 20, expected: 25, section_base: 300, section_per_check: 40, error: true}  # optional: override the length check (SCHEMAS.md)
# quoted_lines: refused  # optional: `warning` while procedures still quote expected results (SCHEMAS.md)
---

# Section order

Copy this file to `docs/tests/acceptance/RELEASE-TEST.md` and rewrite the sections for your product. It is the only place the order of a release test is written down, and `python3 tools/scripts/release-test.py` reads it to build every sheet. What the sheet does with it — which section claims a check, what happens to a check no section claims, why nothing here may carry a duration — is stated once in `tools/instructions/TESTING.md`, "The release test".

**What to write down.** The order is a state machine over the product, not a priority list. Put the sections in the order a person can actually reach the states: fresh install before an account with data, free tier before the upgrade that cannot be undone, everything that needs the hardware on the bench together, and the wipe that ends the session last. That sequencing is the knowledge this file exists to keep, and it is the part that gets thrown away every release when the plan is written by hand.

**One `### ` heading per section, one fenced `yaml` block under it.** The heading is the section's name as the sheet prints it. The keys are below; `surfaces` and `checks` say what the section claims, `state` and `bench` say what it needs. A section with neither `surfaces` nor `checks` can claim nothing and is reported when the sheet is generated.

### Fresh install and first rider

```yaml
surfaces: ["Riders & profiles", "App shell & UX"]   # area: strings, or SUR-* ids whose title is the area string
state: "Fresh install, no rider yet. Cheapest: Settings > Developer > Clear data, then force-stop."
bench: ["Tablet with the candidate build"]
```

### Hardware on the bench

```yaml
surfaces: ["Hardware"]
checks: ["TST-0044"]                                 # optional: ids pulled into this section whatever their area
state: "A rider exists and one ride has been completed, so the ride screen has history to show."
bench: ["Smart trainer, powered and awake", "Heart-rate strap, charged", "A second trainer for the mid-ride swap row"]
```

**The four keys** — `surfaces`, `checks`, `state`, `bench` — are documented once in `SCHEMAS.md`, "`release-test.md` — the section order (`RELEASE-TEST.md`)". **No durations, anywhere**: not in `state`, not in a heading, not in a comment. The sheet counts rows and prints no minutes, and the reason is in "The release test", rule 8.

**A section may be tested from a written script instead of from each check in turn.** Nothing here points at one: where a procedure lives, how it names its section and why the pointer runs one way are stated once in `tools/instructions/TESTING.md`, "The release test", rule 9.
