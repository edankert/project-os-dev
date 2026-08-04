#!/usr/bin/env python3
"""Sync SNAPSHOT.yaml's derived fields from note frontmatter (ADR-0009).

97% of the commits that touch SNAPSHOT.yaml also touch a note in the same
commit: every status change is written twice, by hand. A further 494 commits
changed a note *without* touching the snapshot -- that population is where drift
comes from, and three validator checks (ITEM-STATUS, COUNTER, METRICS) exist for
no purpose except detecting the two copies disagreeing.

This makes the note authoritative for the fields that can be derived.

WHY A SURGICAL UPDATER, NOT A GENERATOR
---------------------------------------
The first implementation regenerated the whole file. A shadow run against all 10
repos rejected that design, and the rejection is worth recording: a snapshot is
not a pure function of `docs/`. It is duplication *plus curation* --

  * ~80 lines of hand-written comments with no frontmatter home
    ("# Pruned: FEAT-0001..0006 (all done)", rationale beside a counter);
  * a curated retention set that no count-based rule reproduces (153 items
    would have been dropped, 180 added);
  * editorial `goal:` / `note:` prose that lives nowhere else.

Regenerating destroys the curated half to fix the duplicated half. So this
script rewrites only the fields that are genuinely derived, in place, and leaves
every byte it does not own:

  UPDATED IN PLACE   an entry's `status`, `title` and `goal` (from the note),
                     `counters`, `metrics`
  REMOVED            terminal entries the retention rule matches (ADR-0018)
  LEFT ALONE         comments, ordering, item-level `note:` prose, focus,
                     project, team, and every entry the rule does not match

Unregistered notes are REPORTED, never auto-added: membership may be narrowed
by a reproducible rule but never widened, because adding is the curation
decision ADR-0009 reserved and ADR-0018 did not reclaim.

BOTH ADDITIONS ARE INERT UNTIL A REPO OPTS IN
---------------------------------------------
`retention.derive_fields` enables title/goal derivation; `retention.prune_window`
enables pruning and sets N. Absent means off. The script therefore lands in
twelve repos changing nothing, and each opts in on its own commit -- without
which every repo's CI would fail `--check` on the same day (TASK-0085).

Retention removes finished business, never unfinished: an entry is held back by
non-empty `note:`, by an outstanding `verification_waiver`, or by a linked test
that is not passing. Eighteen validator codes are emitted from the walk over
`items.*`, so a pruned entry stops being checked -- without those holds,
pruning silenced 12 waiver expiries and 3 VERIFY warnings in testing.

Exit codes: 0 = clean/updated, 1 = --check found drift, 2 = usage error.

Stdlib only. Usage:
    sync-snapshot.py [--repo-root PATH] [--check] [--quiet]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        "_vd", Path(__file__).resolve().parent / "validate-docs.py")
    _vd = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_vd)  # type: ignore[union-attr]
except Exception as exc:  # pragma: no cover
    print("sync-snapshot: cannot load validate-docs.py (%s)" % exc, file=sys.stderr)
    raise

# Reuse the validator's parsers. Two frontmatter readers that disagree would be a
# whole new class of drift, and removing one is the point of this script.
load_yaml = _vd.load_yaml
build_note_index = _vd.build_note_index
note_type = _vd.note_type
compute_metric_counts = _vd.compute_metric_counts
ID_RE = _vd.ID_RE

COLLECTION_OF = {
    "feature": "features", "task": "tasks", "issue": "issues",
    "requirement": "requirements", "phase": "phases", "risk": "risks",
    "test": "tests", "workflow": "workflows", "change": "changes",
    "adr": "decisions", "decision": "decisions", "release": "releases",
    "design": "designs",
}

_ITEM_RE = re.compile(r"^(\s+)([A-Z]+-[\w-]+):\s*(\{.*\})?\s*$")
_STATUS_BLOCK_RE = re.compile(r"^(\s+status:\s*)(.+?)(\s*)$")
_STATUS_INLINE_RE = re.compile(r"(\bstatus:\s*)([A-Za-z][\w-]*)")

#: Fields derived from the note, per ADR-0018 rule 1. The test is whether the
#: field has a counterpart in the note's frontmatter -- `title` and feature
#: `goal` do, `note` does not (it is scratch context; ADR-0018 rule 3).
DERIVED_FIELDS = ("title", "goal")


def _yaml_quote(value):
    """Double-quote a scalar so it is safe in BOTH block and inline-flow context.

    Titles legitimately contain commas, braces and quotes -- 16 of the fleet's
    3,164 carry braces and 3 carry double quotes -- so an unquoted emission
    would corrupt an inline flow mapping. Always quoting is the only shape that
    is correct in both places.
    """
    return '"%s"' % str(value).replace("\\", "\\\\").replace('"', '\\"')


def _scalar_span(line, key):
    """Span (start, end) of `key`'s VALUE in a snapshot line, or None.

    Handles the two styles the fleet actually writes:
      block   `      title: "text"`            -- value runs to end of line
      inline  `    ID: { title: "text", ... }` -- value ends at the quote, or at
                                                  the next `,`/`}` when bare

    Scanning rather than regexing matters: a naive `title: "(.*)"` mis-ends on
    the first embedded quote, and `[^,]*` mis-ends on the first embedded comma.
    """
    body = line.rstrip("\n")
    brace = body.find("{")
    if brace == -1:
        m = re.match(r"^\s+%s:[ \t]*" % re.escape(key), body)
        if not m:
            return None
        return (m.end(), len(body))

    # inline flow mapping: find `key:` at depth 1, outside any quoted scalar
    i, depth, quote = brace, 0, None
    while i < len(body):
        ch = body[i]
        if quote:
            if ch == "\\" and quote == '"':
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif depth == 1 and body.startswith(key + ":", i):
            before = body[i - 1] if i else ","
            if before in "{, \t":
                j = i + len(key) + 1
                while j < len(body) and body[j] in " \t":
                    j += 1
                return (j, _value_end(body, j))
        i += 1
    return None


def _value_end(body, start):
    """End offset of the flow-scalar beginning at `start`."""
    if start < len(body) and body[start] in "\"'":
        q, j = body[start], start + 1
        while j < len(body):
            if body[j] == "\\" and q == '"':
                j += 2
                continue
            if body[j] == q:
                return j + 1
            j += 1
        return len(body)
    j, depth = start, 0
    while j < len(body):
        ch = body[j]
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            if depth == 0:
                break
            depth -= 1
        elif ch == "," and depth == 0:
            break
        j += 1
    return len(body[:j].rstrip())


def note_statuses(root):
    """id -> frontmatter status, using only notes that genuinely CLAIM that id.

    The validator's `index` matches IDs as substrings, so composite names
    legitimately resolve to the wrong note: `CHG-20260525-FEAT-0009-Chrome-Polish`
    is indexed under FEAT-0009 and sorts first, which would have propagated a
    change note's `merged` onto a feature. `claimants` holds only real claims
    (frontmatter id, or an ID-prefixed filename), which is what authority requires.
    """
    index, claimants = build_note_index(root / "docs")
    out = {}
    for the_id, paths in claimants.items():
        if len(paths) != 1:
            continue  # ambiguous: NOTE-DUP-ID reports it; do not guess
        entry = index.get(the_id)
        if not entry or entry[0] != paths[0]:
            fm = _vd.parse_frontmatter(paths[0]) or {}
        else:
            fm = entry[1] or {}
        st = str(fm.get("status", "") or "").strip()
        if st:
            out[the_id] = st
    return out, index


def sync_statuses(lines, statuses):
    """Rewrite each item entry's status to match its note. Returns list of changes."""
    changes, current_id, in_items = [], None, False
    for i, line in enumerate(lines):
        if re.match(r"^items:\s*$", line):
            in_items = True
            continue
        if in_items and re.match(r"^\S", line):
            in_items = False
        if not in_items:
            continue

        m = _ITEM_RE.match(line)
        if m:
            current_id = m.group(2)
            inline = m.group(3)
            if inline and current_id in statuses:
                want = statuses[current_id]

                def _sub(mm, want=want, cid=current_id):
                    if mm.group(2) != want:
                        changes.append((cid, mm.group(2), want))
                        return "%s%s" % (mm.group(1), want)
                    return mm.group(0)

                new = _STATUS_INLINE_RE.sub(_sub, line)
                if new != line:
                    lines[i] = new
            continue

        m = _STATUS_BLOCK_RE.match(line)
        if m and current_id and current_id in statuses:
            have = m.group(2).strip().strip("\"'")
            want = statuses[current_id]
            if have != want:
                changes.append((current_id, have, want))
                lines[i] = "%s%s\n" % (m.group(1), want)
    return changes


def note_fields(root):
    """id -> {field: value} for the derived fields, from notes that CLAIM the id.

    Fail-safe, per ADR-0018 and TASK-0083: an id appears here only when a single
    note claims it AND supplies a non-empty value. Everything else -- missing
    note, zero-byte file, unparseable frontmatter, absent or blank `title:`,
    ambiguous claim -- is simply absent, so the caller leaves the snapshot value
    untouched. Seventeen notes in the fleet are in exactly that state (3
    zero-byte, 14 unparseable), plus 161 CHG-* entries whose date-slug ids no
    note claims; blindly writing `note.title` over them would blank every one.
    """
    _, claimants = build_note_index(root / "docs")
    out = {}
    for the_id, paths in sorted(claimants.items()):
        if len(paths) != 1:
            continue  # ambiguous claim: NOTE-DUP-ID reports it; never guess
        try:
            fm = _vd.parse_frontmatter(paths[0]) or {}
        except Exception:
            continue  # unparseable frontmatter -> leave the snapshot alone
        vals = {}
        for field in DERIVED_FIELDS:
            v = fm.get(field)
            if isinstance(v, str) and v.strip():
                vals[field] = v.strip()
        if vals:
            out[the_id] = vals
    return out


def sync_derived_fields(lines, fields, enabled):
    """Rewrite each entry's `title`/`goal` from its note. Returns list of changes.

    `enabled` is the per-repo opt-in (ADR-0018 / TASK-0085): when false this
    still REPORTS every divergence but writes nothing, which is the report mode
    the fleet rollout ships with.
    """
    changes, current_id, in_items = [], None, False
    for i, line in enumerate(lines):
        if re.match(r"^items:\s*$", line):
            in_items = True
            continue
        if in_items and re.match(r"^\S", line):
            in_items = False
        if not in_items:
            continue

        m = _ITEM_RE.match(line)
        if m:
            current_id = m.group(2)
            if not m.group(3):
                continue  # block-style entry: its fields are on following lines
        elif current_id is None:
            continue

        want = fields.get(current_id)
        if not want:
            continue
        for field, value in want.items():
            span = _scalar_span(lines[i], field)
            if not span:
                continue
            body = lines[i].rstrip("\n")
            have_raw = body[span[0]:span[1]]
            try:
                have = load_yaml("v: " + have_raw).get("v") if have_raw else None
            except Exception:
                have = have_raw.strip().strip("\"'")
            if isinstance(have, str) and have.strip() == value:
                continue
            changes.append((current_id, field, str(have), value))
            if enabled:
                nl = "\n" if lines[i].endswith("\n") else ""
                lines[i] = body[:span[0]] + _yaml_quote(value) + body[span[1]:] + nl
            if not m:
                break  # block style: one field per line
    return changes


def sync_counters(lines, index):
    """counters.<PREFIX> = max observed ID. All-9s sentinels are exempt, as in the validator."""
    observed = {}
    for the_id in index:
        m = ID_RE.match(the_id)
        if not m:
            continue
        prefix, digits = m.group(1), m.group(2)
        if _vd.is_sentinel_id(digits):
            continue  # PHASE-999 / PHASE-0999 parking lot -- see validator
        observed[prefix] = max(observed.get(prefix, 0), int(digits))

    changes, in_counters = [], False
    for i, line in enumerate(lines):
        if re.match(r"^counters:\s*$", line):
            in_counters = True
            continue
        if in_counters and re.match(r"^\S", line):
            in_counters = False
        if not in_counters:
            continue
        m = re.match(r"^(  ([A-Z]+):\s*)(\d+)(\s*(?:#.*)?)$", line.rstrip("\n"))
        # Counters only ever RISE. An ID is allocated, not owned: lowering a counter
        # because its note was deleted would hand the same ID to the next item.
        if m and m.group(2) in observed and observed[m.group(2)] > int(m.group(3)):
            changes.append((m.group(2), m.group(3), observed[m.group(2)]))
            lines[i] = "%s%d%s\n" % (m.group(1), observed[m.group(2)], m.group(4))
    return changes


def sync_metrics(lines, snap, index):
    computed = compute_metric_counts(snap.get("items") or {}, index)
    changes, in_metrics, in_counts = [], False, False
    for i, line in enumerate(lines):
        if re.match(r"^metrics:\s*$", line):
            in_metrics = True
            continue
        if in_metrics and re.match(r"^\S", line):
            break
        if in_metrics and re.match(r"^\s+counts:\s*$", line):
            in_counts = True
            continue
        if not in_counts:
            continue
        m = re.match(r"^(\s*)([\w-]+):\s*(-?\d+)\s*(#.*)?$", line.rstrip("\n"))
        if m and m.group(2) in computed and int(m.group(3)) != computed[m.group(2)]:
            changes.append((m.group(2), m.group(3), computed[m.group(2)]))
            trailing = (" " + m.group(4)) if m.group(4) else ""
            lines[i] = "%s%s: %d%s\n" % (m.group(1), m.group(2), computed[m.group(2)], trailing)
    return changes


def unregistered(snap, index):
    registered = set()
    for coll in (snap.get("items") or {}).values():
        if isinstance(coll, dict):
            registered.update(coll.keys())
    out = []
    for the_id, (path, fm) in sorted(index.items()):
        if the_id in registered or not COLLECTION_OF.get(note_type(fm)):
            continue
        out.append((the_id, path))
    return out


#: Terminal status per collection -- the only statuses a prune may consider.
#: `cancelled`/`superseded`/`declined` are deliberately absent: SNAPSHOT.md's
#: rule is "keep anything not done", so pruning them needs that rule reworded
#: first (TASK-0082).
PRUNABLE_TERMINAL = {"tasks": "done", "issues": "fixed", "features": "done"}


def _owes_verification(entry, note_fm, statuses):
    """True when an entry still has outstanding verification business.

    Eighteen validator codes are emitted from the walk over `items.*`, so a
    pruned entry stops being checked at all. Measured: pruning without this
    silenced 12 VERIFY-WAIVED warnings in project-os-dev whose notes still
    carried `waiver_expires: 2026-10-23`, and 3 VERIFY warnings in your-trainer
    on issues closed against tests that are `ready`, not `passing`. In both
    cases retention would have erased an outstanding obligation by forgetting
    it. Retention removes finished business; it must not remove unfinished.
    """
    if (str(entry.get("verification_waiver", "") or "").strip()
            or str(note_fm.get("verification_waiver", "") or "").strip()):
        return True
    linked = set(_vd.extract_ids(entry.get("tests"))) | set(_vd.extract_ids(note_fm.get("tests")))
    return any(statuses.get(t, "passing") != "passing" for t in linked)


def prunable_ids(snap, index, window, statuses):
    """IDs removable under ADR-0018's conditions. Fail-safe: doubt -> keep."""
    items = snap.get("items") or {}
    focus = {str(v).strip() for v in (snap.get("focus") or {}).values()
             if isinstance(v, str)}
    out = []
    for coll, terminal in sorted(PRUNABLE_TERMINAL.items()):
        entries = items.get(coll)
        if not isinstance(entries, dict):
            continue
        # (2) keep the N most recent by ID. Count-based, never wall-clock: a
        # date-keyed window makes output depend on the day it ran, so an
        # untouched repo would drift overnight and CI's --check would fail.
        def _key(i):
            m = ID_RE.match(i)
            return int(m.group(2)) if m else -1
        recent = set(sorted(entries, key=_key, reverse=True)[:window])
        for the_id, entry in entries.items():
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("status", "") or "").strip()
            if status != terminal:            # (1) terminal only
                continue
            if status == "deferred":          # (3) never -- ADR-0005
                continue
            if the_id in recent:              # (2)
                continue
            if the_id in focus:               # (4)
                continue
            if the_id not in index:           # (5) note must exist and parse
                continue
            # (6) `note:` is scratch context but HOLDS its entry until cleared.
            # `goal:` does NOT hold -- it is derived under rule 1.
            if str(entry.get("note", "") or "").strip():
                continue
            # (7) outstanding verification business holds the entry: an
            # unexpired waiver, or a linked test that is not passing.
            note_fm = (index.get(the_id) or (None, {}))[1] or {}
            if _owes_verification(entry, note_fm, statuses):
                continue
            out.append((coll, the_id))
    return out


def held_ids(snap):
    """Terminal entries kept back by non-empty `note:` -- a backlog, not an exemption."""
    items = snap.get("items") or {}
    out = []
    for coll, terminal in sorted(PRUNABLE_TERMINAL.items()):
        for the_id, entry in sorted((items.get(coll) or {}).items()):
            if isinstance(entry, dict) and str(entry.get("status", "")).strip() == terminal \
               and str(entry.get("note", "") or "").strip():
                out.append((coll, the_id))
    return out


def prune_entries(lines, targets):
    """Delete whole entries in place; never re-emit the file (ADR-0018)."""
    drop = {i for _, i in targets}
    if not drop:
        return []
    keep, removed, skipping, indent = [], [], None, 0
    for line in lines:
        m = _ITEM_RE.match(line)
        if m:
            skipping = None
            if m.group(2) in drop:
                skipping, indent = m.group(2), len(m.group(1))
                removed.append(m.group(2))
                continue
        elif skipping is not None:
            stripped = line.lstrip()
            if stripped and not line.startswith(" " * (indent + 1)):
                skipping = None
            else:
                continue
        keep.append(line)
    if removed:
        for i, line in enumerate(keep):
            if re.match(r"^items:\s*$", line):
                keep.insert(i + 1, "  # Pruned %d terminal item(s) by retention "
                                   "policy (ADR-0018); the notes remain the archive.\n"
                            % len(removed))
                break
    lines[:] = keep
    return removed


def retention_config(snap):
    """The two per-repo gates (ADR-0018, TASK-0085). Absent means OFF.

    Shipping inert is what makes a twelve-repo rollout possible: the script
    lands everywhere and changes nothing until a repo adds these itself. A repo
    that never opts in keeps today's behaviour indefinitely.
    """
    r = snap.get("retention") or {}
    derive = bool(r.get("derive_fields")) if isinstance(r, dict) else False
    window = r.get("prune_window") if isinstance(r, dict) else None
    try:
        window = int(window)
    except (TypeError, ValueError):
        window = None
    return derive, (window if (window is not None and window >= 0) else None)


def record_title_drift(snap, fields, repo):
    """TASK-0084: the lossless migration record, as Markdown.

    Every drifted value is written out BEFORE derivation overwrites it, so the
    migration needs no per-item judgement and no similarity test -- nothing is
    lost, so nothing has to be decided now.
    """
    rows = []
    for coll, entries in sorted((snap.get("items") or {}).items()):
        if not isinstance(entries, dict):
            continue
        for the_id, entry in sorted(entries.items()):
            if not isinstance(entry, dict):
                continue
            want = fields.get(the_id) or {}
            for field in DERIVED_FIELDS:
                have = entry.get(field)
                if not isinstance(have, str) or field not in want:
                    continue
                if have.strip() != want[field]:
                    rows.append((the_id, field, have.strip(), want[field]))
    out = [
        "---",
        'type: "[[reference]]"',
        "id: REFERENCE-SNAPSHOT-FIELD-MIGRATION",
        'title: "Snapshot field migration record: values replaced when title/goal became derived"',
        "status: active",
        "owner: user:edwin",
        "created: 2026-08-04",
        "updated: 2026-08-04",
        'scope: "project"',
        "source: [\"FEAT-0022\", \"TASK-0084\", \"ADR-0018\"]",
        "related: []",
        "---",
        "",
        "# Snapshot field migration record",
        "",
        "The values `SNAPSHOT.yaml` carried for `title:`/`goal:` in **%s** before ADR-0018" % repo,
        "made those fields derived from the notes. Recorded so the migration is lossless and",
        "needs no per-item judgement: anything worth keeping can be mined from here later, and",
        "it is legitimate for that never to happen.",
        "",
        "%d value(s) replaced." % len(rows),
        "",
    ]
    for the_id, field, old, new in rows:
        out += ["## %s (`%s`)" % (the_id, field), "",
                "- **was:** %s" % old, "- **now:** %s" % new, ""]
    return "\n".join(out) + "\n", len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sync SNAPSHOT.yaml derived fields from docs/.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--check", action="store_true", help="Exit 1 on drift; write nothing")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--report-unregistered", action="store_true",
                    help="List notes with no snapshot entry (advisory; never auto-added)")
    ap.add_argument("--no-prune", action="store_true",
                    help="Disable retention pruning for this run")
    ap.add_argument("--record-field-drift", metavar="PATH",
                    help="TASK-0084: write the lossless migration record and exit")
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve()
    snap_path = root / "SNAPSHOT.yaml"
    if not snap_path.is_file():
        print("sync-snapshot: no SNAPSHOT.yaml at %s" % root, file=sys.stderr)
        return 2

    text = snap_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    statuses, index = note_statuses(root)
    fields = note_fields(root)
    derive_on, window = retention_config(load_yaml(text) or {})

    if args.record_field_drift:
        body, n = record_title_drift(load_yaml(text) or {}, fields, root.name)
        Path(args.record_field_drift).write_text(body, encoding="utf-8")
        print("sync-snapshot: recorded %d field value(s) to %s"
              % (n, args.record_field_drift))
        return 0

    st_changes = sync_statuses(lines, statuses)
    fd_changes = sync_derived_fields(lines, fields, derive_on and not args.check)
    ct_changes = sync_counters(lines, index)
    snap_after = load_yaml("".join(lines)) or {}
    mt_changes = sync_metrics(lines, snap_after, index)

    pruned, held = [], []
    if window is not None and not args.no_prune:
        targets = prunable_ids(snap_after, index, window, statuses)
        held = held_ids(snap_after)
        if args.check:
            pruned = [i for _, i in targets]
        else:
            pruned = prune_entries(lines, targets)
            snap_after = load_yaml("".join(lines)) or {}
            mt_changes += sync_metrics(lines, snap_after, index)
    new_text = "".join(lines)

    total = (len(st_changes) + len(ct_changes) + len(mt_changes)
             + (len(fd_changes) if derive_on else 0) + len(pruned))
    if total == 0:
        if not args.quiet:
            print("sync-snapshot: %s up to date" % root.name)
    else:
        verb = "would update" if args.check else "updated"
        print("sync-snapshot: %s %s %d field(s)" % (root.name, verb, total))
        if not args.quiet:
            for cid, old, new in st_changes:
                print("   status  %-14s %s -> %s" % (cid, old, new))
            if derive_on:
                for cid, field, old, new in fd_changes:
                    print("   %-7s %-14s %.40s -> %.40s" % (field, cid, old, new))
            for pfx, old, new in ct_changes:
                print("   counter %-14s %s -> %s" % (pfx, old, new))
            for key, old, new in mt_changes:
                print("   metric  %-14s %s -> %s" % (key, old, new))
            for the_id in pruned:
                print("   pruned  %s" % the_id)
        if not args.check:
            snap_path.write_text(new_text, encoding="utf-8")

    if fd_changes and not derive_on and not args.quiet:
        # Report mode: the fleet rollout ships this way, so divergence is
        # visible in every repo before any of them opts in.
        print("   %d field divergence(s) from notes; set retention.derive_fields "
              "to adopt (TASK-0085)" % len(fd_changes))
    if held and not args.quiet:
        print("   %d terminal entry(ies) held from pruning by non-empty note: "
              "(clear it once the note carries what matters)" % len(held))

    if args.report_unregistered:
        missing = unregistered(load_yaml(new_text) or {}, index)
        if missing:
            print("   %d note(s) with no snapshot entry (curation decision -- not auto-added):" % len(missing))
            for the_id, path in missing[:20]:
                print("      %-14s %s" % (the_id, path.relative_to(root).as_posix()))

    return 1 if (args.check and total) else 0


if __name__ == "__main__":
    sys.exit(main())
