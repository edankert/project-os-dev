---
type: "[[test]]"
id: TST-0003
aliases: ["TST-0003"]
title: "Retention and derivation invariants: every prune condition holds an entry back, and derivation never blanks a title"
status: active
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["FEAT-0022", "ADR-0018", "ISS-0032"]
scope: system
level: unit
entrypoint: "tools/scripts/test-retention.py"
command: "python3 tools/scripts/test-retention.py"
requirements: []
features: [FEAT-0022]
issues: []
tasks: [TASK-0082, TASK-0083]
artifacts: []
evidence: []
adequacy: "Verified by mutation across five review rounds; ten independent breaks now caught. The first two versions of this suite were inadequate and review proved it each time. v1 exercised neither destructive writer — stubbing `prune_entries` and `sync_derived_fields` to `return []` left it green. v2 fixed that but still guarded neither of round one's fixes: its condition-5 fixture used a MISSING note, which a bare index test rejects identically, and its block-derivation assertion checked only that a brace survived, which holds whether or not derivation ran. v3 adds zero-byte, unparseable and status-less note fixtures (reverting condition 5 fails 4 assertions) and asserts the DERIVED string in the braced block case (reverting `_scalar_span` fails 2). Caught: writers stubbed out; condition 5 reverted; `_scalar_span` reverted; the verification hold deleted; blank titles accepted; the scanner replaced with a comma search. Measured coverage, recorded rather than hidden: **10 of 22** mutations are caught. Reverting condition 5 to the looser `the_id not in statuses` IS caught — it fails `cond3 deferred survives`, which an earlier draft of this line wrongly listed as an uncovered gap. Genuinely uncovered: condition 1, condition 4 (`focus`), the blank/non-string title fail-safe, the fail-open `_owes_verification`, the focus scan, the `in_items` guard, doubled-quote handling, a widened `PRUNABLE_TERMINAL`, a 4-column over-delete, the banner, and the ambiguous-claim guard. `compute_metric_counts` has no test at all."
related: [ADR-0018, ADR-0010, ADR-0005, ISS-0033, ISS-0034, ISS-0035, ISS-0036, ISS-0037, ISS-0038, ISS-0039]
reviewed_by: "model:claude-opus-5[1m]"
review_date: 2026-08-04
review_verdict: approved
review_note: "Round-EIGHT clean-context review (fresh session, no memory of authoring; same model family as the author, recorded here as provenance per ADR-0013). APPROVED. Round seven's sole blocking item is genuinely fixed and the fix introduced no new error. I inherited nothing from rounds four to seven and re-derived every property by running code, with `python3 -B` throughout. Skip set measured from scratch, loading each repo's OWN sync-snapshot.py and asking note_fields what it supplies for every id registered under items.*: 203 = 200 CHG-* + 3 TASK, and I decomposed it by CAUSE rather than by prefix — 200 have no claimant at all, 3 are claimed by a zero-byte note, and the 'claimed, parses, no usable title' bucket is EMPTY. Those 3 are cockpit TASK-0182/0183/0187, which are the only zero-byte .md files under docs/ in all twelve. The 14 PyYAML-rejecting files are real at exactly 8 your-trainer / 5 your-health / 1 your-applications.com and all 14 supply titles through the parse_yaml_subset fallback, REQ-0024 included. ':51 and ':53 are accurate; all four surfaces (CHG:57, TST:51, sync-snapshot.py:270-275, test-retention.py:134-136) now agree and all four are correct against measurement; no stale '17'/'seventeen' survives anywhere except the sentence that explicitly retracts it. The adequacy line's '10 of 22' is CONFIRMED and I reached it exactly: my own 22 score 9 caught / 13 survived, and the single gap is my formulation of the blank-title mutation — written the way this note describes it ('a missing title written through as an empty string') it IS caught, by exactly 2 assertions, giving 10 caught / 12 survived. Every per-assertion count stated here is exact: reverting condition 5 fails 4 (cond3 plus all three cond5b fixtures), reverting _scalar_span fails 2, the blank title fails 2. All twelve named survivors individually confirmed to survive; a naive quoted-regex scanner also survives while the comma search is caught, exactly as claimed. 23 assertions green in all twelve repos; both destructive writers execute end to end (stubbing prune_entries fails 1, stubbing sync_derived_fields fails 4). Non-blocking, recorded not blocked: test-retention.py:134's '3 real notes are in this state fleet-wide' is exact for REGISTERED entries — the population derivation touches — but 6 singly-claimed notes fleet-wide supply no usable title; the other 3 (your-trainer TASK-0045, your-sudoku ISS-0010/ISS-0012) are unregistered and statusless, so derivation never sees them, and 'registered' would make the sentence exactly true. Condition (4) still has no fixture and the note says so; condition (1) deleted survives; nothing tests compute_metric_counts. Everything else about this suite held under attack." replaces round six's verdict, which carried the same reviewed_by string — review_date and this note distinguish the rounds. ':51 is now CORRECT and I confirmed it by measurement, not by reading: loading each repo's own sync-snapshot.py and asking note_fields what it supplies for every id registered under items.*, the fleet skip set is 203 = 200 CHG-* + 3 TASK, and those 3 are cockpit TASK-0182/0183/0187, which are the only 3 zero-byte .md files under docs/ in all twelve repos. Both retracted readings are independently refuted: the 14 PyYAML-rejecting files (exactly 8 your-trainer / 5 your-health / 1 your-applications.com) ALL supply titles through load_yaml's parse_yaml_subset fallback, 14 of 14, and your-health's SNAPSHOT:1506 carries the derived REQ-0024 title today; the 14 your-health REF-* entries are registered and none appears in that repo's 39-entry skip set, which is all CHG-*. ':53 is accurate. The adequacy line's '10 of 22' is CONFIRMED: my own 22 score 8 caught / 14 survived, and the gap is my formulations, not the suite — written the way this note describes them, prune_entries stubbed to return [] is caught, a missing title written through as an empty string is caught (2 assertions, exactly as stated), and the scanner-as-comma-search is caught under both natural formulations, which substituted for two survivors gives exactly 10/12. All twelve named survivors individually confirmed to survive; all named catches confirmed caught. 23 assertions green in all twelve repos; both destructive writers execute end to end. What blocks is ONE line, and it is not in this note: test-retention.py:133-136, the fourth of the four surfaces round six named, kept the stale number while dropping the decomposition — it now reads '17 real notes are in this state fleet-wide, all zero-byte', asserting 17 zero-byte notes where 3 exist. That is strictly worse than the text it replaced, which at least named two populations a reader could check. No measurement in the fleet yields 17 (3 zero-byte; 203 skipped entries; 567 of 5,087 docs/ files carry no usable title, 370 of those with an id). Replace '17 real notes' with '3'. Method note for the next reviewer: importlib reuses __pycache__ bytecode keyed on mtime+size, so equal-length mutations can run each other's code — run the suite with -B. Recorded not blocked: condition (4) still has no fixture and the note says so; condition (1) deleted survives; nothing tests compute_metric_counts. Everything else about this suite held under attack."
---

# Retention and derivation invariants

## What it guards

`sync-snapshot.py` gained two powers under [[ADR-0018-What-The-Generator-Owns|ADR-0018]]: it derives `title`/`goal` from the note, and it removes terminal entries. Both are destructive in a way nothing else in the system is — the second deletes lines from a tracked file on every run, in twelve repos.

## Assertions (23)

**Prune conditions, each inverted** — the entry must survive when the condition is violated:

| condition | assertion |
|---|---|
| 1 terminal only | a `backlog` entry survives |
| 2 retention window | an entry inside the window survives |
| 3 never deferred | a `deferred` note is never pruned — asserted as an **outcome**, since (5) now provides the protection structurally and a separate condition would be unreachable |
| 5 note must supply the terminal status | four fixtures: **no note**, **zero-byte**, **unparseable frontmatter**, and **parses but has no `status:`**. Checking mere index membership deleted three real entries; the first suite covered only the no-note case, so reverting the fix stayed green |
| 6 `note:` holds | an entry with `note:` prose survives — **and clearing it releases the hold**, so the hold is provably a backlog rather than an exemption |
| 7 verification owed | an entry with a `verification_waiver` survives |

**Derivation fail-safe** — a note supplying no usable title leaves the snapshot value untouched rather than blanking it, and reports no change. Derivation skips **203** registered entries fleet-wide, and the composition was mis-stated for three review rounds before measurement settled it. **200** are `CHG-*` entries that no note claims by ID, because change notes are keyed by date-slug rather than a numeric one. The other **3** are `project-os-cockpit`'s zero-byte notes (`TASK-0182/0183/0187`), which is the whole population that genuinely cannot supply a title.

Earlier drafts said "seventeen files", counting 14 whose frontmatter PyYAML rejects. That was wrong: `load_yaml` falls back to `parse_yaml_subset`, so all 14 *do* supply titles — `your-health`'s `REQ-0024` derives "AI Coach: chat-based training recommendations" today. A review round proposed a different fourteen (`your-health` `REF-0001..REF-0014`, unclaimed because `REF` is absent from `ID_PREFIXES`); measurement refuted that too — all 14 are supplied. Both the claim and its correction were wrong, in opposite directions, and only running the code decided it.

**Scanner** — a title containing commas, braces and escaped double quotes round-trips through an inline flow mapping. The fleet has 16 titles with braces and 3 with embedded quotes; a regex-based reader corrupts them.

**End-to-end through both writers** — derivation rewrites a value, a **braced block-style** value is derived (the case that made the scanner fix necessary, asserted on the derived string rather than on the brace surviving), the prune removes an entry, the untouched entry survives, the result parses, and no over-deletion reaches `counters:`/`metrics:`. Added after review found the suite passed against writers that did nothing.

## What it does not cover

Idempotence and metrics parity are asserted during the rollout against real repos rather than here (`TASK-0085`), because both need a full corpus to be meaningful. Recorded so the gap is visible: this suite would pass against an implementation that pruned correctly but non-idempotently.
