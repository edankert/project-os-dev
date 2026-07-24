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
     (task done, issue closed, requirement implemented, feature done) unless
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
     (FEATURE-REQ). The last two gates are forward-only — see
     FEATURE_REQ_GATE_FROM.

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

ALLOWED_STATUS = {
    "task": {"backlog", "next", "doing", "blocked", "done", "deferred", "cancelled"},
    "issue": {"triage", "open", "in-progress", "blocked", "fixed", "closed", "reopened", "wont-fix", "deferred"},
    "feature": {"backlog", "planned", "in-progress", "in-review", "done", "deferred", "cancelled", "superseded"},
    "phase": {"planned", "active", "done", "deferred"},
    "requirement": {"draft", "approved", "implemented", "retired", "deferred", "cancelled", "superseded"},
    "risk": {"open", "mitigating", "monitoring", "closed"},
    "workflow": {"draft", "active", "deprecated"},
    "change": {"merged", "reverted"},
    "adr": {"proposed", "accepted", "rejected", "superseded"},
    "test": {"draft", "ready", "passing", "failing", "blocked", "deprecated"},
    "release": {"draft", "staged", "released", "rolled-back"},
}

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
    "issues": "closed",
    "requirements": "implemented",
    "features": "done",
}

RELATIONSHIP_FIELDS = (
    "parent", "features", "tasks", "issues", "requirements", "tests",
    "phases", "phase", "depends", "blocks", "mitigation_tasks", "workflows",
    "origin", "deferred", "implements", "supersedes", "superseded",
)

# ADR-0007 FEATURE-REQ gate cutover. A feature that closed before this date is
# grandfathered: its unresolved requirement criteria are reported as a warning
# (visible debt) rather than an error (blocking). Features touched on or after it
# are held to the gate. Compared against the feature note's `updated:` date;
# an absent or unparseable date is treated as grandfathered.
FEATURE_REQ_GATE_FROM = "2026-07-25"

def _after_gate_cutover(fm):
    """True when a note was last touched on/after the ADR-0007 gate cutover.

    Used to keep the FEATURE-REQ and terminal REQ-BOXES gates forward-only:
    work that closed under the old rules stays a warning (visible debt), while
    anything closed or edited afterwards is a build failure. A missing or
    unparseable `updated:` is treated as grandfathered — the gate never fires
    on a note it cannot date.
    """
    raw = (fm or {}).get("updated")
    if raw is None:
        return False
    text = str(raw).strip().strip('"').strip("'")[:10]
    if len(text) != 10 or text[4] != "-" or text[7] != "-":
        return False
    return text >= FEATURE_REQ_GATE_FROM


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
        "issues_open": count("ISS", {"open", "in-progress", "blocked", "reopened"}),
        "issues_triage": count("ISS", {"triage"}),
        "tasks_deferred": count("TASK", {"deferred"}),
        "issues_deferred": count("ISS", {"deferred"}),
        "requirements_total": count("REQ"),
        "requirements_implemented": count("REQ", {"implemented", "verified"}),
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
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def count_acceptance_boxes(path):
    """Count (unticked, ticked) criteria in a requirement note's Acceptance Criteria section.

    Fenced code blocks are skipped entirely: a `# comment` inside a fence must not be
    read as a heading that ends the section, and a `- [ ]` inside one is not a criterion.
    Falls back to the whole body when the note has no Acceptance heading.
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
            if re.match(r"^#{1,6}\s+Acceptance\b", line, re.IGNORECASE):
                seen_section, section = True, []
                continue
            if seen_section:
                break  # next heading ends the section
        if seen_section:
            section.append(line)
    scan = section if seen_section else body
    return (sum(1 for l in scan if UNCHECKED_RE.match(l)),
            sum(1 for l in scan if CHECKED_RE.match(l)))


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, code, msg):
        self.errors.append("ERROR [%s] %s" % (code, msg))

    def warn(self, code, msg):
        self.warnings.append("WARN  [%s] %s" % (code, msg))


# ------------------------------------------------------------------ checks
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
    """Inspect notes the snapshot cannot see.

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

    for the_id, (path, fm) in sorted(note_index.items()):
        if the_id in registered:
            continue  # covered by STATUS-VALUE / ITEM-STATUS against the snapshot entry
        nt = note_type(fm)
        status = str((fm or {}).get("status", "") or "").strip()
        if not status or nt not in allowed_status:
            continue
        if status not in allowed_status[nt]:
            # Warning, not error, deliberately: this check reaches notes that were
            # never validated before, so it surfaces years of accumulated legacy
            # vocabulary at once (173 across the fleet when introduced). Failing
            # those builds outright would punish repos for drift the tooling
            # allowed. Graduate to report.error once the fleet is migrated.
            report.warn(
                "NOTE-STATUS",
                "%s status '%s' not allowed for %s (%s); the note is not in SNAPSHOT.yaml, so no "
                "snapshot-driven check covers it" % (the_id, status, nt, path.relative_to(root).as_posix()),
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
    validate_unregistered_notes(root, items, note_index, note_claimants, allowed_status, report)

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
            if terminal and status == terminal:
                waiver = str(fm.get("verification_waiver", "") or entry.get("verification_waiver", "")).strip()
                linked_tests = set(extract_ids(entry.get("tests"))) | set(extract_ids(fm.get("tests")))
                if waiver:
                    report.warn("VERIFY-WAIVED", "%s is %s under recorded waiver: %s" % (item_id, terminal, waiver))
                else:
                    for tst in sorted(linked_tests):
                        tst_status = ""
                        tests_coll = items.get("tests") or {}
                        if tst in tests_coll and isinstance(tests_coll[tst], dict):
                            tst_status = str(tests_coll[tst].get("status", ""))
                        elif tst in note_index:
                            tst_status = str((note_index[tst][1] or {}).get("status", ""))
                        else:
                            report.error("VERIFY", "%s is %s but linked test %s was not found" % (item_id, terminal, tst))
                            continue
                        if tst_status != "passing":
                            report.error("VERIFY", "%s is %s but linked test %s is '%s', not passing" % (item_id, terminal, tst, tst_status))
                    if coll_name == "features":
                        for task_ref in extract_ids(entry.get("tasks")):
                            t_entry = (items.get("tasks") or {}).get(task_ref)
                            t_status = str(t_entry.get("status", "")) if isinstance(t_entry, dict) else str((note_index.get(task_ref, (None, {}))[1] or {}).get("status", ""))
                            if t_status and t_status not in ("done", "cancelled"):
                                report.error("VERIFY", "%s is done but task %s is '%s', not scope-resolved (done/cancelled)" % (item_id, task_ref, t_status))

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
        own_feats = sorted({f for f in extract_ids((fm or {}).get("implements")) if prefix_of(f) == "FEAT"})
        if len(own_feats) > 1:
            report.error("REQ-OWNER", "%s implements %d features (%s) but a requirement names at most one (ADR-0007); split the requirement, or pick the true owner and drop the rest" % (req_id, len(own_feats), ", ".join(own_feats)))

        if status == "implemented" and note_path is not None:
            unticked, ticked = count_acceptance_boxes(note_path)
            criteria = entry.get("acceptance") or (fm or {}).get("acceptance") or []
            n_criteria = len(criteria) if isinstance(criteria, list) else 0
            # Forward-only, as for FEATURE-REQ: a requirement that went terminal
            # before the cutover is grandfathered to a warning (visible debt);
            # one advanced or touched afterwards is a build failure.
            emit = report.error if _after_gate_cutover(fm) else report.warn
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
        for f in extract_ids((fm or {}).get("implements")):
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
        emit = report.error if _after_gate_cutover(f_fm) else report.warn
        noun = "requirement it owns has" if len(unresolved) == 1 else "requirements it owns have"
        emit("FEATURE-REQ", "%s is done but a %s unresolved acceptance criteria: %s; tick with evidence, reconcile, or descope the requirement before closing the feature (ADR-0007)" % (feat_id, noun, ", ".join(unresolved)))

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
        prefix, num = m.group(1), int(m.group(2))
        if set(str(num)) == {"9"}:
            return  # all-9s sentinel IDs (e.g. PHASE-999 parking lot) are exempt from counters
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
                report.warn("REVIEW", "%s is '%s' without independent review (reviewed_by/review_verdict); see QUALITY.md" % (item_id, status))

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
