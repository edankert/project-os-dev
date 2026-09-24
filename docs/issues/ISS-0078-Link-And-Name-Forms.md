---
type: "[[issue]]"
id: ISS-0078
aliases: ["ISS-0078"]
title: "Nothing states how a link or a filename is written, so views show long dashed labels"
status: open
phase: ""
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["Edwin, 2026-09-21, on PHASE-0008 rendering as a dashed label in Obsidian"]
reported_by: "user:edwin"
question: ""
severity: medium
component: instructions
parent: ""
related: ["[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]", "[[FEAT-0038-Note-Relevance-Harness]]", "[[ISS-0077-Who-Approves-Requirements]]"]
tests: []
---

# Nothing states how a link or a filename is written

## Problem

A note opened in Obsidian shows some of its linked items as clickable references and others as plain dashed text that goes nowhere. Which one you get depends on how whoever wrote the note happened to spell the link, and three spellings are in use across the repo. Edwin hit this on 2026-09-21 when PHASE-0008 appeared in the features view as a dashed label rather than a ticket.

> [!quote] As reported — 2026-09-21 (user:edwin)
> But PHASE-0008 in the features view does not show as a ticket/note same in the overview detailed section, it shows as some dashed line label
>
> Links should include the full filename

The rule is now settled — **a link includes the full filename** — but it is not written anywhere, and nothing checks it.

## Repro

Open any note with a populated `related:` or `tasks:` field in Obsidian and compare how its entries render.

## Expected

One form, stated once, and a check that holds notes to it. Per Edwin's ruling: `[[FEAT-0038-Note-Relevance-Harness]]`, with a pipe for a readable label where the slug would be noise in prose.

## Actual

Three forms are in use. Measured 2026-09-21 across 459 notes:

| Form | Example | Count | Verdict |
|---|---|---:|---|
| Full filename | `[[FEAT-0038-A-Harness-Scores-...]]` | — | correct |
| Bare-ID wikilink | `[[PHASE-0003]]` | 399 | a link, but not the full filename |
| Bare ID, not a link | `FEAT-0024` | 1057 | already forbidden by `OBSIDIAN.md` |

**347 of 459 notes** carry at least one. `SNAPSHOT.yaml` carries a further **108** bare-ID phase links. The worst-affected fields are `related:` (513 non-links, 62 bare links), `tasks:` (136 / 84) and `phase:` (137 bare links).

A bare-ID wikilink resolves only when the target note carries a matching `aliases:` entry. `PHASE-0006-Codex-Native-Adapter.md` and `PHASE-0007-Reviews-That-Fix-And-A-Backlog-That-Is-True.md` carry no `aliases:` at all, so the 37 notes pointing at them by bare ID resolve to nothing.

### The second half: filenames

A link carrying the full filename is only readable if the filename is short. `OBSIDIAN.md` asks for "the stable ID plus a **short descriptor**" and does not say what short means, so descriptors have grown to a median of 31 characters and a maximum of 79.

Measured 2026-09-21 across 373 ID-prefixed notes: **187 (50%) exceed 30 characters and 54 (14%) exceed 50**. By type, worst first: ISS 71 of 78, TASK 56 of 155, ADR 17 of 33, TST 16 of 21, FEAT 13 of 38, REQ 11 of 32.

The thirteen notes of PHASE-0008 were renamed to 15-25 character descriptors on 2026-09-21 as the first set under the new rule, so they are the reference shape, not an exception: `PHASE-0008-Measured-Note-Ranking`, `FEAT-0038-Note-Relevance-Harness`, `TASK-0154-Parameter-Sweep`.

## Evidence

- `tools/instructions/OBSIDIAN.md` says only "Use **links** in properties instead of bare IDs whenever the target is another note in this docs set." That forbids row three and is silent between rows one and two.
- All five note templates in `docs/__templates__/` ship `phase:` with no example value, so a scaffolding agent has nothing to copy.
- `tools/scripts/validate-docs.py` checks that a link resolves (LINK), never that it is written one way — which is why a repo-wide inconsistency this size passes a green validator.
- Demonstrated cost, 2026-09-21: an agent asked to fix the PHASE-0008 rendering inferred the convention by counting usage, found the bare form more common (137 against 123), rewrote eleven notes to it, and was wrong. The correction and its reasoning are in `[[TASK-0150-Git-History-Benchmark]]`.

## Next Actions

- [ ] State the rule once, in `tools/instructions/OBSIDIAN.md`: a link to another note uses the full filename, with `[[Full-Filename|Label]]` where prose needs a short label.
- [ ] Put a worked example in each `docs/__templates__/` note so a scaffolding agent copies the right shape.
- [ ] Add a validator check for link form, so this cannot drift green again. Without it the sweep below is undone by the next scaffold.
- [ ] Sweep the 399 bare-ID wikilinks and 1,057 non-link bare IDs, and the 108 snapshot entries. Mechanical once the check exists to verify it.
- [ ] Decide whether `aliases:` stays on note frontmatter at all once links carry full filenames, or whether PHASE-0006 and PHASE-0007 should simply gain the field.
- [ ] State a filename rule with a number in it, beside the link rule in `tools/instructions/OBSIDIAN.md` — the PHASE-0008 set used 15-25 characters and reads well.
- [ ] Rename the 187 notes whose descriptor exceeds 30 characters, updating every reference and `SNAPSHOT.yaml` with them. ISS and TASK are 127 of the 187.
- [ ] Add the filename-length check alongside the link-form check, for the same reason: without it the next scaffold reintroduces both.

> [!note] Both checks are deterministic, and deliberately so
> Asked on 2026-09-21 whether a System One model (Jev) should verify these rules. No. "Does `[[X]]` match a filename under `docs/`" is a set membership test and "is the descriptor under N characters" is arithmetic; neither has semantic content to judge. A model would be slower, cost money, and return a probability where a proof is available. It matters more than usual here because these checks belong in the commit gate, where a network call turns an API outage into a commit outage — and `validate-docs.py` already walks all 459 notes in 5.31 seconds for nothing. The one place a model could earn its place is inside the **sweep**, scoring whether a proposed short descriptor still describes its note (one `Noul` per candidate, low confidence escalated to a person). That is a judgment; the checks are not. Measure it against skimming the names by hand before assuming it wins.
- [ ] Carry both rules and both checks to the template repo, since every project-os repo has this shape.
