---
type: "[[issue]]"
id: ISS-0033
aliases: ["ISS-0033"]
title: "Independent review of the FEAT-0022 implementation: the prune deleted three entries whose notes are zero-byte files, derivation silently stops working for any block-style value containing a brace (live in yourtrainer-mcp today), the migration record is empty in four repos that replaced 45 values, and TST-0003 never executes either destructive writer"
status: open
severity: high
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
component: tooling
source: ["review:2026-08-04-independent-review-FEAT-0022-implementation", "fleet re-measurement 2026-08-04 over 12 repos"]
phase: "[[PHASE-999]]"
parent: ""
related: [FEAT-0022, ADR-0018, ISS-0032, TASK-0082, TASK-0083, TASK-0084, TASK-0085, TST-0003, CHG-20260804-Retention-And-Field-Derivation]
tests: [TST-0003]
---

# Independent review findings on the FEAT-0022 implementation

Clean-context independent review (fresh session, notes + diff only, no access to the authoring session's reasoning) of `tools/scripts/sync-snapshot.py`, `tools/scripts/test-retention.py`, `CHG-20260804-Retention-And-Field-Derivation` and `TST-0003`, per `tools/skills/independent-review/SKILL.md`. This is the **code** review; `ISS-0032` was the planning-note review. Verdict: **changes-requested**.

The design holds and most of the measurement is exact — the item counts and byte sizes in the `CHG` impact table reproduce to the digit for eight of nine migrated repos, the fleet figure is `-39%` on the nose, the `12 VERIFY-WAIVED` / `3 VERIFY` silencing measurement reproduces exactly, all twelve repos are at 0 validator errors, and the surgical updater is idempotent and `--check`-correct in both YAML styles. What does not survive is the claim that **nothing was lost**. Three things were.

## Blocking

### 1. Condition (5) does not check that the note parses, and three entries were deleted whose notes are zero-byte files

`sync-snapshot.py:449` reads `if the_id not in index: continue  # (5) note must exist and parse`. It does not check that the note parses. `build_note_index` indexes a note by its **filename** and stores `{}` when `parse_frontmatter` returns `None`, so a zero-byte file satisfies condition (5).

Three entries were pruned in `project-os-cockpit` (commit `48ea49e`) whose notes are 0 bytes:

- `TASK-0182` → `docs/features/overview-scopes/plan/tasks/TASK-0182-Nest-Children-By-Shared-Phase.md` (0 bytes)
- `TASK-0183` → `docs/features/agent-hooks/plan/tasks/TASK-0183-Revive-Ended-Session-On-Activity.md` (0 bytes)
- `TASK-0187` → `docs/features/embedded-terminal/plan/tasks/TASK-0187-Restart-Console-Action.md` (0 bytes)

The snapshot entry was the only surviving record that these were `done`. `metrics.counts.tasks_done` fell `271 → 268` in the same commit, which is the loss showing up in the numbers.

This is the same population `ISS-0032` finding #5 identified — "3 zero-byte in `project-os-cockpit`" — and the fail-safe written in response was applied to derivation only (`note_fields`, `sync-snapshot.py:274`) and not to the prune, in the exact repo where it was measured. The prune is the destructive half.

Related, same line: condition (5) resolves through the **loose substring index**, not `claimants`. `FEAT-0009` in `project-os-cockpit` satisfied it on the strength of `docs/changes/CHG-20260525-FEAT-0009-Chrome-Polish.md` — the very file `note_statuses`' own docstring (`sync-snapshot.py:190-193`) names as the reason not to use `index` for authority. `metrics.counts.features_done` fell `55 → 54` because `compute_metric_counts` then read `merged` from the change note.

Fix: require the note to actually carry the entry's terminal status — the `statuses` map from `note_statuses` is already computed and already passed into `prunable_ids`.

### 2. `_scalar_span` returns `None` for any block-style value containing `{`, so derivation silently stops and `--check` reports clean

`sync-snapshot.py:123` chooses its parsing branch on `body.find("{") != -1` — a test on the whole line, including the value. A **block-style** line whose value contains a brace takes the inline-flow branch, scans forward from the brace for `key:` at depth 1, finds nothing, and returns `None`. The caller `continue`s. No write, **no change reported, and `--check` exits 0**.

Live today. `yourtrainer-mcp` has `retention.derive_fields: true` and:

```
SNAPSHOT.yaml:159   title: "Activity-file tools accept base64 alongside path … 'exactly one of {path, base64}' canonical shape. Bulk tools …"
note TASK-0065      title: "Activity-file tools accept base64 alongside path (mobile / hosted compatibility) — inspect_activity_file / analyze_ride / analyze_route / adherence_scorecard"
```

`python3 tools/scripts/sync-snapshot.py --check` in that repo prints `up to date` and exits 0.

This is the failure mode the commit message, the module docstring (`sync-snapshot.py:118-120`) and `TST-0003:52` all claim was the reason for writing a scanner: *"a naive regex mis-ends on the 16 titles containing braces"*. The scanner handles braces in **inline** style and breaks in **block** style, and ten of the twelve fleet repos are block style. Once a braced title is derived into a block-style repo it is frozen: the field is never maintained again and nothing reports it.

`git grep -nE '^\s+(title|goal):.*\{' SNAPSHOT.yaml` finds this shape in `project-os-cockpit:1833`, `your-applications.com:808` and `yourtrainer-mcp:159`. The first two are `CHG-*` entries no note claims, so only the third diverges — for now.

### 3. The migration record is empty or short in four of twelve repos, and 45 replaced values were never recorded

`CHG-20260804:70` — *"Nothing is lost. Every replaced `title`/`goal` was written to a per-repo `docs/reference/snapshot-field-migration-2026-08-04.md` **before** derivation overwrote it, so the migration needed no per-item judgement and no similarity test."*

Measured by diffing each migration commit against its parent:

| repo | record says | values actually replaced in that commit | `TASK-0085` drift column |
|---|---:|---:|---:|
| project-os-dev *(dogfood)* | **0** | **24** | 26 |
| articles | **0** | **11** | 3 |
| edankert.com | **0** | **8** | 1 |
| yourtrainer-mcp | 1 | 3 | 3 |
| your-sudoku | 44 | 44 | 29 |
| your-applications.com | 16 | 16 | 26 |
| your-health | 33 | 33 | 17 |
| project-os-cockpit | 126 | 126 | 140 |
| your-trainer | 412 | 412 | 413 |

The five complete records are exact — every `was:` matches the pre-migration snapshot value. The four incomplete ones are consistent with `--record-field-drift` having been run **after** a sync had already written the derived values, i.e. `TASK-0085`'s per-repo step 2 ran out of order. The old values survive in git, but the record is the artefact the whole "no per-item judgement" argument rests on, and it is empty in the repo the rollout order deliberately put first *because* it is the one being watched.

### 4. `TST-0003` never executes either destructive writer

`test-retention.py` exercises `prunable_ids` (a pure predicate) and `_scalar_span` (a pure locator). It never calls `prune_entries`, and the derivation assertion is a *no-change* case that a no-op satisfies. Verified by mutation: replacing the body of `prune_entries` with `return []` **and** the body of `sync_derived_fields` with `return []` leaves the suite green — `test-retention: OK (11 assertions)`.

So an implementation that identifies prunable entries correctly and then never prunes, and never derives anything, passes. `TST-0003:35` opens by saying *"Both are destructive in a way nothing else in the system is — the second deletes lines from a tracked file on every run, in twelve repos"*, and `TST-0003:54-56` discloses only idempotence and metrics parity as gaps. The untested code is the code that deletes.

Individually confirmed unguarded, each mutation surviving the suite: `prune_entries` over-deleting by four columns of indent; `_yaml_quote`'s output written unquoted; the retention window off by one; `PRUNABLE_TERMINAL` widened to `requirements`/`risks`; condition (4) deleted.

### 5. `TST-0003`'s condition-3 fixture does not test condition 3, and the condition is unreachable

`prunable_ids` reaches `if status == "deferred"` (`sync-snapshot.py:443`) only after `if status != terminal: continue`, and no member of `PRUNABLE_TERMINAL` is `deferred`. The branch cannot execute.

`test-retention.py:92-100` sets `status: deferred` in both the entry and the note, and `TST-0003:24` describes this as *"a deliberately illegal entry that is both `done` and `deferred`"*. It is not illegal — it is an ordinary deferred entry, rejected by condition (1). Deleting `sync-snapshot.py:443-444` entirely leaves the suite green.

`ISS-0032` finding #6 already reported *"the condition-3 inversion test cannot fail"*. The response documented the difficulty in `TASK-0082`'s verification section rather than resolving it, and the test written afterwards still cannot fail. Either make the fixture actually illegal (terminal status in the entry, `deferred` in the note, so `sync_statuses` is bypassed) or drop the branch and the assertion.

## Non-blocking

### 6. `articles` was not "unchanged", and it is a second undisclosed dirty-tree incident

`CHG-20260804:48` lists `articles` among the repos that were *"unchanged — everything inside the window"*. Commit `cf2dc59` in that repo grew its snapshot **37 → 55 items** and **12,079 → 19,025 bytes (+58%)**, sweeping in 18 item entries (`FEAT-0012`, `FEAT-0013`, `ISS-0001`, `ISS-0002`, `TASK-0021..0032`, two `CHG-*`) plus a rewritten `focus` and five counter bumps that were sitting uncommitted in the working tree.

This is the same failure the `Provenance note: your-health` section records — a dirty tree at migration time — occurring in a second repo, in the migration's own commit, and it is not recorded. It also explains the fleet total: the author's `3,164 items` counts `articles` at 55; the pre-migration parents sum to `3,146`.

### 7. `metrics.counts` was not identical before and after in `project-os-cockpit`

`CHG-20260804:52` claims `metrics.counts` byte-identical before and after in every repo. It holds in 8 of 12. `project-os-dev`, `your-health` and `articles` are confounded by other work in the same commit. `project-os-cockpit` is not: its commit touches only the four migration files, and `features_done: 55 → 54`, `tasks_done: 271 → 268`. That delta is finding #1 showing through.

### 8. `_value_end` mishandles the YAML `''` escape, producing an unparseable snapshot

`sync-snapshot.py:161-170` handles `\"` inside double quotes and nothing inside single quotes, so `'it''s here'` ends at `'it'`. Rewriting then yields:

```
    TASK-0001: { title: "New"'s here', status: done }
```

which `yaml.safe_load` rejects with *"while parsing a flow mapping"*. No fleet snapshot carries a single-quoted `title`/`goal` today, so this is latent — but `_yaml_quote` is not the only thing that ever writes these lines, and a hand-edit is all it takes.

### 9. An inline entry with a trailing comment makes the previous entry's title overwrite it

`_ITEM_RE` (`sync-snapshot.py:90`) requires `\{.*\}\s*$`, so `TASK-0002: { … }  # curated` does not match. In `sync_derived_fields` the line then falls through with `current_id` still pointing at the **previous** entry, and that entry's title is written onto this one:

```
in    TASK-0001: { status: done, title: "one" }
      TASK-0002: { status: done, title: "two" }  # curated comment
out   TASK-0001: { status: done, title: "ONE-NEW" }
      TASK-0002: { status: done, title: "ONE-NEW" }  # curated comment
```

The result parses, so nothing catches it. Latent — no fleet snapshot has this shape — but `sync_statuses` is immune to it by construction and `sync_derived_fields` is not, which is the asymmetry to fix. Same root cause: quoted or otherwise non-conforming entry keys behave the same way.

### 10. Condition (4) protects only exact-match top-level focus strings

`sync-snapshot.py:423-424` collects `focus` values that `isinstance(v, str)` and compares by whole-string equality. Consequences:

- `your-applications.com` and `yourtrainer-mcp` nest their focus under `focus.bundled_launch` / sub-mappings; **no** ID in either is protected.
- IDs named inside `focus.note` prose are unprotected. `your-sudoku`'s `ISS-0068` is named in `focus.note` and was pruned by `7aa1068`.

`extract_ids` and a recursive walk are the existing convention for this everywhere else in the validator. Condition (4) is also the one prune condition `TST-0003` does not invert, and deleting it leaves the suite green — while `TST-0003:39` and `CHG-20260804:64` both say *every* condition is inverted.

### 11. `prune_entries` deletes comments and blank lines, and stacks a banner per run

The module docstring (`sync-snapshot.py:31`) promises `LEFT ALONE   comments, ordering, item-level note: prose …`, and cites *"~80 lines of hand-written comments with no frontmatter home"* as the reason a generator was rejected. The skip loop (`sync-snapshot.py:491-495`) treats any line indented deeper than the pruned key as part of the entry, so a comment attached to nothing and any blank line following a pruned entry are deleted with it.

Separately, `sync-snapshot.py:498-503` inserts a fresh `# Pruned N terminal item(s) …` line under `items:` on **every** run that prunes anything. Each repo has one today; a repo pruned monthly accumulates one line a month.

### 12. `_owes_verification` fails open on a missing test note

`sync-snapshot.py:417` — `statuses.get(t, "passing") != "passing"` — treats a linked test whose note does not exist as passing, so the entry is prunable and whatever the validator would have said about the dangling link goes with it. Every other doubt in `prunable_ids` resolves to *keep*.

### 13. `prune_entries` has no `in_items` guard

`sync_statuses` and `sync_derived_fields` both track `in_items`; `prune_entries` matches `_ITEM_RE` anywhere in the file. No fleet snapshot has an ID-shaped key outside `items:` (checked, all twelve), so this is latent, but it is the only one of the three walkers that would delete from another section.

### 14. `TST-0003` is not registered in `SNAPSHOT.yaml`, and the suite miscounts itself

`items.tests` in `project-os-dev` holds `TST-0001` and `TST-0002` only. `FEAT-0022` is `done` with `tests: ["[[TST-0003]]"]` in its note, and `QUALITY.md`'s verification gate resolves through the snapshot, so the gate that should hold `FEAT-0022` is not reachable. `--report-unregistered` lists it.

`test-retention.py` runs 12 `check()` calls and prints `OK (11 assertions)`; `TST-0003:37` says 11.

### 15. `CHG-20260804`'s `commit:` field is empty

The note devotes a section to the provenance of the commits that carry this change, and records none of them in its own `commit:` field.

## What was checked and held

Stated as checked, not assumed:

- **Idempotence** — independently reproduced in `project-os-dev` (block style, 0 inline entries), `your-trainer` (409 inline flow entries) and `your-sudoku` (134): first run writes nothing, second run writes nothing, file hash unchanged.
- **`--check` semantics** — exits 0 on each synced tree; exits 1 after perturbing a snapshot `title` and again after perturbing a note `status`; exits 0 again after repair. Verified in both YAML styles.
- **No validator check silenced** — the current validator run against the pre-prune and post-prune snapshot in the same tree produces **byte-identical output** in `your-trainer`, and in `project-os-cockpit` differs only in `PATH-ALIAS`' aggregate count (`403 → 168`, entries that no longer exist). No warning code, and no individual warning, disappeared. This was the change's biggest risk and the mitigation works.
- **The holds are load-bearing, at exactly the measured size** — replaying the migration on the pre-migration snapshots with `_owes_verification` stubbed to `False` silences **12 `VERIFY-WAIVED`** in `project-os-dev` and **3 `VERIFY`** in `your-trainer`, reproducing `CHG-20260804:56` to the count. (`your-trainer` also loses 3 `VERIFY-WAIVED`, which the note does not claim.)
- **0 validator errors in all twelve repos**, today, `rc=0` each.
- **Fleet size claims** — `-39%` exact (1,151,665 → 706,995 bytes; the note's `707 KB` is exact at KB=1000, its `1,158 KB` is ~6 KB high). `your-trainer` `1,065 → 412` items and `-71%` exact. Every other row of the impact table reproduces exactly except `project-os-dev`, measured at `71,076 → 64,900` against the note's `70,962 → 64,829`.
- **Corpus statistics** — `16` pre-migration snapshot titles contain braces and `3` contain a double quote: both exact. `3` zero-byte notes fleet-wide: exact.
- **The scanner does what it claims within inline flow style** — titles containing commas, braces, escaped double quotes, non-ASCII, a `title:` substring inside another value, a `subtitle:` key, `tests: [...]` lists and nested flow sequences all locate correctly; `_yaml_quote`'s output round-trips.
- **Fail-safe on derivation** — a missing, zero-byte, unparseable, ambiguously-claimed or title-less note leaves the snapshot value alone. Confirmed by mutation: making `note_fields` accept blank values fails the suite.
- **Counters only rise**; `sync_counters` and `sync_metrics` were not disturbed by this change.
- **`prune_entries` boundaries** — a pruned last entry does not consume the following collection header or top-level section; a comment at entry indent survives; the emitted YAML parses in every shape tried.
- **No ID-shaped key outside `items:`**, and no non-numeric key in `tasks`/`issues`/`features`, in any of the twelve — so the `_key` fallback and the missing `in_items` guard are latent only.
- **The three `keep_*` flags are gone** from every repo.

## Next actions

- [x] Make condition (5) require the note to supply the entry's terminal status, via `statuses`/`claimants` rather than the loose `index`. Restore `TASK-0182`/`TASK-0183`/`TASK-0187`/`FEAT-0009` in `project-os-cockpit`, or write their status into the three zero-byte notes. — condition 5 now tests `the_id not in statuses`, which requires a single claimant with a parseable non-empty status; all three tasks restored from `48ea49e~1`, `tasks_done` back to 271; the fixed script re-run does not re-prune them
- [x] Fix `_scalar_span`'s branch selection: decide block vs inline from the position of the first `{` relative to `key:`, not from its presence anywhere on the line. Re-run derivation fleet-wide afterwards; `yourtrainer-mcp` `TASK-0065` is currently diverged and invisible. — the block pattern is now tried FIRST and the inline scan is the fallback; derivation re-run in all twelve
- [x] Re-run `--record-field-drift` against the pre-migration snapshots for `project-os-dev`, `articles`, `edankert.com` and `yourtrainer-mcp` and commit the real records, or restate `CHG-20260804:70`. — all ten records reconstructed from each repo's pre-migration parent against current note titles — 709 values total, matching the measured drift; the earlier under-count came from the rollout re-running the recorder after migrating
- [x] Add assertions that execute `prune_entries` and the write path of `sync_derived_fields` — at minimum: an entry is removed and its neighbours, comments and blank lines are not; a derived value is written, quoted, and re-reads equal. — six end-to-end assertions added driving both writers; stubbing either to return [] now fails the suite
- [x] Make the condition-3 fixture actually illegal, or delete `sync-snapshot.py:443-444` and the assertion together. — fixture is now terminal-in-entry + deferred-in-note, and the check consults BOTH sources so it is reachable; deleting it fails the suite
- [x] Invert condition (4), and widen the focus scan to a recursive `extract_ids` walk. — focus scan is now a recursive walk collecting every ID-shaped token at any depth, including prose; `your-sudoku` ISS-0068 restored and protected
- [x] Handle `''` in `_value_end`; make `_ITEM_RE` tolerate a trailing comment, or have `sync_derived_fields` clear `current_id` on any unrecognised line at entry indent. — doubled single-quote escape handled; `prune_entries` also gained the `items:` scoping guard its siblings had
- [x] Record the `articles` dirty-tree incident alongside `your-health`; correct the "unchanged" row and the `metrics.counts` claim for `project-os-cockpit`. — CHG note now carries both incidents, the 37->55 articles row, and states plainly that metrics were NOT identical everywhere
- [x] Register `TST-0003` in `SNAPSHOT.yaml`; fix the assertion count in `test-retention.py:137` and `TST-0003:37`; fill `CHG-20260804`'s `commit:`. — registered; the count is now derived from a counter rather than hard-coded (18); commit: filled at close-out

## Status

Open. Findings 1-5 block; the review verdict is recorded on `CHG-20260804-Retention-And-Field-Derivation` and `TST-0003` as `changes-requested`. Per the convention `ISS-0022`/`ISS-0023` established and `ISS-0032` follows, the author fixing these does not close the issue — a fresh clean-context round settles whether the fixes hold.

**Independence of this pass**: fresh context and a separate session, working from the notes and the diff with no access to the authoring session's reasoning; every quantitative claim re-measured from git rather than read from the notes. Same model family as the author (`model:claude-opus-5`), recorded in `reviewed_by`. Under `ADR-0013` context is the mechanism and family is not the gate, so this pass is independent in the sense the skill requires — but a reader who wants a different-family check should know it has not had one.


All findings addressed by the authoring session on 2026-08-04, including the two that caused real damage (three entries deleted against zero-byte notes; derivation silently dead in block style). The issue stays **open**: the author does not clear the verdict on their own work, and `TST-0003` currently fails the `REVIEW` gate as an error precisely because that verdict still says `changes-requested` — which is the gate working. A fresh clean-context round settles it.
