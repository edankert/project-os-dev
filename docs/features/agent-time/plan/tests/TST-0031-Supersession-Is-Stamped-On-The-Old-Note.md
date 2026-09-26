---
type: "[[test]]"
id: TST-0031
aliases: ["TST-0031"]
title: "Supersession written on the new note is stamped on the old one, warned when work in flight links the old one, and shown by the lookup"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0173]]"]
scope: system
level: integration
entrypoint: "../project-os/tools/scripts/test-derive-pointers.sh"
command: "bash ../project-os/tools/scripts/test-derive-pointers.sh"
covers: ["[[ISS-0096-Superseding-Means-Editing-The-Old-Note]]"]
tasks: ["[[TASK-0173]]"]
issues: ["[[ISS-0096-Superseding-Means-Editing-The-Old-Note]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 11 assertions. Seven mutations in a scratch copy: M1 an undecided successor stamps too, 2 failures; M2 no status change, 6; M3 only the last amender kept, 2; M4 one field spelling for every type, 1; M5 finished notes warned too, 1; M6 snapshot-query drops the pointer, 1; M7 the snapshot status is not re-synced after a stamp, 3. Pristine 11 of 11."
related: []
---

# Supersession written on the new note is stamped on the old one, warned when work in flight links the old one, and shown by the lookup

## Purpose

ISS-0096: superseding meant editing the old note by hand, and ADR-0045 went nine days without a pointer to the ADR that amended it. Now the author writes `supersedes:` or `amends:` on the new note only.

## Procedure

`bash tools/scripts/test-derive-pointers.sh` in `~/Dev/repos/project-os`, on a fixture repo run through `sync-snapshot.py`.

- The old ADR gets `superseded: "[[ADR-0002]]"` and status `superseded`, and the snapshot entry follows. The sync names each note it wrote.
- A `proposed` successor replaces nothing yet.
- An ADR amended by two others lists both under `amended_by:` and keeps its status.
- A design gets the field its type spells, `superseded_by:`.
- A second `--check` run finds nothing to stamp.
- A task in flight that links the old ADR gets a CITES-SUPERSEDED warning naming its successor; a finished task linking it gets none.
- `snapshot-query.py` prints `superseded-by=` and `amended-by=`.

## Expected results

- Exit 0: 11 of 11, 2026-09-26.
