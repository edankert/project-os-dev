---
type: "[[issue]]"
id: ISS-0004
aliases: ["ISS-0004"]
title: "Requirements freeze at draft/approved while their features ship: no lifecycle step ever advances them and acceptance criteria go stale"
status: fixed
severity: high
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
component: lifecycle-rules
source: []
related: [FEAT-0012]
tasks: []
---

# Requirements never advance

## Description

No step anywhere in the lifecycle touches a requirement after it is created. Features close; their requirements freeze. Evidence in this repo before the fix (12 pre-existing requirements, every one behind its features):

- REQ-0001..REQ-0009 sit at `approved` although all their implementing features (FEAT-0001..0006, FEAT-0010) are `done`.
- REQ-0010, REQ-0011, REQ-0012 sit at **`draft`** — never even approved — although FEAT-0007/0008/0009 were implemented against them and closed.
- 36 acceptance checkboxes across six notes are unticked; only REQ-0013 (created 2026-07-21) reached `implemented`, and only by hand.

Three root causes:

1. **Close-out is requirement-blind.** `close-out/SKILL.md` updates task, issue, feature, and phase statuses. Requirements appear only in the verification-gating step, which *blocks* `verified` without passing tests. The path `draft → approved → implemented → verified` exists in `STATUSES.md`, but no skill walks it, and nothing ever sets `implemented` ("built but not yet formally verified") — the status designed for exactly this state.
2. **No mechanical check.** `validate-docs.py` treats a `draft` requirement whose features are all `done` as clean. This is the same convention-decay failure the deferral work (FEAT-0011) fixed one link lower in the graph: task→feature completeness is now enforced, feature→requirement is not.
3. **Stale criteria, not just unticked boxes.** Several criteria describe designs the project later walked away from, so they cannot honestly be ticked:
   - REQ-0010 requires "feature frontmatter no longer contains `tasks`/`requirements`/`tests` lists" — features *do* carry `tasks:` today, and FEAT-0011's deferral enforcement is built on that list being the scope of record.
   - REQ-0011 specifies phase statuses `draft/active/completed`; the shipped taxonomy is `planned/active/done/deferred`.
   - REQ-0012 requires removing `feature-overview.base` (done via TASK-0038) but also criteria about `Overview.base` embedding that the cockpit layout superseded.
   - Duplication drift: frontmatter `acceptance:` and body checkboxes state different criteria in the same note (REQ-0010: 5 vs 8) with no rule about which is canonical.

## Impact

- Requirement status carries no information: everything reads `approved`/`draft` regardless of whether it shipped, so nothing can be filtered on "what still needs building" or "what needs verifying".
- Stale criteria silently misrepresent the system's own contract — a reader following REQ-0010 would implement against a model the project abandoned.
- `verified` is unreachable in practice (no `TST-*` notes here), so without `implemented` there is no honest terminal-ish state for delivered requirements.

## Action Required

Fix via [[FEAT-0012-Requirement-Lifecycle-Closure|FEAT-0012]] per [[ADR-0006-Requirement-Advancement-On-Evidence|ADR-0006]]: close-out advances requirements on evidence, feature-scaffold blocks implementing against `draft` requirements, the validator makes stale requirements a build failure (REQ-STALE, with REQ-PREMATURE and REQ-BOXES as warnings), and the 12 existing requirements are backfilled with criteria reconciled.
