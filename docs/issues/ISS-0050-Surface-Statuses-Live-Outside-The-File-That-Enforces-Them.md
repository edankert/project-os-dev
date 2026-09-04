---
type: "[[issue]]"
id: ISS-0050
aliases: ["ISS-0050"]
title: "Surface statuses live outside the file that enforces them"
status: triage
phase: "[[PHASE-0003]]"
severity: low
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
component: docs
source: ["The ISS-0048 drift sweep, pass 11, run 2026-09-04 in a clean context over template 19ba330"]
related: ["[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]"]
tasks: []
tests: []
---

# Surface statuses live outside the file that enforces them

## Problem

`STATUSES.md` opens by saying it is the single normative source for item state, and it has no `[[surface]]` section. The allowed statuses for a surface note are in `TAXONOMY.md` instead. That split is invisible until you notice what reads which file: `load_allowed_status` in the validator parses `STATUSES.md` alone, so editing the surface list in `TAXONOMY.md` changes nothing a check will ever catch.

## Repro

```bash
cd ~/Dev/repos/project-os
grep -n "surface" tools/instructions/STATUSES.md            # no section
sed -n '25,28p' tools/instructions/TAXONOMY.md              # the list lives here
grep -n "def load_allowed_status" -A 12 tools/scripts/validate-docs.py   # reads STATUSES.md only
```

## Expected

Either the surface list sits in `STATUSES.md` with every other type and the validator enforces it, or `STATUSES.md` stops claiming to be the single source for state and says where the exception is.

## Actual

A reader is told one file holds every status list, finds one type missing from it, and has no way to tell whether the list they did find is enforced.

## Evidence

- `tools/instructions/STATUSES.md:13` — the single-normative-source claim.
- `tools/instructions/TAXONOMY.md:25-28` — the surface status list.
- `tools/scripts/validate-docs.py:110` — the enforcing default; `:707` — `load_allowed_status`, reading `STATUSES.md` only.

## Next Actions

- [ ] Decide: move the list into `STATUSES.md`, or record the exception there. Moving it starts enforcing surface statuses in every downstream repo, so a repo holding a surface note outside the list would newly error; that lands under the grandfathering rule (`STATUSES.md`, "Grandfathering") with the violating IDs counted first.

## Sibling search

Sibling found: [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]. Searched `docs/issues/` for: surface, STATUSES, allowed, taxonomy. Filed separately from ISS-0048 because it is a split home rather than a duplicated one, and because the fix changes enforcement.

## Risk scan

No new risks if the exception is recorded; if the list moves, the hazard is the newly-erroring downstream repos named in the Next Action, which the grandfathering rule already covers.
