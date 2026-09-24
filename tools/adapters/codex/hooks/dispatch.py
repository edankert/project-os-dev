#!/usr/bin/env python3
"""Codex lifecycle adapter for project-os hook contracts HC-001..HC-008.

One process handles each event. Confirmed violations block; opaque shell writes
remain subject to git hooks and CI. See tools/adapters/codex/ADAPTER.md.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ITEM = re.compile(r"\b(?:TASK|ISS|FEAT)-\d{2,}\b")
TEST = re.compile(r"\bTST-\d{2,}\b")
STATUS = re.compile(r"^\+\s*status:\s*['\"]?(done|fixed)['\"]?\s*$", re.M)
FOCUS = re.compile(r"^focus:\s*\n((?:[ \t]+[^\n]*\n)*)", re.M)
EXEMPT_PARTS = {"docs", "tools", ".claude", ".codex", ".agents", ".cursor", ".github"}
EXEMPT_NAMES = {"SNAPSHOT.yaml", "CLAUDE.md", "CONTEXT.md", "README.md", "AGENTS.md", "LLM_BRIEF.md", ".gitignore", ".project-os-sync"}
RISK_NAMES = {"package.json", "package-lock.json", "Cargo.toml", "Cargo.lock", "requirements.txt", "go.mod", "go.sum", "Gemfile", "Gemfile.lock", "pom.xml", "build.gradle", "Dockerfile", "Jenkinsfile"}


def emit(value):
    print(json.dumps(value, ensure_ascii=False))


def context(event, value):
    emit({"hookSpecificOutput": {"hookEventName": event, "additionalContext": value}})


def deny(reason):
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}})


def root_for(path, cwd):
    """Use the target repo's snapshot; don't gate unrelated absolute paths."""
    target = Path(path)
    if not target.is_absolute():
        target = cwd / target
    target = target.resolve()
    for parent in (target.parent, *target.parents):
        if (parent / "SNAPSHOT.yaml").is_file():
            return parent
    return None


def snapshot(root):
    try:
        return (root / "SNAPSHOT.yaml").read_text(encoding="utf-8")
    except OSError:
        return ""


def placeholder(text):
    return bool(re.search(r"^\s*replace_me:\s*true\s*$", text, re.M))


def focus(text, name):
    m = FOCUS.search(text)
    if not m:
        return ""
    line = re.search(r"^\s+" + re.escape(name) + r":\s*([^#\n]*)", m.group(1), re.M)
    return line.group(1).strip().strip("\"'") if line else ""


def item_status(text, item):
    m = re.search(r"^    " + re.escape(item) + r":\s*\n((?: {6}[^\n]*\n)*)", text, re.M)
    if not m:
        return ""
    state = re.search(r"^      status:\s*[\"']?([\w-]+)", m.group(1), re.M)
    return state.group(1) if state else ""


def patch_edits(command):
    edits = []
    current = None
    for line in command.splitlines():
        m = re.match(r"\*\*\* (?:Add|Update|Delete) File: (.+)$", line)
        if m:
            current = [m.group(1).strip(), []]
            edits.append(current)
        elif current is not None and line.startswith(("+", " ")) and not line.startswith("+++ "):
            current[1].append(line)
    return [(p, "\n".join(lines)) for p, lines in edits]


def shell_edits(command):
    # These forms are unambiguous. Arbitrary scripts and command substitution
    # are deliberately not guessed at; the commit/CI gate covers them.
    edits = patch_edits(command)
    for m in re.finditer(r"(?:^|[;\n])\s*(?:cat|printf|echo)\b[^\n;]*?\s>>?\s*([A-Za-z0-9_./-]+)", command):
        edits.append((m.group(1), command))
    for m in re.finditer(r"(?:^|[;\n])\s*tee\s+(?:-a\s+)?([A-Za-z0-9_./-]+)", command):
        edits.append((m.group(1), command))
    return edits


def edits(payload):
    inp = payload.get("tool_input") or {}
    if not isinstance(inp, dict):
        return []
    name = payload.get("tool_name", "")
    command = inp.get("command") or ""
    if name == "apply_patch" and isinstance(command, str):
        return patch_edits(command)
    if name == "Bash" and isinstance(command, str):
        return shell_edits(command)
    path = inp.get("file_path")
    return [(path, inp.get("content") or inp.get("new_string") or "")] if isinstance(path, str) else []


def exempt(path, root):
    try:
        rel = Path(path).resolve().relative_to(root)
    except ValueError:
        return True
    parts = rel.parts
    if any(part in EXEMPT_PARTS for part in parts[:-1]):
        return True
    return bool(parts and (parts[-1] in EXEMPT_NAMES or parts[-1].startswith((".prettierrc", ".markdownlint", ".yamllint"))))


def frontmatter(path):
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.match(r"---\s*\n(.*?)\n---", content, re.S)
    return m.group(1) if m else ""


def note_index(root):
    return {m.group(1): p for p in (root / "docs").rglob("*.md") if (m := re.match(r"((?:TASK|ISS|FEAT|TST)-\d+)", p.name))}


def item_tests(item, root, index, pending):
    tests = set(TEST.findall(pending))
    if item in index:
        tests.update(TEST.findall(frontmatter(index[item])))
    snap = snapshot(root)
    m = re.search(r"^    " + re.escape(item) + r":\s*\n((?: {6}[^\n]*\n)*)", snap, re.M)
    if m:
        tests.update(TEST.findall(m.group(1)))
    return tests


def waiver(text):
    if not re.search(r"^verification_waiver:\s*\S", text, re.M):
        return None
    return bool(re.search(r"^waiver_expires:\s*\d{4}-\d{2}-\d{2}\s*$", text, re.M))


def terminal_items(path, pending):
    if not STATUS.search(pending):
        return set()
    name = Path(path).name
    match = re.match(r"((?:TASK|ISS|FEAT)-\d+)", name)
    if match:
        return {match.group(1)}
    if name == "SNAPSHOT.yaml":
        out = set()
        current = None
        for line in pending.splitlines():
            m = re.search(r"\b((?:TASK|ISS|FEAT)-\d+):\s*$", line)
            if m:
                current = m.group(1)
            if STATUS.match(line) and current:
                out.add(current)
        return out
    return set()


def verification(root, path, pending):
    items = terminal_items(path, pending)
    if not items:
        return "", ""
    index = note_index(root)
    blocked = []
    no_tests = []
    for item in sorted(items):
        note_fm = frontmatter(index[item]) if item in index else ""
        current_waiver = waiver(note_fm)
        pending_waiver = waiver("\n".join(line[1:] for line in pending.splitlines() if line.startswith("+")))
        if False in (current_waiver, pending_waiver):
            blocked.append(f"{item} has verification_waiver without waiver_expires")
            continue
        if True in (current_waiver, pending_waiver):
            continue
        tests = item_tests(item, root, index, pending)
        if not tests:
            no_tests.append(item)
            continue
        for test in sorted(tests):
            fm = frontmatter(index[test]) if test in index else ""
            command = re.search(r"^command:\s*(.*)$", fm, re.M)
            if command and command.group(1).strip().strip("\"'"):
                continue
            if re.search(r"^level:\s*['\"]?acceptance\b", fm, re.M):
                continue
            state = re.search(r"^status:\s*['\"]?([\w-]+)", fm, re.M)
            if not state or state.group(1) != "passing":
                blocked.append(f"{item} -> {test} is {state.group(1) if state else 'missing'}")
    reason = "Verification gate (HC-003): " + "; ".join(blocked) + ". Pass the tests or record an expiring waiver." if blocked else ""
    advisory = "Verification gate (HC-003): " + ", ".join(no_tests) + " has no linked test. Confirm this is a documentation-only task or link verification." if no_tests else ""
    return reason, advisory


def risk_hint(paths):
    hits = []
    for path in paths:
        p = Path(path)
        if p.name in RISK_NAMES or p.name.startswith(".env") or ".github/workflows/" in path or p.name.endswith((".lock", ".gradle")):
            hits.append(path)
    if hits:
        return "Risk scan (HC-005): review dependency, configuration, or deployment risk for " + ", ".join(hits[:3]) + ". Create or update a RISK note when a hazard changed."
    return ""


def marker(payload, root):
    session = payload.get("session_id")
    if not session:
        return None
    key = hashlib.sha256((str(root) + "\0" + str(session)).encode()).hexdigest()
    base = Path(tempfile.gettempdir()) / "project-os-codex-hooks"
    base.mkdir(mode=0o700, exist_ok=True)
    return base / key


def pre(payload, cwd):
    advisory = []
    for raw, pending in edits(payload):
        root = root_for(raw, cwd)
        if root is None:
            continue
        snap = snapshot(root)
        if placeholder(snap):
            continue
        path = (cwd / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if not exempt(path, root) and not (focus(snap, "task") or focus(snap, "issue")):
            deny("Document-first gate (HC-001): set focus.task or focus.issue in the target repository's SNAPSHOT.yaml before editing code.")
            return
        reason, hint = verification(root, str(path), pending)
        if reason:
            deny(reason)
            return
        if hint:
            advisory.append(hint)
    if advisory:
        context("PreToolUse", " ".join(advisory))


def post(payload, cwd):
    changed = edits(payload)
    if not changed:
        return
    paths = []
    hints = []
    for raw, pending in changed:
        paths.append(raw)
        root = root_for(raw, cwd)
        if root is None:
            continue
        snap = snapshot(root)
        if placeholder(snap):
            continue
        mark = marker(payload, root)
        if mark:
            mark.touch()
        if re.search(r"^\+\s*status:\s*doing\s*$", pending, re.M):
            phase = focus(snap, "phase")
            if phase:
                hints.append(f"Phase alignment (HC-004): confirm the task starting now belongs to {phase}.")
    risk = risk_hint(paths)
    if risk:
        hints.append(risk)
    if hints:
        context("PostToolUse", " ".join(hints))


def start(payload, cwd):
    root = root_for("SNAPSHOT.yaml", cwd)
    if root and not placeholder(snapshot(root)):
        # HC-002: serve the orientation slice (project-os-dev TASK-0080); fall back to the reminder.
        brief = ""
        slicer = root / "tools/scripts/snapshot-slice.py"
        if slicer.is_file():
            result = subprocess.run([sys.executable, str(slicer), str(root)], capture_output=True, text=True, timeout=20)
            brief = result.stdout.strip() if result.returncode == 0 else ""
        context("SessionStart", brief or "Read CONTEXT.md, docs/INDEX.md, SNAPSHOT.yaml, then run bash tools/agents/bootstrap.sh before work. Inspect the current branch, head, focus, and working tree.")


def prompt(payload, cwd):
    root = root_for("SNAPSHOT.yaml", cwd)
    if root is None:
        return
    snap = snapshot(root)
    if placeholder(snap):
        return
    active = focus(snap, "task") or focus(snap, "issue") or focus(snap, "feature")
    phase = focus(snap, "phase")
    state = item_status(snap, active) if active else ""
    where = f"{active} is {state}, phase {phase}" if active else "nothing in flight"
    if state == "review":
        next_step = "Use independent-reviewer for a clean-context review."
    elif state in ("deferred", "done", "fixed", "implemented"):
        next_step = "Re-adopt parked work or write the next note before coding."
    else:
        next_step = "Write a single item note here; use planner for a multi-item scaffold or ambiguous request. Pass the user's prompt verbatim and what the result enables."
    context("UserPromptSubmit", f"project-os: {where}. {next_step}")


def stop(payload, cwd):
    if payload.get("stop_hook_active"):
        return
    root = root_for("SNAPSHOT.yaml", cwd)
    if root is None:
        return
    snap = snapshot(root)
    if placeholder(snap):
        return
    validator = root / "tools/scripts/validate-docs.sh"
    if validator.is_file():
        result = subprocess.run(["bash", str(validator), "--repo-root", str(root), "--quiet"], cwd=root, capture_output=True, text=True, timeout=60)
        if result.returncode == 1:
            summary = (result.stdout + result.stderr).strip().replace("\n", " ")[:450]
            emit({"decision": "block", "reason": f"Docs validation failed (HC-007): {summary}. Run tools/scripts/validate-docs.sh and fix the errors."})
            return
    mark = marker(payload, root)
    if mark is not None and not mark.exists():
        return
    task = focus(snap, "task")
    issue = focus(snap, "issue")
    if not (task or issue):
        return
    if mark is not None:
        mark.unlink(missing_ok=True)
    item = f"task {task}" if task else f"issue {issue}"
    midflight = "If stopping mid-flight, record a handoff in its note, then stop; the loop guard permits the second stop."
    reason = f"Close-out check (HC-006): focus still names {item}. If complete, update its status and clear or move focus. {midflight}"
    boxes = open_boxes(root, snap, task) if task else None
    if boxes:
        listed = "; ".join(f'"{b}"' for b in boxes[:5])
        more = f" and {len(boxes) - 5} more" if len(boxes) > 5 else ""
        reason = f"Close-out check (HC-006): focus still names task {task}, and its note has {len(boxes)} unticked box(es): {listed}{more}. If work remains, carry on with it. If complete, tick each box with its evidence, set the status to done and clear or move focus. {midflight}"
    elif boxes == []:
        reason = f"Close-out check (HC-006): focus still names task {task}, and every box in its note is ticked. Set the status to done and clear or move focus. {midflight}"
    emit({"decision": "block", "reason": reason})


def open_boxes(root, text, item):
    """Unticked boxes under the task note's Definition of Done and Steps, or None
    when the note cannot be found or has neither section (project-os-dev TASK-0157)."""
    note = None
    m = re.search(r"^    " + re.escape(item) + r":(.*)\n((?: {6}[^\n]*\n)*)", text, re.M)
    if m:
        path = re.search(r"file:\s*(?:\"([^\"]+)\"|'([^']+)'|([^,}\n]+))", m.group(1) + "\n" + m.group(2))
        if path:
            note = root / next(g for g in path.groups() if g).strip()
    if note is None or not note.is_file():
        # A focus task with no snapshot item: find its note by filename.
        note = next((p for p in sorted((root / "docs").rglob(item + "-*.md")) if p.is_file()), None)
    if note is None:
        return None
    boxes, inside, fence, sections = [], False, False, 0
    for line in note.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("```"):
            fence = not fence
        elif fence:
            continue
        elif line.startswith("## "):
            inside = line.strip() in ("## Definition of Done", "## Steps")
            sections += inside
        elif inside and re.match(r"\s*- \[ \]", line):
            box = re.sub(r"^\s*- \[ \]\s*", "", line).replace("\r", "").replace("\t", " ").strip()
            boxes.append(box or "(a box with no text)")
    return boxes if sections else None


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
    event = payload.get("hook_event_name") or (sys.argv[1] if len(sys.argv) > 1 else "")
    try:
        if event == "PreToolUse":
            pre(payload, cwd)
        elif event == "PostToolUse":
            post(payload, cwd)
        elif event == "SessionStart":
            start(payload, cwd)
        elif event == "UserPromptSubmit":
            prompt(payload, cwd)
        elif event == "Stop":
            stop(payload, cwd)
    except (OSError, subprocess.SubprocessError) as exc:
        if event == "Stop":
            emit({"systemMessage": f"project-os hook could not validate docs: {exc}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
