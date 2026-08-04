---
type: "[[issue]]"
aliases: ["ISS-0038"]
id: ISS-0038
title: "Round-six review: the engineering is clean for a third consecutive round and the two notes now agree with each other on every figure I could measure — but the restated \"seventeen\" names fourteen files that demonstrably DO supply titles, so the fail-safe's population is now wrong in a new way on four surfaces, and round five's reading was refuted on a technicality rather than on the substance"
status: open
severity: low
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
component: tooling
source: ["review:2026-08-04-independent-review-round-six-FEAT-0022", "22 mutations + 4 extra formulations + full fleet re-measurement 2026-08-04 over 12 repos"]
phase: "[[PHASE-999]]"
parent: ""
related: [FEAT-0022, ADR-0018, ISS-0026, ISS-0032, ISS-0033, ISS-0034, ISS-0035, ISS-0036, ISS-0037, TASK-0082, TASK-0083, TASK-0084, TASK-0085, TST-0003, CHG-20260804-Retention-And-Field-Derivation]
tests: [TST-0003]
---

# Round-six review findings on the FEAT-0022 record

Sixth clean-context independent review (fresh session; the notes and the diff only, no access to the authoring session's reasoning). `ISS-0033` through `ISS-0037` were read as records of claims to refute, not as findings to trust. Verdict: **changes-requested**, on one item.

**Round five's central diagnosis is fixed.** The two notes were corrected together and now agree with each other on every figure that appears in both: `fails 4 assertions`, `ten independent breaks`, `10 of 22`, `200` (198 pre-migration), `23 assertions`, `3,146`, `16`/`3`. The false known-gap is gone. `every prune condition is violated in turn` is gone on its fourth flagging, replaced by a named list plus an explicit statement that condition (4) has no fixture. `sync-snapshot.py`'s docstring and `_yaml_quote`'s `3,164` are corrected. All of that I re-derived rather than read.

**What blocks is the one item round five and the author disagree about, and the author's refutation does not survive contact with the code.**

## 1. Blocking — the restated "seventeen" names fourteen files that do supply titles

The sentence, identical in `CHG:78` and `TST-0003:51`:

> Derivation fails safe: a note that is missing, zero-byte, unparseable, or has no `title:` leaves the snapshot value untouched. **Seventeen files under `docs/` cannot supply a title** … 3 are zero-byte, and **14 open with `---` delimiters whose YAML does not parse** (8 in `your-trainer`, 5 in `your-health`, 1 in `your-applications.com`).

The population of 14 is real and reproducible — I found it independently, at exactly 8/5/1. They are notes whose `acceptance:` list is indented under the wrong parent, so `yaml.safe_load` raises `ParserError`:

| repo | files |
|---|---|
| your-trainer | `REQ-0194`, `REQ-0195`, `REQ-0196`, `REQ-0197`, `REQ-0198`, `REQ-0199`, `REQ-0200`, `REQ-0201` |
| your-health | `REQ-0017`, `REQ-0020`, `REQ-0024`, `REQ-0025`, `REQ-0026` |
| your-applications.com | `REQ-0028` |

**But every one of them supplies a title**, and the claim is that they cannot. `load_yaml` catches the PyYAML failure and falls back to `parse_yaml_subset`, which reads them fine, so `parse_frontmatter` returns a populated dict and `note_fields` returns a title for all fourteen. Run against the shipped code:

```
your-trainer  REQ-0194 -> 'Per-User Workout Favorites' … REQ-0201 -> 'Paywall Two-Column Comparison Layout'
your-health   REQ-0024 -> 'AI Coach: chat-based training recommendations'
your-app…com  REQ-0028 -> 'Manual + landing coverage stays in lockstep…'
```

`your-health`'s `SNAPSHOT.yaml:1506` carries `title: "AI Coach: chat-based training recommendations"` — the derived value, from a file the note says cannot supply one. These fourteen are not fail-safe cases; they are ordinary notes that derivation processes normally. Measured under the reader the code actually uses, the count of files under `docs/` that open with `---` and cannot be parsed is **0**, in all twelve repos.

The note's own arithmetic corroborates this. The sentence pairs the seventeen with "plus **200** `CHG-*` entries that no note claims by ID" as the set derivation must leave alone. That set is **217**: 200 unclaimed `CHG-*` + **17** non-`CHG` registered entries with no derivable title. Under the note's own reading the total would be 203, and the seventeen would have no relationship to the fail-safe at all. Only the other reading balances.

### What the seventeen actually is — and why both prior descriptions were wrong

- **3 zero-byte note files**: `project-os-cockpit` `TASK-0182`, `TASK-0183`, `TASK-0187`. Both descriptions get these right.
- **14 `your-health` entries `REF-0001`…`REF-0014`**, whose notes **do exist** — `docs/reference/REF-0001-Health-Tracker-Openness-Landscape.md` and thirteen siblings.

So `ISS-0037:139`'s refutation of round five — *"all 14 have note files"* — is literally true, and it is beside the point. `REF` is not in `ID_PREFIXES` (`validate-docs.py:55`), so `ID_RE` never matches those filenames, `build_note_index` records no claim, and `note_fields` can resolve no note for the ID. Round five's *label* ("no note file at all") was wrong; its *population* was right, and the substitute population is wrong in the way that matters. A file that exists but that the ID machinery cannot see is exactly a fail-safe case.

That is also the more interesting fact the seventeen has been hiding for six rounds: **any snapshot entry whose prefix is outside `ID_PREFIXES` is structurally invisible to derivation and to every ID-keyed check** — fourteen live entries in `your-health` today, and the same mechanism is why the 200 `CHG-*` entries are unclaimed. Worth its own issue; the record should stop attributing it to unparseable frontmatter.

**Four surfaces carry the wrong composition** and must move together, which is the failure mode rounds four and five both hit: `CHG-20260804:78`, `TST-0003:51`, `sync-snapshot.py:269-271` (docstring), `test-retention.py:135` (comment).

## 2. Blocking — `CHG:78` carries a paste artifact

The line reads `… is what made an earlier draft of this line irreproducible.md` — plus **200** `CHG-*` entries …`. The stray `` .md` `` is spliced in from the sentence the rewrite replaced; the unbalanced backtick opens a code span that swallows `— plus **200**` and drops its bold. Trivial to fix, but it is in the sentence under discussion.

## Non-blocking, recorded

- **`CHG:120` names nine survivors; `TST-0003` names twelve.** Both are true — `CHG` does not claim its list is exhaustive — but it omits the non-string title fail-safe, the banner and the ambiguous-claim guard. Two lists of the same set at different lengths is what round five's contradiction grew from.
- **`CHG:70` lists conditions "1, 2, 3, 5 and 6" as inverted; condition (7) is inverted too** (`cond7 waiver holds`) and is not listed. It understates rather than overstates, so it is not the round-five failure repeating.
- **`TST-0003`'s `adequacy` puts "blank titles accepted" in the caught list and "the blank/non-string title fail-safe" in the uncovered list.** I checked both formulations rather than assuming a contradiction: making a *missing* title an empty string that gets written **is caught** (2 assertions); accepting a *blank but present* title **survives**. Both statements are true of different mutations. Reading as a contradiction four lines apart is a wording cost, not an error.
- **Item counts have drifted since the note was written.** `CHG:54` calls item counts "the stable measure: 3,146 → 1,817" while disclosing byte drift only; I measure **3,146 → 1,818**, and the table's `project-os-dev` row `161 → 134` measures `161 → 135`. Cause is the same disclosed one — this repo gains notes as review proceeds — and filing this issue moves it again. The honest form is "measured at the time of writing".
- **Carried forward, untouched and correctly recorded as debt**: ADR-0018's six authorised conditions against seven implemented, the fifteen-line non-verbatim drift in the bundled validators, and `prunable_ids` resolving `note_fm` through `index` rather than `claimants` (`sync-snapshot.py:496`). Each is named with its reasoning; none is held against this verdict.

## Next actions

- [ ] Restate the seventeen on all four surfaces: **3 zero-byte notes** (`project-os-cockpit` `TASK-0182/0183/0187`) **plus 14 `your-health` `REF-*` entries whose notes exist but whose prefix is outside `ID_PREFIXES`, so no note claims the ID** — over registered non-`CHG` entries, not over files under `docs/`, and not "unparseable".
- [ ] Delete the 8/5/1 breakdown: those fourteen files parse through the fallback reader and derivation works on them.
- [ ] Remove the stray `` .md` `` from `CHG:78`.
- [ ] Consider an issue for the real finding underneath: entries whose prefix is outside `ID_PREFIXES` (`REF-*` today, 14 of them in `your-health`) are invisible to derivation and to every ID-keyed validator check.
- [ ] Optional: bring `CHG:120`'s survivor list to twelve, and add condition (7) to `CHG:70`'s list.

## What held under attack

Re-derived this session by mutation, construction or measurement. Not inherited from rounds four or five, both of whose "no code defect" conclusions I set out to break.

- **Mutation adequacy is exact.** I wrote my own set of 22 mutations without consulting the prior rounds' list, applied each to a restored source, and scored **10 caught / 12 survived** — the same figure `TST-0003` and `CHG:120` claim. Every one of the twelve survivors `TST-0003` names was individually confirmed to survive, including the ambiguous-claim guard, checked in both `note_fields` and `note_statuses`. Reverting condition (5) to a bare index test fails **4** (`cond3`, and the zero-byte / unparseable / no-status fixtures); reverting it to `the_id not in statuses` **is caught**, failing `cond3 deferred survives`; reverting `_scalar_span` to `find("{")` fails **2**. Stubbing either destructive writer is caught.
- **Nothing was lost.** For each repo, the item IDs present at the migration commit's parent and absent now, each re-resolved against the notes on disk: **1,352 removals, 0 whose note fails to supply exactly the collection's terminal status.**
- **The migration is lossless, checked against git rather than against itself.** All twelve records parsed; every `was:` value compared to the value that repo's pre-migration snapshot actually carried: **709 rows, 709 faithful, 0 mismatches**, and every header count equals its section, `was:` and `now:` counts.
- **The fleet is clean.** 12/12 `validate-docs.sh` exit 0 — `project-os-dev` exit 1 on the standing `REVIEW` error alone — **0 `^ERROR`** and **0 `internal error`** elsewhere; `sync-snapshot.py --check` exit 0 in all twelve; `test-retention.py` green at **23 assertions** in all twelve.
- **Idempotent and at a fixed point.** In each of the twelve, two consecutive **real** syncs left `SNAPSHOT.yaml` byte-identical to the file they started from; every snapshot was hashed, backed up and restored.
- **Fleet figures exact**: before **1,151,665** bytes (git-immutable, matches), items **3,146** pre-migration, **200** unclaimed `CHG-*` now and **198** pre-migration, **16** braced and **3** double-quoted titles among the 3,146. Nine of ten per-repo byte rows and nine of ten item rows exact; `project-os-dev`'s drifts upward, as the note says it does.

## Status

Open. Finding 1 blocks; finding 2 is a one-character fix in the same sentence; the rest are recorded, not blocked. The verdict is recorded on `CHG-20260804-Retention-And-Field-Derivation` and `TST-0003` as `changes-requested`, replacing round five's. Per the convention `ISS-0022`/`ISS-0023` established, the author fixing these does not close the issue.

The `REVIEW` error on `TST-0003` therefore stands and `validate-docs.sh` continues to exit 1 in this repo.

**A note on proportion, since this is round six.** The engineering has been clean for three consecutive rounds and I could not break it; the record is now self-consistent, which is what round five asked for. I am withholding on one sentence, and only because it is demonstrably false rather than merely imprecise: it names fourteen specific files as unable to supply a title, and all fourteen supply one — I ran the shipped code against each. A maintainer trusting it would "repair" fourteen healthy notes and would never learn that the actual mechanism is a prefix outside `ID_PREFIXES`. That is the difference between a gap accurately recorded as a gap, which I would have approved over, and a false statement about how the safety property behaves. Restating one sentence in four places closes it.

**Independence of this pass**: fresh context and a separate session. I started from the two notes and the diff, with no access to the authoring session's reasoning, and no memory of authoring any of this work. `ISS-0033`–`ISS-0037` were read as claims to refute — which is how finding 1 surfaced, since round five's reading and the author's rebuttal are both partly wrong and the disagreement had to be settled against the code rather than against either account. My mutation set was constructed before reading the prior rounds' tables, so the 10/22 agreement is a reproduction rather than a re-reading. **Not independent: the model.** This is `claude-opus-5[1m]`, the same identifier rounds two through five recorded and the same family as the author, so `reviewed_by` alone cannot distinguish this round; `review_date` and the `review_note` are what separate them. Under ADR-0013 context is the mechanism and family is not the gate, so the pass is independent in the sense the skill requires — but six rounds have now run with no different-family check, and that remains the one form of independence this change has never had.

## Status — resolved 2026-08-04, with both sides of the dispute wrong

Round six is **right that the sentence was false**, and its proposed replacement is **also false**. Measurement settles both:

- The 14 files whose frontmatter PyYAML rejects **do supply titles**. `load_yaml` falls back to `parse_yaml_subset`, and `your-health`'s `REQ-0024` carries a derived title in its snapshot today. My claim that they "cannot supply a title" was wrong, and had survived three rounds because every reviewer and I checked the *parse*, never the *fallback*.
- Round six's replacement — `your-health` `REF-0001..REF-0014`, unclaimed because `REF` is absent from `ID_PREFIXES` — is refuted the same way: `note_fields` supplies **all 14**. Its arithmetic (17 + 200 = 217) does not reconcile either; the measured skip set is **203**.

The true population, measured across all twelve repos: derivation skips **203** registered entries — **200** `CHG-*` (date-slug ids no note claims) and **3** zero-byte notes, which are the entire population that genuinely cannot supply a title. Restated on all four surfaces.

The transferable lesson is the one this whole review chain keeps teaching in different costumes: **a plausible number repeated across documents is not evidence, and neither is a reviewer's correction to it.** Five rounds discussed this figure. None of them ran `note_fields` against the files in question, which took one command and ended the argument.

Stays **open**: the author does not clear a verdict on their own work.
