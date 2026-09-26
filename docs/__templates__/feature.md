---
type: "[[feature]]"
id: FEAT-0000
title: ""
status: backlog
phase:
owner: unassigned
created: 2026-01-26
updated: 2026-01-26
source: []
goal: ""
requirements: []
tasks: []
release: ""
acceptance_exception: ""   # leave empty and write the check; fill only where a check can never exist (SCHEMAS.md, feature.md)
# Optional acceptance gate (FEAT-0064). Absent = no gate, which is the
# default and stays the default: a mandatory gate on the one unautomatable
# judgment becomes a rubber stamp. `requested` is stamped at CLOSE-OUT by the
# agent when the feature opted in — the agent asks, it never answers.
# `accepted` is written only by a completed acceptance run (REQ-0028).
# The validator's ACCEPT-STALE warns when a `done` feature has been asking
# for acceptance too long.
acceptance: ""
# Optional design gate (FEAT-0070). Names the `[[design]]` this feature is
# built against. DESIGN-GATE warns — never blocks — when the feature has left
# the pending band while that design was never accepted.
design: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
review_round: ""
related: []
---

# <Feature>

<!-- This note says what is true now. When the feature changes, rewrite the section that changed; the history goes in the change note and the commit message, not in dated sections here (tools/instructions/WRITING.md, rule 11). -->

## Goal
<Two or three sentences, point first: what capability is delivered and for whom. The detail goes under Scope.>

## Scope
<In/out of scope>

## Acceptance
- <observable criteria, each a claim a reviewer can refute; the review packet copies them word for word>

## Verification
<Before the review: the full test command, the date and the result count, e.g. `pytest`, 2026-09-18: 412 passed.>

## Links
- Requirements: use `[[REQ-####-...]]` links
- Tasks: use `[[TASK-####-...]]` links
- Workflows/Repo paths: <links>
