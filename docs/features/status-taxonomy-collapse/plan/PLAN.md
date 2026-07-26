---
type: "[[plan]]"
status: done
parent: "[[FEAT-0013-Status-Taxonomy-Collapse]]"
implements: [REQ-0016, REQ-0017]
related: []
---

# Plan: Status taxonomy collapse

Rules, templates and validator land in `~/Dev/repos/project-os` (template). The migration runs across all 10 fleet repos and is the risky half — it is sequenced last, behind a dry-run, and committed per repo so any single mapping error is revertible in isolation.

- [ ] [[TASK-0053-Decide-Collapsed-Taxonomy|TASK-0053]] — settle the vocabulary (incl. `approved`); rewrite STATUSES.md, templates, SCHEMAS.md
- [ ] [[TASK-0054-Validator-Collapsed-Taxonomy|TASK-0054]] — collapsed ALLOWED_STATUS; status check reaches registered notes
- [ ] [[TASK-0055-Fleet-Vocabulary-Migration|TASK-0055]] — dry-run, then migrate ~300 notes across 10 repos
- [ ] [[TASK-0056-Metric-Definitions|TASK-0056]] — redefine status-keyed metrics; fixes ISS-0008
- [ ] [[TASK-0073-Cockpit-Vocabulary-Alignment|TASK-0073]] — cockpit vocabulary across eight surfaces; the delivered band empties (external)

## Dependencies

- **Hard:** TASK-0053 blocks every other task here — nothing can be enforced, migrated, counted or rendered before the target vocabulary exists.
- **Soft:** TASK-0055 should land after TASK-0054 so the validator can verify the migration rather than trusting it.
- **Downstream:** TASK-0073 lands in `../project-os-cockpit` and propagates back through three hops — `release-to-project-os.sh` → `project-os` (`tools/cockpit/`) → 9 downstream repos.

## Open questions

- Does `approved` survive on requirements? ADR-0008 clause 5 defers this deliberately; TASK-0053 decides it. Dropping it removes the `REQ-PREMATURE` gate and reopens ADR-0006's "approval precedes implementation" clause.
- `superseded` on tasks: 71 notes currently use it. Is the intent `cancelled` (work abandoned) or `done` (work absorbed elsewhere)? The mapping must be established per repo, not guessed globally — this is the single largest migration bucket and the likeliest place for silent misrelabelling.
