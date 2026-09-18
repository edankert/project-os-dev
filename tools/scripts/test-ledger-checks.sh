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
# project-os-dev ISS-0060: in a ledger repo the acceptance check settles from the ledger
def cleared(*files):
    root = Path(tempfile.mkdtemp()); d = root / "docs" / "releases" / "ledgers"; d.mkdir(parents=True)
    for name, data in files:
        (d / name).write_text(json.dumps(data), encoding="utf-8")
    return vd._ledger_cleared(root)
check("a repo with no ledgers settles from mark:", vd._ledger_cleared(Path(tempfile.mkdtemp())) is None)
check("a pass clears the check", "TST-0001" in cleared(("WORKING-app.json", {"entries": [good]})))
check("a fail does not clear it", "TST-0001" not in cleared(("WORKING-app.json", {"entries": [dict(good, mark="fail", reason="x")]})))
check("a later fail supersedes an earlier pass", "TST-0001" not in cleared(("WORKING-app.json", {"entries": [dict(good, date="2026-09-01"), dict(good, mark="fail", reason="x", date="2026-09-02")]})))
check("the latest entry by date wins, not by position", "TST-0001" in cleared(("WORKING-app.json", {"entries": [dict(good, date="2026-09-03"), dict(good, mark="fail", reason="x", date="2026-09-02")]})))
check("an invalidation clears a standing pass", "TST-0001" not in cleared(("WORKING-app.json", {"entries": [dict(good, date="2026-09-01"), {"check": "TST-0001", "invalidated_by": "CHG-1", "date": "2026-09-02"}]})))
check("an excused in a sealed ledger does not survive", "TST-0001" not in cleared(("REL-0001-app.json", {"sealed": "2026-09-01", "entries": [dict(good, mark="excused", reason="x")]})))
check("an excused in the working ledger clears", "TST-0001" in cleared(("WORKING-app.json", {"entries": [dict(good, mark="excused", reason="x")]})))
check("a pass in a sealed ledger survives into the working one", "TST-0001" in cleared(("REL-0001-app.json", {"sealed": "2026-09-01", "entries": [good]}), ("WORKING-app.json", {"entries": []})))
check("the working ledger's fail overrides a sealed pass", "TST-0001" not in cleared(("REL-0001-app.json", {"sealed": "2026-09-01", "entries": [dict(good, date="2026-09-20")]}), ("WORKING-app.json", {"entries": [dict(good, mark="fail", reason="x", date="2026-09-10")]})))
# android loads before ios, so a merged history would let the ios fail win
check("a pass on one platform settles it though another fails", "TST-0001" in cleared(("WORKING-android.json", {"entries": [good]}), ("WORKING-ios.json", {"entries": [dict(good, mark="fail", reason="x")]})))
idx = {"TST-0005": (Path("x"), {"id": "TST-0005", "mark": "done"})}
check("with ledgers, a done mark: no longer settles it", not vd._acceptance_is_settled("TST-0005", idx, set()))
check("without ledgers, a done mark: still settles it", vd._acceptance_is_settled("TST-0005", idx, None))
# the gate itself, end to end: a done feature covered by an acceptance check
import subprocess
e2e = Path(tempfile.mkdtemp())
for sub in ("docs/features/x", "docs/tests", "docs/releases/ledgers"):
    (e2e / sub).mkdir(parents=True)
(e2e / "SNAPSHOT.yaml").write_text('items:\n  features:\n    FEAT-0001: { title: "X", status: done }\n')
(e2e / "docs/features/x/FEAT-0001-X.md").write_text('---\ntype: "[[feature]]"\nid: FEAT-0001\ntitle: "X"\nstatus: done\nowner: user:edwin\ncreated: 2026-09-18\nupdated: 2026-09-18\n---\n# X\n')
(e2e / "docs/tests/TST-0001-A.md").write_text('---\ntype: "[[test]]"\nid: TST-0001\ntitle: "A"\nstatus: active\nlevel: acceptance\ncovers: ["[[FEAT-0001-X]]"]\nowner: user:edwin\ncreated: 2026-09-18\nupdated: 2026-09-18\n---\n# A\n')
def gate(entries):
    (e2e / "docs/releases/ledgers/WORKING-app.json").write_text(json.dumps({"platform": "app", "entries": entries}))
    out = subprocess.run([sys.executable, sys.argv[1], "--repo-root", str(e2e)], capture_output=True, text=True).stdout
    return "[VERIFY-ACCEPTANCE] FEAT-0001" in out
check("the gate is quiet when the ledger passes the check", not gate([good]))
check("the gate warns when the ledger has no verdict for it", gate([]))
# project-os-dev ISS-0063: a walked check lives under docs/tests/acceptance/
loc = Path(tempfile.mkdtemp())
def placed(rel, **fm):
    p = loc / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("---\n---\n")
    r = vd.Report(); vd.validate_acceptance_location(loc, r, {"TST-0009": (p, dict({"id": "TST-0009", "level": "acceptance"}, **fm))})
    return any("ACCEPT-LOCATION" in m for m in r.errors)
check("a walked check beside its feature is refused", placed("docs/features/x/plan/tests/TST-0009-A.md"))
check("a walked check under docs/tests/acceptance/ is fine", not placed("docs/tests/acceptance/TST-0009-A.md"))
check("an automated check beside its feature is fine", not placed("docs/features/x/plan/tests/TST-0009-A.md", command="make test"))
print("test-ledger-checks: %d assertions, %d failure(s)" % (n, failures))
sys.exit(1 if failures else 0)
PYEOF
