---
type: "[[requirement]]"
id: REQ-0015
aliases: ["REQ-0015"]
title: "Relationship model: scalar parent downward, implements upward, feature child lists as scope of record"
status: implemented
phase: []
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
source: []
priority: high
scope: "template-wide"
acceptance:
  - "Tasks and issues declare exactly one scalar parent (feature or issue); deferred tasks are the sole exception, using origin plus a forward home while parked"
  - "Requirements and plans link upward to the features that implement them via an implements list"
  - "Feature notes carry tasks, requirements and tests lists; the tasks list is the feature's scope of record for completeness checks"
  - "Tests link outward to the items they verify via separate requirements, features, issues and tasks lists"
  - "Bases surface relationships through the field-agnostic link graph (file.hasLink) rather than per-field contains filters"
  - "The validator enforces link-graph integrity over these fields, including parent, tasks, implements, supersedes/superseded, origin and deferred"
supersedes: "[[REQ-0010-Named-Relationship-Fields]]"
implements: ["[[FEAT-0007-Relationship-Model]]", "[[FEAT-0011-Deferral-Descoping]]"]
verifies: []
related: [REQ-0010, REQ-0013, ISS-0004]
tests: []
---

# Relationship model (as shipped)

## Statement

Notes must express relationships through a small, fixed set of fields: a single scalar `parent` pointing downward from task/issue to its owner, `implements` lists pointing upward from requirements and plans to features, and child lists (`tasks`, `requirements`, `tests`) on features. A feature's `tasks:` list is its **scope of record** — completeness, deferral, and close-out all key off it. Relationship browsing is served by the generic link graph, not by per-field filters.

This requirement replaces [[REQ-0010-Named-Relationship-Fields|REQ-0010]], whose semantic-named-field design was built and then reverted in May 2026. It documents what the system actually runs on, so the model has a live specification rather than only an abandoned one.

## Acceptance Criteria

- [x] Scalar `parent` on tasks and issues, with the deferred exception — evidence: `docs/__templates__/task.md`, `issue.md` (`parent: ""`); `tools/instructions/TRACEABILITY.md` "Must have exactly one `parent`" plus the deferred exception (`origin` + `phase` replace it while parked, per [[REQ-0013-Deferral-Semantics|REQ-0013]]).
- [x] `implements` lists upward on requirements and plans — evidence: `docs/__templates__/requirement.md`, `plan.md`; `SCHEMAS.md` ("names the features that implement *this requirement*").
- [x] Feature child lists, with `tasks:` as scope of record — evidence: `docs/__templates__/feature.md` (`requirements`, `tasks`, `tests`); `SCHEMAS.md` ("the feature's **current scope**"); enforced by `validate-docs.py` VERIFY (every listed task `done`/`cancelled`) and DEFER-SCOPE.
- [x] Tests link outward via separate lists — evidence: `docs/__templates__/test.md` (`requirements`, `features`, `issues`, `tasks`); `SCHEMAS.md`.
- [x] Bases use the field-agnostic link graph — evidence: `docs/__bases__/CONTEXT.base` `file.hasLink(this.file)`; `NAVIGATION.base` filters on `type`/`status` and groups by `parent`.
- [x] Validator enforces link-graph integrity over these fields — evidence: `RELATIONSHIP_FIELDS` in `tools/scripts/validate-docs.py` includes `parent`, `tasks`, `requirements`, `tests`, `implements`, `supersedes`, `superseded`, `origin` and `deferred`; a LINK error fires for any unresolvable reference in either a snapshot entry or note frontmatter (fixture-verified against a dangling `implements` target).

## Rationale for the shipped model over REQ-0010's

- **Single parent beats multi-parent** for mechanical completeness: "everything in `tasks:` must be resolved" is checkable in one pass; multi-parent scope would need reference counting.
- **Feature child lists were re-added deliberately** and are now depended on by [[FEAT-0011-Deferral-Descoping|FEAT-0011]]: without `tasks:` there is no scope to descope *from*.
- **One generic link-graph filter beats five per-field filters** in Bases: it keeps working when fields are added, and it was the change that let the per-feature/per-phase `.base` proliferation be deleted.

## Traceability

- Implements: [[FEAT-0007-Relationship-Model]], [[FEAT-0011-Deferral-Descoping]]
- Supersedes: [[REQ-0010-Named-Relationship-Fields]]
- Verified by: `tools/scripts/validate-docs.py` (LINK, VERIFY, DEFER-* checks)
