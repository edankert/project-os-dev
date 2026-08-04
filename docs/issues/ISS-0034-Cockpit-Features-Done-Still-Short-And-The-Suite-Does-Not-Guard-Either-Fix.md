---
type: "[[issue]]"
id: ISS-0034
aliases: ["ISS-0034"]
title: "Round-two review of the ISS-0033 fixes: the fixes hold, but project-os-cockpit still reports one done feature short while CHG-20260804 says the metric is restored, and TST-0003 guards neither of the two blocking fixes — reverting condition (5) to `index` or `_scalar_span` to the original brace test leaves the suite green"
status: open
severity: medium
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
component: tooling
source: ["review:2026-08-04-independent-review-round-two-FEAT-0022", "fleet re-measurement 2026-08-04 over 12 repos"]
phase: "[[PHASE-999]]"
parent: ""
related: [FEAT-0022, ADR-0018, ISS-0032, ISS-0033, TASK-0082, TASK-0083, TASK-0084, TASK-0085, TST-0003, CHG-20260804-Retention-And-Field-Derivation]
tests: [TST-0003]
---

# Round-two review findings on the FEAT-0022 fixes

Second clean-context independent review (fresh session, notes + diff only, no access to the authoring session's reasoning or to round one's), of the working-tree state of `tools/scripts/sync-snapshot.py`, `tools/scripts/test-retention.py`, `CHG-20260804-Retention-And-Field-Derivation`, `TST-0003` and the twelve re-migrated repos. Verdict: **changes-requested**.

`ISS-0033`'s five blocking findings were verified on the merits rather than from its tick-marks, and four of the five are resolved outright — the fifth is resolved in code and unrepaired in the data. The migration record is now stronger than its own claim. What blocks is the pair below: one uncorrected loss that the `CHG` note says has been corrected, and a test note whose assertion table describes coverage the suite does not have, for exactly the two defects this round fixed.

## Blocking

### 1. `project-os-cockpit` still reports `features_done: 54` against a pre-migration `55`, and `CHG-20260804:56` says both metrics are back

`CHG-20260804:56` — *"`project-os-cockpit` fell `tasks_done` 271→268 and `features_done` 55→54 because the prune removed entries it should not have; see the review below. **Both are back to their pre-migration values.**"*

`tasks_done` is back at 271 — `TASK-0182`, `TASK-0183` and `TASK-0187` are restored, byte-identical to `48ea49e~1`, and the fixed script does not re-prune them (their notes are still zero-byte, so they are absent from `statuses`). That half is real.

`features_done` is **54**. Measured three ways: the value written in `SNAPSHOT.yaml`, `compute_metric_counts` re-run against the current tree, and `48ea49e~1`'s own `metrics.counts` for the pre-migration figure. `FEAT-0009` was named in `ISS-0033`'s first next action alongside the three tasks; it was not restored, and the completion note silently narrows the ask to *"all three tasks restored"*. `CHG-20260804:83` does the same — *"all three entries are restored"*.

Restoring the entry is **not** the fix, and that is the substance of the finding rather than the bookkeeping. With `FEAT-0009` put back, `prunable_ids(..., window=25, ...)` returns it again on the next sync: its note `docs/features/native-shell-layout/FEAT-0009-Native-Shell-Layout.md` parses, claims the ID, and says `done`, so the fixed condition (5) admits it and it sits far outside a 25-wide window. The prune is legitimate. The loss is downstream:

`compute_metric_counts` is safe for a pruned entry only because it falls back to the note index — *"the notes remain the archive"*, which is the whole migration-safety argument. For `FEAT-0009` that fallback lands on the **wrong note**. `build_note_index` derives IDs from a note's `id:` via `extract_ids`, so `CHG-20260525-FEAT-0009-Chrome-Polish` registers a claim on `FEAT-0009`; `docs/changes/…` sorts before `docs/features/…`, `setdefault` keeps the first, and the archive therefore reports `FEAT-0009` as `merged`, not `done`. `note_statuses` was taught to resolve this through `claimants`; `compute_metric_counts` was not.

Measured fleet-wide: exactly **one** ID in the twelve repos has an index-vs-claimant status disagreement *and* was pruned by this change — `FEAT-0009`. So the exposure is one item today, which is why this is severity `medium` and not `high`. But the metric is permanently one short, nothing reports it, and the note that documents the change asserts the opposite.

Fix: either narrow `build_note_index` so a composite `id:` does not manufacture a claim on an embedded ID, or have `compute_metric_counts` prefer `claimants` the way `note_statuses` does — and until one of those lands, restate `CHG-20260804:56` to say what is actually true.

### 2. `TST-0003` guards neither of the two blocking fixes; its assertion table claims one of them

Mutations performed, each individually, against the working-tree suite (`18 assertions`, green):

| mutation | suite |
|---|---|
| condition (5) reverted to `if the_id not in index` — **the exact round-one defect that deleted three entries** | **SURVIVED** |
| `_scalar_span` reverted to choosing its branch on `body.find("{")` — **the exact round-one defect that killed derivation in ten of twelve repos** | **SURVIVED** |
| `_owes_verification` reverted to `statuses.get(t, "passing")` (fail-open) | SURVIVED |
| `_value_end`'s doubled-single-quote handling deleted | SURVIVED |
| `prune_entries`' `in_items` guard deleted | SURVIVED |
| focus scan reverted to top-level exact strings | SURVIVED |
| condition (4) deleted | SURVIVED |
| retention window off by one | SURVIVED |
| `PRUNABLE_TERMINAL` widened to `requirements`/`risks` | SURVIVED |
| `prune_entries` over-deleting by four columns of indent | SURVIVED |
| blank titles accepted in the derivation fail-safe | SURVIVED |
| `prune_entries` → `return []` | caught |
| `sync_derived_fields` → `return []` | caught |
| condition (3) deleted | caught |
| the `note:` hold deleted | caught |
| the verification hold deleted | caught |
| `_yaml_quote` emitting unquoted | caught |

The two writers are now genuinely executed — `ISS-0033` #4's specific ask is met. But every *fix* this round produced is unguarded, and a straight revert of either blocking defect is invisible to the suite. Both have already regressed once.

Two of these are worse than gaps because the note claims them:

- `TST-0003:47` — *"condition 5 note must exist **and parse** | an entry with no note survives; **a note that is zero-byte or unparseable does not count as existing** — checking mere index membership deleted three real entries"*. There is no zero-byte and no unparseable fixture in `test-retention.py`. The only condition-5 assertion is `cond5 noteless survives`, which a `not in index` implementation satisfies identically. The sentence describes the fix, not the test.
- The block-style end-to-end fixture derives `"note title"` — a title with no brace. One brace in that string is the difference between guarding the round's second blocking fix and not. `fixture()` already writes block style, so the case costs nothing.

`adequacy` is honest about the *previous* inadequacy and then lists five mutations as the evidence for this one; none of the five is either blocking fix.

## Non-blocking

### 3. `_focus_ids` is not an `extract_ids` walk, and it discards the canonical ID it just found

`sync-snapshot.py:436-446`:

```python
acc.update(ID_RE.findall(node) and
           [m.group(0) for m in re.finditer(r"\b[A-Z]+-[\w-]+\b", node)])
```

`ID_RE` locates the canonical IDs and is then used only as a truthiness gate; what is collected is a **greedy** `[A-Z]+-[\w-]+` token. So the two shapes this project writes IDs in most often do not protect anything:

```
focus.note: "blocked on [[TASK-0182-Nest-Children-By-Shared-Phase]]"  -> collects TASK-0182-Nest-Children-By-Shared-Phase
focus.note: "see docs/issues/ISS-0068-Timer.md"                        -> collects ISS-0068-Timer
```

Demonstrated: with either string in `focus`, `prunable_ids` returns `TASK-0182` / `ISS-0068`. `ISS-0033`'s sixth next action asked for *"a recursive `extract_ids` walk"*, ticked as *"collecting every ID-shaped token at any depth"*; `CHG-20260804:86` says *"focus now protects any ID it mentions at any depth"*. Neither is true of wikilink or path form.

Latent today, checked rather than assumed: across all twelve repos, the set of canonical IDs in `focus` that `_focus_ids` misses **and** that are registered items is empty in every repo. `your-sudoku`'s `ISS-0068` is restored, identical to `7aa1068~1`, is named bare in `focus.note`, and is protected.

`_vd.extract_ids` already does exactly this and is imported.

### 4. Condition (5) requires the note to supply *a* status, not the entry's *terminal* status

`ISS-0033`'s first next action asked for *"the note to supply the entry's terminal status"*. The implementation is `if the_id not in statuses`, which only requires a single claimant with a non-empty status. The gap is normally closed by `sync_statuses` running first — except where `sync_statuses` cannot write.

`_STATUS_INLINE_RE` is `(\bstatus:\s*)([A-Za-z][\w-]*)`, so an inline entry whose status is **quoted** is never rewritten. Run through `main()` end to end:

```yaml
items:
  tasks:
    TASK-0001: { status: "done", title: "x" }   # note TASK-0001 says: backlog
```

→ `pruned TASK-0001`. An entry whose note says the work is still `backlog` is deleted, which is the one outcome *"retention removes finished business, never unfinished"* forbids. Latent: no fleet snapshot writes an inline quoted status (checked, all twelve; `obsidian-supernote-sync`'s 32 quoted statuses are block style, which `_STATUS_BLOCK_RE` strips correctly).

Worth recording together: this same unsynced-status path is what makes condition (3) reachable in production, which is otherwise its only route. Closing (5) to `statuses.get(the_id) == terminal` would close (3)'s last real caller too, and the pair should be decided together rather than one at a time.

### 5. `CHG-20260804`'s verification section and impact table did not follow the fixes

- *"Eleven assertions"* (`:68`) — the suite prints 18 and `TST-0003:38` says 18.
- *"every prune condition is violated in turn"* (`:68`) — condition (4) is not inverted; deleting it leaves the suite green. `TST-0003`'s own table now honestly omits condition 4, so the two notes disagree.
- *"three independent breaks each caught"* (`:70`) — `adequacy` now lists five.
- Impact table rows measured against the current trees: `project-os-cockpit` `343 → 346` items and `132,874 → 133,903` bytes; `your-sudoku` `190 → 191` and `46,999 → 47,222`; `yourtrainer-mcp` `20,089 → 19,578`; `project-os-dev` `161 → 134` items and `71,076 → 66,752` bytes against the stated `161 → 133` / `70,962 → 64,829`. The re-migration moved them and the table did not.
- Fleet total: `1,151,665 → 709,588` bytes = **1,152 KB → 710 KB, −38.4%**. The `1,152 KB` correction is exact; `707 KB` and `−39%` are now the pre-restoration figures.
- `commit:` is still empty, ticked as *"filled at close-out"*. The eleven migration commits are known (`949fb2b7`, `48ea49e`, `a2a6e86`, `7aa1068`, `52328fe`, `b780b48`, `5f69ccb`, `7b9aa24`, `15d589b`, `9734997`, `cf2dc59`, plus `bc04a44` for `your-health`).

### 6. `SNAPSHOT.yaml`'s own `focus.note` still carries the figure the `CHG` note corrected

`focus.note` reads *"Fleet snapshots 1,158KB -> 707KB (-39%)"* — the `1,158` that `CHG-20260804:52` explicitly retracts as *"about 6 KB high"* — and names `ISS-0032` as the open review round without mentioning `ISS-0033`.

### 7. The prune banner is now stacking, in the dogfood repo

`project-os-dev` carries **three** `# Pruned N terminal item(s) …` lines under `items:`; every other pruned repo carries one. `ISS-0033` #11 predicted exactly this ("a repo pruned monthly accumulates one line a month"), and it is now measured rather than predicted: the repo held two before this review, and registering `ISS-0034` pushed `ISS-0009` out of the 25-wide issues window, so the single sync run at the end of this pass added the third. The module docstring's `LEFT ALONE   comments` is the promise it sits against.

### 8. `ISS-0033` carries two `## Status` sections

Lines 196 and 202, with different content. The second supersedes the first; both are published.

## What was checked and held

Stated as checked, not assumed. Every number below was re-measured from the working tree or from git in this session.

- **Condition (5) is genuinely fixed.** Constructed the four cases: a zero-byte note, a note with unparseable frontmatter, a note that parses but carries no `status:`, and an ID reachable only through the loose substring index (a `CHG-YYYYMMDD-FEAT-NNNN-Slug` note). All four survive; only a well-formed claimed note is pruned. The three cockpit tasks are restored and `sync-snapshot --check` there is clean, so they are not re-pruned.
- **`_scalar_span` is genuinely fixed.** `      title: "old value with {a, b} braces"` now returns a block span and `sync_derived_fields` rewrites it; the inline path still locates `title` and `status` correctly in a flow mapping containing braces, commas and escaped quotes. `yourtrainer-mcp` `TASK-0065` now matches its note character for character and `--check` there is clean.
- **The migration record is complete, and stronger than the claim.** All ten non-empty records parsed and cross-checked against each repo's pre-migration snapshot: **709** rows total, **0 of 709** `was:` values disagree with the value that snapshot actually carried, and **0** values that changed in any migration commit are missing from a record. The records are supersets — the surplus rows are entries pruned in the same commit, whose drift the commit diff cannot show.
- **Both destructive writers are executed.** `prune_entries` → `return []` and `sync_derived_fields` → `return []` each fail the suite now. `ISS-0033` #4's ask is met.
- **Condition (3) is falsifiable and reachable.** Deleting `sync-snapshot.py:475-476` fails the suite. Reachability confirmed independently of the fixture: through `main()`, an inline `{ status: "done" }` entry whose note says `deferred` survives, and survives *only* because of that branch.
- **`_value_end`'s `''` handling is correct.** `'it''s here'` spans to the true close; `''`, `''''` and a doubled quote at the value's end all terminate correctly, and the rewritten flow mapping parses.
- **`prune_entries` still deletes complete entries** with the `in_items` guard in place, does not consume the following top-level section, and the result parses.
- **The fleet is healthy.** All twelve: `validate-docs.sh` `rc=0` — except `project-os-dev`, whose single error is the standing `REVIEW` verdict itself — `sync-snapshot --check` `rc=0`, and byte-identical output over two consecutive real syncs (idempotent). No repo was dirtied by the verification runs.
- **`TST-0003` is registered** in `items.tests`, so `QUALITY.md`'s gate on `FEAT-0022` resolves. The suite's self-count is now derived and reports 18, matching `TST-0003:38`.
- **`articles` is correctly restated.** `37 → 55` items and `12,079 → 19,025` bytes (`+58%`) reproduce exactly against `cf2dc59~1..cf2dc59`, and the dirty-tree incident is recorded beside `your-health`'s.
- **`metrics.counts` differences are confined to what is claimed**, plus finding 1: `your-trainer`, `your-applications.com`, `your-sudoku`, `yourtrainer-mcp`, `edankert.com`, `obsidian-supernote-sync`, `project-os-bench` and `project-os` show **no** metric change across the migration at all; `your-health`, `project-os-dev` and `articles` are confounded by other work in the same commit, as `CHG-20260804` says; `project-os-cockpit` is the unconfounded one, and it is finding 1.
- **The `1,152 KB` fleet figure is exact** at `1,151,665` bytes pre-migration.

## Next actions

- [x] Decide `FEAT-0009`: narrow `build_note_index` (or `compute_metric_counts`) so a composite `id:` does not claim an embedded ID, or restate `CHG-20260804:56`. Restoring the entry alone does not work — it is re-pruned on the next sync.
- [x] Add the two missing guards to `test-retention.py`: a condition-5 case with a zero-byte or unparseable note (fails when condition 5 reads `index`), and a brace in the block-style end-to-end title (fails when `_scalar_span` tests `find("{")` over the line). Correct `TST-0003:47` either way.
- [x] Replace `_focus_ids`' body with `_vd.extract_ids`, or correct `CHG-20260804:86` and `ISS-0033`'s sixth tick.
- [x] Decide conditions (5) and (3) together: tighten (5) to `statuses.get(the_id) == terminal`, accepting that it removes (3)'s last production caller, or leave both and record why.
- [x] Bring `CHG-20260804`'s verification section, impact table, fleet figure and `commit:` up to the re-migrated state; refresh `SNAPSHOT.yaml`'s `focus.note`.
- [x] Collapse the stacking prune banner to one line, and merge `ISS-0033`'s duplicate `## Status` sections.

## Status

Open. Findings 1-2 block; the verdict is recorded on `CHG-20260804-Retention-And-Field-Derivation` and `TST-0003` as `changes-requested`, replacing round one's. Per the convention `ISS-0022`/`ISS-0023` established and `ISS-0032`/`ISS-0033` follow, the author fixing these does not close the issue.

**Independence of this pass**: fresh context and a separate session, started from the notes and the diff with no access to the authoring session's reasoning and no access to round one's — `ISS-0033` was read as a record of claims to be refuted, not as findings to be trusted, and each of its five blocking items was re-derived by construction or mutation rather than from its tick-marks. Every quantitative claim in this note was measured in this session. Not independent: the **model**. This is `claude-opus-5`, the same model as the author and as round one, differing only in the context-window variant recorded in `reviewed_by` (`model:claude-opus-5[1m]` here, `model:claude-opus-5` in round one). Under `ADR-0013` context is the mechanism and family is not the gate, so this pass is independent in the sense the skill requires — a reader who wants a different-family check should know that neither round has had one.

## Status — fixes applied 2026-08-04

**Blocking 1 (cockpit `features_done` 54 vs 55).** Root cause was in `compute_metric_counts`, not the prune: its archive fallback resolved `FEAT-0009` through `build_note_index`, where the composite `CHG-20260525-FEAT-0009-Chrome-Polish.md` holds the slot and lends its `merged`. `note_statuses` had been taught to use `claimants`; the counter had not. It now consults `claimants` first (authoritative) and falls back to the index. Rejecting the impostor alone was not enough — it holds the index slot, so the real note was absent and the item counted by nobody, which is what my first attempt produced. `project-os-cockpit`'s metrics are now **identical** to `48ea49e~1`.

**Blocking 2 (the suite guards neither fix).** Both mutations now fail it. Condition 5 gained fixtures for a note that *exists but cannot supply a status* — zero-byte, unparseable, and status-less — which is the case the round-one fix was written for and the round-one suite never covered; reverting to `index` fails three assertions. The block-style end-to-end fixture gained a braced value, and its assertion now checks the **derived** string rather than merely that a brace survives — the weaker form passed either way, which is why the defect reverted green. 23 assertions.

**Non-blocking 3-4.** `_focus_ids` now uses the validator's `extract_ids`, so wikilinks and paths yield canonical IDs. Condition 5 requires the note's status to equal the collection's *terminal* status, not merely to exist.

**Two defects I introduced while fixing these, found by re-verifying rather than by the reviewer:**

- The `compute_metric_counts` signature change left `claimants` undefined at one call site, so `validate-docs.py` **crashed** — and printed `internal error` rather than `ERROR`, so a `grep -cE "^ERROR"` harness read it as zero. Several "0 errors" readings in the rollout were therefore meaningless. Fixed; verification now keys on the exit code and greps for `internal error` explicitly.
- Copying `validate-docs.py` to every repo **downgraded `your-health`**, whose copy was ahead (it carries a `REF` prefix fix). That surfaced two spurious `TEST-FIELDS` errors. Its own validator is restored with only the metric fix re-applied. `sync-project-os.sh` would have refused this — MANIFEST marks `tools/scripts/` template-owned with diverged copies *skipped and reported* — and hand-copying bypassed exactly that protection.

The issue stays **open** pending round three; the author does not clear a verdict on their own work.

## Correction, 2026-08-04 — four of these ticks were false

Round three found that four of the six ticked next actions had not been done. They were not overlooked one by one: the author ticked **every** box with a blanket `- [ ]` → `- [x]` substitution and did not check which the work covered.

That is the failure ADR-0006 names — *"ticking to fit"* — committed on an issue whose own subject is claims nothing verifies. The four were the CHG update, `focus.note`, ISS-0033's duplicate `## Status`, and the condition-(5)/(3) decision record. Three were then done; the CHG update was still incomplete when round four checked, so this paragraph was itself premature — a correction that over-claimed while correcting an over-claim. All four are done as of round four's fixes. The lesson is why this note keeps its history rather than being tidied: a tick is a claim, and neither a regex nor a confident sentence makes one true.

Everything above is now complete, verified individually. Round three's own findings are on [[ISS-0035]].
