---
type: "[[test]]"
id: TST-0003
aliases: ["TST-0003"]
title: "Retention and derivation invariants: every prune condition holds an entry back, and derivation never blanks a title"
status: passing
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["FEAT-0022", "ADR-0018", "ISS-0032"]
scope: system
kind: automated
level: unit
entrypoint: "tools/scripts/test-retention.py"
command: "python3 tools/scripts/test-retention.py"
last_run: "2026-08-04T10:05Z"
exit_code: 0
requirements: []
features: [FEAT-0022]
issues: []
tasks: [TASK-0082, TASK-0083]
artifacts: []
evidence: []
adequacy: "Verified by mutation on 2026-08-04, three independent breaks each caught: (1) deleting the verification hold — caught by `cond7 waiver holds`; (2) accepting blank note titles in the derivation fail-safe — caught by the titleless-note assertion; (3) replacing the flow-scalar scanner with a naive comma search — caught by `scanner round-trips a hostile title`, which returned a truncated, corrupted string. The suite is an INVERSION suite: each condition is violated in turn and the entry must survive, because a happy-path-only test cannot distinguish a working rule from a missing one. Condition 3 (deferred) is asserted against a deliberately illegal entry that is both `done` and `deferred`, since the two are mutually exclusive in STATUSES.md and a well-formed corpus therefore cannot violate condition 3 alone — an implementation omitting the deferred check entirely would pass a naive suite."
related: [ADR-0018, ADR-0010, ADR-0005]
reviewed_by: ""
review_date: ""
review_verdict: ""
---

# Retention and derivation invariants

## What it guards

`sync-snapshot.py` gained two powers under [[ADR-0018-What-The-Generator-Owns|ADR-0018]]: it derives `title`/`goal` from the note, and it removes terminal entries. Both are destructive in a way nothing else in the system is — the second deletes lines from a tracked file on every run, in twelve repos.

## Assertions (11)

**Prune conditions, each inverted** — the entry must survive when the condition is violated:

| condition | assertion |
|---|---|
| 1 terminal only | a `backlog` entry survives |
| 2 retention window | an entry inside the window survives |
| 3 never deferred | a `deferred` entry survives (illegal fixture; see `adequacy`) |
| 5 note must exist | an entry with no note survives |
| 6 `note:` holds | an entry with `note:` prose survives — **and clearing it releases the hold**, so the hold is provably a backlog rather than an exemption |
| 7 verification owed | an entry with a `verification_waiver` survives |

**Derivation fail-safe** — a note supplying no usable title leaves the snapshot value untouched rather than blanking it, and reports no change. Seventeen real notes fleet-wide are in that state (3 zero-byte, 14 with unparseable frontmatter), plus 161 `CHG-*` entries no note claims by ID.

**Scanner** — a title containing commas, braces and escaped double quotes round-trips through an inline flow mapping. The fleet has 16 titles with braces and 3 with embedded quotes; a regex-based reader corrupts them.

## What it does not cover

Idempotence and metrics parity are asserted during the rollout against real repos rather than here (`TASK-0085`), because both need a full corpus to be meaningful. Recorded so the gap is visible: this suite would pass against an implementation that pruned correctly but non-idempotently.
