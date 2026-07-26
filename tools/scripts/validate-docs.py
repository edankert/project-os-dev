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

ID_PREFIXES = ("ADR", "FEAT", "ISS", "PHASE", "REQ", "RISK", "REL", "TASK", "TST", "WF")
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
    "test": {"ready", "passing", "failing"},
    "release": {"draft", "released", "reverted"},
}

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


# collection -> (terminal status, human label)
TERMINAL = {
    "tasks": "done",
    "issues": "fixed",   # ADR-0008: `closed` merged into `fixed`; 3% follow-through fleet-wide
    "requirements": "implemented",
    "features": "done",
}

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


# Statuses that resolve an item's place in a parent's scope / a requirement's delivery.
# `deferred` is deliberately absent (STATUSES.md, "Deferral and re-adoption").
RESOLVED_STATUSES = ("done", "cancelled", "superseded")

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
        "features_total": count("FEAT"),
        "features_done": count("FEAT", {"done"}),
        "phases_total": count("PHASE"),
        "phases_done": count("PHASE", {"done"}),
        "tasks_total": count("TASK"),
        "tasks_done": count("TASK", {"done"}),
        "tests_total": count("TST"),
        "tests_passing": count("TST", {"passing"}),
        "tests_failing": count("TST", {"failing"}),
        # ADR-0008: `fixed` is terminal, so it is correctly excluded here. Before the
        # merge, `fixed` meant "implemented, not verified" and 313 fleet-wide issues
        # sat in it counted by nothing (ISS-0008) — resolved by removing the limbo
        # state, not by widening the metric.
        "issues_open": count("ISS", {"open"}),
        "issues_triage": count("ISS", {"triage"}),
        "tasks_deferred": count("TASK", {"deferred"}),
        "issues_deferred": count("ISS", {"deferred"}),
        "requirements_total": count("REQ"),
        "requirements_implemented": count("REQ", {"implemented"}),
        "risks_open": count("RISK", {"open", "mitigating", "monitoring"}),
        "releases_total": count("REL"),
        "decisions_total": count("ADR"),
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

    # feature status -> the plan status that tracks it. `deferred` and
    # `cancelled` are deliberately absent: a parked feature's plan may
    # honestly stay `draft` or become `superseded`, and guessing between
    # them would produce noise rather than signal.
    follows = {
        "backlog": {"draft"},
        "planned": {"draft"},
        "in-progress": {"active"},
        "in-review": {"active"},
        "done": {"done"},
        "superseded": {"superseded"},
    }

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
            type_key = next(iter(expected_types), None)
            if status and type_key in allowed_status and status not in allowed_status[type_key]:
                report.error("STATUS-VALUE", "%s status '%s' not allowed for %s" % (item_id, status, type_key))

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
            if status in ("passing", "failing") and not has_value((fm or {}).get("last_run")):
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
        if status in ("draft", "approved") and all_resolved:
            report.error("REQ-STALE", "%s is '%s' but every implementing feature (%s) has reached a terminal status; advance it per close-out 'Requirement advancement' (tick criteria with evidence, reconcile departures, set implemented) or supersede it" % (req_id, status, ", ".join("%s=%s" % (f, known[f]) for f in sorted(known))))
        elif status == "draft" and any(s in ("in-progress", "in-review", "done") for s in known.values()):
            active = sorted(f for f, s in known.items() if s in ("in-progress", "in-review", "done"))
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
    DESCOPED = ("deferred", "cancelled", "superseded")
    reqs_by_owner = {}   # FEAT id -> [(REQ id, note_path)]
    for req_id in sorted(req_ids):
        note_path, fm = note_index.get(req_id, (None, {}))
        if note_path is None:
            continue
        if effective_status(req_id) in DESCOPED:
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
    PHASE_RESOLVED = {
        "task": {"done", "cancelled", "superseded"},
        "issue": {"fixed", "wont-fix", "cancelled", "superseded"},
        "requirement": {"implemented", "retired", "cancelled", "superseded"},
        "feature": {"done", "cancelled", "superseded"},
        # STATUSES.md says "a note naming it in `phase:`", so a risk parked on a
        # closed phase counts too — an open hazard is not resolved by the phase
        # that raised it closing. Omitting risks made the gate narrower than its
        # own prose (found in independent review of CHG-20260726).
        "risk": {"closed"},
    }
    CLOSED_PHASE_STATUSES = ("done", "superseded")

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
    for coll_name, settled in (("tests", {"passing"}), ("changes", {"merged"})):
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
    args = ap.parse_args(argv)

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
