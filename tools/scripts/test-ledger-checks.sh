#!/usr/bin/env bash
# The acceptance-ledger and frontmatter checks ported from project-os-cockpit
# (project-os-dev TASK-0136), on made-up ledgers and notes. The cockpit keeps its
# own copy with its own tests; this guards the template's.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - "$HERE/validate-docs.py" <<'PYEOF'
import importlib.util, json, sys, tempfile
from pathlib import Path
spec = importlib.util.spec_from_file_location("vd", sys.argv[1]); vd = importlib.util.module_from_spec(spec); spec.loader.exec_module(vd)
failures = n = 0
def check(desc, ok):
    global failures, n
    n += 1; failures += not ok
    print("  %s %s" % ("ok  " if ok else "FAIL", desc))
def ledger(name, data):
    root = Path(tempfile.mkdtemp()); d = root / "docs" / "releases" / "ledgers"; d.mkdir(parents=True)
    (d / name).write_text(json.dumps(data) if not isinstance(data, str) else data, encoding="utf-8")
    r = vd.Report(); vd.validate_ledgers(root, r, {}); return r.errors + r.warnings
good = {"check": "TST-0001", "mark": "pass", "date": "2026-09-18", "method": "manual", "by": "user:edwin"}
codes = lambda out: {m.split("[")[1].split("]")[0] for m in out}
check("a well-formed ledger draws nothing", ledger("WORKING-app.json", {"platform": "app", "entries": [good]}) == [])
check("a fail with no reason draws LEDGER-REASON", "LEDGER-REASON" in codes(ledger("WORKING-app.json", {"platform": "app", "entries": [dict(good, mark="fail")]})))
check("a fail with a reason draws nothing", ledger("WORKING-app.json", {"platform": "app", "entries": [dict(good, mark="fail", reason="broken")]}) == [])
check("an unknown mark draws LEDGER-MARK", "LEDGER-MARK" in codes(ledger("WORKING-app.json", {"platform": "app", "entries": [dict(good, mark="done")]})))
check("a date-shaped non-date draws LEDGER-ENTRY", "LEDGER-ENTRY" in codes(ledger("WORKING-app.json", {"platform": "app", "entries": [dict(good, date="2026-13-45")]})))
check("an entry with no author draws LEDGER-ENTRY", "LEDGER-ENTRY" in codes(ledger("WORKING-app.json", {"platform": "app", "entries": [dict(good, by="")]})))
check("an unknown method draws LEDGER-ENTRY", "LEDGER-ENTRY" in codes(ledger("WORKING-app.json", {"platform": "app", "entries": [dict(good, method="guess")]})))
check("a file that names no platform draws LEDGER-NAME", "LEDGER-NAME" in codes(ledger("notes.json", {"platform": "app", "entries": [good]})))
check("a platform that contradicts the filename draws LEDGER-NAME", "LEDGER-NAME" in codes(ledger("WORKING-ios.json", {"platform": "android", "entries": [good]})))
check("a ledger that is not JSON draws LEDGER-PARSE", "LEDGER-PARSE" in codes(ledger("WORKING-app.json", "{not json")))
# moved verdict fields, only in a repo that keeps ledgers
root = Path(tempfile.mkdtemp()); (root / "docs" / "releases" / "ledgers").mkdir(parents=True)
(root / "docs" / "releases" / "ledgers" / "WORKING-app.json").write_text(json.dumps({"platform": "app", "entries": []}))
note = root / "docs" / "TST-0002.md"; note.write_text("---\nid: TST-0002\nmark: done\n---\n")
r = vd.Report(); vd.validate_moved_verdict_fields(root, r, {"TST-0002": (note, {"id": "TST-0002", "mark": "done", "type": "[[test]]", "level": "acceptance"}), "TST-0004": (note, {"id": "TST-0004", "mark": "done", "type": "[[test]]", "level": "unit"})})
out = r.errors + r.warnings
check("a verdict field on a note in a ledger repo draws LEDGER-FIELD", "LEDGER-FIELD" in codes(out))
check("a unit test is not an acceptance check and is not checked", not any("TST-0004" in m for m in out))
check("LEDGER-FIELD warns before its 2026-12-17 promotion", any("LEDGER-FIELD" in m for m in r.warnings) and not any("LEDGER-FIELD" in m for m in r.errors))
root2 = Path(tempfile.mkdtemp()); (root2 / "docs").mkdir(); note2 = root2 / "docs" / "TST-0003.md"; note2.write_text("---\nid: TST-0003\nmark: done\n---\n")
r = vd.Report(); vd.validate_moved_verdict_fields(root2, r, {"TST-0003": (note2, {"id": "TST-0003", "mark": "done"})})
check("a repo with no ledgers is not checked", r.errors + r.warnings == [])
# frontmatter that does not parse (needs PyYAML; the check fails open without it)
try:
    import yaml  # noqa: F401
    root3 = Path(tempfile.mkdtemp()); (root3 / "docs").mkdir()
    (root3 / "docs" / "TASK-0001.md").write_text('---\nid: TASK-0001\ntitle: "unescaped "quotes" here"\n---\n')
    (root3 / "docs" / "TASK-0002.md").write_text('---\nid: TASK-0002\ntitle: "fine"\n---\n')
    r = vd.Report(); vd.validate_frontmatter_parses(root3, r); out = r.errors + r.warnings
    check("frontmatter that does not parse draws NOTE-FRONTMATTER", any("NOTE-FRONTMATTER" in m and "TASK-0001" in m for m in out))
    check("frontmatter that parses draws nothing", not any("TASK-0002" in m for m in out))
except ImportError:
    print("  skip NOTE-FRONTMATTER cases: PyYAML is not installed, and the check fails open without it")
print("test-ledger-checks: %d assertions, %d failure(s)" % (n, failures))
sys.exit(1 if failures else 0)
PYEOF
