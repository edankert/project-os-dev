#!/usr/bin/env python3
"""project-os docs validator.

Mechanically enforces the invariants that QUALITY.md, SNAPSHOT.md, and
TRACEABILITY.md define by convention:

  1. SNAPSHOT.yaml parses and has the required top-level keys.
  2. Every items.*.<ID> entry points at an existing note file whose
     frontmatter id/status/type agree with the snapshot.
  3. Status values are within the allowed taxonomy (STATUSES.md).
  4. Counter integrity: no allocated ID (snapshot or note) exceeds its
     counter in SNAPSHOT.yaml.
  5. Link-graph integrity: every ID referenced from snapshot relationship
     fields or note frontmatter resolves to a snapshot item or a note file.
  6. Verification invariant: no item may hold a terminal status
     (task done, issue closed, feature done) unless
     every linked TST-* is status: passing — or the note carries an explicit
     recorded waiver (frontmatter key: verification_waiver).
  7. Deferral invariants (STATUSES.md "Deferral and re-adoption"): deferred
     never resolves scope — a feature's tasks: list may not contain deferred
     IDs; deferred items need a forward home (phase), deferred tasks need
     origin provenance and no parent, and deferred notes may not be pruned
     from the snapshot.
  8. Requirement lifecycle (QUALITY.md; close-out "Requirement advancement";
     ADR-0007): a requirement whose implementing feature has reached a terminal
     status (done/cancelled/superseded) may not sit at draft/approved
     (REQ-STALE); features should not implement against a draft requirement
     (REQ-PREMATURE); `implemented` is terminal and must carry one ticked-or-
     reconciled acceptance criterion per criterion of record (REQ-BOXES);
     `implements:` names at most one feature (REQ-OWNER); and a feature may not
     be done while a requirement naming it has unresolved criteria
     (FEATURE-REQ).
  9. Phase closure (STATUSES.md `[[phase]]`): a phase that is done/superseded has
     no unresolved note naming it in `phase:` (PHASE-CHILDREN), and a done phase
     has every exit criterion ticked-with-evidence or reconciled (PHASE-BOXES).
     The table of statuses that count as resolved is itself checked against the
     allowed taxonomy, so a rename cannot land in one table and not the other
     (STATUS-TABLE).
 10. Grandfathering: items already violating a gate when that gate was promoted
     to error are listed in tools/GRANDFATHERED.yaml and report as warnings.
     Everything else errors immediately — there is no date-based exemption.

Exit codes: 0 = clean, 1 = violations found, 2 = usage/internal error.

Stdlib only. Uses PyYAML when available; otherwise falls back to a minimal
parser that supports the constrained YAML subset SNAPSHOT.yaml uses
(nested mappings, inline [a, b] lists, dash lists, quoted scalars, comments).
"""

import argparse
import re
import sys
from pathlib import Path

ID_PREFIXES = ("ADR", "DES", "FEAT", "ISS", "PHASE", "REQ", "RISK", "REL",
               "TASK", "TST", "WF")
ID_RE = re.compile(r"\b(%s)-(\d{2,})\b" % "|".join(ID_PREFIXES))

COLLECTION_TYPE = {
    "features": {"feature"},
    "tasks": {"task"},
    "issues": {"issue"},
    "requirements": {"requirement"},
    "phases": {"phase"},
    "risks": {"risk"},
    "tests": {"test"},
    "workflows": {"workflow"},
    "changes": {"change"},
    "decisions": {"adr", "decision"},
    "designs": {"design"},
    "releases": {"release"},
}

# ADR-0008 (as amended 2026-07-25): 64 declared values collapsed to 53. A value
# is deleted iff it had <10 writes fleet-wide AND zero live notes; values with
# zero writes but no alternative destination for a real outcome are kept
# (`failing`, `rolled-back`, `deprecated`). `superseded` was ADDED to task and
# phase — 72 live notes carry `superseded_by:` pointing at a successor, which is
# neither `done` (never shipped) nor `cancelled` (not abandoned).
ALLOWED_STATUS = {
    "task": {"backlog", "doing", "done", "deferred", "cancelled", "superseded"},
    "issue": {"triage", "open", "fixed", "declined", "deferred"},
    "feature": {"backlog", "planned", "doing", "review", "done", "deferred", "cancelled", "superseded"},
    "phase": {"planned", "active", "done", "deferred", "superseded"},
    "requirement": {"draft", "approved", "implemented", "retired", "deferred", "cancelled", "superseded"},
    "risk": {"open", "closed"},
    "workflow": {"draft", "active", "deprecated"},
    "change": {"merged", "reverted"},
    "adr": {"proposed", "accepted", "superseded"},
    # A design is proposed, accepted, built, and eventually replaced by its own
    # next revision. Every value here already existed in the vocabulary --
    # `draft` from requirement/workflow/plan, `proposed`/`accepted` from adr,
    # `implemented` from requirement, `superseded`/`cancelled` from most types.
    # ADR-0008 collapsed 64 values to 53; a new type is not a reason to reopen
    # that, and this one adds none.
    "design": {"draft", "proposed", "accepted", "implemented", "superseded",
               "cancelled"},
    # `decision` is an accepted alias for `adr` -- COLLECTION_TYPE has mapped
    # decisions to {"adr", "decision"} all along, but ALLOWED_STATUS never
    # carried the alias. Found by the type-table check added for ISS-0014; one
    # such note exists fleet-wide (your-health ADR-0006, `accepted`, legal either
    # way). Not a dead gate, as ISS-0014 first said -- STATUS-VALUE picked one
    # type out of an unordered set, so it fired by hash seed (6/12 measured).
    # ISS-0015 replaced that pick with a union check.
    "decision": {"proposed", "accepted", "superseded"},
    "test": {"ready", "passing", "failing"},
    "release": {"draft", "released", "reverted"},
    # `plan` is consumed by validate_plan_notes through load_allowed_status(). It
    # belongs in the defaults like every other type: without it, a repo whose
    # STATUSES.md lacks a `[[plan]]` section gets an empty allowed set and
    # PLAN-STATE flags every plan it finds (STATUSES.md `[[plan]]`).
    "plan": {"draft", "active", "done", "superseded"},
}

#: Statuses that resolve a child's place in its phase's scope (PHASE-CHILDREN).
#:
#: Module-level, and deliberately sitting next to ALLOWED_STATUS: this is the
#: SECOND status table in this file, and that is what made ISS-0011 possible.
#: ADR-0012 renamed the issue value `wont-fix` -> `declined` and its consequence
#: list named ALLOWED_STATUS but not this table, so the gate went on resolving on
#: a value no issue can hold while refusing the one it can. Nothing caught it:
#: the table was a local inside the check function, reachable by no test, and all
#: ten repos kept validating green. `validate_status_tables` below is the guard.
#:
#: `deferred` is unresolved on purpose (STATUSES.md, "Deferral and re-adoption"):
#: parking an item does not close the phase that owns it. Re-home a deferred item
#: to the phase that will carry it -- usually PHASE-999 -- and the gate is
#: satisfied by the relationship rather than by the word.
PHASE_RESOLVED = {
    "task": {"done", "cancelled", "superseded"},
    "issue": {"fixed", "declined"},
    "requirement": {"implemented", "retired", "cancelled", "superseded"},
    "feature": {"done", "cancelled", "superseded"},
    # STATUSES.md says "a note naming it in `phase:`", so a risk parked on a
    # closed phase counts too -- an open hazard is not resolved by the phase
    # that raised it closing. Omitting risks made the gate narrower than its
    # own prose (found in independent review of CHG-20260726).
    "risk": {"closed"},
}
#: Phase statuses that close a phase, and so arm PHASE-CHILDREN against it.
#:
#: Hoisted by the ISS-0011 commit and then left out of FLAT_STATUS_TABLES --
#: found in independent review of that commit (ISS-0012). Renaming `done` here
#: and nowhere else left --self-check green while PHASE-CHILDREN silently
#: stopped firing: the ISS-0011 failure mode, reintroduced by the fix for it.
CLOSED_PHASE_STATUSES = ("done", "superseded")

#: Requirement statuses meaning "no longer in scope", so FEATURE-REQ skips it.
#: Was a local inside validate() until 2026-07-26 (ISS-0012); a local is a
#: constant no table can register and no check can reach.
DESCOPED_STATUSES = ("deferred", "cancelled", "superseded")

#: Statuses that resolve an item's place in a parent's scope / a requirement's
#: delivery. Applied to a feature's tasks (VERIFY) and to a requirement's
#: implementing features (REQ-STALE), so it must be legal for both types.
#: `deferred` is deliberately absent (STATUSES.md, "Deferral and re-adoption").
RESOLVED_STATUSES = ("done", "cancelled", "superseded")

#: Feature statuses meaning "already being implemented" (REQ-PREMATURE).
#:
#: Was an inline ("in-progress", "in-review", "done") literal until 2026-07-26 --
#: two thirds retired vocabulary after ADR-0012, so the warning could only ever
#: fire on `done` and never on a feature actually mid-build, which is the case it
#: exists to catch. The second instance of the miss recorded in ISS-0011.
FEATURE_ACTIVE_STATUSES = ("doing", "review", "done")

#: Feature status -> the plan statuses that track it (PLAN-FOLLOWS). Keys are
#: feature statuses, values are plan statuses.
#:
#: `deferred` and `cancelled` are deliberately absent: a parked feature's plan may
#: honestly stay `draft` or become `superseded`, and guessing between them would
#: produce noise rather than signal.
#:
#: Keyed on `in-progress`/`in-review` until 2026-07-26, which meant `.get()`
#: returned None for every actively-built feature and the check silently never
#: fired -- the third instance of the ISS-0011 miss, and the one with the widest
#: reach, since PLAN-FOLLOWS exists precisely to track a plan through the build.
PLAN_FOLLOWS_FEATURE = {
    "backlog": {"draft"},
    "planned": {"draft"},
    "doing": {"active"},
    "review": {"active"},
    "done": {"done"},
    "superseded": {"superseded"},
}

#: Snapshot collection -> the statuses at which a REVIEW verdict is required
#: (QUALITY.md "Independent review"). Inline as
#: `(("tests", {"passing"}), ("changes", {"merged"}))` until ISS-0014 -- the
#: last inline status collection in the file, and the one that falsified
#: ISS-0013's "no inline status literal remains" claim.
REVIEW_SETTLED_STATUSES = {
    "tests": ("passing",),
    "changes": ("merged",),
}

#: Test statuses that only the runner may write (TEST-FIELDS, ADR-0010).
#: Inline until ISS-0013 -- the second round of review found it, which is the
#: point: an inline literal is invisible to the guard by construction.
TEST_RUNNER_STATUSES = ("passing", "failing")

#: Requirement statuses meaning "not yet advanced to terminal" (REQ-STALE).
#: Inline until ISS-0013, same reason.
REQ_UNADVANCED_STATUSES = ("draft", "approved")

#: Prefix -> note type, for the metric filters below. Separate from
#: COLLECTION_TYPE, which is keyed by snapshot collection rather than ID prefix.
METRIC_PREFIX_TYPE = {
    "FEAT": "feature", "TASK": "task", "ISS": "issue", "PHASE": "phase",
    "TST": "test", "RISK": "risk", "REQ": "requirement", "REL": "release",
    # `ADR` was absent until ISS-0016 and nothing noticed, because
    # `decisions_total` is a total (`allowed is None`) and the check `continue`d
    # before reaching the prefix. Every total metric was unguarded the same way.
    "ADR": "adr",
}

#: metric name -> (ID prefix, statuses counted). `None` means "count them all".
#:
#: These were nine inline set literals inside compute_metric_counts, one of which
#: (risks_open, then {"open", "mitigating", "monitoring"}) carried two retired
#: values and had been counting one status while reading as though it counted
#: three. ISS-0012 hoisted that one; ISS-0013's review pointed out its eight
#: siblings were still inline, which is the same bug waiting for the next rename.
#: As a table they are checked like everything else.
METRIC_STATUS_FILTERS = {
    "features_total": ("FEAT", None),
    "features_done": ("FEAT", ("done",)),
    "phases_total": ("PHASE", None),
    "phases_done": ("PHASE", ("done",)),
    "tasks_total": ("TASK", None),
    "tasks_done": ("TASK", ("done",)),
    "tasks_deferred": ("TASK", ("deferred",)),
    "tests_total": ("TST", None),
    "tests_passing": ("TST", ("passing",)),
    "tests_failing": ("TST", ("failing",)),
    "issues_open": ("ISS", ("open",)),
    "issues_triage": ("ISS", ("triage",)),
    "issues_deferred": ("ISS", ("deferred",)),
    "requirements_total": ("REQ", None),
    "requirements_implemented": ("REQ", ("implemented",)),
    "risks_open": ("RISK", ("open",)),
    "releases_total": ("REL", None),
    "decisions_total": ("ADR", None),
}

#: Snapshot collection -> the terminal status for that type. Keyed by collection
#: name because that is how the snapshot names them; TERMINAL_TYPES maps each key
#: to the note type its value must be legal for.
TERMINAL = {
    "tasks": "done",
    "issues": "fixed",   # ADR-0008: `closed` merged into `fixed`; 3% follow-through fleet-wide
    "requirements": "implemented",
    "features": "done",
}
TERMINAL_TYPES = {
    "tasks": "task",
    "issues": "issue",
    "requirements": "requirement",
    "features": "feature",
}

#: Flat status collections, with the note types each is compared against.
#: validate_status_tables walks this, so adding a status table means adding a row
#: here rather than remembering to write another check by hand.
FLAT_STATUS_TABLES = {
    "RESOLVED_STATUSES": (RESOLVED_STATUSES, ("task", "feature")),
    "FEATURE_ACTIVE_STATUSES": (FEATURE_ACTIVE_STATUSES, ("feature",)),
    "CLOSED_PHASE_STATUSES": (CLOSED_PHASE_STATUSES, ("phase",)),
    "DESCOPED_STATUSES": (DESCOPED_STATUSES, ("requirement",)),
    "TEST_RUNNER_STATUSES": (TEST_RUNNER_STATUSES, ("test",)),
    "REQ_UNADVANCED_STATUSES": (REQ_UNADVANCED_STATUSES, ("requirement",)),
}


#: Tables checked explicitly above rather than through FLAT_STATUS_TABLES.
#: Named, not identified: see the completeness assertion for why id() is unsafe.
_CHECKED_TABLE_NAMES = frozenset({
    "ALLOWED_STATUS", "PHASE_RESOLVED", "PLAN_FOLLOWS_FEATURE", "TERMINAL",
    "TERMINAL_TYPES", "METRIC_STATUS_FILTERS", "METRIC_PREFIX_TYPE",
    "COLLECTION_TYPE", "REVIEW_SETTLED_STATUSES", "FLAT_STATUS_TABLES",
    "PROMOTIONS", "METRIC_PREFIXES",
})

#: Module-level string collections that are deliberately NOT status collections.
#: The completeness assertion walks every tuple/list/set/frozenset of strings at
#: module scope and demands each be either registered or named here, so this is a
#: record of decisions rather than a suppression.
#:
#: It checked only `tuple`, and only names passing `.isupper()`, until ISS-0013 --
#: a module-level `set` of statuses evaded it entirely, which made the guard's
#: own coverage claim false in the same way ISS-0012 did. Type and case are not
#: what makes something a status table.
_NON_STATUS_COLLECTIONS = frozenset({
    "ID_PREFIXES",           # note ID prefixes
    "RELATIONSHIP_FIELDS",   # frontmatter field names
    # The registry's own bookkeeping. Named rather than exempted by identity:
    # after ISS-0016 the walk is name-keyed, and an identity exemption is
    # exactly the mechanism that made an unregistered table invisible.
    "_CHECKED_TABLE_NAMES",
    "_NON_STATUS_COLLECTIONS",
})


def _check_values(report, label, values, note_type):
    """One STATUS-TABLE assertion: every value legal for note_type."""
    allowed = ALLOWED_STATUS.get(note_type)
    if allowed is None:
        report.error("STATUS-TABLE", "%s is compared against note type '%s', which has no entry in ALLOWED_STATUS; one table knows a type the other does not" % (label, note_type))
        return
    unknown = sorted(set(values) - allowed)
    if unknown:
        phrasing = ("is not an allowed %s status" % note_type if len(unknown) == 1
                    else "are not allowed %s statuses" % note_type)
        report.error("STATUS-TABLE", "%s contains %s, which %s in ALLOWED_STATUS (%s); a value was renamed in one status table and not the other -- see ISS-0011" % (
            label,
            ", ".join("'%s'" % u for u in unknown),
            phrasing,
            ", ".join(sorted(allowed))))


def validate_status_tables(report):
    """STATUS-TABLE -- every value in PHASE_RESOLVED must be a real status.

    The regression guard for ISS-0011. Two independent status tables ship in
    this file, and a value renamed in one but not the other fails silently in
    the worst possible way: the gate does not error, it simply stops recognising
    the renamed status, and every repo keeps passing. A 41-value vocabulary
    migration (ADR-0012) shipped green over exactly that.

    Checked against the ALLOWED_STATUS *constant*, not `load_allowed_status`'s
    per-repo STATUSES.md overlay. Both tables ship here, so their agreement is an
    internal invariant of the validator -- a downstream repo customising its own
    taxonomy must not be able to turn this red, and equally must not be able to
    hide a genuine mismatch by widening its own allowed set.

    Deliberately one-directional: every value in a table must be a real status,
    but a status need not appear in any table. `deferred`, `open` and `triage`
    are all legal and all correctly absent from PHASE_RESOLVED.

    Covers every status collection at MODULE SCOPE. That qualifier is load-bearing
    and was absent twice; see below.

      PHASE_RESOLVED         per-type -- each key's values checked against that type
      FLAT_STATUS_TABLES     flat collections, each with the types it applies to
      PLAN_FOLLOWS_FEATURE   a mapping BETWEEN two vocabularies: feature statuses
                             as keys, plan statuses as values, both checked
      TERMINAL               collection -> terminal status, via TERMINAL_TYPES
      METRIC_STATUS_FILTERS  metric -> (prefix, statuses), via METRIC_PREFIX_TYPE
      REVIEW_SETTLED_STATUSES  collection -> statuses, via COLLECTION_TYPE
      (type tables)          COLLECTION_TYPE / TERMINAL_TYPES / METRIC_PREFIX_TYPE
                             hold note TYPES, asserted to exist in ALLOWED_STATUS
      (completeness)         every module-level tuple/list/set/frozenset/dict
                             holding a string, at any nesting depth, is either
                             registered above or named in _NON_STATUS_COLLECTIONS

    All three of the misses ISS-0011 records would have failed here.

    ISS-0012 records the sequel, and it is the more instructive one. The first
    version of this function walked FLAT_STATUS_TABLES, and CLOSED_PHASE_STATUSES
    was hoisted to module scope by the very commit that added the guard -- and
    then not registered in it. Renaming `done` there and nowhere else left
    --self-check green while PHASE-CHILDREN silently stopped firing: the exact
    failure this function claims to make impossible, reintroduced by the fix for
    it, and found only by an independent reviewer who tried to break it rather
    than reading the docstring. Registration is manual, so it can be forgotten;
    the completeness assertion below is what makes forgetting loud.
    """
    for note_type, resolved in sorted(PHASE_RESOLVED.items()):
        _check_values(report, "PHASE_RESOLVED['%s']" % note_type, resolved, note_type)

    for name, (values, note_types) in sorted(FLAT_STATUS_TABLES.items()):
        for note_type in note_types:
            _check_values(report, "%s (applied to %s notes)" % (name, note_type), values, note_type)

    _check_values(report, "PLAN_FOLLOWS_FEATURE keys", PLAN_FOLLOWS_FEATURE.keys(), "feature")
    plan_values = set()
    for expected in PLAN_FOLLOWS_FEATURE.values():
        plan_values.update(expected)
    _check_values(report, "PLAN_FOLLOWS_FEATURE values", plan_values, "plan")

    for collection, settled in sorted(REVIEW_SETTLED_STATUSES.items()):
        note_types = COLLECTION_TYPE.get(collection)
        if not note_types:
            report.error("STATUS-TABLE", "REVIEW_SETTLED_STATUSES names collection '%s', which has no entry in COLLECTION_TYPE" % collection)
            continue
        for note_type in sorted(note_types):
            _check_values(report, "REVIEW_SETTLED_STATUSES['%s']" % collection, settled, note_type)

    # METRIC_PREFIXES decides which IDs are counted at all. It was exempted by
    # name and checked against nothing, so renaming a prefix there left every
    # metric using it permanently reading 0 -- with the METRICS check agreeing,
    # because it compares the snapshot against the same broken computation
    # (ISS-0016).
    declared = {prefix for prefix, _ in METRIC_STATUS_FILTERS.values()}
    missing = sorted(declared - set(METRIC_PREFIXES))
    if missing:
        report.error("STATUS-TABLE", "METRIC_STATUS_FILTERS counts prefix(es) %s that METRIC_PREFIXES does not collect, so those metrics silently read 0" % ", ".join("'%s'" % m for m in missing))
    unused = sorted(set(METRIC_PREFIXES) - declared)
    if unused:
        report.error("STATUS-TABLE", "METRIC_PREFIXES collects prefix(es) %s that no metric uses; one table knows an ID prefix the other does not" % ", ".join("'%s'" % u for u in unused))

    for metric, (prefix, allowed) in sorted(METRIC_STATUS_FILTERS.items()):
        # The prefix is checked for EVERY metric, including totals. Skipping
        # totals was ISS-0016: a mistyped prefix makes `by_prefix.get(prefix,
        # [])` return [], so the metric silently reads 0 rather than erroring --
        # and "no decisions recorded" is a plausible-looking number, which is
        # what makes it worse than a crash. Seven of the eighteen metrics are
        # totals and all seven were unguarded.
        note_type = METRIC_PREFIX_TYPE.get(prefix)
        if note_type is None:
            report.error("STATUS-TABLE", "METRIC_STATUS_FILTERS['%s'] counts prefix '%s', which has no entry in METRIC_PREFIX_TYPE; a mistyped prefix silently counts zero rather than failing" % (metric, prefix))
            continue
        if allowed is None:
            continue   # a total: the prefix is the whole contract
        _check_values(report, "METRIC_STATUS_FILTERS['%s']" % metric, allowed, note_type)

    for collection, status in sorted(TERMINAL.items()):
        note_type = TERMINAL_TYPES.get(collection)
        if note_type is None:
            report.error("STATUS-TABLE", "TERMINAL names collection '%s', which has no entry in TERMINAL_TYPES, so its terminal status is checked against nothing" % collection)
            continue
        _check_values(report, "TERMINAL['%s']" % collection, (status,), note_type)

    # The type side of the same problem. These tables hold note TYPES rather than
    # statuses, so _check_values does not apply -- but a type renamed here and not
    # in ALLOWED_STATUS fails exactly as quietly, and the completeness walk below
    # cannot tell a table of types from a table of statuses. Assert them.
    # `decision` is an alias of `adr` (COLLECTION_TYPE maps decisions to both).
    # ISS-0015 made STATUS-VALUE check the UNION of a collection's types, which
    # is correct -- and which means a value legal for only one of the pair
    # becomes legal for both. Nothing asserted the rows stay equal, so widening
    # `decision` silently widened `adr` too (ISS-0016).
    for a, b in (("adr", "decision"),):
        if ALLOWED_STATUS.get(a) != ALLOWED_STATUS.get(b):
            report.error("STATUS-TABLE", "ALLOWED_STATUS['%s'] and ALLOWED_STATUS['%s'] are aliases but differ (%s); STATUS-VALUE checks their union, so a value legal for one becomes legal for both" % (
                a, b, " vs ".join(", ".join(sorted(ALLOWED_STATUS.get(k) or ())) for k in (a, b))))

    for label, types in (("COLLECTION_TYPE", {t for ts in COLLECTION_TYPE.values() for t in ts}),
                         ("TERMINAL_TYPES", set(TERMINAL_TYPES.values())),
                         ("METRIC_PREFIX_TYPE", set(METRIC_PREFIX_TYPE.values()))):
        unknown = sorted(types - set(ALLOWED_STATUS))
        if unknown:
            report.error("STATUS-TABLE", "%s names note type(s) %s with no entry in ALLOWED_STATUS; a type renamed in one table and not the other leaves the check comparing against nothing" % (
                label, ", ".join("'%s'" % u for u in unknown)))

    # Completeness. Registration is a manual step, and ISS-0012 is what a missed
    # one costs: a table guarded by nothing reads exactly like a table guarded by
    # this function. So assert the registry covers every module-level string
    # collection rather than trusting the author to remember -- a new constant is
    # loud on its first run, not at the next rename.
    #
    # Shape-agnostic, and it took three rounds of review to get there. It saw only
    # `tuple` until ISS-0013 (a module-level `set` evaded it) and only non-dict
    # containers until ISS-0014 -- while PHASE_RESOLVED, the file's most-used
    # table, is a dict. Anything holding strings, nested to any depth, counts.
    # Keyed on NAME, not id(). Identity looked natural and was wrong: CPython
    # deduplicates equal tuple constants in a code object, so two module-level
    # tables with the same literal are the SAME OBJECT. Status tables routinely
    # share values -- ("done", "superseded") appears in several -- so a new
    # unregistered table would silently inherit a registered one's identity and
    # pass. Demonstrated in ISS-0016: adding ISSUE_ARCHIVED_STATUSES =
    # ("done", "superseded") and RISK_STALE_STATUSES = ("draft", "approved"),
    # both illegal for the types they name and registered nowhere, left
    # --self-check green. A name cannot be interned into another name.
    registered = set(FLAT_STATUS_TABLES)
    registered.update(_CHECKED_TABLE_NAMES)

    def _holds_strings(value, seen=None):
        """True if value is a container with a string anywhere inside it.

        Unbounded, and cycle-safe by identity rather than by a depth cap. It
        capped at depth 4 until ISS-0015 -- which is a defensible implementation
        and an indefensible pair with a docstring promising "any nesting depth".
        Given the choice between weakening the sentence and making it true, make
        it true: a cap is an arbitrary number a future table can exceed, and the
        only reason for one was cycles, which `seen` handles properly.
        """
        if isinstance(value, str):
            return True
        if not isinstance(value, (tuple, list, set, frozenset, dict)):
            return False
        seen = set() if seen is None else seen
        if id(value) in seen:
            return False
        seen.add(id(value))
        items = ([x for kv in value.items() for x in kv] if isinstance(value, dict)
                 else list(value))
        return any(_holds_strings(v, seen) for v in items)

    for name, value in sorted(globals().items()):
        # Only the allow-list itself is exempt by identity. Skipping names by
        # shape -- a leading underscore, a lowercase letter -- is how a status
        # collection hides, which is the whole lesson of ISS-0013.
        if name in _NON_STATUS_COLLECTIONS or name in registered:
            continue
        if isinstance(value, str) or not isinstance(value, (tuple, list, set, frozenset, dict)):
            continue
        if not _holds_strings(value):
            continue
        report.error("STATUS-TABLE", "%s is a module-level collection holding strings that no status table registers; if any of them are statuses, register it, and if none are, name it in _NON_STATUS_COLLECTIONS -- an unregistered status collection is what ISS-0012 and ISS-0013 both were" % name)


def is_sentinel_id(digits):
    """True for all-9s sentinel IDs (PHASE-999, PHASE-0999, PHASE-9999).

    Zero padding varies across the fleet -- project-os-dev writes PHASE-999,
    your-health writes PHASE-0999 -- so padding is stripped first. At least THREE
    nines are required, which is what separates a sentinel from an ordinary
    sequential ID: the older test was `set(str(int(digits))) == {"9"}`, and
    `int("0009")` is 9, so it silently exempted ISS-0009, TASK-99 and every other
    nines-ending ID from counter integrity.
    """
    stripped = digits.lstrip("0") or "0"
    return len(stripped) >= 3 and set(stripped) == {"9"}


def load_allowed_status(root):
    """Overlay ALLOWED_STATUS with the repo's own STATUSES.md.

    STATUSES.md is explicitly per-repo customizable ("If a project needs
    different states, update this file"), so the repo's Allowed: lines are
    the source of truth; hardcoded defaults apply only for types the file
    does not define.
    """
    allowed = {k: set(v) for k, v in ALLOWED_STATUS.items()}
    path = root / "tools" / "instructions" / "STATUSES.md"
    if not path.is_file():
        return allowed
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return allowed
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+`?\[\[(\w[\w-]*)\]\]`?", line.strip())
        if m:
            current = m.group(1).lower()
            continue
        if current and re.match(r"^-\s*Allowed\s*:", line.strip(), re.IGNORECASE):
            vals = set(re.findall(r"`([\w-]+)`", line))
            if vals:
                allowed[current] = vals
            current = None
    return allowed


RELATIONSHIP_FIELDS = (
    "parent", "features", "tasks", "issues", "requirements", "tests",
    "phases", "phase", "depends", "blocks", "mitigation_tasks", "workflows",
    "origin", "deferred", "implements", "supersedes", "superseded",
)

# Grandfather ledger (ISS-0007, ADR-0011 clause 3).
#
# Replaces the previous date heuristic (`FEATURE_REQ_GATE_FROM` compared against
# each note's `updated:`). That approach had two defects its own comment admitted:
# it keyed on when a note was last *edited*, not when the item closed, so editing
# a grandfathered note for any reason re-armed the gate on it — turning an
# unrelated typo fix into a build failure — and a stale or malformed `updated:`
# silently exempted an item the gate should have caught.
#
# The ledger is explicit instead: `tools/GRANDFATHERED.yaml` names the exact item
# IDs that were already violating a gate at the moment it was promoted to error.
# Those report as warnings (visible debt); everything else is an error, from the
# moment of promotion, with no dependence on dates. The ledger only shrinks —
# entries are deleted as the debt is paid — and a stale entry is inert.
#
# Generated by tools/scripts/grandfather.py.
GRANDFATHER_FILE = "tools/GRANDFATHERED.yaml"

#: ADR-0011 clause 2: a warning is legal ONLY as a dated migration state.
#: gate -> the date it becomes an error. Before it, findings warn; on/after, they
#: error (still subject to the grandfather ledger). A gate absent from this table
#: and not calling report.warn directly is already an error.
#:
#: `REVIEW` is here rather than promoted immediately because the fleet carries 207
#: findings (160 CHG, 47 TST) and clause 3 forbids promoting over debt. Narrowing
#: scope to CHG-* only would leave 160, so scope is not the lever — time is, and the
#: 90-day ceiling means a stalled migration fails the build instead of dissolving
#: back into permanent warning noise.
PROMOTIONS = {
    "REVIEW": "2026-10-23",
    # Plans went unvalidated entirely until PLAN-STATE existed, so the
    # debt is pre-existing rather than newly introduced: 19 of 33 plans
    # in project-os-cockpit carry no status. Clause 3 forbids promoting
    # over debt, so this warns while the fleet is groomed.
    "PLAN-STATE": "2026-10-24",
}


def promotion_emit(report, gate, grandfathered, item_id):
    """error / warn for a gate under ADR-0011's dated-promotion rule."""
    if item_id in grandfathered.get(gate, ()):
        return report.warn
    cutover = PROMOTIONS.get(gate)
    if cutover and _today().isoformat() < cutover:
        return report.warn
    return report.error

#: Default staleness window for MANUAL verification (ADR-0010 / REQ-0023).
#: Overridable per repo via `verification.staleness_days` in SNAPSHOT.yaml.
DEFAULT_STALENESS_DAYS = 90


def _today():
    from datetime import date
    return date.today()


def _parse_date(raw):
    """Parse a YYYY-MM-DD prefix; None when absent or malformed."""
    from datetime import date
    text = str(raw or "").strip().strip('"').strip("'")[:10]
    if len(text) != 10 or text[4] != "-" or text[7] != "-":
        return None
    try:
        return date(int(text[0:4]), int(text[5:7]), int(text[8:10]))
    except ValueError:
        return None


def is_stale(fm, staleness_days):
    """True when a MANUAL test's last_verified has aged out.

    Only manual tests (no `command:`) can go stale: an executable test's status
    is re-derived by running it, so age carries no information about it.
    """
    if str((fm or {}).get("command", "") or "").strip():
        return False
    d = _parse_date((fm or {}).get("last_verified"))
    if d is None:
        return False
    return (_today() - d).days > staleness_days


def load_grandfathered(root):
    """gate name -> set of item IDs exempted from that gate at promotion time."""
    path = root / GRANDFATHER_FILE
    if not path.is_file():
        return {}
    try:
        data = load_yaml(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    gates = (data or {}).get("gates") if isinstance(data, dict) else None
    out = {}
    if isinstance(gates, dict):
        for gate, entries in gates.items():
            if isinstance(entries, dict):
                out[str(gate)] = set(entries.keys())
            elif isinstance(entries, list):
                out[str(gate)] = {str(e).split(":")[0].strip() for e in entries if e}
    return out


# RESOLVED_STATUSES moved up beside ALLOWED_STATUS and the other status tables,
# where validate_status_tables can check it (ISS-0011).

# metrics.counts definitions live in tools/instructions/SNAPSHOT.md ("Metrics")
METRIC_PREFIXES = {"FEAT", "TASK", "ISS", "PHASE", "TST", "RISK", "REL", "ADR", "REQ"}


def compute_metric_counts(items, note_index):
    """Counts over all notes in docs/ (the archive) plus snapshot items; snapshot status wins where both exist."""
    statuses = {}
    for coll in (items.values() if isinstance(items, dict) else []):
        if not isinstance(coll, dict):
            continue
        for item_id, entry in coll.items():
            if isinstance(entry, dict) and str(entry.get("status", "") or ""):
                statuses[item_id] = str(entry.get("status", "") or "")
    for nid, (_path, fm) in note_index.items():
        statuses.setdefault(nid, str((fm or {}).get("status", "") or ""))
    by_prefix = {}
    for the_id, status in statuses.items():
        m = ID_RE.match(the_id)
        if m and m.group(1) in METRIC_PREFIXES:
            by_prefix.setdefault(m.group(1), []).append(status)

    def count(prefix, allowed=None):
        vals = by_prefix.get(prefix, [])
        return len(vals) if allowed is None else sum(1 for s in vals if s in allowed)

    return {
        name: count(prefix, None if allowed is None else set(allowed))
        for name, (prefix, allowed) in METRIC_STATUS_FILTERS.items()
    }
def fix_metrics(root):
    """Rewrite metrics.counts values in SNAPSHOT.yaml to the computed counts, preserving formatting."""
    snap_path = root / "SNAPSHOT.yaml"
    text = snap_path.read_text(encoding="utf-8")
    snap = load_yaml(text)
    if not isinstance(snap, dict):
        return []
    computed = compute_metric_counts(snap.get("items") or {}, build_note_index(root / "docs")[0])
    lines = text.splitlines(keepends=True)
    changes = []
    in_metrics = in_counts = False
    counts_indent = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^metrics:\s*(#.*)?$", line):
            in_metrics = True
            continue
        if in_metrics and re.match(r"^\S", line):
            break  # next top-level key
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if in_metrics and re.match(r"^\s+counts:\s*(#.*)?$", line):
            in_counts, counts_indent = True, indent
            continue
        if in_counts:
            if indent <= counts_indent:
                in_counts = False
                continue
            m = re.match(r"^(\s*)([\w-]+):\s*(-?\d+)\s*(#.*)?$", line)
            if m and m.group(2) in computed and int(m.group(3)) != computed[m.group(2)]:
                trailing = (" " + m.group(4)) if m.group(4) else ""
                lines[i] = "%s%s: %d%s\n" % (m.group(1), m.group(2), computed[m.group(2)], trailing)
                changes.append("%s: %s -> %d" % (m.group(2), m.group(3), computed[m.group(2)]))
    if changes:
        snap_path.write_text("".join(lines), encoding="utf-8")
    return changes


# ---------------------------------------------------------------- YAML subset
def _strip_comment(line):
    out, quote = [], None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _scalar(tok):
    tok = tok.strip()
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in "\"'":
        return tok[1:-1]
    if tok in ("true", "True"):
        return True
    if tok in ("false", "False"):
        return False
    if tok in ("", "~", "null"):
        return ""
    return tok


def _inline_list(tok):
    inner = tok.strip()[1:-1].strip()
    if not inner:
        return []
    return [_scalar(p) for p in re.split(r",(?![^\[]*\])", inner)]


def parse_yaml_subset(text):
    """Parse the constrained YAML subset used by SNAPSHOT.yaml and frontmatter."""
    root, stack = {}, [(-1, {})]
    stack[0] = (-1, root)
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = _strip_comment(lines[i])
        i += 1
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else root
        if line.startswith("- "):
            if not isinstance(parent, list):
                continue  # tolerate; fallback parser is best-effort on lists-of-maps
            parent.append(_scalar(line[2:]))
            continue
        m = re.match(r"^([^:]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = _scalar(m.group(1)), m.group(2).strip()
        if not isinstance(parent, dict):
            continue
        if val == "":
            # look ahead: dash list or nested mapping
            child = None
            for j in range(i, len(lines)):
                nxt = _strip_comment(lines[j])
                if not nxt.strip():
                    continue
                nind = len(nxt) - len(nxt.lstrip(" "))
                if nind <= indent:
                    break
                child = [] if nxt.strip().startswith("- ") else {}
                break
            if child is None:
                parent[key] = ""
            else:
                parent[key] = child
                stack.append((indent, child))
        elif val.startswith("["):
            parent[key] = _inline_list(val)
        else:
            parent[key] = _scalar(val)
    return root


def load_yaml(text):
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except Exception:
        return parse_yaml_subset(text)


def parse_frontmatter(path):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return load_yaml(text[4:end]) or {}


# ------------------------------------------------------------------ helpers
def extract_ids(value):
    """Pull canonical IDs out of scalars, wikilinks, or lists thereof."""
    found = []
    if value is None:
        return found
    items = value if isinstance(value, list) else [value]
    for it in items:
        if not isinstance(it, str):
            continue
        for m in ID_RE.finditer(it):
            found.append("%s-%s" % (m.group(1), m.group(2)))
    return found


def note_type(fm):
    t = fm.get("type", "") if isinstance(fm, dict) else ""
    if isinstance(t, str):
        return t.strip().strip("\"'").strip("[]").lower()
    return ""


def has_value(v):
    """True when a frontmatter/snapshot field holds real content (not None/''/[])."""
    if v is None:
        return False
    if isinstance(v, list):
        return any(str(x).strip() for x in v)
    return bool(str(v).strip())


UNCHECKED_RE = re.compile(r"^\s*[-*+]\s*\[\s\]")
CHECKED_RE = re.compile(r"^\s*[-*+]\s*\[[xX]\]")
#: A criterion reconciled rather than delivered — cut, descoped, or shipped in a
#: reduced form. Counts as a verification record (something was decided and written
#: down), which is why PHASE-BOXES must not report an all-`[~]` phase as having
#: "no exit criteria": that phase recorded every criterion, it just delivered none.
RECONCILED_RE = re.compile(r"^\s*[-*+]\s*\[~\]")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def count_acceptance_boxes(path, heading=r"Acceptance\b", require_heading=False, with_reconciled=False):
    """Count (unticked, ticked) criteria in a note's criteria section.

    `heading` selects the section: requirements use "Acceptance Criteria", phases
    use "Exit Criteria" (PHASE-BOXES). Neither counts `- [~]`, which both note
    types use for a criterion that was reconciled or cut rather than delivered.

    Fenced code blocks are skipped entirely: a `# comment` inside a fence must not be
    read as a heading that ends the section, and a `- [ ]` inside one is not a criterion.
    Falls back to the whole body when the note has no matching heading, unless
    `require_heading` — phase notes carry unrelated checklists in other sections, so
    PHASE-BOXES must not read a planning checklist as an exit criterion.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return (0, 0)
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    section, seen_section, in_fence, body = [], False, False, []
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        body.append(line)
        if re.match(r"^#{1,6}\s", line):
            if re.match(r"^#{1,6}\s+%s" % heading, line, re.IGNORECASE):
                seen_section, section = True, []
                continue
            if seen_section:
                break  # next heading ends the section
        if seen_section:
            section.append(line)
    if require_heading and not seen_section:
        return (0, 0, 0) if with_reconciled else (0, 0)
    scan = section if seen_section else body
    counts = (sum(1 for l in scan if UNCHECKED_RE.match(l)),
              sum(1 for l in scan if CHECKED_RE.match(l)))
    if with_reconciled:
        return counts + (sum(1 for l in scan if RECONCILED_RE.match(l)),)
    return counts


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, code, msg):
        self.errors.append("ERROR [%s] %s" % (code, msg))

    def warn(self, code, msg):
        self.warnings.append("WARN  [%s] %s" % (code, msg))


# ------------------------------------------------------------------ checks
#: Set by validate() so validate_plan_notes can resolve a plan's parent
#: feature without a second walk of docs/.
NOTE_INDEX_FOR_PLANS = {}


def build_note_index(docs_dir):
    """Map ID -> (path, frontmatter) for every note in docs/ with an ID.

    Also returns claimants: ID -> [paths], every file declaring that ID. The
    index keeps only the first claimant (setdefault), which is why a second
    note reusing an ID used to be invisible to every check downstream — see
    NOTE-DUP-ID.
    """
    index = {}
    claimants = {}
    if not docs_dir.is_dir():
        return index, claimants
    for path in sorted(docs_dir.rglob("*.md")):
        if "__templates__" in path.parts or "__bases__" in path.parts:
            continue
        fm = parse_frontmatter(path)
        ids = set()
        if isinstance(fm, dict) and isinstance(fm.get("id"), str):
            ids.update(extract_ids(fm["id"]))
        m = ID_RE.match(path.name)
        if m:
            ids.add("%s-%s" % (m.group(1), m.group(2)))
        for i in ids:
            index.setdefault(i, (path, fm if isinstance(fm, dict) else {}))
        # Claiming an ID means *being* that note, which is stricter than the
        # index's substring matching: composite IDs legitimately embed another
        # note's ID (a plan is `PLAN-FEAT-0006`, a change may be
        # `CHG-20260525-FEAT-0009-Chrome-Polish`) and must not count as rival
        # claims on FEAT-0006/FEAT-0009.
        fm_id = str((fm or {}).get("id", "") or "").strip().strip("\"'")
        claimed = set()
        if fm_id in ids:
            claimed.add(fm_id)
        if m:
            claimed.add("%s-%s" % (m.group(1), m.group(2)))
        for i in claimed:
            claimants.setdefault(i, [])
            if path not in claimants[i]:
                claimants[i].append(path)
    return index, claimants


def validate_unregistered_notes(root, items, note_index, claimants, allowed_status, report):
    """Duplicate-ID detection, plus a frontmatter status check over every note.

    Snapshot retention is deliberately active-and-recent: completed work is
    pruned from SNAPSHOT.yaml and the note becomes the archive. Every other
    check here resolves an item's status *through* the snapshot, so a note that
    is not registered is never inspected at all — drift accumulates in it
    unseen. Being unregistered is normal and is NOT reported; what is reported
    is the drift that used to hide there.
    """
    registered = set()
    for coll in items.values():
        if isinstance(coll, dict):
            registered.update(coll.keys())

    for the_id in sorted(claimants):
        paths = claimants[the_id]
        if len(paths) > 1:
            rels = ", ".join(p.relative_to(root).as_posix() for p in paths)
            report.error(
                "NOTE-DUP-ID",
                "%s is declared by %d notes (%s); IDs must be unique — bare-ID links and lookups "
                "resolve to whichever is indexed first, so the others are silently unreachable"
                % (the_id, len(paths), rels),
            )

    # Every note's *frontmatter* status is checked, registered or not.
    #
    # This used to skip anything in SNAPSHOT.yaml, on the stated grounds that
    # registered notes were "covered by STATUS-VALUE / ITEM-STATUS against the
    # snapshot entry". They were not: STATUS-VALUE reads the *snapshot's* status,
    # so a registered note whose frontmatter held an illegal value passed
    # whenever its snapshot entry held a legal one, and ITEM-STATUS only fires
    # when the two differ in a way the comparison catches. The reported count was
    # a floor, not a census (ISS-0009).
    for the_id, (path, fm) in sorted(note_index.items()):
        nt = note_type(fm)
        status = str((fm or {}).get("status", "") or "").strip()
        if not status or nt not in allowed_status:
            continue
        if status not in allowed_status[nt]:
            where = "" if the_id in registered else "; the note is not in SNAPSHOT.yaml, so no snapshot-driven check covers it"
            report.error(
                "NOTE-STATUS",
                "%s status '%s' not allowed for %s (%s)%s" % (
                    the_id, status, nt, path.relative_to(root).as_posix(), where),
            )


#: Placeholder markers the templates ship. A brief still carrying one has been
#: adopted and then abandoned, which is a different (and more actionable) state
#: than a project that never adopted the convention at all.
_BRIEF_PLACEHOLDER_RE = re.compile(r"REPLACE[ _-]?ME", re.IGNORECASE)


def validate_brief(root, report):
    """BRIEF-PLACEHOLDER — the project says what it is, or says nothing.

    ``LLM_BRIEF.md`` ships in every project-os repo describing itself as "the
    machine-oriented project brief". Measured across the fleet on 2026-07-28:
    **10 of 11 repos still carried ``Name: REPLACE ME``**, including the
    template itself and a repo with 43 features. The single exception had been
    created the previous day.

    That file was not failing because nobody needed it. It was failing because
    nothing ever showed it and nothing ever checked it — this validator
    reported dangling links, drifted statuses and unresolved assets, and never
    once noticed that eleven projects had not said what they are.

    A **warning, deliberately**. Erroring would turn ten of eleven repos red
    the moment it landed, and a gate that fails the whole fleet on day one
    teaches people to disable the gate. It escalates when the fleet is filled
    in — the dated-promotion shape ADR-0011 uses.

    A missing brief is **silent**: not every repo adopts the convention, and
    demanding one from a project that never had it is noise rather than a
    finding.
    """
    brief = root / "LLM_BRIEF.md"
    if not brief.is_file():
        return
    try:
        text = brief.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    hits = _BRIEF_PLACEHOLDER_RE.findall(text)
    if hits:
        report.warn(
            "BRIEF-PLACEHOLDER",
            "LLM_BRIEF.md still carries %d template placeholder(s); the brief "
            "is what an agent reads to learn what this project IS, and an "
            "unfilled one teaches it nothing (LLM_BRIEF.md)" % len(hits),
        )


def validate_design_notes(root, docs_dir, report):
    """DESIGN-ASSET — a design must point at an artifact that exists.

    A design note is a claim about a rendered surface, and the render is the
    artifact named by ``asset:``. A note whose asset is missing, or an artifact
    no note claims, is the design equivalent of a dangling link: nothing errors
    today, the design surface renders an empty pane tomorrow, and the reason is
    a typo committed weeks earlier.

    Both directions are checked. The orphan direction matters as much as the
    missing one: an unclaimed 139KB artifact sitting in ``docs/designs/`` is
    either a design nobody wrote a note for, or a leftover from a rename.
    """
    designs_dir = docs_dir / "designs"
    if not designs_dir.is_dir():
        return

    claimed = set()
    for note_path in sorted(designs_dir.rglob("*.md")):
        fm = parse_frontmatter(note_path) or {}
        if note_type(fm) != "design":
            continue
        rel = note_path.relative_to(root)
        asset = str(fm.get("asset", "") or "").strip()
        the_id = str(fm.get("id", "") or "").strip() or rel.name
        status = str(fm.get("status", "") or "").strip().lower()
        if not asset:
            # `draft` is exempt, and the check's own wording is why: "nothing to
            # review" is only true once something is offered for review. A design
            # note is often written before its artifact exists -- this note's
            # first real use was exactly that -- and forcing an empty placeholder
            # file to satisfy a check is how a gate teaches people to fake it.
            if status != "draft":
                report.error("DESIGN-ASSET", "%s is '%s' and declares no asset:; a design offered for review needs a rendered artifact (draft is exempt) (%s)" % (the_id, status or "unset", rel))
            continue
        target = (note_path.parent / asset).resolve()
        if not target.is_file():
            report.error("DESIGN-ASSET", "%s asset: '%s' does not resolve to a file beside the note (%s)" % (the_id, asset, rel))
            continue
        claimed.add(target)

    for artifact in sorted(designs_dir.rglob("*.html")):
        if artifact.resolve() not in claimed:
            report.warn("DESIGN-ORPHAN", "%s is not claimed by any design note's asset:; it is either an unwritten design or a leftover from a rename" % artifact.relative_to(root))


def validate_plan_notes(root, docs_dir, allowed_status, grandfathered, report):
    """PLAN-STATE / PLAN-ID — the plan checks STATUSES.md already promises.

    Plans are the one note type found by ``type:`` rather than by ID. They
    deliberately carry no ``id:``: ``PLAN-FEAT-0012`` *contains*
    ``FEAT-0012``, so ``extract_ids`` would let the plan squat its own
    feature's entry in the note index and answer lookups meant for the
    feature. STATUSES.md states that exemption and names this check as what
    covers plans instead — but the check was never written, so the exemption
    silently meant *no* check reached them: ``note_index`` is keyed by ID, and
    the per-note status walk skips a missing status outright. The measurable
    result, before this landed: 19 of 33 plans in project-os-cockpit carried
    no status at all, and three carried the forbidden ID, with the build
    green throughout.

    Three rules, in the order they matter:

    * **PLAN-ID** — a plan must not declare ``id:``. Error immediately: the
      population is tiny (three notes fleet-wide when this shipped, all
      fixed in the same change), and the failure mode it prevents is a
      silently wrong lookup rather than untidy metadata.
    * **PLAN-STATE** — a plan must carry a status drawn from its allowed
      set. Dated promotion (ADR-0011 clause 2) because the existing debt is
      real and clause 3 forbids promoting over it.
    * **PLAN-FOLLOWS** — a plan's status should track its parent feature's,
      which is what STATUSES.md means by "follows its parent feature ...
      advanced at close-out". Always a warning: the mapping is a convention
      with legitimate exceptions (a superseded delivery sequence under a live
      feature is the obvious one), and close-out is what reconciles it.
    """
    if not docs_dir.is_dir():
        return

    # Feature status -> plan status: PLAN_FOLLOWS_FEATURE, module-level and
    # checked by validate_status_tables. It was a local keyed on the retired
    # `in-progress`/`in-review` (ISS-0011), which silently disabled PLAN-FOLLOWS
    # for every actively-built feature.
    follows = PLAN_FOLLOWS_FEATURE

    allowed = allowed_status.get("plan") or set()
    for path in sorted(docs_dir.rglob("*.md")):
        if "__templates__" in path.parts or "__bases__" in path.parts:
            continue
        fm = parse_frontmatter(path)
        if not isinstance(fm, dict) or note_type(fm) != "plan":
            continue
        rel = path.relative_to(root).as_posix()
        label = rel

        declared_id = str(fm.get("id", "") or "").strip().strip("\"'")
        if declared_id:
            report.error(
                "PLAN-ID",
                "%s declares id: %s — plans must not carry an ID. "
                "`extract_ids` reads %s out of it, so the plan can claim its "
                "own feature's entry in the note index and answer lookups "
                "meant for the feature (tools/instructions/STATUSES.md, "
                "`[[plan]]`). Remove `id:` and `aliases:`; plans are found by "
                "type." % (label, declared_id, declared_id.split("-", 1)[-1]),
            )

        status = str(fm.get("status", "") or "").strip()
        emit = promotion_emit(report, "PLAN-STATE", grandfathered, rel)
        if not status:
            emit(
                "PLAN-STATE",
                "%s has no status — plans take one of %s and it is advanced at "
                "close-out (STATUSES.md, `[[plan]]`). Nothing else validates a "
                "plan's status: they are exempt from the ID-keyed checks."
                % (label, ", ".join(sorted(allowed)) or "the plan vocabulary"),
            )
            continue
        if allowed and status not in allowed:
            emit(
                "PLAN-STATE",
                "%s status '%s' not allowed for plan (allowed: %s)"
                % (label, status, ", ".join(sorted(allowed))),
            )
            continue

        # Does it track the feature it implements?
        parent_ids = set()
        for key in ("implements", "parent"):
            parent_ids.update(extract_ids(fm.get(key)))
        for parent_id in sorted(parent_ids):
            entry = NOTE_INDEX_FOR_PLANS.get(parent_id)
            if not entry:
                continue
            parent_fm = entry[1]
            if note_type(parent_fm) != "feature":
                continue
            parent_status = str(parent_fm.get("status", "") or "").strip()
            expected = follows.get(parent_status)
            if expected and status not in expected:
                report.warn(
                    "PLAN-FOLLOWS",
                    "%s is '%s' but %s is '%s' — a plan's status follows its "
                    "feature (expected %s). Close-out advances it; amend the "
                    "plan or the feature if the divergence is deliberate."
                    % (label, status, parent_id, parent_status,
                       " or ".join(sorted(expected))),
                )
            break

    # A PLAN.md that never became a note. It is not a contract violation —
    # plans are found by `type:`, so an untyped file simply is not one — but
    # it is the other half of why plans drift: 19 such files sat under
    # feature `plan/` directories in project-os-cockpit, invisible to every
    # check here and to every cockpit surface, while reading exactly like
    # the 14 that were notes. Warn so the choice is deliberate.
    for path in sorted(docs_dir.rglob("PLAN.md")):
        if "__templates__" in path.parts or "__bases__" in path.parts:
            continue
        fm = parse_frontmatter(path)
        if isinstance(fm, dict) and note_type(fm) == "plan":
            continue
        report.warn(
            "PLAN-UNTYPED",
            "%s has no `type: \"[[plan]]\"` frontmatter, so it is not a plan "
            "note: no status check reaches it, it cannot be linked by ID, and "
            "it never appears in the cockpit. Add plan frontmatter (see "
            "docs/__templates__/plan.md) or rename the file if it is prose."
            % path.relative_to(root).as_posix(),
        )


def validate(root, report):
    # Self-check first: it needs no repo state, and a validator whose own status
    # tables disagree cannot be trusted to report on anything else.
    validate_status_tables(report)

    snap_path = root / "SNAPSHOT.yaml"
    if not snap_path.is_file():
        report.error("SNAP-MISSING", "SNAPSHOT.yaml not found at repo root")
        return
    try:
        snap = load_yaml(snap_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        report.error("SNAP-PARSE", "SNAPSHOT.yaml failed to parse: %s" % exc)
        return
    if not isinstance(snap, dict):
        report.error("SNAP-PARSE", "SNAPSHOT.yaml did not parse to a mapping")
        return

    for key in ("version", "updated", "counters", "focus", "items"):
        if key not in snap:
            report.error("SNAP-KEYS", "SNAPSHOT.yaml missing required top-level key: %s" % key)

    items = snap.get("items") or {}
    counters = snap.get("counters") or {}
    docs_dir = root / "docs"
    note_index, note_claimants = build_note_index(docs_dir)
    allowed_status = load_allowed_status(root)
    grandfathered = load_grandfathered(root)
    verification_cfg = snap.get("verification") if isinstance(snap.get("verification"), dict) else {}
    try:
        staleness_days = int(verification_cfg.get("staleness_days", DEFAULT_STALENESS_DAYS))
    except (TypeError, ValueError):
        staleness_days = DEFAULT_STALENESS_DAYS

    def emit_for(gate, item_id):
        """report.warn when `item_id` was already violating `gate` at promotion, else report.error."""
        if item_id in grandfathered.get(gate, ()):
            return report.warn
        return report.error
    validate_unregistered_notes(root, items, note_index, note_claimants, allowed_status, report)
    NOTE_INDEX_FOR_PLANS.clear()
    NOTE_INDEX_FOR_PLANS.update(note_index)
    validate_brief(root, report)
    validate_design_notes(root, docs_dir, report)
    validate_plan_notes(root, docs_dir, allowed_status, grandfathered, report)

    def resolves(ref_id):
        for coll in items.values():
            if isinstance(coll, dict) and ref_id in coll:
                return True
        return ref_id in note_index

    # -- per-item checks
    all_snapshot_ids = []
    path_alias_items = []
    for coll_name, coll in (items.items() if isinstance(items, dict) else []):
        if not isinstance(coll, dict):
            continue
        expected_types = COLLECTION_TYPE.get(coll_name, set())
        for item_id, entry in coll.items():
            if not isinstance(entry, dict):
                report.error("ITEM-SHAPE", "%s.%s is not a mapping" % (coll_name, item_id))
                continue
            all_snapshot_ids.append(item_id)
            # SNAPSHOT.md specifies `file`; accept `path` as a legacy alias used by some downstream repos.
            file_rel = entry.get("file") or entry.get("path") or ""
            if not entry.get("file") and entry.get("path"):
                path_alias_items.append(item_id)
            fm = {}
            if not file_rel:
                report.error("ITEM-FILE", "%s has no file path in snapshot" % item_id)
            else:
                note_path = root / file_rel
                if not note_path.is_file():
                    report.error("ITEM-FILE", "%s file does not exist: %s" % (item_id, file_rel))
                else:
                    fm = parse_frontmatter(note_path) or {}
                    fm_id_raw = str(fm.get("id", "") or "").strip()
                    fm_ids = extract_ids(fm.get("id", ""))
                    if fm_id_raw != item_id and fm_ids and item_id not in fm_ids:
                        report.error("ITEM-ID", "%s note frontmatter id is %s (%s)" % (item_id, fm.get("id"), file_rel))
                    nt = note_type(fm)
                    if expected_types and nt and nt not in expected_types:
                        report.error("ITEM-TYPE", "%s note type '%s' not in %s (%s)" % (item_id, nt, sorted(expected_types), file_rel))
                    snap_status = entry.get("status", "")
                    fm_status = fm.get("status", "")
                    if snap_status and fm_status and str(snap_status) != str(fm_status):
                        report.error("ITEM-STATUS", "%s status drift: snapshot=%s note=%s (%s)" % (item_id, snap_status, fm_status, file_rel))
            status = str(entry.get("status", ""))
            # A collection may map to several note types -- `decisions` accepts
            # both `adr` and `decision`. Check the union: a status legal for any
            # accepted type is legal. This was `next(iter(expected_types), None)`
            # until ISS-0015, which picked ONE type out of an unordered set, so a
            # bogus status on a decisions-collection item errored or passed by
            # hash seed -- a per-run coin flip rather than a stable check. It
            # reads correct today only because `adr` and `decision` happen to
            # carry the same vocabulary; a repo customising one re-splits them.
            known = [t for t in sorted(expected_types or ()) if t in allowed_status]
            if status and known:
                legal = set()
                for t in known:
                    legal |= allowed_status[t]
                if status not in legal:
                    report.error("STATUS-VALUE", "%s status '%s' not allowed for %s (allowed: %s)" % (
                        item_id, status, "/".join(known), ", ".join(sorted(legal))))

            # -- link integrity
            for field in RELATIONSHIP_FIELDS:
                for ref in extract_ids(entry.get(field)):
                    if not resolves(ref):
                        report.error("LINK", "%s.%s references %s which resolves to no snapshot item or note" % (item_id, field, ref))

            # -- verification invariant
            terminal = TERMINAL.get(coll_name)
            # ADR-0007: requirements are gated on their acceptance criteria
            # (REQ-BOXES), never on linked tests. `verified` was retired
            # precisely because requirement-level test-gating was the wrong
            # instrument; re-applying it here — and only to requirements that
            # happen to link a test — would reintroduce it through the back
            # door and perversely punish linking one at all. Test status stays
            # informational for requirements; VERIFY still gates tasks, issues
            # and features, where linked tests are the agreed instrument.
            if coll_name == "requirements":
                terminal = None
            if terminal and status == terminal:
                waiver = str(fm.get("verification_waiver", "") or entry.get("verification_waiver", "")).strip()
                linked_tests = set(extract_ids(entry.get("tests"))) | set(extract_ids(fm.get("tests")))
                if waiver:
                    expires_raw = fm.get("waiver_expires") or entry.get("waiver_expires")
                    expires = _parse_date(expires_raw)
                    if not has_value(expires_raw):
                        emit_for("WAIVER", item_id)(
                            "WAIVER",
                            "%s is %s under a waiver with no waiver_expires:; an open-ended waiver is a rule "
                            "deletion written in the passive voice (ADR-0010)" % (item_id, terminal))
                    elif expires is None:
                        emit_for("WAIVER", item_id)(
                            "WAIVER", "%s waiver_expires is not a YYYY-MM-DD date: %r" % (item_id, expires_raw))
                    elif expires < _today():
                        emit_for("WAIVER", item_id)(
                            "WAIVER", "%s is %s under a waiver that expired %s; renew it with a reason or "
                            "satisfy the gate" % (item_id, terminal, expires))
                    else:
                        report.warn("VERIFY-WAIVED", "%s is %s under recorded waiver (expires %s): %s"
                                    % (item_id, terminal, expires, waiver))
                else:
                    for tst in sorted(linked_tests):
                        tst_status = ""
                        tests_coll = items.get("tests") or {}
                        if tst in tests_coll and isinstance(tests_coll[tst], dict):
                            tst_status = str(tests_coll[tst].get("status", ""))
                        elif tst in note_index:
                            tst_status = str((note_index[tst][1] or {}).get("status", ""))
                        else:
                            emit_for("VERIFY", item_id)("VERIFY", "%s is %s but linked test %s was not found" % (item_id, terminal, tst))
                            continue
                        if tst_status != "passing":
                            emit_for("VERIFY", item_id)("VERIFY", "%s is %s but linked test %s is '%s', not passing" % (item_id, terminal, tst, tst_status))
                        elif tst in note_index and is_stale(note_index[tst][1], staleness_days):
                            # REQ-0023: verification that was true a year ago is not
                            # evidence about today's system.
                            emit_for("VERIFY", item_id)(
                                "VERIFY", "%s is %s but linked manual test %s is passing yet stale (last_verified over %d days ago)"
                                % (item_id, terminal, tst, staleness_days))
                    if coll_name == "features":
                        for task_ref in extract_ids(entry.get("tasks")):
                            t_entry = (items.get("tasks") or {}).get(task_ref)
                            t_status = str(t_entry.get("status", "")) if isinstance(t_entry, dict) else str((note_index.get(task_ref, (None, {}))[1] or {}).get("status", ""))
                            if t_status and t_status not in RESOLVED_STATUSES:
                                emit_for("VERIFY", item_id)("VERIFY", "%s is done but task %s is '%s', not scope-resolved (%s)" % (item_id, task_ref, t_status, "/".join(RESOLVED_STATUSES)))

            # -- deferral invariants (STATUSES.md "Deferral and re-adoption")
            if coll_name == "features":
                for task_ref in extract_ids(entry.get("tasks")):
                    t_entry = (items.get("tasks") or {}).get(task_ref)
                    t_status = str(t_entry.get("status", "")) if isinstance(t_entry, dict) else str((note_index.get(task_ref, (None, {}))[1] or {}).get("status", ""))
                    if t_status == "deferred":
                        report.error("DEFER-SCOPE", "%s lists deferred task %s in tasks: (its scope); descope it into deferred: per the deferral procedure (tools/skills/status-transition/SKILL.md)" % (item_id, task_ref))
            # a blank snapshot status must not mask a deferred note
            eff_status = status or str(fm.get("status", "") or "")
            if eff_status == "deferred" and coll_name in ("tasks", "issues", "requirements", "features"):
                if not (has_value(entry.get("phase")) or has_value(fm.get("phase"))):
                    report.error("DEFER-HOME", "%s is deferred without a forward home: set phase to a future phase or the PHASE-999 parking lot" % item_id)
                if coll_name == "tasks":
                    if not (has_value(entry.get("origin")) or has_value(fm.get("origin"))):
                        report.error("DEFER-ORIGIN", "%s is deferred without origin provenance (the former parent)" % item_id)
                    if has_value(entry.get("parent")) or has_value(fm.get("parent")):
                        report.error("DEFER-PARENT", "%s is deferred but still has a parent; descoping clears parent (origin + phase replace it while parked)" % item_id)

    # -- test verification fields (ADR-0010; REQ-0022 / REQ-0023)
    for the_id, (path, fm) in sorted(note_index.items()):
        if note_type(fm) != "test":
            continue
        rel = path.relative_to(root).as_posix()
        command = str((fm or {}).get("command", "") or "").strip()
        status = str((fm or {}).get("status", "") or "").strip()
        if command:
            # An executable test's status is the runner's output, so it must carry
            # the run that produced it. A stamped status with no `last_run` means
            # somebody typed it -- the exact thing ADR-0010 removes.
            if status in TEST_RUNNER_STATUSES and not has_value((fm or {}).get("last_run")):
                emit_for("TEST-FIELDS", the_id)(
                    "TEST-FIELDS",
                    "%s declares a command: and is '%s' but has no last_run:; an executable test's status is "
                    "written by tools/scripts/run-tests.py, never by hand (ADR-0010) (%s)" % (the_id, status, rel))
        else:
            if not has_value((fm or {}).get("last_verified")):
                emit_for("TEST-FIELDS", the_id)(
                    "TEST-FIELDS",
                    "%s is a manual test with no last_verified:; record when the procedure was last performed, "
                    "or give it a command: so it can be executed (%s)" % (the_id, rel))
            elif is_stale(fm, staleness_days):
                report.warn(
                    "TEST-STALE",
                    "%s was last verified %s, over %d days ago; it no longer satisfies the verification gate (%s)"
                    % (the_id, str((fm or {}).get("last_verified")).strip('"'), staleness_days, rel))

    # -- requirement lifecycle (QUALITY.md; close-out "Requirement advancement")
    def effective_status(the_id):
        for coll in (items.values() if isinstance(items, dict) else []):
            if isinstance(coll, dict) and isinstance(coll.get(the_id), dict):
                snap_status = str(coll[the_id].get("status", "") or "")
                if snap_status:
                    return snap_status
        if the_id in note_index:
            return str((note_index[the_id][1] or {}).get("status", "") or "")
        return ""

    def prefix_of(the_id):
        m = ID_RE.match(the_id)
        return m.group(1) if m else ""

    reqs_coll = items.get("requirements") if isinstance(items.get("requirements"), dict) else {}
    req_ids = {k for k in reqs_coll if prefix_of(k) == "REQ"}
    req_ids.update(nid for nid, (_p, nfm) in note_index.items() if note_type(nfm) == "requirement")

    feature_reqs = {}  # FEAT id -> set of REQ ids it claims to implement
    for fid, fentry in (items.get("features") or {}).items():
        if isinstance(fentry, dict):
            feature_reqs.setdefault(fid, set()).update(extract_ids(fentry.get("requirements")))
    for nid, (_p, nfm) in note_index.items():
        if note_type(nfm) == "feature":
            feature_reqs.setdefault(nid, set()).update(extract_ids((nfm or {}).get("requirements")))

    for req_id in sorted(req_ids):
        entry = reqs_coll.get(req_id) if isinstance(reqs_coll.get(req_id), dict) else {}
        note_path, fm = note_index.get(req_id, (None, {}))
        status = effective_status(req_id)
        # implementing features: the requirement's own `implements:` plus any feature claiming it
        feats = {f for f in set(extract_ids(entry.get("implements"))) | set(extract_ids((fm or {}).get("implements"))) if prefix_of(f) == "FEAT"}
        feats.update(fid for fid, reqs in feature_reqs.items() if req_id in reqs and prefix_of(fid) == "FEAT")
        feat_status = {f: effective_status(f) for f in feats}
        known = {f: s for f, s in feat_status.items() if s}
        all_resolved = bool(known) and all(s in RESOLVED_STATUSES for s in known.values())
        if status in REQ_UNADVANCED_STATUSES and all_resolved:
            report.error("REQ-STALE", "%s is '%s' but every implementing feature (%s) has reached a terminal status; advance it per close-out 'Requirement advancement' (tick criteria with evidence, reconcile departures, set implemented) or supersede it" % (req_id, status, ", ".join("%s=%s" % (f, known[f]) for f in sorted(known))))
        elif status == "draft" and any(s in FEATURE_ACTIVE_STATUSES for s in known.values()):
            active = sorted(f for f, s in known.items() if s in FEATURE_ACTIVE_STATUSES)
            report.warn("REQ-PREMATURE", "%s is still draft but %s is already being implemented; approve or amend the requirement first (feature-scaffold 'Requirement approval gate')" % (req_id, ", ".join(active)))
        # -- ADR-0007: `implements:` names at most one feature
        own_feats = sorted({
            f for f in (extract_ids(entry.get("implements")) + extract_ids((fm or {}).get("implements")))
            if prefix_of(f) == "FEAT"
        })
        if len(own_feats) > 1:
            report.error("REQ-OWNER", "%s implements %d features (%s) but a requirement names at most one (ADR-0007); split the requirement, or pick the true owner and drop the rest" % (req_id, len(own_feats), ", ".join(own_feats)))

        if status == "implemented" and note_path is not None:
            # `reconciled` (`- [~]`) counts toward the verification record and toward
            # box/criterion parity: STATUSES.md defines the gate as "ticked-with-evidence
            # OR reconciled", so a requirement that honestly reconciles a criterion it did
            # not deliver must not then be reported as missing a box for it.
            unticked, ticked, reconciled = count_acceptance_boxes(note_path, with_reconciled=True)
            ticked += reconciled
            criteria = entry.get("acceptance") or (fm or {}).get("acceptance") or []
            n_criteria = len(criteria) if isinstance(criteria, list) else 0
            # Forward-only, as for FEATURE-REQ: a requirement that went terminal
            # before the cutover is grandfathered to a warning (visible debt);
            # one advanced or touched afterwards is a build failure.
            emit = emit_for("REQ-BOXES", req_id)
            if unticked:
                emit("REQ-BOXES", "%s is '%s' (terminal) but %d acceptance criterion/criteria remain unticked (%s); tick with evidence or reconcile them" % (req_id, status, unticked, note_path.relative_to(root)))
            elif n_criteria and not (unticked + ticked):
                emit("REQ-BOXES", "%s is '%s' (terminal) with %d acceptance criteria but no verification record — its note has no ticked acceptance checkboxes (%s); add one box per criterion with an evidence pointer (SCHEMAS.md)" % (req_id, status, n_criteria, note_path.relative_to(root)))
            elif n_criteria and (unticked + ticked) != n_criteria:
                emit("REQ-BOXES", "%s is '%s' (terminal) with %d criteria of record but %d acceptance checkbox(es) (%s); SCHEMAS.md requires one box per criterion, so the verification record is partial" % (req_id, status, n_criteria, unticked + ticked, note_path.relative_to(root)))

    # -- ADR-0007 FEATURE-REQ: a feature may not be `done` while a requirement
    #    naming it still has an unresolved acceptance criterion. Forward-only.
    reqs_by_owner = {}   # FEAT id -> [(REQ id, note_path)]
    for req_id in sorted(req_ids):
        note_path, fm = note_index.get(req_id, (None, {}))
        if note_path is None:
            continue
        if effective_status(req_id) in DESCOPED_STATUSES:
            continue
        r_entry = reqs_coll.get(req_id) if isinstance(reqs_coll.get(req_id), dict) else {}
        owners = set(extract_ids(r_entry.get("implements"))) | set(extract_ids((fm or {}).get("implements")))
        for f in sorted(owners):
            if prefix_of(f) == "FEAT":
                reqs_by_owner.setdefault(f, []).append((req_id, note_path))

    for feat_id, owned in sorted(reqs_by_owner.items()):
        if effective_status(feat_id) != "done":
            continue
        f_path, f_fm = note_index.get(feat_id, (None, {}))
        unresolved = []
        for req_id, req_path in owned:
            unticked, ticked = count_acceptance_boxes(req_path)
            if unticked:
                unresolved.append("%s (%d unticked)" % (req_id, unticked))
        if not unresolved:
            continue
        emit = emit_for("FEATURE-REQ", feat_id)
        noun = ("a requirement it owns has" if len(unresolved) == 1
                else "requirements it owns have")
        emit("FEATURE-REQ", "%s is done but %s unresolved acceptance criteria: %s; tick with evidence, reconcile, or descope the requirement before closing the feature (ADR-0007)" % (feat_id, noun, ", ".join(unresolved)))

    # -- ISS-0357 PHASE-CHILDREN / PHASE-BOXES: a closed phase must have closed
    #    its children and recorded evidence for its exit criteria.
    #
    #    Both gates read the *children* — every note whose `phase:` names the phase —
    #    rather than the phase's own `features:` list. The drift these were written for
    #    was entirely in children left pointing at a phase after their owning feature
    #    had moved on (six PHASE-011 notes whose features had migrated to PHASE-015);
    #    a features-list check sees nothing wrong in that shape.
    #
    #    `deferred` is unresolved on purpose (STATUSES.md, "Deferral and re-adoption"):
    #    parking an item does not close the phase that owns it. Re-home a deferred item
    #    to the phase that will carry it — usually PHASE-999 — and the gate is satisfied
    #    by the relationship rather than by the word.
    #
    #    PHASE_RESOLVED and CLOSED_PHASE_STATUSES are module-level constants, checked
    #    against ALLOWED_STATUS by validate_status_tables (STATUS-TABLE). They used to
    #    be locals here, which is precisely why ISS-0011 went unnoticed: no test could
    #    reach them.

    children_by_phase = {}   # PHASE id -> [(child id, child status)]
    for child_id, (_c_path, c_fm) in note_index.items():
        ctype = note_type(c_fm)
        if ctype not in PHASE_RESOLVED:
            continue
        for ph_id in extract_ids((c_fm or {}).get("phase")):
            if prefix_of(ph_id) == "PHASE":
                children_by_phase.setdefault(ph_id, []).append((child_id, ctype))

    for ph_id, (ph_path, ph_fm) in sorted(note_index.items()):
        if note_type(ph_fm) != "phase":
            continue
        ph_status = effective_status(ph_id)
        if ph_status not in CLOSED_PHASE_STATUSES:
            continue
        open_children = sorted(
            "%s (%s)" % (cid, effective_status(cid) or "?")
            for cid, ctype in children_by_phase.get(ph_id, [])
            if effective_status(cid) not in PHASE_RESOLVED[ctype]
        )
        if open_children:
            emit = emit_for("PHASE-CHILDREN", ph_id)
            emit("PHASE-CHILDREN", "%s is '%s' but %d item(s) still name it as their phase without a resolved status: %s; resolve them, or re-home each to the phase that now owns its work (%s)" % (
                ph_id, ph_status, len(open_children), ", ".join(open_children), ph_path.relative_to(root)))

        if ph_status != "done":
            continue   # a superseded phase's criteria moved to its successor
        unticked, ticked, reconciled = count_acceptance_boxes(
            ph_path, heading=r"Exit\b", require_heading=True, with_reconciled=True)
        emit = emit_for("PHASE-BOXES", ph_id)
        if unticked:
            emit("PHASE-BOXES", "%s is done but %d exit criterion/criteria remain unticked (%s); tick each with an evidence pointer, or mark it `- [~]` with the reason it was cut" % (
                ph_id, unticked, ph_path.relative_to(root)))
        elif not (ticked or reconciled):
            # Without this, `require_heading` makes the gate vacuous exactly where it
            # matters most: a done phase with no Exit section — or one whose heading
            # was renamed — scored (0, 0) and passed silently. "No criteria recorded"
            # is the same missing-evidence failure as "criteria left unticked".
            #
            # `reconciled` is counted here so an all-`[~]` phase is not reported as
            # having no criteria: it recorded every one of them and delivered none,
            # which is a different (and honestly documented) state.
            emit("PHASE-BOXES", "%s is done but records no exit criteria (%s); add an `## Exit Criteria` section with one checkbox per criterion, each ticked with an evidence pointer or marked `- [~]` with the reason it was cut" % (
                ph_id, ph_path.relative_to(root)))

    # -- deferred notes must stay in the snapshot (SNAPSHOT.md retention)
    for item_id, (path, fm) in sorted(note_index.items()):
        if str((fm or {}).get("status", "") or "") != "deferred":
            continue
        if not ID_RE.match(item_id) or ID_RE.match(item_id).group(1) not in ("TASK", "ISS", "REQ", "FEAT", "PHASE"):
            continue
        in_snapshot = any(isinstance(c, dict) and item_id in c for c in items.values()) if isinstance(items, dict) else False
        if not in_snapshot:
            report.error("DEFER-RETENTION", "%s is deferred but missing from SNAPSHOT.yaml; deferred items are active and never pruned (%s)" % (item_id, path.relative_to(root)))

    # -- counter integrity (snapshot IDs and note IDs)
    if path_alias_items:
        report.warn("PATH-ALIAS", "%d item(s) use legacy `path:` instead of `file:` (e.g. %s); prefer `file:` per SNAPSHOT.md" % (len(path_alias_items), path_alias_items[0]))

    def check_counter(the_id, origin):
        m = ID_RE.match(the_id)
        if not m:
            return
        prefix, digits = m.group(1), m.group(2)
        num = int(digits)
        if is_sentinel_id(digits):
            return  # PHASE-999 / PHASE-0999 parking lot
        limit = counters.get(prefix)
        if isinstance(limit, str) and limit.isdigit():
            limit = int(limit)
        if isinstance(limit, int) and num > limit:
            report.error("COUNTER", "%s (%s) exceeds counters.%s = %s in SNAPSHOT.yaml" % (the_id, origin, prefix, limit))

    for sid in all_snapshot_ids:
        check_counter(sid, "snapshot")
    for nid in sorted(note_index):
        check_counter(nid, str(note_index[nid][0].relative_to(root)))

    # -- metrics counts (computed vs recorded; SNAPSHOT.md "Metrics")
    metrics = snap.get("metrics") or {}
    counts = metrics.get("counts") if isinstance(metrics, dict) else None
    if isinstance(counts, dict):
        computed = compute_metric_counts(items, note_index)
        for key in sorted(counts):
            if key not in computed:
                continue
            val = counts[key]
            try:
                recorded = int(val)
            except (TypeError, ValueError):
                report.error("METRICS", "metrics.counts.%s is not an integer: %r" % (key, val))
                continue
            if recorded != computed[key]:
                report.error("METRICS", "metrics.counts.%s is %d but computed %d (run validate-docs.sh --fix-metrics)" % (key, recorded, computed[key]))

    # -- independent-review fields (QUALITY.md "Independent review (different-model)")
    for coll_name, settled in sorted(REVIEW_SETTLED_STATUSES.items()):
        coll = items.get(coll_name) or {}
        if not isinstance(coll, dict):
            continue
        for item_id, entry in coll.items():
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("status", ""))
            if status not in settled:
                continue
            file_rel = entry.get("file") or entry.get("path") or ""
            fm = parse_frontmatter(root / file_rel) or {} if file_rel and (root / file_rel).is_file() else {}
            verdict = str(fm.get("review_verdict", "") or entry.get("review_verdict", "") or "").strip()
            if verdict == "changes-requested":
                report.error("REVIEW", "%s is '%s' but review_verdict is changes-requested" % (item_id, status))
            elif not verdict:
                promotion_emit(report, "REVIEW", grandfathered, item_id)(
                    "REVIEW",
                    "%s is '%s' without independent review (reviewed_by/review_verdict); see QUALITY.md "
                    "— becomes an error on %s (ADR-0011)" % (item_id, status, PROMOTIONS["REVIEW"]))

    # -- focus resolution
    focus = snap.get("focus") or {}
    if isinstance(focus, dict):
        for key in ("feature", "task", "issue", "phase"):
            for ref in extract_ids(focus.get(key, "")):
                if not resolves(ref):
                    report.error("FOCUS", "focus.%s = %s resolves to no snapshot item or note" % (key, ref))

    # -- note frontmatter link integrity for notes referenced by the snapshot
    for item_id, (path, fm) in sorted(note_index.items()):
        if not fm:
            continue
        in_snapshot = any(isinstance(c, dict) and item_id in c for c in items.values()) if isinstance(items, dict) else False
        if not in_snapshot:
            continue  # archived notes may reference pruned history; docs-audit covers them
        for field in RELATIONSHIP_FIELDS:
            for ref in extract_ids(fm.get(field)):
                if not resolves(ref):
                    report.error("LINK", "%s frontmatter %s references %s which resolves to no snapshot item or note (%s)" % (item_id, field, ref, path.relative_to(root)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate project-os SNAPSHOT.yaml <-> docs/ consistency.")
    ap.add_argument("--repo-root", default=None, help="Repo root (default: nearest ancestor with SNAPSHOT.yaml)")
    ap.add_argument("--quiet", action="store_true", help="Suppress warnings and the success line")
    ap.add_argument("--fix-metrics", action="store_true", help="Rewrite metrics.counts to the computed counts before validating")
    ap.add_argument("--self-check", action="store_true", help="Run only the validator's internal consistency checks (STATUS-TABLE) and exit; needs no repo")
    args = ap.parse_args(argv)

    # Internal-consistency only: no SNAPSHOT.yaml, no docs/, no repo at all.
    #
    # This is what TST-0002 executes, and the separation is deliberate. Pointing
    # that note at the full validator deadlocked: its `command:` reported every
    # repo error, so the moment run-tests stamped it `failing` the VERIFY gate on
    # the issue linking it became one more error, and no subsequent run could
    # ever return 0. A test that gates on its own result cannot converge. Scope
    # each test note to the invariant it actually names -- TST-0001 already owns
    # "the whole repo validates".
    if args.self_check:
        report = Report()
        validate_status_tables(report)
        for line in report.errors:
            print(line)
        if report.errors:
            print("validate-docs: FAIL (%d error%s)" % (len(report.errors), "s" if len(report.errors) != 1 else ""))
            return 1
        if not args.quiet:
            print("validate-docs: self-check OK (status tables consistent)")
        return 0

    if args.repo_root:
        root = Path(args.repo_root).resolve()
    else:
        root = Path.cwd().resolve()
        while root != root.parent and not (root / "SNAPSHOT.yaml").is_file():
            root = root.parent
    if not (root / "SNAPSHOT.yaml").is_file():
        print("validate-docs: no SNAPSHOT.yaml found from %s upward" % Path.cwd(), file=sys.stderr)
        return 2

    if args.fix_metrics:
        try:
            for change in fix_metrics(root):
                print("validate-docs: fixed metrics.counts.%s" % change)
        except Exception as exc:  # noqa: BLE001
            print("validate-docs: --fix-metrics failed: %s" % exc, file=sys.stderr)
            return 2

    report = Report()
    try:
        validate(root, report)
    except Exception as exc:  # noqa: BLE001
        print("validate-docs: internal error: %s" % exc, file=sys.stderr)
        return 2

    for line in report.errors:
        print(line)
    if not args.quiet:
        for line in report.warnings:
            print(line)
    if report.errors:
        print("validate-docs: FAIL (%d error%s)" % (len(report.errors), "s" if len(report.errors) != 1 else ""))
        return 1
    if not args.quiet:
        print("validate-docs: OK (%s)" % root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
