---
type: "[[plan]]"
status: done
parent: "[[FEAT-0014-Single-State-Contract]]"
implements: [REQ-0018]
related: []
---

# Plan: Single state contract

All three tasks land in `~/Dev/repos/project-os` (template) and propagate by sync.

- [ ] [[TASK-0057-Author-States-Contract|TASK-0057]] — author STATES.md (values, gates, and *who writes the value* per type)
- [ ] [[TASK-0058-Strip-Restatements|TASK-0058]] — replace restatements with links across 6 files; fixes ISS-0006
- [ ] [[TASK-0059-Adapter-Regeneration|TASK-0059]] — regenerate adapters, verify no tool-facing copy survives

## Dependencies

- **Hard:** TASK-0057 blocks TASK-0058 (nothing to link to until the contract exists); TASK-0058 blocks TASK-0059.
- **Soft:** this feature is best sequenced **last** among the five, so the contract is authored once against the final vocabulary (FEAT-0013), the final authorship model (FEAT-0015), and the final verification rules (FEAT-0016) — rather than being written and then rewritten four times.

## Open questions

- Does `STATES.md` replace `STATUSES.md` outright, or absorb it and leave a stub? A rename breaks inbound links in nine downstream repos and in every generated adapter; absorbing under the existing filename is cheaper but leaves a name that undersells the file's new scope.
- Should `ISS-0006` be fixed immediately as a one-line correction, or wait for TASK-0058 to delete the sentence entirely? Immediate correction is near-zero risk and stops ten repos acting on a reverted rule in the meantime; the deletion still happens later. Recommended: fix now, delete later.
