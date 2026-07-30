---
type: "[[issue]]"
id: ISS-0024
aliases: ["ISS-0024"]
title: "The template ships three WF notes at status: draft that nothing links and no repo has ever touched — 8 of 8 adopting repos still carry them unedited at draft since 2026-01-29, and the two repos that actually used docs/workflows/ deleted them first"
status: open
severity: low
owner: user:edwin
created: 2026-07-30
updated: 2026-07-30
component: docs
source: ["project-os-cockpit PHASE-010 (surface ownership), 2026-07-29: deciding where the [[workflow]] type belongs in the cockpit's IA required measuring whether the type is used at all"]
phase: "[[PHASE-999-Parking-Lot]]"
related: [WF-0001, WF-0002, WF-0003]
depends: []
tests: []
---

# Template workflows ship permanently draft

## The finding

`docs/workflows/` in the template ships three notes — [[WF-0001-Existing-Project-Init]], [[WF-0002-Template-Sync]], [[WF-0003-Recovery-Resume]] — plus a README indexing them. Every adopting repo inherits all three at `status: draft`, `updated: 2026-01-29`, and **not one has ever been edited, advanced, or linked to.**

Measured across the 11 repos under `~/Dev/repos/` on 2026-07-30:

| Repos | `docs/workflows/` contents | Template three at | Ever edited |
|---|---|---|---|
| 8 | the template three (one also has 2 bespoke) | `draft`, `updated: 2026-01-29` | never |
| 2 | 5 and 1 bespoke workflows | **deleted** | n/a |
| 1 | empty | absent | n/a |

The 8 include `project-os` itself and `project-os-dev`. Every bespoke workflow anyone has written — 8 of them across `obsidian-supernote-sync`, `your-trainer` and `your-applications.com` — carries `status: active`. **No exceptions in either direction**: every authored workflow is active, every template workflow is draft.

The two repos where someone actually engaged with `docs/workflows/` (`obsidian-supernote-sync`, `your-trainer`) removed the template three before writing their own. `your-applications.com` is the sole repo that kept them *and* added its own.

## Why draft is the load-bearing part

`STATUSES.md` gives `[[workflow]]` the transitions `draft` → `active` → `deprecated`. So the template hands every new project three notes that assert, in their own frontmatter, that they are unfinished — and provides no moment at which anyone would advance them, because they describe project-os's operations rather than the adopting project's.

An adopter reading `docs/workflows/` sees three drafts about the template's own machinery and none about their build, test or deploy. The README's `REPLACE ME` line asks them to add their own; six months of fleet evidence says they add nothing and the drafts stay.

## They are wrappers, not content

Each of the three has a single `entrypoints:` value pointing at something else that already owns the material:

- `WF-0001` → `tools/skills/project-derive/SKILL.md`
- `WF-0002` → `tools/scripts/sync-project-os.sh` (documented in `tools/instructions/SYNCING.md`)
- `WF-0003` → `tools/skills/snapshot-sync/SKILL.md` (and `HANDOFF.md`)

Nothing links back. Grepping the template for inbound references to the three IDs outside `docs/workflows/` returns only the README's own index and one incidental mention in `CHG-20260717-Manifest-Sync-And-Fleet-Validation` ("workflows: not-applicable"). Notably `SYNCING.md` — the instruction file for the exact operation `WF-0002` describes — does not link it.

So they are orphans in the link graph, restating skills and instructions that *are* linked and *are* maintained.

## A correction to how this was first framed

When this surfaced during project-os-cockpit's PHASE-010 it was described as "content nobody asked for". That is wrong and worth not propagating: the three describe **real project-os operations**, and the derive/sync/recovery trio is a defensible list of the template's front doors. The defect is not that they are meaningless. It is that they are permanently-draft duplicate indexes of material owned elsewhere, and the fleet has voted with six months of silence.

## Options

Not decided here — this is the template's call, and there is a real argument for each.

1. **Ship `docs/workflows/` with the README only.** The three operations stay documented where they already are (skills + instructions), which is where the maintained copy lives. Adopters get an empty, self-explaining folder for their own workflows. Removes 3 permanently-draft notes from every repo. Cost: loses the one place that lists project-os's entrypoints as a set.
2. **Keep them, ship `status: active`, and link them.** Make them the front door they claim to be: `SYNCING.md` links `WF-0002`, the `project-derive` skill links `WF-0001`, `HANDOFF.md` links `WF-0003`. Cost: creates a second maintained surface for material the instructions already own, and `SYNCING.md` has to stay in step with `WF-0002` forever.
3. **Leave it.** Defensible if the drafts are read as examples rather than as project state — but nothing says so, and `status: draft` says the opposite.

Option 1 is the recommendation. Option 2 is the honest alternative if the entrypoint index is considered worth keeping; what should not persist is the current state, where the notes claim to be unfinished, nothing points at them, and no repo in six months has treated them as either.

## Evidence

```
$ for d in ~/Dev/repos/*/; do ... done          # 2026-07-30
project-os                 WF=3  template=3  status: draft
project-os-cockpit         WF=3  template=3  status: draft
project-os-dev             WF=3  template=3  status: draft
project-os-bench           WF=3  template=3  status: draft
edankert.com               WF=3  template=3  status: draft
your-applications.com      WF=5  template=3  status: draft
your-health                WF=3  template=3  status: draft
your-sudoku                WF=3  template=3  status: draft
articles                   WF=0  template=0
obsidian-supernote-sync    WF=5  template=0     (5 bespoke, all active)
your-trainer               WF=1  template=0     (1 bespoke, active)

$ grep -rn "WF-0001\|WF-0002\|WF-0003" --include="*.md" . | grep -v "^./docs/workflows/"
docs/changes/CHG-20260717-Manifest-Sync-And-Fleet-Validation.md:45: ... (WF-0002 entrypoint unchanged)
```

## Next Actions

- [ ] Decide between options 1 and 2
- [ ] If 1: remove the three notes, rewrite `docs/workflows/README.md`'s index section, drop `WF: 3` from the template's `counters` (or keep it — counters only ever rise, and an allocated ID is not freed by deletion)
- [ ] If 2: advance to `active`, add inbound links from `SYNCING.md`, `HANDOFF.md` and the two skills, and note the ongoing sync obligation in `SYNCING.md`
- [ ] Either way, decide whether adopting repos are expected to inherit the change on next sync (`sync-project-os.sh` copies `tools/`, not `docs/`, so `docs/workflows/` in existing repos will not update on its own)
