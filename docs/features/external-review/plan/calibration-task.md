# Calibration task — ISS-0011 → ISS-0015

You are reviewing `tools/scripts/validate-docs.py`, specifically the function
`validate_status_tables()` and the module-level status tables it checks.

## Background you need

project-os notes carry a `status:` field. The legal values per note type live in
`ALLOWED_STATUS`. The file also contains **several other tables of status
values** used by individual checks. When a status is renamed in one table and
not another, nothing errors — the affected check simply stops recognising the
renamed value, and every repository keeps validating green.

That happened for real: ADR-0012 renamed the issue status `wont-fix` →
`declined`, the rename landed in `ALLOWED_STATUS` and not in `PHASE_RESOLVED`,
and the miss survived a 41-value migration across ten repositories.

`validate_status_tables()` is the guard written to make that class of drift
impossible. It is reachable standalone:

```
python3 tools/scripts/validate-docs.py --self-check
```

## What has already been found

This guard has been through **five rounds of review**, all by models of the same
family as its author. Each round found real defects. They are recorded as
ISS-0011 through ISS-0015, included below with their full Resolution sections,
so you can see exactly what was already caught and how each was verified.

Read them. Do not re-report them.

## Your job

**Find something all five rounds missed.**

Concretely, attack in roughly this order:

1. **Can you make a status drift that `--self-check` does not catch?** Add a
   status collection the completeness walk cannot see; rename a value in a table
   that is checked weakly or not at all; find a check that reads statuses
   without going through any registered table.
2. **Is any claim in the notes still false?** The recurring failure across all
   five rounds was a coverage claim written wider than the code. The docstring
   of `validate_status_tables`, TST-0002's "Coverage boundary" section, and the
   Resolution sections of ISS-0012..0015 all make specific assertions. Test them.
   Quote the exact sentence you are refuting.
3. **Does the guard have side effects it should not?** Look at
   `compute_metric_counts` and `METRIC_STATUS_FILTERS`, which were restructured
   during this sequence. The claim is that the restructure was
   behaviour-preserving across all 18 metrics.
4. **Anything else about this file that is wrong.** You are not limited to the
   status tables. One earlier round found that a commit had silently duplicated
   half the file — inert when run as a script, so every check passed over it.
   Look for that class of problem: real defects that all the mechanical checks
   are structurally incapable of seeing.

## Ground rules

- The worktree is yours. Break things, run `--self-check`, observe, restore.
- Every finding needs a `repro` command you actually ran and the `observed`
  output you actually got. A finding you cannot reproduce is not a finding, and
  will be discarded before a human sees it.
- **A null result is a valid and useful answer.** If you attack this hard and it
  holds, say so and list what you tried in `attacks_that_failed`. That is a real
  measurement about five rounds of review having converged — it will be recorded
  as such. Do not manufacture a finding to have something to report.
- Do not report style, naming, or "consider adding a test" suggestions. Defects
  with reproductions only.
